import docker


def create_ubuntu_ssh_container(ssh_public_key):
    client = docker.from_env()

    print("Pulling Ubuntu image...")
    client.images.pull('ubuntu:latest')

    print("Creating and starting Ubuntu docker...")
    container = client.containers.run(
        'ubuntu:latest',
        name='ubuntu-ssh',
        detach=True,
        tty=True,
        ports={'22/tcp': None},
        command="/bin/bash",
        mem_limit='6g',
        volumes={"ubuntu_home": {'bind': "/home/ubuntu", 'mode': 'rw'}},
    )

    print("Installing and configuring SSH...")
    container.exec_run("apt-get update")
    container.exec_run("apt-get install -y openssh-server sudo")
    container.exec_run("mkdir -p /var/run/sshd")

    # 'ubuntu' 사용자 생성
    container.exec_run("useradd -m -d /home/ubuntu -s /bin/bash ubuntu")
    container.exec_run("chown -R ubuntu:ubuntu /home/ubuntu")

    # sudo 권한 부여 및 비밀번호 없이 root로 전환 가능하게 설정
    container.exec_run("bash -c \"echo 'ubuntu ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/ubuntu && chmod 0440 /etc/sudoers.d/ubuntu\"")

    # SSH 디렉토리 및 authorized_keys 파일 생성
    container.exec_run("mkdir -p /home/ubuntu/.ssh")
    container.exec_run("touch /home/ubuntu/.ssh/authorized_keys")
    container.exec_run(["sh", "-c", f"echo '{ssh_public_key.decode()}' > /home/ubuntu/.ssh/authorized_keys"])

    # 권한 설정
    container.exec_run("chown -R ubuntu:ubuntu /home/ubuntu/.ssh")
    container.exec_run("chmod 700 /home/ubuntu/.ssh")
    container.exec_run("chmod 600 /home/ubuntu/.ssh/authorized_keys")

    # SSH 설정 수정
    container.exec_run("sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config")
    container.exec_run("sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config")
    container.exec_run("sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config")

    print("Starting SSH service...")
    container.exec_run("service ssh restart")

    container_info = client.api.inspect_container(container.id)
    ip_address = container_info['NetworkSettings']['IPAddress']
    port_info = container_info['NetworkSettings']['Ports']['22/tcp'][0]
    host_port = port_info['HostPort']

    print(f"\nContainer '{container.name}' is ready.")
    print(f"Container IP: {ip_address}")
    print(f"SSH Port on Host: {host_port}")

    return container, ip_address, host_port

def clean_up_container(container):
    print("Stopping and removing docker...")
    container.stop()
    container.remove()