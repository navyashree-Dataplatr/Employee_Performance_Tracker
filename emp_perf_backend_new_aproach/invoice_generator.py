"""
Invoice Generator for Lyell Project Monthly Billing

This module generates structured invoice data for Lyell project monthly billing,
aggregating employee hours, applying SOW caps, and creating invoice records.
"""

from datetime import date, datetime
from typing import Dict, List, Optional
import json


class LyellInvoiceGenerator:
    """
    Generates monthly invoices for Lyell project with SOW compliance.
    """
    
    def __init__(self, lyell_individual_analyzer, billing_rate: float = 75.0):
        """
        Initialize invoice generator with Lyell analyzer.
        
        Args:
            lyell_individual_analyzer: Instance of LyellIndividualAnalyzer
            billing_rate: Hourly billing rate for the project
        """
        self.lyell_analyzer = lyell_individual_analyzer
        self.billing_rate = billing_rate
    
    def generate_invoice_number(self, year: int, month: int) -> str:
        """
        Generate invoice number in format: INV-LYELL-YYYY-MM-001
        
        Args:
            year: Invoice year
            month: Invoice month
            
        Returns:
            Invoice number string
        """
        return f"INV-LYELL-{year}-{month:02d}-001"
    
    def generate_monthly_invoice(self, year: int, month: int) -> Dict:
        """
        Generate comprehensive monthly invoice for Lyell project.
        
        Args:
            year: Year to generate invoice for
            month: Month to generate invoice for (1-12)
            
        Returns:
            Dictionary with complete invoice data including:
            - Invoice metadata (number, period, generation date)
            - Summary totals (hours, billable hours, extra hours)
            - Employee breakdown
            - Category breakdown
            - SOW compliance status
        """
        print(f"Generating invoice for Lyell project: {year}-{month:02d}")
        
        # Calculate date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            from datetime import timedelta
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            from datetime import timedelta
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get monthly performance data from analyzer
        monthly_data = self.lyell_analyzer.get_lyell_monthly_performance(year, month)
        
        # Generate invoice number
        invoice_number = self.generate_invoice_number(year, month)
        
        # Extract employee performance data
        employee_performance = monthly_data.get('employee_performance', [])
        
        # Calculate invoice totals
        totals = self._calculate_invoice_totals(employee_performance)
        
        # Generate employee breakdown for invoice
        employee_breakdown = self._generate_employee_breakdown(employee_performance)
        
        # Generate category breakdown
        category_breakdown = self._generate_category_breakdown(employee_performance)
        
        # Check SOW compliance
        has_violations = any(emp.get('total_extra_hours', 0) > 0 for emp in employee_performance)
        
        # Construct invoice data
        invoice_data = {
            'invoice_number': invoice_number,
            'year': year,
            'month': month,
            'month_name': start_date.strftime('%B'),
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'generated_by': 'Dataplatr Analytics System',
            
            # Summary totals
            'total_hours': round(totals['total_hours'], 2),
            'total_billable_hours': round(totals['total_billable_hours'], 2),
            'total_extra_hours': round(totals['total_extra_hours'], 2),
            'hourly_rate': self.billing_rate,
            'total_billable_amount': round(totals['total_billable_hours'] * self.billing_rate, 2),
            'total_employees': len(employee_performance),
            'total_days_worked': monthly_data.get('daily_activity', []),
            
            # Breakdowns
            'employee_breakdown': employee_breakdown,
            'category_breakdown': category_breakdown,
            
            # Compliance
            'has_sow_violations': has_violations,
            'sow_cap_info': {
                'etl_cap': '4 hours/day per employee',
                'reporting_cap': '4 hours/day per employee',
                'other_categories': 'No cap',
                'hourly_rate': f"${self.billing_rate}/hr"
            },
            
            # Status
            'status': 'GENERATED',
            'period_description': f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
        }
        
        print(f"✓ Invoice generated: {invoice_number}")
        print(f"  Total hours: {totals['total_hours']:.2f}")
        print(f"  Billable hours: {totals['total_billable_hours']:.2f}")
        print(f"  Extra hours: {totals['total_extra_hours']:.2f}")
        print(f"  Employees: {len(employee_performance)}")
        
        return invoice_data
    
    def _calculate_invoice_totals(self, employee_performance: List[Dict]) -> Dict:
        """
        Calculate total hours across all employees.
        
        Args:
            employee_performance: List of employee performance dictionaries
            
        Returns:
            Dictionary with total hours, billable hours, and extra hours
        """
        total_hours = sum(emp.get('total_hours_on_lyell', 0) for emp in employee_performance)
        total_billable_hours = sum(emp.get('total_billable_hours', 0) for emp in employee_performance)
        total_extra_hours = sum(emp.get('total_extra_hours', 0) for emp in employee_performance)
        
        return {
            'total_hours': total_hours,
            'total_billable_hours': total_billable_hours,
            'total_extra_hours': total_extra_hours
        }
    
    def _generate_employee_breakdown(self, employee_performance: List[Dict]) -> List[Dict]:
        """
        Generate employee-level breakdown for invoice.
        
        Args:
            employee_performance: List of employee performance dictionaries
            
        Returns:
            List of employee invoice items
        """
        employee_breakdown = []
        
        for emp in employee_performance:
            category_breakdown = emp.get('category_breakdown', {})
            
            employee_item = {
                'employee_name': emp.get('employee_name', 'Unknown'),
                'employee_email': emp.get('employee_email', ''),
                'total_hours': round(emp.get('total_hours_on_lyell', 0), 2),
                'billable_hours': round(emp.get('total_billable_hours', 0), 2),
                'extra_hours': round(emp.get('total_extra_hours', 0), 2),
                'days_worked': emp.get('total_days_on_lyell', 0),
                'categories': {
                    'actual_hours': category_breakdown.get('actual_hours', {}),
                    'billable_hours': category_breakdown.get('billable_hours', {}),
                    'extra_hours': category_breakdown.get('extra_hours', {})
                },
                'billing_efficiency': emp.get('billing_efficiency', 100),
                'sow_compliance': emp.get('sow_compliance_status', 'Compliant'),
                'rate': self.billing_rate,
                'billable_amount': round(emp.get('total_billable_hours', 0) * self.billing_rate, 2)
            }
            
            employee_breakdown.append(employee_item)
        
        # Sort by total hours (descending)
        employee_breakdown.sort(key=lambda x: x['total_hours'], reverse=True)
        
        return employee_breakdown
    
    def _generate_category_breakdown(self, employee_performance: List[Dict]) -> List[Dict]:
        """
        Generate category-level breakdown for invoice.
        
        Args:
            employee_performance: List of employee performance dictionaries
            
        Returns:
            List of category invoice items
        """
        # Aggregate across all employees by category
        category_totals = {}
        
        for emp in employee_performance:
            category_breakdown = emp.get('category_breakdown', {})
            
            actual_hours = category_breakdown.get('actual_hours', {})
            billable_hours = category_breakdown.get('billable_hours', {})
            extra_hours = category_breakdown.get('extra_hours', {})
            
            for category in actual_hours.keys():
                if category not in category_totals:
                    category_totals[category] = {
                        'total_hours': 0,
                        'billable_hours': 0,
                        'extra_hours': 0
                    }
                
                category_totals[category]['total_hours'] += actual_hours.get(category, 0)
                category_totals[category]['billable_hours'] += billable_hours.get(category, 0)
                category_totals[category]['extra_hours'] += extra_hours.get(category, 0)
        
        # Convert to list format
        category_breakdown = []
        for category, totals in category_totals.items():
            category_item = {
                'category': category,
                'category_label': category.title(),
                'total_hours': round(totals['total_hours'], 2),
                'billable_hours': round(totals['billable_hours'], 2),
                'extra_hours': round(totals['extra_hours'], 2),
                'has_cap': category in ['etl', 'reporting'],
                'cap_value': '4 hours/day' if category in ['etl', 'reporting'] else 'No cap',
                'rate': self.billing_rate,
                'billable_amount': round(totals['billable_hours'] * self.billing_rate, 2)
            }
            category_breakdown.append(category_item)
        
        # Sort by total hours (descending)
        category_breakdown.sort(key=lambda x: x['total_hours'], reverse=True)
        
        return category_breakdown
    
    def get_available_invoice_periods(self) -> List[Dict]:
        """
        Get list of available invoice periods based on Lyell data.
        
        Returns:
            List of dictionaries with year, month, and data availability
        """
        # Get all unique months from Lyell data
        lyell_data = self.lyell_analyzer._filter_lyell_data()
        
        if lyell_data.empty:
            return []
        
        # Extract unique year-month combinations
        lyell_data['year_month'] = lyell_data['clean_date'].apply(
            lambda x: (x.year, x.month)
        )
        unique_periods = lyell_data['year_month'].unique()
        
        # Format as list
        available_periods = []
        for year, month in sorted(unique_periods, reverse=True):
            month_name = date(year, month, 1).strftime('%B')
            available_periods.append({
                'year': year,
                'month': month,
                'month_name': month_name,
                'period': f"{month_name} {year}",
                'has_data': True
            })
        
        return available_periods
