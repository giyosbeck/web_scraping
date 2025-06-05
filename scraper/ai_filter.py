import json
import logging
import re
from typing import List, Dict, Any, Optional
import requests
from dataclasses import dataclass


@dataclass
class CountryFilter:
    """Data class representing a country filter candidate."""
    selector: str
    url: Optional[str] = None
    text: Optional[str] = None


class CountryFilterAI:
    """
    AI-powered helper for detecting country filter elements in HTML pages.
    Uses LLM to analyze raw HTML and propose alternative selectors or direct URLs.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the CountryFilterAI helper.
        
        Args:
            api_key (str, optional): OpenAI API key. If None, will try to get from environment
            model (str): LLM model to use (default: gpt-3.5-turbo)
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
        
        # Try to get API key from environment if not provided
        if not self.api_key:
            import os
            self.api_key = os.getenv('OPENAI_API_KEY')
            
        if not self.api_key:
            self.logger.warning("No OpenAI API key provided. AI filter detection will be disabled.")
    
    def detect_filters(self, page_html: str) -> List[CountryFilter]:
        """
        Analyze HTML content and detect potential country filter elements.
        
        Args:
            page_html (str): Raw HTML content of the page
            
        Returns:
            List[CountryFilter]: List of detected country filter candidates
        """
        if not self.api_key:
            self.logger.warning("No API key available for AI filter detection")
            return []
        
        try:
            # Compose system prompt for the LLM
            system_prompt = self._create_system_prompt()
            
            # Prepare the HTML content (truncate if too long to avoid token limits)
            processed_html = self._preprocess_html(page_html)
            
            # Create user message with the HTML
            user_message = f"Please analyze this HTML and find country filter elements:\n\n{processed_html}"
            
            # Send request to LLM
            response = self._call_llm(system_prompt, user_message)
            
            # Parse and validate the JSON response
            filters = self._parse_response(response)
            
            self.logger.info(f"AI detected {len(filters)} country filter candidates")
            return filters
            
        except Exception as e:
            self.logger.error(f"Error in AI filter detection: {e}")
            return []
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt for the LLM to analyze HTML and find country filters.
        
        Returns:
            str: System prompt text
        """
        return """You are an expert web scraper analyzing HTML to find country filter elements on university listing pages.

Your task is to identify elements that could be used to filter universities by country. Look for:
1. Dropdown selects with country options
2. Links or buttons for specific countries
3. Filter elements with country names
4. Navigation elements that lead to country-specific pages

Return your findings as a JSON array of objects, each with these fields:
- "selector": CSS selector to find the element (required)
- "url": Direct URL if it's a link (optional)
- "text": Visible text content of the element (optional)

Focus on elements that contain country names or could be used to navigate to country-specific university listings.

Example response format:
[
  {
    "selector": ".country-filter select option[value='usa']",
    "url": "https://example.com/universities_usa_ab",
    "text": "United States"
  },
  {
    "selector": ".filter-menu a[href*='canada']",
    "url": "https://example.com/universities_canada_ab", 
    "text": "Canada"
  }
]

Only return valid JSON. If no country filters are found, return an empty array []."""
    
    def _preprocess_html(self, html: str) -> str:
        """
        Preprocess HTML to reduce size and focus on relevant content.
        
        Args:
            html (str): Raw HTML content
            
        Returns:
            str: Processed HTML content
        """
        # Remove script and style tags to reduce noise
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Truncate if too long (keep first 8000 characters to stay within token limits)
        if len(html) > 8000:
            html = html[:8000] + "\n... [HTML truncated for analysis]"
            
        return html
    
    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """
        Make API call to the LLM service.
        
        Args:
            system_prompt (str): System prompt for the LLM
            user_message (str): User message with HTML content
            
        Returns:
            str: LLM response text
            
        Raises:
            Exception: If API call fails
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
            'max_tokens': 1000,
            'temperature': 0.1
        }
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except requests.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise Exception(f"LLM API call failed: {e}")
        except KeyError as e:
            self.logger.error(f"Unexpected API response format: {e}")
            raise Exception(f"Invalid API response format: {e}")
    
    def _parse_response(self, response: str) -> List[CountryFilter]:
        """
        Parse and validate the LLM JSON response.
        
        Args:
            response (str): Raw LLM response text
            
        Returns:
            List[CountryFilter]: Parsed and validated filter candidates
        """
        filters = []
        
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate that it's a list
            if not isinstance(data, list):
                self.logger.warning("LLM response is not a JSON array")
                return []
            
            # Process each filter candidate
            for item in data:
                if not isinstance(item, dict):
                    self.logger.warning(f"Skipping invalid filter item: {item}")
                    continue
                
                # Validate required fields
                selector = item.get('selector')
                if not selector or not isinstance(selector, str):
                    self.logger.warning(f"Skipping filter with invalid selector: {item}")
                    continue
                
                # Extract optional fields
                url = item.get('url')
                text = item.get('text')
                
                # Validate URL if provided
                if url and not isinstance(url, str):
                    self.logger.warning(f"Invalid URL in filter: {item}")
                    url = None
                
                # Validate text if provided
                if text and not isinstance(text, str):
                    text = None
                
                # Create filter object
                filter_obj = CountryFilter(
                    selector=selector.strip(),
                    url=url.strip() if url else None,
                    text=text.strip() if text else None
                )
                
                filters.append(filter_obj)
            
            self.logger.info(f"Successfully parsed {len(filters)} filter candidates")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Raw response: {response}")
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
        
        return filters
    
    def is_available(self) -> bool:
        """
        Check if AI filter detection is available (API key is set).
        
        Returns:
            bool: True if AI detection is available, False otherwise
        """
        return bool(self.api_key)