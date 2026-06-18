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
    ⚙️ Updated PDF Generator: Dynamic Logo Scale, No Company Text, Tight Signature with Seal
    """
    eid, name, designation, category, department, final_payable = employee_data
    
    # Server path management
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(current_dir, "logo.png")
    sig_path = os.path.join(current_dir, "signature.png")
    seal_path = os.path.join(current_dir, "seal.png")  # Seal file path definition
    
    # 📄 SimpleDocTemplate A5 size ebong layout safe margin (25)
    doc = SimpleDocTemplate(pdf_buf, pagesize=A5, rightMargin=25, leftMargin=25, topMargin=15, bottomMargin=15)
    story = []
    
    styles = getSampleStyleSheet()
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, leading=12, alignment=1, textColor=colors.HexColor('#1F4E78'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=8.5, leading=12)
    bold_style = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')
    right_bold_style = ParagraphStyle('RightBold', parent=bold_style, alignment=2)

    # 🏢 1. Logo Section (Boro ebong un-stretched/un-squeezed proper aspect ratio setup)
    if os.path.exists(logo_path):
        try:
            # Logo boro korte width=180 ebong width onujayi safe proportional height=55 set kora holo
            logo_img = Image(logo_path, width=180, height=55)
            logo_img.hAlign = 'CENTER'
            story.append(logo_img)
            story.append(Spacer(1, 4))
        except Exception:
            pass

    # Header text theke company name bad deya holo, shudhu Period ta asbe
    story.append(Paragraph(f"<b>Monthly Salary Pay Slip — {full_month}</b>", sub_style))
    story.append(Spacer(1, 15))
    
    # 👥 2. Employee Info Table (A5 wide optimization)
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
    story.append(Spacer(1, 30))
    
    # ✍️ 4. Signature & Seal Section (Daan dike nikhut alignment ebong pashapashi thakar setup)
    sig_text = Paragraph("_______________________<br/><b>Authorized Signature</b>", body_style)
    
    # Signature row images processing loop
    sig_elements = []
    
    # Custom tight inner table to hold signature and seal side-by-side or closely aligned
    inner_sig_data = []
    
    # Seal and Signature graphic processing inside right panel
    has_sig = os.path.exists(sig_path)
    has_seal = os.path.exists(seal_path)
    
    # Render box parameters based on availability
    if has_sig or has_seal:
        row_imgs = []
        if has_seal:
            try:
                seal_img = Image(seal_path, width=45, height=45)
                row_imgs.append(seal_img)
            except Exception: pass
        if has_sig:
            try:
                sig_img = Image(sig_path, width=80, height=30)
                row_imgs.append(sig_img)
            except Exception: pass
            
        # Puts images in a direct grid line row if both exist, otherwise simple element
        if len(row_imgs) == 2:
            inner_sig_data.append([row_imgs[0], row_imgs[1]])
        elif len(row_imgs) == 1:
            inner_sig_data.append(["", row_imgs[0]])
        else:
            inner_sig_data.append(["", ""])
    else:
        inner_sig_data.append(["", ""])
        
    inner_sig_data.append(["", sig_text]) # Bottom text insertion
    
    # Parent block wrapper table to strictly force layout on the RIGHT SIDE (colWidths customized to avoid wide gaps)
    t_inner = Table(inner_sig_data, colWidths=[65, 110])
    t_inner.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1)
    ]))

    # Main structure placement grid: Left 195 units blank, Right 175 units takes the inner signature module
    t_final_sig_block = Table([["", t_inner]], colWidths=[195, 175])
    t_final_sig_block.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM')
    ]))
    
    story.append(t_final_sig_block)
        
    # Build A5 document PDF stream
    doc.build(story)
