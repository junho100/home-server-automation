import time
from selenium.webdriver.common.by import By

from network.base_port_forwarding_class import BasePortForwarding


class MercusysPortForwarding(BasePortForwarding):
    def __init__(self, url):
        super().__init__(url)

    def create_port_forwarding(self, password, private_ip, port, server_port):
        driver = self._initialize_driver()

        driver.find_element(By.XPATH, "//*[@type='password']").send_keys(password)

        driver.find_element(By.XPATH, "//*[@title='LOG IN']").click()

        advanced_nav_parent_element = driver.find_element(By.CSS_SELECTOR, '[navi-value="advanced"]')
        advanced_nav_parent_element.find_element(By.TAG_NAME, "a").click()

        nat_nav_parent_element = driver.find_element(By.CSS_SELECTOR, '[navi-value="nat"]')
        nat_nav_parent_element.click()

        nat_nav_parent_element.find_element(By.CSS_SELECTOR, '[navi-value="portForwarding"]').click()

        add_btn = driver.find_element(By.CSS_SELECTOR, 'div#port-forwarding-grid_bar.operation-container')
        add_btn.click()

        driver.find_element(By.XPATH,
                                          '//*[@label-field="{PORT_FORWARDING.SERVICE_NAME}"]/div[2]/div[1]/span[2]/input').send_keys("backend")

        driver.find_element(By.XPATH,
                                 '//*[@label-field="{PORT_FORWARDING.DEVICE_IP_ADDRESS}"]/div[2]/div[1]/span[2]/input').send_keys(private_ip)

        driver.find_element(By.XPATH, '//*[@id="port-forwarding-external-port"]/div[2]/div[1]/span[2]/input').send_keys(port)
        driver.find_element(By.XPATH, '//*[@id="port-forwarding-internal-port"]/div[2]/div[1]/span[2]/input').send_keys(port)

        driver.find_element(By.XPATH, '//*[@id="port-forwarding-grid-save-button"]/div[2]/div[1]/a').click()

        add_btn.click()

        driver.find_element(By.XPATH,
                                          '//*[@label-field="{PORT_FORWARDING.SERVICE_NAME}"]/div[2]/div[1]/span[2]/input').send_keys("crypto")

        driver.find_element(By.XPATH,
                                 '//*[@label-field="{PORT_FORWARDING.DEVICE_IP_ADDRESS}"]/div[2]/div[1]/span[2]/input').send_keys(private_ip)

        driver.find_element(By.XPATH, '//*[@id="port-forwarding-external-port"]/div[2]/div[1]/span[2]/input').send_keys(server_port)
        driver.find_element(By.XPATH, '//*[@id="port-forwarding-internal-port"]/div[2]/div[1]/span[2]/input').send_keys(server_port)

        driver.find_element(By.XPATH, '//*[@id="port-forwarding-grid-save-button"]/div[2]/div[1]/a').click()

        driver.quit()

    def delete_port_forwarding(self, password):
        driver = self._initialize_driver()

        driver.get(url=self.url)

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