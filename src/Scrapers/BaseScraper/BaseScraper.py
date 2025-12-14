from selenium import webdriver
from seleniumwire import webdriver as webdriver_wire

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from loguru import logger
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time
import random
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    WebDriverException
)
from selenium.webdriver.remote.webelement import WebElement

class BaseScraper:
    def __init__(self,wire:bool=False,headless:bool=False):
        self.soup=None
        self.headless=headless
        self.logger = logger
        self.ua = UserAgent(os="windows")
        self.options = Options()
        self.driver = None
        self.wire=wire
        self.wait = None      
        self.init_driver()
    def set_options(self):
        try:
            self.logger.info("Setting options for webdriver")
            if self.headless==True:
                self.options.add_argument("--headless")
            self.options.add_argument(f"user-agent={self.ua.random}")
            self.options.add_argument("--disable-blink-features=AutomationControlled")
            self.options.add_argument('--no-sandbox')
            self.options.add_argument('--disable-dev-shm-usage')
            self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self.options.add_experimental_option('useAutomationExtension', False)
            self.options.set_capability('goog:loggingPrefs', {
                                                            'browser': 'ALL',
                                                            'driver': 'ALL',
                                                            'performance': 'ALL'
                                                            })
            self.logger.info("Options set successfully")
        except Exception as e:
            self.logger.error(f"Error setting options: {e}")
    def init_driver(self):
        try:
            self.logger.info("Initializing driver")
            self.set_options()
            if self.wire == True:
                self.driver = webdriver_wire.Chrome(options=self.options)
            else:
                self.driver = webdriver.Chrome(options=self.options)
            self.driver.execute_cdp_cmd("Network.enable", {})
            self.driver.execute_cdp_cmd("Log.enable", {})
            self.long_wait = WebDriverWait(self.driver, timeout=120)
            self.short_wait = WebDriverWait(self.driver, timeout=20)
            self.action = ActionChains(self.driver)
            self.logger.info("Driver initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing driver: {e}")
            raise
    def make_soup(self,page_source):
        self.soup = BeautifulSoup(page_source, 'html5lib')
        return self.soup   
    def random_sleep(self,min_s=1.2, max_s=2.8):
        time.sleep(random.uniform(min_s, max_s))
    def human_scroling_by_action(self,delt_x=0,delt_y=1000):
        self.action.scroll_by_amount(delt_x, delt_y).perform()
        time.sleep(.6)
        self.action.scroll_by_amount(delt_x, -50).perform()
    def _find_one_element_with_retry(self, first:tuple,n_retry:int=3, second:tuple=None, name:str=None)->WebElement:
        for trial in range(n_retry):    
            try:
                self.logger.info(f"Finding element {name if name else first}")
                return self.short_wait.until(EC.element_located_to_be_selected(first))
            except (StaleElementReferenceException,Exception,TimeoutException) as e:
                self.logger.warning(f"First version failed: {e}")
                self.logger.info("Trying Second Version")
                if second:
                    try:
                        self.logger.info(f"Finding element {name if name else second}")
                        return self.short_wait.until(EC.element_located_to_be_selected(second))
                    except (StaleElementReferenceException,Exception,TimeoutException) as e:
                        self.logger.error(f"Second version failed too: {e}")
                        self.logger.info(f"the trail number  {trial+1} is fialed")
                        self.human_scroling_by_action()
                        self.human_scroling_by_action(delt_x=0,delt_y=-1000) 
        return None
    def _find_multiple_elements_with_retry(self, main_element:WebElement, first:tuple,n_retry:int=3, second:tuple=None, name:str=None)->list[WebElement]:

        for trial in range(n_retry):
            try:
                self.logger.info(f"Finding element {name if name else first}")
                return main_element.find_elements(*first)
            except (StaleElementReferenceException, Exception, TimeoutException) as e:
                self.logger.warning(f"First version failed: {e}")
                self.logger.info("Trying Second Version")
                if second:
                    try:
                        self.logger.info(f"Finding element {name if name else second}")
                        return main_element.find_elements(*second)
                    except (StaleElementReferenceException, Exception, TimeoutException) as e:
                        self.logger.error(f"Second version failed too: {e}")
                        self.logger.info(f"the trail number  {trial+1} is fialed")
                        self.human_scroling_by_action()
                        self.human_scroling_by_action(delt_x=0, delt_y=-1000)
        return None
    
