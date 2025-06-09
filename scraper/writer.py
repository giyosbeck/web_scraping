"""
University Data Writer - Handles saving extracted university data
"""

import json
import os
from typing import Dict, Any
from scraper.logger_config import get_logger


class Writer:
    def __init__(self, logger):
        self.logger = logger
        
    def save_to_json(self, data, output_file):
        """Save data to JSON file"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Save data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Successfully saved data to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data to {output_file}: {e}")
            return False


class UniversityWriter:
    """Handles saving extracted university data to files."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the writer.
        
        Args:
            output_dir: Directory to save output files
        """
        self.logger = get_logger(__name__)
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                self.logger.info(f"Created output directory: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"Error creating output directory: {e}")
    
    def save_universities_data(self, data: Dict[str, Any], filename: str) -> bool:
        """
        Save universities data to a JSON file.
        
        Args:
            data: University data to save
            filename: Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved universities data to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving universities data: {e}")
            return False
    
    def save_single_university(self, university_data: Dict[str, Any], filename: str = None) -> bool:
        """
        Save a single university's data to a JSON file.
        
        Args:
            university_data: Single university data
            filename: Optional custom filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if filename is None:
                # Generate filename from university name
                uni_name = university_data.get('university', {}).get('name', 'Unknown')
                safe_name = "".join(c for c in uni_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_')
                filename = f"{safe_name}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(university_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved university data to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving single university data: {e}")
            return False