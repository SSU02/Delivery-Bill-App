"""
PDF generation module for delivery bills - Exactly matching Excel/PDF template
ONE CONTINUOUS BOX around entire challan
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from typing import List, Dict
import os
import tempfile

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PdfFileReader as PdfReader
    except ImportError:
        PdfWriter = None
        PdfReader = None

class PDFGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        if 'ChallanTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='ChallanTitle',
                parent=self.styles['Heading1'],
                fontSize=14,
                textColor=colors.black,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        
        if 'CompanyHeader' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CompanyHeader',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=2,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        
        if 'CompanySubHeader' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CompanySubHeader',
                parent=self.styles['Normal'],
                fontSize=7,
                textColor=colors.black,
                spaceAfter=1,
                alignment=TA_CENTER,
                fontName='Helvetica'
            ))
    
    def generate_pdf(self, invoice_data: Dict, output_path: str):
        """
        Generate delivery challan with ONE CONTINUOUS BOX around entire document
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=10*mm, leftMargin=10*mm,
                                topMargin=10*mm, bottomMargin=10*mm)
        
        story = []
        
        # Use the helper method to build the table (same format as multi-page)
        main_table = self._build_invoice_table(invoice_data)
        story.append(main_table)
        
        # Build PDF
        doc.build(story)
    
    def _build_invoice_table(self, invoice_data: Dict):
        """
        Build the invoice table for a single customer - extracted from generate_pdf
        Returns the table with exact same format as original
        """
        # Get all data
        invoice_no = invoice_data.get('invoice_number', '')
        mode_transport = invoice_data.get('mode_of_transport', 'Road')
        vehicle_no = invoice_data.get('vehicle_number', '')
        date_supply = invoice_data.get('date_of_supply', '')
        e_way_bill_no = invoice_data.get('e_way_bill_no', '')
        e_way_document_no = invoice_data.get('e_way_document_no', '')
        is_original = '✓' if invoice_data.get('is_original', False) else ''
        is_duplicate = '✓' if invoice_data.get('is_duplicate', False) else ''
        is_triplicate = '✓' if invoice_data.get('is_triplicate', False) else ''
        
        customer = invoice_data.get('customer', {})
        place_of_supply = invoice_data.get('place_of_supply', '')
        state_code = invoice_data.get('state_code', '33')
        gstin_unique = invoice_data.get('gstin_unique_id', '')
        
        items = invoice_data.get('items', [])
        
        # Build ONE BIG TABLE with all rows - EXACT SAME AS ORIGINAL
        main_table_data = []
        
        # Row 0: Title - DELIVERY CHALLAN (smaller font)
        main_table_data.append(['DELIVERY CHALLAN'] + ['']*14)
        
        # Row 1: Company name - SENTHIL EXPLOSIVES
        main_table_data.append(['SENTHIL EXPLOSIVES'] + ['']*14)
        
        # Row 2: Address
        main_table_data.append(['No:20, Panchayat Office Street Sulur, Coimbatore-641402'] + ['']*14)
        
        # Row 3: Godown (bold)
        main_table_data.append(['Godown at : S.F.No.126/2 (v) No.80 Sulur Coimbatore - 641402'] + ['']*14)
        
        # Row 4: E WAY BILL NO (col 0) + Mode of Transport (col 8) + Original checkbox (col 13-14)
        row4 = ['E WAY BILL NO : ' + e_way_bill_no] + ['']*7 + ['Mode of Transport : ' + mode_transport] + ['']*4 + [is_original, 'Original']
        main_table_data.append(row4)
        
        # Row 5: E WAY DOCUMENT NO (col 0) + Vehicle No (col 8) + Duplicate checkbox (col 13-14)
        row5 = ['E WAY DOCUMENT NO : ' + e_way_document_no] + ['']*7 + ['Veh.No: ' + vehicle_no] + ['']*4 + [is_duplicate, 'Duplicate']
        main_table_data.append(row5)
        
        # Row 6: Invoice No (col 0) + Date of Supply (col 8) + Triplicate checkbox (col 13-14)
        row6 = ['INVOICE NO : ' + invoice_no] + ['']*7 + ['Date  of Supply : ' + date_supply] + ['']*4 + [is_triplicate, 'Triplicate']
        main_table_data.append(row6)
        
        # Row 7: Receiver Details header (empty row above removed)
        main_table_data.append(['Details of Receiver'] + ['']*14)
        
        # Row 8: Name
        customer_name = customer.get('name', '')
        main_table_data.append(['Name: ' + customer_name] + ['']*14)
        
        # Row 9: Address
        customer_address = customer.get('address', '')
        main_table_data.append(['Address: ' + customer_address] + ['']*14)
        
        # Row 10: SF.NO
        sf_no = customer.get('sf_no', '')
        main_table_data.append(['SF.NO: ' + sf_no] + ['']*14)
        
        # Row 11: RC.NO (left) and State Code (right)
        rc_no = customer.get('rc_no', '')
        row11 = ['RC.NO: ' + rc_no] + ['']*8 + ['State Code : ' + state_code] + ['']*5
        main_table_data.append(row11)
        
        # Row 12: State (left) and GSTIN/Unique ID from invoice (right, directly below State Code at col 9)
        customer_state = customer.get('state', '')
        row12 = ['State: ' + customer_state] + ['']*8 + ['GSTIN/Unique ID: ' + gstin_unique] + ['']*5
        main_table_data.append(row12)
        
        # Row 13: customer GSTIN (left) and Place of Supply (center) - in same row
        customer_gstin = customer.get('gstin', '')  # GSTIN from receiver details
        row13 = ['GSTIN: ' + customer_gstin] + ['']*4 + ['Place of Supply : ' + place_of_supply] + ['']*9
        main_table_data.append(row13)
        
        # Row 14: Empty row for spacing
        main_table_data.append(['']*15)
        
        # Items table section
        items_start_row = len(main_table_data)
        
        if items:
            total_taxable_value = sum(item.get('taxable_value', 0) for item in items)
            total_cgst_rs = sum(item.get('cgst_rs', 0) for item in items)
            total_sgst_rs = sum(item.get('sgst_rs', 0) for item in items)
            total_igst_rs = sum(item.get('igst_rs', 0) for item in items)
            total_items_total = sum(item.get('total', 0) for item in items)
            total_items_amount = sum(item.get('total_amount', 0) for item in items)
            
            # Items headers row 1 - Main headers
            # Taxable Value will be split into two words to fit better
            main_table_data.append([
                'S.No', 'Description of Goods', 'HSN Code', 'Unit', 'Qty', 'Rate', 'Total',
                'Taxable\nValue',  # Split into two lines to fit better
                'CGST', '', 'SGST', '', 'IGST', '', 'TOTAL'
            ])
            
            # Items headers row 2 - Sub-headers for tax columns (CGST, SGST, IGST have 2 subcolumns each, TOTAL has 1)
            # CGST spans 8-9, so subheaders at 8-9: Rate, Rs.
            # SGST spans 10-11, so subheaders at 10-11: Rate, Rs.
            # IGST spans 12-13, so subheaders at 12-13: Rate, Rs.
            # TOTAL is at 14, so Amount at 14
            main_table_data.append([
                '', '', '', '', '', '', '', '',
                'Rate', 'Rs.', 'Rate', 'Rs.', 'Rate', 'Rs.', 'Amount'
            ])
            
            # Items data rows (removed empty column, fixed structure)
            for idx, item in enumerate(items, 1):
                description = item.get('description', '')
                # Handle description that might have notes above (like "Used for Explosation")
                cgst_rate_val = item.get('cgst_rate', 0)
                sgst_rate_val = item.get('sgst_rate', 0)
                igst_rate_val = item.get('igst_rate', 0)
                main_table_data.append([
                    str(idx),
                    description,
                    str(item.get('hsn_code', '')),
                    item.get('unit', ''),
                    f"{item.get('qty', 0):.2f}",
                    f"{item.get('rate', 0):.2f}",
                    f"{item.get('total', 0):.2f}",
                    f"{item.get('taxable_value', 0):.2f}",
                    f"{cgst_rate_val:.2f}%" if cgst_rate_val > 0 else '',  # Add % sign
                    f"{item.get('cgst_rs', 0):.2f}",
                    f"{sgst_rate_val:.2f}%" if sgst_rate_val > 0 else '',  # Add % sign
                    f"{item.get('sgst_rs', 0):.2f}",
                    f"{igst_rate_val:.2f}%" if igst_rate_val > 0 else '',  # Add % sign
                    f"{item.get('igst_rs', 0):.2f}" if item.get('igst_rs', 0) > 0 else '',
                    f"{item.get('total_amount', 0):.2f}"
                ])
            
            # Empty row before totals
            main_table_data.append(['']*15)
            
            # Totals row within items table (aligned with data structure)
            # Data rows: col 6=total, col 7=taxable_value, col 9=cgst_rs, col 11=sgst_rs, col 13=igst_rs, col 14=total_amount
            # Totals row should align with data columns (no "Total" label - the value goes directly at col 6)
            totals_row_idx = len(main_table_data)
            main_table_data.append([
                '', '', '', '', '', '',  # Col 0-5: empty
                f"{total_items_total:.2f}",  # Col 6: sum of 'Total' column (col 6 in data rows)
                f"{total_taxable_value:.2f}",  # Col 7: sum of taxable_value (col 7 in data rows)
                '',  # Col 8: CGST rate (empty for totals, rates don't sum)
                f"{total_cgst_rs:.2f}",  # Col 9: sum of cgst_rs (col 9 in data rows)
                '',  # Col 10: SGST rate (empty for totals)
                f"{total_sgst_rs:.2f}",  # Col 11: sum of sgst_rs (col 11 in data rows)
                '',  # Col 12: IGST rate (empty for totals)
                f"{total_igst_rs:.2f}" if total_igst_rs > 0 else '',  # Col 13: sum of igst_rs (col 13 in data rows)
                f"{total_items_amount:.2f}"  # Col 14: sum of total_amount (col 14 in data rows)
            ])
        
        # Totals section (below items table)
        words_text = invoice_data.get('total_in_words', '')
        freight = invoice_data.get('freight_charges', 0)
        grand_total = invoice_data.get('grand_total', 0)
        rounded_total = grand_total - (sum(item.get('total_amount', 0) for item in items) if items else 0) - freight
        
        # Row: Challan Total value in words (left) and Freight Charges (right)
        main_table_data.append([
            'Challan Total value ( In Words) :', '', '', '', '', '', '', '', '', '', 'Freight Charges', '', '', '', f"{freight:.2f}"
        ])
        
        # Row: Words text (left) and Rounded off (right)
        main_table_data.append([
            words_text, '', '', '', '', '', '', '', '', '', 'Rounded off', '', '', '', f"{rounded_total:.2f}"
        ])
        
        # Row: Empty (left) and Total/Grand Total (right)
        main_table_data.append([
            '', '', '', '', '', '', '', '', '', '', 'Total', '', '', '', f"{grand_total:.2f}"
        ])
        
        # Blaster details section (empty row above removed)
        blaster_name = invoice_data.get('blaster_name', '')
        document_no = invoice_data.get('document_no', '')
        blaster_address = invoice_data.get('blaster_address', '')
        
        # Name of shot fire / Blaster with SENTHIL EXPLOSIVES on same row (moved 3 steps left, spanning cols 10-14 for centering)
        # Use Paragraph for center alignment
        senthil_paragraph = Paragraph('SENTHIL EXPLOSIVES', ParagraphStyle(
            'CustomCenter',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7,
            alignment=TA_CENTER
        ))
        main_table_data.append([
            'Name of the shot fire / Blaster : ' + blaster_name, '', '', '', '', '', '', '', '', '', senthil_paragraph, '', '', '', ''
        ])
        
        # Document No
        main_table_data.append([
            'Document No : ' + document_no, '', '', '', '', '', '', '', '', '', '', '', '', '', ''
        ])
        
        # Address with PARTNER on same row (moved 3 steps left, spanning cols 10-14 for centering)
        # Use Paragraph for center alignment
        partner_paragraph = Paragraph('PARTNER', ParagraphStyle(
            'CustomCenter',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7,
            alignment=TA_CENTER
        ))
        main_table_data.append([
            'Address: ' + blaster_address, '', '', '', '', '', '', '', '', '', partner_paragraph, '', '', '', ''
        ])
        
        # Create the single table - 170mm wide, 15 columns (0-14)
        # Column structure:
        # 0=S.No, 1=Description, 2=HSN, 3=Unit, 4=Qty, 5=Rate, 6=Total, 7=Taxable Value,
        # 8=CGST(merged)/Rate, 9=Rs., 10=SGST(merged)/Rate, 11=Rs.,
        # 12=IGST(merged)/Rate, 13=Rs., 14=TOTAL/Amount
        col_widths = [
            8*mm,   # 0: S.No
            33*mm,  # 1: Description (made slightly wider)
            12*mm,  # 2: HSN Code
            8*mm,   # 3: Unit
            9*mm,   # 4: Qty
            10*mm,  # 5: Rate
            10*mm,  # 6: Total
            11*mm,  # 7: Taxable Value
            7.5*mm, # 8: CGST (merged in row 1) / Rate (row 2) / cgst_rate% (data) (made slightly wider)
            7.5*mm, # 9: Rs. (row 2) / cgst_rs (data) (made slightly wider)
            7.5*mm, # 10: SGST (merged in row 1) / Rate (row 2) / sgst_rate% (data) (made slightly wider)
            7.5*mm, # 11: Rs. (row 2) / sgst_rs (data) (made slightly wider)
            7.5*mm, # 12: IGST (merged in row 1) / Rate (row 2) / igst_rate% (data) (made slightly wider)
            7.5*mm, # 13: Rs. (row 2) / igst_rs (data) (made slightly wider)
            13*mm   # 14: TOTAL (row 1) / Amount (row 2) / total_amount (data) (made slightly wider)
        ]
        # Adjust to total exactly 170mm
        total = sum(col_widths)
        if total != 170*mm:
            adjustment = (170*mm - total) / 15
            col_widths = [w + adjustment for w in col_widths]
        
        main_table = Table(main_table_data, colWidths=col_widths)
        
        # Calculate row indices dynamically
        # Fixed rows: 0-14 (title, company, invoice details, receiver details) = 15 rows
        # Row 14 is empty, so items start at row 15 (index 15)
        if items:
            items_header1 = items_start_row
            items_header2 = items_start_row + 1
            items_data_start = items_start_row + 2
            items_data_end = items_data_start + len(items) - 1
            items_totals_row = items_data_end + 2  # +1 for empty row, +1 for totals row
            totals_section_start = items_totals_row + 1
        else:
            # No items - totals section starts right after receiver details
            totals_section_start = 15  # Row 14 is empty, totals start at 15
        
        blaster_start = totals_section_start + 3  # 3 rows for totals section (empty row removed, so blaster_start is now 1 row earlier)
        last_row = len(main_table_data) - 1
        
        # Build base style list
        style_list = [
            # Basic formatting for entire table
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            
            # OUTER BOX - continuous border around ENTIRE table
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Title row (0) - DELIVERY CHALLAN (smaller font, reduced padding)
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),  # Reduced from 14
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('SPAN', (0, 0), (-1, 0)),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2),  # Reduced from 5
            ('TOPPADDING', (0, 0), (-1, 0), 2),  # Reduced from 5
            
            # Line below DELIVERY CHALLAN (row 0, bottom border)
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            
            # Company name row (1) - SENTHIL EXPLOSIVES
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 11),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('SPAN', (0, 1), (-1, 1)),
            
            # Company address rows (2-3) - Normal font (not bold), reduced spacing
            ('ALIGN', (0, 2), (-1, 3), 'CENTER'),
            ('SPAN', (0, 2), (-1, 2)),
            ('SPAN', (0, 3), (-1, 3)),
            ('FONTNAME', (0, 2), (-1, 3), 'Helvetica'),  # Normal font (not bold)
            ('BOTTOMPADDING', (0, 2), (-1, 2), 1),  # Reduced spacing
            ('TOPPADDING', (0, 3), (-1, 3), 1),  # Reduced spacing
            
            # Line below address section (row 3, bottom border)
            ('LINEBELOW', (0, 3), (-1, 3), 0.5, colors.black),
            
            # Invoice section (rows 4-6) - Updated layout
            # Row 4: E WAY BILL NO (col 0) + Mode of Transport (col 8) + Original checkbox (col 13-14)
            ('FONTNAME', (0, 4), (0, 4), 'Helvetica'),  # E WAY BILL NO (left side, row 4) - normal font
            ('ALIGN', (0, 4), (0, 4), 'LEFT'),
            ('FONTNAME', (8, 4), (8, 4), 'Helvetica'),  # Mode of Transport (right side, row 4) - normal font
            ('ALIGN', (8, 4), (8, 4), 'LEFT'),
            # Row 5: E WAY DOCUMENT NO (col 0) + Vehicle No (col 8) + Duplicate checkbox (col 13-14)
            ('FONTNAME', (0, 5), (0, 5), 'Helvetica'),  # E WAY DOCUMENT NO (left side, row 5) - normal font
            ('ALIGN', (0, 5), (0, 5), 'LEFT'),
            ('FONTNAME', (8, 5), (8, 5), 'Helvetica'),  # Vehicle No (right side, row 5) - normal font
            ('ALIGN', (8, 5), (8, 5), 'LEFT'),
            # Row 6: Invoice No (col 0) + Date of Supply (col 8) + Triplicate checkbox (col 13-14)
            ('FONTNAME', (0, 6), (0, 6), 'Helvetica-Bold'),  # Invoice No (left side, row 6) - BOLD
            ('ALIGN', (0, 6), (0, 6), 'LEFT'),  # Invoice No left aligned
            ('FONTNAME', (8, 6), (8, 6), 'Helvetica'),  # Date of Supply (right side, row 6) - normal font
            ('ALIGN', (8, 6), (8, 6), 'LEFT'),
            # Line separating invoice section from Details of Receiver (below row 6)
            ('LINEBELOW', (0, 6), (-1, 6), 0.5, colors.black),
            # Original checkbox - tick mark is in column 13, "Original" text in column 14 (row 4)
            ('VALIGN', (13, 4), (13, 4), 'MIDDLE'),  # Vertical alignment for tick mark
            ('ALIGN', (13, 4), (13, 4), 'CENTER'),  # Tick mark (checkbox) centered in its cell
            ('ALIGN', (14, 4), (14, 4), 'LEFT'),  # "Original" text left-aligned next to checkbox
            ('BOX', (13, 4), (13, 4), 0.5, colors.black),  # Box around the checkbox cell (column 13, row 4)
            ('BOTTOMPADDING', (13, 4), (13, 4), 2),
            ('TOPPADDING', (13, 4), (13, 4), 2),
            # Duplicate checkbox - tick mark is in column 13, "Duplicate" text in column 14 (row 5)
            ('VALIGN', (13, 5), (13, 5), 'MIDDLE'),  # Vertical alignment for tick mark
            ('ALIGN', (13, 5), (13, 5), 'CENTER'),  # Tick mark (checkbox) centered in its cell
            ('ALIGN', (14, 5), (14, 5), 'LEFT'),  # "Duplicate" text left-aligned next to checkbox
            ('BOX', (13, 5), (13, 5), 0.5, colors.black),  # Box around the checkbox cell (column 13, row 5)
            ('BOTTOMPADDING', (13, 5), (13, 5), 2),
            ('TOPPADDING', (13, 5), (13, 5), 2),
            # Triplicate checkbox - tick mark is in column 13, "Triplicate" text in column 14 (row 6)
            ('VALIGN', (13, 6), (13, 6), 'MIDDLE'),  # Vertical alignment for tick mark
            ('ALIGN', (13, 6), (13, 6), 'CENTER'),  # Tick mark (checkbox) centered in its cell
            ('ALIGN', (14, 6), (14, 6), 'LEFT'),  # "Triplicate" text left-aligned next to checkbox
            ('BOX', (13, 6), (13, 6), 0.5, colors.black),  # Box around the checkbox cell (column 13, row 6)
            ('BOTTOMPADDING', (13, 6), (13, 6), 2),
            ('TOPPADDING', (13, 6), (13, 6), 2),
            
            # Receiver Details header (row 7) - BOLD and larger font
            ('SPAN', (0, 7), (-1, 7)),
            ('FONTSIZE', (0, 7), (-1, 7), 10),  # Larger font size for header
            ('FONTNAME', (0, 7), (-1, 7), 'Helvetica-Bold'),  # BOLD for header
            
            # Receiver Details data rows (8-13) - Normal font (not bold, normal size), reduced spacing
            ('FONTSIZE', (0, 8), (-1, 13), 7),  # Normal font size (matches default)
            ('FONTNAME', (0, 8), (-1, 13), 'Helvetica'),  # Normal font (NOT bold) - explicitly set
            ('ALIGN', (0, 8), (-1, 13), 'LEFT'),
            ('BOTTOMPADDING', (0, 8), (-1, 13), 1),  # Reduced spacing between fields
            ('TOPPADDING', (0, 8), (-1, 13), 1),  # Reduced spacing between fields
            # State Code (row 11, column 9) - Normal font (not bold)
            ('ALIGN', (9, 11), (9, 11), 'LEFT'),
            ('FONTNAME', (9, 11), (9, 11), 'Helvetica'),  # Normal font (not bold)
            # GSTIN/Unique ID from invoice (row 12, column 9) - directly below State Code (adjacent row)
            ('ALIGN', (9, 12), (9, 12), 'LEFT'),
            # Place of Supply centered (row 13, column 5) - same row as customer GSTIN
            ('ALIGN', (5, 13), (5, 13), 'CENTER'),  # Place of Supply centered
            # Customer GSTIN (row 13, column 0) - same row as Place of Supply
            ('ALIGN', (0, 13), (0, 13), 'LEFT'),
            
            # Totals section (rows totals_section_start to totals_section_start+2) - reduced spacing
            ('FONTNAME', (0, totals_section_start), (0, totals_section_start), 'Helvetica-Bold'),
            ('FONTNAME', (10, totals_section_start), (10, totals_section_start), 'Helvetica-Bold'),
            ('FONTNAME', (10, totals_section_start+1), (10, totals_section_start+1), 'Helvetica-Bold'),
            ('FONTNAME', (10, totals_section_start+2), (10, totals_section_start+2), 'Helvetica-Bold'),
            ('ALIGN', (15, totals_section_start), (15, totals_section_start+2), 'RIGHT'),  # Amounts right aligned
            ('SPAN', (0, totals_section_start+1), (9, totals_section_start+1)),  # Words span multiple columns
            ('TOPPADDING', (0, totals_section_start), (-1, totals_section_start+2), 1),  # Reduced top padding
            ('BOTTOMPADDING', (0, totals_section_start), (-1, totals_section_start+2), 1),  # Reduced bottom padding
            
            # Blaster section (rows blaster_start to blaster_start+2) - reduced spacing
            ('FONTNAME', (0, blaster_start), (0, blaster_start+2), 'Helvetica'),
            ('TOPPADDING', (0, blaster_start), (-1, blaster_start+2), 1),  # Reduced top padding
            ('BOTTOMPADDING', (0, blaster_start), (-1, blaster_start+2), 1),  # Reduced bottom padding
            
            # Line above blaster section (separating totals from blaster)
            ('LINEABOVE', (0, blaster_start), (-1, blaster_start), 0.5, colors.black),
            
            # SENTHIL EXPLOSIVES (row blaster_start, columns 10-14) - same row as Name of shot fire, center-aligned (span for better centering)
            ('SPAN', (10, blaster_start), (14, blaster_start)),  # Span columns 10-14 for wider centered area
            ('VALIGN', (10, blaster_start), (10, blaster_start), 'MIDDLE'),
            # Paragraph object handles alignment internally, so no ALIGN needed
            
            # PARTNER (row blaster_start+2, columns 10-14) - same row as Address, center-aligned (span for better centering)
            ('SPAN', (10, blaster_start+2), (14, blaster_start+2)),  # Span columns 10-14 for wider centered area
            ('VALIGN', (10, blaster_start+2), (10, blaster_start+2), 'MIDDLE'),
            # Paragraph object handles alignment internally, so no ALIGN needed
        ]
        
        # Add items table styling only if items exist
        if items:
            # Items table headers (rows items_header1, items_header2)
            style_list.extend([
                ('FONTNAME', (0, items_header1), (-1, items_header2), 'Helvetica-Bold'),
                ('FONTSIZE', (0, items_header1), (-1, items_header1), 7),
                ('FONTSIZE', (0, items_header2), (-1, items_header2), 6),
                ('ALIGN', (0, items_header1), (-1, items_header2), 'CENTER'),
                ('VALIGN', (0, items_header1), (-1, items_header2), 'MIDDLE'),
                # Merge CGST, SGST, IGST headers in row 1
                # Row 1: CGST(8), ''(9), SGST(10), ''(11), IGST(12), ''(13), TOTAL(14)
                # Row 2: Rate(8), Rs.(9), Rate(10), Rs.(11), Rate(12), Rs.(13), Amount(14)
                # Span each header over its two subcolumns (CGST, SGST, IGST span 2 columns each, TOTAL is single column)
                ('SPAN', (8, items_header1), (9, items_header1)),  # CGST spans 8-9 (2 columns for Rate and Rs)
                ('SPAN', (10, items_header1), (11, items_header1)),  # SGST spans 10-11 (2 columns for Rate and Rs)
                ('SPAN', (12, items_header1), (13, items_header1)),  # IGST spans 12-13 (2 columns for Rate and Rs)
                # TOTAL does not span - it's only at column 14
                # Grid borders for header rows
                ('GRID', (0, items_header1), (-1, items_header2), 0.5, colors.black),
                
                # Items data rows - center aligned, full grid
                ('ALIGN', (0, items_data_start), (-1, items_data_end), 'CENTER'),
                ('VALIGN', (0, items_data_start), (-1, items_data_end), 'MIDDLE'),
                ('FONTSIZE', (0, items_data_start), (-1, items_data_end), 7),
                ('GRID', (0, items_data_start), (-1, items_data_end), 0.5, colors.black),
                
                # Items totals row
                ('FONTNAME', (0, items_totals_row), (-1, items_totals_row), 'Helvetica-Bold'),
                ('ALIGN', (0, items_totals_row), (-1, items_totals_row), 'CENTER'),
                ('LINEABOVE', (0, items_totals_row), (-1, items_totals_row), 1, colors.black),
                ('GRID', (0, items_totals_row), (-1, items_totals_row), 0.5, colors.black),
            ])
        
        main_table.setStyle(TableStyle(style_list))
        
        return main_table
    
    def generate_multi_page_pdf(self, invoice_data_list: List[Dict], output_path: str):
        """
        Generate a single PDF with multiple pages, one page per customer
        This method generates individual PDFs first (using the exact same format as generate_pdf),
        then merges them into a single multi-page PDF to ensure perfect formatting match.
        """
        if PdfWriter is None or PdfReader is None:
            raise ImportError("pypdf or PyPDF2 is required for PDF merging. Please install it: pip install pypdf")
        
        # Create temporary directory for individual PDFs
        temp_dir = tempfile.mkdtemp()
        temp_pdf_files = []
        
        try:
            # Generate individual PDF for each customer (using exact same method as single PDF)
            for idx, invoice_data in enumerate(invoice_data_list):
                # Create temporary file for this customer's PDF
                temp_pdf_path = os.path.join(temp_dir, f"temp_invoice_{idx}.pdf")
                temp_pdf_files.append(temp_pdf_path)
                
                # Generate PDF using the exact same method as single PDF generation
                self.generate_pdf(invoice_data, temp_pdf_path)
            
            # Merge all PDFs into one
            pdf_writer = PdfWriter()
            
            for temp_pdf_path in temp_pdf_files:
                if os.path.exists(temp_pdf_path):
                    pdf_reader = PdfReader(temp_pdf_path)
                    # Add all pages from this PDF
                    for page_num in range(len(pdf_reader.pages)):
                        pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Write merged PDF to output path
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
        
        finally:
            # Clean up temporary files
            for temp_pdf_path in temp_pdf_files:
                try:
                    if os.path.exists(temp_pdf_path):
                        os.remove(temp_pdf_path)
                except Exception:
                    pass
            
            # Remove temporary directory
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass