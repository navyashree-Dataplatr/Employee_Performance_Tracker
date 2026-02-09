import pandas as pd

class TeamAnalyzer:
    def __init__(self, base_processor, individual_analyzer):
        self.base = base_processor
        self.individual = individual_analyzer
    
    def get_team_overview_metrics(self):
        all_metrics = []
        
        for primary_email in self.base.employee_all_emails.keys():
            metrics = self.individual.get_employee_detailed_metrics(primary_email)
            if metrics:
                all_metrics.append(metrics)
        
        if not all_metrics:
            return None
        
        df = pd.DataFrame(all_metrics)
        
        status_counts = df['status'].value_counts().to_dict()
        
        consistent_reporters = len(df[df['status'].isin(['Excellent', 'Good'])])
        partial_reporters = len(df[df['status'] == 'Inconsistent'])
        frequent_defaulters = len(df[df['status'].isin(['Poor', 'Very Poor', 'Non-Reporter'])])
        
        high_performers = len(df[df['avg_tasks_per_day'] > 3])
        
        avg_submission_rate = df['submission_rate'].mean()
        avg_daily_hours = df['avg_daily_hours'].mean()
        avg_tasks = df['avg_tasks_per_day'].mean()
        
        employees_with_gaps = len(df[df['max_gap'] >= 2])
        
        total_underutilized = df['underutilized_days'].sum()
        total_overloaded = df['overloaded_days'].sum()
        total_work_days = df['total_reports'].sum()
        
        underutilized_pct = (total_underutilized / total_work_days * 100) if total_work_days > 0 else 0
        overloaded_pct = (total_overloaded / total_work_days * 100) if total_work_days > 0 else 0
        
        top_performers = df.nlargest(5, 'submission_rate')[['name', 'submission_rate', 'avg_tasks_per_day']].to_dict('records')
        bottom_performers = df.nsmallest(5, 'submission_rate')[['name', 'submission_rate', 'max_gap']].to_dict('records')
        
        return {
            'total_employees': len(all_metrics),
            'date_range': f"{self.base.min_date} to {self.base.max_date}",
            'total_working_days': self.base.total_days,
            'status_breakdown': status_counts,
            'consistent_reporters': consistent_reporters,
            'partial_reporters': partial_reporters,
            'frequent_defaulters': frequent_defaulters,
            'high_performers': high_performers,
            'avg_submission_rate': round(avg_submission_rate, 1),
            'avg_daily_hours': round(avg_daily_hours, 2),
            'avg_tasks_per_day': round(avg_tasks, 2),
            'employees_with_gaps': employees_with_gaps,
            'underutilized_percentage': round(underutilized_pct, 1),
            'overloaded_percentage': round(overloaded_pct, 1),
            'top_performers': top_performers,
            'bottom_performers': bottom_performers
        }
    
    def get_high_performers(self, task_threshold=3):
        """Get employees with above-average task completion"""
        high_performers = []
        for primary_email in self.base.employee_all_emails.keys():
            metrics = self.individual.get_employee_detailed_metrics(primary_email)
            if metrics and metrics['avg_tasks_per_day'] > task_threshold:
                high_performers.append(metrics)
        
        high_performers.sort(key=lambda x: x['avg_tasks_per_day'], reverse=True)
        return high_performers

