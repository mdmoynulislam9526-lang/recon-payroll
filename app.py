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
SUPABASE_KEY = "sb_publishable_polNmuBnDGzfd91wFvCozw_eUJUtGrx"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

# --- SUPABASE FETCH FUNCTIONS ---
def get_employees():
    return supabase.table("employees_final_version").select("*").execute().data

def get_attendance(month_year):
    return supabase.table("monthly_attendance_records").select("*").eq("month_year", month_year).execute().data

# --- IMAGE LOADING ---
def get_img_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode('utf-8')
    return ""

logo_base64_str = get_img_base64("logo.png")

# --- MANAGEMENT FUNCTION ---
def render_inline_management(r, prefix=""):
    eid, ename, edesg, ecat, edept, esalary = r['emp_id'], r['name'], r['designation'], r['category'], r['department'], r['salary']
    with st.container():
        col_info, col_act1, col_act2 = st.columns([3, 0.6, 0.6])
        col_info.markdown(f"**[{eid}] {ename}** — {edesg} ({edept}) | Tk {esalary:,.2f}")
        if col_act1.button("Edit 📝", key=f"{prefix}_edit_{eid}"): st.session_state[f"emode_{prefix}_{eid}"] = True
        if col_act2.button("Delete ❌", key=f"{prefix}_del_{eid}"):
            supabase.table("employees_final_version").delete().eq("emp_id", eid).execute()
            supabase.table("monthly_attendance_records").delete().eq("emp_id", eid).execute()
            st.rerun()
        if st.session_state.get(f"emode_{prefix}_{eid}", False):
            with st.form(key=f"form_{prefix}_{eid}"):
                c_n = st.text_input("Name", value=ename)
                c_s = st.text_input("Salary", value=str(esalary))
                if st.form_submit_button("Save"):
                    supabase.table("employees_final_version").update({"name": c_n, "salary": float(c_s)}).eq("emp_id", eid).execute()
                    st.session_state[f"emode_{prefix}_{eid}"] = False
                    st.rerun()

# --- MAIN UI ---
st.title("💼 RECON LABORATORIES LTD - Advanced Payroll Management System")
st.markdown("---")

col1, col2 = st.columns([1, 2.3])

with col1:
    st.header("➕ Add New Person")
    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("ID").strip()
        name = st.text_input("Name")
        dept = st.selectbox("Department", ["Production", "Quality Control", "Development", "Accounts & Finance"])
        cat = st.selectbox("Category", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
        desg = st.text_input("Designation")
        salary = st.text_input("Gross Salary")
        if st.form_submit_button("Add to Database"):
            supabase.table("employees_final_version").insert({"emp_id": input_id, "name": name, "designation": desg, "category": cat, "department": dept, "salary": float(salary)}).execute()
            st.rerun()

with col2:
    rows = get_employees()
    if rows:
        m_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        c_m, c_y = st.columns(2)
        full_month = f"{c_m.selectbox('Month', m_list, index=m_list.index(datetime.now().strftime('%B')))}, {c_y.selectbox('Year', ['2024', '2025', '2026'])}"
        
        tab_emp, tab_search, tab_proc = st.tabs(["👥 All Employees", "🔍 Search", "📊 Attendance Processor"])
        
        with tab_emp:
            for cat_val in ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"]:
                with st.expander(f"{cat_val}"):
                    for r in [x for x in rows if x['category'] == cat_val]: render_inline_management(r)
        
        with tab_proc:
            with st.form("bulk_sheet"):
                sheet_data = []
                for r in rows:
                    st.write(f"{r['name']}")
                    c1, c2 = st.columns(2)
                    p = c1.number_input("Present", value=26, key=f"p_{r['emp_id']}")
                    adv = c2.number_input("Advance", value=0.0, key=f"adv_{r['emp_id']}")
                    sheet_data.append({'eid': r['emp_id'], 'p': p, 'adv': adv})
                if st.form_submit_button("Save Records"):
                    for item in sheet_data:
                        supabase.table("monthly_attendance_records").upsert({"month_year": full_month, "emp_id": item['eid'], "present": item['p'], "advance": item['adv']}).execute()
                    st.success("Saved!")
    else:
        st.info("Database is empty.")
