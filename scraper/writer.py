import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any


class DataWriter:
    """
    Handles writing university data to JSON files with proper directory structure.
    """
    
    def __init__(self, base_output_path: str = "unipage_data/"):
        """
        Initialize DataWriter with base output path.
        
        Args:
            base_output_path (str): Base directory for output files
        """
        self.base_output_path = Path(base_output_path)
        self.logger = logging.getLogger(__name__)
        
        # Create base directory if it doesn't exist
        self.base_output_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"DataWriter initialized with base path: {self.base_output_path}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize university name for use as filename.
        
        Args:
            filename (str): Raw university name
            
        Returns:
            str: Sanitized filename safe for filesystem
        """
        # Remove or replace invalid characters for filenames
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Replace multiple spaces/underscores with single underscore
        sanitized = re.sub(r'[_\s]+', '_', sanitized)
        # Remove leading/trailing underscores and spaces
        sanitized = sanitized.strip('_ ')
        # Limit length to avoid filesystem issues
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized
    
    def save_university_data(self, country: str, city: str, uni_name: str, data_dict: Dict[str, Any]) -> bool:
        """
        Save university data to JSON file with proper directory structure.
        
        Args:
            country (str): Country name
            city (str): City name
            uni_name (str): University name
            data_dict (Dict[str, Any]): University data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Sanitize inputs for directory/file names
            sanitized_country = self._sanitize_filename(country)
            sanitized_city = self._sanitize_filename(city)
            sanitized_uni_name = self._sanitize_filename(uni_name)
            
            # Create directory structure: unipage_data/{country}/{city}
            output_dir = self.base_output_path / sanitized_country / sanitized_city
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create output file path
            output_file = output_dir / f"{sanitized_uni_name}.json"
            
            # Write data as pretty-printed JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, sort_keys=True)
            
            self.logger.info(f"Successfully saved university data: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save university data for {uni_name}: {str(e)}")
            return False
    
    def get_output_path(self, country: str, city: str, uni_name: str) -> Path:
        """
        Get the expected output file path for given university.
        
        Args:
            country (str): Country name
            city (str): City name
            uni_name (str): University name
            
        Returns:
            Path: Expected output file path
        """
        sanitized_country = self._sanitize_filename(country)
        sanitized_city = self._sanitize_filename(city)
        sanitized_uni_name = self._sanitize_filename(uni_name)
        
        return self.base_output_path / sanitized_country / sanitized_city / f"{sanitized_uni_name}.json"