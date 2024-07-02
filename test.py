import docker
import requests
import netifaces
import time
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

GET_IP_FAILED = "Error: Unable to get IP"

def get_network_info():
    # 기본 게이트웨이 인터페이스 찾기
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET]
    default_interface = default_gateway[1]

    # 게이트웨이 IP 주소
    gateway_ip = default_gateway[0]

    # 인터페이스의 IP 주소들
    interface_info = netifaces.ifaddresses(default_interface)
    private_ip = interface_info[netifaces.AF_INET][0]['addr']

    return private_ip, gateway_ip, default_interface

def get_public_ip():
    services = [
        'https://api.ipify.org',
        'http://ip.42.pl/raw',
        'http://ifconfig.me/ip',
        'https://ident.me'
    ]
    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except requests.RequestException:
            continue
    return GET_IP_FAILED


def generate_ssh_key():
    key = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048
    )

    private_key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )

    return private_key, public_key


def create_ubuntu_ssh_container():
    client = docker.from_env()

    print("Generating SSH key pair...")
    private_key, public_key = generate_ssh_key()

    # Save private key to a file
    with open('ubuntu_ssh_key.pem', 'wb') as key_file:
        key_file.write(private_key)
    os.chmod('ubuntu_ssh_key.pem', 0o600)

    print("Pulling Ubuntu image...")
    client.images.pull('ubuntu:latest')

    print("Creating and starting Ubuntu container...")
    container = client.containers.run(
        'ubuntu:latest',
        name='ubuntu-ssh',
        detach=True,
        tty=True,
        ports={'22/tcp': None},
        command="/bin/bash"
    )

    print("Installing and configuring SSH...")
    container.exec_run("apt-get update")
    container.exec_run("apt-get install -y openssh-server")
    container.exec_run("mkdir -p /var/run/sshd")
    container.exec_run("mkdir -p /root/.ssh")

    # Add public key to authorized_keys
    container.exec_run("touch /root/.ssh/authorized_keys")
    container.exec_run(["sh", "-c", f"echo '{public_key.decode()}' > /root/.ssh/authorized_keys"])

    # Set correct permissions
    container.exec_run("chmod 700 /root/.ssh")
    container.exec_run("chmod 600 /root/.ssh/authorized_keys")

    # SSH 설정 수정
    container.exec_run(
        "sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config")
    container.exec_run("sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config")
    container.exec_run("sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config")

    print("Starting SSH service...")
    container.exec_run("service ssh restart")

    # 디버깅을 위한 로그 확인
    print("Checking SSH configuration:")
    print(container.exec_run("grep PasswordAuthentication /etc/ssh/sshd_config").output.decode())
    print(container.exec_run("grep PubkeyAuthentication /etc/ssh/sshd_config").output.decode())
    print(container.exec_run("grep PermitRootLogin /etc/ssh/sshd_config").output.decode())

    print("\nChecking authorized_keys:")
    print(container.exec_run("cat /root/.ssh/authorized_keys").output.decode())

    print("\nChecking permissions:")
    print(container.exec_run("ls -la /root/.ssh").output.decode())

    print("\nChecking SSH service status:")
    print(container.exec_run("service ssh status").output.decode())

    container_info = client.api.inspect_container(container.id)
    ip_address = container_info['NetworkSettings']['IPAddress']
    port_info = container_info['NetworkSettings']['Ports']['22/tcp'][0]
    host_port = port_info['HostPort']

    print(f"\nContainer '{container.name}' is ready.")
    print(f"Container IP: {ip_address}")
    print(f"SSH Port on Host: {host_port}")
    print(f"You can now connect via SSH using:")
    print(f"ssh -i ubuntu_ssh_key.pem root@localhost -p {host_port}")

    # SSH 로그 확인 (문제 해결에 도움이 될 수 있음)
    print("\nLast 10 lines of SSH log:")
    print(container.exec_run("tail -n 10 /var/log/auth.log").output.decode())

    return container, ip_address, host_port

if __name__ == "__main__":
    public_ip = get_public_ip()

    if public_ip == GET_IP_FAILED:
        print("Failed to get public IP address.")
        exit(1)

    private_ip, gateway_ip, interface = get_network_info()

    container, ip, port = create_ubuntu_ssh_container()
    gateway_manager_url = f"http://{gateway_ip}"
    print("\nContainer is running. Press Ctrl+C to stop and remove the container.")
    print(f"Connect to the container via SSH using: ssh -i ubuntu_ssh_key.pem root@localhost -p {port}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping and removing container...")
        container.stop()
        container.remove()
        print("Container stopped and removed.")