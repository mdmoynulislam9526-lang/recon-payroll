import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def calculate_salary_breakdown(base_salary, absent_days, fine_amount, category, present_days=26):
    """
    RECON Laboratories Ltd - Payroll Calculation Engine
    """
    # ১. টোটাল আর্নিং বা বেস স্যালারি নির্ধারণ
    total_earnings = base_salary
    
    # ২. ডেইলি বেসিস কর্মীদের জন্য স্পেশাল অনুপস্থিতি কর্তন (Absent Cut) লজিক
    if category == 'Worker (Daily Basis)':
        # এখানে base_salary হলো পার-ডে রেট (Daily Wage Rate)
        # মোট উপার্জন = উপস্থিত দিন x ডেইলি রেট
        actual_earned = base_salary * present_days
        # অনুপস্থিতি কর্তন = অনুপস্থিত দিন x ডেইলি রেট
        absent_deduction = base_salary * absent_days
        # টোটাল আর্নিং হিসেবে দেখানোর জন্য (উপস্থিত + অনুপস্থিত দিন) অর্থাৎ ফুল মাসের বেইজ টাকা
        total_earnings = base_salary * (present_days + absent_days)
    else:
        # পার্মানেন্ট, অফিসার ও ম্যানেজারদের জন্য ২৬ দিন বেস ধরে অনুপস্থিতি কর্তন
        daily_rate = base_salary / 26
        absent_deduction = daily_rate * absent_days
        actual_earned = base_salary - absent_deduction

    # ৩. ফাইন বা জরিমানা যুক্ত করা
    total_deductions = absent_deduction + fine_amount
    
    # ৪. নেট পেয়েবল হিসাব (ট্যাক্স বা প্রভিডেন্ট ফান্ড আপাতত ০)
    tax_deduction = 0.0
    pf_deduction = 0.0
    net_payable = actual_earned - fine_amount

    # কোনো কারণে হিসাব মাইনাসে গেলে তা ০ করে দেওয়া
    if net_payable < 0:
        net_payable = 0.0

    return base_salary, tax_deduction, pf_deduction, total_deductions, absent_deduction, net_payable, total_earnings


def generate_pdf_bytes(emp_tuple, month_str, absent_days, fine_amount, present_days, buffer):
    """
    Generates a professional PDF pay slip into the provided bytes buffer.
    """
    emp_id, name, designation, category, department, base_salary = emp_tuple
    
    # লাইভ ক্যালকুলেশন রান করা
    b_sal, tax, pf, t_ded, ab_cut, net_p, t_earn = calculate_salary_breakdown(
        base_salary, absent_days, fine_amount, category, present_days
    )

    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # কাস্টম স্টাইলস
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#1A365D"), alignment=1)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#4A5568"), alignment=1)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor("#2B6CB0"), spaceBefore=10, spaceAfter=5)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#2D3748"))
    bold_body = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')

    # হেডার অংশ
    story.append(Paragraph("RECON LABORATORIES LTD.", title_style))
    story.append(Paragraph("Factory: Sreepur, Gazipur, Bangladesh", subtitle_style))
    story.append(Paragraph(f"<b>PAY SLIP FOR THE MONTH OF:</b> {month_str.upper()}", subtitle_style))
    story.append(Spacer(1, 15))
    
    # কর্মচারী পরিচিতি টেবিল
    info_data = [
        [Paragraph(f"<b>Employee ID:</b> {emp_id}", body_style), Paragraph(f"<b>Name:</b> {name}", body_style)],
        [Paragraph(f"<b>Designation:</b> {designation}", body_style), Paragraph(f"<b>Department:</b> {department}", body_style)],
        [Paragraph(f"<b>Category:</b> {category}", body_style), Paragraph(f"<b>Attendance Base:</b> {present_days + absent_days if category=='Worker (Daily Basis)' else 26} Days", body_style)]
    ]
    info_table = Table(info_data, colWidths=[200, 320])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    # স্যালারি ব্রেকডাউন টেবিল
    story.append(Paragraph("Salary & Deductions Breakdown", section_style))
    
    if category == 'Worker (Daily Basis)':
        earnings_title = "Dynamic Monthly Base (Rate x Total Days)"
        rate_label = f"Daily Wage Rate: Tk {base_salary:,.2f}"
    else:
        earnings_title = "Gross Base Salary"
        rate_label = f"Monthly Fixed: Tk {base_salary:,.2f}"

    breakdown_data = [
        [Paragraph("<b>Description</b>", bold_body), Paragraph("<b>Earnings (Tk)</b>", bold_body), Paragraph("<b>Deductions (Tk)</b>", bold_body)],
        [Paragraph(earnings_title, body_style), Paragraph(f"{t_earn:,.2f}", body_style), Paragraph("-", body_style)],
        [Paragraph(f"Absent Deduction ({absent_days} Days)", body_style), Paragraph("-", body_style), Paragraph(f"{ab_cut:,.2f}", body_style)],
        [Paragraph(f"Fine / Penalty", body_style), Paragraph("-", body_style), Paragraph(f"{fine_amount:,.2f}", body_style)],
        [Paragraph("<b>Total</b>", bold_body), Paragraph(f"<b>{t_earn:,.2f}</b>", bold_body), Paragraph(f"<b>{t_ded:,.2f}</b>", bold_body)],
        [Paragraph(f"<b>NET PAYABLE SALARY ({rate_label})</b>", bold_body), Paragraph(f"<b>Tk {net_p:,.2f}</b>", bold_body), Paragraph("", body_style)]
    ]
    
    bd_table = Table(breakdown_data, colWidths=[260, 130, 130])
    bd_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0,-2), (-1,-1), colors.HexColor("#EDF2F7")),
        ('LINEABOVE', (0,-2), (-1,-2), 1.5, colors.HexColor("#1A365D")),
        ('SPAN', (0,-1), (1,-1)),
    ]))
    
    # হেডার টেক্সট হোয়াইট করার জন্য কাস্টম ফিক্স
    for i in range(3):
        breakdown_data[0][i].style.textColor = colors.white

    story.append(bd_table)
    story.append(Spacer(1, 40))
    
    # সিগনেচার লাইন
    sig_data = [
        [Paragraph("____________________________<br/><b>Prepared By (Accounts)</b>", body_style), 
         Paragraph("____________________________<br/><b>Approved By (Management)</b>", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(sig_table)

    doc.build(story)
