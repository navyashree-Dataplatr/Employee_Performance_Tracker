
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
    
    def _get_max_hours_for_category(self, project: str, category: str) -> Optional[float]:
        """Get maximum allowed hours for a category in a project."""
        if project == 'lyell':
            return self.LYELL_SOW_RULES.get(category, {}).get('max_hours_per_day')
        else:
            return None  # No caps for other projects
    
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