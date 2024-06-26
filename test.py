import docker
import time


def create_ubuntu_ssh_container():
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
    container.exec_run("apt-get install -y iputils-ping")
    container.exec_run("apt-get install -y net-tools")
    container.exec_run("mkdir /var/run/sshd")

    # 명시적인 비밀번호 설정
    password = "TestPassword123!"
    result = container.exec_run(f"bash -c \"echo 'root:{password}' | chpasswd\"")
    print("Password set result:", result.output.decode())

    # SSH 설정 수정
    container.exec_run("sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config")
    container.exec_run("sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config")

    print("Starting SSH service...")
    container.exec_run("/usr/sbin/sshd")

    container_info = client.api.inspect_container(container.id)
    ip_address = container_info['NetworkSettings']['IPAddress']
    port_info = container_info['NetworkSettings']['Ports']['22/tcp'][0]
    host_port = port_info['HostPort']

    print(f"\nContainer '{container.name}' is ready.")
    print(f"Container IP: {ip_address}")
    print(f"SSH Port on Host: {host_port}")
    print(f"You can now connect via SSH using:")
    print(f"ssh root@localhost -p {host_port}")
    print(f"Password: {password}")

    return container, ip_address, host_port


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