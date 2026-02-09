"""
Google Sheets Connector Module
Fetches work report data directly from Google Sheets via CSV export.
"""

import pandas as pd
import requests
import logging
from typing import Optional
from io import StringIO

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleGoogleSheetConnector:
    """
    Simple connector to fetch data from Google Sheets via CSV export.
    """
    
    def __init__(self, sheet_url: str, timeout: int = 30):
        """
        Initialize with Google Sheet URL.
        
        Args:
            sheet_url: Full Google Sheet export URL
            timeout: Request timeout in seconds
        """
        self.sheet_url = sheet_url
        self.timeout = timeout
        logger.info(f"Initialized Google Sheet connector with URL: {sheet_url}")
    
    def get_work_reports(self, gid: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch work reports from Google Sheet.
        
        Args:
            gid: Optional sheet ID (overrides gid in URL if provided)
            
        Returns:
            DataFrame with work report data
        """
        try:
            # Build the final URL
            final_url = self.sheet_url
            
            # If gid is provided, replace it in the URL
            if gid:
                # Extract base URL without gid parameter
                if 'gid=' in final_url:
                    base_url = final_url.split('gid=')[0]
                    final_url = f"{base_url}gid={gid}"
                else:
                    # Add gid parameter if not present
                    final_url = f"{final_url}&gid={gid}" if '?' in final_url else f"{final_url}?gid={gid}"
            
            logger.info(f"Fetching data from: {final_url}")
            
            # Fetch the CSV data
            response = requests.get(final_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Read CSV data
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            logger.info(f"Successfully fetched {len(df)} rows from Google Sheet")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from Google Sheet: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing Google Sheet data: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test connection to Google Sheet.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(self.sheet_url, timeout=10)
            return response.status_code == 200
        except:
            return False