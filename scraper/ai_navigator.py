import json
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from typing import Dict, List, Any, Optional


class AINavigator:
    """
    AI-driven web navigator that uses LLM to analyze pages and decide navigation strategy.
    No hardcoded selectors - let AI figure out how to navigate the site.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek/deepseek-r1:free", base_url: str = "https://openrouter.ai/api/v1"):
        """
        Initialize AI Navigator with OpenRouter API.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use (default: deepseek/deepseek-r1:free)
            base_url: OpenRouter API base URL
        """
        self.api_key = api_key or self._get_api_key()
        self.model = model
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        
        # Initialize Chrome WebDriver
        self.driver = self._setup_driver()
        
    def _get_api_key(self) -> str:
        """Get API key from environment variables."""
        import os
        return os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY', '')
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver."""
        chrome_options = Options()
        # Don't run headless to avoid Cloudflare detection
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        # Use a more realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        # Disable automation indicators
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.implicitly_wait(10)
        
        self.logger.info("Chrome WebDriver initialized for AI navigation")
        return driver
    
    def scrape_university_data(self, start_url: str = "https://www.unipage.net/en/home") -> Dict[str, Any]:
        """
        Start from the given URL and use AI to navigate and extract university data.
        
        Args:
            start_url: Starting URL (default: unipage.net home page)
            
        Returns:
            Dict containing all discovered university data
        """
        try:
            # Go directly to the universities page that we know works
            universities_url = "https://www.unipage.net/en/universities"
            self.logger.info(f"Going directly to universities page: {universities_url}")
            self.driver.get(universities_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # Wait for content to load
            
            # Get page content and extract university links directly
            page_html = self.driver.page_source
            self.logger.info("Extracting university links from page...")
            
            # Use regex to find university links (pattern: /en/123/university-name)
            import re
            university_links = re.findall(r'href="([^"]*\/en\/\d+\/[^"]*)"', page_html)
            
            # Convert relative URLs to absolute URLs
            full_university_links = []
            for link in university_links:
                if link.startswith('/'):
                    full_url = f"https://www.unipage.net{link}"
                else:
                    full_url = link
                full_university_links.append(full_url)
            
            # Remove duplicates
            unique_links = list(dict.fromkeys(full_university_links))
            
            self.logger.info(f"Found {len(unique_links)} unique university links")
            print(f"🎯 Found {len(unique_links)} university links!")
            
            # Process universities (limit to 10 for testing)
            universities = []
            for i, uni_url in enumerate(unique_links[:10]):
                try:
                    print(f"📚 Processing university {i+1}/{min(10, len(unique_links))}: {uni_url}")
                    self.logger.info(f"Visiting university page: {uni_url}")
                    self.driver.get(uni_url)
                    time.sleep(2)
                    
                    # Extract data from this university page using AI
                    uni_html = self.driver.page_source
                    uni_data = self._extract_university_data(uni_html, uni_url)
                    if uni_data and isinstance(uni_data, dict):
                        universities.append(uni_data)
                        print(f"   ✅ Extracted: {uni_data.get('name', 'Unknown')}")
                    else:
                        print(f"   ❌ Failed to extract data")
                        
                except Exception as e:
                    self.logger.error(f"Error visiting university {uni_url}: {e}")
                    print(f"   💥 Error: {e}")
            
            return {"universities": universities, "total_found": len(universities)}
            
        except Exception as e:
            self.logger.error(f"Error in AI-driven scraping: {e}")
            return {}
        finally:
            self.driver.quit()
    
    def _ask_ai_for_navigation_plan(self, page_html: str, current_url: str) -> Dict[str, Any]:
        """
        Send page HTML to AI and ask for navigation strategy.
        
        Args:
            page_html: Current page HTML content
            current_url: Current page URL
            
        Returns:
            Dict containing AI's navigation plan
        """
        if not self.api_key:
            self.logger.error("No API key available for AI navigation")
            return {}
        
        # Prepare the HTML (remove scripts/styles and truncate)
        clean_html = self._clean_html_for_ai(page_html)
        
        print(f"🔍 DEBUG: Clean HTML length: {len(clean_html)}")
        print(f"🔍 DEBUG: Clean HTML first 200 chars: {clean_html[:200]}")
        
        system_prompt = """You are a web scraping expert. Analyze the provided HTML and determine how to find university information.

Your goal: Extract university data from UniPage.net including names, locations, descriptions, etc.

IMPORTANT: 
- Only use VALID CSS selectors (no "or" statements, no speculative text)
- Look for actual links in the HTML that contain university information
- If you see university links, extract them directly
- University links usually match pattern: /en/123456/university-name

Respond with a JSON object containing:
{
  "strategy": "description of what you found and what to do next",
  "next_action": "navigate_to_link" | "extract_data" | "find_universities_page",
  "target_selector": "valid CSS selector only (no 'or' statements)",
  "target_url": "URL to navigate to (if known)",
  "university_links": ["list of university page URLs found (if any)"],
  "extracted_data": [{"name": "...", "url": "...", "description": "..."}] // if universities found on current page
}

Only return valid JSON. If you cannot find university links, set university_links to [] and suggest a different strategy."""
        
        user_message = f"""Current URL: {current_url}

Page HTML:
{clean_html}

What should I do to find university information? What links or elements should I click?"""
        
        try:
            print(f"🔍 DEBUG: Making API call to {self.model}")
            response = self._call_ai_api(system_prompt, user_message)
            print(f"🔍 DEBUG: API response: {response}")
            print(f"🔍 DEBUG: Response type: {type(response)}")
            print(f"🔍 DEBUG: Response length: {len(response) if response else 'None'}")
            
            if not response or response.strip() == "":
                print("🔍 DEBUG: Empty response from AI!")
                return {}
                
            # Strip markdown code blocks if present
            clean_response = self._strip_markdown_json(response)
            print(f"🔍 DEBUG: Clean response: {clean_response}")
            
            return json.loads(clean_response)
        except Exception as e:
            print(f"🔍 DEBUG: Exception in _ask_ai_for_navigation_plan: {e}")
            self.logger.error(f"Error getting AI navigation plan: {e}")
            return {}
    
    def _strip_markdown_json(self, response: str) -> str:
        """Strip markdown code block formatting from JSON response."""
        import re
        
        # Remove ```json ... ``` blocks
        response = re.sub(r'```json\s*\n?', '', response, flags=re.IGNORECASE)
        response = re.sub(r'```\s*$', '', response)
        response = re.sub(r'^\s*```\s*', '', response)
        
        return response.strip()
    
    def _execute_navigation_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the navigation plan provided by AI.
        
        Args:
            plan: AI's navigation plan
            
        Returns:
            Dict containing extracted university data
        """
        universities = []
        
        try:
            strategy = plan.get("strategy", "")
            next_action = plan.get("next_action", "")
            
            self.logger.info(f"Executing AI strategy: {strategy}")
            self.logger.info(f"Next action: {next_action}")
            
            if next_action == "extract_data" and plan.get("extracted_data"):
                # AI found universities on current page
                extracted = plan["extracted_data"]
                if isinstance(extracted, list):
                    universities = extracted
                    self.logger.info(f"AI extracted {len(universities)} universities from current page")
                
            elif next_action == "navigate_to_link" and plan.get("target_url"):
                # AI wants us to navigate to a specific URL
                target_url = plan["target_url"]
                self.logger.info(f"AI suggested navigating to: {target_url}")
                
                self.driver.get(target_url)
                time.sleep(3)
                
                # Get the new page and ask AI again
                new_html = self.driver.page_source
                new_plan = self._ask_ai_for_navigation_plan(new_html, target_url)
                sub_result = self._execute_navigation_plan(new_plan)
                if isinstance(sub_result.get("universities"), list):
                    universities.extend(sub_result["universities"])
                
            elif next_action == "find_universities_page" and plan.get("target_selector"):
                # AI found a link/button to click
                selector = plan["target_selector"]
                self.logger.info(f"AI suggested clicking element: {selector}")
                
                try:
                    # Validate selector first
                    if not selector or "(" in selector or "or" in selector.lower() or "speculative" in selector.lower():
                        self.logger.warning(f"Invalid selector detected: {selector}. Trying alternative approach.")
                        # Try to navigate to a specific country page directly
                        country_url = "https://www.unipage.net/en/turkey/universities"
                        self.logger.info(f"Trying direct country URL: {country_url}")
                        self.driver.get(country_url)
                        time.sleep(3)
                        
                        new_html = self.driver.page_source
                        new_plan = self._ask_ai_for_navigation_plan(new_html, country_url)
                        sub_result = self._execute_navigation_plan(new_plan)
                        if isinstance(sub_result.get("universities"), list):
                            universities.extend(sub_result["universities"])
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        element.click()
                        time.sleep(3)
                        
                        # Get the new page and ask AI again
                        new_html = self.driver.page_source
                        current_url = self.driver.current_url
                        new_plan = self._ask_ai_for_navigation_plan(new_html, current_url)
                        sub_result = self._execute_navigation_plan(new_plan)
                        if isinstance(sub_result.get("universities"), list):
                            universities.extend(sub_result["universities"])
                    
                except Exception as e:
                    self.logger.error(f"Error with selector {selector}: {e}")
                    # Fallback: try direct country page
                    try:
                        country_url = "https://www.unipage.net/en/turkey/universities"
                        self.logger.info(f"Fallback: trying direct country URL: {country_url}")
                        self.driver.get(country_url)
                        time.sleep(3)
                        
                        new_html = self.driver.page_source
                        new_plan = self._ask_ai_for_navigation_plan(new_html, country_url)
                        sub_result = self._execute_navigation_plan(new_plan)
                        if isinstance(sub_result.get("universities"), list):
                            universities.extend(sub_result["universities"])
                    except Exception as e2:
                        self.logger.error(f"Fallback also failed: {e2}")
            
            elif plan.get("university_links"):
                # AI found direct links to university pages
                university_links = plan["university_links"]
                self.logger.info(f"AI found {len(university_links)} university links")
                
                for uni_url in university_links[:10]:  # Limit to avoid overwhelming
                    try:
                        self.logger.info(f"Visiting university page: {uni_url}")
                        self.driver.get(uni_url)
                        time.sleep(2)
                        
                        # Extract data from this university page
                        uni_html = self.driver.page_source
                        uni_data = self._extract_university_data(uni_html, uni_url)
                        if uni_data and isinstance(uni_data, dict):
                            universities.append(uni_data)
                            
                    except Exception as e:
                        self.logger.error(f"Error visiting university {uni_url}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error executing navigation plan: {e}")
        
        # Ensure universities is always a list
        if not isinstance(universities, list):
            universities = []
            
        return {"universities": universities, "total_found": len(universities)}
    
    def _extract_university_data(self, html: str, url: str) -> Dict[str, Any]:
        """
        Use AI to extract university data from a university page.
        
        Args:
            html: University page HTML
            url: University page URL
            
        Returns:
            Dict containing university data
        """
        clean_html = self._clean_html_for_ai(html)
        
        system_prompt = """Extract university information from this HTML. Return a JSON object with:
{
  "name": "University Name",
  "location": "City, Country", 
  "description": "University description",
  "website": "Official website URL",
  "programs": ["List", "of", "programs"],
  "student_count": "Number of students (if available)",
  "founded": "Year founded (if available)",
  "type": "Public/Private (if available)"
}

Only return valid JSON. Extract what you can find."""
        
        user_message = f"University page URL: {url}\n\nHTML:\n{clean_html}"
        
        try:
            response = self._call_ai_api(system_prompt, user_message)
            # Strip markdown code blocks if present
            clean_response = self._strip_markdown_json(response)
            data = json.loads(clean_response)
            data["scraped_url"] = url
            data["scraped_at"] = self._get_timestamp()
            return data
        except Exception as e:
            self.logger.error(f"Error extracting university data: {e}")
            return {}
    
    def _clean_html_for_ai(self, html: str) -> str:
        """Clean HTML for AI analysis by removing scripts, styles, and truncating."""
        import re
        
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Increase truncation limit to capture more university links
        if len(html) > 20000:
            html = html[:20000] + "\n... [HTML truncated]"
        
        return html
    
    def _call_ai_api(self, system_prompt: str, user_message: str) -> str:
        """Call the AI API with the given prompts."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'max_tokens': 4000,  # Increased for reasoning models
            'temperature': 0.1
        }
        
        # Debug logging
        self.logger.debug(f"API Request - Model: {self.model}")
        self.logger.debug(f"API Request - System prompt length: {len(system_prompt)}")
        self.logger.debug(f"API Request - User message length: {len(user_message)}")
        
        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # Debug the response
            self.logger.debug(f"API Response - Status: {response.status_code}")
            self.logger.debug(f"API Response - Headers: {dict(response.headers)}")
            self.logger.debug(f"API Response - Raw text (first 1000 chars): {response.text[:1000]}")
            
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            self.logger.debug(f"API Response - Content: {content}")
            self.logger.debug(f"API Response - Finish reason: {result['choices'][0].get('finish_reason')}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            # Log more details if available
            if 'response' in locals():
                self.logger.error(f"Response status: {response.status_code}")
                self.logger.error(f"Response text: {response.text}")
            raise
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


if __name__ == "__main__":
    # Simple test run
    navigator = AINavigator()
    result = navigator.scrape_university_data()
    print(json.dumps(result, indent=2)) 