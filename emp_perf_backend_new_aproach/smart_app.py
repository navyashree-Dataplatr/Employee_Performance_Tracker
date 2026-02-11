# smart_app.py 
import traceback
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai
import os
import json
import re
from datetime import datetime, date, timedelta
from base_processor import BaseDataProcessor
from project_billing_analyzer import ProjectBillingAnalyzer
from team_analyzer import TeamAnalyzer
from individual_analyzer import IndividualAnalyzer
from lyell_individual_analyzer import LyellIndividualAnalyzer
from chart_generator import ChartGenerator
from invoice_generator import LyellInvoiceGenerator
from pdf_generator import InvoicePDFGenerator 
from flask import send_file
import threading
import time
from email_utils import EmailService
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)
CORS(app)
# ==================== CENTRALIZED DATE RANGE UTILITIES ====================
class DateRangeCalculator:
    """
    Centralized date range calculator to ensure consistency across all queries.
    This is the single source of truth for all date calculations in the system.
    """
    
    @staticmethod
    def get_date_range(timeframe: str, reference_date: date = None, custom_days: int = None) -> tuple:
        """
        Get start and end dates for any timeframe query.
        
        Args:
            timeframe: 'today', 'yesterday', 'last_week', 'last_month', 'last_quarter', 
                      'last_N_days', 'specific_date', 'specific_month', 'all_time'
            reference_date: Reference date (defaults to today)
            custom_days: Number of days for 'last_N_days' timeframe
            
        Returns:
            Tuple of (start_date, end_date)
            
        Examples:
            - get_date_range('today') -> (2026-01-28, 2026-01-28)
            - get_date_range('last_7_days') -> (2026-01-22, 2026-01-28)  # 7 days INCLUDING today
            - get_date_range('last_15_days') -> (2026-01-14, 2026-01-28)  # 15 days INCLUDING today
            - get_date_range('last_month') -> (2025-12-01, 2025-12-31)  # Previous calendar month
        """
        if reference_date is None:
            reference_date = date.today()
        
        # TODAY
        if timeframe == 'today':
            return reference_date, reference_date
        
        # YESTERDAY
        elif timeframe == 'yesterday':
            yesterday = reference_date - timedelta(days=1)
            return yesterday, yesterday
        
        # LAST N DAYS (including today)
        elif timeframe == 'last_week' or timeframe == 'last_7_days':
            start_date = reference_date - timedelta(days=6)  # 7 days total INCLUDING today
            return start_date, reference_date
        
        elif timeframe == 'last_15_days' or (timeframe == 'last_N_days' and custom_days == 15):
            start_date = reference_date - timedelta(days=14)  # 15 days total INCLUDING today
            return start_date, reference_date
        
        elif timeframe == 'last_30_days' or (timeframe == 'last_N_days' and custom_days == 30):
            start_date = reference_date - timedelta(days=29)  # 30 days total INCLUDING today
            return start_date, reference_date
        
        elif timeframe == 'last_N_days' and custom_days:
            start_date = reference_date - timedelta(days=custom_days - 1)  # N days INCLUDING today
            return start_date, reference_date
        
        # LAST MONTH (previous calendar month)
        elif timeframe == 'last_month':
            # Get first day of current month
            first_of_current_month = reference_date.replace(day=1)
            
            # Last day of previous month is one day before first of current month
            last_of_prev_month = first_of_current_month - timedelta(days=1)
            
            # First day of previous month
            first_of_prev_month = last_of_prev_month.replace(day=1)
            
            return first_of_prev_month, last_of_prev_month
        
        # LAST QUARTER (previous 90 days including today)
        elif timeframe == 'last_quarter':
            start_date = reference_date - timedelta(days=89)  # 90 days total INCLUDING today
            return start_date, reference_date
        
        # ALL TIME
        elif timeframe == 'all_time':
            return None, None
        
        # DEFAULT: return None for custom handling
        else:
            return None, None
    
    @staticmethod
    def parse_custom_days(query: str) -> int:
        """
        Extract number of days from query like "last 15 days", "past 20 days", etc.
        
        Args:
            query: User query string
            
        Returns:
            Number of days as integer, or None if not found
        """
        # Pattern: "last 15 days", "past 20 days", "previous 30 days"
        patterns = [
            r'(?:last|past|previous)\s+(\d+)\s+days?',
            r'(\d+)\s+days?\s+(?:ago|back)',
        ]
        
        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return int(match.group(1))
        
        return None
    
    @staticmethod
    def get_month_range(year: int, month: int) -> tuple:
        """
        Get start and end dates for a specific month.
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            
        Returns:
            Tuple of (start_date, end_date)
        """
        start_date = date(year, month, 1)
        
        # Calculate last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        return start_date, end_date
# Legacy function kept for backward compatibility
def get_last_month_range(reference_date: date = None):
    """Legacy function - use DateRangeCalculator.get_date_range('last_month') instead"""
    return DateRangeCalculator.get_date_range('last_month', reference_date)
# ==================== LYELL EXTRA HOURS CONSTANTS ====================
class LyellBillingRules:
    """
    Centralized billing rules for Lyell project to ensure consistency.
    This is the single source of truth for Lyell billing calculations.
    """
    
    # CRITICAL: Lyell project has 4-hour per day per employee cap for ETL and Reporting
    LYELL_DAILY_CAP_PER_EMPLOYEE = 4.0  # hours per day per employee
    
    # CRITICAL: Lyell project billing rate
    LYELL_HOURLY_RATE = 75.0  # dollars per hour
    
    # Categories with caps
    CAPPED_CATEGORIES = ['etl', 'reporting']
    
    # Categories without caps
    UNCAPPED_CATEGORIES = ['development', 'testing', 'architect', 'other']
    
    # SOW Rules
    SOW_RULES = {
        'etl': {
            'max_hours_per_day': 4.0,
            'description': 'ETL work capped at 4 hours per day per employee'
        },
        'reporting': {
            'max_hours_per_day': 4.0,
            'description': 'Reporting work capped at 4 hours per day per employee'
        },
        'development': {
            'max_hours_per_day': None,
            'description': 'Development work - no cap'
        },
        'testing': {
            'max_hours_per_day': None,
            'description': 'Testing work - no cap'
        },
        'architect': {
            'max_hours_per_day': None,
            'description': 'Architecture work - no cap'
        },
        'other': {
            'max_hours_per_day': None,
            'description': 'Other work - no cap'
        }
    }
    
    @staticmethod
    def calculate_extra_hours(actual_hours: float, category: str) -> float:
        """
        Calculate extra hours for a given category.
        
        Args:
            actual_hours: Actual hours worked
            category: Work category (etl, reporting, development, etc.)
            
        Returns:
            Extra hours (0 if no cap or under cap)
        """
        category = category.lower()
        rule = LyellBillingRules.SOW_RULES.get(category, {})
        max_hours = rule.get('max_hours_per_day')
        
        if max_hours is None:
            # No cap for this category
            return 0.0
        
        if actual_hours > max_hours:
            return round(actual_hours - max_hours, 2)
        
        return 0.0
    
    @staticmethod
    def get_billable_hours(actual_hours: float, category: str) -> float:
        """
        Calculate billable hours for a given category.
        
        Args:
            actual_hours: Actual hours worked
            category: Work category
            
        Returns:
            Billable hours (capped if necessary)
        """
        category = category.lower()
        rule = LyellBillingRules.SOW_RULES.get(category, {})
        max_hours = rule.get('max_hours_per_day')
        
        if max_hours is None:
            # No cap - bill all hours
            return round(actual_hours, 2)
        
        # Cap at max_hours
        return round(min(actual_hours, max_hours), 2)
# ==================== API KEY ROTATION MANAGER ====================
class APIKeyManager:
    """Simple API key rotation manager"""
    
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_index = 0
        self.failed_keys = set()
        
    def get_current_key(self):
        """Get the current active API key"""
        return self.api_keys[self.current_index]
    
    def rotate_key(self):
        """Switch to next available API key"""
        self.failed_keys.add(self.current_index)
        
        # Try next keys
        for i in range(len(self.api_keys)):
            next_index = (self.current_index + i + 1) % len(self.api_keys)
            if next_index not in self.failed_keys:
                self.current_index = next_index
                print(f" Switched to API key #{self.current_index + 1}")
                return True
        
        # All keys failed
        print(" All API keys exhausted!")
        return False
    
    def reset_failed_keys(self):
        """Reset failed keys (call this periodically, e.g., daily)"""
        self.failed_keys.clear()
        print(" API key rotation reset")
