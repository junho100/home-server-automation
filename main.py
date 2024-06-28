import docker
import requests
import netifaces
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


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


def create_port_forwarding(url, password, private_ip, port):
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
    return "Error: Unable to get IP"


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
    public_ip = get_public_ip()
    private_ip, gateway_ip, interface = get_network_info()

    password = input("Enter the password for the gateway:")
    container, ip, port = create_ubuntu_ssh_container()
    gateway_manager_url = f"http://{gateway_ip}"
    create_port_forwarding(gateway_manager_url, password, private_ip, port)
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
