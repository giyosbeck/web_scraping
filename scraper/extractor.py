import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any

class DataExtractor:
    """
    Extracts university data from HTML content and structures it according to the schema.
    """
    
    def __init__(self, html_content: str, current_url: str = None):
        """
        Initialize the DataExtractor with raw HTML content.
        
        Args:
            html_content (str): Raw HTML content to parse
            current_url (str, optional): Current page URL for fallback extraction
        """
        self.html_content = html_content
        self.current_url = current_url
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.logger = logging.getLogger(__name__)
        self.logger.info("DataExtractor initialized with HTML content")
    
    def extract_main_info(self) -> Dict[str, Any]:
        """
        Extract main university information from page title and Quick Facts table.
        
        Returns:
            Dict containing main university information
        """
        main_info = {}
        
        try:
            # Extract university name from h1.page-title
            page_title = self.soup.find('h1', class_='page-title')
            if page_title:
                main_info['name'] = page_title.get_text(strip=True)
                self.logger.info(f"Successfully extracted university name from h1.page-title: {main_info['name']}")
            else:
                self.logger.debug("h1.page-title selector failed, trying fallback h1 tag")
                # Fallback to any h1 tag
                h1_tag = self.soup.find('h1')
                if h1_tag:
                    main_info['name'] = h1_tag.get_text(strip=True)
                    self.logger.info(f"Successfully extracted university name from h1 fallback: {main_info['name']}")
                else:
                    self.logger.debug("h1 fallback selector failed, trying URL-based extraction")
                    # URL-based fallback using extract_university_name_from_url
                    if self.current_url:
                        main_info['name'] = self._extract_university_name_from_url(self.current_url)
                        self.logger.info(f"Successfully extracted university name from URL: {main_info['name']}")
                    else:
                        main_info['name'] = "Unknown University"
                        self.logger.warning("All university name extraction methods failed")
            
            # Extract Quick Facts from table
            quick_facts_table = self.soup.find('table', class_='quick-facts') or self.soup.find('div', class_='quick-facts')
            if quick_facts_table:
                facts = {}
                rows = quick_facts_table.find_all('tr') if quick_facts_table.name == 'table' else quick_facts_table.find_all('div', class_='fact-row')
                
                for row in rows:
                    cells = row.find_all(['td', 'th', 'div'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower().replace(' ', '_')
                        value = cells[1].get_text(strip=True)
                        facts[key] = value
                
                main_info['quick_facts'] = facts
                self.logger.info(f"Successfully extracted {len(facts)} quick facts from table.quick-facts or div.quick-facts")
                
                # Extract city from quick facts if available
                city_keys = ['city', 'location', 'address', 'campus_location']
                for key in city_keys:
                    if key in facts and facts[key]:
                        main_info['city'] = facts[key]
                        self.logger.info(f"Successfully extracted city from quick facts: {main_info['city']}")
                        break
            else:
                main_info['quick_facts'] = {}
                self.logger.debug("Quick facts selectors (table.quick-facts, div.quick-facts) failed")
                
                # Try to extract city from URL or page metadata as fallback
                if not main_info.get('city'):
                    city = self._extract_city_fallback()
                    if city:
                        main_info['city'] = city
                        self.logger.info(f"Successfully extracted city from fallback method: {city}")
                    else:
                        self.logger.warning("All city extraction methods failed")
                
        except Exception as e:
            self.logger.error(f"Error extracting main info: {str(e)}")
            main_info = {'name': 'Unknown University', 'quick_facts': {}}
        
        return main_info
    
    def extract_contents(self) -> Dict[str, Any]:
        """
        Extract university description and student figures.
        
        Returns:
            Dict containing description and student information
        """
        contents = {}
        
        try:
            # Extract description from .university-description
            description_elem = self.soup.find(class_='university-description')
            if description_elem:
                contents['description'] = description_elem.get_text(strip=True)
                self.logger.info("Successfully extracted university description from .university-description")
            else:
                self.logger.debug(".university-description selector failed, trying fallback selectors")
                # Fallback to common description selectors
                fallback_selectors = ['.description', '.about', '.overview', 'p']
                description_found = False
                for selector in fallback_selectors:
                    elem = self.soup.select_one(selector)
                    if elem and len(elem.get_text(strip=True)) > 100:
                        contents['description'] = elem.get_text(strip=True)
                        self.logger.info(f"Successfully extracted university description from fallback selector: {selector}")
                        description_found = True
                        break
                    else:
                        self.logger.debug(f"Fallback selector {selector} failed or content too short")
                
                if not description_found:
                    contents['description'] = ""
                    self.logger.warning("All university description extraction methods failed")
            
            # Extract student figures
            student_figures = {}
            
            # Look for student enrollment numbers
            enrollment_patterns = ['enrollment', 'students', 'student_count', 'total_students']
            enrollment_found = False
            for pattern in enrollment_patterns:
                elem = self.soup.find(text=lambda text: text and pattern.lower() in text.lower())
                if elem:
                    parent = elem.parent
                    if parent:
                        text = parent.get_text(strip=True)
                        # Extract numbers from text
                        import re
                        numbers = re.findall(r'\d+(?:,\d+)*', text)
                        if numbers:
                            student_figures['total_enrollment'] = numbers[0].replace(',', '')
                            self.logger.info(f"Successfully extracted student enrollment using pattern '{pattern}': {student_figures['total_enrollment']}")
                            enrollment_found = True
                            break
                        else:
                            self.logger.debug(f"Pattern '{pattern}' found but no numbers extracted from text: {text}")
                    else:
                        self.logger.debug(f"Pattern '{pattern}' found but parent element is None")
                else:
                    self.logger.debug(f"Enrollment pattern '{pattern}' not found in page text")
            
            if not enrollment_found:
                self.logger.warning("All student enrollment extraction methods failed")
            
            contents['student_figures'] = student_figures
            self.logger.info(f"Final student figures extracted: {student_figures}")
            
        except Exception as e:
            self.logger.error(f"Error extracting contents: {str(e)}")
            contents = {'description': '', 'student_figures': {}}
        
        return contents
    
    def extract_tuition_fees(self) -> Dict[str, Any]:
        """
        Extract tuition fees information from .tuition-fees-section.
        
        Returns:
            Dict containing tuition fees data
        """
        tuition_fees = {}
        
        try:
            fees_section = self.soup.find(class_='tuition-fees-section')
            if fees_section:
                # Extract fee information
                fee_items = fees_section.find_all(['div', 'p', 'li'])
                fees = {}
                
                for item in fee_items:
                    text = item.get_text(strip=True)
                    if '$' in text or '€' in text or '£' in text or 'fee' in text.lower():
                        # Parse fee information
                        import re
                        currency_match = re.search(r'[\$€£]\s*(\d+(?:,\d+)*(?:\.\d+)?)', text)
                        if currency_match:
                            amount = currency_match.group(1).replace(',', '')
                            fee_type = text.split(':')[0].strip() if ':' in text else 'tuition'
                            fees[fee_type.lower().replace(' ', '_')] = {
                                'amount': amount,
                                'currency': currency_match.group(0)[0],
                                'description': text
                            }
                
                tuition_fees['fees'] = fees
                self.logger.info(f"Successfully extracted {len(fees)} fee items from .tuition-fees-section")
            else:
                tuition_fees['fees'] = {}
                self.logger.debug(".tuition-fees-section selector failed")
                self.logger.warning("Tuition fees section not found")
                
        except Exception as e:
            self.logger.error(f"Error extracting tuition fees: {str(e)}")
            tuition_fees = {'fees': {}}
        
        return tuition_fees
    
    def extract_study_programs(self) -> Dict[str, Any]:
        """
        Extract study programs from .programs-section.
        
        Returns:
            Dict containing study programs data
        """
        study_programs = {}
        
        try:
            programs_section = self.soup.find(class_='programs-section')
            if programs_section:
                programs = []
                
                # Look for program listings
                program_items = programs_section.find_all(['div', 'li', 'h3', 'h4'])
                
                for item in program_items:
                    text = item.get_text(strip=True)
                    if text and len(text) > 5:  # Filter out empty or very short items
                        program = {
                            'name': text,
                            'level': self._determine_program_level(text),
                            'description': text
                        }
                        programs.append(program)
                
                study_programs['programs'] = programs
                self.logger.info(f"Successfully extracted {len(programs)} study programs from .programs-section")
            else:
                study_programs['programs'] = []
                self.logger.debug(".programs-section selector failed")
                self.logger.warning("Study programs section not found")
                
        except Exception as e:
            self.logger.error(f"Error extracting study programs: {str(e)}")
            study_programs = {'programs': []}
        
        return study_programs
    
    def extract_rankings(self) -> Dict[str, Any]:
        """
        Extract university rankings from .rankings-section.
        
        Returns:
            Dict containing rankings data
        """
        rankings = {}
        
        try:
            rankings_section = self.soup.find(class_='rankings-section')
            if rankings_section:
                ranking_items = []
                
                # Look for ranking information
                items = rankings_section.find_all(['div', 'p', 'li'])
                
                for item in items:
                    text = item.get_text(strip=True)
                    if any(keyword in text.lower() for keyword in ['rank', 'position', '#', 'top']):
                        import re
                        # Extract ranking number
                        rank_match = re.search(r'#?(\d+)', text)
                        if rank_match:
                            ranking_item = {
                                'rank': int(rank_match.group(1)),
                                'source': self._extract_ranking_source(text),
                                'description': text
                            }
                            ranking_items.append(ranking_item)
                
                rankings['rankings'] = ranking_items
                self.logger.info(f"Successfully extracted {len(ranking_items)} rankings from .rankings-section")
            else:
                rankings['rankings'] = []
                self.logger.debug(".rankings-section selector failed")
                self.logger.warning("Rankings section not found")
                
        except Exception as e:
            self.logger.error(f"Error extracting rankings: {str(e)}")
            rankings = {'rankings': []}
        
        return rankings
    
    def extract_json_ld(self) -> Dict[str, Any]:
        """
        Parse JSON-LD structured data from script tags for fallback information.
        
        Returns:
            Dict containing JSON-LD data
        """
        json_ld_data = {}
        
        try:
            script_tags = self.soup.find_all('script', type='application/ld+json')
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        json_ld_data.update(data)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                json_ld_data.update(item)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON-LD: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted JSON-LD data with {len(json_ld_data)} keys")
            
        except Exception as e:
            self.logger.error(f"Error extracting JSON-LD: {str(e)}")
        
        return json_ld_data
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Combine all extracted data into final dictionary matching the schema structure.
        
        Returns:
            Dict containing all extracted university data
        """
        try:
            self.logger.info("Starting comprehensive data extraction")
            
            # Extract all sections
            main_info = self.extract_main_info()
            contents = self.extract_contents()
            tuition_fees = self.extract_tuition_fees()
            study_programs = self.extract_study_programs()
            rankings = self.extract_rankings()
            json_ld = self.extract_json_ld()
            
            # Combine into final structure
            final_data = {
                'university_name': main_info.get('name', 'Unknown University'),
                'main_info': main_info,
                'description': contents.get('description', ''),
                'student_figures': contents.get('student_figures', {}),
                'tuition_fees': tuition_fees,
                'study_programs': study_programs,
                'rankings': rankings,
                'json_ld_data': json_ld,
                'extraction_metadata': {
                    'timestamp': self._get_timestamp(),
                    'source': 'UniPage.net',
                    'extractor_version': '1.0.0'
                }
            }
            
            # Use JSON-LD data as fallback for missing information
            if json_ld and not final_data['description']:
                final_data['description'] = json_ld.get('description', '')
            
            if json_ld and not final_data['university_name']:
                final_data['university_name'] = json_ld.get('name', 'Unknown University')
            
            self.logger.info("Data extraction completed successfully")
            return final_data
            
        except Exception as e:
            self.logger.error(f"Error in extract_all: {str(e)}")
            return {
                'university_name': 'Unknown University',
                'main_info': {},
                'description': '',
                'student_figures': {},
                'tuition_fees': {'fees': {}},
                'study_programs': {'programs': []},
                'rankings': {'rankings': []},
                'json_ld_data': {},
                'extraction_metadata': {
                    'timestamp': self._get_timestamp(),
                    'source': 'UniPage.net',
                    'extractor_version': '1.0.0',
                    'error': str(e)
                }
            }
    
    def _determine_program_level(self, program_text: str) -> str:
        """
        Determine the academic level of a program based on its text.
        
        Args:
            program_text (str): Program description text
            
        Returns:
            str: Program level (bachelor, master, phd, etc.)
        """
        text_lower = program_text.lower()
        
        if any(keyword in text_lower for keyword in ['bachelor', 'b.s.', 'b.a.', 'undergraduate']):
            return 'bachelor'
        elif any(keyword in text_lower for keyword in ['master', 'm.s.', 'm.a.', 'graduate']):
            return 'master'
        elif any(keyword in text_lower for keyword in ['phd', 'ph.d.', 'doctorate', 'doctoral']):
            return 'phd'
        else:
            return 'unknown'
    
    def _extract_ranking_source(self, ranking_text: str) -> str:
        """
        Extract the source of a ranking from its text.
        
        Args:
            ranking_text (str): Ranking description text
            
        Returns:
            str: Ranking source
        """
        common_sources = ['QS', 'Times Higher Education', 'THE', 'US News', 'Shanghai', 'ARWU']
        
        for source in common_sources:
            if source.lower() in ranking_text.lower():
                return source
        
        return 'Unknown'
    
    def _extract_university_name_from_url(self, uni_url: str) -> str:
        """
        Extract university name from university URL pattern.
        
        Args:
            uni_url (str): URL like https://www.unipage.net/en/12345/university-name
            
        Returns:
            str: University name extracted from URL
        """
        try:
            import re
            from urllib.parse import urlparse
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
    
    def _extract_city_fallback(self) -> str:
        """
        Extract city from URL or page metadata as fallback.
        
        Returns:
            str: City name or empty string if not found
        """
        try:
            # Try to extract from meta tags
            meta_selectors = [
                'meta[name="geo.placename"]',
                'meta[property="og:locality"]',
                'meta[name="location"]',
                'meta[name="city"]'
            ]
            
            for selector in meta_selectors:
                meta_tag = self.soup.select_one(selector)
                if meta_tag and meta_tag.get('content'):
                    city = meta_tag.get('content').strip()
                    self.logger.debug(f"Successfully extracted city from meta tag {selector}: {city}")
                    return city
                else:
                    self.logger.debug(f"Meta selector {selector} failed")
            
            # Try to extract from structured data
            script_tags = self.soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Look for address or location information
                        if 'address' in data:
                            address = data['address']
                            if isinstance(address, dict):
                                city = address.get('addressLocality') or address.get('city')
                                if city:
                                    self.logger.debug(f"Successfully extracted city from JSON-LD address: {city}")
                                    return city
                        if 'location' in data:
                            location = data['location']
                            if isinstance(location, dict):
                                city = location.get('name') or location.get('addressLocality')
                                if city:
                                    self.logger.debug(f"Successfully extracted city from JSON-LD location: {city}")
                                    return city
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            self.logger.debug("All city fallback extraction methods failed")
            return ""
            
        except Exception as e:
            self.logger.error(f"Error in city fallback extraction: {str(e)}")
            return ""
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
