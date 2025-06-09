import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class Navigator:
    def __init__(self, logger):
        self.logger = logger
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Initialize the Chrome WebDriver with necessary options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        
    def navigate_to_country(self, country_name):
        """Navigate to the country page and click university search"""
        try:
            self.logger.info(f"Navigating to country: {country_name}")
            self.driver.get("https://www.unipage.net/en/study_countries")
            time.sleep(5)  # Wait for Cloudflare
            
            # DEBUG: Print page source
            self.logger.info("Page source:")
            self.logger.info(self.driver.page_source)
            
            # Try multiple selectors for the country link
            selectors = [
                f"//a[contains(text(), '{country_name}')]",
                f"//a[.//span[contains(text(), '{country_name}')]]",
                f"//*[contains(text(), '{country_name}') and (self::a or self::button)]",
                f"//div[contains(@class, 'country')]//a[contains(text(), '{country_name}')]",
                f"//div[contains(@class, 'country-card')]//a[contains(text(), '{country_name}')]"
            ]
            country_link = None
            for selector in selectors:
                try:
                    country_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    if country_link:
                        self.logger.info(f"Found country link with selector: {selector}")
                        break
                except Exception as e:
                    self.logger.info(f"Selector failed: {selector} ({e})")
            if not country_link:
                self.logger.error(f"Could not find clickable country link for {country_name}")
                return False
            country_link.click()
            time.sleep(3)
            
            # Click university search button
            search_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'University search')]")
            ))
            search_button.click()
            time.sleep(3)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to country: {e}")
            return False
            
    def navigate_to_university(self, university_name):
        """Navigate to the first university page"""
        try:
            # Click first university (Bilkent for testing)
            university_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@href, '/universities/')]")
            ))
            university_link.click()
            time.sleep(3)
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to university: {e}")
            return False
            
    def navigate_degree_programs(self, degree):
        """Navigate through degree programs with pagination"""
        try:
            # Click degree tab
            degree_tab = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//button[contains(text(), '{degree}')]")
            ))
            degree_tab.click()
            time.sleep(2)
            
            # Click "Other programs" button
            other_programs = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Other programs')]")
            ))
            other_programs.click()
            time.sleep(2)
            
            # Get total programs count
            count_text = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(text(), 'Items 1-10 of')]")
            )).text
            total_programs = int(count_text.split('of')[1].strip())
            self.logger.info(f"Found {total_programs} programs for {degree}")
            
            # Handle pagination
            program_links = []
            current_page = 1
            programs_per_page = 10
            total_pages = (total_programs + programs_per_page - 1) // programs_per_page
            
            while current_page <= total_pages:
                # Extract program links from current page
                program_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/programs/')]")
                for element in program_elements:
                    try:
                        name = element.text.strip()
                        url = element.get_attribute('href')
                        if name and url:
                            program_links.append({
                                'name': name,
                                'url': url
                            })
                    except:
                        continue
                
                # Go to next page if not on last page
                if current_page < total_pages:
                    next_button = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(@aria-label, 'Next page')]")
                    ))
                    next_button.click()
                    time.sleep(2)
                
                current_page += 1
            
            return program_links
            
        except Exception as e:
            self.logger.error(f"Failed to navigate degree programs: {e}")
            return []
            
    def get_page_content(self):
        """Get the current page content"""
        try:
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Failed to get page content: {e}")
            return None
            
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit() 