#!/usr/bin/env python3
"""
Demo script to explore and scrape from all countries on UniPage.net/ru/study_countries
"""

import time
import json
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
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def extract_country_links(driver):
    """Extract all country links from the study countries page"""
    url = "https://www.unipage.net/ru/study_countries"
    
    logger.info(f"🌍 Accessing: {url}")
    driver.get(url)
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    time.sleep(3)  # Additional wait for dynamic content
    
    logger.info("🔍 Looking for country links...")
    
    # Find all links that might be countries
    all_links = driver.find_elements(By.TAG_NAME, "a")
    
    country_links = []
    patterns = [
        "/ru/universities_",
        "/ru/study/",
        "/ru/education/"
    ]
    
    for link in all_links:
        try:
            href = link.get_attribute("href")
            text = link.text.strip()
            
            if href and text:
                # Check if it's a university/study link
                for pattern in patterns:
                    if pattern in href:
                        country_links.append({
                            "country": text,
                            "url": href
                        })
                        break
        except Exception as e:
            continue
    
    # Remove duplicates
    unique_countries = {}
    for item in country_links:
        key = item["url"]
        if key not in unique_countries:
            unique_countries[key] = item
    
    return list(unique_countries.values())

def demo_scrape_countries(max_countries=5):
    """Demo: scrape universities from multiple countries"""
    driver = setup_driver()
    
    try:
        # Get all country links
        countries = extract_country_links(driver)
        
        logger.info(f"📊 Found {len(countries)} countries!")
        
        # Show all countries
        print("\n🌍 Available Countries:")
        for i, country in enumerate(countries, 1):
            print(f"{i:2}. {country['country']} - {country['url']}")
        
        if not countries:
            logger.error("❌ No countries found. The page structure might have changed.")
            return
        
        # Demo: Process first few countries
        print(f"\n🚀 Demo: Processing first {max_countries} countries...")
        
        results = {}
        
        for i, country in enumerate(countries[:max_countries]):
            country_name = country['country']
            country_url = country['url']
            
            logger.info(f"\n📍 Processing {i+1}/{max_countries}: {country_name}")
            logger.info(f"🔗 URL: {country_url}")
            
            try:
                # Navigate to country page
                driver.get(country_url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                time.sleep(2)
                
                # Find university links
                university_links = []
                links = driver.find_elements(By.TAG_NAME, "a")
                
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/ru/" in href and href.count("/") >= 4:
                        # Pattern like /ru/123/university-name
                        parts = href.split("/")
                        if len(parts) >= 4 and parts[2].isdigit():
                            university_links.append({
                                "name": link.text.strip() or f"University {parts[2]}",
                                "url": href
                            })
                
                # Remove duplicates
                unique_unis = {uni['url']: uni for uni in university_links}
                universities = list(unique_unis.values())
                
                results[country_name] = {
                    "country_url": country_url,
                    "universities_count": len(universities),
                    "universities": universities[:10]  # Show first 10
                }
                
                logger.info(f"✅ Found {len(universities)} universities in {country_name}")
                
                # Show sample universities
                for j, uni in enumerate(universities[:3]):
                    print(f"   {j+1}. {uni['name']}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {country_name}: {e}")
                results[country_name] = {
                    "error": str(e),
                    "universities_count": 0
                }
        
        # Save results
        with open("countries_demo_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 Results saved to: countries_demo_results.json")
        
        # Summary
        print(f"\n📊 DEMO SUMMARY:")
        total_universities = sum(r.get('universities_count', 0) for r in results.values())
        print(f"Countries processed: {len(results)}")
        print(f"Total universities found: {total_universities}")
        
        return results
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🎯 UniPage.net Countries Demo Scraper")
    print("=" * 50)
    
    # Run demo with first 5 countries
    demo_scrape_countries(max_countries=5) 