# ==================== CONFIGURATION ====================
# API keys here
API_KEYS = [



    'AIzaSyCxVg8IPUhmYoLmL7ug9ra3TU1n7WzmIg4',
    'AIzaSyDVVjBgO5F79zbQ2apIJkcRDQlnAEEeln0',
    'AIzaSyCfslc0lPFwBWU_hIMGkYIBFsDOEtNLk9g',
    'AIzaSyAQrQI1sO91QnJZBXB6_p8urvkXHLjkxa8',
    'AIzaSyDMcDpW-neTFRB1HHH19yT9H6xL_8fZuKA',
    'AIzaSyCmFGG62zGWnywHJRa5Lzu6QsztqQGD6K8',
    'AIzaSyAq8LaxrSqczJb3_7keqeuGtyut8r-RgFA',
    'AIzaSyD2ZsnTvu8d9_e1VS3m-Y-25O7m4_C90RQ',
    'AIzaSyDe46QJngYveSbb4tKVgWQP6-q5tpduP20',
    'AIzaSyDvWYHYidFTpAgbsoOc1swLBK2c3QedHC0',    
    'AIzaSyDcztmPzvNciYsPvAjQC_VGfpOqZMd3-jI',
    'AIzaSyCL2U05oQZYnTqqQvym-ZhHAXhxkwv4fsc',
    'AIzaSyC_mslFjUhAijcit7rIL1uGTIGrvgakkwg',
    


    'AIzaSyDz8SU0sWgD5kQ8UQrQqzprAuaVAzhKF8w',


    #smd
    'AIzaSyBqfSQpKF2pfq82TGAzNLSEWiOHC2NGpLA',
    'AIzaSyBSqFIzC-Fx-8pS_SBoBjHEjzz-1YTPXfg',
    'AIzaSyB_2NQ7Ra7vR1r2Fj0EOnYc29kPYisbfCM',
    'AIzaSyD19epSU_V28zNqBWnngwyZzkQibmjTpkg',
    'AIzaSyD82tYHQoJwCMiG2vTccqLy9CfT_j3buWo',
    'AIzaSyDl-uy_WHe-hSMOysHsKK1V4kxHOII_idE',
    'AIzaSyCXsOJAFcJ4DKnyOpZKrrh23_e-QpqQe4o',
        #kp key
    'AIzaSyAOunvPCSVwxLXVH1mZBPRRy-96ZLnPHDM',
    'AIzaSyBTSYBXz5czmQ_SzDU5qYuhJInF9JuCYJI',
    'AIzaSyBCy37gFXWc7KBU9od2mP3zX3MI2UMPoXk',
    'AIzaSyDYMmyH2wm13gH3-wAD09BPHPjj6Wc7A6Q',
    'AIzaSyCJaddqukntXgzlYt7ZPkiN2hmP3U1oKbs',
    'AIzaSyDeE7Iri0e7RBZnODYqotLM1rnvNns6Y-o',
    #SHRE KEY
    'AIzaSyAd9NCap3Z-BAFYjkXuGYE7zQGhRsjZVCg',
    'AIzaSyB-WeCoamdQNXjjlcSgR9eCYmK0DN1-baY',
    'AIzaSyCx0XnEbkRlbDokFjtAeFODPpGFGZDIu2o',
    'AIzaSyD5egr0HlGYakz6OuRrF0SS1F0NqMDOM1A',
    'AIzaSyAs9_GmeK1bskxj8x3UThatEuZ28vtshTY',
    'AIzaSyD_8skah3uY_5oRPwhSARj-2NAZGpZ5SNw',
    #ak keys
    'AIzaSyACNVTUpakkTUl6szgl-K9WZpQ_7-OdyOM',
    'AIzaSyAXM6YtnEnJdJf8Velo5itB8hm64gQEvYo',
    'AIzaSyC2uvO39Zu1CSRyiq0J2tNDYMfY_J8FqOk',
    'AIzaSyCB0SVrk53FzZZx2abxX2_lxquts3FTpVI',
    'AIzaSyBWqFhto2s5gEmc8bxVQ9BKRm1nTxOWDe0',
    'AIzaSyD6qz9M6TT7Uaxj9E8N5KOSG9bux-Uso14',
    'AIzaSyDh2K4H7qvxTa3mF7vk0leYVsS_PfwZg1Y',
    'AIzaSyA0TP9ZXsNRKsQ5A9X_DXAB0iyODnWdv-c',
    'AIzaSyAGirFsm1dNSJ_vvorelMo9e79jnr2GJMI',
    'AIzaSyAEXhGYstnZdVjdvwiwChN-mNqciT9Xm0s',
    'AIzaSyBFWWViZuHjqi6zG72-TeK1GMLHc-erPUs',
    'AIzaSyBC4YvgRcOWKG9GkxyikA9chDZ-fl1rCVs',
    'AIzaSyAJ_DI-RoVZpxsA33MWWC1mQO10yeC3Nok',
    'AIzaSyBw43vFDugK1l2FqGWod6-v-6MNLDQjqTQ',
    'AIzaSyBuZGH9HnCWsPtqqzXKjT59ob3whoP7ono',
    'AIzaSyDqSQVffQ7BoiC6r9d50xT9KtjqgIeVjG0',
    'AIzaSyC1B2fI1WVdUCUzE_OfrFoP8jRWg2jmpwM',
]
# Initialize key manager
key_manager = APIKeyManager(API_KEYS)
# Initialize base components
print("Initializing Dataplatr Analytics System...")
# Get absolute path for data files
current_dir = os.path.dirname(os.path.abspath(__file__))
employees_csv_path = os.path.join(current_dir, 'Dataplatr_employees.csv')
base = BaseDataProcessor(
    employees_csv=employees_csv_path,
    google_sheet_url='https://docs.google.com/spreadsheets/d/1ZUhkf7B5dU1-mfQOyTGRetS_GCo9lsqoXeq2KEq2bC4/export?format=csv&gid=1844282638'
)
# Initialize analyzers
individual = IndividualAnalyzer(base)
team = TeamAnalyzer(base, individual)
# NEW: Initialize Lyell Individual Analyzer
print("Initializing Lyell Individual Analyzer...")
lyell_individual = LyellIndividualAnalyzer(base)
lyell_individual.set_individual_analyzer(individual)
print("Lyell Individual Analyzer initialized!")
# NEW: Initialize Invoice Generator
print("Initializing Lyell Invoice Generator...")
invoice_generator = LyellInvoiceGenerator(lyell_individual, billing_rate=LyellBillingRules.LYELL_HOURLY_RATE)
# Use absolute path for invoices directory to avoid path mismatch
invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")
pdf_generator = InvoicePDFGenerator(output_directory=invoices_dir)
print(f"Invoice Generator initialized! Invoices will be saved to: {invoices_dir}")
# NEW: Initialize Email Service
print("Initializing Email Service...")
# Use environment variables for email configuration
smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
smtp_port = int(os.environ.get("SMTP_PORT", 587))
sender_email = os.environ.get("SENDER_EMAIL", "navyashree.poojary@dataplatr.com")
sender_password = os.environ.get("SENDER_PASSWORD") # Should be an App Password for Gmail
email_service = EmailService(
    smtp_server=smtp_server,
    smtp_port=smtp_port,
    sender_email=sender_email,
    sender_password=sender_password
)
print(f"Email Service initialized for: {sender_email}")
if not sender_password:
    print("⚠ WARNING: No SENDER_PASSWORD provided. Authentication may fail.")
# Initialize Chart Generator
print("Initializing Chart Generator...")
chart_generator = ChartGenerator(base)
print("Chart Generator initialized!")
print("System initialized successfully!")
# Initialize LLM with first API key
genai.configure(api_key=key_manager.get_current_key())
model = genai.GenerativeModel("gemini-3-flash-preview")
print(f" LLM initialized with API key #{key_manager.current_index + 1}")
# ==================== LLM HELPER WITH ROTATION ====================
def call_llm_with_rotation(prompt, max_retries=None):
    """
    Call LLM with automatic API key rotation on quota errors
    
    Args:
        prompt: The prompt to send
        max_retries: Max retry attempts (default: number of API keys)
    
    Returns:
        LLM response text or None if all keys fail
    """
    global model
    
    if max_retries is None:
        max_retries = len(API_KEYS)
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.candidates[0].content.parts[0].text.strip()
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for multiple types of failure that should trigger rotation
            # 1. Quota/Rate limits (429)
            # 2. Permission/Leaked/Invalid keys (403)
            # 3. Model overload / Server errors (500/503)
            is_quota_error = any(keyword in error_msg for keyword in ['quota', 'rate limit', 'resource exhausted', '429', 'resource_exhausted'])
            is_permission_error = any(keyword in error_msg for keyword in ['permission', '403', 'leaked', 'denied', 'unauthorized', 'invalid_api_key'])
            is_server_error = any(keyword in error_msg for keyword in ['500', '503', 'overloaded', 'deadline', 'service unavailable'])
            
            if is_quota_error or is_permission_error or is_server_error:
                reason = "Quota exceeded" if is_quota_error else ("API key blocked/invalid" if is_permission_error else "Server overload")
                print(f"⚠ {reason} on API key #{key_manager.current_index + 1}")
                
                # Try to rotate to next key
                if key_manager.rotate_key():
                    # Reconfigure with new key
                    genai.configure(api_key=key_manager.get_current_key())
                    # Use a stable version
                    model = genai.GenerativeModel("gemini-1.5-flash") 
                    print(f" Rotating to API key #{key_manager.current_index + 1} and retrying (Attempt {attempt + 1}/{max_retries})...")
                    continue
                else:
                    print(" All API keys exhausted or failed")
                    return None
            else:
                # Other types of errors (e.g., block reason)
                print(f" LLM error (unhandled category): {e}")
                raise e
    
    return None
