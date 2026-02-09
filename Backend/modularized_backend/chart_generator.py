class ChartGenerator:
    def __init__(self, base_processor, individual_analyzer, team_analyzer):
        self.base = base_processor
        self.individual = individual_analyzer
        self.team = team_analyzer
    
    def get_chart_data(self):
        """Get data formatted for charts"""
        team_metrics = self.team.get_team_overview_metrics()
        if not team_metrics:
            return None
        
        # Get status distribution data
        status_distribution = []
        if 'status_breakdown' in team_metrics:
            for status, count in team_metrics['status_breakdown'].items():
                status_distribution.append({
                    'status': status,
                    'count': count
                })
        
        # Get submission rate distribution
        submission_rates = []
        for primary_email in self.base.employee_all_emails.keys():
            metrics = self.individual.get_employee_detailed_metrics(primary_email)
            if metrics:
                submission_rates.append({
                    'name': metrics['name'],
                    'rate': metrics['submission_rate']
                })
        
        # Sort by rate for top 10
        submission_rates.sort(key=lambda x: x['rate'], reverse=True)
        top_submitters = submission_rates[:10]
        
        # Get daily hours distribution
        daily_hours = []
        for primary_email in self.base.employee_all_emails.keys():
            metrics = self.individual.get_employee_detailed_metrics(primary_email)
            if metrics and metrics['avg_daily_hours'] > 0:
                daily_hours.append({
                    'name': metrics['name'],
                    'hours': metrics['avg_daily_hours']
                })
        
        # Sort by hours for top 10
        daily_hours.sort(key=lambda x: x['hours'], reverse=True)
        top_hours = daily_hours[:10]
        
        return {
            'status_distribution': status_distribution,
            'top_submitters': top_submitters,
            'top_hours': top_hours,
            'team_metrics': {
                'avg_submission_rate': team_metrics['avg_submission_rate'],
                'avg_daily_hours': team_metrics['avg_daily_hours'],
                'total_employees': team_metrics['total_employees'],
                'high_performers': team_metrics['high_performers']
            }
        }
