import streamlit as st
import sqlite3
import os
from datetime import datetime
import base64
from io import BytesIO

# ReportLab for PDF
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas

# Page configuration
st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("payroll_v2.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees_new (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            designation TEXT NOT NULL,
            salary REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("payroll_v2.db", check_same_thread=False)

# ক্যালকুলেশন লজিক আরও নিখুঁত ও সুরক্ষিত করা হয়েছে
def calculate_salary_breakdown(gross_salary, absent_days, fine_amount):
    try:
        gross_salary = float(gross_salary)
        absent_days = int(absent_days)
        fine_amount = float(fine_amount)
    except ValueError:
        gross_salary = 0.0
        absent_days = 0
        fine_amount = 0.0

    basic = gross_salary / 1.6
    home_rent = basic * 0.40
    medical = basic * 0.10
    ta_da = basic * 0.10
    
    # অনুপস্থিতির কারণে বেতন কাটার একদম সঠিক হিসাব
    per_day_salary = gross_salary / 30
    absent_deduction = per_day_salary * absent_days
    total_deductions = absent_deduction + fine_amount
    net_payable = gross_salary - total_deductions
    
    return basic, home_rent, medical, ta_da, absent_deduction, net_payable

# --- PDF GENERATION FUNCTION ---
def generate_pdf_bytes(emp_data, selected_month, absent_days, fine_amount):
    emp_id, name, designation, gross_salary = emp_data
    basic, home_rent, medical, ta_da, absent_deduction, net_payable = calculate_salary_breakdown(gross_salary, absent_days, fine_amount)
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5
    
    # Header Logo
    if os.path.exists("logo.png"):
        c.drawImage("logo.png", 20, height - 75, width=width-40, height=55, mask='auto')
    else:
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, height - 40, "RECON LABORATORIES LTD")
        
    c.setLineWidth(1)
    c.line(20, height - 90, width - 20, height - 90)
    
    # Meta Info
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20, height - 110, f"Date: {current_date}")
    c.drawRightString(width - 20, height - 110, f"Month: {selected_month}")
    
    c.setFont("Helvetica", 10)
    c.drawString(20, height - 135, f"Employee ID : {emp_id}")
    c.drawString(20, height - 150, f"Name            : {name}")
    c.drawString(20, height - 165, f"Designation   : {designation}")
    
    c.line(20, height - 180, width - 20, height - 180)
    
    # Table Header
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(20, height - 205, width - 40, 20, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, height - 192, "Description")
    c.drawRightString(width - 25, height - 192, "Amount (Tk)")
    
    # Table Content
    c.setFont("Helvetica", 10)
    y_pos = height - 225
    items = [
        ("Gross/Basic Salary Structure", float(gross_salary)),
        ("  - Basic Salary Component", basic),
        ("  - Home Rent (40%)", home_rent),
        ("  - Medical Allowance (10%)", medical),
        ("  - TA / DA Allowance (10%)", ta_da),
    ]
    
    for desc, amt in items:
        c.drawString(25, y_pos, desc)
        c.drawRightString(width - 25, y_pos, f"{amt:,.2f}")
        y_pos -= 18
        
    # Deductions Section
    c.line(20, y_pos + 5, width - 20, y_pos + 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, y_pos - 5, "Deductions:")
    y_pos -= 15
    
    c.setFont("Helvetica", 10)
    c.drawString(25, y_pos, f"  - Absent Deduction ({absent_days} Days)")
    c.drawRightString(width - 25, y_pos, f"- {absent_deduction:,.2f}")
    y_pos -= 15
    
    c.drawString(25, y_pos, f"  - Penalty / Fine")
    c.drawRightString(width - 25, y_pos, f"- {fine_amount:,.2f}")
    y_pos -= 15
        
    # Net Payable
    c.line(20, y_pos + 5, width - 20, y_pos + 5)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25, y_pos - 10, "Net Payable Amount")
    c.drawRightString(width - 25, y_pos - 10, f"{net_payable:,.2f}")
    c.line(20, y_pos - 20, width - 20, y_pos - 20)
    
    # Seal & Signature
    sig_y = 55
    if os.path.exists("seal.png"):
        c.drawImage("seal.png", width - 180, sig_y, width=65, height=65, mask='auto')
    if os.path.exists("signature.png"):
        c.drawImage("signature.png", width - 130, sig_y + 15, width=90, height=35, mask='auto')
        
    c.line(width - 140, sig_y + 10, width - 20, sig_y + 10)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width - 80, sig_y - 2, "Authorized Sign")
    
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(20, 20, "Confidential & Generated Automatically.")
    
    c.showPage()
    c.save()
    
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

# --- WEB UI INTERFACE ---
st.title("💼 RECON LABORATORIES LTD - Payroll System")
st.markdown("---")

col1, col2 = st.columns([1.2, 2])

