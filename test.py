import docker
import time
import socket


def create_ubuntu_ssh_container():
    client = docker.from_env()

    print("Pulling Ubuntu image...")
    client.images.pull('ubuntu:latest')

    print("Creating and starting Ubuntu container with host network...")
    container = client.containers.run(
        'ubuntu:latest',
        name='ubuntu-ssh',
        detach=True,
        tty=True,
        network_mode='host',
        command="/bin/bash",
        privileged=True
    )

    print("Installing and configuring SSH...")
    container.exec_run("apt-get update")
    container.exec_run("apt-get install -y openssh-server")
    container.exec_run("mkdir /var/run/sshd")

    # 명시적인 비밀번호 설정
    password = "TestPassword123!"
    result = container.exec_run(f"bash -c \"echo 'root:{password}' | chpasswd\"")
    print("Password set result:", result.output.decode())

    # SSH 설정 수정
    container.exec_run("sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config")
    container.exec_run("sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config")

    # SSH 포트를 8080으로 변경
    container.exec_run("sed -i 's/#Port 22/Port 8080/' /etc/ssh/sshd_config")

    print("Starting SSH service...")
    container.exec_run("/usr/sbin/sshd")

    # 호스트 IP 주소 가져오기
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    print(f"\nContainer '{container.name}' is ready.")
    print(f"Host IP: {ip_address}")
    print(f"SSH Port: 8080")
    print(f"You can now connect via SSH using:")
    print(f"ssh -p 8080 root@{ip_address}")
    print(f"Password: {password}")

    return container, ip_address


if __name__ == "__main__":
    container, ip = create_ubuntu_ssh_container()
    print("\nContainer is running. Press Ctrl+C to stop and remove the container.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping and removing container...")
        container.stop()
        container.remove()
        print("Container stopped and removed.")