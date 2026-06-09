import streamlit as st
import sqlite3
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import base64

# ReportLab for PDF
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas

# Page configuration
st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("company_data.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT NOT NULL,
            salary REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("company_data.db", check_same_thread=False)

def calculate_salary_breakdown(gross_salary):
    basic = gross_salary / 1.6
    home_rent = basic * 0.40
    medical = basic * 0.10
    ta_da = basic * 0.10
    return basic, home_rent, medical, ta_da

# --- PDF GENERATION FUNCTION ---
def generate_pdf_bytes(emp_data, selected_month):
    emp_id, name, designation, gross_salary = emp_data
    basic, home_rent, medical, ta_da = calculate_salary_breakdown(float(gross_salary))
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
        ("Basic Salary", basic),
        ("Home Rent (40%)", home_rent),
        ("Medical Allowance (10%)", medical),
        ("TA / DA Allowance (10%)", ta_da)
    ]
    
    for desc, amt in items:
        c.drawString(25, y_pos, desc)
        c.drawRightString(width - 25, y_pos, f"{amt:,.2f}")
        y_pos -= 20
        
    # Net Payable
    c.line(20, y_pos + 10, width - 20, y_pos + 10)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25, y_pos - 5, "Net Payable")
    c.drawRightString(width - 25, y_pos - 5, f"{float(gross_salary):,.2f}")
    c.line(20, y_pos - 15, width - 20, y_pos - 15)
    
    # --- ONLY ONE SEAL & SIGNATURE AT BOTTOM ---
    sig_y = 60
    # মাস্ক 'auto' ব্যবহারের ফলে ছবির ব্যাকগ্রাউন্ড সাদা আসবে না, ট্রান্সপারেন্ট দেখাবে
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

col1, col2 = st.columns([1, 2])

# Left Side: Form to Add Employee
with col1:
    st.header("➕ Add New Employee")
    with st.form("employee_form", clear_on_submit=True):
        name = st.text_input("Employee Name")
        designation = st.text_input("Designation")
        salary = st.text_input("Total Salary (Tk)")
        submit_btn = st.form_submit_button("Add Employee")
        
        if submit_btn:
            if name == "" or designation == "" or salary == "":
                st.error("সব ঘর পূরণ করুন!")
            else:
                try:
                    salary_val = float(salary)
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO employees (name, designation, salary) VALUES (?, ?, ?)", (name, designation, salary_val))
                    conn.commit()
                    conn.close()
                    st.success(f"{name} সফলভাবে যুক্ত হয়েছেন!")
                except ValueError:
                    st.error("Salary সংখ্যা হতে হবে!")

# Right Side: View Database, Select Month & Actions
with col2:
    st.header("📋 Employee Database & Pay Slip")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees")
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
            select_y = st.selectbox("Select Year",
