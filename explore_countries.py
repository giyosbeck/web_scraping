#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json

def explore_study_countries():
    """Explore the Russian study countries page"""
    url = 'https://www.unipage.net/ru/study_countries'
    
    try:
        response = requests.get(url)
        print(f'✅ Status: {response.status_code}')
        print(f'📄 Content length: {len(response.content)}')
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for country links
        print("\n🔍 Looking for country links...")
        
        # Try different selectors for country links
        selectors = [
            'a[href*="/ru/universities"]',
            '.country-list a',
            '.countries a', 
            'a[href*="study"]',
            'a[href*="country"]'
        ]
        
        all_links = []
        for selector in selectors:
            links = soup.select(selector)
            if links:
                print(f"Found {len(links)} links with selector: {selector}")
                for link in links[:5]:  # Show first 5
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    print(f"  - {text}: {href}")
                all_links.extend(links)
        
        # Get all links that might be countries
        print(f"\n📊 Total potential links found: {len(all_links)}")
        
        # Look for any patterns
        print("\n🌍 All unique href patterns:")
        hrefs = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/ru/' in href and ('universities' in href or 'study' in href):
                hrefs.add(href)
        
        for href in sorted(hrefs)[:10]:  # Show first 10
            print(f"  {href}")
            
        print(f"\nTotal university-related links: {len(hrefs)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_study_countries() 