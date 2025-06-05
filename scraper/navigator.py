from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
import time
import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Optional
from .ai_filter import CountryFilterAI


class WebNavigator:
    """
    Web navigator class for scraping UniPage.net using Selenium WebDriver.
    Handles navigation, page loading, and link extraction.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 10):
        """
        Initialize the WebNavigator with Chrome WebDriver.
        
        Args:
            headless (bool): Run browser in headless mode (default: True)
            timeout (int): Default timeout for page loads in seconds (default: 10)
        """
        self.timeout = timeout
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            # Initialize Chrome driver using webdriver-manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(self.timeout)
            self.logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise WebDriverException(f"WebDriver initialization failed: {e}")
    
    def open_home_page(self) -> bool:
        """
        Open the UniPage.net home page.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.driver.get("https://www.unipage.net/en/home")
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self._log_page_elements()
            self.logger.info("Successfully opened UniPage.net home page")
            return True
        except TimeoutException:
            self.logger.error("Timeout while loading home page")
            return False
        except Exception as e:
            self.logger.error(f"Error opening home page: {e}")
            return False
    
    def get_country_links(self) -> List[str]:
        """
        Navigate to the Universities page and extract country links from the filter dropdown.
        Falls back to AI-powered detection if dropdown is not found.
        
        Returns:
            List[str]: List of country URLs with _ab suffix
        """
        country_links = []
        try:
            # Navigate to the Universities page
            self.driver.get("https://www.unipage.net/en/universities")
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for the country filter dropdown
            if self.wait_for_element(By.CSS_SELECTOR, ".filters .filter--country select", timeout=15):
                select_element = self.driver.find_element(By.CSS_SELECTOR, ".filters .filter--country select")
                options = select_element.find_elements(By.TAG_NAME, "option")
                
                for option in options:
                    value = option.get_attribute("value")
                    if value and value.strip() and value != "":
                        # Build full URL with _ab suffix
                        country_url = f"https://www.unipage.net/en/universities_{value}_ab"
                        country_links.append(country_url)
                
                self.logger.info(f"Found {len(country_links)} country links from dropdown")
            else:
                self.logger.warning("Country filter dropdown not found")
                # Summarize all select elements on the page for debugging
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                if selects:
                    for sel in selects:
                        self.logger.warning(
                            "Select element: id=%s, class=%s, outerHTML(first100)=%s",
                            sel.get_attribute("id"),
                            sel.get_attribute("class"),
                            sel.get_attribute("outerHTML")[:100] if sel.get_attribute("outerHTML") else None
                        )
                else:
                    self.logger.warning("No <select> elements found on the page.")
            
            # If no country links found, fall back to AI detection
            if not country_links:
                self.logger.info("Falling back to AI-powered country filter detection")
                country_links = self._ai_discover_country_links()
                
        except Exception as e:
            self.logger.error(f"Error extracting country links: {e}")
        
        return country_links
    
    def open_url(self, url: str) -> bool:
        """
        Generic method to load any URL and wait for page to load.
        
        Args:
            url (str): URL to navigate to
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait to ensure dynamic content loads
            time.sleep(2)
            
            self._log_page_elements()
            self.logger.info(f"Successfully opened URL: {url}")
            return True
        except TimeoutException:
            self.logger.error(f"Timeout while loading URL: {url}")
            return False
        except Exception as e:
            self.logger.error(f"Error opening URL {url}: {e}")
            return False
    
    def get_university_urls_from_sitemap(self) -> List[str]:
        """
        Fetch sitemap.xml and extract university URLs matching the pattern.
        
        Returns:
            List[str]: List of university URLs from sitemap
        """
        university_urls = []
        try:
            # Fetch sitemap.xml
            response = requests.get("https://www.unipage.net/sitemap.xml", timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Extract URLs matching university pattern
            university_pattern = re.compile(r'/en/\d+/[^/]+/?$')
            
            # Handle different sitemap formats
            for url_elem in root.iter():
                if url_elem.tag.endswith('loc'):
                    url = url_elem.text
                    if url and university_pattern.search(url):
                        university_urls.append(url)
            
            self.logger.info(f"Found {len(university_urls)} university URLs from sitemap")
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching sitemap: {e}")
        except ET.ParseError as e:
            self.logger.error(f"Error parsing sitemap XML: {e}")
        except Exception as e:
            self.logger.error(f"Error processing sitemap: {e}")
        
        return university_urls
    
    def navigate_to_country(self, country: str) -> bool:
        """
        Navigate to a specific country's universities page.
        
        Args:
            country (str): Country name for the URL pattern
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            url = f"https://www.unipage.net/en/universities_{country.lower()}_ab"
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait to ensure dynamic content loads
            time.sleep(2)
            
            self._log_page_elements()
            self.logger.info(f"Successfully navigated to {country} universities page")
            return True
        except TimeoutException:
            self.logger.error(f"Timeout while loading {country} universities page")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to {country} page: {e}")
            return False
    
    def get_university_links(self) -> List[str]:
        """
        Extract all university links from the current page.
        
        Returns:
            List[str]: List of university URLs
        """
        university_links = []
        try:
            # Wait for links to be present
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            
            # Try scoped queries first
            scoped_selectors = [
                ".university-list a",
                ".universities-container a", 
                ".universities-wrapper a"
            ]
            
            links = []
            for selector in scoped_selectors:
                try:
                    scoped_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if scoped_links:
                        links.extend(scoped_links)
                        self.logger.info(f"Found {len(scoped_links)} links using selector: {selector}")
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # Fallback to all anchor tags if no scoped links found
            if not links:
                self.logger.info("No scoped links found, falling back to all anchor tags")
                links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                href = link.get_attribute("href")
                if href and self._is_university_link(href):
                    university_links.append(href)
            
            # Remove duplicates while preserving order
            university_links = list(dict.fromkeys(university_links))
            
            self.logger.info(f"Found {len(university_links)} university links")
            return university_links
            
        except TimeoutException:
            self.logger.error("Timeout while waiting for links to load")
            return []
        except Exception as e:
            self.logger.error(f"Error extracting university links: {e}")
            return []
    
    def _ai_discover_country_links(self) -> List[str]:
        """
        Use AI to discover country filter elements and extract country URLs.
        
        Returns:
            List[str]: List of discovered country URLs
        """
        country_links = []
        
        try:
            # Initialize AI filter helper
            ai_filter = CountryFilterAI()
            
            if not ai_filter.is_available():
                self.logger.warning("AI filter detection not available (no API key)")
                return []
            
            # Get current page HTML
            html = self.get_page_source()
            if not html:
                self.logger.error("Could not retrieve page source for AI analysis")
                return []
            
            # Detect filter candidates using AI
            candidates = ai_filter.detect_filters(html)
            self.logger.info(f"AI detected {len(candidates)} country filter candidates")
            
            # Process each candidate
            for i, candidate in enumerate(candidates):
                self.logger.debug(f"Processing AI candidate {i+1}/{len(candidates)}: {candidate.selector}")
                
                try:
                    # If candidate has a direct URL, use it
                    if candidate.url:
                        country_links.append(candidate.url)
                        self.logger.info(f"Added direct URL from candidate: {candidate.url}")
                        continue
                    
                    # Otherwise, try to click the element and capture the URL
                    if self.wait_for_element(By.CSS_SELECTOR, candidate.selector, timeout=5):
                        # Store current URL before clicking
                        original_url = self.get_current_url()
                        
                        # Find and click the element
                        element = self.driver.find_element(By.CSS_SELECTOR, candidate.selector)
                        element.click()
                        
                        # Wait a moment for navigation
                        time.sleep(2)
                        
                        # Get the new URL
                        new_url = self.get_current_url()
                        
                        if new_url and new_url != original_url:
                            country_links.append(new_url)
                            self.logger.info(f"Successfully clicked candidate and captured URL: {new_url}")
                        else:
                            self.logger.warning(f"No URL change after clicking candidate: {candidate.selector}")
                        
                        # Navigate back to original page
                        self.driver.back()
                        time.sleep(2)
                        
                    else:
                        self.logger.warning(f"Could not find element for candidate: {candidate.selector}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing AI candidate {candidate.selector}: {e}")
                    # Try to recover by going back if we're on a different page
                    try:
                        current_url = self.get_current_url()
                        if current_url and "universities" not in current_url:
                            self.driver.back()
                            time.sleep(2)
                    except:
                        pass
            
            # Remove duplicates while preserving order
            country_links = list(dict.fromkeys(country_links))
            
            self.logger.info(f"AI discovery completed: found {len(country_links)} unique country URLs")
            
        except Exception as e:
            self.logger.error(f"Error in AI country link discovery: {e}")
        
        return country_links
    
    def _is_university_link(self, href: str) -> bool:
        """
        Check if a link is a university detail page link.
        
        Args:
            href (str): The href attribute value
            
        Returns:
            bool: True if it's a university link, False otherwise
        """
        if not href:
            return False
        
        # Use regex pattern to match /en/\d+/[^/]+/?$
        university_pattern = re.compile(r'/en/\d+/[^/]+/?$')
        return bool(university_pattern.search(href))
    
    def navigate_to_university(self, url: str) -> bool:
        """
        Navigate to a specific university detail page.
        
        Args:
            url (str): University page URL
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            self._log_page_elements()
            self.logger.info(f"Successfully navigated to university page: {url}")
            return True
        except TimeoutException:
            self.logger.error(f"Timeout while loading university page: {url}")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to university page {url}: {e}")
            return False
    
    def get_page_source(self) -> Optional[str]:
        """
        Get the HTML source of the current page.
        
        Returns:
            Optional[str]: Page source HTML or None if error
        """
        try:
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Error getting page source: {e}")
            return None
    
    def get_current_url(self) -> Optional[str]:
        """
        Get the current page URL.
        
        Returns:
            Optional[str]: Current URL or None if error
        """
        try:
            return self.driver.current_url
        except Exception as e:
            self.logger.error(f"Error getting current URL: {e}")
            return None
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for a specific element to be present on the page.
        
        Args:
            by (By): Selenium By locator type
            value (str): Locator value
            timeout (int, optional): Custom timeout, uses default if None
            
        Returns:
            bool: True if element found, False otherwise
        """
        wait_time = timeout or self.timeout
        try:
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            self.logger.warning(f"Element not found within {wait_time} seconds: {by}={value}")
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for element {by}={value}: {e}")
            return False
    
    def quit(self):
        """
        Cleanly quit the WebDriver and close browser.
        """
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures driver is closed."""
        self.quit()
    
    def _log_page_elements(self):
        """
        Log all DOM elements on the current page for debugging purposes.
        Only logs if LOG_PAGE_ELEMENTS environment variable is set.
        """
        # If LOG_PAGE_ELEMENTS is not set, exit
        if not os.getenv('LOG_PAGE_ELEMENTS'):
            return
        # Gather all elements
        elements = self.driver.find_elements(By.XPATH, '//*')
        self.logger.debug(f"DOM snapshot start: {len(elements)} elements")
        # Process in batches of 50
        for i in range(0, len(elements), 50):
            batch = elements[i:i+50]
            batch_data = []
            for idx, el in enumerate(batch):
                try:
                    batch_data.append({
                        'index': i+idx,
                        'tag': el.tag_name,
                        'id': el.get_attribute('id') or '',
                        'class': el.get_attribute('class') or '',
                        'name': el.get_attribute('name') or '',
                        'href': el.get_attribute('href') or '',
                        'src': el.get_attribute('src') or '',
                        'text': (el.text or '')[:150]
                    })
                except Exception as e:
                    self.logger.debug(f"Element {i+idx} error: {e}")
            self.logger.debug(f"DOM Batch {i//50 + 1}: {batch_data}")
        self.logger.debug("DOM snapshot completed")
