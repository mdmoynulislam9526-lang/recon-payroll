import os
from io import BytesIO
from reportlab.lib.pagesizes import A5
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def calculate_salary_breakdown(base_salary, absent_days, fine_amount, category, present_days, advanced_payment=0.0):
    """
    বেতন, হাউজ রেন্ট, মেডিকেল এবং অ্যাডভান্সড পেমেন্ট হিসাব করার মূল লজিক
    """
    if category == 'Worker (Daily Basis)':
        gross_salary = base_salary * present_days
        absent_cut = 0.0
        house_rent = 0.0
        medical_allowance = 0.0
    else:
        gross_salary = base_salary
        if present_days < 26 and absent_days > 0:
            absent_cut = (base_salary / 26) * absent_days
        else:
            absent_cut = 0.0
        
        # মূল বেতনের ৩০% হাউজ রেন্ট এবং ১০% মেডিকেল
        house_rent = base_salary * 0.30
        medical_allowance = base_salary * 0.10

    # ফাইনাল পেঅ্যাবল = গ্রস - এবসেন্ট - ফাইন - অগ্রিম বা অ্যাডভান্সড
    net_payable = gross_salary - absent_cut - fine_amount - advanced_payment
    return gross_salary, house_rent, medical_allowance, 0.0, absent_cut, net_payable, advanced_payment


def generate_pdf_bytes(employee_data, full_month, absent_days, fine_amount, present_days, pdf_buf):
    """
    A5 সাইজ পিডিএফ: পাশে লম্বা লোগো, কাছাকাছি সিল-সিগনেচার এবং অ্যাডভান্সড পেমেন্টসহ
    """
    # ডাটা আনপ্যাক করা (app.py থেকে ৮টি ভ্যালু আসবে)
    eid, name, designation, category, department, house_rent, medical_allowance, advanced_payment, final_payable = employee_data
    
    # সার্ভার পাথ ম্যানেজমেন্ট
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(current_dir, "logo.png")
    sig_path = os.path.join(current_dir, "signature.png")
    seal_path = os.path.join(current_dir, "seal.png")
    
    doc = SimpleDocTemplate(pdf_buf, pagesize=A5, rightMargin=25, leftMargin=25, topMargin=15, bottomMargin=15)
    story = []
    
    styles = getSampleStyleSheet()
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, leading=12, alignment=1, textColor=colors.HexColor('#1F4E78'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=8.5, leading=12)
    bold_style = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')
    right_bold_style = ParagraphStyle('RightBold', parent=bold_style, alignment=2)

    # 🏢 ১. লোগো সেকশন (পাশে লম্বা করা হয়েছে)
    if os.path.exists(logo_path):
        try:
            # লোগো পাশে লম্বা করার জন্য width=200 এবং height=50 করা হলো
            logo_img = Image(logo_path, width=200, height=50)
            logo_img.hAlign = 'CENTER'
            story.append(logo_img)
            story.append(Spacer(1, 4))
        except Exception:
            pass

    story.append(Paragraph(f"<b>Monthly Salary Pay Slip — {full_month}</b>", sub_style))
    story.append(Spacer(1, 10))
    
    # 👥 ২. কর্মচারীর তথ্য টেবিল
    info_data = [
        [Paragraph(f"<b>Employee ID:</b> {eid}", body_style), Paragraph(f"<b>Department:</b> {department}", body_style)],
        [Paragraph(f"<b>Name:</b> {name}", body_style), Paragraph(f"<b>Category:</b> {category}", body_style)],
        [Paragraph(f"<b>Designation:</b> {designation}", body_style), Paragraph(f"<b>Period:</b> {full_month}", body_style)]
    ]
    t_info = Table(info_data, colWidths=[185, 185])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 10))
    
    # 📊 ৩. ফাইনান্সিয়াল টেবিল (সবগুলো এলাউন্স এবং অ্যাডভান্সড পেমেন্টসহ)
    # ক্যাটাগরি অনুযায়ী এবসেন্ট কাট হিসাবের জন্য
    if category == 'Worker (Daily Basis)':
        absent_cut = 0.0
    else:
        base_estimate = final_payable + fine_amount + advanced_payment
        absent_cut = (base_estimate / 26) * absent_days if present_days < 26 and absent_days > 0 else 0.0

    breakdown_data = [
        [Paragraph("<b>Description</b>", bold_style), Paragraph("<b>Amount / Details</b>", right_bold_style)],
        [Paragraph("Attendance Status", body_style), Paragraph(f"Present: {present_days} Days | Absent: {absent_days} Days", body_style)],
        [Paragraph("House Rent Allowance", body_style), Paragraph(f"Tk {house_rent:,.2f}", body_style)],
        [Paragraph("Medical Allowance", body_style), Paragraph(f"Tk {medical_allowance:,.2f}", body_style)],
        [Paragraph("Absent Penalty Cut", body_style), Paragraph(f"Tk {absent_cut:,.2f}", body_style)],
        [Paragraph("Total Penalty / Fine Deducted", body_style), Paragraph(f"Tk {fine_amount:,.2f}", body_style)],
        [Paragraph("Advanced Payment (Deduction)", bold_style), Paragraph(f"Tk {advanced_payment:,.2f}", body_style)],
        [Paragraph("<b>Net Payable Salary (Final)</b>", bold_style), Paragraph(f"<b>Tk {final_payable:,.2f}</b>", right_bold_style)]
    ]
    
    t_breakdown = Table(breakdown_data, colWidths=[210, 160])
    t_breakdown.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2F5597')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F2F4F7')),
    ]))
    story.append(t_breakdown)
    story.append(Spacer(1, 20))
    
    # ✍️ ৪. সিগনেচার ও সিল সেকশন (খুব কাছাকাছি আনা হয়েছে এবং ড্যাশ লাইন ফিক্সড)
    sig_text = Paragraph("<font size='7'>_______________________</font><br/><b>Authorized Signature</b>", body_style)
    
    inner_sig_data = []
    has_sig = os.path.exists(sig_path)
    has_seal = os.path.exists(seal_path)
    
    if has_sig or has_seal:
        row_imgs = []
        if has_seal:
            try:
                # সিলটিকে সিগনেচারের ঠিক বামে সুন্দর সাইজে বসানোর জন্য
                seal_img = Image(seal_path, width=45, height=45)
                row_imgs.append(seal_img)
            except Exception: pass
        if has_sig:
            try:
                sig_img = Image(sig_path, width=80, height=30)
                row_imgs.append(sig_img)
            except Exception: pass
            
        if len(row_imgs) == 2:
            inner_sig_data.append([row_imgs[0], row_imgs[1]])
        elif len(row_imgs) == 1:
            inner_sig_data.append(["", row_imgs[0]])
        else:
            inner_sig_data.append(["", ""])
    else:
        inner_sig_data.append(["", ""])
        
    inner_sig_data.append(["", sig_text])
    
    # সিল এবং সিgনেচার যাতে দূরে না যায়, তাই টেবিল উইডথ কমিয়ে আনা হয়েছে (৫৫ এবং ১১০)
    t_inner = Table(inner_sig_data, colWidths=[55, 110])
    t_inner.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1)
    ]))

    # পুরো ব্লকটিকে ডানপাশে পুশ করার মেইন টেবিল
    t_final_sig_block = Table([["", t_inner]], colWidths=[205, 165])
    t_final_sig_block.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM')
    ]))
    
    story.append(t_final_sig_block)
    doc.build(story)
