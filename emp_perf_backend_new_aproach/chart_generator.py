

# chart_generator.py
class ChartGenerator:
    def __init__(self, base_processor):
        self.base = base_processor
    
    def get_chart_data(self):
        """Get data formatted for charts - automatically includes all available data"""
        try:
            from team_analyzer import TeamAnalyzer
            from individual_analyzer import IndividualAnalyzer
            
            # Initialize analyzers
            individual = IndividualAnalyzer(self.base)
            team = TeamAnalyzer(self.base, individual)
            
            # Initialize result structure
            result = {
                'status_distribution': [],
                'top_submitters': [],
                'top_hours': [],
                'team_metrics': {},
                'project_distribution': [],  # NEW: Team-wide project distribution
                'project_hours': [],  # NEW: Project hours by employee
                'extra_hours_breakdown': [],  # NEW: Extra hours by employee
                'category_compliance': [],  # NEW: Compliance by category
                'daily_project_hours': [],  # NEW: Project hours over time
                'billing_efficiency': [],  # NEW: Billing efficiency by employee
                'debug_info': {}
            }
            
            # === EXISTING TEAM METRICS ===
            team_metrics = team.get_team_overview_metrics()
            if team_metrics:
                print(f"Team metrics available: {bool(team_metrics)}")
                
                # Get status distribution data
                if 'status_breakdown' in team_metrics and team_metrics['status_breakdown']:
                    for status, count in team_metrics['status_breakdown'].items():
                        result['status_distribution'].append({
                            'status': status,
                            'count': count
                        })
                
                # Team metrics summary
                result['team_metrics'] = {
                    'avg_submission_rate': team_metrics.get('avg_submission_rate', 0),
                    'avg_daily_hours': team_metrics.get('avg_daily_hours', 0),
                    'total_employees': team_metrics.get('total_employees', 0),
                    'high_performers': team_metrics.get('high_performers', 0),
                    'consistent_reporters': team_metrics.get('consistent_reporters', 0),
                    'partial_reporters': team_metrics.get('partial_reporters', 0),
                    'frequent_defaulters': team_metrics.get('frequent_defaulters', 0),
                    'employees_with_gaps': team_metrics.get('employees_with_gaps', 0)
                }
            
            # === INDIVIDUAL METRICS ===
            employee_emails = list(self.base.employee_all_emails.keys())
            print(f"Total employee emails: {len(employee_emails)}")
            
            submission_rates = []
            daily_hours = []
            
            for idx, email in enumerate(employee_emails[:47]):  # Limit to 47 for performance
                try:
                    metrics = individual.get_employee_detailed_metrics(email)
                    if metrics:
                        # Add submission rate
                        if 'submission_rate' in metrics:
                            submission_rates.append({
                                'name': metrics.get('name', f'Employee {idx}'),
                                'rate': metrics['submission_rate']
                            })
                        
                        # Add daily hours
                        if metrics.get('avg_daily_hours', 0) > 0:
                            daily_hours.append({
                                'name': metrics.get('name', f'Employee {idx}'),
                                'hours': metrics['avg_daily_hours']
                            })
                except Exception as e:
                    print(f"Error getting metrics for {email}: {e}")
                    continue
            
            # Sort and add to results
            submission_rates.sort(key=lambda x: x['rate'], reverse=True)
            result['top_submitters'] = submission_rates  # Return all submitters for complete chart
            
            daily_hours.sort(key=lambda x: x['hours'], reverse=True)
            result['top_hours'] = daily_hours  # Return all employees for complete chart
            
            # === NEW: PROJECT-SPECIFIC DATA ===
            project_data = self._extract_project_data()
            if project_data:
                result['project_hours'] = project_data.get('project_hours', [])
                result['project_distribution'] = project_data.get('project_distribution', [])
                result['extra_hours_breakdown'] = project_data.get('extra_hours_breakdown', [])
                result['category_compliance'] = project_data.get('category_compliance', [])
                result['daily_project_hours'] = project_data.get('daily_project_hours', [])
                result['billing_efficiency'] = project_data.get('billing_efficiency', [])
            
            # Debug info
            result['debug_info'] = {
                'employee_count': len(employee_emails),
                'submission_rates_count': len(submission_rates),
                'daily_hours_count': len(daily_hours),
                'status_items': len(result['status_distribution']),
                'project_distribution_count': len(result['project_distribution']),
                'project_hours_count': len(result['project_hours']),
                'extra_hours_count': len(result['extra_hours_breakdown'])
            }
            
            print(f"Chart data generated with {len(result['top_submitters'])} submitters and {len(result['project_hours'])} project entries")
            return result
            
        except Exception as e:
            print(f"Error generating chart data: {e}")
            import traceback
            traceback.print_exc()
            return self._get_empty_chart_data()
    
    def _extract_project_data(self):
        """Extract project-specific data for charts"""
        try:
            project_data = {
                'project_hours': [],
                'project_distribution': [],
                'extra_hours_breakdown': [],
                'category_compliance': [],
                'daily_project_hours': [],
                'billing_efficiency': []
            }
            
            # Check if base has project data attributes
            if not hasattr(self.base, 'all_entries'):
                print("No all_entries attribute found in base")
                return project_data
            
            # Try to extract project hours by employee
            project_hours_map = {}
            extra_hours_map = {}
            category_map = {}
            daily_hours_map = {}
            
            for entry in self.base.all_entries:
                try:
                    employee_name = entry.get('employee_name', 'Unknown')
                    project = entry.get('project', 'Unknown')
                    hours = float(entry.get('hours', 0))
                    extra_hours = float(entry.get('extra_hours', 0))
                    category = entry.get('category', 'Unknown')
                    date = entry.get('date', '')
                    
                    # Project hours by employee
                    key = f"{employee_name}|{project}"
                    if key not in project_hours_map:
                        project_hours_map[key] = {
                            'employee': employee_name,
                            'project': project,
                            'total_hours': 0,
                            'billable_hours': 0
                        }
                    project_hours_map[key]['total_hours'] += hours
                    project_hours_map[key]['billable_hours'] += (hours - extra_hours)
                    
                    # Extra hours by employee
                    if extra_hours > 0:
                        if employee_name not in extra_hours_map:
                            extra_hours_map[employee_name] = {
                                'employee': employee_name,
                                'extra_hours': 0
                            }
                        extra_hours_map[employee_name]['extra_hours'] += extra_hours
                    
                    # Category compliance
                    cat_key = f"{project}|{category}"
                    if cat_key not in category_map:
                        category_map[cat_key] = {
                            'project': project,
                            'category': category,
                            'total_hours': 0,
                            'extra_hours': 0
                        }
                    category_map[cat_key]['total_hours'] += hours
                    category_map[cat_key]['extra_hours'] += extra_hours
                    
                    # Daily project hours
                    day_key = f"{date}|{project}"
                    if day_key not in daily_hours_map:
                        daily_hours_map[day_key] = {
                            'date': date,
                            'project': project,
                            'hours': 0
                        }
                    daily_hours_map[day_key]['hours'] += hours
                    
                except Exception as e:
                    print(f"Error processing entry: {e}")
                    continue
            
            # Convert to lists
            project_data['project_hours'] = sorted(
                list(project_hours_map.values()),
                key=lambda x: x['total_hours'],
                reverse=True
            )
            
            project_data['extra_hours_breakdown'] = sorted(
                list(extra_hours_map.values()),
                key=lambda x: x['extra_hours'],
                reverse=True
            )
            
            project_data['category_compliance'] = sorted(
                list(category_map.values()),
                key=lambda x: x['extra_hours'],
                reverse=True
            )
            
            project_data['daily_project_hours'] = sorted(
                list(daily_hours_map.values()),
                key=lambda x: x['date']
            )

            # Team-wide project distribution
            team_project_hours = {}
            total_team_hours = 0
            for item in project_data['project_hours']:
                p = item['project']
                h = item['total_hours']
                team_project_hours[p] = team_project_hours.get(p, 0) + h
                total_team_hours += h

            for p, h in team_project_hours.items():
                project_data['project_distribution'].append({
                    'project': p,
                    'hours': round(h, 2),
                    'percentage': round((h / total_team_hours * 100), 1) if total_team_hours > 0 else 0
                })
            
            # Calculate billing efficiency
            for item in project_data['project_hours']:
                if item['total_hours'] > 0:
                    efficiency = (item['billable_hours'] / item['total_hours']) * 100
                    project_data['billing_efficiency'].append({
                        'employee': item['employee'],
                        'project': item['project'],
                        'efficiency': round(efficiency, 1)
                    })
            
            print(f"Project data extracted: {len(project_data['project_hours'])} project entries, {len(project_data['extra_hours_breakdown'])} employees with extra hours")
            return project_data
            
        except Exception as e:
            print(f"Error extracting project data: {e}")
            import traceback
            traceback.print_exc()
            return {
                'project_hours': [],
                'project_distribution': [],
                'extra_hours_breakdown': [],
                'category_compliance': [],
                'daily_project_hours': [],
                'billing_efficiency': []
            }
    
    def _get_empty_chart_data(self):
        """Return empty chart data structure"""
        return {
            'status_distribution': [],
            'top_submitters': [],
            'top_hours': [],
            'team_metrics': {
                'avg_submission_rate': 0,
                'avg_daily_hours': 0,
                'total_employees': 0,
                'high_performers': 0,
                'consistent_reporters': 0,
                'partial_reporters': 0,
                'frequent_defaulters': 0,
                'employees_with_gaps': 0
            },
            'project_hours': [],
            'project_distribution': [],
            'extra_hours_breakdown': [],
            'category_compliance': [],
            'daily_project_hours': [],
            'billing_efficiency': [],
            'debug_info': {
                'employee_count': 0,
                'submission_rates_count': 0,
                'daily_hours_count': 0,
                'status_items': 0,
                'project_distribution_count': 0,
                'project_hours_count': 0,
                'extra_hours_count': 0,
                'error': 'Failed to generate chart data'
            }
        }