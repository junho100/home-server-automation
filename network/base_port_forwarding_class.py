import abc

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class BasePortForwarding:

    def __init__(self, url):
        self.url = url
        self.driver = self._initialize_driver()

    def _initialize_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option("detach", True)

        try:
            driver = webdriver.Chrome(options=chrome_options)

            driver.implicitly_wait(3)

            driver.get(url=self.url)

            return driver
        except Exception as e:
            raise RuntimeError(f"Failed to initialize driver: {e}")

    @abc.abstractmethod
    def create_port_forwarding(self, password, private_ip, port, server_port):
        raise NotImplementedError("method `create_port_forwarding` should be implemented")

    @abc.abstractmethod
    def delete_port_forwarding(self, password):
        raise NotImplementedError("method `delete_port_forwarding` should be implemented")

