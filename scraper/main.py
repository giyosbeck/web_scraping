#!/usr/bin/env python3
"""
UniPage.net University Scraper
Scrapes detailed university information from https://www.unipage.net/en/study_countries
"""

import os
import json
import argparse
import logging
import time
from typing import Dict, List, Any
from scraper.logger_config import setup_logging, get_logger
from scraper.navigator import Navigator
from scraper.extractor import Extractor
from scraper.writer import Writer


def main():
    """Main entry point for university scraping."""
    # Setup logging
    logger = setup_logging()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape university data from unipage.net')
    parser.add_argument('--country', type=str, default='Turkey', help='Country to scrape')
    args = parser.parse_args()
    
    # Initialize components
    navigator = Navigator(logger)
    extractor = Extractor(logger)
    writer = Writer(logger)
    
    try:
        # Setup browser
        navigator.setup_driver()
        
        # Navigate to country and university
        if not navigator.navigate_to_country(args.country):
            logger.error("Failed to navigate to country page")
            return
            
        if not navigator.navigate_to_university("Bilkent University"):
            logger.error("Failed to navigate to university page")
            return
            
        # Extract common university info
        common_info = extractor.extract_common_info(navigator.get_page_content())
        if not common_info:
            logger.error("Failed to extract common university info")
            return
            
        # Extract programs for each degree level
        all_programs = []
        for degree in ['Bachelor', 'Master', 'Doctorate']:
            logger.info(f"Processing {degree} programs...")
            
            # Navigate and extract program links
            program_links = navigator.navigate_degree_programs(degree)
            if not program_links:
                logger.warning(f"No program links found for {degree}")
                continue
                
            # Extract program details
            for link in program_links:
                try:
                    # Navigate to program page
                    navigator.driver.get(link['url'])
                    time.sleep(2)
                    
                    # Extract program details
                    program_info = extractor.extract_program_info(navigator.get_page_content())
                    if program_info:
                        program_info['degree_level'] = degree
                        all_programs.append(program_info)
                        
                except Exception as e:
                    logger.error(f"Error processing program {link['name']}: {e}")
                    continue
                    
        # Combine all data
        university_data = {
            **common_info,
            'programs': all_programs
        }
        
        # Save to file
        output_file = f"universities/{common_info['name'].lower().replace(' ', '_')}.json"
        writer.save_to_json(university_data, output_file)
        
        logger.info(f"Successfully scraped {len(all_programs)} programs")
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
    finally:
        navigator.close()


if __name__ == "__main__":
    main()
