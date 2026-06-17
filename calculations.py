import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def calculate_salary_breakdown(base_salary, absent_days, fine_amount, category, present_days):
    """
    আপনার বেতন হিসাব করার মূল লজিক (যা আগে ছিল)
    """
    # আপনার আগের নিয়মে হিসাব-নিকাশ
    if category == 'Worker (Daily Basis)':
        # ডেইলি বেসিস ওয়ার্কারদের জন্য উপস্থিত দিনের ওপর সরাসরি বেতন
        gross_salary = base_salary * present_days
        absent_cut = 0.0
    else:
        # পার্মানেন্ট স্টাফদের জন্য ২৬ দিন হিসাব করে এবসেন্ট কাটা
        gross_salary = base_salary
        if present_days < 26 and absent_days > 0:
            absent_cut = (base_salary / 26) * absent_days
        else:
            absent_cut = 0.0

    net_payable = gross_salary - absent_cut - fine_amount
    return gross_salary, 0.0, 0.0, 0.0, absent_cut, net_payable, 0.0


def generate_pdf_bytes(employee_data, full_month, absent_days, fine_amount, present_days, pdf_buf):
    """
    ১০০% ফিক্সড পিডিএফ জেনারেটর (সার্ভারে লোগো ও সিগনেচারসহ)
    """
    eid, name, designation, category, department, final_payable = employee_data
    
    # --- 🚀 সার্ভারের জন্য ইমেজ পাথ চেনার ম্যাজিক ট্রিক ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(current_dir, "logo.png")
    sig_path = os.path.join(current_dir, "signature.png")
    
    # পিডিএফ ডকুমেন্ট সেটআপ
    doc = SimpleDocTemplate(pdf_buf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#1F4E78'), alignment=1)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=11, leading=14, alignment=1, textColor=colors.HexColor('#555555'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)
    bold_style = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')

    # ১. কোম্পানি লোগো যোগ করা (যদি গিটহাবে logo.png ফাইলটি থাকে)
    if os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=70, height=45)
            logo_img.hAlign = 'CENTER'
            story.append(logo_img)
            story.append(Spacer(1, 5))
        except Exception:
            pass # কোনো কারণে ইমেজ ক্রাশ করলে পিডিএফ যেন বন্ধ না হয়

    # কোম্পানি হেডার টেক্সট
    story.append(Paragraph("<b>RECON LABORATORIES LTD.</b>", title_style))
    story.append(Paragraph(f"Monthly Salary Pay Slip — {full_month}", sub_style))
    story.append(Spacer(1, 20))
    
    # ২. কর্মচারীর তথ্যের টেবিল
    info_data = [
        [Paragraph(f"<b>Employee ID:</b> {eid}", body_style), Paragraph(f"<b>Department:</b> {department}", body_style)],
        [Paragraph(f"<b>Name:</b> {name}", body_style), Paragraph(f"<b>Category:</b> {category}", body_style)],
        [Paragraph(f"<b>Designation:</b> {designation}", body_style), Paragraph(f"<b>Period:</b> {full_month}", body_style)]
    ]
    t_info = Table(info_data, colWidths=[260, 260])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 20))
    
    # ৩. ফাইনাল স্যালারি ব্রেকডাউন টেবিল
    calc_salary = final_payable  # সিম্পল রিপ্রেজেন্টেশন
    
    breakdown_data = [
        [Paragraph("<b>Description</b>", bold_style), Paragraph("<b>Amount (BDT)</b>", bold_style)],
        [Paragraph("Attendance Status", body_style), Paragraph(f"Present: {present_days} Days | Absent: {absent_days} Days", body_style)],
        [Paragraph("Total Penalty / Fine Deducted", body_style), Paragraph(f"Tk {fine_amount:,.2f}", body_style)],
        [Paragraph("<b>Net Payable Salary (Final)</b>", bold_style), Paragraph(f"<b>Tk {final_payable:,.2f}</b>", bold_style)]
    ]
    
    t_breakdown = Table(breakdown_data, colWidths=[320, 200])
    t_breakdown.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2F5597')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F2F4F7')),
    ]))
    story.append(t_breakdown)
    story.append(Spacer(1, 40))
    
    # ৪. সিগনেচার সেকশন (যদি গিটহাবে signature.png ফাইলটি থাকে)
    sig_element = Paragraph("_______________________<br/><b>Authorized Signature</b>", body_style)
    
    if os.path.exists(sig_path):
        try:
            sig_img = Image(sig_path, width=90, height=35)
            sig_img.hAlign = 'LEFT'
            sig_data = [[sig_img], [sig_element]]
            t_sig = Table(sig_data, colWidths=[200])
            t_sig.setStyle(TableStyle([('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
            story.append(t_sig)
        except Exception:
            story.append(sig_element)
    else:
        story.append(sig_element)
        
    # PDF ফাইল বিল্ড করা
    doc.build(story)
