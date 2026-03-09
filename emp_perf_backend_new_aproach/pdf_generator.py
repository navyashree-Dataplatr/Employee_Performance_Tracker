"""
PDF Invoice Generator for Lyell Project

This module generates professional PDF invoices using ReportLab library.
Includes formatted tables, headers, and SOW compliance notes.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from typing import Dict
import os


class InvoicePDFGenerator:

    def __init__(self, output_directory: str = "invoices"):
        self.output_directory = output_directory
        os.makedirs(output_directory, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='InvoiceSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=10,
            spaceBefore=15
        ))



# This is the main function that generates the PDF invoice. It takes in invoice data and an optional filename.
    def generate_invoice_pdf(self, invoice_data: Dict, filename: str = None) -> str:
        if not filename:
            filename = f"Lyell_Invoice_{invoice_data['year']}-{invoice_data['month']:02d}"

        output_path = os.path.join(self.output_directory, f"{filename}.pdf")

        # ALWAYS delete old cached PDF before regenerating
        # This ensures stale files never get served
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"🗑 Deleted old cached PDF: {output_path}")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch
        )

        story = []
        story.extend(self._create_header(invoice_data))
        story.extend(self._create_metadata(invoice_data))
        story.extend(self._create_summary_table(invoice_data))
        story.extend(self._create_category_table(invoice_data))
        story.extend(self._create_employee_table(invoice_data))
        story.extend(self._create_compliance_notes(invoice_data))
        story.extend(self._create_footer(invoice_data))

        doc.build(story)
        print(f"✓ PDF invoice generated: {output_path}")
        return output_path



# This section creates the header of the invoice, including the company name and invoice title.
    def _create_header(self, invoice_data: Dict) -> list:
        return [
            Paragraph("Dataplatr Analytics", self.styles['InvoiceTitle']),
            Paragraph("Lyell Project - Monthly Invoice", self.styles['InvoiceSubtitle']),
            Spacer(1, 0.2 * inch)
        ]



# This section creates a metadata table with invoice number, period, and total employees.
    def _create_metadata(self, invoice_data: Dict) -> list:
      
        metadata_data = [
            ['Invoice Number:',  invoice_data['invoice_number']],
            ['Period:',          invoice_data['period_description']],
            ['Total Employees:', str(invoice_data['total_employees'])]
        ]

        metadata_table = Table(metadata_data, colWidths=[2 * inch, 4.5 * inch])
        metadata_table.setStyle(TableStyle([
            ('FONT',          (0, 0), (-1, -1), 'Helvetica',      10),
            ('FONT',          (0, 0), (0,  -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR',     (0, 0), (0,  -1), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR',     (1, 0), (1,  -1), colors.HexColor('#444444')),
            ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        return [metadata_table, Spacer(1, 0.3 * inch)]


# This section creates a summary table with total hours, billable hours, extra hours, hourly rate, and total amount.
    def _create_summary_table(self, invoice_data: Dict) -> list:
        summary_data = [
            ['Description',                    'Value'],
            ['Total Hours Worked',              f"{invoice_data['total_hours']:.2f} hrs"],
            ['Billable Hours (After SOW Caps)', f"{invoice_data['total_billable_hours']:.2f} hrs"],
            ['Extra Hours (Unbillable)',         f"{invoice_data['total_extra_hours']:.2f} hrs"],
            ['Hourly Rate',                     f"${invoice_data['hourly_rate']:.2f}/hr"],
            ['Total Billable Amount',           f"${invoice_data['total_billable_amount']:,.2f}"],
        ]

        summary_table = Table(summary_data, colWidths=[4.5 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),   colors.HexColor('#2563eb')),
            ('TEXTCOLOR',     (0, 0), (-1, 0),   colors.white),
            ('FONT',          (0, 0), (-1, 0),   'Helvetica-Bold', 11),
            ('ALIGN',         (0, 0), (-1, 0),   'LEFT'),
            ('FONT',          (0, 1), (-1, -1),  'Helvetica', 10),
            ('ALIGN',         (0, 1), (0,  -1),  'LEFT'),
            ('ALIGN',         (1, 1), (1,  -1),  'RIGHT'),
            ('FONT',          (0, -1), (-1, -1), 'Helvetica-Bold', 11),
            ('BACKGROUND',    (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('GRID',          (0, 0), (-1, -1),  1, colors.HexColor('#d1d5db')),
            ('BOTTOMPADDING', (0, 0), (-1, -1),  8),
            ('TOPPADDING',    (0, 0), (-1, -1),  8),
        ]))

        return [
            Paragraph("Invoice Summary", self.styles['SectionHeader']),
            summary_table,
            Spacer(1, 0.3 * inch)
        ]


# This section creates a detailed category breakdown table, showing hours and amounts for each work category.
    def _create_category_table(self, invoice_data: Dict) -> list:
        category_data = [['Category', 'Total Hours', 'Billable', 'Extra', 'Rate', 'Amount']]

        for cat in invoice_data['category_breakdown']:
            category_data.append([
                cat['category_label'],
                f"{cat['total_hours']:.2f}",
                f"{cat['billable_hours']:.2f}",
                f"{cat['extra_hours']:.2f}",
                f"${cat['rate']:.2f}",
                f"${cat['billable_amount']:,.2f}"
            ])

        category_table = Table(
            category_data,
            colWidths=[1.8 * inch, 1 * inch, 1 * inch, 1 * inch, 1 * inch, 1.2 * inch]
        )
        category_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#2563eb')),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONT',          (0, 0), (-1, 0),  'Helvetica-Bold', 10),
            ('ALIGN',         (0, 0), (0,  0),  'LEFT'),
            ('ALIGN',         (1, 0), (-1, 0),  'CENTER'),
            ('FONT',          (0, 1), (-1, -1), 'Helvetica', 9),
            ('ALIGN',         (0, 1), (0,  -1), 'LEFT'),
            ('ALIGN',         (1, 1), (-1, -1), 'CENTER'),
            ('GRID',          (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ]))

        return [
            Paragraph("Category Breakdown", self.styles['SectionHeader']),
            category_table,
            Spacer(1, 0.3 * inch)
        ]


# This section creates a detailed employee breakdown table, showing hours and amounts for each employee.
    def _create_employee_table(self, invoice_data: Dict) -> list:
        employee_data = [['Employee', 'Days', 'Total Hours', 'Billable', 'Rate', 'Amount']]

        for emp in invoice_data['employee_breakdown']:
            employee_data.append([
                emp['employee_name'],
                str(emp['days_worked']),
                f"{emp['total_hours']:.2f}",
                f"{emp['billable_hours']:.2f}",
                f"${emp['rate']:.2f}",
                f"${emp['billable_amount']:,.2f}"
            ])

        employee_table = Table(
            employee_data,
            colWidths=[1.8 * inch, 0.6 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.3 * inch]
        )
        employee_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#2563eb')),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONT',          (0, 0), (-1, 0),  'Helvetica-Bold', 9),
            ('ALIGN',         (0, 0), (0,  0),  'LEFT'),
            ('ALIGN',         (1, 0), (-1, 0),  'CENTER'),
            ('FONT',          (0, 1), (-1, -1), 'Helvetica', 8),
            ('ALIGN',         (0, 1), (0,  -1), 'LEFT'),
            ('ALIGN',         (1, 1), (-1, -1), 'CENTER'),
            ('GRID',          (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ]))

        return [
            Paragraph("Employee Breakdown", self.styles['SectionHeader']),
            employee_table,
            Spacer(1, 0.3 * inch)
        ]

# This section adds detailed SOW compliance notes to the invoice, including any violations and unbillable hours.
    def _create_compliance_notes(self, invoice_data: Dict) -> list:
        compliance_status = (
            'Has Violations' if invoice_data['has_sow_violations'] else '✓ Fully Compliant'
        )

        notes_text = (
            "<b>Lyell Project SOW Caps:</b><br/>"
            "• ETL Work: Maximum 4 hours per day per employee<br/>"
            "• Reporting Work: Maximum 4 hours per day per employee<br/>"
            "• Development, Testing, Architecture: No caps applied<br/><br/>"
            f"<b>Compliance Status:</b> {compliance_status}<br/>"
        )

        if invoice_data['has_sow_violations']:
            notes_text += (
                f"<br/>Total extra hours (unbillable): "
                f"<b>{invoice_data['total_extra_hours']:.2f} hours</b><br/>"
                "These hours exceeded the SOW caps and are marked as unbillable."
            )

        return [
            Paragraph("SOW Compliance Notes", self.styles['SectionHeader']),
            Paragraph(notes_text, self.styles['Normal']),
            Spacer(1, 0.2 * inch)
        ]


    def _create_footer(self, invoice_data: Dict) -> list:
        # Simple footer with generated by info
        footer_text = f"<i>Generated by: {invoice_data['generated_by']}</i>"
        return [Spacer(1, 0.3 * inch), Paragraph(footer_text, self.styles['Normal'])]