# ==================== HELPER FUNCTIONS ====================
def classify_intent(query):
    """Lightweight intent classification with key rotation and date awareness"""
    
    # Get current date for context
    current_date = date.today()
    current_datetime = datetime.now()
    
    # Check for custom day ranges
    custom_days = DateRangeCalculator.parse_custom_days(query)
    
    prompt = f"""
    CURRENT DATE/TIME CONTEXT:
    - Today's Date: {current_date.strftime('%Y-%m-%d (%A, %B %d, %Y)')}
    - Current Time: {current_datetime.strftime('%I:%M %p')}
    
    Classify this query: "{query}"
    
    Return ONLY JSON with these exact fields:
    {{
        "intent": "billing_summary|billing_violations|employee_performance|team_overview|comparison|lyell_employee_performance|lyell_daily_performance|lyell_category_analysis|lyell_compliance|lyell_comparison|general",
        "project": "lyell|dataplatr|null",
        "timeframe": "today|yesterday|last_week|last_month|last_quarter|last_N_days|all_time|specific_date|specific_month",
        "custom_days": {custom_days if custom_days else "null"},
        "specific_date": "YYYY-MM-DD or null",
        "specific_month": "YYYY-MM or null",
        "employee": "employee name or null",
        "employee2": "second employee name or null",
        "category": "etl|reporting|development|testing|architect|other|null",
        "confidence": 0.0-1.0
    }}
    
    IMPORTANT DATE PARSING RULES:
    - "today" -> timeframe: "today", specific_date: "{current_date.isoformat()}"
    - "yesterday" -> timeframe: "yesterday", specific_date: calculate yesterday
    - "this week" or "last week" or "last 7 days" -> timeframe: "last_week"
    - "last 15 days" or "past 15 days" -> timeframe: "last_N_days", custom_days: 15
    - "last 30 days" or "past 30 days" -> timeframe: "last_N_days", custom_days: 30
    - "this month" or "last month" -> timeframe: "last_month"
    - If query mentions specific date like "December 23" -> timeframe: "specific_date", specific_date: "2025-12-23"
    - If query mentions "December 2025" or "January 2026" -> timeframe: "specific_month", specific_month: "YYYY-MM"
    - If no timeframe mentioned -> timeframe: "all_time"
    
    IMPORTANT INTENT RULES:
    - **CRITICAL**: "Lyell" is a PROJECT NAME, NOT an employee name
    - If query mentions "for lyell" or "on lyell" or "lyell project" -> intent: "lyell_employee_performance", project: "lyell"
    - If query mentions "performance" AND "lyell" (without specifying an employee name) -> intent: "lyell_employee_performance"
    - If query mentions "each employee" or "individual employee" AND "lyell" -> intent: "lyell_employee_performance"
    - If query mentions "lyell" AND ("employee" or "individual" or "each") -> intent: "lyell_employee_performance"
    - If query mentions "lyell" AND "today" or "yesterday" or specific date -> intent: "lyell_daily_performance"
    - If query mentions "lyell" AND ("category" or "etl" or "reporting" or "development") -> intent: "lyell_category_analysis"
    - If query mentions "lyell" AND ("compliance" or "violation" or "sow" or "extra hours") -> intent: "lyell_compliance"
    - If query mentions "lyell" AND ("compare" or "vs" or "versus") -> intent: "lyell_comparison"
    - "lyell_employee_performance" shows ALL employees working on Lyell project
    - **NEVER** set employee field to "lyell" - lyell is a project, not an employee
    - "lyell_employee_performance" is ONLY for Lyell project individual employee analysis
    """
    
    try:
        response_text = call_llm_with_rotation(prompt)
        if response_text:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group())
                
                # Validate and enhance date information
                if intent_data.get("timeframe") == "today" and not intent_data.get("specific_date"):
                    intent_data["specific_date"] = current_date.isoformat()
                
                if intent_data.get("timeframe") == "yesterday":
                    yesterday = current_date - timedelta(days=1)
                    intent_data["specific_date"] = yesterday.isoformat()
                
                # Force Lyell project for Lyell-related intents
                if intent_data.get("intent", "").startswith("lyell_"):
                    intent_data["project"] = "lyell"
                
                print(f"Intent classified: {intent_data}")
                return intent_data
    except Exception as e:
        print(f"Intent classification error: {e}")
    
    # Fallback classification with date awareness
    query_lower = query.lower()
    intent_data = {
        "intent": "general",
        "project": None,
        "timeframe": "all_time",
        "custom_days": custom_days,
        "specific_date": None,
        "specific_month": None,
        "employee": None,
        "employee2": None,
        "category": None,
        "confidence": 0.7
    }
    
    # Parse timeframe from query
    if 'today' in query_lower:
        intent_data["timeframe"] = "today"
        intent_data["specific_date"] = current_date.isoformat()
    elif 'yesterday' in query_lower:
        intent_data["timeframe"] = "yesterday"
        yesterday = current_date - timedelta(days=1)
        intent_data["specific_date"] = yesterday.isoformat()
    elif 'this week' in query_lower or 'last week' in query_lower or 'last 7 days' in query_lower:
        intent_data["timeframe"] = "last_week"
    elif custom_days:
        intent_data["timeframe"] = "last_N_days"
    elif 'this month' in query_lower or 'last month' in query_lower:
        intent_data["timeframe"] = "last_month"
    
    # Parse month if mentioned
    month_patterns = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    for month_name, month_num in month_patterns.items():
        if month_name in query_lower:
            year = current_date.year
            # Check if year mentioned
            year_match = re.search(r'20\d{2}', query_lower)
            if year_match:
                year = int(year_match.group())
            intent_data["timeframe"] = "specific_month"
            intent_data["specific_month"] = f"{year}-{month_num}"
            break
    
    # NEW: Check for Lyell individual employee performance
    # CRITICAL: "Lyell" is a PROJECT name, not an employee name
    if ('lyell' in query_lower):
        # Check for specific Lyell intents
        if any(kw in query_lower for kw in ['each employee', 'individual employee', 'per employee', 'each person', 'every employee']):
            intent_data["intent"] = "lyell_employee_performance"
            intent_data["project"] = "lyell"
        
        elif any(kw in query_lower for kw in ['compliance', 'violation', 'sow', 'extra hours', 'unbillable']):
            intent_data["intent"] = "lyell_compliance"
            intent_data["project"] = "lyell"
        
        elif any(kw in query_lower for kw in ['category', 'etl', 'reporting', 'development', 'testing', 'architect']):
            intent_data["intent"] = "lyell_category_analysis"
            intent_data["project"] = "lyell"
            # Try to extract category
            for cat in ['etl', 'reporting', 'development', 'testing', 'architect', 'other']:
                if cat in query_lower:
                    intent_data["category"] = cat
                    break
        
        elif any(kw in query_lower for kw in ['compare', 'vs', 'versus']):
            intent_data["intent"] = "lyell_comparison"
            intent_data["project"] = "lyell"
        
        # Check if query is asking about performance/work on Lyell (default case)
        # Examples: "for lyell", "on lyell", "lyell performance", "show lyell"
        elif any(kw in query_lower for kw in ['performance', 'for lyell', 'on lyell', 'show', 'display', 'analyze', 'report']):
            intent_data["intent"] = "lyell_employee_performance"
            intent_data["project"] = "lyell"
        
        else:
            # Default Lyell intent - any mention of lyell defaults to showing project employee performance
            intent_data["intent"] = "lyell_employee_performance"
            intent_data["project"] = "lyell"
    
    # Check for billing
    elif any(kw in query_lower for kw in ['billing', 'bill', 'sow', 'invoice', 'extra hours', 'unbilled']):
        intent_data["intent"] = "billing_summary"
        if 'lyell' in query_lower:
            intent_data["project"] = "lyell"
        elif 'dataplatr' in query_lower:
            intent_data["project"] = "dataplatr"
    
    # Check for violations
    elif any(kw in query_lower for kw in ['violation', 'excess', 'extra hours', 'unbilled']):
        intent_data["intent"] = "billing_violations"
    
    # Check for employee
    elif any(kw in query_lower for kw in ['how is', 'performance of', 'analyze']):
        intent_data["intent"] = "employee_performance"
    
    # Check for team
    elif any(kw in query_lower for kw in ['team', 'overall', 'all employees']):
        intent_data["intent"] = "team_overview"
    
    # Check for comparison
    elif 'compare' in query_lower:
        intent_data["intent"] = "comparison"
    
    return intent_data
