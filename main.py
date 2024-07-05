import docker
import requests
import netifaces
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from flask import Flask, send_file
import threading
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import socket
from waitress.server import create_server


app = Flask(__name__)

PRIVATE_KEY_PATH = 'ubuntu_ssh_key.pem'
public_key : bytes
download_count = 0
server_thread = None
stop_server = threading.Event()
GET_IP_FAILED = "Error: Unable to get IP"

def initialize_driver(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("detach", True)

    try:
        driver = webdriver.Chrome(options=chrome_options)

        driver.implicitly_wait(3)

        driver.get(url=url)

        return driver
    except Exception as e:
        print("An error occurred while initializing the driver.")
        print(e)
        exit(1)

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

    with open(PRIVATE_KEY_PATH, 'wb') as key_file:
        key_file.write(private_key)
    os.chmod(PRIVATE_KEY_PATH, 0o600)

    return private_key, public_key

@app.route('/download_key')
def download_key():
    global download_count
    if download_count == 0:
        download_count += 1
        return send_file(PRIVATE_KEY_PATH, as_attachment=True)
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

def create_port_forwarding(url, password, private_ip, port, server_port):
    driver = initialize_driver(url)

    password_input = driver.find_element(By.XPATH, "//*[@type='password']")

    password_input.send_keys(password)

    btn = driver.find_element(By.XPATH, "//*[@title='LOG IN']")

    btn.click()

    parent_element = driver.find_element(By.CSS_SELECTOR, '[navi-value="advanced"]')
    advanced_nav = parent_element.find_element(By.TAG_NAME, "a")
    advanced_nav.click()

    parent_element2 = driver.find_element(By.CSS_SELECTOR, '[navi-value="nat"]')
    parent_element2.click()
    port_forwarding_nav = parent_element2.find_element(By.CSS_SELECTOR, '[navi-value="portForwarding"]')
    port_forwarding_nav.click()

    add_btn = driver.find_element(By.CSS_SELECTOR, 'div#port-forwarding-grid_bar.operation-container')
    add_btn.click()

    server_name = driver.find_element(By.XPATH,
                                      '//*[@label-field="{PORT_FORWARDING.SERVICE_NAME}"]/div[2]/div[1]/span[2]/input')
    server_name.send_keys("backend")

    ip = driver.find_element(By.XPATH,
                             '//*[@label-field="{PORT_FORWARDING.DEVICE_IP_ADDRESS}"]/div[2]/div[1]/span[2]/input')
    ip.send_keys(private_ip)

    ex_port = driver.find_element(By.XPATH, '//*[@id="port-forwarding-external-port"]/div[2]/div[1]/span[2]/input')
    in_port = driver.find_element(By.XPATH, '//*[@id="port-forwarding-internal-port"]/div[2]/div[1]/span[2]/input')

    ex_port.send_keys(port)
    in_port.send_keys(port)

    driver.find_element(By.XPATH, '//*[@id="port-forwarding-grid-save-button"]/div[2]/div[1]/a').click()

    add_btn.click()

    server_name = driver.find_element(By.XPATH,
                                      '//*[@label-field="{PORT_FORWARDING.SERVICE_NAME}"]/div[2]/div[1]/span[2]/input')
    server_name.send_keys("key")

    ip = driver.find_element(By.XPATH,
                             '//*[@label-field="{PORT_FORWARDING.DEVICE_IP_ADDRESS}"]/div[2]/div[1]/span[2]/input')
    ip.send_keys(private_ip)

    ex_port = driver.find_element(By.XPATH, '//*[@id="port-forwarding-external-port"]/div[2]/div[1]/span[2]/input')
    in_port = driver.find_element(By.XPATH, '//*[@id="port-forwarding-internal-port"]/div[2]/div[1]/span[2]/input')

    ex_port.send_keys(server_port)
    in_port.send_keys(server_port)

    driver.find_element(By.XPATH, '//*[@id="port-forwarding-grid-save-button"]/div[2]/div[1]/a').click()

    driver.quit()


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


def delete_port_forwarding(url, password):
    driver = initialize_driver(url)

    password_input = driver.find_element(By.XPATH, "//*[@type='password']")

    password_input.send_keys(password)

    btn = driver.find_element(By.XPATH, "//*[@title='LOG IN']")

    btn.click()

    parent_element = driver.find_element(By.CSS_SELECTOR, '[navi-value="advanced"]')
    advanced_nav = parent_element.find_element(By.TAG_NAME, "a")
    advanced_nav.click()

    parent_element2 = driver.find_element(By.CSS_SELECTOR, '[navi-value="nat"]')
    parent_element2.click()
    port_forwarding_nav = parent_element2.find_element(By.CSS_SELECTOR, '[navi-value="portForwarding"]')
    port_forwarding_nav.click()

    delete_btns = driver.find_elements(By.XPATH, '//a[@class="grid-content-btn grid-content-btn-delete btn-delete"]')
    while len(delete_btns) > 0:
        delete_btns[0].click()
        time.sleep(1)
        delete_btns = driver.find_elements(By.XPATH,
                                           '//a[@class="grid-content-btn grid-content-btn-delete btn-delete"]')

    driver.quit()


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
    print(f"After downloading, you can connect via SSH using:")
    print(f"ssh -i {PRIVATE_KEY_PATH} root@localhost -p {host_port}")

    return container, ip_address, host_port


if __name__ == "__main__":
    generate_ssh_key()
    public_ip = get_public_ip()


    if public_ip == GET_IP_FAILED:
        print("Failed to get public IP address.")
        exit(1)

    private_ip, gateway_ip, interface = get_network_info()

    password = input("Enter the password for the gateway:")

    server_port = find_available_port()
    print(f"Flask server will run on port: {server_port}")
    # Flask 서버 시작
    server_thread = threading.Thread(target=run_flask_server, args=(server_port,))
    server_thread.start()

    print(f"You can now download the private key from: http://{public_ip}:{server_port}/download_key")

    container, ip, port = create_ubuntu_ssh_container()
    gateway_manager_url = f"http://{gateway_ip}"


    create_port_forwarding(gateway_manager_url, password, private_ip, port, server_port)
    print("\nContainer is running. Press Ctrl+C to stop and remove the container.")
    print(f"Connect to the container via SSH using: ssh root@{public_ip} -p {port}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        delete_port_forwarding(gateway_manager_url, password)
        print("\nStopping and removing container...")
        container.stop()
        container.remove()
        print("Container stopped and removed.")

        print("Cleaning up...")
        os.remove(PRIVATE_KEY_PATH)
        print("Private key file removed.")

        print("Exiting program...")
        os._exit(0)
