#!/usr/bin/env python3
"""
Simple AI-driven university scraper for UniPage.net
No hardcoded selectors - let AI figure out how to navigate!
"""
import json
import argparse
import os
import logging
from scraper.logger_config import setup_logging, get_logger
from scraper.ai_navigator import AINavigator


def main():
    """Main entry point for AI-driven university scraping."""
    parser = argparse.ArgumentParser(description="AI-driven UniPage.net scraper")
    parser.add_argument(
        "--url", 
        type=str, 
        default="https://www.unipage.net/en/home",
        help="Starting URL (default: unipage.net home page)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="ai_scraped_universities.json",
        help="Output JSON file (default: ai_scraped_universities.json)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (or set OPENROUTER_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    # Setup logging with DEBUG level
    setup_logging()
    # Enable DEBUG level for debugging
    logging.getLogger().setLevel(logging.DEBUG)
    logger = get_logger(__name__)
    
    # Check for API key
    api_key = args.api_key or os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("No API key provided. Set OPENROUTER_API_KEY environment variable or use --api-key")
        logger.info("Get a free API key from: https://openrouter.ai/")
        return
    
    try:
        logger.info("=== AI-Driven University Scraper Starting ===")
        logger.info(f"Starting URL: {args.url}")
        logger.info(f"Output file: {args.output}")
        
        # Initialize AI Navigator
        navigator = AINavigator(api_key=api_key)
        
        # Let AI scrape the universities
        logger.info("Letting AI analyze the website and extract university data...")
        result = navigator.scrape_university_data(args.url)
        
        # Save results
        if result and result.get("universities"):
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Success! Found {result['total_found']} universities")
            logger.info(f"Data saved to: {args.output}")
            
            # Print summary
            print(f"\nScraping completed!")
            print(f"Universities found: {result['total_found']}")
            print(f"Saved to: {args.output}")
            
            if result["universities"]:
                print(f"\nSample universities:")
                for i, uni in enumerate(result["universities"][:3]):
                    if isinstance(uni, dict):
                        print(f"  {i+1}. {uni.get('name', 'Unknown')} - {uni.get('location', 'Unknown location')}")
                    else:
                        print(f"  {i+1}. {uni}")
                if len(result["universities"]) > 3:
                    print(f"  ... and {len(result['universities']) - 3} more")
        else:
            logger.warning("No universities found. AI might need different prompts or the site structure has changed.")
            print("❌ No universities found. Check the logs for details.")
    
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 