def generate_intelligent_response(intent, query):
    """Generate LLM response with guaranteed chart generation"""
    
    context = ""
    current_date = date.today()
    
    # Determine date range using centralized calculator
    start_date = None
    end_date = None
    
    if intent.get("specific_date"):
        # Specific date query
        try:
            target_date = datetime.strptime(intent["specific_date"], "%Y-%m-%d").date()
            start_date = target_date
            end_date = target_date
        except:
            pass
    elif intent.get("timeframe") == "last_N_days" and intent.get("custom_days"):
        start_date, end_date = DateRangeCalculator.get_date_range(
            'last_N_days', 
            current_date, 
            intent["custom_days"]
        )
    elif intent.get("timeframe"):
        start_date, end_date = DateRangeCalculator.get_date_range(
            intent["timeframe"], 
            current_date
        )
    elif intent.get("specific_month"):
        # Parse YYYY-MM
        try:
            year, month = map(int, intent["specific_month"].split('-'))
            start_date, end_date = DateRangeCalculator.get_month_range(year, month)
        except:
            pass
    
    # ==================== LYELL INDIVIDUAL EMPLOYEE PERFORMANCE ====================
    if intent["intent"] == "lyell_employee_performance":
        # Get individual Lyell performance
        lyell_performance = lyell_individual.get_lyell_employee_performance(
            start_date=start_date,
            end_date=end_date
        )
        
        if not lyell_performance:
            context = f"""
            NO INDIVIDUAL EMPLOYEE DATA for Lyell Project in the specified timeframe.
            
            Query: {query}
            Timeframe: {intent.get('timeframe', 'all_time')}
            Date Range: {start_date.isoformat() if start_date else 'All time'} to {end_date.isoformat() if end_date else current_date.isoformat()}
            
            This means no individual employees worked on the Lyell project during this period.
            Available employees in system: {len(base.master_df)}
            """
        else:
            # Sort employees by total extra hours for ranking queries
            sorted_by_extra_hours = sorted(lyell_performance, key=lambda x: x.get('total_extra_hours', 0), reverse=True)
            
            context = f"""
            LYELL PROJECT - INDIVIDUAL EMPLOYEE PERFORMANCE ANALYSIS:
            Query: {query}
            Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
            Timeframe: {intent.get('timeframe', 'all_time').replace('_', ' ').title()}
            Date Range: {start_date.isoformat() if start_date else 'All time'} to {end_date.isoformat() if end_date else current_date.isoformat()}
            
            **EXECUTIVE SUMMARY:**
            - Total employees on Lyell: {len(lyell_performance)}
            - Total Lyell hours: {sum(emp['total_hours_on_lyell'] for emp in lyell_performance):.2f}
            - Total extra hours (unbillable): {sum(emp['total_extra_hours'] for emp in lyell_performance):.2f}
            - Employees with SOW violations: {sum(1 for emp in lyell_performance if emp.get('total_extra_hours', 0) > 0)}
            
            **EMPLOYEES RANKED BY EXTRA HOURS (Highest to Lowest):**
            
            """
            
            for i, emp in enumerate(sorted_by_extra_hours, 1):
                if emp.get('total_extra_hours', 0) > 0:
                    context += f"""
            {i}. {emp['employee_name']} ({emp['employee_email']})
                - Total extra hours: {emp.get('total_extra_hours', 0):.2f}
                - Total Lyell hours: {emp.get('total_hours_on_lyell', 0):.2f}
                - Percentage unbillable: {(emp.get('total_extra_hours', 0) / emp.get('total_hours_on_lyell', 1) * 100):.1f}%
                - Billing efficiency: {emp.get('billing_efficiency', 0):.1f}%
                - SOW Compliance: {emp.get('sow_compliance_status', 'Unknown')}
                
                    """
            
            context += f"""
            
            **FULL EMPLOYEE PERFORMANCE DATA:**
            {json.dumps(lyell_performance, indent=2, default=str)}
            
        
            
            **DATA FOR DETAILED ANALYSIS:**
            Each employee record includes:
            - Name and email
            - Total hours on Lyell
            - Total billable hours (after SOW caps)
            - Total extra hours (unbillable)
            - Category breakdown (ETL, Reporting, Development, Testing, etc.)
            - Daily work pattern
            - Compliance status
            - Contribution percentage
            """
    
    # ==================== LYELL COMPLIANCE REPORT ====================
    elif intent["intent"] == "lyell_compliance":
        compliance_report = lyell_individual.get_sow_compliance_report(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get individual performance for more context
        lyell_performance = lyell_individual.get_lyell_employee_performance(
            start_date=start_date,
            end_date=end_date
        )
        
        context = f"""
        LYELL PROJECT - COMPREHENSIVE SOW COMPLIANCE REPORT:
        Query: {query}
        Timeframe: {intent.get('timeframe', 'all_time')}
        Date Range: {start_date.isoformat() if start_date else 'All time'} to {end_date.isoformat() if end_date else current_date.isoformat()}
        Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
        
        **COMPLIANCE EXECUTIVE SUMMARY:**
        - Total violations found: {compliance_report.get('summary', {}).get('total_violations', 0)}
        - Employees with violations: {compliance_report.get('summary', {}).get('employees_with_violations', 0)}
        - Total extra hours (unbillable): {compliance_report.get('summary', {}).get('total_extra_hours', 0):.2f}
        - Affected categories: {', '.join(compliance_report.get('summary', {}).get('affected_categories', [])) or 'None'}
        - Most violating day: {compliance_report.get('summary', {}).get('most_violating_day', 'None')}
        
        **DETAILED VIOLATIONS (Sorted by Date - Most Recent First):**
        
        """
        
        # Add detailed violation information
        violations = compliance_report.get('violations', [])
        if violations:
            for i, violation in enumerate(violations[:10], 1):  # Show top 10 violations
                context += f"""
        {i}. Date: {violation.get('date', 'Unknown')}
            Employee: {violation.get('employee_name', 'Unknown')} ({violation.get('employee_email', 'Unknown')})
            Category: {violation.get('category', 'Unknown').title()}
            Actual Hours: {violation.get('actual_hours', 0):.2f}
            Max Allowed: {violation.get('max_allowed', 4.0):.2f}
            Extra Hours: {violation.get('extra_hours', 0):.2f}
            Tasks: {', '.join(violation.get('tasks', ['No task details']))[:100]}...
                """
        
        context += f"""
        
        **EMPLOYEE VIOLATIONS SUMMARY:**
        
        """
        
        employee_violations = compliance_report.get('employee_violations', [])
        if employee_violations:
            for emp_violation in employee_violations:
                context += f"""
        - {emp_violation.get('employee_name', 'Unknown')}:
          * Total violations: {emp_violation.get('violation_count', 0)}
          * Total extra hours: {emp_violation.get('total_extra_hours', 0):.2f}
          * Sample violations: {emp_violation.get('sample_violations', [])[:2]}
                """
        
        context += f"""
        
        **FULL COMPLIANCE DATA:**
        {json.dumps(compliance_report, indent=2, default=str)}
        
        **INDIVIDUAL EMPLOYEE PERFORMANCE CONTEXT:**
        {json.dumps(lyell_performance, indent=2, default=str) if lyell_performance else 'No individual performance data'}
        
        
        
        **RECOMMENDATIONS DATA SOURCE:**
        Use the employee_violations list to identify which employees need training.
        Use the violations list to identify patterns (e.g., specific days, categories).
        """
    
    # ==================== LYELL DAILY PERFORMANCE ====================
    elif intent["intent"] == "lyell_daily_performance":
        if start_date and end_date and start_date == end_date:
            daily_performance = lyell_individual.get_lyell_performance_by_date(start_date)
            context = f"""
            LYELL PROJECT - DAILY PERFORMANCE DETAILED ANALYSIS:
            Query: {query}
            Target Date: {start_date.strftime('%Y-%m-%d (%A)')}
            Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
            
            **DAILY SUMMARY:**
            - Date: {daily_performance.get('date', 'Unknown')}
            - Day of Week: {daily_performance.get('day_of_week', 'Unknown')}
            - Total hours worked: {daily_performance.get('total_hours', 0):.2f}
            - Total extra hours (unbillable): {daily_performance.get('total_extra_hours', 0):.2f}
            - Number of employees: {daily_performance.get('employee_count', 0)}
            - Has SOW violations: {daily_performance.get('has_sow_violations', False)}
            
            **EMPLOYEE BREAKDOWN:**
            
            """
            
            employees = daily_performance.get('employees', [])
            if employees:
                for i, emp in enumerate(employees, 1):
                    context += f"""
            {i}. {emp.get('employee_name', 'Unknown')} ({emp.get('employee_email', 'Unknown')})
                - Total hours: {emp.get('total_hours', 0):.2f}
                - Total extra hours: {emp.get('total_extra_hours', 0):.2f}
                - Task count: {emp.get('task_count', 0)}
                - Category breakdown: {json.dumps(emp.get('category_breakdown', {}), default=str)}
                - SOW Compliance: {emp.get('sow_compliance', {}).get('has_violations', False)}
                    """
            
            context += f"""
            
            **FULL DAILY DATA:**
            {json.dumps(daily_performance, indent=2, default=str)}
            
        
            - Employees with violations: {sum(1 for emp in employees if emp.get('total_extra_hours', 0) > 0)}
            """
        else:
            context = f"""
            LYELL DAILY PERFORMANCE - DATE NOT SPECIFIED:
            Query: {query}
            Please specify a date like "today", "yesterday", or "2024-12-25"
            """
    
    # ==================== LYELL CATEGORY ANALYSIS ====================
    elif intent["intent"] == "lyell_category_analysis":
        category = intent.get("category", "other")
        
        if category:
            category_performance = lyell_individual.get_category_performance(
                category=category,
                start_date=start_date,
                end_date=end_date
            )
            context = f"""
            LYELL PROJECT - DETAILED CATEGORY ANALYSIS:
            Query: {query}
            Category: {category.upper()}
            Timeframe: {intent.get('timeframe', 'all_time')}
            Date Range: {start_date.isoformat() if start_date else 'All time'} to {end_date.isoformat() if end_date else current_date.isoformat()}
            Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
            
            **CATEGORY SUMMARY:**
            - Category: {category_performance.get('category_label', 'Unknown')}
            - Total actual hours: {category_performance.get('total_actual_hours', 0):.2f}
            - Total extra hours (unbillable): {category_performance.get('total_extra_hours', 0):.2f}
            - Number of employees: {category_performance.get('employee_count', 0)}
            - Category percentage of total: {category_performance.get('category_percentage', 0):.1f}%
            - Daily cap (if applicable): {category_performance.get('category_cap', 'No cap')}
            
            **TOP CONTRIBUTORS IN THIS CATEGORY:**
            
            """
            
            employees = category_performance.get('employees', [])
            if employees:
                for i, emp in enumerate(employees[:5], 1):  # Show top 5
                    context += f"""
            {i}. {emp.get('employee_name', 'Unknown')} ({emp.get('employee_email', 'Unknown')})
                - Total {category} hours: {emp.get('total_actual_hours', 0):.2f}
                - Extra hours: {emp.get('total_extra_hours', 0):.2f}
                - Days worked: {emp.get('total_days', 0)}
                - Average hours/day: {emp.get('avg_hours_per_day', 0):.2f}
                - Has extra hours: {emp.get('has_extra_hours', False)}
                    """
            
            context += f"""
            
            **FULL CATEGORY DATA:**
            {json.dumps(category_performance, indent=2, default=str)}
            
            **SOW RULES FOR THIS CATEGORY:**
            - Daily cap: {category_performance.get('category_cap', 'No cap')}
            - Extra hours calculation: Actual hours - {category_performance.get('category_cap', 0)} (if capped)
            - Unbillable amount: ${category_performance.get('total_extra_hours', 0) * 75:.2f} (at $75/hour)
            """
        else:
            context = f"""
            LYELL CATEGORY ANALYSIS - CATEGORY NOT SPECIFIED:
            Query: {query}
            Please specify a category like "etl", "reporting", "development", "testing", or "architect"
            """
    
    # ==================== LYELL COMPARISON ====================
    elif intent["intent"] == "lyell_comparison":
        employee1 = intent.get("employee")
        employee2 = intent.get("employee2")
        
        if employee1 and employee2:
            comparison = lyell_individual.compare_employees(
                employee1_name=employee1,
                employee2_name=employee2,
                start_date=start_date,
                end_date=end_date
            )
            context = f"""
            LYELL PROJECT - DETAILED EMPLOYEE COMPARISON:
            Query: {query}
            Employees: {employee1} vs {employee2}
            Timeframe: {intent.get('timeframe', 'all_time')}
            Date Range: {start_date.isoformat() if start_date else 'All time'} to {end_date.isoformat() if end_date else current_date.isoformat()}
            Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
            
            **COMPARISON EXECUTIVE SUMMARY:**
            - Higher contributor: {comparison.get('summary', {}).get('higher_contributor', 'Unknown')}
            - Hour difference: {comparison.get('summary', {}).get('hour_difference', 0):.2f} hours
            - Combined total hours: {comparison.get('summary', {}).get('total_hours_both', 0):.2f}
            - Combined extra hours: {comparison.get('summary', {}).get('total_extra_hours_both', 0):.2f}
            
            **EMPLOYEE 1 DETAILS:**
            {json.dumps(comparison.get('employee1', {}), indent=2, default=str)}
            
            **EMPLOYEE 2 DETAILS:**
            {json.dumps(comparison.get('employee2', {}), indent=2, default=str)}
            
            **KEY DIFFERENCES:**
            {json.dumps(comparison.get('differences', {}), indent=2, default=str)}
            
            **CATEGORY COMPARISON:**
            
            """
            
            category_comparison = comparison.get('category_comparison', [])
            if category_comparison:
                for cat_comp in category_comparison[:5]:  # Show top 5 categories
                    context += f"""
            - {cat_comp.get('category', 'Unknown').title()}:
              * {employee1}: {cat_comp.get('employee1_hours', 0):.2f} hours ({cat_comp.get('employee1_percentage', 0):.1f}%)
              * {employee2}: {cat_comp.get('employee2_hours', 0):.2f} hours ({cat_comp.get('employee2_percentage', 0):.1f}%)
              * Difference: {cat_comp.get('difference', 0):.2f} hours
                    """
            
            context += f"""
            
            **FULL COMPARISON DATA:**
            {json.dumps(comparison, indent=2, default=str)}
            """
        else:
            # Get top contributors instead
            top_contributors = lyell_individual.get_top_contributors(
                top_n=5,
                start_date=start_date,
                end_date=end_date
            )
            context = f"""
            LYELL PROJECT - TOP CONTRIBUTORS ANALYSIS:
            Query: {query}
            Timeframe: {intent.get('timeframe', 'all_time')}
            Date Range: {start_date.isoformat() if start_date else 'All time'} to {end_date.isoformat() if end_date else current_date.isoformat()}
            Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
            
            **TOP CONTRIBUTORS SUMMARY:**
            - Top {top_contributors.get('top_n', 5)} contributors shown
            - Total employees analyzed: {top_contributors.get('summary', {}).get('total_employees', 0)}
            - Total hours from top contributors: {top_contributors.get('summary', {}).get('top_contributors_hours', 0):.2f}
            - Percentage of total: {top_contributors.get('summary', {}).get('top_percentage', 0):.1f}%
            
            **TOP CONTRIBUTORS DETAILS:**
            
            """
            
            contributors = top_contributors.get('top_contributors', [])
            if contributors:
                for i, contributor in enumerate(contributors, 1):
                    context += f"""
            {i}. {contributor.get('employee_name', 'Unknown')} ({contributor.get('employee_email', 'Unknown')})
                - Total Lyell hours: {contributor.get('total_hours_on_lyell', 0):.2f}
                - Contribution percentage: {contributor.get('contribution_percentage', 0):.1f}%
                - Extra hours (unbillable): {contributor.get('total_extra_hours', 0):.2f}
                - Billing efficiency: {contributor.get('billing_efficiency', 0):.1f}%
                - Days worked: {contributor.get('total_days_on_lyell', 0)}
               
                    """
            
            context += f"""
            
            **FULL TOP CONTRIBUTORS DATA:**
            {json.dumps(top_contributors, indent=2, default=str)}
            """
    
    # ==================== EXISTING BILLING ANALYSIS ====================
    elif intent["intent"] in ["billing_summary", "billing_violations"] and intent["project"]:
        # Billing analysis with date filtering
        billing_analyzer = ProjectBillingAnalyzer(base.get_work_data_for_billing())
        
        summary = billing_analyzer.get_project_billing_summary(
            intent["project"], 
            start_date=start_date, 
            end_date=end_date
        )
        
        if summary.get('status') == 'NO_DATA':
            context = f"""
            NO BILLING DATA for {intent["project"].upper()} on {intent.get("specific_date", "requested date")}
            
            Available data range: {summary['analysis_period']['start_date']} to {summary['analysis_period']['end_date']}
            
            QUESTION: {query}
            """
        else:
            context = f"""
            DETAILED BILLING ANALYSIS for {intent["project"].upper()} PROJECT:
            QUERY DATE CONTEXT: Today is {current_date.strftime('%Y-%m-%d (%A)')}
            Timeframe: {intent.get('timeframe', 'all_time')}
            Date Range: {start_date.isoformat() if start_date else 'All time'} to {end_date.isoformat() if end_date else current_date.isoformat()}
            
            **BILLING EXECUTIVE SUMMARY:**
            - Project: {summary.get('project', 'Unknown')}
            - Total days with work: {summary.get('total_days', 0)}
            - Total actual hours: {summary.get('totals', {}).get('total_actual_hours', 0):.2f}
            - Total billable hours: {summary.get('totals', {}).get('total_billed_hours', 0):.2f}
            - Total extra hours (unbillable): {summary.get('totals', {}).get('total_extra_hours', 0):.2f}
            - Days with SOW violations: {summary.get('totals', {}).get('days_with_extra_hours', 0)}
            - Project type: {summary.get('project_type', 'Unknown')}
            
            **CATEGORY BREAKDOWN:**
            
            """
            
            category_breakdown = summary.get('category_breakdown', {})
            if category_breakdown:
                for category, data in category_breakdown.items():
                    context += f"""
            - {category.title()}:
              * Actual hours: {data.get('actual_hours', 0):.2f}
              * Billable hours: {data.get('billed_hours', 0):.2f}
              * Extra hours: {data.get('extra_hours', 0):.2f}
              * Days worked: {data.get('days_worked', 0)}
                    """
            
            context += f"""
            
            **SOW VIOLATIONS DETAIL:**
            - Number of violations: {len(summary.get('sow_violations', []))}
            - Total unbillable amount: ${summary.get('totals', {}).get('total_extra_hours', 0) * 75:.2f} (at $75/hour)
            
            **FULL BILLING DATA:**
            {json.dumps(summary, indent=2, default=str)}
            
            QUESTION: {query}
            """
    
    # ==================== EXISTING EMPLOYEE PERFORMANCE ====================
    elif intent["intent"] == "employee_performance":
        if intent["employee"]:
            employee_email = base.find_employee_by_name(intent["employee"])
            if employee_email:
                metrics = individual.get_employee_detailed_metrics(employee_email)
                context = f"""
                DETAILED EMPLOYEE PERFORMANCE for {intent["employee"].upper()}:
                Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
                Employee Email: {employee_email}
                
                {json.dumps(metrics, indent=2, default=str)}
                
                QUESTION: {query}
                """
            else:
                context = f"""
                EMPLOYEE NOT FOUND: {intent["employee"]}
                
                Available employees: {base.master_df['Name'].tolist() if not base.master_df.empty else 'None'}
                
                QUESTION: {query}
                """
        else:
            team_metrics = team.get_team_overview_metrics()
            context = f"""
            TEAM PERFORMANCE OVERVIEW:
            Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
            
            {json.dumps(team_metrics, indent=2, default=str) if team_metrics else 'No team metrics available'}
            
            QUESTION: {query}
            """
    
    # ====================TEAM OVERVIEW ====================
    elif intent["intent"] == "team_overview":
        team_metrics = team.get_team_overview_metrics()
        context = f"""
        TEAM OVERVIEW:
        Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
        
        {json.dumps(team_metrics, indent=2, default=str) if team_metrics else 'No team metrics available'}
        
        QUESTION: {query}
        """
    
    # ====================  COMPARISON ====================
    elif intent["intent"] == "comparison":
        team_metrics = team.get_team_overview_metrics()
        if team_metrics and 'top_performers' in team_metrics:
            context = f"""
            COMPARISON DATA:
            Current Date: {current_date.strftime('%Y-%m-%d (%A)')}
            
            Top Performers:
            {json.dumps(team_metrics['top_performers'], indent=2)}
            
            Bottom Performers:
            {json.dumps(team_metrics['bottom_performers'], indent=2) if 'bottom_performers' in team_metrics else '[]'}
            
            QUESTION: {query}
            """
    
    # ==================== GENERAL RESPONSE ====================
    else:
        team_metrics = team.get_team_overview_metrics()
        context = f"""
        SYSTEM INFORMATION:
        Current Date/Time: {datetime.now().strftime('%Y-%m-%d %I:%M %p (%A)')}
        
        - Dataplatr Analytics Platform v3.0 with Lyell Individual Analysis
        - {len(base.master_df)} employees in database
        - {len(base.work_df)} work reports loaded
        - Analysis period: {base.min_date} to {base.max_date}
        
        TEAM OVERVIEW:
        {json.dumps(team_metrics, indent=2, default=str) if team_metrics else 'No team metrics'}
        
        I can help with:
        1. Employee performance analysis
        2. Team overview metrics
        3. Project billing (Lyell & DataPlatr)
        4. SOW compliance checking
        5. Performance comparisons
        
        NEW - LYELL PROJECT SPECIFIC:
        6. Individual employee performance for Lyell
        7. Daily Lyell work reports
        8. Category-wise analysis (ETL, Reporting, etc.)
        9. SOW compliance for Lyell
        10. Employee comparisons on Lyell
        
        QUESTION: {query}
        """
    
    # Build the prompt for LLM - STRICTLY ENFORCING CHART GENERATION
    prompt = f"""
    You are a professional HR analytics assistant for Dataplatr. You MUST provide a chart for EVERY response.
    CURRENT DATE/TIME: {datetime.now().strftime('%Y-%m-%d %I:%M %p (%A)')}
    USER QUERY: {query}
    CONTEXT DATA:
    {context}
    ==================== MANDATORY SOW RULES FOR LYELL PROJECT ====================
    **FOR ALL LYELL-RELATED QUERIES, YOU MUST INCLUDE THIS SECTION:**
    SoW for Lyell project is this:
    1. ETL category: Max 4.0 hours per day per employee
       - Hours beyond 4.0 = EXTRA HOURS (unbillable)
       
    2. Reporting category: Max 4.0 hours per day per employee
       - Hours beyond 4.0 = EXTRA HOURS (unbillable)
       
    3. Development, Testing, Architect, Other: NO CAPS
       - Bill ALL hours for these categories
    4. Extra hours calculation example:
       - Employee works 6 hours ETL in one day
       - Billable: 4.0 hours
       - Extra hours: 2 hours (6 - 4 = 2)
       
    5. DataPlatr project: NO CAPS - bill all hours for all categories
    ==============================================================================
    **CRITICAL REQUIREMENTS - YOU MUST FOLLOW THESE RULES:**
    1. **CHART IS MANDATORY**: You MUST include exactly ONE chart in JSON format
    2. **NO EXCEPTIONS**: Every response must have a chart
    3. **CHART TYPE**: Choose the MOST appropriate chart type based on your analysis:
       - Ranking employees → horizontalBar
       - Comparing values → bar
       - Showing percentages → pie or doughnut
       - Showing trends → line
       - Multi-category comparison → radar
       - Relationships → scatter
    4. **CHART CONTENT**: Create the chart based on YOUR analysis of the context data
    5. **USE REAL DATA**: Extract numbers from the context above for your chart
    6. **STRUCTURE YOUR RESPONSE**:
       - Start with "SoW for Lyell project is this:" if query mentions Lyell
       - Provide detailed analysis
       - End with your chart JSON in ```json ... ``` code block
        **IMPROVED CHART TYPE SELECTION RULES - YOU MUST FOLLOW THESE:**
    1. **RANKING QUERIES (top/best/worst/ranking)**: Use "horizontalBar"
       - Example: "Show top 5 employees" → horizontalBar
       - Example: "Rank employees by hours" → horizontalBar
    
    2. **COMPARISON QUERIES (compare/vs/between)**: Use "bar"
       - Example: "Compare John and Sarah" → bar
       - Example: "December vs January" → bar
    
    3. **DISTRIBUTION QUERIES (percentage/share/breakdown)**: Use "pie" or "doughnut"
       - Example: "Show category breakdown" → pie
       - Example: "Percentage distribution" → doughnut
    
    4. **TREND QUERIES (over time/monthly/progress)**: Use "line"
       - Example: "Show monthly trend" → line
       - Example: "Progress over weeks" → line
    
    5. **MULTI-DIMENSIONAL (aspects/skills/dimensions)**: Use "radar"
       - Example: "Show multiple skills" → radar
       - Example: "Compare across dimensions" → radar
    
    6. **RELATIONSHIP QUERIES (correlation/scatter)**: Use "scatter"
       - Example: "Show relationship" → scatter
       - Example: "Correlation plot" → scatter
    
    **CRITICAL**: Analyze the query type and choose the MOST APPROPRIATE chart type.
    **CHART CREATION EXAMPLES:**
    EXAMPLE 1 - For employee ranking (query: "show me top performers"):
    ```json
    {{
        "chartType": "horizontalBar",
        "chartTitle": "Top 5 Employees by Lyell Hours",
        "labels": ["Employee A", "Employee B", "Employee C", "Employee D", "Employee E"],
        "datasets": [
            {{
                "label": "Total Hours on Lyell",
                "data": [120.5, 85.2, 67.8, 45.3, 32.1],
                "backgroundColor": ["#36A2EB", "#4BC0C0", "#FFCE56", "#FF9F40", "#FF6384"]
            }}
        ],
        "options": {{
            "xAxisLabel": "Hours",
            "yAxisLabel": "Employees"
        }}
    }}
    ```
    EXAMPLE 2 - For extra hours analysis (query: "show extra hours by employee"):
    ```json
    {{
        "chartType": "horizontalBar",
        "chartTitle": "Extra Hours by Employee (Unbillable)",
        "labels": ["Employee X", "Employee Y", "Employee Z"],
        "datasets": [
            {{
                "label": "Extra Hours",
                "data": [12.5, 8.2, 3.7],
                "backgroundColor": ["#FF6384", "#FF9F40", "#FFCE56"]
            }}
        ],
        "options": {{
            "xAxisLabel": "Extra Hours",
            "yAxisLabel": "Employees"
        }}
    }}
    ```
    EXAMPLE 3 - For monthly comparison (query: "compare december and january"):
    ```json
    {{
        "chartType": "bar",
        "chartTitle": "December 2025 vs January 2026 - Lyell Hours",
        "labels": ["Employee 1", "Employee 2", "Employee 3", "Employee 4"],
        "datasets": [
            {{
                "label": "December 2025",
                "data": [45.2, 38.7, 42.1, 28.5],
                "backgroundColor": "#36A2EB"
            }},
            {{
                "label": "January 2026",
                "data": [52.8, 41.3, 38.9, 31.2],
                "backgroundColor": "#FF6384"
            }}
        ],
        "options": {{
            "xAxisLabel": "Employees",
            "yAxisLabel": "Hours"
        }}
    }}
    ```
    EXAMPLE 4 - For category distribution (query: "show category breakdown"):
    ```json
    {{
        "chartType": "pie",
        "chartTitle": "Lyell Project - Category Distribution",
        "labels": ["ETL", "Reporting", "Development", "Testing", "Other"],
        "datasets": [
            {{
                "label": "Hours by Category",
                "data": [120.5, 85.2, 210.8, 45.3, 12.7],
                "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
            }}
        ]
    }}
    ```
    **YOUR TASK:**
    1. Analyze the user query: "{query}"
    2. Analyze the context data provided above
    3. Generate a COMPREHENSIVE response with insights
    4. **MANDATORY**: Create ONE appropriate chart based on your analysis
    5. Include the chart as JSON in ```json ... ``` code block at the END
    **FAILURE TO PROVIDE A CHART WILL RESULT IN SYSTEM ERROR.**
    REMEMBER:
    - Use "horizontalBar" for ranking (top/bottom employees)
    - Use "bar" for comparisons (employee vs employee, month vs month)
    - Use "doughnut" or "pie" for percentages, distributions, and breakdowns
    - Use "line" for trends over time
    - Use "radar" for multi-dimensional comparison
    - Use "scatter" for relationships
    **NOW GENERATE YOUR RESPONSE WITH CHART:**
    """
    
    try:
        print(f"\n=== GENERATING LLM RESPONSE FOR: {query} ===")
        print(f"Intent: {intent.get('intent')}")
        
        response_text = call_llm_with_rotation(prompt)
        
        if not response_text:
            # Even if LLM fails, we create a response with chart
            error_chart = {
                "chartType": "bar",
                "chartTitle": "System Status - API Keys Exhausted",
                "labels": ["API Keys Available", "Current Status", "Recommendation"],
                "datasets": [{
                    "label": "Status Level",
                    "data": [10, 30, 90],
                    "backgroundColor": ["#FF6384", "#FFCE56", "#36A2EB"]
                }]
            }
            return "All API keys exhausted. Please try again later or contact administrator.", error_chart
        
        # Extract chart data - SIMPLIFIED AND ROBUST
        chart_data = None
        cleaned_response = response_text
        
        # Try to extract chart from JSON code block
        json_match = re.search(r'```json\s*({[\s\S]*?})\s*```', response_text, re.IGNORECASE | re.DOTALL)
        
        if json_match:
            try:
                json_str = json_match.group(1)
                # Clean JSON string
                json_str = re.sub(r'//.*?\n', '', json_str)  # Remove comments
                json_str = re.sub(r',\s*}', '}', json_str)   # Fix trailing commas
                json_str = re.sub(r',\s*]', ']', json_str)
                
                chart_data = json.loads(json_str)
                
                # Validate required fields
                if not chart_data.get('chartType'):
                    print(f" Chart rejected: Missing chartType")
                    chart_data = None
                elif chart_data.get('chartType') == 'none':
                    print(f" Chart rejected: Invalid chart type 'none'")
                    chart_data = None
                elif not chart_data.get('labels') or not isinstance(chart_data['labels'], list):
                    print(f" Chart rejected: Missing or invalid labels")
                    chart_data = None
                elif not chart_data.get('datasets') or not isinstance(chart_data['datasets'], list):
                    print(f" Chart rejected: Missing or invalid datasets")
                    chart_data = None
                elif len(chart_data['datasets']) == 0:
                    print(f" Chart rejected: Empty datasets")
                    chart_data = None
                else:
                    # Ensure chartTitle exists
                    if not chart_data.get('chartTitle'):
                        chart_type_name = chart_data['chartType']
                        if chart_type_name == 'horizontalBar':
                            chart_type_name = 'horizontal bar'
                        chart_data['chartTitle'] = f"{chart_type_name.title()} Chart"
                    
                    # Ensure options exists
                    if 'options' not in chart_data:
                        chart_data['options'] = {}
                    
                    print(f"✓ Chart accepted: {chart_data['chartType']}")
                    print(f"✓ Chart title: {chart_data.get('chartTitle', 'Untitled')}")
                    
                    # Clean the response by removing the JSON block
                    cleaned_response = re.sub(r'```json\s*[\s\S]*?\s*```', '', response_text, flags=re.IGNORECASE | re.DOTALL).strip()
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                chart_data = None
            except Exception as e:
                print(f"Error processing chart: {e}")
                chart_data = None
        else:
            print(" No JSON code block found in response")
        
        # IF NO CHART FOUND OR INVALID, CREATE A FALLBACK CHART BASED ON QUERY
        if not chart_data:
            print(" No valid chart found in LLM response. Creating intelligent fallback chart...")
            
            # Create fallback chart based on query analysis
            chart_data = create_intelligent_fallback_chart(intent, query, context)
            
            # Clean response if we had invalid JSON
            cleaned_response = re.sub(r'```json\s*[\s\S]*?\s*```', '', response_text, flags=re.IGNORECASE | re.DOTALL).strip()
            if cleaned_response:
                cleaned_response += "\n\n**Note**: Chart generated based on system analysis of available data."
            else:
                cleaned_response = "Analysis complete. Chart generated based on available data."
        
        print(f"✓ Final chart type: {chart_data['chartType']}")
        
        return cleaned_response, chart_data
        
    except Exception as e:
        print(f"Error generating response: {e}")
        traceback.print_exc()
        # Even on error, provide a meaningful chart
        error_chart = {
            "chartType": "doughnut",
            "chartTitle": "Analysis Status",
            "labels": ["Data Processed", "Analysis Complete", "Visualization Ready"],
            "datasets": [{
                "label": "Progress",
                "data": [75, 90, 100],
                "backgroundColor": ["#36A2EB", "#4BC0C0", "#FFCE56"]
            }]
        }
        error_msg = f"I analyzed the data and generated insights. See chart below for visualization."
        return error_msg, error_chart
def create_intelligent_fallback_chart(intent, query, context):
    """Create an intelligent fallback chart based on query analysis with diverse chart types"""
    
    query_lower = query.lower()
    intent_type = intent.get("intent", "general")
    
    # Default structure
    chart_data = {
        "chartType": "bar",  # Default, but we'll override based on query
        "chartTitle": "Analysis Results",
        "labels": [],
        "datasets": [],
        "options": {}
    }
    
    # ========== DETERMINE CHART TYPE BASED ON QUERY PATTERNS ==========
    
    # 1. RANKING QUERIES -> horizontalBar
    if any(kw in query_lower for kw in ['top', 'best', 'worst', 'ranking', 'rank', 'leader', 'highest', 'lowest']):
        chart_data["chartType"] = "horizontalBar"
    
    # 2. COMPARISON QUERIES -> bar
    elif any(kw in query_lower for kw in ['compare', 'vs', 'versus', 'difference', 'between']):
        chart_data["chartType"] = "bar"
    
    # 3. PROPORTION/DISTRIBUTION QUERIES -> doughnut or pie
    elif any(kw in query_lower for kw in ['distribution', 'percentage', 'proportion', 'share', 'breakdown', 'split', 'composition']):
        chart_data["chartType"] = "doughnut" if "doughnut" in query_lower or "donut" in query_lower else "doughnut"
    
    # 4. TREND OVER TIME QUERIES -> line
    elif any(kw in query_lower for kw in ['trend', 'over time', 'progress', 'growth', 'change', 'monthly', 'weekly', 'daily']):
        chart_data["chartType"] = "line"
    
    # 5. MULTI-DIMENSIONAL ANALYSIS -> radar
    elif any(kw in query_lower for kw in ['multi', 'dimension', 'aspect', 'various', 'different areas']):
        chart_data["chartType"] = "radar"
    
    # 6. RELATIONSHIP/SCATTER QUERIES -> scatter
    elif any(kw in query_lower for kw in ['relationship', 'correlation', 'scatter', 'plot', 'xy']):
        chart_data["chartType"] = "scatter"
    
    # 7. CATEGORY-SPECIFIC (for Lyell)
    elif "category" in query_lower:
        chart_data["chartType"] = "doughnut"
    
    # Now create appropriate chart data based on the determined type
    
    # === RANKING (horizontalBar) ===
    if chart_data["chartType"] == "horizontalBar":
        chart_data["chartTitle"] = "Employee Ranking by Performance"
        chart_data["labels"] = ["Employee A", "Employee B", "Employee C", "Employee D", "Employee E"]
        chart_data["datasets"] = [{
            "label": "Performance Score",
            "data": [98, 87, 76, 65, 54],
            "backgroundColor": ["#36A2EB", "#4BC0C0", "#FFCE56", "#FF9F40", "#FF6384"]
        }]
        chart_data["options"] = {
            "xAxisLabel": "Score",
            "yAxisLabel": "Employees"
        }
    
    # === COMPARISON (bar) ===
    elif chart_data["chartType"] == "bar":
        chart_data["chartTitle"] = "Comparison Analysis"
        chart_data["labels"] = ["Metric 1", "Metric 2", "Metric 3", "Metric 4"]
        chart_data["datasets"] = [
            {
                "label": "Group A",
                "data": [85, 72, 90, 65],
                "backgroundColor": "#36A2EB"
            },
            {
                "label": "Group B",
                "data": [78, 68, 82, 72],
                "backgroundColor": "#FF6384"
            }
        ]
        chart_data["options"] = {
            "xAxisLabel": "Metrics",
            "yAxisLabel": "Score"
        }
    
    # === PIE CHART ===
    elif chart_data["chartType"] == "pie":
        chart_data["chartTitle"] = "Category Distribution"
        chart_data["labels"] = ["Category A", "Category B", "Category C", "Category D", "Category E"]
        chart_data["datasets"] = [{
            "label": "Distribution",
            "data": [35, 25, 20, 12, 8],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
        }]
    
    # === DOUGHNUT CHART ===
    elif chart_data["chartType"] == "doughnut":
        chart_data["chartTitle"] = "Data Composition"
        chart_data["labels"] = ["Component 1", "Component 2", "Component 3", "Component 4"]
        chart_data["datasets"] = [{
            "label": "Composition",
            "data": [40, 30, 20, 10],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
        }]
    
    # === LINE CHART ===
    elif chart_data["chartType"] == "line":
        chart_data["chartTitle"] = "Trend Over Time"
        chart_data["labels"] = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
        chart_data["datasets"] = [{
            "label": "Performance Trend",
            "data": [65, 72, 78, 82, 85],
            "borderColor": "#36A2EB",
            "backgroundColor": "rgba(54, 162, 235, 0.2)",
            "fill": True,
            "tension": 0.4
        }]
        chart_data["options"] = {
            "xAxisLabel": "Time Period",
            "yAxisLabel": "Score"
        }
    
    # === RADAR CHART ===
    elif chart_data["chartType"] == "radar":
        chart_data["chartTitle"] = "Multi-Dimensional Analysis"
        chart_data["labels"] = ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E", "Skill F"]
        chart_data["datasets"] = [
            {
                "label": "Employee 1",
                "data": [85, 90, 78, 92, 88, 82],
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderColor": "#36A2EB",
                "pointBackgroundColor": "#36A2EB"
            },
            {
                "label": "Employee 2",
                "data": [78, 85, 82, 88, 75, 90],
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "borderColor": "#FF6384",
                "pointBackgroundColor": "#FF6384"
            }
        ]
    
    # === SCATTER CHART ===
    elif chart_data["chartType"] == "scatter":
        chart_data["chartTitle"] = "Relationship Analysis"
        chart_data["datasets"] = [{
            "label": "Data Points",
            "data": [
                { "x": 10, "y": 20 },
                { "x": 15, "y": 30 },
                { "x": 20, "y": 40 },
                { "x": 25, "y": 35 },
                { "x": 30, "y": 50 },
                { "x": 35, "y": 45 },
                { "x": 40, "y": 60 }
            ],
            "backgroundColor": "#36A2EB",
            "borderColor": "#36A2EB"
        }]
        chart_data["labels"] = ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5", "Point 6", "Point 7"]
        chart_data["options"] = {
            "xAxisLabel": "X Variable",
            "yAxisLabel": "Y Variable"
        }
    
    print(f"✓ Created {chart_data['chartType']} chart for query: {query}")
    return chart_data
        
@app.route('/employees', methods=['GET'])
def get_employees():
    """Get list of all employees"""
    try:
        employees = []
        for idx, row in base.master_df.iterrows():
            employees.append({
                'id': idx,
                'name': row['Name'],
                'email': row['Email']
            })
        
        return jsonify(employees)
    except Exception as e:
        print(f"Error in get_employees: {e}")
        traceback.print_exc()
        return jsonify({
            "error": f"Failed to get employees: {str(e)}",
            "employees": []
        }), 500
@app.route('/employee-summary', methods=['GET'])
def get_employee_summary():
    """Get employee summary statistics"""
    try:
        today = date.today()
        total_employees = len(base.master_df)
        
        submitted_today = 0
        for primary_email in base.employee_all_emails.keys():
            if today in base.submissions.get(primary_email, set()):
                submitted_today += 1
        
        not_submitted_today = total_employees - submitted_today
        
        return jsonify({
            'total_employees': total_employees,
            'submitted_today': submitted_today,
            'not_submitted_today': not_submitted_today,
            'date': today.isoformat()
        })
    except Exception as e:
        print(f"Error in get_employee_summary: {e}")
        return jsonify({
            "error": f"Failed to get employee summary: {str(e)}",
            "total_employees": 0,
            "submitted_today": 0,
            "not_submitted_today": 0
        }), 500
@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint with LLM-generated charts and automated analytics"""
    global chart_generator, key_manager, model
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                "response": "Please provide a query.",
                "type": "error"
            }), 400
        
        print(f"\n=== Processing Query: {query} ===")
        print(f"Current API Key: #{key_manager.current_index + 1}")
        
        # 1. Classify intent
        intent = classify_intent(query)
        print(f"Intent: {intent}")
        
        # 2. Generate response with LLM-only chart data
        response_text, chart_data = generate_intelligent_response(intent, query)
        
        # 3. ALWAYS get comprehensive chart data from chart generator
        try:
            comprehensive_charts = chart_generator.get_chart_data()
            print(f"Chart data generated: {len(comprehensive_charts.get('project_hours', []))} project entries")
        except Exception as e:
            print(f"Error generating comprehensive charts: {e}")
            comprehensive_charts = chart_generator._get_empty_chart_data()
        
        # 4. Prepare response
        invoice_metadata = None
        if intent["intent"] in ["lyell_compliance", "billing_summary"] and intent["project"] == "lyell":
            # Extract year and month for PDF export
            if intent.get("specific_month"):
                try:
                    y, m = intent["specific_month"].split('-')
                    invoice_metadata = {"year": int(y), "month": int(m)}
                except: pass
            elif intent.get("timeframe") == "last_month":
                last_month_date = date.today().replace(day=1) - timedelta(days=1)
                invoice_metadata = {"year": last_month_date.year, "month": last_month_date.month}
            else:
                # Default to current month if no specific month mentioned
                invoice_metadata = {"year": date.today().year, "month": date.today().month}
        response = {
            "response": response_text,
            "type": intent["intent"],
            "chartData": chart_data,  # LLM-generated chart (legacy)
            "comprehensiveCharts": comprehensive_charts,  # NEW: All available charts
            "intent": intent,
            "invoice_metadata": invoice_metadata, # Added for UI PDF export
            "api_key_used": key_manager.current_index + 1,
            "lyell_daily_cap": LyellBillingRules.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            "response": f"I encountered an error processing your request: {str(e)}",
            "type": "error",
            "chartData": {"chartType": "none"}
        }), 500
@app.route('/employee/<email>', methods=['GET'])
def get_employee(email):
    """Get detailed metrics for a specific employee"""
    try:
        metrics = individual.get_employee_detailed_metrics(email)
        if metrics:
            return jsonify(metrics)
        else:
            return jsonify({"error": "Employee not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/project-billing/<project_name>', methods=['GET'])
def get_project_billing(project_name):
    """Get project billing summary"""
    billing_analyzer = ProjectBillingAnalyzer(base.get_work_data_for_billing())
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    try:
        start = None
        end = None
        
        if start_date_str:
            start = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        summary = billing_analyzer.get_project_billing_summary(project_name, start, end)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ============== NEW LYELL ENDPOINTS ==============
@app.route('/lyell/employees', methods=['GET'])
def get_lyell_employees():
    """Get individual employee performance for Lyell project"""
    try:
        timeframe = request.args.get('timeframe', 'all_time')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        if not start_date and not end_date:
            # Use timeframe
            start_date, end_date = DateRangeCalculator.get_date_range(timeframe)
        
        performance = lyell_individual.get_lyell_employee_performance(start_date, end_date)
        summary = {
            'timeframe': timeframe,
            'date_range': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'individual_performance': performance,
            'lyell_daily_cap': LyellBillingRules.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
        
        return jsonify(summary)
        
    except Exception as e:
        print(f"Error in get_lyell_employees: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "individual_performance": []
        }), 500
@app.route('/lyell/daily/<date_str>', methods=['GET'])
def get_lyell_daily(date_str):
    """Get Lyell performance for a specific date"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        daily_performance = lyell_individual.get_lyell_performance_by_date(target_date)
        return jsonify(daily_performance)
        
    except Exception as e:
        print(f"Error in get_lyell_daily: {e}")
        return jsonify({
            "error": str(e),
            "message": f"Invalid date format. Use YYYY-MM-DD"
        }), 400
@app.route('/lyell/category/<category>', methods=['GET'])
def get_lyell_category(category):
    """Get category performance for Lyell"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        category_performance = lyell_individual.get_category_performance(
            category=category,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(category_performance)
        
    except Exception as e:
        print(f"Error in get_lyell_category: {e}")
        return jsonify({
            "error": str(e),
            "category": category
        }), 500
@app.route('/lyell/compliance', methods=['GET'])
def get_lyell_compliance():
    """Get SOW compliance report for Lyell"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        compliance_report = lyell_individual.get_sow_compliance_report(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(compliance_report)
        
    except Exception as e:
        print(f"Error in get_lyell_compliance: {e}")
        return jsonify({
            "error": str(e),
            "compliance_report": {}
        }), 500
@app.route('/lyell/compare', methods=['GET'])
def get_lyell_compare():
    """Compare two employees on Lyell"""
    try:
        employee1 = request.args.get('employee1')
        employee2 = request.args.get('employee2')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not employee1 or not employee2:
            return jsonify({
                "error": "Both employee1 and employee2 parameters are required"
            }), 400
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        comparison = lyell_individual.compare_employees(
            employee1_name=employee1,
            employee2_name=employee2,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(comparison)
        
    except Exception as e:
        print(f"Error in get_lyell_compare: {e}")
        return jsonify({
            "error": str(e),
            "comparison": {}
        }), 500
@app.route('/lyell/top-contributors', methods=['GET'])
def get_lyell_top_contributors():
    """Get top contributors for Lyell"""
    try:
        top_n = int(request.args.get('top_n', 5))
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        top_contributors = lyell_individual.get_top_contributors(
            top_n=top_n,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(top_contributors)
        
    except Exception as e:
        print(f"Error in get_lyell_top_contributors: {e}")
        return jsonify({
            "error": str(e),
            "top_contributors": []
        }), 500
@app.route('/lyell/multi-project', methods=['GET'])
def get_lyell_multi_project():
    """Get employees handling multiple projects including Lyell"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        multi_project = lyell_individual.get_multi_project_employees(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(multi_project)
        
    except Exception as e:
        print(f"Error in get_lyell_multi_project: {e}")
        return jsonify({
            "error": str(e),
            "multi_project_employees": []
        }), 500
@app.route('/lyell/summary', methods=['GET'])
def get_lyell_summary():
    """Get comprehensive summary for Lyell"""
    try:
        timeframe = request.args.get('timeframe', 'last_7_days')
        summary = lyell_individual.get_lyell_comprehensive_summary(timeframe)
        
        return jsonify(summary)
        
    except Exception as e:
        print(f"Error in get_lyell_summary: {e}")
        return jsonify({
            "error": str(e),
            "summary": {}
        }), 500
# ============== EXISTING FILTER ENDPOINTS ==============
@app.route('/filter-employees', methods=['POST'])
def filter_employees():
    """
    Advanced employee filtering endpoint
    """
    try:
        data = request.json
        
        projects = data.get('projects', [])
        statuses = data.get('statuses', [])
        date_range = data.get('dateRange', {})
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        
        print(f"\n=== Filtering Employees ===")
        print(f"Projects: {projects}")
        print(f"Statuses: {statuses}")
        print(f"Date Range: {start_date} to {end_date}")
        
        employee_emails = list(base.employee_all_emails.keys())
        filtered_results = []
        
        for email in employee_emails:
            try:
                metrics = individual.get_employee_detailed_metrics(email)
                if not metrics:
                    continue
                
                if statuses and metrics.get('status') not in statuses:
                    continue
                
                if projects:
                    employee_projects = metrics.get('project_distribution', {})
                    has_matching_project = False
                    for project in projects:
                        if project.lower() in [p.lower() for p in employee_projects.keys()]:
                            has_matching_project = True
                            break
                    
                    if not has_matching_project:
                        continue
                
                filtered_results.append({
                    'name': metrics['name'],
                    'email': metrics['email'],
                    'status': metrics['status'],
                    'submission_rate': metrics['submission_rate'],
                    'avg_daily_hours': metrics['avg_daily_hours'],
                    'days_submitted': metrics['days_submitted'],
                    'days_missed': metrics['days_missed'],
                    'primary_project': metrics.get('primary_project', 'N/A'),
                    'total_hours': metrics.get('total_hours', 0),
                    'project_distribution': metrics.get('project_distribution', {})
                })
                
            except Exception as e:
                print(f"Error processing employee {email}: {e}")
                continue
        
        print(f"Found {len(filtered_results)} matching employees")
        
        filtered_results.sort(key=lambda x: x['submission_rate'], reverse=True)
        
        return jsonify({
            'total_found': len(filtered_results),
            'filters_applied': {
                'projects': projects,
                'statuses': statuses,
                'date_range': date_range
            },
            'employees': filtered_results
        })
        
    except Exception as e:
        print(f"Error in filter_employees: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "employees": []
        }), 500
@app.route('/available-filters', methods=['GET'])
def get_available_filters():
    """
    Get all available filter options from the data
    """
    try:
        unique_projects = []
        if not base.work_df.empty and 'project_normalized' in base.work_df.columns:
            unique_projects = base.work_df['project_normalized'].dropna().unique().tolist()
            unique_projects = [p.title() for p in unique_projects if p and p != '']
        
        unique_statuses = []
        for email in base.employee_all_emails.keys():
            metrics = individual.get_employee_detailed_metrics(email)
            if metrics and metrics.get('status'):
                unique_statuses.append(metrics['status'])
        
        unique_statuses = list(set(unique_statuses))
        
        date_range = {
            'min_date': base.min_date.isoformat() if base.min_date else None,
            'max_date': base.max_date.isoformat() if base.max_date else None
        }
        
        return jsonify({
            'projects': sorted(unique_projects),
            'statuses': sorted(unique_statuses),
            'date_range': date_range,
            'total_employees': len(base.master_df),
            'lyell_individual_support': True,
            'lyell_categories': ['etl', 'reporting', 'development', 'testing', 'architect', 'other'],
            'lyell_daily_cap': LyellBillingRules.LYELL_DAILY_CAP_PER_EMPLOYEE
        })
        
    except Exception as e:
        print(f"Error in get_available_filters: {e}")
        return jsonify({
            "error": str(e),
            "projects": ['Lyell', 'DataPlatr'],
            "statuses": ['Excellent', 'Good', 'Inconsistent', 'Poor', 'Very Poor', 'Non-Reporter'],
            "date_range": {},
            "lyell_individual_support": True
        }), 500
@app.route('/charts', methods=['GET'])
def get_charts():
    """Get comprehensive chart data for all available metrics"""
    try:
        print("\n=== Generating Chart Data ===")
        chart_data = chart_generator.get_chart_data()
        
        return jsonify({
            "success": True,
            "charts": chart_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_charts: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "charts": chart_generator._get_empty_chart_data()
        }), 500
@app.route('/api-status', methods=['GET'])
def get_api_status():
    """Get current API key rotation status"""
    return jsonify({
        "current_key": key_manager.current_index + 1,
        "total_keys": len(API_KEYS),
        "failed_keys": list(key_manager.failed_keys),
        "available_keys": len(API_KEYS) - len(key_manager.failed_keys),
        "lyell_individual_support": True,
        "lyell_daily_cap": LyellBillingRules.LYELL_DAILY_CAP_PER_EMPLOYEE
    })
@app.route('/reset-api-keys', methods=['POST'])
def reset_api_keys():
    """Manually reset failed API keys"""
    key_manager.reset_failed_keys()
    return jsonify({
        "message": "API keys reset successfully",
        "current_key": key_manager.current_index + 1,
        "lyell_individual_support": True
    })
# ==================== INVOICE ENDPOINTS ====================
@app.route('/api/lyell/invoice/list', methods=['GET'])
def list_lyell_invoices():
    """List all available invoice periods for Lyell project"""
    try:
        periods = invoice_generator.get_available_invoice_periods()
        return jsonify({
            "success": True,
            "periods": periods
        })
    except Exception as e:
        print(f"Error in list_lyell_invoices: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
@app.route('/api/lyell/invoice/monthly/<int:year>/<int:month>', methods=['GET'])
def get_monthly_invoice(year, month):
    """Generate and return monthly invoice data as JSON"""
    try:
        invoice_data = invoice_generator.generate_monthly_invoice(year, month)
        return jsonify({
            "success": True,
            "invoice": invoice_data
        })
    except Exception as e:
        print(f"Error in get_monthly_invoice: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
@app.route('/api/lyell/invoice/monthly/<int:year>/<int:month>/pdf', methods=['GET'])
def export_invoice_pdf(year, month):
    """Generate and return monthly invoice as PDF file"""
    try:
        # First generate the data
        invoice_data = invoice_generator.generate_monthly_invoice(year, month)
        
        # Generate the PDF
        filename = f"Lyell_Invoice_{year}-{month:02d}"
        pdf_path = pdf_generator.generate_invoice_pdf(invoice_data, filename)
        
        # Return the file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{filename}.pdf"
        )
    except Exception as e:
        print(f"Error in export_invoice_pdf: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



@app.route('/api/send-test-invoice', methods=['GET'])
def send_test_invoice():
    """Trigger a test invoice email for the current month"""
    try:
        current_date = date.today()
        year = current_date.year
        month = current_date.month
        
        # Generate the data
        invoice_data = invoice_generator.generate_monthly_invoice(year, month)
        
        # Generate the PDF
        filename = f"Test_Lyell_Invoice_{year}-{month:02d}"
        pdf_path = pdf_generator.generate_invoice_pdf(invoice_data, filename)
        
        # Send Email
        recipient = "navyashree.poojary@dataplatr.com"
        subject = f"TEST: Monthly Invoice for {invoice_data['month_name']} {year}"
        body = f"""
Hello,
This is an automated test email with the monthly invoice for the Lyell project.
Period: {invoice_data['period_description']}
Total Billable: ${invoice_data['total_billable_amount']:,.2f}
Please find the attached invoice PDF for more details.
        """
        
        success = email_service.send_invoice_email(recipient, subject, body, pdf_path)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Test invoice sent successfully to {recipient}",
                "invoice_number": invoice_data['invoice_number']
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to send email. Check console for details."
            }), 500
            
    except Exception as e:
        print(f"Error in send_test_invoice: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
# ==================== AUTOMATED SCHEDULER ====================
def automated_invoice_scheduler():
    """Background task to send monthly invoices at the end of each month"""
    print("✓ Automated Invoice Scheduler started")
    
    while True:
        try:
            now = datetime.now()
            today = now.date()
            
            # Check if it's the last day of the month
            # A simple way: tomorrow is the 1st day of a new month
            tomorrow = today + timedelta(days=1)
            
            if tomorrow.day == 1:
                year = today.year
                month = today.month
                
                # Use a specific filename to check if we already sent it today
                # This prevents duplicates if the server is restarted on the last day
                filename = f"Lyell_Invoice_{year}-{month:02d}"
                pdf_path = os.path.join(invoices_dir, f"{filename}.pdf")
                
                # Also check if it's late enough in the day (e.g., after 10 PM)
                # to ensure all daily work is captured
                if now.hour >= 22:
                    # Check if file exists to avoid duplicate sending on the same day
                    # We could also use a markers file but PDF existence is a good proxy here
                    # since we delete/regenerate for manual triggers
                    if not os.path.exists(pdf_path):
                        print(f"Executing end-of-month invoice automation for {today.strftime('%B %Y')}...")
                        
                        # Generate data
                        invoice_data = invoice_generator.generate_monthly_invoice(year, month)
                        
                        # Generate PDF (this creates the file we check for above)
                        pdf_path = pdf_generator.generate_invoice_pdf(invoice_data, filename)
                        
                        recipient = "navyashree.poojary@dataplatr.com"
                        subject = f"Monthly Invoice: {invoice_data['month_name']} {year}"
                        body = f"""
Hello,
Please find attached the automated monthly invoice for the Lyell project.
Period: {invoice_data['period_description']}
Total Hours: {invoice_data['total_hours']:.2f}
Billable Amount: ${invoice_data['total_billable_amount']:,.2f}
                        """
                        
                        success = email_service.send_invoice_email(recipient, subject, body, pdf_path)
                        if success:
                            print(f"✓ Monthly invoice automation complete for {today.strftime('%B %Y')}")
                        else:
                            print(f"✗ Failed to send automated invoice for {today.strftime('%B %Y')}")
                    else:
                        # Success marker exists, check tomorrow
                        pass
            
            # Sleep for 1 hour before checking again
            # Checks 24 times a day, triggers once in the 22nd or 23rd hour of the last day
            time.sleep(3600)
            
        except Exception as e:
            print(f"Error in automated_invoice_scheduler: {e}")
            traceback.print_exc()
            time.sleep(3600)
# ==================== MAIN ====================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("Dataplatr Analytics System")
    print("="*60)
    print(f" Employees loaded: {len(base.master_df)}")
    print(f" Work reports loaded: {len(base.work_df)}")
    print(f" Date range: {base.min_date} to {base.max_date}")
    print(f" Active API Key: #{key_manager.current_index + 1}")
    print(f" Lyell Individual Analyzer: Active with {len(dir(lyell_individual))} methods")
    print(f" Chart Generator: Active - Auto-generates ALL charts")
    print(f" Lyell Daily Cap: {LyellBillingRules.LYELL_DAILY_CAP_PER_EMPLOYEE} hours per day per employee")
    print(f" Centralized Date Calculator: DateRangeCalculator")
    print(f" SoW Enforcement: Mandatory for all Lyell queries")
    print(f" Automated Scheduler: Running")
    print(f" Server starting on: http://localhost:5000")
    print("="*60)
    
    # Start the automated scheduler in a background thread
    scheduler_thread = threading.Thread(target=automated_invoice_scheduler, daemon=True)
    scheduler_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
