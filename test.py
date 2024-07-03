import docker
import os
import socket
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from flask import Flask, send_file
import threading
import time
import sys
from waitress.server import create_server

app = Flask(__name__)

private_key_path = 'ubuntu_ssh_key.pem'
public_key = None
download_count = 0
server_thread = None
stop_server = threading.Event()


def generate_ssh_key():
    global public_key
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

    with open(private_key_path, 'wb') as key_file:
        key_file.write(private_key)
    os.chmod(private_key_path, 0o600)

    return private_key, public_key


@app.route('/download_key')
def download_key():
    global download_count
    if download_count == 0:
        download_count += 1
        return send_file(private_key_path, as_attachment=True)
    else:
        return "Key has already been downloaded", 403


def find_available_port(start_port=5000, max_port=65535):
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                continue
    raise IOError("No free ports")


def run_flask_server(port):
    def shutdown_server():
        server = create_server(app, host='0.0.0.0', port=port)
        threading.Thread(target=server.run).start()
        stop_server.wait()
        server.close()

    shutdown_server()


def create_ubuntu_ssh_container(flask_port):
    client = docker.from_env()

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

    # authorized_keys 파일 생성 및 공개 키 추가
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
    print(f"You can now download the private key from: http://localhost:{flask_port}/download_key")
    print(f"After downloading, you can connect via SSH using:")
    print(f"ssh -i {private_key_path} root@localhost -p {host_port}")

    return container, ip_address, host_port


if __name__ == "__main__":
    generate_ssh_key()

    flask_port = find_available_port()
    print(f"Flask server will run on port: {flask_port}")

    container, ip, port = create_ubuntu_ssh_container(flask_port)

    # Flask 서버 시작
    server_thread = threading.Thread(target=run_flask_server, args=(flask_port,))
    server_thread.start()

    print("\nContainer is running. Press Ctrl+C to stop and remove the container.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping and removing container...")
        container.stop()
        container.remove()
        print("Container stopped and removed.")

        print("Cleaning up...")
        os.remove(private_key_path)
        print("Private key file removed.")

        print("Exiting program...")
        os._exit(0)
