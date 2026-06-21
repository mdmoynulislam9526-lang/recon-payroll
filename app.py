import streamlit as st
from supabase import create_client
from datetime import datetime
import calendar
from io import BytesIO
import pandas as pd
import re
import os
import base64
from calculations import calculate_salary_breakdown, generate_pdf_bytes

# --- SUPABASE CONFIGURATION ---
SUPABASE_URL = "https://qoelqzaodnxjfsmsyvhc.supabase.co"
SUPABASE_KEY = "sb_publishable_polNmuBnDGzfd91wFvCozw_eUJUtGrx" # Ekhane apnar anon/public key-ti bosan

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

# --- LOGO & IMAGES ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode('utf-8')
    return ""

logo_base64_str = get_image_base64("logo.png")
sig_base64_str = get_image_base64("signature.png")
seal_base64_str = get_image_base64("seal.png")

st.title("💼 RECON LABORATORIES LTD - Advanced Payroll Management System")
st.markdown("---")

col1, col2 = st.columns([1, 2.3])

with col1:
    st.header("➕ Add New Person")
    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("ID (Numbers only)").strip()
        name = st.text_input("Name")
        department = st.selectbox("Select Department", ["Production", "Quality Control", "Development", "Maintenance", "Accounts & Finance", "HR & Admin", "Store & Inventory", "Sales & Marketing"])
        category = st.selectbox("Select Category", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
        designation = st.text_input("Designation")
        salary = st.text_input("Gross Salary / Daily Wage Rate (Tk)")
        
        if st.form_submit_button("Add to Database", use_container_width=True, type="primary"):
            try:
                supabase.table("employees_final_version").insert({
                    "emp_id": input_id, "name": name, "designation": designation, 
                    "category": category, "department": department, "salary": float(salary)
                }).execute()
                st.success(f"{name} added!")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error: {e}")

with col2:
    # Data Fetching
    rows = supabase.table("employees_final_version").select("*").execute().data
    
    if rows:
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        if 'selected_month' not in st.session_state: st.session_state.selected_month = datetime.now().strftime("%B")
            
        c_col1, c_col2 = st.columns(2)
        select_m = c_col1.selectbox("Select Month", months_list, index=months_list.index(st.session_state.selected_month))
        select_y = c_col2.selectbox("Select Year", [str(y) for y in range(2023, 2030)], index=0)
        
        full_month = f"{select_m}, {select_y}"
        
        db_records = supabase.table("monthly_attendance_records").select("*").eq("month_year", full_month).execute().data
        saved_db_tracker = {str(r['emp_id']): r for r in db_records}

        # --- Dashboard & Tabs ---
        tab_emp, tab0, tab1, tab2 = st.tabs(["👥 All Employees", "🔍 Search Employee", "📄 Individual Pay Slip", "📊 Attendance & Payroll Processor"])
        
        with tab_emp:
            for r in rows:
                st.write(f"**{r['name']}** ({r['emp_id']})")
                # Ekhane apnar purono render_inline_management logic bosate paren
        
        with tab2:
            st.write("Attendance Processor content here...")
            # Ekhane apnar purono bulk_sheet_form logic bosate paren
            if st.button("Save Attendance"):
                # Supabase upsert logic
                pass
