import pandas as pd
import re
import requests
from io import StringIO

class SimpleGoogleSheetConnector:
    def __init__(self, sheet_url):
        """
        Initialize with Google Sheet URL
        Uses public CSV export - no authentication needed!
        """
        self.sheet_url = sheet_url
        
    def extract_sheet_id(self, url):
        """Extract sheet ID from Google Sheets URL"""
        # Pattern: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'd/([a-zA-Z0-9-_]+)/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract sheet ID from URL: {url}")
    
    def get_work_reports(self, gid='0'):
        """
        Get work reports data from Google Sheet
        gid: Sheet ID within the spreadsheet (default 0 for first sheet)
        """
        try:
            # Extract sheet ID from URL
            sheet_id = self.extract_sheet_id(self.sheet_url)
            
            # Construct CSV export URL
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            
            print(f"Fetching data from: {csv_url}")
            
            # Fetch CSV data
            response = requests.get(csv_url)
            response.raise_for_status()  # Check for HTTP errors
            
            # Read CSV into DataFrame
            csv_content = response.content.decode('utf-8')
            df = pd.read_csv(StringIO(csv_content))
            
            print(f"Successfully fetched {len(df)} rows from Google Sheet")
            return df
            
        except Exception as e:
            print(f"Error fetching from Google Sheet: {str(e)}")
            # Return empty DataFrame if there's an error
            return pd.DataFrame()

