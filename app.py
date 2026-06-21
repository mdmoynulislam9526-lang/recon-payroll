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
# Ekhane apnar nijer URL ebong KEY bosan
SUPABASE_URL = "https://supabase.com/dashboard/project/qoelqzaodnxjfsmsyvhc/settings/general"
SUPABASE_KEY = "sb_publishable_polNmuBnDGzfd91wFvCozw_eUJUtGrx"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

# --- SUPABASE FUNCTIONS ---
def get_employees():
    response = supabase.table("employees_final_version").select("*").execute()
    return response.data

def get_attendance(month_year):
    response = supabase.table("monthly_attendance_records").select("*").eq("month_year", month_year).execute()
    return response.data

# --- APP START ---
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
            data = {"emp_id": input_id, "name": name, "designation": designation, "category": category, "department": department, "salary": float(salary)}
            supabase.table("employees_final_version").insert(data).execute()
            st.success(f"{name} added successfully!")
            st.rerun()

with col2:
    rows = get_employees()
    if rows:
        st.subheader("Employee List (Loaded from Supabase)")
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.info("No data found in Supabase.")
