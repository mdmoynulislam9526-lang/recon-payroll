import streamlit as st
import sqlite3
import os
from datetime import datetime
import base64
from io import BytesIO
import pandas as pd  # স্যালারি শিটের এক্সেল তৈরির জন্য

# ReportLab for PDF
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas

# Page configuration
st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("payroll_v5.db", check_same_thread=False)
    cursor = conn.cursor()
    # এখানে department যুক্ত করে নতুন টেবিল তৈরি করা হয়েছে
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees_final_version (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            designation TEXT NOT NULL,
            category TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("payroll_v5.db", check_same_thread=False)

def calculate_salary_breakdown(gross_salary, absent_days, fine_amount, category, present_days=0):
    try:
        gross_salary = float(gross_salary)
        absent_days = int(absent_days)
        fine_amount = float(fine_amount)
        present_days = int(present_days)
    except ValueError:
        gross_salary = 0.0
        absent_days = 0
        fine_amount = 0.0
        present_days = 0

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

# --- PDF GENERATION FUNCTION ---
def generate_pdf_bytes(emp_data, selected_month, absent_days, fine_amount, present_days):
    emp_id, name, designation, category, department, gross_salary = emp_data
    basic, home_rent, medical, ta_da, absent_deduction, net_payable, total_earnings = calculate_salary_breakdown(
        gross_salary, absent_days, fine_amount, category, present_days
    )
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    buffer = BytesIO()
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
            (f"Total Wage ({present_days} Days Worked x {gross_salary:,.2f})", total_earnings),
            ("  - Basic Component Share", basic),
            ("  - House Rent Component", home_rent),
            ("  - Allowances & Medical", medical + ta_da),
        ]
    else:
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
        
    c.line(20, y_pos + 5, width - 20, y_pos + 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, y_pos - 5, "Deductions:")
    y_pos -= 15
    
    c.setFont("Helvetica", 10)
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
    
    return buffer.getvalue()

# --- WEB UI INTERFACE ---
st.title("💼 RECON LABORATORIES LTD - Professional Payroll System")
st.markdown("---")

col1, col2 = st.columns([1.2, 2])

