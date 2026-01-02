"""
PDF generation module for delivery bills - Professional single-page format
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from typing import List, Dict

class PDFGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#000000'),
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanySubHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#000000'),
            spaceAfter=2,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#000000'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
    
    def generate_pdf(self, invoice_data: Dict, output_path: str):
        """
        Generate professional single-page PDF invoice
        """
        # Reduced margins for more space
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=10*mm, leftMargin=10*mm,
                                topMargin=10*mm, bottomMargin=10*mm)
        
        story = []
        
        # Company Header - Compact
        company_header = Table([
            ['SENTHIL EXPLOSIVES'],
            ['No:20, Panchayat Office Street Sulur, Coimbatore-641402'],
            ['Godown at: S.F.No.126/2 (v) No.80 Sulur Coimbatore - 641402'],
            ['GSTIN: 33ACIFS0095D1ZC']
        ], colWidths=[180*mm])
        
        company_header.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(company_header)
        story.append(Spacer(1, 4))
        
        # Invoice Title
        title_table = Table([['DELIVERY CHALLAN']], colWidths=[180*mm])
        title_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(title_table)
        story.append(Spacer(1, 4))
        
        # Top section: Invoice details and Customer details side by side
        invoice_details = [
            ['Invoice No:', invoice_data.get('invoice_number', '')],
            ['Date:', invoice_data.get('date_of_supply', '')],
            ['Category:', invoice_data.get('category', '')],
            ['Location:', invoice_data.get('location_name', '')],
            ['Vehicle No:', invoice_data.get('vehicle_number', '')],
        ]
        
        customer = invoice_data.get('customer', {})
        customer_details = [
            ['Receiver Name:', customer.get('name', '')],
            ['Address:', customer.get('address', '')],
            ['SF.NO:', customer.get('sf_no', '')],
            ['RC.NO:', customer.get('rc_no', '')],
            ['State:', customer.get('state', '')],
            ['GSTIN:', customer.get('gstin', '')],
        ]
        
        # Create two-column layout
        left_table = Table(invoice_details, colWidths=[40*mm, 50*mm])
        left_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        right_table = Table(customer_details, colWidths=[40*mm, 50*mm])
        right_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Combine in two columns
        combined_table = Table([
            [left_table, right_table]
        ], colWidths=[90*mm, 90*mm])
        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(combined_table)
        story.append(Spacer(1, 4))
        
        # Additional details - compact
        additional_data = [
            ['Mode of Transport:', invoice_data.get('mode_of_transport', 'Road'),
             'Original:', '✓' if invoice_data.get('is_original', False) else ''],
            ['Place of Supply:', invoice_data.get('place_of_supply', ''),
             'GSTIN/Unique ID:', invoice_data.get('gstin_unique_id', '')],
        ]
        
        additional_table = Table(additional_data, colWidths=[30*mm, 50*mm, 30*mm, 50*mm])
        additional_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(additional_table)
        story.append(Spacer(1, 4))
        
        # Items Table - Compact and professional
        items = invoice_data.get('items', [])
        if items:
            # Header row
            items_header = [
                'S.No', 'Description', 'HSN', 'Unit', 'Qty', 
                'Rate', 'Total', 'Tax Val', 'CGST', 'SGST', 'IGST', 'Amount'
            ]
            
            items_data = [items_header]
            
            # Item rows
            for idx, item in enumerate(items, 1):
                cgst_str = f"{item.get('cgst_rate', 0):.1f}%\n{item.get('cgst_rs', 0):.2f}"
                sgst_str = f"{item.get('sgst_rate', 0):.1f}%\n{item.get('sgst_rs', 0):.2f}"
                igst_str = ""
                if item.get('igst_rate', 0) > 0:
                    igst_str = f"{item.get('igst_rate', 0):.1f}%\n{item.get('igst_rs', 0):.2f}"
                
                items_data.append([
                    str(idx),
                    item.get('description', '')[:30],  # Truncate long descriptions
                    item.get('hsn_code', ''),
                    item.get('unit', ''),
                    f"{item.get('qty', 0):.2f}",
                    f"{item.get('rate', 0):.2f}",
                    f"{item.get('total', 0):.2f}",
                    f"{item.get('taxable_value', 0):.2f}",
                    cgst_str,
                    sgst_str,
                    igst_str,
                    f"{item.get('total_amount', 0):.2f}"
                ])
            
            # Grand Total Row
            grand_total = invoice_data.get('grand_total', 0)
            items_data.append([
                '', '', '', '', '', '', '', '',
                '', '', '',
                f"{grand_total:.2f}"
            ])
            
            # Compact column widths
            items_table = Table(items_data, colWidths=[
                6*mm, 30*mm, 12*mm, 8*mm, 10*mm, 12*mm, 12*mm, 12*mm,
                14*mm, 14*mm, 14*mm, 14*mm
            ])
            
            items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                ('TOPPADDING', (0, 0), (-1, 0), 4),
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -2), 2),
                ('TOPPADDING', (0, 1), (-1, -2), 2),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Total row
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 7),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 4),
                ('TOPPADDING', (0, -1), (-1, -1), 4),
            ]))
            
            story.append(items_table)
            story.append(Spacer(1, 4))
        
        # Totals section - compact
        freight = invoice_data.get('freight_charges', 0)
        total_data = [
            ['Freight Charges:', f"{freight:.2f}"],
            ['Total Amount:', f"{invoice_data.get('grand_total', 0):.2f}"],
        ]
        
        total_table = Table(total_data, colWidths=[40*mm, 50*mm])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, 1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(total_table)
        
        # Total in words
        words_text = invoice_data.get('total_in_words', '')
        if words_text:
            words_table = Table([['Challan Total Value (In Words):', words_text]], 
                              colWidths=[50*mm, 130*mm])
            words_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(words_table)
            story.append(Spacer(1, 4))
        
        # Blaster Details - compact
        blaster_data = [
            ['Name of shot fire / Blaster:', invoice_data.get('blaster_name', '')],
            ['Document No:', invoice_data.get('document_no', '')],
            ['Address:', invoice_data.get('blaster_address', '')],
        ]
        
        blaster_table = Table(blaster_data, colWidths=[50*mm, 130*mm])
        blaster_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(blaster_table)
        story.append(Spacer(1, 6))
        
        # Signature area - at bottom
        signature_table = Table([
            ['', 'Senthil Explosives Partner'],
            ['', '(Seal/Stamp and Signature)']
        ], colWidths=[140*mm, 40*mm])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(signature_table)
        
        # Build PDF
        doc.build(story)
