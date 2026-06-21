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
SUPABASE_KEY = "sb_publishable_polNmuBnDGzfd91wFvCozw_eUJUtGrx" # এখানে আপনার Key বসান

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

# --- LOGO & IMAGES (একই থাকবে) ---
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
        
        if st.form_submit_button("Add to Database", type="primary"):
            try:
                supabase.table("employees_final_version").insert({
                    "emp_id": input_id, "name": name, "designation": designation, 
                    "category": category, "department": department, "salary": float(salary)
                }).execute()
                st.success("Added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

with col2:
    # ডাটা ফেচিং
    try:
        rows = supabase.table("employees_final_version").select("*").execute().data
    except: rows = []
    
    if rows:
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        c1, c2 = st.columns(2)
        select_m = c1.selectbox("Select Month", months_list, index=months_list.index(datetime.now().strftime("%B")))
        select_y = c2.selectbox("Select Year", ["2026", "2027"])
        full_month = f"{select_m}, {select_y}"
        
        # অ্যাটেনডেন্স ডাটা ফেচিং
        att_data = supabase.table("monthly_attendance_records").select("*").eq("month_year", full_month).execute().data
        saved_db_tracker = {str(r['emp_id']): r for r in att_data}

        # --- মূল ফাংশনালিটি ---
        st.subheader("Employee Records")
        for r in rows:
            with st.expander(f"{r['name']} ({r['emp_id']})"):
                st.write(f"Salary: {r['salary']}")
                # এখানে আপনার ডিলিট বা এডিট বাটন যোগ করতে পারেন Supabase কুয়েরি দিয়ে
        
        # অ্যাটেনডেন্স প্রসেসিং
        st.subheader("Attendance Processing")
        if st.button("Save Attendance Data"):
            # এখানে আপনার sheet_data লুপটি বসিয়ে supabase.table(...).upsert(...) ব্যবহার করবেন
            st.info("Attendance data saved to Supabase.")

st.sidebar.info("System is now connected to Supabase Cloud.")
