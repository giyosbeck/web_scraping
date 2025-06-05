#!/usr/bin/env python3
"""
Final working AI-driven university scraper for UniPage.net
Uses the discovered working URL pattern and direct approach.
"""
import json
import logging
import requests
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, List, Any, Optional


class FinalAIScraper:
    """Final working AI scraper that uses the discovered working approach."""
    
    def __init__(self, api_key: str, model: str = "deepseek/deepseek-r1:free"):
        """Initialize the scraper."""
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.logger = logging.getLogger(__name__)
        
        # Setup Chrome WebDriver (non-headless to bypass Cloudflare)
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("🚀 Chrome WebDriver initialized")
    
    def scrape_universities(self) -> Dict[str, Any]:
        """Scrape university data using the working approach."""
        try:
            # Step 1: Go directly to the working universities page
            universities_url = "https://www.unipage.net/en/universities"
            print(f"🔍 Loading universities page: {universities_url}")
            self.driver.get(universities_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)
            
            print(f"✅ Page loaded: {self.driver.title}")
            
            # Step 2: Extract university links using regex
            page_html = self.driver.page_source
            university_links = re.findall(r'href="([^"]*\/en\/\d+\/[^"]*)"', page_html)
            
            # Convert to full URLs and remove duplicates
            full_links = []
            for link in university_links:
                if link.startswith('/'):
                    full_url = f"https://www.unipage.net{link}"
                else:
                    full_url = link
                full_links.append(full_url)
            
            unique_links = list(dict.fromkeys(full_links))
            print(f"🎯 Found {len(unique_links)} unique university links!")
            
            # Step 3: Process each university (limit to 5 for testing)
            universities = []
            for i, uni_url in enumerate(unique_links[:5]):
                try:
                    print(f"\n📚 Processing university {i+1}/5: {uni_url}")
                    self.driver.get(uni_url)
                    time.sleep(2)
                    
                    # Extract data using AI
                    uni_html = self.driver.page_source
                    uni_data = self._extract_university_data_with_ai(uni_html, uni_url)
                    
                    if uni_data:
                        universities.append(uni_data)
                        print(f"   ✅ Extracted: {uni_data.get('name', 'Unknown')}")
                    else:
                        print(f"   ❌ Failed to extract data")
                        
                except Exception as e:
                    print(f"   💥 Error: {e}")
            
            return {"universities": universities, "total_found": len(universities)}
            
        except Exception as e:
            print(f"💥 Error in scraping: {e}")
            return {}
        finally:
            self.driver.quit()
    
    def _extract_university_data_with_ai(self, html: str, url: str) -> Dict[str, Any]:
        """Use AI to extract university data."""
        # Clean HTML
        clean_html = self._clean_html(html)
        
        system_prompt = """Extract university information from this HTML. Return ONLY valid JSON:
{
  "name": "University Name",
  "location": "City, Country",
  "description": "Brief description",
  "website": "Official website URL",
  "programs": ["Program 1", "Program 2"],
  "type": "Public/Private",
  "founded": "Year founded"
}

Extract what you can find. Return only the JSON object."""
        
        user_message = f"University URL: {url}\n\nHTML:\n{clean_html[:8000]}"
        
        try:
            response = self._call_ai_api(system_prompt, user_message)
            clean_response = self._strip_markdown_json(response)
            data = json.loads(clean_response)
            data["scraped_url"] = url
            data["scraped_at"] = self._get_timestamp()
            return data
        except Exception as e:
            print(f"      ⚠️ AI extraction error: {e}")
            return {}
    
    def _clean_html(self, html: str) -> str:
        """Clean HTML for AI analysis."""
        import re
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        return html
    
    def _strip_markdown_json(self, response: str) -> str:
        """Strip markdown code blocks."""
        import re
        response = re.sub(r'```json\s*\n?', '', response, flags=re.IGNORECASE)
        response = re.sub(r'```\s*$', '', response)
        response = re.sub(r'^\s*```\s*', '', response)
        return response.strip()
    
    def _call_ai_api(self, system_prompt: str, user_message: str) -> str:
        """Call AI API."""
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
            'max_tokens': 4000,
            'temperature': 0.1
        }
        
        response = requests.post(
            f'{self.base_url}/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Final AI University Scraper")
    parser.add_argument("--api-key", required=True, help="OpenRouter API key")
    parser.add_argument("--output", default="final_universities.json", help="Output file")
    
    args = parser.parse_args()
    
    print("🎓 Final AI University Scraper Starting!")
    
    scraper = FinalAIScraper(args.api_key)
    result = scraper.scrape_universities()
    
    if result and result.get("universities"):
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 SUCCESS!")
        print(f"📊 Universities scraped: {result['total_found']}")
        print(f"💾 Saved to: {args.output}")
        
        for i, uni in enumerate(result["universities"]):
            print(f"  {i+1}. {uni.get('name', 'Unknown')} - {uni.get('location', 'Unknown')}")
    else:
        print("❌ No universities found")


if __name__ == "__main__":
    main() 