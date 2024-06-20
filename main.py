import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import socket


def initialize_driver(url):
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=chrome_options)

    driver.implicitly_wait(3)

    driver.get(url=url)

    return driver


def create_port_forwarding(url, password):
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

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))

    ip = driver.find_element(By.XPATH,
                             '//*[@label-field="{PORT_FORWARDING.DEVICE_IP_ADDRESS}"]/div[2]/div[1]/span[2]/input')
    ip.send_keys(s.getsockname()[0])
    s.close()

    ex_port = driver.find_element(By.XPATH, '//*[@id="port-forwarding-external-port"]/div[2]/div[1]/span[2]/input')
    in_port = driver.find_element(By.XPATH, '//*[@id="port-forwarding-internal-port"]/div[2]/div[1]/span[2]/input')

    ex_port.send_keys("8080")
    in_port.send_keys("8080")

    driver.find_element(By.XPATH, '//*[@id="port-forwarding-grid-save-button"]/div[2]/div[1]/a').click()

    driver.quit()


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


if __name__ == '__main__':
    ip = input('Enter your ip address: ')
    user_password = input('Enter your password: ')

    op = input('Enter 1 to create port forwarding or 2 to delete port forwarding: ')

    if op == '1':
        create_port_forwarding(ip, user_password)
    elif op == '2':
        delete_port_forwarding(ip, user_password)
    else:
        print('Invalid input')
