"""
PDF Invoice Generator for Lyell Project

This module generates professional PDF invoices using ReportLab library.
Includes formatted tables, headers, and SOW compliance notes.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from typing import Dict
import os


class InvoicePDFGenerator:
    """
    Generates professional PDF invoices for Lyell project monthly billing.
    """
    
    def __init__(self, output_directory: str = "invoices"):
        """
        Initialize PDF generator.
        
        Args:
            output_directory: Directory to save generated PDFs
        """
        self.output_directory = output_directory
        
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for invoice."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='InvoiceSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=10,
            spaceBefore=15
        ))
    
    def generate_invoice_pdf(self, invoice_data: Dict, filename: str = None) -> str:
        """
        Generate PDF invoice from invoice data.
        
        Args:
            invoice_data: Dictionary with invoice details
            filename: Optional custom filename (without extension)
            
        Returns:
            Path to generated PDF file
        """
        # Generate filename if not provided
        if not filename:
            filename = f"Lyell_Invoice_{invoice_data['year']}-{invoice_data['month']:02d}"
        
        output_path = os.path.join(self.output_directory, f"{filename}.pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build PDF content
        story = []
        
        # Header
        story.extend(self._create_header(invoice_data))
        
        # Invoice metadata
        story.extend(self._create_metadata(invoice_data))
        
        # Summary totals
        story.extend(self._create_summary_table(invoice_data))
        
        # Category breakdown
        story.extend(self._create_category_table(invoice_data))
        
        # Employee breakdown
        story.extend(self._create_employee_table(invoice_data))
        
        # SOW compliance notes
        story.extend(self._create_compliance_notes(invoice_data))
        
        # Footer
        story.extend(self._create_footer(invoice_data))
        
        # Build PDF
        doc.build(story)
        
        print(f"✓ PDF invoice generated: {output_path}")
        return output_path
    
    def _create_header(self, invoice_data: Dict) -> list:
        """Create invoice header."""
        elements = []
        
        # Company name
        elements.append(Paragraph("Dataplatr Analytics", self.styles['InvoiceTitle']))
        
        # Invoice title
        elements.append(Paragraph(
            f"Lyell Project - Monthly Invoice",
            self.styles['InvoiceSubtitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_metadata(self, invoice_data: Dict) -> list:
        """Create invoice metadata section."""
        elements = []
        
        metadata_data = [
            ['Invoice Number:', invoice_data['invoice_number']],
            ['Period:', invoice_data['period_description']],
            ['Generated:', datetime.fromisoformat(invoice_data['generated_at']).strftime('%B %d, %Y at %I:%M %p')],
            ['Total Employees:', str(invoice_data['total_employees'])]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#666666')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_summary_table(self, invoice_data: Dict) -> list:
        """Create summary totals table."""
        elements = []
        
        elements.append(Paragraph("Invoice Summary", self.styles['SectionHeader']))
        
        summary_data = [
            ['Description', 'Hours'],
            ['Total Hours Worked', f"{invoice_data['total_hours']:.2f}"],
            ['Billable Hours (After SOW Caps)', f"{invoice_data['total_billable_hours']:.2f}"],
            ['Extra Hours (Unbillable)', f"{invoice_data['total_extra_hours']:.2f}"],
            ['Hourly Rate', f"${invoice_data['hourly_rate']:.2f}/hr"],
            ['Total Billable Amount', f"${invoice_data['total_billable_amount']:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[4.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            
            # Data rows
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            
            # Totals (last row)
            ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 11),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_category_table(self, invoice_data: Dict) -> list:
        """Create category breakdown table."""
        elements = []
        
        elements.append(Paragraph("Category Breakdown", self.styles['SectionHeader']))
        
        # Header row
        category_data = [
            ['Category', 'Total Hours', 'Billable', 'Extra', 'Rate', 'Amount']
        ]
        
        # Data rows
        for cat in invoice_data['category_breakdown']:
            category_data.append([
                cat['category_label'],
                f"{cat['total_hours']:.2f}",
                f"{cat['billable_hours']:.2f}",
                f"{cat['extra_hours']:.2f}",
                f"${cat['rate']:.2f}",
                f"${cat['billable_amount']:,.2f}"
            ])
        
        category_table = Table(category_data, colWidths=[1.8*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
        category_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(category_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_employee_table(self, invoice_data: Dict) -> list:
        """Create employee breakdown table."""
        elements = []
        
        elements.append(Paragraph("Employee Breakdown", self.styles['SectionHeader']))
        
        # Header row
        employee_data = [
            ['Employee', 'Days', 'Total Hours', 'Billable', 'Rate', 'Amount']
        ]
        
        # Data rows
        for emp in invoice_data['employee_breakdown']:
            employee_data.append([
                emp['employee_name'],
                str(emp['days_worked']),
                f"{emp['total_hours']:.2f}",
                f"{emp['billable_hours']:.2f}",
                f"${emp['rate']:.2f}",
                f"${emp['billable_amount']:,.2f}"
            ])
        
        employee_table = Table(employee_data, colWidths=[1.8*inch, 0.6*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.3*inch])
        employee_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(employee_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_compliance_notes(self, invoice_data: Dict) -> list:
        """Create SOW compliance notes."""
        elements = []
        
        elements.append(Paragraph("SOW Compliance Notes", self.styles['SectionHeader']))
        
        notes_text = f"""
        <b>Lyell Project SOW Caps:</b><br/>
        • ETL Work: Maximum 4 hours per day per employee<br/>
        • Reporting Work: Maximum 4 hours per day per employee<br/>
        • Development, Testing, Architecture: No caps applied<br/>
        <br/>
        <b>Compliance Status:</b> {'⚠️ Has Violations' if invoice_data['has_sow_violations'] else '✓ Fully Compliant'}<br/>
        """
        
        if invoice_data['has_sow_violations']:
            notes_text += f"""
            <br/>
            Total extra hours (unbillable): <b>{invoice_data['total_extra_hours']:.2f} hours</b><br/>
            These hours exceeded the SOW caps and are marked as unbillable.
            """
        
        notes_para = Paragraph(notes_text, self.styles['Normal'])
        elements.append(notes_para)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_footer(self, invoice_data: Dict) -> list:
        """Create invoice footer."""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        
        footer_text = f"""
        <i>This invoice was automatically generated by Dataplatr Analytics System.<br/>
        Generated by: {invoice_data['generated_by']}<br/>
        For questions or clarifications, please contact your project manager.</i>
        """
        
        footer_para = Paragraph(footer_text, self.styles['Normal'])
        elements.append(footer_para)
        
        return elements