# --- LEFT SIDE: MANAGEMENT ---
with col1:
    st.header("➕ Add New Person")
    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("ID (e.g., RECON-M01, RECON-W05)")
        name = st.text_input("Name")
        
        # নতুন ডিপার্টমেন্ট অপশন যুক্ত করা হয়েছে
        department = st.selectbox("Select Department (বিভাগ)", [
            "Production (উৎপাদন)",
            "Quality Control (কিউসি)",
            "Accounts & Finance",
            "HR & Admin",
            "Store & Inventory",
            "Sales & Marketing"
        ])
        
        category = st.selectbox("Select Category", [
            "Manager", 
            "Officer", 
            "Worker (Permanent)", 
            "Worker (Daily Basis)"
        ])
        
        designation = st.text_input("Designation (পদবী)")
        salary = st.text_input("Gross Salary / Daily Wage Rate (Tk)")
        submit_btn = st.form_submit_button("Add to Database")
        
        if submit_btn:
            if input_id == "" or name == "" or designation == "" or salary == "":
                st.error("সব ঘর পূরণ করুন!")
            else:
                try:
                    salary_val = float(salary)
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO employees_final_version (emp_id, name, designation, category, department, salary) VALUES (?, ?, ?, ?, ?, ?)", 
                                   (input_id, name, designation, category, department, salary_val))
                    conn.commit()
                    conn.close()
                    st.success(f"{name} ({department}) সফলভাবে যুক্ত হয়েছেন!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("এই IDটি ইতিমধ্যে ডাটাবেজে আছে!")
                except ValueError:
                    st.error("টাকা সংখ্যায় হতে হবে!")

    st.markdown("---")
    st.header("❌ Remove Person")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, name, department FROM employees_final_version")
    del_rows = cursor.fetchall()
    conn.close()
    
    if del_rows:
        del_options = {f"[{r[2]}] {r[0]} - {r[1]}": r[0] for r in del_rows}
        selected_del_key = st.selectbox("Select Person to Remove", list(del_options.keys()))
        if st.button("Delete Person", type="primary", use_container_width=True):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees_final_version WHERE emp_id = ?", (del_options[selected_del_key],))
            conn.commit()
            conn.close()
            st.success("ডাটাবেজ থেকে মুছে ফেলা হয়েছে!")
            st.rerun()

# --- RIGHT SIDE: CALCULATIONS ---
with col2:
    st.header("📋 Payroll Calculation & Reports")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees_final_version")
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        current_m_idx = int(datetime.now().strftime("%m")) - 1
        current_y = datetime.now().strftime("%Y")
        
        m_col, y_col = st.columns(2)
        with m_col:
            select_m = st.selectbox("Select Month", months_list, index=current_m_idx)
        with y_col:
            select_y = st.selectbox("Select Year", [str(y) for y in range(2024, 2031)], index=list(range(2024, 2031)).index(int(current_y)))
            
        full_selected_month = f"{select_m}, {select_y}"
        
        tab1, tab2 = st.tabs(["📄 Individual Pay Slip", "📊 Full Salary Sheet (সবার একসাথে)"])
        
        # ট্যাব ১: সিঙ্গেল স্লিপ
        with tab1:
            emp_options = {f"[{r[4]}] {r[0]} - {r[1]}": r for r in rows}
            selected_emp_key = st.selectbox("Select Person for Pay Slip", list(emp_options.keys()))
            selected_emp = emp_options[selected_emp_key]
            
            st.markdown(f"##### 🗓️ Attendance Input for {selected_emp[3]}")
            with st.form("calculation_form"):
                attn_col, fine_col = st.columns(2)
                with attn_col:
                    if selected_emp[3] == 'Worker (Daily Basis)':
                        present_days = st.number_input("Total Present Days", min_value=0, max_value=31, value=26, step=1, key="ind_pres")
                        absent_days = 0
                    else:
                        absent_days = st.number_input("Absent Days", min_value=0, max_value=26, value=0, step=1, key="ind_abs")
                        present_days = 0
                with fine_col:
                    fine_amount = st.number_input("Fine / Penalty (Tk)", min_value=0.0, value=0.0, step=10.0, key="ind_fine")
                
                calc_btn = st.form_submit_button("🔄 Calculate Slip")
                if calc_btn:
                    st.session_state['f_absent'] = absent_days
                    st.session_state['f_present'] = present_days
                    st.session_state['f_fine'] = fine_amount

            final_absent = st.session_state.get('f_absent', 0)
            final_present = st.session_state.get('f_present', 26 if selected_emp[3] == 'Worker (Daily Basis)' else 0)
            final_fine = st.session_state.get('f_fine', 0.0)

            b, hr, m, td, absent_deduction, net_payable, total_earnings = calculate_salary_breakdown(
                selected_emp[5], final_absent, final_fine, selected_emp[3], final_present
            )
            
            st.markdown("---")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.write(f"**ID:** {selected_emp[0]} | **Name:** {selected_emp[1]}")
                st.write(f"**Department:** {selected_emp[4]} | **Designation:** {selected_emp[2]}")
                st.write(f"**Net Payable:** Tk {net_payable:,.2f}")
            
            pdf_bytes = generate_pdf_bytes(selected_emp, full_selected_month, final_absent, final_fine, final_present)
            b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                st.download_button("📥 Download Pay Slip (PDF)", data=pdf_bytes, file_name=f"PaySlip_{selected_emp[0]}.pdf", mime="application/pdf", use_container_width=True)
            with act_col2:
                st.markdown(f'<a href="data:application/pdf;base64,{b64_pdf}" target="_blank"><button style="width:100%; height:38px; background-color:#ff4b4b; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🖨️ Print Pay Slip</button></a>', unsafe_allow_html=True)

        # ট্যাব ২: ফুল স্যালারি শিট
        with tab2:
            st.markdown(f"### 📋 {full_selected_month} এর স্যালারি শিট জেনারেটর")
            
            sheet_data = []
            with st.form("bulk_sheet_form"):
                for r in rows:
                    emp_id, name, designation, category, dept, salary_rate = r
                    st.markdown(f"**🔹 [{dept}] {emp_id} - {name}** ({designation})")
                    col_input1, col_input2 = st.columns(2)
                    
                    with col_input1:
                        if category == 'Worker (Daily Basis)':
                            p_days = st.number_input(f"Present Days", min_value=0, max_value=31, value=26, step=1, key=f"p_{emp_id}")
                            a_days = 0
                        else:
                            a_days = st.number_input(f"Absent Days", min_value=0, max_value=26, value=0, step=1, key=f"a_{emp_id}")
                            p_days = 0
                    with col_input2:
                        f_amt = st.number_input(f"Penalty/Fine (Tk)", min_value=0.0, value=0.0, step=10.0, key=f"f_{emp_id}")
                    
                    sheet_data.append({
                        'emp_data': r,
                        'absent_days': a_days,
                        'present_days': p_days,
                        'fine_amount': f_amt
                    })
                    st.markdown("<hr style='margin:5px 0px; border-color:#eee;'>", unsafe_allow_html=True)
                
                submit_sheet = st.form_submit_button("📊 Generate Salary Sheet", use_container_width=True)
            
            if submit_sheet:
                final_table = []
                for item in sheet_data:
                    emp_id, name, designation, category, dept, salary_rate = item['emp_data']
                    b, hr, m, td, absent_deduction, net_payable, total_earnings = calculate_salary_breakdown(
                        salary_rate, item['absent_days'], item['fine_amount'], category, item['present_days']
                    )
                    
                    final_table.append({
                        "Employee ID": emp_id,
                        "Name": name,
                        "Department": dept,  # এক্সেল ফাইলে ডিপার্টমেন্ট কলাম যুক্ত হলো
                        "Category": category,
                        "Designation": designation,
                        "Base Salary/Rate": salary_rate,
                        "Total Earnings": round(total_earnings, 2),
                        "Absent Cut": round(absent_deduction, 2),
                        "Fine/Penalty": round(item['fine_amount'], 2),
                        "Net Payable (টাকা)": round(net_payable, 2)
                    })
                
                df = pd.DataFrame(final_table)
                st.success("🎉 স্যালারি শিট সফলভাবে তৈরি হয়েছে!")
                st.dataframe(df, use_container_width=True)
                
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="SalarySheet")
                excel_bytes = excel_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Full Salary Sheet (Excel)",
                    data=excel_bytes,
                    file_name=f"RECON_Payroll_Sheet_{select_m}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
    else:
        st.info("বর্তমানে ডাটাবেজে কেউ যুক্ত নেই। বাম পাশের ফর্ম থেকে নতুন লোক যুক্ত করুন।")
