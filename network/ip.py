import netifaces
import socket
import requests

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

    return private_ip, gateway_ip

def find_available_port(start_port=5000, max_port=65535):
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                continue
    raise IOError("No free ports")

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
    raise RuntimeError("Failed to get public IP address")
