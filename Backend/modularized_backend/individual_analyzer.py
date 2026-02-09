from datetime import datetime, timedelta

class IndividualAnalyzer:
    def __init__(self, base_processor):
        self.base = base_processor
    
    def get_employee_detailed_metrics(self, employee_email):
        employee_email = employee_email.lower().strip()
        
        if employee_email not in self.base.employee_all_emails:
            return None
        
        employee_info = self.base.master_df[self.base.master_df['Email'] == employee_email]
        if employee_info.empty:
            return None
        
        employee_info = employee_info.iloc[0]
        name = employee_info['Name']
        
        submitted_dates = self.base.submissions.get(employee_email, set())
        days_done = len(submitted_dates)
        days_missed = self.base.total_days - days_done
        rate = (days_done / self.base.total_days) * 100 if self.base.total_days > 0 else 0
        
        missed_dates = sorted(self.base.working_days_set - submitted_dates)
        max_gap = 0
        if missed_dates:
            current_gap = 1
            for i in range(len(missed_dates) - 1):
                if (missed_dates[i+1] - missed_dates[i]).days == 1:
                    current_gap += 1
                    max_gap = max(max_gap, current_gap)
                else:
                    current_gap = 1
            max_gap = max(max_gap, current_gap) if current_gap > 0 else 0
        
        if days_done == 0:
            status = 'Non-Reporter'
        elif rate >= 90:
            status = 'Excellent'
        elif rate >= 70 and max_gap < 3:
            status = 'Good'
        elif rate >= 50 or max_gap < 4:
            status = 'Inconsistent'
        elif rate >= 30 or max_gap < 5:
            status = 'Poor'
        else:
            status = 'Very Poor'
        
        employee_work = self.base.work_df[self.base.work_df['email'].isin(self.base.employee_all_emails[employee_email])]
        
        avg_hours = employee_work['Hours'].mean() if not employee_work.empty else 0
        
        unique_days = employee_work['clean_date'].nunique()
        avg_tasks = employee_work['task_count'].sum() / unique_days if unique_days > 0 else 0
        
        completion_ratio = employee_work['task_count'].sum() / len(employee_work) if len(employee_work) > 0 else 0
        
        task_diversity = employee_work['Tasks_Completed'].nunique() / len(employee_work) if len(employee_work) > 0 else 0
        
        recent_7_days = employee_work[employee_work['clean_date'] >= (datetime.now() - timedelta(days=7))]
        recent_submissions = len(recent_7_days['clean_date'].unique())
        
        recent_30_days = employee_work[employee_work['clean_date'] >= (datetime.now() - timedelta(days=30))]
        recent_30_submissions = len(recent_30_days['clean_date'].unique())
        
        underutilized_days = len(employee_work[employee_work['Hours'] < 8])
        overloaded_days = len(employee_work[employee_work['Hours'] > 10])
        
        return {
            'name': name,
            'email': employee_email,
            'status': status,
            'days_submitted': days_done,
            'days_missed': days_missed,
            'submission_rate': round(rate, 1),
            'max_gap': max_gap,
            'avg_daily_hours': round(avg_hours, 2),
            'avg_tasks_per_day': round(avg_tasks, 2),
            'completion_ratio': round(completion_ratio, 2),
            'task_diversity': round(task_diversity, 2),
            'recent_7_days_submissions': recent_submissions,
            'recent_30_days_submissions': recent_30_submissions,
            'underutilized_days': underutilized_days,
            'overloaded_days': overloaded_days,
            'total_reports': len(employee_work),
            'date_range': f"{self.base.min_date} to {self.base.max_date}"
        }
    
    def get_comparison_metrics(self, employee_emails):
        comparison_data = []
        
        for email in employee_emails:
            email = email.lower().strip()
            metrics = self.get_employee_detailed_metrics(email)
            if metrics:
                comparison_data.append(metrics)
        
        return comparison_data

