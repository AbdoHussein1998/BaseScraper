from selenium import webdriver
from seleniumwire import webdriver as webdriver_wire
from bs4.element import Tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from loguru import logger
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from typing import Optional

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
    """
    BaseScraper provides a reusable foundation for Selenium-based web scraping.

    This class encapsulates:
    - Selenium WebDriver initialization (standard or Selenium Wire)
    - Browser configuration and anti-detection options
    - Explicit wait utilities (short and long waits)
    - Human-like interaction helpers (scrolling, random sleep)
    - Robust element-finding helpers with retry and fallback logic
    - BeautifulSoup integration for HTML parsing

    The class is designed to be inherited by site-specific scrapers,
    ensuring consistent driver setup, logging, and error handling.
    """
    def __init__(self, wire:bool=False, headless:bool=False, short_wait_duration=20, long_wait_duration=120):
        self.soup = None
        self.headless = headless
        self.logger = logger
        self.ua = UserAgent(os="windows")
        self.options = Options()
        self.driver = None
        self.wire = wire
        self.long_wait_duration = long_wait_duration
        self.short_wait_duration = short_wait_duration
        
        # Separate caches for primary and secondary locator
        self.primary_locator = None
        self.secondary_locator = None
            
    def set_options(self):
        try:
            self.logger.info("Setting options for webdriver")

            # ===============================
            # 🧠 Core
            # ===============================
            if self.headless is True:
                self.options.add_argument("--headless=new")

            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--disable-software-rasterizer")
            self.options.add_argument("--disable-dev-shm-usage")
            self.options.add_argument("--no-sandbox")

            # ===============================
            # 🕵️ Stealth
            # ===============================
            self.options.add_argument(f"user-agent={self.ua.random}")
            self.options.add_argument("--disable-blink-features=AutomationControlled")
            self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self.options.add_experimental_option("useAutomationExtension", False)

            # ===============================
            # 🚫 Background / Chrome Noise
            # ===============================
            self.options.add_argument("--disable-background-networking")
            self.options.add_argument("--disable-sync")
            self.options.add_argument("--disable-translate")
            self.options.add_argument("--disable-default-apps")
            self.options.add_argument("--disable-extensions")

            # ===============================
            # 🖼️ Kill Rendering (JS SAFE)
            # ===============================
            self.options.add_argument("--blink-settings=imagesEnabled=false")

            # ===============================
            # 🔥 Content Settings (XHR SAFE)
            # ===============================
            prefs = {
                # Visuals
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.fonts": 2,
                "profile.managed_default_content_settings.stylesheets": 2,

                # Media
                "profile.managed_default_content_settings.video": 2,
                "profile.managed_default_content_settings.sound": 2,

                # Popups / noise
                "profile.managed_default_content_settings.popups": 2,
                "profile.managed_default_content_settings.notifications": 2,

                # APIs / hardware
                "profile.managed_default_content_settings.geolocation": 2,
                "profile.managed_default_content_settings.media_stream": 2,
                "profile.managed_default_content_settings.media_stream_mic": 2,
                "profile.managed_default_content_settings.media_stream_camera": 2,
                "profile.managed_default_content_settings.usb": 2,
                "profile.managed_default_content_settings.serial": 2,
                "profile.managed_default_content_settings.bluetooth": 2,
                "profile.managed_default_content_settings.midi_sysex": 2,

                # KEEP JS
                "profile.managed_default_content_settings.javascript": 1,

                # Tracking
                "profile.managed_default_content_settings.cookies": 2,
                "profile.managed_default_content_settings.third_party_cookies": 2,

                # Misc
                "profile.managed_default_content_settings.automatic_downloads": 2,
                "profile.managed_default_content_settings.payment_handler": 2,
            }

            self.options.add_experimental_option("prefs", prefs)

            # ===============================
            # 🧪 Selenium-Wire Mode
            # ===============================
            if self.wire is True:
                self.options.add_argument("--disable-web-security")
                self.options.add_argument("--allow-running-insecure-content")
                self.options.add_argument("--ignore-certificate-errors")

                self.options.set_capability(
                    "goog:loggingPrefs",
                    {
                        "performance": "ALL"  # browser/driver removed to reduce overhead
                    }
                )

            self.logger.info("Options set successfully")

        except Exception as e:
            self.logger.error(f"Error setting options: {e}")
    def start(self):
        if not self.driver:
            self.init_driver()
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
            self.long_wait = WebDriverWait(self.driver, timeout=self.long_wait_duration)
            self.short_wait = WebDriverWait(self.driver, timeout=self.short_wait_duration)
            self.action = ActionChains(self.driver)
            self.driver.command_executor._client_config.timeout = 300
            self.logger.info("Driver initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing driver: {e}")
            raise

    def make_soup(self,page_source):
        self.soup = BeautifulSoup(page_source, 'html5lib')
        return self.soup   

    def random_sleep(self,min_s=1.2, max_s=2.8):
        time.sleep(random.uniform(min_s, max_s))

    def human_scroling_by_action(self,delt_x=0,delt_y=1163):
        self.action.scroll_by_amount(delt_x, delt_y).perform()
        time.sleep(.6)
        self.action.scroll_by_amount(delt_x, -123).perform()
        
    def extract_soup_elemnt(self,main_elemnt: Tag,extractor: tuple,second_extractor: Optional[tuple] = None,name: Optional[str] = None) -> Tag:
        """
        Extract a single element from the soup with optional fallback extractor.
        
        Args:
            main_elemnt: The parent element to search within
            extractor: Primary tuple extractor
            second_extractor: Optional fallback tuple extractor
            name: Optional name for logging purposes
        
        Returns:
            Found Tag element or default BeautifulSoup span
        """
        log_name = name or str(extractor)
        
        self.logger.info(f"Extracting the main elemnt from the soup {log_name}")
        
        # Try primary extractor
        found = main_elemnt.find(*extractor)
        if found:
            self.logger.success(f"[SUCCESS] Found the main elemnt using primary extractor: {log_name}")
            return found
        
        self.logger.debug(f"Primary extractor failed: {extractor}")
        
        # Try second extractor if provided
        if second_extractor:
            found = main_elemnt.find(*second_extractor)
            if found:
                self.logger.success(f"[SUCCESS] Found the main elemnt using secondary extractor: {log_name}")
                return found
            self.logger.debug(f"Secondary extractor failed: {second_extractor}")
        
        # All extractors failed
        self.logger.warning(f"[WARNING] All extractors failed for: {log_name}")
        return BeautifulSoup("<span>None</span>", "html5lib")

    def extract_soup_elemnts(self,main_elemnt: BeautifulSoup | Tag,extractor: tuple,second_extractor: Optional[tuple] = None,name: Optional[str] = None
    ) -> list[Tag]:
        """
        Extract multiple elements from the soup with optional fallback extractor.
        
        Args:
            main_elemnt: The parent element to search within
            extractor: Primary tuple extractor
            second_extractor: Optional fallback tuple extractor
            name: Optional name for logging purposes
        
        Returns:
            List of found Tag elements or default list with BeautifulSoup span
        """
        log_name = name or str(extractor)
        
        self.logger.info(f"Extracting the main elemnts from the soup {log_name}")
        
        # Try primary extractor
        found = main_elemnt.find_all(*extractor)
        if found:
            self.logger.success(f"[SUCCESS] Found {len(found)} elemnt(s) using primary extractor: {log_name}")
            return found
        
        self.logger.debug(f"Primary extractor failed: {extractor}")
        
        # Try second extractor if provided
        if second_extractor:
            found = main_elemnt.find_all(*second_extractor)
            if found:
                self.logger.success(f"[SUCCESS] Found {len(found)} elemnt(s) using secondary extractor: {log_name}")
                return found
            self.logger.debug(f"Secondary extractor failed: {second_extractor}")
        
        # All extractors failed
        self.logger.warning(f"[WARNING] All extractors failed for: {log_name}")
        return [BeautifulSoup("<span>None</span>", "html5lib")]
        
    def discover_and_cache_locator_primary(self, name: str, first: tuple, second: tuple = None, n_retry: int = 3) -> tuple | None:
        self.logger.info(f"[PRIMARY DISCOVERY] Testing locator for: {name}")
        for trial in range(1, n_retry + 1):
            try:
                self.short_wait.until(EC.visibility_of_element_located(first))
                self.primary_locator = first
                return first
            except (TimeoutException, NoSuchElementException):
                pass
            if second:
                try:
                    self.short_wait.until(EC.visibility_of_element_located(second))
                    self.primary_locator = second
                    return second
                except (TimeoutException, NoSuchElementException):
                    pass
            time.sleep(1)
        return None

    def discover_and_cache_locator_secondary(self, main_element: WebElement, name: str, first: tuple, second: tuple = None, n_retry: int = 3) -> tuple | None:
        self.random_sleep(min_s=1.5,max_s=3)
        for trial in range(1, n_retry + 1):
            try:
                if main_element.find_elements(*first):
                    self.secondary_locator = first
                    return first
            except Exception:
                pass
            if second:
                try:
                    if main_element.find_elements(*second):
                        self.secondary_locator = second
                        return second
                except Exception:
                    pass
            time.sleep(1)
        return None

    def selenium_find_one_element_with_retry(self, first: tuple, second: tuple = None, name: str = None) -> WebElement | None:
        if not name:
            return None
        if self.primary_locator not in [first,second]:
            if not self.discover_and_cache_locator_primary(name, first, second):
                return None
        try:
            return self.short_wait.until(EC.visibility_of_element_located(self.primary_locator))
        except TimeoutException:
            return None

    def selenium_find_multiple_elements_with_retry(self, first: tuple, second: tuple = None, name: str = None) -> list[WebElement]:
        if not name:
            return []
        if self.primary_locator not in [first,second]:
            if not self.discover_and_cache_locator_primary(name, first, second):
                return []
        try:
            return self.short_wait.until(EC.visibility_of_all_elements_located(self.primary_locator))
        except TimeoutException:
            return []

    def selenium_find_multiple_elements_within_main_element_with_retry(self, main_element: WebElement, first: tuple, second: tuple = None, name: str = None) -> list[WebElement]:
        if not name:
            return []
        if self.secondary_locator not in [first,second]:
            if not self.discover_and_cache_locator_secondary(main_element, name, first, second):
                return []
        try:
            return main_element.find_elements(*self.secondary_locator)
        except StaleElementReferenceException:
            return []

