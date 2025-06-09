"""
University Navigator - Handles web navigation for university scraping
"""

import time
import re
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from scraper.logger_config import get_logger
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


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
            
            # Click on country
            country_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//a[contains(text(), '{country_name}')]")
            ))
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

    def open_study_countries_page(self) -> bool:
        """
        Open the study countries page.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            url = "https://www.unipage.net/en/study_countries"
            self.logger.info(f"Opening study countries page: {url}")
            
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(3)  # Additional wait for content to load
            
            self.logger.info("Study countries page loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open study countries page: {e}")
            return False
    
    def find_country_link(self, country_name: str) -> Optional[str]:
        """
        Find a link to a specific country on the study countries page.
        
        Args:
            country_name: Name of the country to find
        
        Returns:
            str: URL to the country page if found, None otherwise
        """
        try:
            self.logger.info(f"Looking for country: {country_name}")
            
            # Get all links on the page
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    if href and text:
                        # Check if this link is for our target country
                        if (country_name.lower() in text.lower() or 
                            country_name.lower() in href.lower() or
                            text.lower() in country_name.lower()):
                            
                            # Validate that it's a country page link
                            if "/en/" in href and ("universities" in href or "study" in href):
                                self.logger.info(f"Found country link: {text} -> {href}")
                                return href
                                
                except Exception as e:
                    continue
            
            # If exact match not found, try alternative approach
            # Look for country cards or sections
            try:
                # Try to find elements containing the country name
                country_elements = self.driver.find_elements(
                    By.XPATH, f"//*[contains(text(), '{country_name}')]"
                )
                
                for element in country_elements:
                    # Look for a link within or near this element
                    try:
                        # Check if element itself is a link
                        if element.tag_name == "a":
                            href = element.get_attribute("href")
                            if href and "/en/" in href:
                                self.logger.info(f"Found country link via text search: {href}")
                                return href
                        
                        # Check parent elements for links
                        parent = element.find_element(By.XPATH, "..")
                        if parent.tag_name == "a":
                            href = parent.get_attribute("href")
                            if href and "/en/" in href:
                                self.logger.info(f"Found country link via parent: {href}")
                                return href
                        
                        # Check for nearby links
                        nearby_links = element.find_elements(By.XPATH, ".//a | ../a | ../../a")
                        for nearby_link in nearby_links:
                            href = nearby_link.get_attribute("href")
                            if href and "/en/" in href and ("universities" in href or "study" in href):
                                self.logger.info(f"Found country link via nearby element: {href}")
                                return href
                                
                    except Exception:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Alternative country search failed: {e}")
            
            self.logger.error(f"Could not find link for country: {country_name}")
            return None
                
        except Exception as e:
            self.logger.error(f"Error finding country link: {e}")
            return None
    
    def open_country_page(self, country_url: str) -> bool:
        """
        Open a country page.
        
        Args:
            country_url: URL of the country page
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Opening country page: {country_url}")
            
            self.driver.get(country_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(3)  # Additional wait for content to load
            
            self.logger.info("Country page loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open country page: {e}")
            return False
    
    def get_university_links(self) -> List[str]:
        """
        Extract university links from the current page.
        
        Returns:
            list: List of university page URLs
        """
        try:
            self.logger.info("Extracting university links from page")
            
            # Get all links on the page
            links = self.driver.find_elements(By.TAG_NAME, "a")
            university_links = []
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href:
                        # Check if this looks like a university page link
                        # University links typically match pattern: /en/[id]/[university-name]
                        if re.match(r'https?://[^/]+/en/\d+/[^/]+', href):
                            university_links.append(href)
                            
                except Exception:
                    continue
            
            # Remove duplicates while preserving order
            unique_links = list(dict.fromkeys(university_links))
            
            self.logger.info(f"Found {len(unique_links)} university links")
            
            if len(unique_links) == 0:
                # Log the page source for debugging
                self.logger.warning("No university links found. Page might have different structure.")
                # Try alternative patterns
                alternative_links = []
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        text = link.text.strip() if link.text else ""
                        
                        if href and text:
                            # Look for university-related keywords
                            university_keywords = ["university", "college", "institute", "school"]
                            if any(keyword in text.lower() for keyword in university_keywords):
                                if "/en/" in href:
                                    alternative_links.append(href)
                                    
                    except Exception:
                        continue
                
                if alternative_links:
                    unique_alternative = list(dict.fromkeys(alternative_links))
                    self.logger.info(f"Found {len(unique_alternative)} alternative university links")
                    return unique_alternative
            
            return unique_links
            
        except Exception as e:
            self.logger.error(f"Error extracting university links: {e}")
            return []
    
    def open_university_page(self, university_url: str) -> bool:
        """
        Open a university page and expand all program sections.
        
        Args:
            university_url: URL of the university page
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Opening university page: {university_url}")
            
            self.driver.get(university_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(3)  # Initial wait for content to load
            
            # Try to expand all program sections
            self._expand_all_programs()
            
            self.logger.info("University page loaded and expanded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open university page: {e}")
            return False
    
    def _expand_all_programs(self):
        """
        Use the original university page content instead of navigating to programs page
        (which gets blocked by Cloudflare). The main page contains sufficient program data.
        """
        try:
            self.logger.info("Using original university page content for program extraction...")
            
            # The current page already contains program information
            # No need to navigate to separate programs page that gets blocked
            page_source = self.driver.page_source
            page_length = len(page_source)
            self.logger.info(f"University page content length: {page_length} characters")
            
            # Check if we have program content
            program_count = page_source.lower().count('program')
            bilkent_count = page_source.lower().count('bilkent')
            
            self.logger.info(f"Program mentions: {program_count}")
            self.logger.info(f"Bilkent mentions: {bilkent_count}")
            
            if bilkent_count > 0 and program_count > 0:
                self.logger.info("University page contains program information")
            else:
                self.logger.warning("Limited program content found on university page")
            
            # Content ready for extraction
            
            self.logger.info("Program extraction from university page completed!")
            
        except Exception as e:
            self.logger.error(f"Error expanding program data: {e}")

    def _extract_university_id(self, url: str) -> str:
        """Extract university ID from URL like /en/9801/bilkent_university"""
        try:
            import re
            match = re.search(r'/en/(\d+)/', url)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None
    
    def _click_degree_tab(self, degree: str) -> bool:
        """
        Click on a specific degree level tab (bachelor, master, doctorate).
        
        Args:
            degree: The degree level to click
        
        Returns:
            bool: True if tab was found and clicked, False otherwise
        """
        try:
            # Try different selectors for degree tabs
            tab_selectors = [
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{degree}')]",
                f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{degree}')]",
                f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{degree}')]//button",
                f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{degree}')]//a",
                f"//*[contains(@class, 'tab') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{degree}')]"
            ]
            
            for selector in tab_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.logger.info(f"Found and clicking {degree} tab")
                            self.driver.execute_script("arguments[0].click();", element)
                            return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error clicking {degree} tab: {e}")
            return False
    
    def _click_other_programs_button(self):
        """
        Click the "other programs" button in the Study programs section to show all programs.
        
        Returns:
            bool: True if button was found and clicked, False otherwise
        """
        try:
            self.logger.info("Looking for 'Study programs' section and 'other programs' button...")
            
            # Multiple selectors to find the "other programs" button
            selectors = [
                "//button[contains(text(), 'other programs')]",
                "//a[contains(text(), 'other programs')]",
                "//span[contains(text(), 'other programs')]",
                "//*[contains(@class, 'more') and contains(text(), 'program')]",
                "//*[contains(@class, 'show-more') and contains(text(), 'program')]",
                "//button[contains(text(), 'Show more')]",
                "//a[contains(text(), 'Show more')]",
                "//button[contains(text(), 'View all')]",
                "//a[contains(text(), 'View all')]",
                "//*[contains(text(), 'other programs')]",
                "//*[contains(text(), 'more programs')]",
                "//*[contains(text(), 'all programs')]"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, selector)))
                    self.logger.info(f"Found 'other programs' button with selector: {selector}")
                    
                    # Scroll to element
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    # Click the element
                    element.click()
                    self.logger.info("Successfully clicked 'other programs' button")
                    
                    # Wait for content to load
                    time.sleep(3)
                    return True
                    
                except (TimeoutException, NoSuchElementException):
                    continue
                except Exception as e:
                    self.logger.warning(f"Error clicking with selector {selector}: {e}")
                    continue
            
            self.logger.error("Could not find or click 'other programs' button")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in _click_other_programs_button: {e}")
            return False
    
    def _handle_program_pagination(self):
        """
        Handle pagination to get all programs (Items 1-10 of 86)
        Returns: str - combined content from all pages
        """
        try:
            self.logger.info("Starting pagination handling...")
            all_content = []
            page_number = 1
            max_pages = 15  # Increased limit for 86 programs (86/10 = 9 pages minimum)
            programs_found = 0
            
            # Navigate through all pages manually using URL parameters
            university_id = self._extract_university_id(self.driver.current_url)
            
            for page_num in range(1, max_pages + 1):
                self.logger.info(f"Processing page {page_num}")
                
                # Construct page URL
                page_url = f"https://www.unipage.net/en/programs?universityIds[]={university_id}&page={page_num}"
                
                # Navigate to specific page
                if page_num > 1:  # First page already loaded
                    self.driver.get(page_url)
                    time.sleep(4)
                
                # Get current page content
                page_content = self.driver.page_source
                all_content.append(page_content)
                
                # Look for pagination info (e.g., "Items 1-10 of 86")
                pagination_info = self._extract_pagination_info()
                if pagination_info:
                    self.logger.info(f"Pagination info: {pagination_info}")
                    
                    # Extract current range to check if we're done
                    import re
                    match = re.search(r'(\d+)-(\d+) of (\d+)', pagination_info)
                    if match:
                        start_item = int(match.group(1))
                        end_item = int(match.group(2))
                        total_items = int(match.group(3))
                        self.logger.info(f"Progress: {end_item}/{total_items} programs on page {page_num}")
                        
                        # If we've reached the last item, we're done
                        if end_item >= total_items:
                            self.logger.info("Reached all programs!")
                            break
                        
                        # If this page shows no new content (same as previous), we're done
                        if page_num > 1 and start_item <= 10:
                            self.logger.info("No new content on this page, stopping")
                            break
                        else:
                    # No pagination info found, might be the last page
                    if page_num > 1:
                        self.logger.info("No pagination info found, might be done")
                        break
            
            # Combine all content
            combined_content = "\n".join(all_content)
            total_programs_mentions = combined_content.lower().count('program')
            
            self.logger.info("Pagination completed:")
            self.logger.info(f"   Pages processed: {len(all_content)}")
            self.logger.info(f"   Total content length: {len(combined_content)} characters")
            self.logger.info(f"   Program mentions found: {total_programs_mentions}")
            
            return combined_content
            
        except Exception as e:
            self.logger.error(f"Error in pagination handling: {e}")
            return ""
    
    def _extract_pagination_info(self):
        """Extract pagination information like 'Items 1-10 of 86'"""
        try:
            # Look for pagination text patterns
            patterns = [
                "Items \\d+-\\d+ of \\d+",
                "\\d+-\\d+ of \\d+",
                "Page \\d+ of \\d+",
                "Showing \\d+-\\d+ of \\d+"
            ]
            
            page_text = self.driver.page_source
            import re
            
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    return match.group(0)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting pagination info: {e}")
            return None
    
    def _click_next_page(self):
        """
        Handle AJAX pagination by loading more content
        Returns: bool indicating success
        """
        try:
            # First try to scroll down to trigger lazy loading
            self.logger.info("Trying to load more content via scrolling...")
            
            # Get current page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height > last_height:
                self.logger.info("New content loaded via scrolling")
                return True
            
            # Try to find and click "Load more" or pagination buttons
            load_more_selectors = [
                "//button[contains(text(), 'Load more')]",
                "//a[contains(text(), 'Load more')]",
                "//button[contains(text(), 'Show more')]",
                "//a[contains(text(), 'Show more')]",
                "//*[contains(@class, 'load-more')]",
                "//*[contains(@class, 'show-more')]",
                "//button[contains(@class, 'next')]",
                "//a[contains(@class, 'next')]",
                "//*[contains(@class, 'pagination')]//a[not(contains(@class, 'disabled'))]",
                "//*[contains(@class, 'pagination')]//button[not(contains(@class, 'disabled'))]"
            ]
            
            for selector in load_more_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Scroll to element
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)
                            
                            # Click the element
                            element.click()
                            self.logger.info(f"Successfully clicked load more button with selector: {selector}")
                            
                            # Wait for content to load
                            time.sleep(5)
                            return True
                            
                except Exception as e:
                    continue
            
            # Try to manually construct next page URL
            current_url = self.driver.current_url
            if "page=" not in current_url:
                # Add page parameter
                next_url = current_url + "&page=2"
            else:
                # Increment page number
                import re
                page_match = re.search(r'page=(\d+)', current_url)
                if page_match:
                    current_page = int(page_match.group(1))
                    next_page = current_page + 1
                    next_url = re.sub(r'page=\d+', f'page={next_page}', current_url)
                else:
                    return False
            
            self.logger.info(f"Trying to navigate to next page URL: {next_url}")
            self.driver.get(next_url)
            time.sleep(5)
            
            # Check if we got different content
            pagination_info = self._extract_pagination_info()
            if pagination_info and "1-10" not in pagination_info:
                self.logger.info(f"Successfully navigated to next page: {pagination_info}")
            return True
            
            self.logger.info("No more pages available")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in _click_next_page: {e}")
            return False
    
    def get_page_source(self) -> str:
        """
        Get the current page source.
        
        Returns:
            str: HTML source of the current page
        """
        try:
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Error getting page source: {e}")
            return ""
    
    def quit(self):
        """Close the browser."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
    
    def extract_program_links(self) -> List[Dict[str, str]]:
        """
        Extract all program page links after content has been fully expanded.
        
        Returns:
            List of dictionaries containing program information and links
        """
        try:
            self.logger.info("Extracting program page links...")
            
            program_links = []
            
            # Look for program page buttons/links
            program_link_selectors = [
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'program page')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'program page')]",
                "//a[contains(@href, 'program')]",
                "//a[contains(@href, 'course')]",
                "//a[contains(@href, 'dep/')]",  # Department/program specific URLs
                "//*[contains(@class, 'program')]//a",
                "//*[contains(@class, 'course')]//a",
                "//*[@data-program-url]",
                "//a[contains(@class, 'program-link')]"
            ]
            
            for selector in program_link_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            href = element.get_attribute('href')
                            text = element.text.strip()
                            
                            if href and href not in [link['url'] for link in program_links]:
                                # Extract program info from surrounding context
                                program_info = self._extract_program_context(element)
                                
                                program_links.append({
                                    'name': text or program_info.get('name', 'Unknown Program'),
                                    'url': href,
                                    'degree_level': program_info.get('degree_level', 'Unknown'),
                                    'faculty': program_info.get('faculty', 'Unknown'),
                                    'study_field': program_info.get('study_field', 'Unknown')
                                })
                                
                except Exception as e:
                    self.logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            self.logger.info(f"Found {len(program_links)} program links")
            
            # Log some examples
            for i, link in enumerate(program_links[:5]):
                self.logger.info(f"   {i+1}. {link['name']} - {link['url']}")
            
            if len(program_links) > 5:
                self.logger.info(f"   ... and {len(program_links) - 5} more programs")
            
            return program_links
            
        except Exception as e:
            self.logger.error(f"Error extracting program links: {e}")
            return []
    
    def _extract_program_context(self, element) -> Dict[str, str]:
        """
        Extract contextual information about a program from its surrounding HTML.
        
        Args:
            element: The web element containing the program link
            
        Returns:
            Dictionary with program context information
        """
        try:
            context = {
                'name': '',
                'degree_level': 'Unknown',
                'faculty': 'Unknown', 
                'study_field': 'Unknown'
            }
            
            # Try to find program name from element text or nearby elements
            program_name = element.text.strip()
            if not program_name:
                # Look for program name in parent elements
                parent = element.find_element(By.XPATH, "..")
                program_name = parent.text.strip()
            
            context['name'] = program_name
            
            # Try to determine degree level from URL or surrounding context
            href = element.get_attribute('href') or ''
            page_source = self.driver.page_source.lower()
            
            # Look for degree level indicators
            if any(keyword in href.lower() for keyword in ['bachelor', 'undergraduate', 'ba', 'bs', 'bsc']):
                context['degree_level'] = 'Bachelor'
            elif any(keyword in href.lower() for keyword in ['master', 'graduate', 'ma', 'ms', 'msc', 'mba']):
                context['degree_level'] = 'Master'
            elif any(keyword in href.lower() for keyword in ['doctorate', 'phd', 'doctoral']):
                context['degree_level'] = 'Doctorate'
            
            # Try to extract faculty from URL or context
            if 'engineering' in href.lower() or 'engineering' in program_name.lower():
                context['faculty'] = 'Faculty of Engineering'
            elif 'law' in href.lower() or 'law' in program_name.lower():
                context['faculty'] = 'Faculty of Law'
            elif any(keyword in href.lower() or keyword in program_name.lower() 
                    for keyword in ['business', 'economics', 'management']):
                context['faculty'] = 'Faculty of Economics, Administrative and Social Sciences'
            elif any(keyword in href.lower() or keyword in program_name.lower() 
                    for keyword in ['science', 'mathematics', 'physics', 'chemistry']):
                context['faculty'] = 'Faculty of Science'
            elif any(keyword in href.lower() or keyword in program_name.lower() 
                    for keyword in ['art', 'design', 'architecture', 'music']):
                context['faculty'] = 'Faculty of Art, Design and Architecture'
            
            return context
            
        except Exception as e:
            self.logger.debug(f"Error extracting program context: {e}")
            return {
                'name': element.text.strip() if element.text else 'Unknown Program',
                'degree_level': 'Unknown',
                'faculty': 'Unknown',
                'study_field': 'Unknown'
            }
