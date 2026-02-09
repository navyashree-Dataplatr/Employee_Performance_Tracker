


# trial sow rules and hours 

# extra n 4hrs trial
# FILE: lyell_individual_analyzer.py
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import re


class LyellIndividualAnalyzer:
    """
    Comprehensive analyzer for Lyell project individual employee performance.
    Supports all types of queries including date-range, task-level, compliance, and comparisons.
    
    CRITICAL BILLING RULES FOR LYELL:
    - ETL: Max 4 hours per day per employee (hours beyond 4 = extra hours)
    - Reporting: Max 4 hours per day per employee (hours beyond 4 = extra hours)
    - Development, Testing, Architect, Other: NO CAPS - bill all hours
    """
    
    # CRITICAL: Lyell project billing cap
    LYELL_DAILY_CAP_PER_EMPLOYEE = 4.0  # hours per day per employee
    
    # SOW Rules for Lyell - SINGLE SOURCE OF TRUTH
    LYELL_SOW_RULES = {
        'etl': {
            'max_hours_per_day': 4.0,  # CRITICAL: 4 hours per day per employee
            'keywords': [r'\[etl\]', r'etl', r'data pipeline', r'data processing', r'elf work']
        },
        'reporting': {
            'max_hours_per_day': 4.0,  # CRITICAL: 4 hours per day per employee
            'keywords': [r'report', r'dashboard', r'analytics', r'visualization', r'reporting']
        },
        # No caps for these categories (Lyell)
        'development': {
            'max_hours_per_day': None,  # NO CAP
            'keywords': [r'development', r'dev', r'coding', r'programming', r'\[development\]']
        },
        'testing': {
            'max_hours_per_day': None,  # NO CAP
            'keywords': [r'testing', r'qa', r'quality assurance', r'\[testing\]', r'\[qa\]']
        },
        'architect': {
            'max_hours_per_day': None,  # NO CAP
            'keywords': [r'architect', r'design', r'planning', r'strategy', r'architecture']
        },
        'other': {
            'max_hours_per_day': None,  # NO CAP
            'keywords': []
        }
    }
    
    def __init__(self, base_processor):
        """
        Initialize with BaseDataProcessor
        
        Args:
            base_processor: Instance of BaseDataProcessor
        """
        self.base = base_processor
        self.individual_analyzer = None  # Will be set separately if needed
    
    def set_individual_analyzer(self, individual_analyzer):
        """Set reference to IndividualAnalyzer for general metrics"""
        self.individual_analyzer = individual_analyzer
    
    def _calculate_extra_hours(self, actual_hours: float, category: str) -> float:
        """
        Calculate extra hours for a given category based on Lyell SOW rules.
        
        CRITICAL LOGIC:
        - ETL: Max 4 hours per day per employee
        - Reporting: Max 4 hours per day per employee
        - Other categories: NO CAP (extra hours = 0)
        
        Args:
            actual_hours: Actual hours worked
            category: Work category (etl, reporting, development, etc.)
            
        Returns:
            Extra hours (0 if no cap or under cap)
            
        Examples:
            - _calculate_extra_hours(6, 'etl') -> 2.0 (6 - 4 = 2)
            - _calculate_extra_hours(3, 'etl') -> 0.0 (under cap)
            - _calculate_extra_hours(10, 'development') -> 0.0 (no cap)
        """
        category = category.lower()
        rule = self.LYELL_SOW_RULES.get(category, {})
        max_hours = rule.get('max_hours_per_day')
        
        if max_hours is None:
            # No cap for this category
            return 0.0
        
        if actual_hours > max_hours:
            return round(actual_hours - max_hours, 2)
        
        return 0.0
    
    def _get_billable_hours(self, actual_hours: float, category: str) -> float:
        """
        Calculate billable hours for a given category.
        
        Args:
            actual_hours: Actual hours worked
            category: Work category
            
        Returns:
            Billable hours (capped if necessary)
        """
        category = category.lower()
        rule = self.LYELL_SOW_RULES.get(category, {})
        max_hours = rule.get('max_hours_per_day')
        
        if max_hours is None:
            # No cap - bill all hours
            return round(actual_hours, 2)
        
        # Cap at max_hours (4 for ETL/Reporting)
        return round(min(actual_hours, max_hours), 2)
    
    def _extract_category(self, task_text: str) -> str:
        """
        Extract work category from task text for Lyell.
        
        Args:
            task_text: Raw task description
            
        Returns:
            Category name (standardized)
        """
        if pd.isna(task_text):
            return 'other'
        
        text = str(task_text).lower()
        
        # Check each SOW category for matches
        for category, rule in self.LYELL_SOW_RULES.items():
            for keyword in rule['keywords']:
                if re.search(keyword, text, re.IGNORECASE):
                    return category
        
        # Check for bracket notation: [Category]
        bracket_match = re.search(r'\[([^\]]+)\]', text)
        if bracket_match:
            bracket_content = bracket_match.group(1).lower()
            # Map bracket content to categories
            if 'etl' in bracket_content:
                return 'etl'
            elif 'dev' in bracket_content or 'development' in bracket_content:
                return 'development'
            elif 'test' in bracket_content or 'qa' in bracket_content:
                return 'testing'
            elif 'report' in bracket_content:
                return 'reporting'
            elif 'architect' in bracket_content:
                return 'architect'
        
        # Default category
        return 'other'
    
    def _filter_lyell_data(self, 
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> pd.DataFrame:
        """
        Filter work data for Lyell project within date range
        
        Args:
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            
        Returns:
            DataFrame with Lyell work data
        """
        if self.base.work_df.empty:
            return pd.DataFrame()
        
        # DEBUG: Show project distribution before filtering
        print(f"DEBUG _filter_lyell_data: Total rows in work_df: {len(self.base.work_df)}")
        print(f"DEBUG _filter_lyell_data: Unique projects: {self.base.work_df['project_normalized'].unique()}")
        
        # Filter for Lyell project
        lyell_data = self.base.work_df[
            self.base.work_df['project_normalized'] == 'lyell'
        ].copy()
        
        print(f"DEBUG _filter_lyell_data: Found {len(lyell_data)} Lyell rows before date filtering")
        
        if lyell_data.empty:
            return lyell_data
        
        # Filter by date range if provided
        if start_date:
            rows_before = len(lyell_data)
            lyell_data = lyell_data[
                lyell_data['clean_date'].dt.date >= start_date
            ]
            print(f"DEBUG _filter_lyell_data: After start_date filter ({start_date}): {len(lyell_data)} rows (removed {rows_before - len(lyell_data)})")
        
        if end_date:
            rows_before = len(lyell_data)
            lyell_data = lyell_data[
                lyell_data['clean_date'].dt.date <= end_date
            ]
            print(f"DEBUG _filter_lyell_data: After end_date filter ({end_date}): {len(lyell_data)} rows (removed {rows_before - len(lyell_data)})")
        
        if not lyell_data.empty:
            print(f"DEBUG _filter_lyell_data: Final filtered data - {len(lyell_data)} rows, Total hours: {lyell_data['Hours'].sum():.2f}")
        
        # IMPORTANT FIX: Process each row's tasks individually to get accurate category breakdown
        # Split tasks by newline to handle multiple tasks per row
        expanded_rows = []
        for idx, row in lyell_data.iterrows():
            tasks_text = str(row['Tasks_Completed']) if pd.notna(row['Tasks_Completed']) else ''
            hours = row['Hours']
            
            # If there are multiple tasks separated by newline, split them
            if '\n' in tasks_text:
                task_lines = [line.strip() for line in tasks_text.split('\n') if line.strip()]
                # Try to extract hours from each task line
                for task_line in task_lines:
                    # Extract hours from task line if present (e.g., "(2h)", "(1.5h)")
                    task_hours_match = re.search(r'\((\d+(?:\.\d+)?)\s*(?:hrs?|hours?|h|mins?|minutes?|m)\)', task_line.lower())
                    if task_hours_match:
                        task_hours = float(task_hours_match.group(1))
                        # Check if it's minutes
                        if 'min' in task_line.lower():
                            task_hours = task_hours / 60.0
                    else:
                        # If no hours in task line, assume equal distribution
                        task_hours = hours / len(task_lines) if len(task_lines) > 0 else hours
                    
                    new_row = row.copy()
                    new_row['Tasks_Completed'] = task_line
                    new_row['Hours'] = task_hours
                    expanded_rows.append(new_row)
            else:
                expanded_rows.append(row)
        
        if expanded_rows:
            lyell_data = pd.DataFrame(expanded_rows)
            # Reset index
            lyell_data = lyell_data.reset_index(drop=True)
        
        # Add category for task-level analysis - NOW it's accurate per task
        lyell_data['category'] = lyell_data['Tasks_Completed'].apply(self._extract_category)
        
        print(f"DEBUG _filter_lyell_data: After task expansion - {len(lyell_data)} rows")
        print(f"DEBUG _filter_lyell_data: Category distribution:")
        print(lyell_data['category'].value_counts())
        
        return lyell_data
    
    def _get_employee_name(self, email: str) -> str:
        """Get employee name from email"""
        email = email.lower().strip()
        
        # Check email_to_employee mapping
        if email in self.base.email_to_employee:
            primary_email = self.base.email_to_employee[email]
            employee_info = self.base.master_df[
                self.base.master_df['Email'] == primary_email
            ]
            if not employee_info.empty:
                return employee_info.iloc[0]['Name']
        
        # Try direct lookup in master_df
        employee_info = self.base.master_df[
            self.base.master_df['Email'] == email
        ]
        if not employee_info.empty:
            return employee_info.iloc[0]['Name']
        
        # Try finding by any email variant
        for idx, row in self.base.master_df.iterrows():
            if email in [e.lower() for e in row['Emails']]:
                return row['Name']
        
        return "Unknown Employee"
    
    def _find_employee_by_name(self, name_query: str) -> Optional[str]:
        """Find employee email by partial name match"""
        name_query = name_query.lower().strip()
        
        for idx, row in self.base.master_df.iterrows():
            employee_name = row['Name'].lower()
            if name_query in employee_name or employee_name in name_query:
                return row['Email']
        
        return None
    
    # ==================== CORE PERFORMANCE METHODS ====================
    
    def get_lyell_employee_performance(self,
                                     start_date: Optional[date] = None,
                                     end_date: Optional[date] = None) -> List[Dict]:
        """
        🔹 Get individual employee performance for Lyell project
        Supports: "Show each employee's performance for the Lyell project"
        
        Args:
            start_date: Start date for analysis (inclusive)
            end_date: End date for analysis (inclusive)
            
        Returns:
            List of dictionaries with individual employee performance metrics including extra hours
        """
        print(f"Analyzing Lyell individual performance from {start_date} to {end_date}")
        
        # Get Lyell work data
        lyell_data = self._filter_lyell_data(start_date, end_date)
        
        # DEBUG: Print filtered data details for troubleshooting
        print(f"DEBUG: Lyell data filtered - {len(lyell_data)} rows")
        if not lyell_data.empty:
            print(f"DEBUG: Date range in filtered data: {lyell_data['clean_date'].min()} to {lyell_data['clean_date'].max()}")
            print(f"DEBUG: Total hours in filtered data: {lyell_data['Hours'].sum():.2f}")
            print(f"DEBUG: Unique projects in filtered data: {lyell_data['project_normalized'].unique()}")
            print(f"DEBUG: Unique employees: {lyell_data['email'].nunique()}")
        
        if lyell_data.empty:
            print("No Lyell data found in the specified date range")
            return []
        
        # Group by employee email
        employee_groups = lyell_data.groupby('email')
        
        employee_performance = []
        
        for email, group in employee_groups:
            try:
                # Get employee name
                employee_name = self._get_employee_name(email)
                
                # Calculate basic metrics
                total_hours = group['Hours'].sum()
                total_days = group['clean_date'].dt.date.nunique()
                avg_hours_per_day = total_hours / total_days if total_days > 0 else 0
                
                # Calculate category-wise hours and extra hours
                category_hours = {}
                category_billable_hours = {}
                category_extra_hours = {}
                total_extra_hours = 0
                total_billable_hours = 0
                
                # Group by category first, then by date
                for category, cat_group in group.groupby('category'):
                    # Group by date to calculate daily hours for this category
                    daily_cat_hours = cat_group.groupby('clean_date')['Hours'].sum()
                    
                    cat_actual_hours = 0
                    cat_billable_hours = 0
                    cat_extra_hours = 0
                    
                    for day_date, day_hours in daily_cat_hours.items():
                        cat_actual_hours += day_hours
                        
                        # Calculate billable and extra hours for this day
                        billable = self._get_billable_hours(day_hours, category)
                        extra = self._calculate_extra_hours(day_hours, category)
                        
                        cat_billable_hours += billable
                        cat_extra_hours += extra
                    
                    category_hours[category] = round(cat_actual_hours, 2)
                    category_billable_hours[category] = round(cat_billable_hours, 2)
                    category_extra_hours[category] = round(cat_extra_hours, 2)
                    
                    total_billable_hours += cat_billable_hours
                    total_extra_hours += cat_extra_hours
                
                # Daily breakdown
                daily_hours = group.groupby('clean_date').agg({
                    'Hours': 'sum'
                }).reset_index()
                
                daily_breakdown = []
                for _, row in daily_hours.iterrows():
                    daily_breakdown.append({
                        'date': row['clean_date'].date().isoformat(),
                        'hours': round(float(row['Hours']), 2),
                        'day_of_week': row['clean_date'].strftime('%A')
                    })
                
                # Task analysis
                task_counts = group['task_count'].sum()
                avg_tasks_per_day = task_counts / total_days if total_days > 0 else 0
                
                # Get general employee metrics if available
                general_metrics = {}
                if self.individual_analyzer:
                    try:
                        general_metrics = self.individual_analyzer.get_employee_detailed_metrics(email)
                    except:
                        pass
                
                # Create performance record
                performance = {
                    'employee_name': employee_name,
                    'employee_email': email,
                    'project': 'Lyell',
                    'analysis_period': {
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None
                    },
                    'total_hours_on_lyell': round(total_hours, 2),
                    'total_billable_hours': round(total_billable_hours, 2),
                    'total_extra_hours': round(total_extra_hours, 2),
                    'total_days_on_lyell': total_days,
                    'avg_hours_per_day': round(avg_hours_per_day, 2),
                    'total_tasks': int(task_counts),
                    'avg_tasks_per_day': round(avg_tasks_per_day, 2),
                    'category_breakdown': {
                        'actual_hours': category_hours,
                        'billable_hours': category_billable_hours,
                        'extra_hours': category_extra_hours
                    },
                    'daily_breakdown': sorted(daily_breakdown, key=lambda x: x['date']),
                    'date_range_metrics': {
                        'first_date_in_range': group['clean_date'].min().date().isoformat() if not group.empty else None,
                        'last_date_in_range': group['clean_date'].max().date().isoformat() if not group.empty else None,
                        'days_with_work': total_days
                    },
                    'contribution_percentage': 0,  # Will be calculated later
                    'extra_hours_percentage': round((total_extra_hours / total_hours * 100), 1) if total_hours > 0 else 0,
                    'billing_efficiency': round((total_billable_hours / total_hours * 100), 1) if total_hours > 0 else 0,
                    'sow_compliance_status': 'Compliant' if total_extra_hours == 0 else 'Has Violations',
                    'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE,
                    'general_metrics': {
                        'status': general_metrics.get('status', 'Unknown'),
                        'submission_rate': general_metrics.get('submission_rate', 0),
                        'avg_daily_hours': general_metrics.get('avg_daily_hours', 0)
                    } if general_metrics else None
                }
                
                employee_performance.append(performance)
                
            except Exception as e:
                print(f"Error processing employee {email}: {e}")
                continue
        
        # Calculate contribution percentages
        total_hours_all = sum(emp['total_hours_on_lyell'] for emp in employee_performance)
        if total_hours_all > 0:
            for emp in employee_performance:
                emp['contribution_percentage'] = round(
                    (emp['total_hours_on_lyell'] / total_hours_all) * 100, 1
                )
        
        # Sort by total hours (descending)
        employee_performance.sort(key=lambda x: x['total_hours_on_lyell'], reverse=True)
        
        print(f"Generated performance data for {len(employee_performance)} employees on Lyell")
        return employee_performance
    
    # ==================== DATE-RANGE & TIME-BASED QUERIES ====================
    
    def get_lyell_performance_by_date(self, 
                                    target_date: date) -> Dict:
        """
        🔹 What work was done on the Lyell project on specific date?
        
        Args:
            target_date: Specific date to analyze
            
        Returns:
            Dictionary with daily performance summary including extra hours
        """
        print(f"Analyzing Lyell performance for date: {target_date}")
        
        # Get data for specific date
        lyell_data = self._filter_lyell_data(target_date, target_date)
        
        if lyell_data.empty:
            return {
                'date': target_date.isoformat(),
                'status': 'NO_DATA',
                'message': f'No work recorded for Lyell project on {target_date}',
                'total_hours': 0,
                'employee_count': 0,
                'employees': []
            }
        
        # Group by employee
        daily_summary = []
        employee_groups = lyell_data.groupby('email')
        
        for email, group in employee_groups:
            employee_name = self._get_employee_name(email)
            total_hours = group['Hours'].sum()
            tasks = group['Tasks_Completed'].dropna().tolist()
            
            # Category breakdown with extra hours - FIXED: group by category first
            category_actual = {}
            category_billable = {}
            category_extra = {}
            total_extra = 0
            
            # Group by category to get accurate breakdown
            for category, cat_group in group.groupby('category'):
                cat_hours = cat_group['Hours'].sum()
                category_actual[category] = round(cat_hours, 2)
                category_billable[category] = self._get_billable_hours(cat_hours, category)
                category_extra[category] = self._calculate_extra_hours(cat_hours, category)
                total_extra += category_extra[category]
            
            daily_summary.append({
                'employee_name': employee_name,
                'employee_email': email,
                'total_hours': round(total_hours, 2),
                'total_extra_hours': round(total_extra, 2),
                'task_count': len(tasks),
                'tasks': tasks[:10],  # Limit to 10 tasks
                'category_breakdown': {
                    'actual_hours': category_actual,
                    'billable_hours': category_billable,
                    'extra_hours': category_extra
                },
                'sow_compliance': self._check_daily_sow_compliance(group),
                'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
            })
        
        # Sort by hours (descending)
        daily_summary.sort(key=lambda x: x['total_hours'], reverse=True)
        
        total_hours = sum(emp['total_hours'] for emp in daily_summary)
        total_extra_hours = sum(emp['total_extra_hours'] for emp in daily_summary)
        
        return {
            'date': target_date.isoformat(),
            'day_of_week': target_date.strftime('%A'),
            'status': 'ANALYZED',
            'total_hours': round(total_hours, 2),
            'total_extra_hours': round(total_extra_hours, 2),
            'employee_count': len(daily_summary),
            'employees': daily_summary,
            'category_summary': self._aggregate_categories(daily_summary),
            'has_sow_violations': any(emp.get('sow_compliance', {}).get('has_violations', False) 
                                    for emp in daily_summary),
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    def get_lyell_monthly_performance(self,
                                    year: int,
                                    month: int) -> Dict:
        """
        🔹 Which employees worked on Lyell in specific month?
        
        Args:
            year: Year to analyze
            month: Month to analyze (1-12)
            
        Returns:
            Monthly performance summary
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        print(f"Analyzing Lyell performance for {year}-{month:02d}")
        
        # Get performance for the month
        performance = self.get_lyell_employee_performance(start_date, end_date)
        
        # Get daily activity pattern
        lyell_data = self._filter_lyell_data(start_date, end_date)
        
        daily_pattern = {}
        if not lyell_data.empty:
            for day_date, day_group in lyell_data.groupby('clean_date'):
                date_key = day_date.date().isoformat()
                daily_hours = day_group['Hours'].sum()
                employee_names = [self._get_employee_name(email) 
                                for email in day_group['email'].unique()]
                
                daily_pattern[date_key] = {
                    'total_hours': round(daily_hours, 2),
                    'employee_count': len(employee_names),
                    'employees': employee_names[:5]  # Limit to 5
                }
        
        # Convert to list and sort
        daily_pattern_list = [
            {'date': date_key, **data}
            for date_key, data in daily_pattern.items()
        ]
        daily_pattern_list.sort(key=lambda x: x['date'])
        
        total_extra_hours = sum(emp['total_extra_hours'] for emp in performance)
        
        return {
            'year': year,
            'month': month,
            'month_name': start_date.strftime('%B'),
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_employees': len(performance),
            'total_hours': sum(emp['total_hours_on_lyell'] for emp in performance),
            'total_extra_hours': round(total_extra_hours, 2),
            'employee_performance': performance,
            'daily_activity': daily_pattern_list,
            'top_contributors': sorted(performance, 
                                     key=lambda x: x['total_hours_on_lyell'], 
                                     reverse=True)[:5],
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    # ==================== CATEGORY / TASK-LEVEL QUERIES ====================
    
    def get_category_performance(self,
                               category: str,
                               start_date: Optional[date] = None,
                               end_date: Optional[date] = None) -> Dict:
        """
        🔹 How many hours were spent on specific category for Lyell?
        
        Args:
            category: Category to analyze (etl, reporting, testing, development, architect, other)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Category performance summary with extra hours breakdown
        """
        print(f"Analyzing {category} category performance for Lyell")
        
        # Get Lyell data
        lyell_data = self._filter_lyell_data(start_date, end_date)
        
        if lyell_data.empty:
            return {
                'category': category,
                'status': 'NO_DATA',
                'total_hours': 0,
                'employee_count': 0,
                'employees': []
            }
        
        # Filter by category
        category_data = lyell_data[lyell_data['category'] == category]
        
        if category_data.empty:
            return {
                'category': category,
                'status': 'NO_DATA',
                'message': f'No {category} work found in the specified date range',
                'total_hours': 0,
                'employee_count': 0,
                'employees': []
            }
        
        # Group by employee
        employee_performance = []
        employee_groups = category_data.groupby('email')
        
        for email, group in employee_groups:
            employee_name = self._get_employee_name(email)
            
            # Calculate daily hours to get accurate extra hours
            daily_hours = group.groupby('clean_date')['Hours'].sum()
            
            total_actual_hours = 0
            total_billable_hours = 0
            total_extra_hours = 0
            
            for day_date, day_hours in daily_hours.items():
                total_actual_hours += day_hours
                total_billable_hours += self._get_billable_hours(day_hours, category)
                total_extra_hours += self._calculate_extra_hours(day_hours, category)
            
            total_days = group['clean_date'].dt.date.nunique()
            
            # Get tasks for this category
            tasks = group['Tasks_Completed'].dropna().unique().tolist()
            
            employee_performance.append({
                'employee_name': employee_name,
                'employee_email': email,
                'total_actual_hours': round(total_actual_hours, 2),
                'total_billable_hours': round(total_billable_hours, 2),
                'total_extra_hours': round(total_extra_hours, 2),
                'total_days': total_days,
                'avg_hours_per_day': round(total_actual_hours / total_days, 2) if total_days > 0 else 0,
                'task_count': len(tasks),
                'sample_tasks': tasks[:5],  # Limit to 5 sample tasks
                'has_extra_hours': total_extra_hours > 0,
                'category_cap': self.LYELL_SOW_RULES[category]['max_hours_per_day']
            })
        
        # Sort by hours (descending)
        employee_performance.sort(key=lambda x: x['total_actual_hours'], reverse=True)
        
        total_actual_hours = sum(emp['total_actual_hours'] for emp in employee_performance)
        total_extra_hours = sum(emp['total_extra_hours'] for emp in employee_performance)
        
        # Compare with other categories
        all_categories = lyell_data.groupby('category').agg({
            'Hours': 'sum'
        }).to_dict()['Hours']
        
        category_percentage = (total_actual_hours / sum(all_categories.values())) * 100 if sum(all_categories.values()) > 0 else 0
        
        return {
            'category': category,
            'category_label': category.title(),
            'status': 'ANALYZED',
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'total_actual_hours': round(total_actual_hours, 2),
            'total_extra_hours': round(total_extra_hours, 2),
            'employee_count': len(employee_performance),
            'category_percentage': round(category_percentage, 1),
            'employees': employee_performance,
            'top_contributor': employee_performance[0] if employee_performance else None,
            'category_comparison': {
                cat: round(hours, 2)
                for cat, hours in all_categories.items()
            },
            'category_cap': self.LYELL_SOW_RULES[category]['max_hours_per_day'],
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    def get_employee_category_breakdown(self,
                                      employee_name: str,
                                      start_date: Optional[date] = None,
                                      end_date: Optional[date] = None) -> Dict:
        """
        🔹 Show task category–wise breakdown per employee for Lyell
        
        Args:
            employee_name: Employee name (partial match)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Employee category breakdown with extra hours
        """
        # Find employee email
        employee_email = self._find_employee_by_name(employee_name)
        
        if not employee_email:
            return {
                'employee_name': employee_name,
                'status': 'NOT_FOUND',
                'message': f'Employee "{employee_name}" not found'
            }
        
        # Get Lyell data for this employee
        lyell_data = self._filter_lyell_data(start_date, end_date)
        employee_data = lyell_data[lyell_data['email'] == employee_email.lower().strip()]
        
        if employee_data.empty:
            actual_name = self._get_employee_name(employee_email)
            return {
                'employee_name': actual_name,
                'employee_email': employee_email,
                'status': 'NO_DATA',
                'message': f'No Lyell work found for {actual_name} in the specified date range'
            }
        
        # Group by category
        category_breakdown = []
        category_groups = employee_data.groupby('category')
        
        for category, group in category_groups:
            # Calculate daily hours for accurate extra hours
            daily_hours = group.groupby('clean_date')['Hours'].sum()
            
            total_actual_hours = 0
            total_billable_hours = 0
            total_extra_hours = 0
            
            for day_date, day_hours in daily_hours.items():
                total_actual_hours += day_hours
                total_billable_hours += self._get_billable_hours(day_hours, category)
                total_extra_hours += self._calculate_extra_hours(day_hours, category)
            
            total_days = group['clean_date'].dt.date.nunique()
            tasks = group['Tasks_Completed'].dropna().unique().tolist()
            
            # Daily pattern for this category
            daily_pattern = group.groupby('clean_date').agg({
                'Hours': 'sum'
            }).reset_index()
            
            daily_hours_list = []
            for _, row in daily_pattern.iterrows():
                day_hours = float(row['Hours'])
                daily_hours_list.append({
                    'date': row['clean_date'].date().isoformat(),
                    'actual_hours': round(day_hours, 2),
                    'billable_hours': self._get_billable_hours(day_hours, category),
                    'extra_hours': self._calculate_extra_hours(day_hours, category)
                })
            
            category_breakdown.append({
                'category': category,
                'category_label': category.title(),
                'total_actual_hours': round(total_actual_hours, 2),
                'total_billable_hours': round(total_billable_hours, 2),
                'total_extra_hours': round(total_extra_hours, 2),
                'total_days': total_days,
                'avg_hours_per_day': round(total_actual_hours / total_days, 2) if total_days > 0 else 0,
                'task_count': len(tasks),
                'sample_tasks': tasks[:3],  # Limit to 3 sample tasks
                'daily_pattern': sorted(daily_hours_list, key=lambda x: x['date']),
                'category_cap': self.LYELL_SOW_RULES[category]['max_hours_per_day']
            })
        
        # Sort by hours (descending)
        category_breakdown.sort(key=lambda x: x['total_actual_hours'], reverse=True)
        
        total_hours = employee_data['Hours'].sum()
        total_extra_hours = sum(cat['total_extra_hours'] for cat in category_breakdown)
        
        # Calculate percentages
        for category in category_breakdown:
            category['percentage'] = round((category['total_actual_hours'] / total_hours) * 100, 1) if total_hours > 0 else 0
        
        actual_name = self._get_employee_name(employee_email)
        
        return {
            'employee_name': actual_name,
            'employee_email': employee_email,
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'total_hours_on_lyell': round(total_hours, 2),
            'total_extra_hours': round(total_extra_hours, 2),
            'total_days_on_lyell': employee_data['clean_date'].dt.date.nunique(),
            'category_breakdown': category_breakdown,
            'primary_category': category_breakdown[0]['category'] if category_breakdown else None,
            'category_diversity': len(category_breakdown),
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    # ==================== COMPLIANCE / ANOMALY QUERIES ====================
    
    def get_sow_compliance_report(self,
                                start_date: Optional[date] = None,
                                end_date: Optional[date] = None) -> Dict:
        """
        🔹 Identify potential SOW violations for Lyell
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            SOW compliance report with extra hours details
        """
        print(f"Checking SOW compliance for Lyell from {start_date} to {end_date}")
        
        # Get Lyell data
        lyell_data = self._filter_lyell_data(start_date, end_date)
        
        if lyell_data.empty:
            return {
                'status': 'NO_DATA',
                'message': 'No Lyell data found in the specified date range',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'employees_with_violations': 0,
                    'total_extra_hours': 0
                }
            }
        
        # Check compliance for each day
        violations = []
        daily_compliance = {}
        
        for day_date, day_group in lyell_data.groupby('clean_date'):
            date_key = day_date.date()
            daily_violations = []
            
            # Check each employee's work for the day
            for email, emp_group in day_group.groupby('email'):
                employee_name = self._get_employee_name(email)
                
                # Check category-wise compliance - FIXED: group by category first
                for category, cat_group in emp_group.groupby('category'):
                    category_hours = cat_group['Hours'].sum()
                    extra_hours = self._calculate_extra_hours(category_hours, category)
                    
                    if extra_hours > 0:
                        max_allowed = self.LYELL_SOW_RULES[category]['max_hours_per_day']
                        
                        violation = {
                            'date': date_key.isoformat(),
                            'employee_name': employee_name,
                            'employee_email': email,
                            'category': category,
                            'actual_hours': round(category_hours, 2),
                            'max_allowed': max_allowed,
                            'extra_hours': extra_hours,
                            'tasks': cat_group['Tasks_Completed'].dropna().unique().tolist()[:3]
                        }
                        
                        daily_violations.append(violation)
            
            if daily_violations:
                daily_compliance[date_key.isoformat()] = {
                    'violation_count': len(daily_violations),
                    'total_extra_hours': sum(v['extra_hours'] for v in daily_violations)
                }
                violations.extend(daily_violations)
        
        # Group violations by employee
        employee_violations = {}
        for violation in violations:
            emp_key = violation['employee_email']
            if emp_key not in employee_violations:
                employee_violations[emp_key] = {
                    'employee_name': violation['employee_name'],
                    'violations': [],
                    'total_extra_hours': 0
                }
            
            employee_violations[emp_key]['violations'].append(violation)
            employee_violations[emp_key]['total_extra_hours'] += violation['extra_hours']
        
        # Convert to list
        employee_violations_list = [
            {
                'employee_name': data['employee_name'],
                'employee_email': emp_key,
                'violation_count': len(data['violations']),
                'total_extra_hours': round(data['total_extra_hours'], 2),
                'sample_violations': data['violations'][:3]  # Limit to 3
            }
            for emp_key, data in employee_violations.items()
        ]
        
        # Sort by violation count (descending)
        employee_violations_list.sort(key=lambda x: x['violation_count'], reverse=True)
        
        total_extra_hours = sum(v['extra_hours'] for v in violations)
        
        return {
            'status': 'ANALYZED',
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'violations': violations[:50],  # Limit to 50 violations
            'employee_violations': employee_violations_list,
            'daily_compliance': daily_compliance,
            'summary': {
                'total_violations': len(violations),
                'employees_with_violations': len(employee_violations),
                'total_extra_hours': round(total_extra_hours, 2),
                'affected_categories': list(set(v['category'] for v in violations)),
                'most_violating_day': max(daily_compliance.items(), 
                                        key=lambda x: x[1]['violation_count'])[0] if daily_compliance else None
            },
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    def get_overtime_report(self,
                          hour_threshold: float = 8.0,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> Dict:
        """
        🔹 Which employees logged more than X hours in a single day for Lyell?
        
        Note: This is OVERTIME detection (8+ hours), NOT extra hours (which is 4+ for ETL/Reporting)
        
        Args:
            hour_threshold: Hour threshold for overtime (default: 8)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Overtime report (separate from extra hours)
        """
        print(f"Checking overtime (> {hour_threshold} hours) for Lyell")
        
        # Get Lyell data
        lyell_data = self._filter_lyell_data(start_date, end_date)
        
        if lyell_data.empty:
            return {
                'status': 'NO_DATA',
                'hour_threshold': hour_threshold,
                'overtime_instances': [],
                'summary': {
                    'total_instances': 0,
                    'employees_with_overtime': 0,
                    'total_overtime_hours': 0
                }
            }
        
        # Calculate daily hours per employee
        daily_hours = lyell_data.groupby(['clean_date', 'email']).agg({
            'Hours': 'sum'
        }).reset_index()
        
        # Find overtime instances
        overtime_instances = []
        
        for _, row in daily_hours.iterrows():
            if row['Hours'] > hour_threshold:
                employee_name = self._get_employee_name(row['email'])
                overtime_hours = row['Hours'] - hour_threshold
                
                # Get tasks for this day
                day_tasks = lyell_data[
                    (lyell_data['clean_date'] == row['clean_date']) &
                    (lyell_data['email'] == row['email'])
                ]['Tasks_Completed'].dropna().unique().tolist()
                
                overtime_instances.append({
                    'date': row['clean_date'].date().isoformat(),
                    'day_of_week': row['clean_date'].strftime('%A'),
                    'employee_name': employee_name,
                    'employee_email': row['email'],
                    'total_hours': round(row['Hours'], 2),
                    'threshold': hour_threshold,
                    'overtime_hours': round(overtime_hours, 2),
                    'tasks': day_tasks[:3]  # Limit to 3 tasks
                })
        
        # Group by employee
        employee_overtime = {}
        for instance in overtime_instances:
            emp_key = instance['employee_email']
            if emp_key not in employee_overtime:
                employee_overtime[emp_key] = {
                    'employee_name': instance['employee_name'],
                    'instances': [],
                    'total_overtime_hours': 0
                }
            
            employee_overtime[emp_key]['instances'].append(instance)
            employee_overtime[emp_key]['total_overtime_hours'] += instance['overtime_hours']
        
        # Convert to list
        employee_overtime_list = [
            {
                'employee_name': data['employee_name'],
                'employee_email': emp_key,
                'instance_count': len(data['instances']),
                'total_overtime_hours': round(data['total_overtime_hours'], 2),
                'avg_overtime_per_instance': round(data['total_overtime_hours'] / len(data['instances']), 2) 
                if data['instances'] else 0,
                'sample_instances': data['instances'][:2]  # Limit to 2
            }
            for emp_key, data in employee_overtime.items()
        ]
        
        # Sort by instance count (descending)
        employee_overtime_list.sort(key=lambda x: x['instance_count'], reverse=True)
        
        total_overtime_hours = sum(instance['overtime_hours'] for instance in overtime_instances)
        
        return {
            'status': 'ANALYZED',
            'hour_threshold': hour_threshold,
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'overtime_instances': overtime_instances[:50],  # Limit to 50
            'employee_overtime': employee_overtime_list,
            'summary': {
                'total_instances': len(overtime_instances),
                'employees_with_overtime': len(employee_overtime),
                'total_overtime_hours': round(total_overtime_hours, 2),
                'avg_overtime_per_instance': round(total_overtime_hours / len(overtime_instances), 2) 
                if overtime_instances else 0,
                'most_overtime_employee': employee_overtime_list[0]['employee_name'] if employee_overtime_list else None
            },
            'note': f'This is overtime detection (>{hour_threshold}h), separate from extra hours (4h cap for ETL/Reporting)'
        }
    
    # ==================== COMPARISON QUERIES ====================
    
    def compare_employees(self,
                        employee1_name: str,
                        employee2_name: str,
                        start_date: Optional[date] = None,
                        end_date: Optional[date] = None) -> Dict:
        """
        🔹 Compare two employees' performance on Lyell
        
        Args:
            employee1_name: First employee name
            employee2_name: Second employee name
            start_date: Start date for comparison
            end_date: End date for comparison
            
        Returns:
            Comparison report with extra hours
        """
        # Find employee emails
        employee1_email = self._find_employee_by_name(employee1_name)
        employee2_email = self._find_employee_by_name(employee2_name)
        
        if not employee1_email:
            return {
                'status': 'ERROR',
                'message': f'Employee "{employee1_name}" not found'
            }
        
        if not employee2_email:
            return {
                'status': 'ERROR',
                'message': f'Employee "{employee2_name}" not found'
            }
        
        # Get Lyell data
        lyell_data = self._filter_lyell_data(start_date, end_date)
        
        # Get data for each employee
        emp1_data = lyell_data[lyell_data['email'] == employee1_email.lower().strip()]
        emp2_data = lyell_data[lyell_data['email'] == employee2_email.lower().strip()]
        
        # Get employee names
        emp1_name = self._get_employee_name(employee1_email)
        emp2_name = self._get_employee_name(employee2_email)
        
        # Calculate metrics for employee 1
        emp1_metrics = self._calculate_employee_metrics(emp1_data, emp1_name, employee1_email)
        emp2_metrics = self._calculate_employee_metrics(emp2_data, emp2_name, employee2_email)
        
        # Calculate differences
        differences = {}
        for key in ['total_hours', 'total_extra_hours', 'total_days', 'avg_hours_per_day', 'task_count']:
            if key in emp1_metrics and key in emp2_metrics:
                diff = emp1_metrics[key] - emp2_metrics[key]
                differences[key] = {
                    'difference': round(diff, 2),
                    'percentage_difference': round((diff / emp2_metrics[key]) * 100, 1) if emp2_metrics[key] > 0 else 0
                }
        
        # Category comparison
        category_comparison = []
        all_categories = set(emp1_metrics.get('category_breakdown', {}).keys()) | \
                        set(emp2_metrics.get('category_breakdown', {}).keys())
        
        for category in all_categories:
            emp1_hours = emp1_metrics.get('category_breakdown', {}).get(category, 0)
            emp2_hours = emp2_metrics.get('category_breakdown', {}).get(category, 0)
            emp1_extra = emp1_metrics.get('category_extra_hours', {}).get(category, 0)
            emp2_extra = emp2_metrics.get('category_extra_hours', {}).get(category, 0)
            
            category_comparison.append({
                'category': category,
                'employee1_hours': emp1_hours,
                'employee2_hours': emp2_hours,
                'employee1_extra_hours': emp1_extra,
                'employee2_extra_hours': emp2_extra,
                'difference': round(emp1_hours - emp2_hours, 2),
                'employee1_percentage': round((emp1_hours / emp1_metrics['total_hours']) * 100, 1) 
                if emp1_metrics['total_hours'] > 0 else 0,
                'employee2_percentage': round((emp2_hours / emp2_metrics['total_hours']) * 100, 1) 
                if emp2_metrics['total_hours'] > 0 else 0
            })
        
        # Sort by difference (absolute value)
        category_comparison.sort(key=lambda x: abs(x['difference']), reverse=True)
        
        # Determine who contributed more
        if emp1_metrics['total_hours'] > emp2_metrics['total_hours']:
            higher_contributor = emp1_name
            hour_difference = emp1_metrics['total_hours'] - emp2_metrics['total_hours']
        else:
            higher_contributor = emp2_name
            hour_difference = emp2_metrics['total_hours'] - emp1_metrics['total_hours']
        
        return {
            'status': 'COMPARED',
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'employee1': emp1_metrics,
            'employee2': emp2_metrics,
            'differences': differences,
            'category_comparison': category_comparison,
            'summary': {
                'higher_contributor': higher_contributor,
                'hour_difference': round(hour_difference, 2),
                'total_hours_both': round(emp1_metrics['total_hours'] + emp2_metrics['total_hours'], 2),
                'total_extra_hours_both': round(emp1_metrics['total_extra_hours'] + emp2_metrics['total_extra_hours'], 2),
                'combined_percentage': round(((emp1_metrics['total_hours'] + emp2_metrics['total_hours']) / 
                                          lyell_data['Hours'].sum()) * 100, 1) if not lyell_data.empty else 0
            },
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    def get_top_contributors(self,
                           top_n: int = 5,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> Dict:
        """
        🔹 Who are the top contributors for the Lyell project?
        
        Args:
            top_n: Number of top contributors to return
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Top contributors report with extra hours
        """
        # Get all employee performance
        performance = self.get_lyell_employee_performance(start_date, end_date)
        
        if not performance:
            return {
                'status': 'NO_DATA',
                'top_contributors': [],
                'summary': {
                    'total_employees': 0,
                    'total_hours': 0
                }
            }
        
        # Take top N
        top_contributors = performance[:top_n]
        
        # Calculate summary statistics
        total_hours_all = sum(emp['total_hours_on_lyell'] for emp in performance)
        total_extra_hours_all = sum(emp['total_extra_hours'] for emp in performance)
        top_hours = sum(emp['total_hours_on_lyell'] for emp in top_contributors)
        top_extra_hours = sum(emp['total_extra_hours'] for emp in top_contributors)
        
        return {
            'status': 'ANALYZED',
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'top_n': top_n,
            'top_contributors': top_contributors,
            'summary': {
                'total_employees': len(performance),
                'total_hours': round(total_hours_all, 2),
                'total_extra_hours': round(total_extra_hours_all, 2),
                'top_contributors_hours': round(top_hours, 2),
                'top_contributors_extra_hours': round(top_extra_hours, 2),
                'top_percentage': round((top_hours / total_hours_all) * 100, 1) if total_hours_all > 0 else 0,
                'avg_hours_top': round(top_hours / len(top_contributors), 2) if top_contributors else 0,
                'avg_hours_all': round(total_hours_all / len(performance), 2) if performance else 0
            },
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    # ==================== HELPER METHODS ====================
    
    def _calculate_employee_metrics(self, 
                                  employee_data: pd.DataFrame,
                                  employee_name: str,
                                  employee_email: str) -> Dict:
        """Calculate comprehensive metrics for an employee with extra hours"""
        if employee_data.empty:
            return {
                'employee_name': employee_name,
                'employee_email': employee_email,
                'total_hours': 0,
                'total_extra_hours': 0,
                'total_days': 0,
                'avg_hours_per_day': 0,
                'task_count': 0,
                'category_breakdown': {},
                'category_extra_hours': {},
                'status': 'NO_DATA'
            }
        
        total_hours = employee_data['Hours'].sum()
        total_days = employee_data['clean_date'].dt.date.nunique()
        
        # Category breakdown with extra hours - FIXED: group by category first
        category_hours = {}
        category_extra_hours = {}
        
        for category, cat_group in employee_data.groupby('category'):
            # Calculate daily hours for accurate extra hours
            daily_cat_hours = cat_group.groupby('clean_date')['Hours'].sum()
            
            cat_total_hours = 0
            cat_total_extra = 0
            
            for day_date, day_hours in daily_cat_hours.items():
                cat_total_hours += day_hours
                cat_total_extra += self._calculate_extra_hours(day_hours, category)
            
            category_hours[category] = round(cat_total_hours, 2)
            category_extra_hours[category] = round(cat_total_extra, 2)
        
        total_extra_hours = sum(category_extra_hours.values())
        
        # Task count
        task_count = employee_data['task_count'].sum()
        
        # Daily pattern
        daily_pattern = employee_data.groupby('clean_date').agg({
            'Hours': 'sum'
        }).reset_index()
        
        daily_hours = []
        for _, row in daily_pattern.iterrows():
            daily_hours.append({
                'date': row['clean_date'].date().isoformat(),
                'hours': round(float(row['Hours']), 2),
                'day_of_week': row['clean_date'].strftime('%A')
            })
        
        return {
            'employee_name': employee_name,
            'employee_email': employee_email,
            'total_hours': round(total_hours, 2),
            'total_extra_hours': round(total_extra_hours, 2),
            'total_days': total_days,
            'avg_hours_per_day': round(total_hours / total_days, 2) if total_days > 0 else 0,
            'task_count': int(task_count),
            'avg_tasks_per_day': round(task_count / total_days, 2) if total_days > 0 else 0,
            'category_breakdown': category_hours,
            'category_extra_hours': category_extra_hours,
            'daily_pattern': sorted(daily_hours, key=lambda x: x['date']),
            'date_range': {
                'first_date': employee_data['clean_date'].min().date().isoformat(),
                'last_date': employee_data['clean_date'].max().date().isoformat()
            },
            'status': 'ANALYZED',
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    def _check_daily_sow_compliance(self, daily_data: pd.DataFrame) -> Dict:
        """Check SOW compliance for a day's work"""
        violations = []
        
        # Group by category - FIXED: ensure proper grouping
        for category, group in daily_data.groupby('category'):
            category_hours = group['Hours'].sum()
            extra_hours = self._calculate_extra_hours(category_hours, category)
            
            if extra_hours > 0:
                max_allowed = self.LYELL_SOW_RULES[category]['max_hours_per_day']
                
                violations.append({
                    'category': category,
                    'actual_hours': round(category_hours, 2),
                    'max_allowed': max_allowed,
                    'extra_hours': extra_hours
                })
        
        total_extra_hours = sum(v['extra_hours'] for v in violations)
        
        return {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'total_extra_hours': round(total_extra_hours, 2),
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    def _aggregate_categories(self, employee_list: List[Dict]) -> Dict:
        """Aggregate category hours from employee list"""
        category_totals = {}
        
        for employee in employee_list:
            category_breakdown = employee.get('category_breakdown', {})
            
            # Handle both old format (dict of hours) and new format (dict with actual_hours)
            if isinstance(category_breakdown, dict):
                if 'actual_hours' in category_breakdown:
                    # New format
                    for category, hours in category_breakdown.get('actual_hours', {}).items():
                        category_totals[category] = category_totals.get(category, 0) + hours
                else:
                    # Old format
                    for category, hours in category_breakdown.items():
                        category_totals[category] = category_totals.get(category, 0) + hours
        
        return category_totals
    
    # ==================== MULTI-PROJECT ANALYSIS ====================
    
    def get_multi_project_employees(self,
                                  start_date: Optional[date] = None,
                                  end_date: Optional[date] = None) -> Dict:
        """
        🔹 Identify employees handling multiple projects
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Multi-project employee report
        """
        if self.base.work_df.empty:
            return {
                'status': 'NO_DATA',
                'multi_project_employees': [],
                'summary': {
                    'total_employees': 0,
                    'multi_project_count': 0
                }
            }
        
        # Filter by date if provided
        work_data = self.base.work_df.copy()
        if start_date:
            work_data = work_data[work_data['clean_date'].dt.date >= start_date]
        if end_date:
            work_data = work_data[work_data['clean_date'].dt.date <= end_date]
        
        # Get unique projects per employee
        employee_projects = {}
        
        for email, group in work_data.groupby('email'):
            employee_name = self._get_employee_name(email)
            projects = group['project_normalized'].dropna().unique().tolist()
            projects = [p for p in projects if p]  # Remove empty strings
            
            if len(projects) > 1:
                # Calculate hours per project
                project_hours = {}
                for project, proj_group in group.groupby('project_normalized'):
                    if project:  # Skip empty
                        project_hours[project] = round(proj_group['Hours'].sum(), 2)
                
                employee_projects[email] = {
                    'employee_name': employee_name,
                    'email': email,
                    'projects': projects,
                    'project_count': len(projects),
                    'project_hours': project_hours,
                    'total_hours': round(group['Hours'].sum(), 2),
                    'primary_project': max(project_hours.items(), key=lambda x: x[1])[0] 
                    if project_hours else None
                }
        
        # Convert to list and sort by project count
        multi_project_list = list(employee_projects.values())
        multi_project_list.sort(key=lambda x: x['project_count'], reverse=True)
        
        # Check specifically for Lyell + other projects
        lyell_multi = []
        for emp in multi_project_list:
            if 'lyell' in emp['projects']:
                other_projects = [p for p in emp['projects'] if p != 'lyell']
                lyell_hours = emp['project_hours'].get('lyell', 0)
                other_hours = sum(hours for proj, hours in emp['project_hours'].items() 
                                if proj != 'lyell')
                
                lyell_multi.append({
                    'employee_name': emp['employee_name'],
                    'email': emp['email'],
                    'lyell_hours': lyell_hours,
                    'other_projects': other_projects,
                    'other_hours': other_hours,
                    'lyell_percentage': round((lyell_hours / emp['total_hours']) * 100, 1) 
                    if emp['total_hours'] > 0 else 0
                })
        
        # Sort Lyell multi by Lyell hours
        lyell_multi.sort(key=lambda x: x['lyell_hours'], reverse=True)
        
        return {
            'status': 'ANALYZED',
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'multi_project_employees': multi_project_list,
            'lyell_multi_project_employees': lyell_multi,
            'summary': {
                'total_multi_project': len(multi_project_list),
                'total_lyell_multi': len(lyell_multi),
                'avg_projects_per_multi': round(sum(emp['project_count'] for emp in multi_project_list) / 
                                              len(multi_project_list), 1) if multi_project_list else 0,
                'most_projects': multi_project_list[0]['employee_name'] if multi_project_list else None,
                'highest_lyell_multi': lyell_multi[0]['employee_name'] if lyell_multi else None
            }
        }
    
    # ==================== COMPREHENSIVE SUMMARY ====================
    
    def get_lyell_comprehensive_summary(self,
                                      timeframe: str = 'last_7_days') -> Dict:
        """
        Get comprehensive summary of Lyell project including all analysis types
        
        Args:
            timeframe: 'today', 'yesterday', 'last_7_days', 'last_30_days', 'last_quarter', 'all_time'
            
        Returns:
            Comprehensive summary with extra hours
        """
        current_date = date.today()
        start_date = None
        end_date = current_date
        
        if timeframe == 'today':
            start_date = current_date
        elif timeframe == 'yesterday':
            start_date = current_date - timedelta(days=1)
            end_date = start_date
        elif timeframe == 'last_7_days':
            start_date = current_date - timedelta(days=6)  # 7 days INCLUDING today
        elif timeframe == 'last_30_days':
            start_date = current_date - timedelta(days=29)  # 30 days INCLUDING today
        elif timeframe == 'last_quarter':
            start_date = current_date - timedelta(days=89)  # 90 days INCLUDING today
        # 'all_time' uses no start_date filter
        
        print(f"Generating comprehensive Lyell summary for {timeframe}")
        
        # Get all analyses
        performance = self.get_lyell_employee_performance(start_date, end_date)
        top_contributors = self.get_top_contributors(5, start_date, end_date)
        sow_compliance = self.get_sow_compliance_report(start_date, end_date)
        overtime_report = self.get_overtime_report(8.0, start_date, end_date)
        multi_project = self.get_multi_project_employees(start_date, end_date)
        
        # Get category breakdown
        category_summary = {}
        if performance:
            # Aggregate all categories
            for emp in performance:
                category_breakdown = emp.get('category_breakdown', {})
                
                # Handle both old and new format
                if isinstance(category_breakdown, dict):
                    if 'actual_hours' in category_breakdown:
                        # New format
                        for category, hours in category_breakdown.get('actual_hours', {}).items():
                            category_summary[category] = category_summary.get(category, 0) + hours
                    else:
                        # Old format
                        for category, hours in category_breakdown.items():
                            category_summary[category] = category_summary.get(category, 0) + hours
        
        # Calculate consistency metrics
        consistency_metrics = []
        for emp in performance[:10]:  # Top 10 by hours
            if emp['total_days_on_lyell'] > 0:
                date_range_days = (end_date - start_date).days + 1 if start_date else 365  # Approximate
                consistency = (emp['total_days_on_lyell'] / date_range_days) * 100
                
                consistency_metrics.append({
                    'employee_name': emp['employee_name'],
                    'days_worked': emp['total_days_on_lyell'],
                    'total_days': date_range_days,
                    'consistency_percentage': round(consistency, 1),
                    'avg_hours_per_work_day': emp['avg_hours_per_day']
                })
        
        # Sort by consistency
        consistency_metrics.sort(key=lambda x: x['consistency_percentage'], reverse=True)
        
        return {
            'timeframe': timeframe,
            'date_range': {
                'start_date': start_date.isoformat() if start_date else 'All time',
                'end_date': end_date.isoformat(),
                'current_date': current_date.isoformat()
            },
            'performance_summary': {
                'total_employees': len(performance),
                'total_hours': sum(emp['total_hours_on_lyell'] for emp in performance),
                'total_extra_hours': sum(emp['total_extra_hours'] for emp in performance),
                'total_days': sum(emp['total_days_on_lyell'] for emp in performance),
                'avg_hours_per_employee': round(
                    sum(emp['total_hours_on_lyell'] for emp in performance) / len(performance), 2
                ) if performance else 0
            },
            'top_contributors': top_contributors.get('top_contributors', []),
            'sow_compliance': {
                'has_violations': sow_compliance.get('summary', {}).get('total_violations', 0) > 0,
                'total_violations': sow_compliance.get('summary', {}).get('total_violations', 0),
                'total_extra_hours': sow_compliance.get('summary', {}).get('total_extra_hours', 0)
            },
            'overtime_analysis': {
                'total_overtime_instances': overtime_report.get('summary', {}).get('total_instances', 0),
                'employees_with_overtime': overtime_report.get('summary', {}).get('employees_with_overtime', 0),
                'total_overtime_hours': overtime_report.get('summary', {}).get('total_overtime_hours', 0)
            },
            'category_breakdown': {
                cat: round(hours, 2)
                for cat, hours in category_summary.items()
            },
            'consistency_analysis': consistency_metrics[:5],  # Top 5 most consistent
            'multi_project_analysis': {
                'total_multi_project': multi_project.get('summary', {}).get('total_multi_project', 0),
                'lyell_multi_project': multi_project.get('summary', {}).get('total_lyell_multi', 0)
            },
            'key_insights': self._generate_key_insights(
                performance, 
                top_contributors, 
                sow_compliance, 
                overtime_report
            ),
            'timestamp': datetime.now().isoformat(),
            'lyell_daily_cap': self.LYELL_DAILY_CAP_PER_EMPLOYEE
        }
    
    def _generate_key_insights(self, 
                             performance: List[Dict],
                             top_contributors: Dict,
                             sow_compliance: Dict,
                             overtime_report: Dict) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        if not performance:
            return ["No Lyell project data available for analysis"]
        
        # 1. Top contributor insight
        if top_contributors.get('top_contributors'):
            top_emp = top_contributors['top_contributors'][0]
            insights.append(
                f"Top contributor: {top_emp['employee_name']} with {top_emp['total_hours_on_lyell']} hours "
                f"({top_emp.get('contribution_percentage', 0)}% of total Lyell hours), "
                f"{top_emp.get('total_extra_hours', 0)} extra hours"
            )
        
        # 2. SOW compliance insight
        violations = sow_compliance.get('summary', {}).get('total_violations', 0)
        extra_hours = sow_compliance.get('summary', {}).get('total_extra_hours', 0)
        
        if violations > 0:
            insights.append(
                f"SOW compliance: {violations} violations detected with "
                f"{extra_hours} extra hours beyond the {self.LYELL_DAILY_CAP_PER_EMPLOYEE}h daily cap for ETL/Reporting"
            )
        else:
            insights.append("SOW compliance: No violations detected - all work within daily caps")
        
        # 3. Overtime insight
        overtime_instances = overtime_report.get('summary', {}).get('total_instances', 0)
        if overtime_instances > 0:
            insights.append(
                f"Overtime: {overtime_instances} instances of >8 hour days with "
                f"{overtime_report['summary'].get('total_overtime_hours', 0)} total overtime hours"
            )
        
        # 4. Employee distribution insight
        if len(performance) > 0:
            total_hours = sum(emp['total_hours_on_lyell'] for emp in performance)
            if top_contributors.get('top_contributors'):
                top_hours = sum(emp['total_hours_on_lyell'] 
                              for emp in top_contributors['top_contributors'][:3])
                top_percentage = (top_hours / total_hours) * 100 if total_hours > 0 else 0
                insights.append(
                    f"Work distribution: Top 3 employees account for {top_percentage:.1f}% of total Lyell hours"
                )
        
        # 5. Category distribution insight
        category_hours = {}
        for emp in performance:
            category_breakdown = emp.get('category_breakdown', {})
            
            # Handle both old and new format
            if isinstance(category_breakdown, dict):
                if 'actual_hours' in category_breakdown:
                    # New format
                    for category, hours in category_breakdown.get('actual_hours', {}).items():
                        category_hours[category] = category_hours.get(category, 0) + hours
                else:
                    # Old format
                    for category, hours in category_breakdown.items():
                        category_hours[category] = category_hours.get(category, 0) + hours
        
        if category_hours:
            top_category = max(category_hours.items(), key=lambda x: x[1])
            cap_info = f" (capped at {self.LYELL_DAILY_CAP_PER_EMPLOYEE}h/day)" if top_category[0] in ['etl', 'reporting'] else " (no cap)"
            insights.append(
                f"Primary focus: {top_category[0].title()} tasks account for {top_category[1]:.1f} hours "
                f"({(top_category[1]/sum(category_hours.values())*100):.1f}% of total){cap_info}"
            )
        
        return insights