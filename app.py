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

# --- LOGO & IMAGES ---
logo_base64_str = ""
current_dir = os.path.dirname(os.path.abspath(__file__))
local_logo_path = os.path.join(current_dir, "logo.png")
if os.path.exists(local_logo_path):
    with open(local_logo_path, "rb") as img_file:
        logo_base64_str = base64.b64encode(img_file.read()).decode('utf-8')

sig_base64_str = "" 
sig_html_element = f"<img src='data:image/png;base64,{sig_base64_str}' style='width: 150px;'>" if sig_base64_str else "____________________"

st.title("💼 RECON LABORATORIES LTD - Advanced Payroll Management System")
st.markdown("---")

col1, col2 = st.columns([1, 2.3])

# --- SIDE PANEL ---
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
            if not (input_id and name and designation and salary):
                st.error("Please fill all fields!")
            elif not re.match(r"^[0-9]+$", input_id):
                st.error("⚠️ Invalid ID Format!")
            else:
                try:
                    supabase.table("employees_final_version").insert({
                        "emp_id": input_id, "name": name, "designation": designation, 
                        "category": category, "department": department, "salary": float(salary)
                    }).execute()
                    st.success(f"{name} added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Error: {e}")

# --- FUNCTION: RENDER MANAGEMENT ---
def render_inline_management(r, prefix=""):
    eid, ename, edesg, ecat, edept, esalary = r['emp_id'], r['name'], r['designation'], r['category'], r['department'], r['salary']
    with st.container():
        col_info, col_act1, col_act2 = st.columns([3, 0.6, 0.6])
        with col_info:
            st.markdown(f"**[{eid}] {ename}** — {edesg} ({edept}) | Tk {esalary:,.2f}")
        with col_act1:
            if st.button("Edit 📝", key=f"{prefix}_edit_{eid}"):
                st.session_state[f"emode_{prefix}_{eid}"] = True
        with col_act2:
            if st.button("Delete ❌", key=f"{prefix}_del_{eid}", type="secondary"):
                supabase.table("employees_final_version").delete().eq("emp_id", eid).execute()
                supabase.table("monthly_attendance_records").delete().eq("emp_id", eid).execute()
                st.rerun()
        if st.session_state.get(f"emode_{prefix}_{eid}", False):
            with st.form(key=f"form_{prefix}_{eid}"):
                ch_name = st.text_input("Name", value=ename)
                ch_salary = st.text_input("Salary", value=str(esalary))
                if st.form_submit_button("Save"):
                    supabase.table("employees_final_version").update({"name": ch_name, "salary": float(ch_salary)}).eq("emp_id", eid).execute()
                    st.session_state[f"emode_{prefix}_{eid}"] = False
                    st.rerun()

# --- MAIN DASHBOARD (col2) ---
with col2:
    response = supabase.table("employees_final_version").select("*").execute()
    rows = response.data 

    if rows:
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        if 'selected_month' not in st.session_state: st.session_state.selected_month = datetime.now().strftime("%B")
            
        c_col1, c_col2 = st.columns(2)
        with c_col1: select_m = st.selectbox("Select Month", months_list, index=months_list.index(st.session_state.selected_month))
        with c_col2: 
            current_year = datetime.now().year
            available_years = [str(y) for y in range(2023, current_year + 5)]
            select_y = st.selectbox("Select Year", available_years, index=available_years.index(str(current_year)))
        
        full_month = f"{select_m}, {select_y}"
        days_in_month = calendar.monthrange(int(select_y), months_list.index(select_m) + 1)[1]
        
        att_response = supabase.table("monthly_attendance_records").select("*").eq("month_year", full_month).execute()
        db_records = att_response.data
        saved_db_tracker = {str(r['emp_id']): r for r in db_records}

        # --- TABS ---
        tab_emp, tab0, tab1, tab2, tab3, tab4 = st.tabs(["👥 All Employees", "🔍 Search", "📄 Pay Slip", "📊 Attendance & Processor", "📑 Summary Sheet", "📈 Dashboard Summary"])
        
        with tab3:
            st.subheader("📊 Attendance & Processor")
            with st.form("attendance_processor_form"):
                cat_to_process = st.selectbox("Select Category", ["Officer", "Manager", "Worker (Permanent)", "Worker (Daily Basis)"])
                submitted = st.form_submit_button("Process Attendance")
            
            if submitted:
                # ক্যালকুলেশন লজিক এখানে
                for r in rows:
                    if r['category'] == cat_to_process:
                        eid = str(r['emp_id'])
                        rec = saved_db_tracker.get(eid, {"present_days": 26, "absent_days": 0, "fine_amount": 0.0})
                        
                        # ফাংশন কল
                        gross, house_rent, medical, _, ab_cut, net_p, adv_paid = calculate_salary_breakdown(
                            r['salary'], rec.get('absent_days', 0), rec.get('fine_amount', 0), 
                            r['category'], rec.get('present_days', 26), rec.get('advance_cut', 0)
                        )
                        st.write(f"{r['name']}: Net Payable = {net_p:,.2f}")
        
        with tab4:
            st.subheader("📈 Dashboard Summary")
            total_salary = sum([r['salary'] for r in rows])
            st.metric("Total Base Salary Budget", f"Tk {total_salary:,.2f}")
        
        df_rows = pd.DataFrame(rows)
        cat_summary = df_rows.groupby('category')['salary'].agg(['count', 'sum']).reset_index()
        st.table(cat_summary)
    else:
        st.info("No records loaded yet.")
