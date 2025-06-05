#!/usr/bin/env python3
"""
Simple test to find working university URLs on UniPage.net
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def test_university_urls():
    """Test various university URL patterns to find working ones."""
    
    # Setup Chrome WebDriver (non-headless to bypass Cloudflare)
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print("🔍 Testing university URL patterns...")
        
        # Test various URL patterns
        test_urls = [
            "https://www.unipage.net/en/universities",
            "https://www.unipage.net/en/search",
            "https://www.unipage.net/en/directory",
            "https://www.unipage.net/en/education",
            "https://www.unipage.net/en/study",
            "https://www.unipage.net/universities",
            "https://www.unipage.net/search"
        ]
        
        for url in test_urls:
            print(f"\n📍 Testing: {url}")
            try:
                driver.get(url)
                time.sleep(3)
                
                title = driver.title
                page_source = driver.page_source
                
                print(f"   📄 Title: {title}")
                print(f"   📏 Page size: {len(page_source)} chars")
                
                # Look for university links in the page
                university_links = re.findall(r'href="([^"]*\/en\/\d+\/[^"]*)"', page_source)
                if university_links:
                    print(f"   🎯 Found {len(university_links)} university links!")
                    for i, link in enumerate(university_links[:5]):
                        print(f"      {i+1}. {link}")
                    return url, university_links
                else:
                    print("   ❌ No university links found")
                    
            except Exception as e:
                print(f"   💥 Error: {e}")
        
        print("\n🔍 No university URL pattern found, trying search page...")
        
        # Try the search/universities page we know loads
        driver.get("https://www.unipage.net/en/home")
        time.sleep(5)
        
        # Try to find and click universities link
        try:
            unis_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Universities")
            unis_link.click()
            time.sleep(3)
            
            print(f"📍 After clicking Universities link:")
            print(f"   🌐 Current URL: {driver.current_url}")
            print(f"   📄 Title: {driver.title}")
            
            page_source = driver.page_source
            university_links = re.findall(r'href="([^"]*\/en\/\d+\/[^"]*)"', page_source)
            if university_links:
                print(f"   🎯 Found {len(university_links)} university links!")
                for i, link in enumerate(university_links[:5]):
                    print(f"      {i+1}. {link}")
                return driver.current_url, university_links
                
        except Exception as e:
            print(f"💥 Error clicking Universities link: {e}")
        
        return None, []
        
    finally:
        driver.quit()

if __name__ == "__main__":
    working_url, links = test_university_urls()
    if working_url and links:
        print(f"\n✅ SUCCESS! Found working URL: {working_url}")
        print(f"🎓 Sample university links: {links[:3]}")
    else:
        print("\n❌ No working university URLs found") 