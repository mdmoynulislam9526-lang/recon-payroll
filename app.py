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
    
    # ২৬ দিনের হিসেবে অনুপস্থিতির কারণে কেটে নেওয়া বেতন
    per_day_salary = gross_salary / 26
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
    c.drawString(25, y_pos, f"  - Absent Deduction ({absent_days} Days / 26)")
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
    
    # --- 🎯 সিল ও সিগনেচার একদম ডানপাশে ও কাছাকাছি আনার ফাইনাল ফিক্স ---
    sig_y = 50
    
    # সিলটিকে একদম ডান কোনায় (width - 85) আনা হয়েছে এবং উচ্চতা একটু বাড়ানো হয়েছে (sig_y + 12)
    if os.path.exists("seal.png"):
