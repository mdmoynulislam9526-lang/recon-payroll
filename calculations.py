import os
from io import BytesIO
from reportlab.lib.pagesizes import A5  # 📄 Paper size standard A5 kora holo
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def calculate_salary_breakdown(base_salary, absent_days, fine_amount, category, present_days):
    """
    Employee salary calculation logic
    """
    if category == 'Worker (Daily Basis)':
        gross_salary = base_salary * present_days
        absent_cut = 0.0
    else:
        gross_salary = base_salary
        if present_days < 26 and absent_days > 0:
            absent_cut = (base_salary / 26) * absent_days
        else:
            absent_cut = 0.0

    net_payable = gross_salary - absent_cut - fine_amount
    return gross_salary, 0.0, 0.0, 0.0, absent_cut, net_payable, 0.0


def generate_pdf_bytes(employee_data, full_month, absent_days, fine_amount, present_days, pdf_buf):
    """
    ⚙️ Fixed PDF Generator: A5 Size, Proper Logo Aspect, Right Aligned Signature
    """
    eid, name, designation, category, department, final_payable = employee_data
    
    # Server path management
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(current_dir, "logo.png")
    sig_path = os.path.join(current_dir, "signature.png")
    
    # 📄 SimpleDocTemplate a pagesize=A5 ebong A5 er sathe khap khay emon margins (25) set kora holo
    doc = SimpleDocTemplate(pdf_buf, pagesize=A5, rightMargin=25, leftMargin=25, topMargin=20, bottomMargin=20)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=15, leading=18, textColor=colors.HexColor('#1F4E78'), alignment=1)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, leading=11, alignment=1, textColor=colors.HexColor('#555555'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=8.5, leading=12)
    bold_style = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')
    right_bold_style = ParagraphStyle('RightBold', parent=bold_style, alignment=2)

    # 🏢 1. Logo Section (Chepta hoba na, aspect ratio maintain hobe)
    if os.path.exists(logo_path):
        try:
            # Logo chepta rodh korte width=110 ebong properly scaling height=40 kora holo
            logo_img = Image(logo_path, width=110, height=40)
            logo_img.hAlign = 'CENTER'
            story.append(logo_img)
            story.append(Spacer(1, 4))
        except Exception:
            pass

    # Company Header info
    story.append(Paragraph("<b>RECON LABORATORIES LTD.</b>", title_style))
    story.append(Paragraph(f"Monthly Salary Pay Slip — {full_month}", sub_style))
    story.append(Spacer(1, 12))
    
    # 👥 2. Employee Info Table (A5 wide optimization - usable width approx 370)
    info_data = [
        [Paragraph(f"<b>Employee ID:</b> {eid}", body_style), Paragraph(f"<b>Department:</b> {department}", body_style)],
        [Paragraph(f"<b>Name:</b> {name}", body_style), Paragraph(f"<b>Category:</b> {category}", body_style)],
        [Paragraph(f"<b>Designation:</b> {designation}", body_style), Paragraph(f"<b>Period:</b> {full_month}", body_style)]
    ]
    t_info = Table(info_data, colWidths=[185, 185])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))
    
    # 📊 3. Financial Table Section (Optimized for A5 Paper layout)
    breakdown_data = [
        [Paragraph("<b>Description</b>", bold_style), Paragraph("<b>Amount / Details</b>", right_bold_style)],
        [Paragraph("Attendance Status", body_style), Paragraph(f"Present: {present_days} Days | Absent: {absent_days} Days", body_style)],
        [Paragraph("Total Penalty / Fine Deducted", body_style), Paragraph(f"Tk {fine_amount:,.2f}", body_style)],
        [Paragraph("<b>Net Payable Salary (Final)</b>", bold_style), Paragraph(f"<b>Tk {final_payable:,.2f}</b>", right_bold_style)]
    ]
    
    t_breakdown = Table(breakdown_data, colWidths=[210, 160])
    t_breakdown.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2F5597')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F2F4F7')),
    ]))
    story.append(t_breakdown)
    story.append(Spacer(1, 25))
    
    # ✍️ 4. Signature Section (Right Aligned structure for A5 Layout)
    sig_text = Paragraph("_______________________<br/><b>Authorized Signature</b>", body_style)
    
    # Signature box alignment right side a push korar jonno left side a khali space maintain kora holo
    if os.path.exists(sig_path):
        try:
            sig_img = Image(sig_path, width=85, height=30)
            sig_img.hAlign = 'RIGHT'
            # Left side high width black column wrapper data structure
            sig_data = [
                ["", sig_img],
                ["", sig_text]
            ]
            t_sig = Table(sig_data, colWidths=[230, 140])
            t_sig.setStyle(TableStyle([
                ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2)
            ]))
            story.append(t_sig)
        except Exception:
            # Falling safety if image rendering fails
            t_sig_fallback = Table([["", sig_text]], colWidths=[230, 140])
            t_sig_fallback.setStyle(TableStyle([('ALIGN', (1,0), (1,-1), 'RIGHT')]))
            story.append(t_sig_fallback)
    else:
        t_sig_fallback = Table([["", sig_text]], colWidths=[230, 140])
        t_sig_fallback.setStyle(TableStyle([('ALIGN', (1,0), (1,-1), 'RIGHT')]))
        story.append(t_sig_fallback)
        
    # Build A5 document PDF stream
    doc.build(story)
