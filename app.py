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

def get_employees():
    return supabase.table("employees_final_version").select("*").execute().data

def render_inline_management(r, prefix=""):
    eid, ename, edesg, ecat, edept, esalary = r['emp_id'], r['name'], r['designation'], r['category'], r['department'], r['salary']
    
    with st.container():
        col_info, col_act1, col_act2 = st.columns([3, 0.6, 0.6])
        col_info.markdown(f"**[{eid}] {ename}** — {edesg} ({edept}) | Tk {esalary:,.2f}")
        
        if col_act1.button("Edit 📝", key=f"{prefix}_edit_{eid}"): 
            st.session_state[f"emode_{prefix}_{eid}"] = True
            
        if col_act2.button("Delete ❌", key=f"{prefix}_del_{eid}"):
            supabase.table("employees_final_version").delete().eq("emp_id", eid).execute()
            st.rerun()

        if st.session_state.get(f"emode_{prefix}_{eid}", False):
            with st.form(key=f"form_{prefix}_{eid}"):
                col_a, col_b = st.columns(2)
                new_id = col_a.text_input("ID", value=eid)
                new_name = col_b.text_input("Name", value=ename)
                new_dept = col_a.selectbox("Department", ["Production", "Quality Control", "Development", "Accounts & Finance"], index=["Production", "Quality Control", "Development", "Accounts & Finance"].index(edept))
                new_cat = col_b.selectbox("Category", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"], index=["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"].index(ecat))
                new_desg = col_a.text_input("Designation", value=edesg)
                new_salary = col_b.number_input("Salary", value=float(esalary))
                
                if st.form_submit_button("Save Changes"):
                    supabase.table("employees_final_version").update({
                        "emp_id": new_id, "name": new_name, "department": new_dept, 
                        "category": new_cat, "designation": new_desg, "salary": new_salary
                    }).eq("emp_id", eid).execute()
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
        salary = st.number_input("Gross Salary", step=1.0)
        if st.form_submit_button("Add to Database"):
            supabase.table("employees_final_version").insert({"emp_id": input_id, "name": name, "designation": desg, "category": cat, "department": dept, "salary": float(salary)}).execute()
            st.rerun()

with col2:
    rows = get_employees()
    if rows:
        st.subheader("👥 Employee Management")
        for r in rows:
            render_inline_management(r)
    else:
        st.info("No data found.")
