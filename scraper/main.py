import argparse
import sys
import re
from urllib.parse import urlparse
from scraper.logger_config import setup_logging, get_logger
from scraper.navigator import WebNavigator
from scraper.extractor import DataExtractor
from scraper.writer import DataWriter


def extract_country_from_url(country_url: str) -> str:
    """
    Extract country name from country URL pattern.
    
    Args:
        country_url (str): URL like https://www.unipage.net/en/universities_usa_ab
        
    Returns:
        str: Country name extracted from URL
    """
    try:
        # Extract country slug from URL pattern /en/universities_{country}_ab
        match = re.search(r'/en/universities_([^_]+)_ab', country_url)
        if match:
            country_slug = match.group(1)
            # Convert slug to readable name (replace underscores with spaces, capitalize)
            country_name = country_slug.replace('_', ' ').title()
            return country_name
        else:
            # Fallback: extract from URL path
            path = urlparse(country_url).path
            parts = path.strip('/').split('/')
            if len(parts) >= 2:
                return parts[-1].replace('_', ' ').title()
            return "Unknown"
    except Exception:
        return "Unknown"


def extract_university_name_from_url(uni_url: str) -> str:
    """
    Extract university name from university URL pattern.
    
    Args:
        uni_url (str): URL like https://www.unipage.net/en/12345/university-name
        
    Returns:
        str: University name extracted from URL
    """
    try:
        # Extract name from URL pattern /en/{id}/{name}
        match = re.search(r'/en/\d+/([^/?]+)', uni_url)
        if match:
            name_slug = match.group(1)
            # Convert slug to readable name (replace hyphens/underscores with spaces, capitalize)
            uni_name = name_slug.replace('-', ' ').replace('_', ' ').title()
            return uni_name
        else:
            # Fallback: extract from URL path
            path = urlparse(uni_url).path
            parts = path.strip('/').split('/')
            if len(parts) >= 3:
                return parts[-1].replace('-', ' ').replace('_', ' ').title()
            return "Unknown University"
    except Exception:
        return "Unknown University"


def parse_args():
    parser = argparse.ArgumentParser(description="UniPage.net scraper")
    parser.add_argument(
        "--countries",
        type=str,
        default="all",
        help='Comma-separated list of country names or "all" to process all discovered countries'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging()
    logger = get_logger(__name__)

    navigator = None
    try:
        navigator = WebNavigator(headless=True, timeout=10)
        writer = DataWriter()

        # Open home page and discover country URLs
        logger.info("Opening home page and discovering countries...")
        if not navigator.open_home_page():
            logger.error("Failed to open home page, exiting")
            return

        # Get all available country URLs
        country_urls = navigator.get_country_links()
        if not country_urls:
            logger.error("No country URLs discovered, exiting")
            return

        logger.info(f"Discovered {len(country_urls)} countries")

        # Filter country URLs by --countries argument if specified
        if args.countries.lower() != "all":
            requested_countries = [c.strip().lower() for c in args.countries.split(",") if c.strip()]
            filtered_urls = []
            
            for country_url in country_urls:
                country_name = extract_country_from_url(country_url).lower()
                if any(req_country in country_name or country_name in req_country 
                       for req_country in requested_countries):
                    filtered_urls.append(country_url)
            
            if not filtered_urls:
                logger.warning(f"No countries matched the filter: {args.countries}")
                logger.info("Available countries: %s", 
                           [extract_country_from_url(url) for url in country_urls[:10]])
                return
            
            country_urls = filtered_urls
            logger.info(f"Filtered to {len(country_urls)} countries based on --countries argument")

        # Process each country
        for country_url in country_urls:
            country_name = extract_country_from_url(country_url)
            logger.info("Processing country: %s (%s)", country_name, country_url)
            
            # Navigate to country page
            if not navigator.open_url(country_url):
                logger.error("Skipping country %s: failed to open country page", country_name)
                continue

            # Get university links from country page
            university_links = navigator.get_university_links()
            
            # Fallback to sitemap if no links found on country page
            if not university_links:
                logger.warning("No university links found on country page, trying sitemap fallback")
                sitemap_links = navigator.get_university_urls_from_sitemap()
                if sitemap_links:
                    # Filter sitemap links that might be relevant to this country
                    # This is a best-effort approach since sitemap doesn't have country info
                    university_links = sitemap_links[:50]  # Limit to avoid overwhelming
                    logger.info(f"Using {len(university_links)} links from sitemap as fallback")
                else:
                    logger.error("No university links found for country %s, skipping", country_name)
                    continue
            
            logger.info(f"Found {len(university_links)} university links for {country_name}")

            # Process each university
            for uni_url in university_links:
                logger.debug("Processing university: %s", uni_url)
                
                # Navigate to university page
                if not navigator.navigate_to_university(uni_url):
                    logger.warning("Failed to open university URL: %s", uni_url)
                    continue
                
                # Get page HTML
                html = navigator.get_page_source()
                if html is None:
                    logger.warning("No page source for URL: %s", uni_url)
                    continue

                # Extract university data
                extractor = DataExtractor(html)
                record = extractor.extract_all()

                # Get city and university name from extracted data or URL fallback
                city = ""
                uni_name = ""
                
                try:
                    # Try to get city from extracted data
                    city = record.get("main_info", {}).get("city", "")
                    if not city:
                        # Try quick_facts for location info
                        quick_facts = record.get("main_info", {}).get("quick_facts", {})
                        city = quick_facts.get("city", "") or quick_facts.get("location", "")
                except Exception:
                    logger.warning("City not found in extracted data for URL: %s", uni_url)
                
                try:
                    # Try to get university name from extracted data
                    uni_name = record.get("university_name", "")
                    if not uni_name:
                        uni_name = record.get("main_info", {}).get("name", "")
                except Exception:
                    logger.warning("University name not found in extracted data for URL: %s", uni_url)
                
                # Fallback to URL parsing if data extraction failed
                if not city:
                    city = "Unknown"
                if not uni_name:
                    uni_name = extract_university_name_from_url(uni_url)

                # Save university data
                success = writer.save_university_data(country_name, city, uni_name, record)
                if not success:
                    logger.error("Failed to save data for %s at %s", uni_name, uni_url)
                else:
                    logger.info("Successfully saved data for %s in %s, %s", uni_name, city, country_name)

    except Exception as e:
        logger = logger if "logger" in locals() else None
        if logger:
            logger.error("Unexpected error: %s", str(e), exc_info=True)
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
    finally:
        if navigator:
            navigator.quit()


if __name__ == "__main__":
    main()