# --- LEFT SIDE: MANAGEMENT (ADD & REMOVE) ---
with col1:
    st.header("➕ Add New Employee")
    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("Employee ID (e.g., RECON-01)")
        name = st.text_input("Employee Name")
        designation = st.text_input("Designation")
        salary = st.text_input("Gross Salary (Tk)")
        submit_btn = st.form_submit_button("Add Employee")
        
        if submit_btn:
            if input_id == "" or name == "" or designation == "" or salary == "":
                st.error("সব ঘর পূরণ করুন!")
            else:
                try:
                    salary_val = float(salary)
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO employees_new (emp_id, name, designation, salary) VALUES (?, ?, ?, ?)", (input_id, name, designation, salary_val))
                    conn.commit()
                    conn.close()
                    st.success(f"ID: {input_id} সফলভাবে যুক্ত হয়েছেন!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("এই Employee IDটি ইতিমধ্যে ডাটাবেজে আছে!")
                except ValueError:
                    st.error("Salary সংখ্যা হতে হবে!")

    st.markdown("---")
    st.header("❌ Remove Employee")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, name FROM employees_new")
    del_rows = cursor.fetchall()
    conn.close()
    
    if del_rows:
        del_options = {f"{r[0]} - {r[1]}": r[0] for r in del_rows}
        selected_del_key = st.selectbox("Select Employee to Remove", list(del_options.keys()))
        if st.button("Delete Employee", type="primary", use_container_width=True):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees_new WHERE emp_id = ?", (del_options[selected_del_key],))
            conn.commit()
            conn.close()
            st.success("कर्मचारी সফলভাবে ডাটাবেজ থেকে মুছে ফেলা হয়েছে!")
            st.rerun()
    else:
        st.info("মুছে ফেলার মতো কোনো কর্মচারী নেই।")

# --- RIGHT SIDE: DATABASE & PAY SLIP CALCULATION ---
with col2:
    st.header("📋 Employee Database & Pay Slip")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees_new")
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        current_m_idx = int(datetime.now().strftime("%m")) - 1
        current_y = datetime.now().strftime("%Y")
        
        m_col, y_col = st.columns(2)
        with m_col:
            select_m = st.selectbox("Select Pay Slip Month", months_list, index=current_m_idx)
        with y_col:
            select_y = st.selectbox("Select Year", [str(y) for y in range(2024, 2031)], index=list(range(2024, 2031)).index(int(current_y)))
            
        full_selected_month = f"{select_m}, {select_y}"
        
        emp_options = {f"ID: {r[0]} | {r[1]}": r for r in rows}
        selected_emp_key = st.selectbox("Select Employee for Pay Slip", list(emp_options.keys()))
        selected_emp = emp_options[selected_emp_key]
        
        # গুরুত্বপূর্ণ ফিক্স: ইনপুট বক্সে 'key' ব্যবহার করা হয়েছে যাতে ডেটা হারিয়ে না যায়
        st.markdown("#### 🗓️ Attendance & Penalty Input")
        attn_col, fine_col = st.columns(2)
        with attn_col:
            absent_days = st.number_input("Absent Days (অনুপস্থিত দিন)", min_value=0, max_value=31, value=0, step=1, key="absent_input")
        with fine_col:
            fine_amount = st.number_input("Fine / Penalty (জরিমানা টাকা)", min_value=0.0, value=0.0, step=10.0, key="fine_input")
        
        st.markdown("---")
        st.subheader(f"📄 Pay Slip Preview ({full_selected_month})")
        
        # নতুন লাইভ ভ্যালু দিয়ে ক্যালকুলেশন
        b, hr, m, td, absent_deduction, net_payable = calculate_salary_breakdown(selected_emp[3], absent_days, fine_amount)
        
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.write(f"**Employee ID:** {selected_emp[0]}")
            st.write(f"**Employee Name:** {selected_emp[1]}")
            st.write(f"**Designation:** {selected_emp[2]}")
            st.write(f"**Gross Structure:** Tk {selected_emp[3]:,.2f}")
        with p_col2:
            st.write(f"**Absent Cut:** Tk {absent_deduction:,.2f}")
            st.write(f"**Fine/Penalty:** Tk {fine_amount:,.2f}")
            st.write(f"### **Net Payable:** Tk {net_payable:,.2f}")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # পিডিএফ জেনারেট করার সময় একদম লেটেস্ট ভ্যালু পুশ করা হচ্ছে
        pdf_bytes = generate_pdf_bytes(selected_emp, full_selected_month, absent_days, fine_amount)
        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            st.download_button(
                label="📥 Download Pay Slip (PDF)",
                data=pdf_bytes,
                file_name=f"PaySlip_{selected_emp[0]}_{select_m}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_download"
            )
        with act_col2:
            st.markdown(
                f'<a href="data:application/pdf;base64,{b64_pdf}" target="_blank" style="text-decoration:none;">'
                f'<button style="width:100%; height:38px; background-color:#ff4b4b; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🖨️ Open & Print Pay Slip</button></a>',
                unsafe_allow_html=True
            )
    else:
        st.info("বর্তমানে কোনো কর্মচারী যুক্ত নেই। বাম পাশের ফর্ম থেকে কর্মচারী যুক্ত করুন।")
