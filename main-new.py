import docker
import time
import ipaddress
import netifaces


def get_host_network_info():
    gateways = netifaces.gateways()
    default_interface = gateways['default'][netifaces.AF_INET][1]
    interface_info = netifaces.ifaddresses(default_interface)[netifaces.AF_INET][0]
    ip = interface_info['addr']
    netmask = interface_info['netmask']
    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
    return str(network), default_interface

def create_ipvlan_network(client, network_name, subnet, parent_interface):
    try:
        return client.networks.get(network_name)
    except docker.errors.NotFound:
        return client.networks.create(
            network_name,
            driver="ipvlan",
            ipam=docker.types.IPAMConfig(
                pool_configs=[docker.types.IPAMPool(subnet=subnet)]
            ),
            options={
                "ipvlan_mode": "l2",
                "parent": parent_interface
            }
        )

def create_ubuntu_ssh_container():
    client = docker.from_env(timeout=180)

    # 호스트 네트워크 정보 가져오기
    host_subnet, parent_interface = get_host_network_info()
    network_name = "ipvlan_network"

    print("Host subnet:", host_subnet)
    print("Parent interface:", parent_interface)

    # IPvlan 네트워크 생성
    network = create_ipvlan_network(client, network_name, host_subnet, parent_interface)

    print("Pulling Ubuntu image...")
    client.images.pull('ubuntu:latest')

    print("Creating and starting Ubuntu container...")
    try:
        container = client.containers.run(
            'ubuntu:latest',
            name='ubuntu-ssh',
            detach=True,
            tty=True,
            network=network_name,
            command="/bin/bash"
        )
    except docker.errors.APIError as e:
        print(f"Error creating container: {e}")
        raise

    print("Installing and configuring SSH...")
    container.exec_run("apt-get update")
    container.exec_run("apt-get install -y openssh-server")
    container.exec_run("mkdir /var/run/sshd")

    # SSH 설정
    password = "TestPassword123!"
    container.exec_run(f"bash -c \"echo 'root:{password}' | chpasswd\"")
    container.exec_run("sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config")
    container.exec_run("sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config")

    print("Starting SSH service...")
    container.exec_run("/usr/sbin/sshd")

    # 컨테이너 IP 주소 가져오기
    container.reload()
    container_ip = container.attrs['NetworkSettings']['Networks'][network_name]['IPAddress']

    print(f"\nContainer '{container.name}' is ready.")
    print(f"Container IP: {container_ip}")
    print(f"SSH Port: 22")
    print(f"You can now connect via SSH using:")
    print(f"ssh root@{container_ip}")
    print(f"Password: {password}")

    return container, container_ip, 22


if __name__ == "__main__":
    container, ip, port = create_ubuntu_ssh_container()
    print("\nContainer is running. Press Ctrl+C to stop and remove the container.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping and removing container...")
        container.stop()
        container.remove()
        print("Container stopped and removed.")