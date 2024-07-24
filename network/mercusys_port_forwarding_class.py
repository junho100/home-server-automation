import time
from enum import Enum

from selenium.webdriver.common.by import By

from network.base_port_forwarding_class import BasePortForwarding

class SELECTORS(Enum):
    X_PATH_PASSWORD_INPUT = "//*[@type='password']",
    X_PATH_LOGIN_BTN = "//*[@title='LOG IN']",
    CSS_ADVANCED_NAV_PARENT = '[navi-value="advanced"]',
    CSS_NAT_NAV_PARENT = '[navi-value="nat"]',
    CSS_PORT_FORWARDING_NAV = '[navi-value="portForwarding"]',
    CSS_ADD_BTN = 'div#port-forwarding-grid_bar.operation-container',
    X_PATH_SERVICE_NAME_INPUT = '//*[@label-field="{PORT_FORWARDING.SERVICE_NAME}"]/div[2]/div[1]/span[2]/input',
    X_PATH_DEVICE_IP_INPUT = '//*[@label-field="{PORT_FORWARDING.DEVICE_IP_ADDRESS}"]/div[2]/div[1]/span[2]/input',
    X_PATH_EXTERNAL_PORT_INPUT = '//*[@id="port-forwarding-external-port"]/div[2]/div[1]/span[2]/input',
    X_PATH_INTERNAL_PORT_INPUT = '//*[@id="port-forwarding-internal-port"]/div[2]/div[1]/span[2]/input',
    X_PATH_SAVE_BTN = '//*[@id="port-forwarding-grid-save-button"]/div[2]/div[1]/a',
    X_PATH_DELETE_BTN = '//a[@class="grid-content-btn grid-content-btn-delete btn-delete"]'


class MercusysPortForwarding(BasePortForwarding):
    def __init__(self, url):
        super().__init__(url)

    def create_port_forwarding(self, password, private_ip, port, server_port):
        driver = self._initialize_driver()

        driver.find_element(By.XPATH, SELECTORS.X_PATH_PASSWORD_INPUT.value).send_keys(password)

        driver.find_element(By.XPATH, SELECTORS.X_PATH_LOGIN_BTN.value).click()

        advanced_nav_parent_element = driver.find_element(By.CSS_SELECTOR, SELECTORS.CSS_ADVANCED_NAV_PARENT.value)
        advanced_nav_parent_element.find_element(By.TAG_NAME, "a").click()

        nat_nav_parent_element = driver.find_element(By.CSS_SELECTOR, SELECTORS.CSS_NAT_NAV_PARENT.value)
        nat_nav_parent_element.click()

        nat_nav_parent_element.find_element(By.CSS_SELECTOR, SELECTORS.CSS_PORT_FORWARDING_NAV.value).click()

        add_btn = driver.find_element(By.CSS_SELECTOR, SELECTORS.CSS_ADD_BTN.value)
        add_btn.click()

        driver.find_element(By.XPATH, SELECTORS.X_PATH_SERVICE_NAME_INPUT.value).send_keys("backend")

        driver.find_element(By.XPATH, SELECTORS.X_PATH_DEVICE_IP_INPUT.value).send_keys(private_ip)

        driver.find_element(By.XPATH, SELECTORS.X_PATH_EXTERNAL_PORT_INPUT.value).send_keys(port)
        driver.find_element(By.XPATH, SELECTORS.X_PATH_INTERNAL_PORT_INPUT.value).send_keys(port)

        driver.find_element(By.XPATH, SELECTORS.X_PATH_SAVE_BTN.value).click()

        add_btn.click()

        driver.find_element(By.XPATH, SELECTORS.X_PATH_SERVICE_NAME_INPUT.value).send_keys("crypto")

        driver.find_element(By.XPATH, SELECTORS.X_PATH_DEVICE_IP_INPUT.value).send_keys(private_ip)

        driver.find_element(By.XPATH, SELECTORS.X_PATH_EXTERNAL_PORT_INPUT.value).send_keys(server_port)
        driver.find_element(By.XPATH, SELECTORS.X_PATH_INTERNAL_PORT_INPUT.value).send_keys(server_port)

        driver.find_element(By.XPATH, SELECTORS.X_PATH_SAVE_BTN.value).click()

        driver.quit()

    def delete_port_forwarding(self, password):
        driver = self._initialize_driver()

        driver.get(url=self.url)

        driver.find_element(By.XPATH, SELECTORS.X_PATH_PASSWORD_INPUT.value).send_keys(password)

        driver.find_element(By.XPATH, SELECTORS.X_PATH_LOGIN_BTN.value).click()

        advanced_nav_parent_element = driver.find_element(By.CSS_SELECTOR, SELECTORS.CSS_ADVANCED_NAV_PARENT.value)
        advanced_nav_parent_element.find_element(By.TAG_NAME, "a").click()

        nat_nav_parent_element = driver.find_element(By.CSS_SELECTOR, SELECTORS.CSS_NAT_NAV_PARENT.value)
        nat_nav_parent_element.click()
        nat_nav_parent_element.find_element(By.CSS_SELECTOR, SELECTORS.CSS_PORT_FORWARDING_NAV.value).click()

        delete_btns = driver.find_elements(By.XPATH, SELECTORS.X_PATH_DELETE_BTN.value)
        while len(delete_btns) > 0:
            delete_btns[0].click()
            time.sleep(1)
            delete_btns = driver.find_elements(By.XPATH, SELECTORS.X_PATH_DELETE_BTN.value)

        driver.quit()