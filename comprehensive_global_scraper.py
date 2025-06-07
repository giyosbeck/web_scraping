#!/usr/bin/env python3
"""
Comprehensive Global University Scraper for UniPage.net
Scrapes universities from all 34 discovered countries
"""

import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('global_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# All 34 discovered countries
COUNTRIES = [
    {"name": "Germany", "code": "germany"},
    {"name": "USA", "code": "usa"},
    {"name": "UK", "code": "uk"},
    {"name": "Canada", "code": "canada"},
    {"name": "Australia", "code": "australia"},
    {"name": "France", "code": "france"},
    {"name": "Netherlands", "code": "netherlands"},
    {"name": "Sweden", "code": "sweden"},
    {"name": "Norway", "code": "norway"},
    {"name": "Denmark", "code": "denmark"},
    {"name": "Finland", "code": "finland"},
    {"name": "Switzerland", "code": "switzerland"},
    {"name": "Austria", "code": "austria"},
    {"name": "Spain", "code": "spain"},
    {"name": "Italy", "code": "italy"},
    {"name": "Japan", "code": "japan"},
    {"name": "Singapore", "code": "singapore"},
    {"name": "New Zealand", "code": "new_zealand"},
    {"name": "Belgium", "code": "belgium"},
    {"name": "Poland", "code": "poland"},
    {"name": "China", "code": "china"},
    {"name": "Turkey", "code": "turkey"},
    {"name": "Brazil", "code": "brazil"},
    {"name": "Mexico", "code": "mexico"},
    {"name": "Argentina", "code": "argentina"},
    {"name": "Chile", "code": "chile"},
    {"name": "India", "code": "india"},
    {"name": "Thailand", "code": "thailand"},
    {"name": "Ireland", "code": "ireland"},
    {"name": "Portugal", "code": "portugal"},
    {"name": "Greece", "code": "greece"},
    {"name": "Hungary", "code": "hungary"},
    {"name": "Romania", "code": "romania"},
    {"name": "Croatia", "code": "croatia"}
]

def setup_driver():
    """Setup Chrome driver with optimized options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-images")  # Speed optimization
    # Don't disable JavaScript as Russian site needs it
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(5)
    return driver

def scrape_country_universities(driver, country_name, country_code):
    """Scrape all universities from a specific country"""
    url = f"https://www.unipage.net/ru/universities_{country_code}"
    
    logger.info(f"🏛️ Scraping {country_name} universities from: {url}")
    
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        
        universities = []
        links = driver.find_elements(By.TAG_NAME, "a")
        
        # Extract university links using regex pattern
        import re
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
                        "slug": uni_slug,
                        "country": country_name,
                        "country_code": country_code
                    })
        
        # Remove duplicates
        unique_unis = {}
        for uni in universities:
            if uni['url'] not in unique_unis:
                unique_unis[uni['url']] = uni
        
        universities = list(unique_unis.values())
        
        logger.info(f"✅ {country_name}: Found {len(universities)} universities")
        return universities
        
    except Exception as e:
        logger.error(f"❌ Error scraping {country_name}: {e}")
        return []

def run_global_scraper(countries_to_scrape=None, output_dir="global_universities_data"):
    """Run the comprehensive global scraper"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Use all countries if none specified
    if countries_to_scrape is None:
        countries_to_scrape = COUNTRIES
    
    driver = setup_driver()
    
    try:
        start_time = datetime.now()
        logger.info(f"🌍 Starting Global University Scraper for {len(countries_to_scrape)} countries")
        logger.info(f"📁 Output directory: {output_dir}")
        
        all_results = {}
        total_universities = 0
        
        for i, country in enumerate(countries_to_scrape, 1):
            country_name = country['name']
            country_code = country['code']
            
            logger.info(f"\n📍 [{i}/{len(countries_to_scrape)}] Processing {country_name}")
            
            universities = scrape_country_universities(driver, country_name, country_code)
            
            if universities:
                # Save individual country file
                country_file = os.path.join(output_dir, f"{country_code}_universities.json")
                with open(country_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "country": country_name,
                        "country_code": country_code,
                        "url": f"https://www.unipage.net/ru/universities_{country_code}",
                        "universities_count": len(universities),
                        "universities": universities,
                        "scraped_at": datetime.now().isoformat()
                    }, f, ensure_ascii=False, indent=2)
                
                all_results[country_name] = universities
                total_universities += len(universities)
                
                logger.info(f"💾 Saved {len(universities)} universities to {country_file}")
            
            # Small delay between countries
            time.sleep(1)
        
        # Save comprehensive summary
        summary = {
            "scraping_session": {
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_minutes": (datetime.now() - start_time).total_seconds() / 60,
                "countries_processed": len(countries_to_scrape),
                "total_universities_found": total_universities
            },
            "countries_summary": []
        }
        
        for country_name, universities in all_results.items():
            summary["countries_summary"].append({
                "country": country_name,
                "universities_count": len(universities),
                "sample_universities": universities[:3]  # First 3 as sample
            })
        
        # Save summary
        summary_file = os.path.join(output_dir, "scraping_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Print final summary
        print(f"\n🎯 GLOBAL SCRAPING COMPLETED!")
        print("=" * 60)
        print(f"📊 Countries processed: {len(all_results)}")
        print(f"🏛️ Total universities found: {total_universities}")
        print(f"⏱️ Duration: {(datetime.now() - start_time).total_seconds() / 60:.1f} minutes")
        print(f"📁 Results saved to: {output_dir}/")
        print(f"📄 Summary: {summary_file}")
        
        # Show top countries by university count
        print(f"\n🏆 TOP COUNTRIES BY UNIVERSITY COUNT:")
        sorted_countries = sorted(all_results.items(), key=lambda x: len(x[1]), reverse=True)
        for i, (country, unis) in enumerate(sorted_countries[:10], 1):
            print(f"{i:2}. {country}: {len(unis)} universities")
        
        return all_results, summary
        
    finally:
        driver.quit()

def quick_demo(num_countries=5):
    """Quick demo with first N countries"""
    print(f"🚀 Running Quick Demo with {num_countries} countries...")
    demo_countries = COUNTRIES[:num_countries]
    return run_global_scraper(demo_countries, "demo_global_data")

def full_scraper():
    """Run full scraper for all 34 countries"""
    print("🌍 Running Full Global Scraper for ALL 34 countries...")
    print("⚠️  This will take approximately 15-20 minutes")
    
    confirm = input("Do you want to continue? (y/N): ")
    if confirm.lower() == 'y':
        return run_global_scraper(COUNTRIES, "full_global_data")
    else:
        print("❌ Cancelled by user")

if __name__ == "__main__":
    print("🎯 UniPage.net Global University Scraper")
    print("=" * 50)
    print("1. Quick Demo (5 countries)")
    print("2. Medium Run (15 countries)")  
    print("3. Full Scraper (ALL 34 countries)")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        quick_demo(5)
    elif choice == "2":
        run_global_scraper(COUNTRIES[:15], "medium_global_data")
    elif choice == "3":
        full_scraper()
    else:
        print("Running quick demo by default...")
        quick_demo(3) 