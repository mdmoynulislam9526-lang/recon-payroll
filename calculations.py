import os
from datetime import datetime
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas

def calculate_salary_breakdown(gross_salary, absent_days, fine_amount, category, present_days=0):
    try:
        gross_salary = float(gross_salary)
        absent_days = int(absent_days)
        fine_amount = float(fine_amount)
        present_days = int(present_days)
    except ValueError:
        gross_salary, absent_days, fine_amount, present_days = 0.0, 0, 0.0, 0

    if category == 'Worker (Daily Basis)':
        total_earnings = gross_salary * present_days
        basic = total_earnings / 1.6
        home_rent = basic * 0.40
        medical = basic * 0.10
        ta_da = basic * 0.10
        absent_deduction = 0.0
        net_payable = total_earnings - fine_amount
    else:
        total_earnings = gross_salary
        basic = gross_salary / 1.6
        home_rent = basic * 0.40
        medical = basic * 0.10
        ta_da = basic * 0.10
        per_day_salary = gross_salary / 26
        absent_deduction = per_day_salary * absent_days
        net_payable = gross_salary - (absent_deduction + fine_amount)
    
    return basic, home_rent, medical, ta_da, absent_deduction, net_payable, total_earnings

def generate_pdf_bytes(emp_data, selected_month, absent_days, fine_amount, present_days, buffer):
    emp_id, name, designation, category, department, gross_salary = emp_data
    b, hr, m, td, absent_deduction, net_payable, total_earnings = calculate_salary_breakdown(
        gross_salary, absent_days, fine_amount, category, present_days
    )
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    c = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    
    if os.path.exists("logo.png"):
        c.drawImage("logo.png", 20, height - 75, width=width-40, height=55, mask='auto')
    else:
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, height - 40, "RECON LABORATORIES LTD")
        
    c.setLineWidth(1)
    c.line(20, height - 90, width - 20, height - 90)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20, height - 110, f"Date: {current_date}")
    c.drawRightString(width - 20, height - 110, f"Month: {selected_month}")
    
    c.setFont("Helvetica", 10)
    c.drawString(20, height - 135, f"Employee ID : {emp_id}")
    c.drawString(20, height - 150, f"Name            : {name}")
    c.drawString(20, height - 165, f"Department   : {department}")
    c.drawString(20, height - 180, f"Category       : {category}")
    c.drawString(20, height - 195, f"Designation   : {designation}")
    
    c.line(20, height - 210, width - 20, height - 210)
    
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(20, height - 235, width - 40, 20, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, height - 222, "Description")
    c.drawRightString(width - 25, height - 222, "Amount (Tk)")
    
    c.setFont("Helvetica", 10)
    y_pos = height - 255
    
    if category == 'Worker (Daily Basis)':
        items = [
            (f"Total Wage ({present_days} Days x {gross_salary:,.2f})", total_earnings),
            ("  - Basic Component Share", b),
            ("  - House Rent Component", hr),
            ("  - Allowances & Medical", m + td),
        ]
    else:
        items = [
            ("Gross/Basic Salary Structure", float(gross_salary)),
            ("  - Basic Salary Component", b),
            ("  - Home Rent (40%)", hr),
            ("  - Medical Allowance (10%)", m),
            ("  - TA / DA Allowance (10%)", td),
        ]
    
    for desc, amt in items:
        c.drawString(25, y_pos, desc)
        c.drawRightString(width - 25, y_pos, f"{amt:,.2f}")
        y_pos -= 18
        
    c.line(20, y_pos + 5, width - 20, y_pos + 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, y_pos - 5, "Deductions:")
    y_pos -= 15
    
    if category != 'Worker (Daily Basis)':
        c.drawString(25, y_pos, f"  - Absent Deduction ({absent_days} Days / 26)")
        c.drawRightString(width - 25, y_pos, f"- {absent_deduction:,.2f}")
        y_pos -= 15
    
    c.drawString(25, y_pos, f"  - Penalty / Fine")
    c.drawRightString(width - 25, y_pos, f"- {fine_amount:,.2f}")
    y_pos -= 15
        
    c.line(20, y_pos + 5, width - 20, y_pos + 5)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25, y_pos - 10, "Net Payable Amount")
    c.drawRightString(width - 25, y_pos - 10, f"{net_payable:,.2f}")
    c.line(20, y_pos - 20, width - 20, y_pos - 20)
    
    sig_y = 50
    if os.path.exists("seal.png"):
        c.drawImage("seal.png", width - 85, sig_y + 12, width=60, height=60, mask='auto')
    if os.path.exists("signature.png"):
        c.drawImage("signature.png", width - 135, sig_y + 18, width=80, height=30, mask='auto')
        
    c.line(width - 140, sig_y + 10, width - 20, sig_y + 10)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width - 80, sig_y - 2, "Authorized Sign")
    
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(20, 20, "Confidential & Generated Automatically.")
    
    c.showPage()
    c.save()
