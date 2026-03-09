
import pandas as pd
from datetime import datetime, date
import re
from typing import Dict, List, Tuple, Optional


class ProjectBillingAnalyzer:
    """
    Analyzes project billing data with SOW enforcement for Lyell project ONLY.
    DataPlatr project has no caps - bill all hours.
    """
    
    # SOW Billing Rules (Lyell Project ONLY)
    LYELL_SOW_RULES = {

        # ETL & Reporting have caps. Development, Testing, Architect have no caps.
        'etl': {
            'max_hours_per_day': 4.0,
            'keywords': [r'\[etl\]', r'etl', r'data pipeline', r'data processing', r'elf work']
        },
        'reporting': {
            'max_hours_per_day': 4.0,
            'keywords': [r'report', r'dashboard', r'analytics', r'visualization', r'reporting']
        },


        # No caps for these categories (Lyell)
        'development': {
            'max_hours_per_day': None,
            'keywords': [r'development', r'dev', r'coding', r'programming', r'\[development\]']
        },
        'testing': {
            'max_hours_per_day': None,
            'keywords': [r'testing', r'qa', r'quality assurance', r'\[testing\]', r'\[qa\]']
        },
        'architect': {
            'max_hours_per_day': None,
            'keywords': [r'architect', r'design', r'planning', r'strategy', r'architecture']
        },
        'other': {
            'max_hours_per_day': None,
            'keywords': []
        }
    }
    
    # DataPlatr Project: NO CAPS for any category
    DATAPLATR_RULES = {
        'all_categories': {
            'max_hours_per_day': None  # No caps at all
        }
    }
    
    # Project mappings (case-insensitive)
    PROJECT_NAMES = {
        'lyell': ['lyell'],
        'dataplatr': ['dataplatr', 'datapltr', 'data platr']
    }
    

    # Initialize with work data DataFrame from BaseDataProcessor. Expected columns: ['work_date', 'project', 'Tasks_Completed', 'Hours']
    def __init__(self, work_df: pd.DataFrame):
        """
        Initialize with work data DataFrame from BaseDataProcessor.
        
        Args:
            work_df: DataFrame from BaseDataProcessor.get_work_data_for_billing()
                    Expected columns: ['work_date', 'project', 'Tasks_Completed', 'Hours']
        """
        if work_df.empty:
            self.work_df = pd.DataFrame(columns=['work_date', 'project', 'Tasks_Completed', 'Hours'])
            print("Warning: Empty DataFrame provided to billing analyzer")
        else:
            self.work_df = work_df.copy()
            self._prepare_data()
    


    # This section prepares and cleans the data for billing analysis, including normalizing project names and extracting categories from task descriptions.
    def _prepare_data(self):
        """Prepare and clean data for billing analysis."""
        print(f"Preparing billing data: {len(self.work_df)} rows")
        
        # Ensure we have required columns
        required_cols = ['work_date', 'project', 'Tasks_Completed', 'Hours']
        for col in required_cols:
            if col not in self.work_df.columns:
                raise ValueError(f"Missing required column for billing: {col}")
        
        # Filter out rows without hours
        self.work_df = self.work_df[self.work_df['Hours'] > 0].copy()
        
        # Normalize project names
        self.work_df['project_normalized'] = self.work_df['project'].apply(
            self._normalize_project_name
        )
        
        # Extract category from task description
        self.work_df['category'] = self.work_df['Tasks_Completed'].apply(
            self._extract_category
        )
        
        # Ensure work_date is date type
        self.work_df['work_date'] = pd.to_datetime(self.work_df['work_date']).dt.date
        
        print(f"Billing data prepared: {len(self.work_df)} valid rows")
        print(f"Projects found: {self.work_df['project_normalized'].unique()}")
    


    # This section normalizes project names to a standard format for consistent analysis. It checks against known project names and returns a normalized version.
    def _normalize_project_name(self, project_name: str) -> str:
        """
        Normalize project name to standard format.
        
        Args:
            project_name: Raw project name from data
            
        Returns:
            Normalized project name (lowercase, standardized)
        """
        if pd.isna(project_name):
            return 'unknown'
        
        name = str(project_name).lower().strip()
        
        # Check against known project names
        for normalized, aliases in self.PROJECT_NAMES.items():
            for alias in aliases:
                if alias.lower() in name:
                    return normalized
        
        # Return original if not recognized
        return name
    



    # This section extracts the work category from the task description using keyword matching and bracket notation. It applies Lyell SOW rules for categorization.
    # For Lyell project, it checks for specific keywords to categorize tasks into ETL, Reporting, Development, Testing, Architect, or Other. For DataPlatr, it categorizes all tasks as 'all_categories' since there are no caps.
    # It also looks for bracket notation (e.g., [ETL]) to help identify categories. If no category is matched, it defaults to 'other'.
    
    def _extract_category(self, task_text: str) -> str:
        """
        Extract work category from task text.
        
        Args:
            task_text: Raw task description
            
        Returns:
            Category name (standardized)
        """
        if pd.isna(task_text):
            return 'other'
        
        text = str(task_text).lower()
        
        # Check each SOW category for matches (Lyell rules)
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
    


    # This section applies SOW rules based on the project and category. For Lyell, it enforces caps on ETL and Reporting categories, while Development, Testing, and Architect have no caps. For DataPlatr, there are no caps for any category, so all hours are billable.
    # It returns a tuple of (billable_hours, extra_hours) based on the rules applied.
    # For Lyell:
    # - ETL & Reporting: If hours exceed 4 per day, only 4 are billable and the rest are extra.
    # - Development, Testing, Architect: All hours are billable with no caps.
    # For DataPlatr:
    # - All categories: No caps, all hours are billable.
    # For any other projects, it defaults to no caps and bills all hours.
    # This function is called during the daily aggregation process to determine how many hours are billable and how many are extra based on the SOW rules for the specific project and category.
    def _apply_project_sow_rules(self, project: str, category: str, hours: float) -> Tuple[float, float]:
        """
        Apply SOW rules based on project and category.
        
        SPECIAL RULE: Only Lyell has caps. DataPlatr has no caps.
        
        Args:
            project: Project name (normalized)
            category: Work category
            hours: Actual hours worked
            
        Returns:
            Tuple of (billable_hours, extra_hours)
        """
        if project == 'lyell':
            # Apply Lyell SOW rules
            rule = self.LYELL_SOW_RULES.get(category, self.LYELL_SOW_RULES['other'])
            max_hours = rule.get('max_hours_per_day')
            
            if max_hours is None:
                # No cap for this category in Lyell
                return hours, 0.0
            else:
                # Apply cap (ETL & Reporting only)
                billable = min(hours, max_hours)
                extra = max(0, hours - max_hours)
                return billable, extra
        
        elif project == 'dataplatr':
            # DataPlatr: NO CAPS for any category
            return hours, 0.0
        
        else:
            # Other projects: No caps (default)
            return hours, 0.0
    


    # This is the main function to get a comprehensive billing summary for a project, including daily breakdown, totals, category breakdown, and SOW violations. It takes into account the special rules for Lyell and DataPlatr projects.
    # For Lyell, it identifies SOW violations based on extra hours in capped categories. For DataPlatr, it simply bills all hours with no violations.
    # The function returns a dictionary with all the relevant billing information, which can be used for reporting or invoice generation.
    # It also handles filtering by date range and returns an empty summary if no data is found for the specified project and period.
    # The summary includes:
    # - Project name and analysis period
    # - Total days analyzed
    # - Daily summary with actual hours, billed hours, extra hours, and category details
    # - Overall totals for actual hours, billed hours, extra hours, and category totals
    # - SOW violations (for Lyell) with details on dates and extra hours
    # - SOW rules applied for the project
    # - Project type (Lyell with caps or DataPlatr with no caps)
    def get_project_billing_summary(
        self, 
        project_name: str, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        Get comprehensive billing summary for a project.
        
        SPECIAL: Lyell has SOW caps, DataPlatr has no caps.
        
        Args:
            project_name: Project name ('lyell', 'dataplatr')
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            
        Returns:
            Dictionary with billing summary
        """
        print(f"Generating billing summary for {project_name}")
        
        # Filter data by project and date
        filtered_df = self._filter_by_project_and_date(
            project_name, start_date, end_date
        )
        
        if filtered_df.empty:
            return self._empty_summary(project_name, start_date, end_date)
        
        # Aggregate by date and category
        daily_summary = self._aggregate_daily_billing(filtered_df, project_name)
        
        # Calculate totals
        totals = self._calculate_totals(daily_summary)
        
        # Get category breakdown
        category_breakdown = self._get_category_breakdown(daily_summary)
        
        # Identify SOW violations (Lyell only)
        sow_violations = self._identify_sow_violations(daily_summary, project_name)
        
        # Get applicable SOW rules
        sow_rules_applied = self._get_sow_rules_for_project(project_name)
        
        return {
            'project': project_name.title(),
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else filtered_df['work_date'].min().isoformat(),
                'end_date': end_date.isoformat() if end_date else filtered_df['work_date'].max().isoformat()
            },
            'total_days': len(daily_summary),
            'daily_summary': daily_summary,
            'totals': totals,
            'category_breakdown': category_breakdown,
            'sow_violations': sow_violations,
            'sow_rules_applied': sow_rules_applied,
            'project_type': 'LYELL_WITH_CAPS' if project_name == 'lyell' else 'NO_CAPS'
        }
    


    # This section filters the DataFrame by project and date range. It normalizes the project name for consistent filtering and applies date filters if provided. It returns a filtered DataFrame that can be used for further analysis.
    # The function checks for the normalized project name in the 'project_normalized' column and filters the data accordingly. It also applies date filters based on the 'work_date' column, allowing for analysis of specific periods. If no data is found after filtering, it returns an empty DataFrame.

    
    def _filter_by_project_and_date(
        self, 
        project_name: str, 
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> pd.DataFrame:
        """Filter DataFrame by project and date range."""
        # Normalize project name for filtering
        normalized_project = self._normalize_project_name(project_name)
        
        # Filter by project
        filtered = self.work_df[
            self.work_df['project_normalized'] == normalized_project
        ].copy()
        
        if filtered.empty:
            return filtered
        
        # Filter by date range
        if start_date:
            filtered = filtered[filtered['work_date'] >= start_date]
        if end_date:
            filtered = filtered[filtered['work_date'] <= end_date]
        
        print(f"Filtered to {len(filtered)} rows for {project_name}")
        return filtered
    


    # This section aggregates hours by date and category, applying SOW rules for the Lyell project. It groups the data by work date and category, sums the hours, and then applies the SOW rules to determine billable and extra hours. It returns a list of daily billing records with all the relevant details for each day.
    # For each day, it calculates the total actual hours, total billed hours, total extra hours, and whether there are any extra hours (SOW violations for Lyell). It also provides a breakdown of hours by category for each day, including the actual hours, billed hours, extra hours, and the maximum allowed hours based on the SOW rules. This detailed daily summary is essential for understanding billing patterns and identifying any compliance issues with the SOW for the Lyell project. For DataPlatr, all hours are billed with no caps, so there will be no extra hours or violations.
    # The function processes each day separately, applying the appropriate rules based on the project type, and compiles a comprehensive summary that can be used for reporting or invoice generation.
    # It also prints out the number of days of billing data that were aggregated for the specified project.
    def _aggregate_daily_billing(self, df: pd.DataFrame, project: str) -> List[Dict]:
        """
        Aggregate hours by date and category, applying SOW rules.
        
        Returns:
            List of daily billing records with SOW rules applied
        """
        # Group by date and category
        grouped = df.groupby(['work_date', 'category']).agg({
            'Hours': 'sum'
        }).reset_index()
        
        # Process each day
        daily_summary = []
        
        for (work_date, date_group) in grouped.groupby('work_date'):
            daily_record = {
                'date': work_date,
                'categories': {},
                'total_actual_hours': 0,
                'total_billed_hours': 0,
                'total_extra_hours': 0,
                'has_extra_hours': False,
                'extra_hours_detail': {}
            }
            
            # Process each category for this day
            for _, row in date_group.iterrows():
                category = row['category']
                actual_hours = float(row['Hours'])
                
                # Apply SOW rules based on project
                billed_hours, extra_hours = self._apply_project_sow_rules(
                    project, category, actual_hours
                )
                
                daily_record['categories'][category] = {
                    'actual_hours': actual_hours,
                    'billed_hours': billed_hours,
                    'extra_hours': extra_hours,
                    'max_allowed': self._get_max_hours_for_category(project, category)
                }
                
                daily_record['total_actual_hours'] += actual_hours
                daily_record['total_billed_hours'] += billed_hours
                daily_record['total_extra_hours'] += extra_hours
                
                if extra_hours > 0:
                    daily_record['has_extra_hours'] = True
                    daily_record['extra_hours_detail'][category] = extra_hours
            
            daily_summary.append(daily_record)
        
        print(f"Aggregated {len(daily_summary)} days of billing data for {project}")
        return daily_summary
    


    # This section retrieves the maximum allowed hours for a given category in a project based on the SOW rules. For Lyell, it checks the specific category against the LYELL_SOW_RULES to determine if there is a cap on hours. For DataPlatr and other projects, it returns None since there are no caps. This function is used during the daily aggregation process to provide information on how many hours are allowed for billing in each category, which is essential for identifying SOW violations in the Lyell project.
   
    def _get_max_hours_for_category(self, project: str, category: str) -> Optional[float]:
        """Get maximum allowed hours for a category in a project."""
        if project == 'lyell':
            return self.LYELL_SOW_RULES.get(category, {}).get('max_hours_per_day')
        else:
            return None  # No caps for other projects
    

    # This section calculates overall totals from the daily billing summary, including total actual hours, total billed hours, total extra hours, and counts of days with extra hours. It also aggregates totals by category across all days. This comprehensive totals calculation is crucial for understanding the overall billing situation for the project and identifying any patterns in SOW violations for the Lyell project. For DataPlatr, since there are no caps, the total extra hours will always be zero, and all actual hours will be billed.
    # The function iterates through the daily summary records, summing up the hours and counting the days with extra hours. It also compiles category totals to provide insights into which categories are contributing most to the billing and any potential SOW issues for Lyell.
    # The resulting totals dictionary is included in the final billing summary returned by the get_project_billing_summary function, providing a clear overview of the billing metrics for the project.
    # It also prints out the total actual hours, total billed hours, and total extra hours calculated from the daily summary for transparency and debugging purposes.
    def _calculate_totals(self, daily_summary: List[Dict]) -> Dict:
        """Calculate overall totals from billing summary."""
        totals = {
            'total_actual_hours': 0.0,
            'total_billed_hours': 0.0,
            'total_extra_hours': 0.0,
            'days_with_extra_hours': 0,
            'category_totals': {}
        }
        
        # Initialize category totals
        all_categories = set()
        for day in daily_summary:
            for category in day['categories'].keys():
                all_categories.add(category)
        
        for category in all_categories:
            totals['category_totals'][category] = {
                'actual_hours': 0.0,
                'billed_hours': 0.0,
                'extra_hours': 0.0,
                'days_worked': 0
            }
        
        # Calculate totals
        for day in daily_summary:
            totals['total_actual_hours'] += day['total_actual_hours']
            totals['total_billed_hours'] += day['total_billed_hours']
            totals['total_extra_hours'] += day['total_extra_hours']
            
            if day['has_extra_hours']:
                totals['days_with_extra_hours'] += 1
            
            # Aggregate by category
            for category, details in day['categories'].items():
                cat_total = totals['category_totals'][category]
                cat_total['actual_hours'] += details['actual_hours']
                cat_total['billed_hours'] += details['billed_hours']
                cat_total['extra_hours'] += details['extra_hours']
                cat_total['days_worked'] += 1
        
        return totals
    



    # This section gets a breakdown of hours by category across all days in the billing summary. It compiles totals for actual hours, billed hours, extra hours, and counts of days worked for each category. This category breakdown is essential for understanding which categories are contributing most to the billing and any potential SOW issues for the Lyell project. For DataPlatr, since there are no caps, the extra hours will always be zero, but this breakdown still provides insights into how hours are distributed across different types of work.
    # The function iterates through the daily summary records and aggregates the hours for each category,
    # providing a clear picture of the billing distribution by category, which can be used for reporting or to inform future SOW negotiations for the Lyell project.
    def _get_category_breakdown(self, daily_summary: List[Dict]) -> Dict:
        """Get breakdown of hours by category."""
        breakdown = {}
        
        for day in daily_summary:
            for category, details in day['categories'].items():
                if category not in breakdown:
                    breakdown[category] = {
                        'actual_hours': 0.0,
                        'billed_hours': 0.0,
                        'extra_hours': 0.0,
                        'days_worked': 0
                    }
                
                cat_data = breakdown[category]
                cat_data['actual_hours'] += details['actual_hours']
                cat_data['billed_hours'] += details['billed_hours']
                cat_data['extra_hours'] += details['extra_hours']
                cat_data['days_worked'] += 1
        
        return breakdown
    


    # This section identifies SOW violations based on extra hours in capped categories for the Lyell project. It iterates through the daily summary and checks for any days that have extra hours, which indicate a violation of the SOW rules for Lyell. For DataPlatr, since there are no caps, this function will return an empty list as there can be no violations.
    # For each violation found in the Lyell project, it compiles details such as the date of the violation, total extra hours, category details of the extra hours, total actual hours, and total billed hours for that day. This information is crucial for understanding the extent of SOW violations and can be used for reporting or to inform discussions with the client about compliance with the SOW.
    # The function returns a list of violations sorted by date in descending order, allowing for easy identification of the most recent violations. This detailed information on SOW violations is an important aspect of the billing analysis for the Lyell project, while for DataPlatr, it confirms that there are no compliance issues due to the absence of caps.      

    def _identify_sow_violations(self, daily_summary: List[Dict], project: str) -> List[Dict]:
        """
        Identify days with SOW violations (extra hours).
        Only Lyell has violations. DataPlatr has none.
        """
        if project != 'lyell':
            return []  # No violations for non-Lyell projects
        
        violations = []
        
        for day in daily_summary:
            if day['has_extra_hours']:
                violation = {
                    'date': day['date'],
                    'total_extra_hours': day['total_extra_hours'],
                    'category_details': day['extra_hours_detail'],
                    'total_actual_hours': day['total_actual_hours'],
                    'total_billed_hours': day['total_billed_hours']
                }
                violations.append(violation)
        
        # Sort by date descending (most recent first)
        violations.sort(key=lambda x: x['date'], reverse=True)
        
        return violations
    


    # This section retrieves the description of SOW rules applied for a project. For Lyell, it provides details on the caps for ETL and Reporting categories, as well as the fact that Development, Testing, and Architect have no caps. For DataPlatr and other projects, it simply states that there are no caps and all hours are billable. This information is included in the billing summary to provide context on the rules that were applied during the analysis and to help explain any SOW violations for the Lyell project.  
    # The function returns a dictionary with the SOW rules for each category, which can be used in reporting or to inform clients about the billing rules that were applied to their project. This is particularly important for the Lyell project, where understanding the specific caps and rules is essential for interpreting the billing summary and any violations that may have occurred. For DataPlatr, it reinforces the fact that there are no restrictions on billing hours, which can be useful for clients to understand their billing structure.  

    def _get_sow_rules_for_project(self, project: str) -> Dict:
        """Get description of SOW rules applied for a project."""
        if project == 'lyell':
            rules = {}
            for category, rule in self.LYELL_SOW_RULES.items():
                max_hours = rule.get('max_hours_per_day')
                if max_hours is not None:
                    rules[category] = f"Max {max_hours} hours/day (SOW Cap)"
                else:
                    rules[category] = "No cap (bill all hours)"
            return rules
        else:
            # DataPlatr and other projects
            return {
                'all_categories': "No caps - bill all actual hours"
            }
        


        # This section returns an empty summary when no data is found for the specified project and date range. It includes the project name, analysis period, total days (0), empty daily summary, totals with zero hours, empty category breakdown, no SOW violations, applicable SOW rules for the project, project type, and a message indicating that no billing data was found. This function is called in the get_project_billing_summary method when the filtered DataFrame is empty after applying the project and date filters. It ensures that the billing summary always returns a consistent structure, even when there is no data to analyze, which can be useful for reporting or client communication.  

    
    def _empty_summary(
        self, 
        project_name: str, 
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict:
        """Return empty summary when no data is found."""
        return {
            'project': project_name.title(),
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'total_days': 0,
            'daily_summary': [],
            'totals': {
                'total_actual_hours': 0.0,
                'total_billed_hours': 0.0,
                'total_extra_hours': 0.0,
                'days_with_extra_hours': 0,
                'category_totals': {}
            },
            'category_breakdown': {},
            'sow_violations': [],
            'sow_rules_applied': self._get_sow_rules_for_project(project_name),
            'project_type': 'LYELL_WITH_CAPS' if project_name == 'lyell' else 'NO_CAPS',
            'status': 'NO_DATA',
            'message': f'No billing data found for {project_name}'
        }
    


    # This section provides a method to get a detailed billing report for a specific day. It calls the get_project_billing_summary method with the same start and end date to retrieve the summary for that specific day. If no work is recorded for that day, it returns a message indicating that there is no data. Otherwise, it extracts the relevant information from the daily summary and returns a detailed report for that day, including total actual hours, total billed hours, total extra hours, category breakdown, and SOW compliance status. This function can be used to generate daily reports for clients or internal review, providing insights into the billing details for each day of work.
    # It also includes the project type (Lyell with caps or DataPlatr with no caps) in the report, which can help explain the billing details and any SOW compliance issues for the Lyell project. This daily report is a useful tool for understanding the billing on a day-by-day basis and can be used to identify any specific days that may have had significant extra hours or SOW violations for the Lyell project. For DataPlatr, it will confirm that all hours are billed with no extra hours or violations.
    # The function returns a dictionary with the daily billing report, which can be used for reporting or client communication, providing a clear and detailed view of the billing for that specific day.
    
    
    def get_daily_billing_report(
        self, 
        project_name: str, 
        target_date: date
    ) -> Dict:
        """
        Get detailed billing report for a specific day.
        
        Args:
            project_name: Project name
            target_date: Date to analyze
            
        Returns:
            Detailed daily billing report
        """
        print(f"Getting daily billing report for {project_name} on {target_date}")
        
        summary = self.get_project_billing_summary(
            project_name, target_date, target_date
        )
        
        if summary['total_days'] == 0:
            return {
                'project': project_name.title(),
                'date': target_date.isoformat(),
                'status': 'NO_DATA',
                'message': f'No work recorded for {project_name} on {target_date}'
            }
        
        daily_data = summary['daily_summary'][0]
        
        return {
            'project': project_name.title(),
            'date': target_date.isoformat(),
            'status': 'ANALYZED',
            'total_actual_hours': daily_data['total_actual_hours'],
            'total_billed_hours': daily_data['total_billed_hours'],
            'total_extra_hours': daily_data['total_extra_hours'],
            'has_extra_hours': daily_data['has_extra_hours'],
            'categories': daily_data['categories'],
            'extra_hours_detail': daily_data['extra_hours_detail'],
            'sow_compliance': 'VIOLATION' if daily_data['has_extra_hours'] else 'COMPLIANT',
            'project_type': 'LYELL_WITH_CAPS' if project_name == 'lyell' else 'NO_CAPS'
        }
    


    # This section provides a method to get a summary of all projects with billing data. It iterates through the unique normalized project names in the DataFrame, generates a billing summary for each project using the get_project_billing_summary method, and compiles a list of project summaries. Each project summary includes the project name, total days analyzed, total actual hours, total billed hours, total extra hours, number of SOW violations (for Lyell), and the project type (Lyell with caps or DataPlatr with no caps). The function returns a dictionary containing the list of project summaries and the total number of projects analyzed. This method is useful for generating an overview of all projects with billing data, allowing for easy comparison and reporting across multiple projects.
    # It also handles the case where the DataFrame is empty, returning an empty list of projects and a total project count of zero, ensuring that the function always returns a consistent structure even when there is no data to analyze. This comprehensive summary can be used for high-level reporting or to inform clients about the billing status of all their projects in one place.   
    def get_all_projects_summary(self) -> Dict:
        """
        Get summary of all projects with billing data.
        
        Returns:
            Dictionary with project summaries
        """
        if self.work_df.empty:
            return {'projects': [], 'total_projects': 0}
        
        # Get unique projects
        unique_projects = self.work_df['project_normalized'].unique()
        project_summaries = []
        
        for project in unique_projects:
            if project != 'unknown':
                summary = self.get_project_billing_summary(project)
                project_summaries.append({
                    'name': project.title(),
                    'normalized_name': project,
                    'total_days': summary['total_days'],
                    'total_actual_hours': summary['totals']['total_actual_hours'],
                    'total_billed_hours': summary['totals']['total_billed_hours'],
                    'total_extra_hours': summary['totals']['total_extra_hours'],
                    'sow_violations': len(summary['sow_violations']),
                    'project_type': 'LYELL_WITH_CAPS' if project == 'lyell' else 'NO_CAPS'
                })
        
        return {
            'projects': project_summaries,
            'total_projects': len(project_summaries)
        }