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

    Attributes:
        driver (webdriver.Chrome):
            The active Selenium WebDriver instance.
        soup (BeautifulSoup | None):
            Parsed HTML document created from the current page source.
        logger (loguru.logger):
            Logger instance used for structured logging.
        ua (fake_useragent.UserAgent):
            User-agent generator for browser fingerprint randomization.
        options (selenium.webdriver.chrome.options.Options):
            Chrome browser options.
        wire (bool):
            If True, initializes Selenium Wire driver instead of standard Selenium.
        headless (bool):
            If True, runs the browser in headless mode.
        short_wait (WebDriverWait):
            Short explicit wait instance.
        long_wait (WebDriverWait):
            Long explicit wait instance.
        action (ActionChains):
            ActionChains instance for advanced user interactions.

    Args:
        wire (bool, optional):
            Enable Selenium Wire for network inspection. Defaults to False.
        headless (bool, optional):
            Run Chrome in headless mode. Defaults to False.
        short_wait_duration (int, optional):
            Timeout (in seconds) for short waits. Defaults to 20.
        long_wait_duration (int, optional):
            Timeout (in seconds) for long waits. Defaults to 120.
    """
    def __init__(self,wire:bool=False,headless:bool=False,short_wait_duration=20,long_wait_duration=120):
        self.soup=None
        self.headless=headless
        self.logger = logger
        self.ua = UserAgent(os="windows")
        self.options = Options()
        self.driver = None
        self.wire=wire
        self.long_wait_duration=long_wait_duration
        self.short_wait_duration=short_wait_duration
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
            self.long_wait = WebDriverWait(self.driver, timeout=self.long_wait_duration)
            self.short_wait = WebDriverWait(self.driver, timeout=self.short_wait_duration)
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
        """
        Perform a human-like scroll action using Selenium ActionChains.

        This method scrolls the page vertically (and optionally horizontally)
        by a specified amount, pauses briefly to simulate natural user behavior,
        and then performs a small reverse scroll. This pattern helps reduce
        automation detection by mimicking realistic scrolling patterns.

        Args:
            delt_x (int, optional):
                Horizontal scroll offset in pixels. Defaults to 0.
            delt_y (int, optional):
                Vertical scroll offset in pixels. Defaults to 1000.

        Returns:
            None
        """
        self.action.scroll_by_amount(delt_x, delt_y).perform()
        time.sleep(.6)
        self.action.scroll_by_amount(delt_x, -50).perform()
    
    

    def extract_soup_elemnt(self,main_elemnt:Tag,extractor:tuple,name:Optional[str]=None)->Tag:
        """
        Extract a single element from a BeautifulSoup element using a selector.

        This method searches for the first matching element inside the provided
        BeautifulSoup tag using the given extractor. If the element is not found,
        a placeholder `<span>None</span>` element is returned to prevent
        downstream errors caused by `None` values.

        Args:
            main_elemnt (Tag):
                The BeautifulSoup tag within which the search is performed.
            extractor (tuple):
                A BeautifulSoup-compatible selector, typically in the form
                (tag_name, attributes_dict).
            name (Optional[str], optional):
                Human-readable name used for logging instead of the raw selector.

        Returns:
            Tag:
                The first matching BeautifulSoup Tag if found, otherwise a
                placeholder `<span>None</span>` tag.
        """        
        self.logger.info(f"Extracting the main elemnt from the soup {extractor if not name else name} ")
        found=main_elemnt.find(*extractor)
        if found:
            self.logger.success(f"[SUCCESS] We've Found the main elemnt from the soup {extractor if not name else name} ")
            return found
        else:
            self.logger.warning(f"[Warning] the elemnt with {main_elemnt} is not exited")
            return BeautifulSoup("<span>None</span>", "html5lib")
    def extract_soup_elemnts(self,main_elemnt:BeautifulSoup|Tag, extractor:tuple,name:Optional[str]=None)->list[Tag]:

        """
        Extract multiple elements from a BeautifulSoup document or tag.

        This method searches for all matching elements using the provided
        extractor. If no elements are found, a list containing a placeholder
        `<span>None</span>` element is returned to ensure consistent return types
        and avoid empty-list handling issues in calling code.

        Args:
            main_elemnt (BeautifulSoup | Tag):
                The BeautifulSoup document or tag within which the search is performed.
            extractor (tuple):
                A BeautifulSoup-compatible selector used to locate elements.
            name (Optional[str], optional):
                Human-readable name used for logging instead of the raw selector.

        Returns:
            list[Tag]:
                A list of matching BeautifulSoup Tags, or a list containing a
                placeholder `<span>None</span>` tag if no matches are found.
        """    
        self.logger.info(f"Extracting the main elemnts from the soup {extractor if not name else name}")
        found=main_elemnt.find_all(*extractor)
        if found:
            self.logger.success(f"[SUCESS] We've Found the main elemnts from the soup {extractor if not name else name}")
            return found
        else:
            self.logger.warning(f"[WARNING] the elemnts with main_elemnt is not exited = {extractor if not name else name}")
            return [BeautifulSoup("<span>None</span>", "html5lib")]


    def selenium_find_one_element_with_retry(self,first: tuple,n_retry: int = 3,second: tuple = None,name: str = None) -> WebElement | None:
        """
        Locate a single visible web element using explicit waits with retry support.

        This method attempts to find an element using a primary locator.
        If the element is not found within the short wait timeout, it optionally
        retries using a fallback locator. The process repeats for a defined
        number of retries with short delays between attempts.

        Args:
            first (tuple):
                Primary Selenium locator in the form (By, selector).
            n_retry (int, optional):
                Number of retry attempts before giving up. Defaults to 3.
            second (tuple, optional):
                Fallback Selenium locator used if the primary locator fails.
            name (str, optional):
                Human-readable element name for logging purposes.

        Returns:
            WebElement | None:
                The located WebElement if successful, otherwise None after
                exhausting all retries.
        """
        element_name = name or first

        for trial in range(1, n_retry + 1):
            try:
                self.logger.info(f"[TRY {trial}/{n_retry}] Finding element: {element_name} using {first}")
                element = self.short_wait.until(EC.visibility_of_element_located(first))
                self.logger.success(f"[SUCCESS] Element found: {element_name} on try {trial}")
                return element

            except TimeoutException:
                self.logger.warning(f"[TIMEOUT] First locator failed on try {trial}: {first}")

                if second:
                    try:
                        self.logger.info(f"[TRY {trial}/{n_retry}] Trying fallback locator: {second}")
                        element = self.short_wait.until(EC.visibility_of_element_located(second))
                        self.logger.success(f"[SUCCESS] Element found with fallback locator: {element_name}")
                        return element
                    except TimeoutException:
                        self.logger.warning(f"[TIMEOUT] Fallback locator failed on try {trial}: {second}")

            time.sleep(1)

        self.logger.error(
            f"[FAILED] Could not find element after {n_retry} retries: {element_name}"
        )
        return None
    def selenium_find_multiple_within_main_element_elements_with_retry(self,main_element: WebElement,first: tuple,n_retry: int = 3,second: tuple = None,name: str = None) -> list[WebElement]:
        """
        Locate multiple child elements within a parent WebElement with retry logic.

        This method searches for child elements inside a given parent element
        using a primary locator. If no elements are found, it optionally attempts
        a fallback locator. The method handles stale parent elements by retrying
        the operation multiple times.

        Args:
            main_element (WebElement):
                The parent element within which to search for child elements.
            first (tuple):
                Primary locator used to find child elements.
            n_retry (int, optional):
                Number of retry attempts. Defaults to 3.
            second (tuple, optional):
                Fallback locator used if the primary locator finds no elements.
            name (str, optional):
                Human-readable name for logging purposes.

        Returns:
            list[WebElement]:
                A list of located WebElements. Returns an empty list if no
                elements are found after all retries.
        """
        element_name = name or first
        for trial in range(1, n_retry + 1):
            self.logger.info(f"[TRY {trial}/{n_retry}] Finding child elements: {element_name}")

            try:
                elements = main_element.find_elements(*first)
                if elements:
                    self.logger.success(f"[SUCCESS] Found {len(elements)} elements using {first}")
                    return elements

                self.logger.warning(f"[EMPTY] No elements found using {first}")

                if second:
                    elements = main_element.find_elements(*second)
                    if elements:
                        self.logger.success(f"[SUCCESS] Found {len(elements)} elements using fallback {second}")
                        return elements
                    self.logger.warning(f"[EMPTY] No elements found using fallback {second}")

            except StaleElementReferenceException:
                self.logger.warning(f"[STALE] Main element became stale on try {trial}")
            time.sleep(1)
        self.logger.error(f"[FAILED] No child elements found after {n_retry} retries: {element_name}")
        return []
    def selenium_find_multiple_elements_with_retry(self,first: tuple,n_retry: int = 3,second: tuple = None,name: str = None) -> list[WebElement]:
        """
        Locate multiple visible elements on the page using explicit waits and retries.

        The method attempts to locate all visible elements matching the primary
        locator. If the attempt times out, an optional fallback locator is used.
        The search is repeated for a defined number of retries before failing.

        Args:
            first (tuple):
                Primary Selenium locator in the form (By, selector).
            n_retry (int, optional):
                Number of retry attempts before failure. Defaults to 3.
            second (tuple, optional):
                Fallback locator used if the primary locator times out.
            name (str, optional):
                Human-readable element name used for logging.

        Returns:
            list[WebElement]:
                A list of visible WebElements if found, otherwise an empty list
                after all retry attempts fail.
        """
        element_name = name or first

        for trial in range(1, n_retry + 1):
            try:
                self.logger.info(f"[TRY {trial}/{n_retry}] Finding elements: {element_name} using {first}")
                elements = self.short_wait.until(EC.visibility_of_all_elements_located(first))
                if elements:
                    self.logger.success(f"[SUCCESS] Found {len(elements)} elements on try {trial}")
                    return elements
            except TimeoutException:
                self.logger.warning(f"[TIMEOUT] First locator failed on try {trial}: {first}")
                if second:
                    try:
                        self.logger.info(f"[TRY {trial}/{n_retry}] Trying fallback locator: {second}")
                        elements = self.short_wait.until(EC.visibility_of_all_elements_located(second))
                        if elements:
                            self.logger.success( f"[SUCCESS] Found {len(elements)} elements using fallback")
                            return elements
                    except TimeoutException:
                        self.logger.warning(f"[TIMEOUT] Fallback locator failed on try {trial}: {second}")
            time.sleep(1)
        self.logger.error(f"[FAILED] Could not find elements after {n_retry} retries: {element_name}")
        return []
