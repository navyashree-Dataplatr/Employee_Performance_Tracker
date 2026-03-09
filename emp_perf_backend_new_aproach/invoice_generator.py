

"""
Invoice Generator for Lyell Project Monthly Billing
"""  # This is a description of the file. It explains that this code generates invoices for the Lyell project.

from datetime import date, timedelta  # Import date functions to work with dates
from typing import Dict, List  # Import typing helpers for better code readability


class LyellInvoiceGenerator:  # Main class that handles invoice generation
    
    def __init__(self, lyell_individual_analyzer, billing_rate: float = 75.0):
        # Constructor function - runs automatically when object is created
        
        self.lyell_analyzer = lyell_individual_analyzer  
        # Stores the analyzer object which provides Lyell project work data

        self.billing_rate = billing_rate  
        # Stores hourly billing rate (default is $75 per hour)
    
    def generate_invoice_number(self, year: int, month: int) -> str:
        # Function to generate a unique invoice number using year and month

        return f"INV-LYELL-{year}-{month:02d}-001"
        # Creates invoice number in format like INV-LYELL-2026-03-001


    def generate_monthly_invoice(self, year: int, month: int) -> Dict:
        # Main function that generates invoice data for a specific month

        print(f"Generating invoice for Lyell project: {year}-{month:02d}")
        # Prints a message indicating invoice generation started

        start_date = date(year, month, 1)
        # Creates the first date of the given month

        if month == 12:
            # Special handling if the month is December

            end_date = date(year + 1, 1, 1) - timedelta(days=1)
            # End date becomes Dec 31 (Jan 1 of next year minus 1 day)

        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            # Otherwise end date is last day of the given month

        monthly_data = self.lyell_analyzer.get_lyell_monthly_performance(year, month)
        # Fetch monthly performance data for Lyell project from analyzer

        invoice_number = self.generate_invoice_number(year, month)
        # Generate invoice number for this invoice

        employee_performance = monthly_data.get('employee_performance', [])
        # Extract employee performance list from monthly data

        totals = self._calculate_invoice_totals(employee_performance)
        # Calculate overall totals like total hours and billable hours

        employee_breakdown = self._generate_employee_breakdown(employee_performance)
        # Create detailed billing info for each employee

        category_breakdown = self._generate_category_breakdown(employee_performance)
        # Create summary of hours grouped by work category

        has_violations = any(emp.get('total_extra_hours', 0) > 0 for emp in employee_performance)
        # Check if any employee has extra hours beyond allowed limits

        invoice_data = {
            # Dictionary that stores the final invoice information

            'invoice_number': invoice_number,  # Unique invoice ID
            'year': year,  # Invoice year
            'month': month,  # Invoice month
            'month_name': start_date.strftime('%B'),  # Month name (e.g., March)
            'period_start': start_date.isoformat(),  # Start date in ISO format
            'period_end': end_date.isoformat(),  # End date in ISO format
            'generated_by': 'Dataplatr Analytics System',  # System generating invoice

            'total_hours': round(totals['total_hours'], 2),
            # Total hours worked across all employees

            'total_billable_hours': round(totals['total_billable_hours'], 2),
            # Total billable hours across employees

            'total_extra_hours': round(totals['total_extra_hours'], 2),
            # Total hours exceeding allowed limits

            'hourly_rate': self.billing_rate,
            # Billing rate per hour

            'total_billable_amount': round(totals['total_billable_hours'] * self.billing_rate, 2),
            # Total invoice amount (billable hours * rate)

            'total_employees': len(employee_performance),
            # Number of employees who worked on Lyell project

            'total_days_worked': monthly_data.get('daily_activity', []),
            # Daily work activity data

            'employee_breakdown': employee_breakdown,
            # Detailed per employee billing information

            'category_breakdown': category_breakdown,
            # Summary of hours grouped by work category

            'has_sow_violations': has_violations,
            # Indicates if any SOW (Statement of Work) rules were violated

            'sow_cap_info': {
                # SOW limits information

                'etl_cap': '4 hours/day per employee',
                # Maximum allowed ETL hours per day

                'reporting_cap': '4 hours/day per employee',
                # Maximum allowed Reporting hours per day

                'other_categories': 'No cap',
                # Other work categories have no limits

                'hourly_rate': f"${self.billing_rate}/hr"
                # Hourly billing rate formatted for display
            },

            'status': 'GENERATED',
            # Current status of invoice

            'period_description': f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
            # Human readable invoice period
        }

        print(f"✓ Invoice generated: {invoice_number}")
        # Print confirmation message

        print(f"  Total hours: {totals['total_hours']:.2f}")
        # Print total hours worked

        print(f"  Billable hours: {totals['total_billable_hours']:.2f}")
        # Print billable hours

        print(f"  Extra hours: {totals['total_extra_hours']:.2f}")
        # Print extra hours

        print(f"  Employees: {len(employee_performance)}")
        # Print total employees

        return invoice_data
        # Return the complete invoice data dictionary
    
    
    def _calculate_invoice_totals(self, employee_performance: List[Dict]) -> Dict:
        # Private function to calculate overall totals

        return {
            'total_hours': sum(emp.get('total_hours_on_lyell', 0) for emp in employee_performance),
            # Sum of total hours worked by all employees

            'total_billable_hours': sum(emp.get('total_billable_hours', 0) for emp in employee_performance),
            # Sum of all billable hours

            'total_extra_hours': sum(emp.get('total_extra_hours', 0) for emp in employee_performance)
            # Sum of extra hours beyond limits
        }



    def _generate_employee_breakdown(self, employee_performance: List[Dict]) -> List[Dict]:
        # Private function to generate detailed billing data for each employee

        employee_breakdown = []
        # Create empty list to store employee billing data

        for emp in employee_performance:
            # Loop through each employee record

            category_breakdown = emp.get('category_breakdown', {})
            # Get category-wise work hours

            employee_breakdown.append({
                'employee_name': emp.get('employee_name', 'Unknown'),
                # Employee name

                'employee_email': emp.get('employee_email', ''),
                # Employee email

                'total_hours': round(emp.get('total_hours_on_lyell', 0), 2),
                # Total hours worked

                'billable_hours': round(emp.get('total_billable_hours', 0), 2),
                # Total billable hours

                'extra_hours': round(emp.get('total_extra_hours', 0), 2),
                # Extra hours exceeding limits

                'days_worked': emp.get('total_days_on_lyell', 0),
                # Total days worked on project

                'categories': {
                    'actual_hours': category_breakdown.get('actual_hours', {}),
                    # Actual hours by category

                    'billable_hours': category_breakdown.get('billable_hours', {}),
                    # Billable hours by category

                    'extra_hours': category_breakdown.get('extra_hours', {})
                    # Extra hours by category
                },

                'billing_efficiency': emp.get('billing_efficiency', 100),
                # Percentage of billable efficiency

                'sow_compliance': emp.get('sow_compliance_status', 'Compliant'),
                # Indicates if employee followed SOW limits

                'rate': self.billing_rate,
                # Hourly rate applied

                'billable_amount': round(emp.get('total_billable_hours', 0) * self.billing_rate, 2)
                # Total billing amount for employee
            })

        employee_breakdown.sort(key=lambda x: x['total_hours'], reverse=True)
        # Sort employees by highest total hours

        return employee_breakdown
        # Return sorted employee billing data



    def _generate_category_breakdown(self, employee_performance: List[Dict]) -> List[Dict]:
        # Private function to calculate totals by work category

        category_totals = {}
        # Dictionary to store totals for each category

        for emp in employee_performance:
            # Loop through employees

            category_breakdown = emp.get('category_breakdown', {})
            # Get category breakdown

            actual_hours = category_breakdown.get('actual_hours', {})
            # Actual hours by category

            billable_hours = category_breakdown.get('billable_hours', {})
            # Billable hours by category

            extra_hours = category_breakdown.get('extra_hours', {})
            # Extra hours by category

            for category in actual_hours.keys():
                # Loop through each category

                if category not in category_totals:
                    # Initialize category totals if not present

                    category_totals[category] = {'total_hours': 0, 'billable_hours': 0, 'extra_hours': 0}

                category_totals[category]['total_hours'] += actual_hours.get(category, 0)
                # Add actual hours to total

                category_totals[category]['billable_hours'] += billable_hours.get(category, 0)
                # Add billable hours

                category_totals[category]['extra_hours'] += extra_hours.get(category, 0)
                # Add extra hours

        category_breakdown = []
        # List to store category summary

        for category, totals in category_totals.items():
            # Loop through category totals

            category_breakdown.append({
                'category': category,
                # Category name

                'category_label': category.title(),
                # Formatted category name

                'total_hours': round(totals['total_hours'], 2),
                # Total hours for category

                'billable_hours': round(totals['billable_hours'], 2),
                # Billable hours for category

                'extra_hours': round(totals['extra_hours'], 2),
                # Extra hours for category

                'has_cap': category in ['etl', 'reporting'],
                # True if category has SOW cap

                'cap_value': '4 hours/day' if category in ['etl', 'reporting'] else 'No cap',
                # Cap value description

                'rate': self.billing_rate,
                # Billing rate

                'billable_amount': round(totals['billable_hours'] * self.billing_rate, 2)
                # Total billing amount for category
            })

        category_breakdown.sort(key=lambda x: x['total_hours'], reverse=True)
        # Sort categories by highest hours

        return category_breakdown
        # Return category breakdown


    def get_available_invoice_periods(self) -> List[Dict]:
        # Function to determine which months have available data

        lyell_data = self.lyell_analyzer._filter_lyell_data()
        # Fetch filtered Lyell project dataset

        if lyell_data.empty:
            return []
            # Return empty list if no data available

        lyell_data['year_month'] = lyell_data['clean_date'].apply(
            lambda x: (x.year, x.month)
        )
        # Create (year, month) tuple column

        unique_periods = lyell_data['year_month'].unique()
        # Get unique year-month combinations

        available_periods = []
        # List to store available invoice periods

        for year, month in sorted(unique_periods, reverse=True):
            # Loop through unique periods sorted by latest first

            month_name = date(year, month, 1).strftime('%B')
            # Get month name

            available_periods.append({
                'year': year,
                'month': month,
                'month_name': month_name,
                'period': f"{month_name} {year}",
                'has_data': True
            })
            # Add period info to list

        return available_periods
        # Return list of available invoice months