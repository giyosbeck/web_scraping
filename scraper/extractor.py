"""
University Data Extractor - Extracts comprehensive university information using AI
"""

import json
import re
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from scraper.logger_config import get_logger


class Extractor:
    def __init__(self, logger):
        self.logger = logger
        
    def extract_common_info(self, html_content):
        """Extract common university information"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic info
            name = soup.find('h1').text.strip()
            type_elem = soup.find('div', text=re.compile('Type:'))
            uni_type = type_elem.find_next('div').text.strip() if type_elem else 'Unknown'
            
            # Extract location
            location_elem = soup.find('div', text=re.compile('Location:'))
            location_text = location_elem.find_next('div').text.strip() if location_elem else ''
            city = location_text.split(',')[0].strip() if location_text else 'Unknown'
            
            # Extract website
            website_elem = soup.find('a', href=re.compile('^http'))
            website = website_elem['href'] if website_elem else ''
            
            # Extract description
            desc_elem = soup.find('div', text=re.compile('About'))
            description = desc_elem.find_next('div').text.strip() if desc_elem else ''
            
            # Extract rankings
            rankings = {}
            rankings_elem = soup.find('div', text=re.compile('Rankings'))
            if rankings_elem:
                ranking_items = rankings_elem.find_next('div').find_all('div')
                for item in ranking_items:
                    text = item.text.strip()
                    if 'QS' in text:
                        rankings['QS_World_University_Rankings'] = int(re.search(r'\d+', text).group())
                    elif 'THE' in text:
                        rankings['THE_Ranking'] = int(re.search(r'\d+', text).group())
            
            # Extract tuition fees
            tuition = {}
            tuition_elem = soup.find('div', text=re.compile('Tuition fees'))
            if tuition_elem:
                fee_items = tuition_elem.find_next('div').find_all('div')
                for item in fee_items:
                    text = item.text.strip()
                    if 'Bachelor' in text:
                        tuition['bachelor'] = self._extract_fee_info(text)
                    elif 'Master' in text:
                        tuition['master'] = self._extract_fee_info(text)
                    elif 'Doctorate' in text:
                        tuition['doctorate'] = self._extract_fee_info(text)
            
            return {
                'name': name,
                'type': uni_type,
                'location': {
                    'country': 'Turkey',
                    'city': city
                },
                'website': website,
                'about': {
                    'description': description,
                    'rankings': rankings
                },
                'tuition_fees': tuition
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting common info: {e}")
            return None
            
    def extract_program_info(self, html_content):
        """Extract program information"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract program name
            name = soup.find('h1').text.strip()
            
            # Extract study mode
            mode_elem = soup.find('div', text=re.compile('Study mode:'))
            study_mode = mode_elem.find_next('div').text.strip() if mode_elem else 'Unknown'
            
            # Extract duration
            duration_elem = soup.find('div', text=re.compile('Duration:'))
            duration = duration_elem.find_next('div').text.strip() if duration_elem else 'Unknown'
            
            # Extract language
            language_elem = soup.find('div', text=re.compile('Language:'))
            language = language_elem.find_next('div').text.strip() if language_elem else 'Unknown'
            
            # Extract tuition
            tuition_elem = soup.find('div', text=re.compile('Tuition fee:'))
            tuition = self._extract_fee_info(tuition_elem.find_next('div').text.strip()) if tuition_elem else {}
            
            # Extract exams
            exams = []
            exams_elem = soup.find('div', text=re.compile('Exams:'))
            if exams_elem:
                exam_items = exams_elem.find_next('div').find_all('div')
                for item in exam_items:
                    exams.append(item.text.strip())
            
            return {
                'name': name,
                'study_mode': study_mode,
                'duration': duration,
                'language': language,
                'tuition': tuition,
                'exams': exams
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting program info: {e}")
            return None
            
    def _extract_fee_info(self, text):
        """Helper method to extract fee information"""
        try:
            # Extract amount
            amount_match = re.search(r'(\d[\d,]*\.?\d*)', text)
            amount = float(amount_match.group(1).replace(',', '')) if amount_match else None
            
            # Extract currency
            currency_match = re.search(r'(USD|EUR|TRY)', text)
            currency = currency_match.group(1) if currency_match else 'USD'
            
            # Extract period
            period = 'year'
            if 'semester' in text.lower():
                period = 'semester'
            elif 'month' in text.lower():
                period = 'month'
                
            return {
                'amount': amount,
                'currency': currency,
                'period': period
            }
        except:
            return {}

class UniversityExtractor:
    """Extracts comprehensive university data using AI and web scraping."""
    
    def __init__(self, api_key: str, model: str = "deepseek/deepseek-r1:free"):
        """
        Initialize the extractor.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use for AI extraction
        """
        self.logger = get_logger(__name__)
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
    
    def extract_university_data(self, html: str, url: str, program_links: List[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Extract comprehensive university data using multi-pass AI extraction.
        
        Args:
            html: University page HTML
            url: University page URL
        
        Returns:
            dict: Comprehensive university data in the specified format
        """
        try:
            self.logger.info(f"Extracting university data from: {url}")
            
            # Clean and prepare HTML for AI analysis
            clean_html = self._clean_html(html)
            
            # Save debug info about content size
            self.logger.info(f"Original HTML size: {len(html)} characters")
            self.logger.info(f"Cleaned HTML size: {len(clean_html)} characters")
            
            # Count program mentions
            program_keywords = ["bachelor", "master", "phd", "doctorate", "program", "degree"]
            keyword_counts = {}
            for keyword in program_keywords:
                count = clean_html.lower().count(keyword)
                keyword_counts[keyword] = count
            self.logger.info(f"Program keywords in clean HTML: {keyword_counts}")
            
            # Content ready for AI processing
            
            # Use AI to extract comprehensive university data with better error handling
            university_data = self._multi_pass_extraction(clean_html, url)
            
            if university_data:
                # Count extracted programs for comparison
                extracted_programs = self._count_extracted_programs(university_data)
                self.logger.info(f"Successfully extracted data for: {university_data.get('university', {}).get('name', 'Unknown')}")
                self.logger.info(f"Extracted programs: {extracted_programs}")
                
                # Check if we got all expected programs (target: 86 for Bilkent)
                total_extracted = extracted_programs.get('Total', 0)
                if total_extracted < 86:  # We need ALL 86 programs
                    self.logger.warning(f"TARGET MISSED: Extracted {total_extracted}/86 programs, trying enhanced extraction...")
                    enhanced_data = self._enhanced_extraction_pass(clean_html, url, university_data)
                    if enhanced_data:
                        university_data = enhanced_data
                        extracted_programs = self._count_extracted_programs(university_data)
                        total_final = extracted_programs.get('Total', 0)
                        if total_final >= 86:
                            self.logger.info(f"SUCCESS: Enhanced extraction achieved {total_final}/86 programs!")
                        else:
                            self.logger.warning(f"STILL MISSING: {86 - total_final} programs after enhancement")
                        self.logger.info(f"Enhanced extraction: {extracted_programs}")
                
                return university_data
            else:
                self.logger.error("AI failed to extract university data")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting university data: {e}")
            return None
    
    def _clean_html(self, html: str) -> str:
        """
        Clean HTML content for AI analysis while preserving ALL program data.
        
        Args:
            html: Raw HTML content
        
        Returns:
            str: Cleaned HTML content with preserved program information
        """
        try:
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style tags
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content but preserve some structure
            text_content = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)
            
            # INCREASED truncation limit to handle ALL program data (was 25000, now 40000)
            if len(text_content) > 40000:
                # For very large content, use smarter program-focused extraction
                program_keywords = ["bachelor", "master", "phd", "doctorate", "program", "degree", "faculty", 
                                  "engineering", "business", "law", "medicine", "science", "arts", "economics",
                                  "computer", "mathematics", "physics", "chemistry", "architecture", "design"]
                
                # Split into larger chunks and keep ALL program-related content
                words = text_content.split()
                important_chunks = []
                current_chunk = []
                chunk_has_programs = False
                
                for word in words:
                    current_chunk.append(word)
                    
                    # Check if this word indicates program content
                    if any(keyword in word.lower() for keyword in program_keywords):
                        chunk_has_programs = True
                    
                    # When chunk reaches good size, decide whether to keep it
                    if len(current_chunk) >= 100:  # Larger chunks for better context
                        if chunk_has_programs or len(important_chunks) == 0:  # Always keep first chunk
                            important_chunks.append(' '.join(current_chunk))
                        
                        # Reset for next chunk
                        current_chunk = []
                        chunk_has_programs = False
                
                # Add final chunk if it has content
                if current_chunk:
                    important_chunks.append(' '.join(current_chunk))
                
                # Combine important chunks
                if important_chunks:
                    text_content = ' '.join(important_chunks)
                
                # Only truncate if EXTREMELY large (was 25000, now 40000)
                if len(text_content) > 40000:
                    self.logger.warning(f"Content still large ({len(text_content)} chars), keeping first 40K chars")
                    text_content = text_content[:40000] + "\n... [Content truncated but program data prioritized]"
            
            self.logger.info(f"Final cleaned content size: {len(text_content)} characters")
            return text_content
            
        except Exception as e:
            self.logger.error(f"Error cleaning HTML: {e}")
            return html[:25000]  # Fallback to truncated raw HTML
    
    def _multi_pass_extraction(self, content: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Use multiple extraction passes to get comprehensive program data.
        """
        try:
            # First pass: Basic extraction with comprehensive cheatsheet
            self.logger.info("Starting Pass 1: Comprehensive extraction with AI cheatsheet")
            university_data = self._ai_extract_with_cheatsheet(content, url)
            
            if university_data:
                programs_count = self._count_extracted_programs(university_data).get('Total', 0)
                self.logger.info(f"Pass 1 extracted: {programs_count} programs")
                
                if programs_count >= 86:  # Target achieved - we need ALL 86 programs
                    self.logger.info(f"TARGET ACHIEVED: {programs_count}/86 programs extracted!")
                    return university_data
                
                # Second pass: Fill missing programs using targeted extraction
                self.logger.info("Starting Pass 2: Targeted missing program extraction")
                enhanced_data = self._extract_missing_programs(content, university_data)
                if enhanced_data:
                    return enhanced_data
            
            return university_data
                
        except Exception as e:
            self.logger.error(f"Multi-pass extraction failed: {e}")
            return None
    
    def _ai_extract_with_cheatsheet(self, content: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract university data using AI with comprehensive cheatsheet for faster processing.
        """
        system_prompt = """Extract ALL university programs from Bilkent University.

TARGET: Find 86 total programs (Bachelor, Master, Doctorate levels).

TASK: Extract every program mentioned in the content. The content contains 500+ program mentions.

Return ONLY valid JSON in this EXACT structure with ALL programs:

{{
  "university": {{
    "name": "Bilkent University",
    "type": "private non-profit",
    "location": {{
      "country": "Turkey",
      "city": "Ankara"
    }},
    "website": "http://www.bilkent.edu.tr",
    "about": {{
      "description": "Description here",
      "establishment_year": 1984,
      "students": {{
        "total": 9961,
        "international": 521,
        "female_percentage": 46
      }},
      "rankings": {{
        "QS_World_University_Rankings_2025": 477,
        "THE_Ranking": 701,
        "by_subject": {{
          "Social_Sciences_And_Management": {{"QS_2024": 276}}
        }}
      }},
      "degrees_offered": ["Bachelor", "Master", "Doctorate"]
    }},
    "tuition_fees": {{
      "academic_calendar": "Semesters",
      "calculation_period": "Per year",
      "bachelor": {{
        "local": {{"cost": 4165, "currency": "USD", "period": "year"}},
        "foreign": {{"cost": 14468, "currency": "USD", "period": "year"}}
      }},
      "financial_aid": "Yes",
      "additional_costs": ["accommodation", "transportation"],
      "website_for_details": "http://www.bilkent.edu.tr"
    }},
    "study_programs": [
      {{
        "level": "Bachelor",
        "faculties": [
          {{
            "name": "Faculty of Law",
            "programs": [
              {{
                "name": "Law",
                "study_mode": "On campus",
                "study_form": "Full-time",
                "duration_months": 48,
                "exams": ["IELTS", "TOEFL"],
                "study_field": "Law",
                "exam_scores": {{"IELTS": 6.5, "TOEFL_iBT": 87}},
                "program_page": null,
                "price": {{"cost": 16945, "currency": "USD", "period": "year"}}
              }}
            ]
          }},
          {{
            "name": "Faculty of Economics, Administrative and Social Sciences",
            "programs": [
              // EXTRACT ALL PROGRAMS FROM THIS FACULTY - should be 8-10+ programs
            ]
          }},
          {{
            "name": "Faculty of Engineering",
            "programs": [
              // EXTRACT ALL ENGINEERING PROGRAMS - should be 6-8+ programs
            ]
          }},
          {{
            "name": "Faculty of Science",
            "programs": [
              // EXTRACT ALL SCIENCE PROGRAMS - should be 6-8+ programs
            ]
          }},
          {{
            "name": "Faculty of Humanities and Letters",
            "programs": [
              // EXTRACT ALL HUMANITIES PROGRAMS - should be 8-10+ programs
            ]
          }},
          {{
            "name": "Faculty of Art, Design and Architecture",
            "programs": [
              // EXTRACT ALL ART/DESIGN PROGRAMS - should be 6-8+ programs
            ]
          }},
          {{
            "name": "Faculty of Applied Sciences",
            "programs": [
              // EXTRACT ALL APPLIED SCIENCES PROGRAMS
            ]
          }}
        ]
      }},
      {{
        "level": "Master",
        "faculties": [
          // EXTRACT ALL MASTER PROGRAMS - should be 30-35+ programs
        ]
      }},
      {{
        "level": "Doctorate",
        "faculties": [
          // EXTRACT ALL DOCTORATE PROGRAMS - should be 15-20+ programs
        ]
      }}
    ]
  }}
}}

CRITICAL RULES:
1. TARGET: Extract ALL 86 programs
2. Check EVERY faculty and department 
3. Look for variations: BSc, BA, MSc, MA, MBA, LLM, PhD, Ph.D.
4. Include specialized and professional programs
5. Don't skip anything - be exhaustive
6. Return ONLY valid JSON"""

        user_message = f"""Extract ALL 86 university programs from Bilkent University. Use the cheatsheet above to ensure comprehensive extraction.

Content to analyze:
{content}

Target: 86 programs total. Return complete JSON with ALL programs."""

        return self._call_ai_api(system_prompt, user_message)
    
    def _extract_missing_programs(self, content: str, current_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Targeted extraction to find programs that were missed in the first pass.
        """
        try:
            current_count = self._count_extracted_programs(current_data).get('Total', 0)
            missing_count = 86 - current_count
            
            if missing_count <= 0:
                return current_data
            
            self.logger.info(f"Looking for {missing_count} missing programs...")
            
            # Extract current program names for comparison
            current_programs = self._extract_current_program_names(current_data)
            
            missing_prompt = f"""You are a specialized program hunter. Your job is to find the {missing_count} MISSING programs from Bilkent University.

CURRENT PROGRAMS ALREADY EXTRACTED ({current_count} programs):
{current_programs}

CRITICAL TASK: Find the {missing_count} MISSING programs that were not extracted above.

Look through the content carefully for:
1. Programs mentioned but not in the current list
2. Alternative program names or variations
3. Specialized or professional programs
4. Programs in different faculties
5. Joint degree programs
6. Certificate programs
7. Double major programs

Return ONLY the missing programs in this JSON format:
{{
  "missing_programs": [
    {{
      "level": "Bachelor",
      "faculty": "Faculty Name",
      "program": {{
        "name": "Program Name",
        "study_mode": "On campus",
        "study_form": "Full-time",
        "duration_months": 48,
        "exams": ["IELTS", "TOEFL"],
        "study_field": "Field Name",
        "exam_scores": {{"IELTS": 6.5, "TOEFL_iBT": 87}},
        "program_page": null,
        "price": {{"cost": 14468, "currency": "USD", "period": "year"}}
      }}
    }}
  ]
}}

Content to search: {content[:15000]}"""

            missing_data = self._call_ai_api(missing_prompt, "Find all missing programs")
            
            if missing_data and 'missing_programs' in missing_data:
                # Merge missing programs with current data
                return self._merge_missing_programs(current_data, missing_data['missing_programs'])
            
            return current_data
                
        except Exception as e:
            self.logger.error(f"Error extracting missing programs: {e}")
            return current_data
    
    def _extract_current_program_names(self, data: Dict[str, Any]) -> str:
        """Extract current program names for comparison."""
        try:
            programs = []
            study_programs = data.get('university', {}).get('study_programs', [])
            
            for level_data in study_programs:
                level = level_data.get('level', 'Unknown')
                faculties = level_data.get('faculties', [])
                
                for faculty in faculties:
                    faculty_name = faculty.get('name', 'Unknown')
                    faculty_programs = faculty.get('programs', [])
                    
                    for program in faculty_programs:
                        program_name = program.get('name', 'Unknown')
                        programs.append(f"{level} - {faculty_name} - {program_name}")
            
            return '\n'.join(programs)
                
        except Exception as e:
            self.logger.error(f"Error extracting current program names: {e}")
            return "Error extracting current programs"
    
    def _merge_missing_programs(self, current_data: Dict[str, Any], missing_programs: List[Dict]) -> Dict[str, Any]:
        """Merge missing programs into current data."""
        try:
            study_programs = current_data.get('university', {}).get('study_programs', [])
            
            for missing in missing_programs:
                level = missing.get('level')
                faculty_name = missing.get('faculty')
                program_data = missing.get('program')
                
                # Find or create level
                level_found = False
                for level_data in study_programs:
                    if level_data.get('level') == level:
                        # Find or create faculty
                        faculties = level_data.get('faculties', [])
                        faculty_found = False
                        
                        for faculty in faculties:
                            if faculty.get('name') == faculty_name:
                                faculty['programs'].append(program_data)
                                faculty_found = True
                                break
                        
                        if not faculty_found:
                            faculties.append({
                                "name": faculty_name,
                                "programs": [program_data]
                            })
                        
                        level_found = True
                        break
                
                if not level_found:
                    study_programs.append({
                        "level": level,
                        "faculties": [{
                            "name": faculty_name,
                            "programs": [program_data]
                        }]
                    })
            
            return current_data
            
        except Exception as e:
            self.logger.error(f"Error merging missing programs: {e}")
            return current_data
    
    def _enhanced_extraction_pass(self, content: str, url: str, current_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enhanced extraction pass using different AI strategy.
        """
        try:
            current_count = self._count_extracted_programs(current_data).get('Total', 0)
            
            enhanced_prompt = f"""ENHANCED EXTRACTION PASS - BILKENT UNIVERSITY

Previous extraction found {current_count} programs, but we need 86 total.

ENHANCED STRATEGY:
1. Scan for EVERY mention of degrees: BSc, BA, MSc, MA, MBA, LLM, PhD, Ph.D.
2. Look for program lists, tables, and course catalogs
3. Check for variations in program names
4. Include all specializations and concentrations
5. Look for certificate and diploma programs
6. Check for double degree and joint programs

CRITICAL: Extract EVERY SINGLE program you can find. We need ALL 86 programs.

Return the complete university data with ALL programs found:

{self.system_prompt.split('CRITICAL: You must return valid JSON')[1]}"""

            return self._call_ai_api(enhanced_prompt, content)
            
        except Exception as e:
            self.logger.error(f"Enhanced extraction pass failed: {e}")
            return current_data
    
    def _call_ai_api(self, system_prompt: str, user_message: str) -> str:
        """
        Call the AI API with the given prompts.
        
        Args:
            system_prompt: System prompt
            user_message: User message
            
        Returns:
            str: AI response
        """
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
            'max_tokens': 8000,
            'temperature': 0.1
        }
        
        try:
            self.logger.debug("Making API call to extract university data")
            
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=120  # Increased timeout for comprehensive extraction
            )
            
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            self.logger.debug("API call successful")
            return content
            
        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            raise
    
    def _parse_ai_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse and validate the AI JSON response.
        
        Args:
            response: Raw AI response
            
        Returns:
            dict: Parsed university data
        """
        try:
            # Clean the response - remove markdown code blocks if present
            clean_response = self._strip_markdown_json(response)
            
            # Parse JSON
            data = json.loads(clean_response)
            
            # Validate the structure
            if "university" in data and isinstance(data["university"], dict):
                self.logger.debug("Successfully parsed AI response")
                return data
            else:
                self.logger.error("Invalid university data structure in AI response")
                return None
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Raw response: {response[:500]}...")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _strip_markdown_json(self, response: str) -> str:
        """
        Strip markdown code block formatting from JSON response.
        
        Args:
            response: Raw response with potential markdown
        
        Returns:
            str: Clean JSON string
        """
        # Remove ```json ... ``` blocks
        response = re.sub(r'```json\s*\n?', '', response, flags=re.IGNORECASE)
        response = re.sub(r'```\s*$', '', response)
        response = re.sub(r'^\s*```\s*', '', response)
        
        return response.strip()
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    def _count_extracted_programs(self, university_data: Any) -> Dict[str, int]:
        """Count how many programs were extracted by level."""
        try:
            # Handle case where AI returns string instead of dict
            if isinstance(university_data, str):
                self.logger.warning("University data is string, attempting to parse as JSON")
                try:
                    university_data = json.loads(university_data)
                except:
                    return {"error": "invalid_json_string", "Total": 0}
            
            if not isinstance(university_data, dict):
                return {"error": "invalid_data_type", "Total": 0}
            
            counts = {"Bachelor": 0, "Master": 0, "Doctorate": 0, "Total": 0}
            
            study_programs = university_data.get("university", {}).get("study_programs", [])
            for level_data in study_programs:
                level = level_data.get("level", "Unknown")
                faculties = level_data.get("faculties", [])
                
                level_count = 0
                for faculty in faculties:
                    programs = faculty.get("programs", [])
                    level_count += len(programs)
                
                if level in counts:
                    counts[level] = level_count
                counts["Total"] += level_count
            
            return counts
        except Exception as e:
            self.logger.error(f"Error counting programs: {e}")
            return {"error": "count_failed", "Total": 0}
