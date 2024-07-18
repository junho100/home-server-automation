from flask import Flask, send_file
import threading
import os
from waitress.server import create_server
import time

from network.ip import get_public_ip, get_network_info, find_available_port
from network.port_forwarding import create_port_forwarding, delete_port_forwarding
from crypto.ssh import generate_ssh_key
from container_vm import create_ubuntu_ssh_container

app = Flask(__name__)

download_count = 0
server_thread = None
stop_server = threading.Event()
GET_IP_FAILED = "Error: Unable to get IP"
PRIVATE_KEY_PATH = 'ubuntu_ssh_key.pem'

@app.route('/key')
def download_key():
    global download_count
    if download_count == 0:
        download_count += 1
        return send_file(PRIVATE_KEY_PATH, as_attachment=True)
    else:
        return "Key has already been downloaded", 403

def run_flask_server(port):
    def shutdown_server():
        server = create_server(app, host='0.0.0.0', port=port)
        threading.Thread(target=server.run).start()
        stop_server.wait()
        server.close()

    shutdown_server()

if __name__ == "__main__":
    password = input("Enter the password for the gateway:")

    print("Getting network information...")
    public_ip = get_public_ip()

    if public_ip == GET_IP_FAILED:
        print("Failed to get public IP address.")
        exit(1)

    print("Generating SSH crypto...")
    public_key = generate_ssh_key(PRIVATE_KEY_PATH)

    print("Getting network information...")
    private_ip, gateway_ip = get_network_info()

    print("Finding available port...")
    server_port = find_available_port()

    print(f"Flask server will run on port: {server_port}")
    server_thread = threading.Thread(target=run_flask_server, args=(server_port,))
    server_thread.start()

    print(f"You can now download the private crypto from: http://{public_ip}:{server_port}/key")

    print("Creating and starting Ubuntu docker...")
    container, ip, port = create_ubuntu_ssh_container(public_key)
    gateway_manager_url = f"http://{gateway_ip}"

    print("Creating port forwarding rules...")
    create_port_forwarding(gateway_manager_url, password, private_ip, port, server_port)
    print("\nContainer is running. Press Ctrl+C to stop and remove the docker.")
    print(f"Connect to the docker via SSH using: ssh -i {PRIVATE_KEY_PATH} ubuntu@{public_ip} -p {port}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCleaning up...")
        delete_port_forwarding(gateway_manager_url, password)
        print("\nStopping and removing docker...")
        container.stop()
        container.remove()
        print("Container stopped and removed.")

        print("Cleaning up...")
        os.remove(PRIVATE_KEY_PATH)
        print("Private crypto file removed.")

        print("Exiting program...")
        os._exit(0)
