#!/usr/bin/env python3
"""
Improved Countries Scraper for UniPage.net Russian version
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    """Setup Chrome driver with proper options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def find_country_pages(driver):
    """Find all country pages by exploring the universities section"""
    
    # Try different entry points
    entry_points = [
        "https://www.unipage.net/ru/study_countries",
        "https://www.unipage.net/ru/universities_countries", 
        "https://www.unipage.net/ru/universities"
    ]
    
    all_countries = []
    
    for url in entry_points:
        logger.info(f"🔍 Exploring: {url}")
        
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            # Look for country-specific links
            links = driver.find_elements(By.TAG_NAME, "a")
            
            country_patterns = [
                r"/ru/universities_([a-z_]+)(_ab)?$",  # Pattern like /ru/universities_germany_ab
                r"/ru/universities/([a-z_]+)$",        # Pattern like /ru/universities/germany
            ]
            
            for link in links:
                href = link.get_attribute("href")
                text = link.text.strip()
                
                if href and text:
                    for pattern in country_patterns:
                        match = re.search(pattern, href)
                        if match:
                            country_code = match.group(1)
                            all_countries.append({
                                "country": text,
                                "country_code": country_code,
                                "url": href,
                                "source": url
                            })
                            break
            
        except Exception as e:
            logger.warning(f"❌ Error exploring {url}: {e}")
    
    # Remove duplicates
    unique_countries = {}
    for country in all_countries:
        key = country["url"]
        if key not in unique_countries:
            unique_countries[key] = country
    
    return list(unique_countries.values())

def discover_countries_via_search(driver):
    """Discover countries by trying known country codes"""
    
    # Common country codes to try
    country_codes = [
        "germany", "usa", "uk", "canada", "australia", "france", "netherlands", 
        "sweden", "norway", "denmark", "finland", "switzerland", "austria",
        "spain", "italy", "japan", "south_korea", "singapore", "new_zealand",
        "belgium", "czech_republic", "poland", "russia", "china", "turkey",
        "brazil", "mexico", "argentina", "chile", "india", "thailand",
        "ireland", "portugal", "greece", "hungary", "romania", "croatia"
    ]
    
    working_countries = []
    
    logger.info(f"🌍 Testing {len(country_codes)} country codes...")
    
    for i, code in enumerate(country_codes):
        # Try different URL patterns
        urls_to_try = [
            f"https://www.unipage.net/ru/universities_{code}",
            f"https://www.unipage.net/ru/universities_{code}_ab"
        ]
        
        for url in urls_to_try:
            try:
                driver.get(url)
                
                # Quick check if page loads successfully
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check if it's a valid university page (not error page)
                page_source = driver.page_source.lower()
                
                if ("университет" in page_source or "университеты" in page_source or 
                    "university" in page_source or "college" in page_source):
                    
                    working_countries.append({
                        "country": code.replace("_", " ").title(),
                        "country_code": code,
                        "url": url,
                        "status": "verified"
                    })
                    
                    logger.info(f"✅ Found working country: {code} - {url}")
                    break  # Found working URL for this country
                    
            except Exception:
                continue  # Try next URL pattern
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            logger.info(f"📊 Progress: {i + 1}/{len(country_codes)} countries tested")
    
    return working_countries

def scrape_universities_from_country(driver, country_url, max_universities=5):
    """Scrape universities from a specific country page"""
    
    logger.info(f"🏛️ Scraping universities from: {country_url}")
    
    try:
        driver.get(country_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        
        universities = []
        links = driver.find_elements(By.TAG_NAME, "a")
        
        # Look for university links (pattern: /ru/number/university-name)
        university_pattern = re.compile(r"/ru/(\d+)/([^/?]+)")
        
        for link in links:
            href = link.get_attribute("href")
            text = link.text.strip()
            
            if href and university_pattern.search(href):
                match = university_pattern.search(href)
                if match:
                    uni_id = match.group(1)
                    uni_slug = match.group(2)
                    
                    universities.append({
                        "id": uni_id,
                        "name": text or uni_slug.replace("_", " ").title(),
                        "url": href,
                        "slug": uni_slug
                    })
        
        # Remove duplicates
        unique_unis = {uni['url']: uni for uni in universities}
        universities = list(unique_unis.values())
        
        logger.info(f"📚 Found {len(universities)} universities")
        
        # Show first few
        for i, uni in enumerate(universities[:3]):
            print(f"   📖 {uni['name']}")
        
        return universities[:max_universities]
        
    except Exception as e:
        logger.error(f"❌ Error scraping universities: {e}")
        return []

def demo_full_countries_scraper():
    """Full demo of countries and universities scraping"""
    
    driver = setup_driver()
    
    try:
        print("🎯 UNIPAGE.NET COUNTRIES & UNIVERSITIES DEMO")
        print("=" * 60)
        
        # Method 1: Try to find countries from main pages
        print("\n🔍 Method 1: Searching for countries from main pages...")
        countries_found = find_country_pages(driver)
        
        if countries_found:
            print(f"✅ Found {len(countries_found)} countries via exploration:")
            for country in countries_found:
                print(f"   🌍 {country['country']} - {country['url']}")
        else:
            print("❌ No countries found via exploration")
        
        # Method 2: Discover via testing country codes
        print(f"\n🔍 Method 2: Testing known country codes...")
        discovered_countries = discover_countries_via_search(driver)
        
        print(f"\n✅ DISCOVERED {len(discovered_countries)} WORKING COUNTRIES:")
        for i, country in enumerate(discovered_countries, 1):
            print(f"{i:2}. {country['country']} - {country['url']}")
        
        # Demo: Scrape from first few countries
        demo_countries = discovered_countries[:3]  # First 3 countries
        
        if demo_countries:
            print(f"\n🚀 DEMO: Scraping universities from {len(demo_countries)} countries...")
            
            demo_results = {}
            
            for country in demo_countries:
                country_name = country['country']
                country_url = country['url']
                
                print(f"\n📍 {country_name}")
                print("-" * 40)
                
                universities = scrape_universities_from_country(driver, country_url, max_universities=10)
                
                demo_results[country_name] = {
                    "country_url": country_url,
                    "universities_count": len(universities),
                    "universities": universities
                }
            
            # Save results
            with open("full_demo_results.json", "w", encoding="utf-8") as f:
                json.dump({
                    "discovered_countries": discovered_countries,
                    "demo_results": demo_results
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n📁 Results saved to: full_demo_results.json")
            
            # Summary
            total_unis = sum(r['universities_count'] for r in demo_results.values())
            print(f"\n📊 DEMO SUMMARY:")
            print(f"Total countries discovered: {len(discovered_countries)}")
            print(f"Countries scraped in demo: {len(demo_results)}")
            print(f"Total universities in demo: {total_unis}")
            
            return discovered_countries, demo_results
        
    finally:
        driver.quit()

if __name__ == "__main__":
    demo_full_countries_scraper() 