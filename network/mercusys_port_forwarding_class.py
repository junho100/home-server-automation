import time
from selenium.webdriver.common.by import By

from network.base_port_forwarding_class import BasePortForwarding


class MercusysPortForwarding(BasePortForwarding):
    def __init__(self, url):
        super().__init__(url)

    def create_port_forwarding(self, password, private_ip, port, server_port):
        driver = self.driver

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
        server_name.send_keys("crypto")

        ip = driver.find_element(By.XPATH,
                                 '//*[@label-field="{PORT_FORWARDING.DEVICE_IP_ADDRESS}"]/div[2]/div[1]/span[2]/input')
        ip.send_keys(private_ip)

        ex_port = driver.find_element(By.XPATH, '//*[@id="port-forwarding-external-port"]/div[2]/div[1]/span[2]/input')
        in_port = driver.find_element(By.XPATH, '//*[@id="port-forwarding-internal-port"]/div[2]/div[1]/span[2]/input')

        ex_port.send_keys(server_port)
        in_port.send_keys(server_port)

        driver.find_element(By.XPATH, '//*[@id="port-forwarding-grid-save-button"]/div[2]/div[1]/a').click()

        driver.quit()

    def delete_port_forwarding(self, password):
        driver = self.driver

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

        delete_btns = driver.find_elements(By.XPATH,
                                           '//a[@class="grid-content-btn grid-content-btn-delete btn-delete"]')
        while len(delete_btns) > 0:
            delete_btns[0].click()
            time.sleep(1)
            delete_btns = driver.find_elements(By.XPATH,
                                               '//a[@class="grid-content-btn grid-content-btn-delete btn-delete"]')

        driver.quit()