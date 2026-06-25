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
    eid, ename, edesg, ecat, edept, esalary = r
    with st.container():
        col_info, col_act1, col_act2 = st.columns([3, 0.6, 0.6])
        with col_info:
            st.markdown(f"**[{eid}] {ename}** — {edesg} ({edept}) | Tk {esalary:,.2f}")
        with col_act1:
            if st.button("Edit 📝", key=f"{prefix}_edit_{eid}"): st.session_state[f"emode_{prefix}_{eid}"] = True
        with col_act2:
            if st.button("Delete ❌", key=f"{prefix}_del_{eid}", type="secondary"):
                # Supabase Delete
                supabase.table("employees_final_version").delete().eq("emp_id", eid).execute()
                supabase.table("monthly_attendance_records").delete().eq("emp_id", eid).execute()
                st.rerun()
        if st.session_state.get(f"emode_{prefix}_{eid}", False):
            with st.form(key=f"form_{prefix}_{eid}"):
                ch_name = st.text_input("Name", value=ename)
                ch_salary = st.text_input("Salary", value=str(esalary))
                if st.form_submit_button("Save"):
                    # Supabase Update
                    supabase.table("employees_final_version").update({"name": ch_name, "salary": float(ch_salary)}).eq("emp_id", eid).execute()
                    st.session_state[f"emode_{prefix}_{eid}"] = False
                    st.rerun()

with col2:
    response = supabase.table("employees_final_version").select("*").execute()
    rows = response.data
    
    if rows:
        # --- FIXED MONTH SELECTION ---
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        if 'selected_month' not in st.session_state:
            st.session_state.selected_month = datetime.now().strftime("%B")
            
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            select_m = st.selectbox("Select Month", months_list, index=months_list.index(st.session_state.selected_month))
            st.session_state.selected_month = select_m
        
        current_year = datetime.now().year
        available_years = [str(y) for y in range(2023, current_year + 5)]
        with c_col2:
            select_y = st.selectbox("Select Year", available_years, index=available_years.index(str(current_year)))
        
        full_month = f"{select_m}, {select_y}"
        
        month_num = months_list.index(select_m) + 1
        days_in_month = calendar.monthrange(int(select_y), month_num)[1]
        
# Supabase থেকে ডাটা ফেচ করা হচ্ছে
        response = supabase.table("monthly_attendance_records").select("*").eq("month_year", full_month).execute()
        db_records = response.data
        
        # ডাটা ডিকশনারি ফরম্যাটে ট্র্যাকার তৈরি করা হচ্ছে
# Supabase থেকে ডাটা ফেচ করা হচ্ছে
        response = supabase.table("monthly_attendance_records").select("*").eq("month_year", full_month).execute()
        db_records = response.data
        
        # আপনার কলামের নাম অনুযায়ী ট্র্যাকার তৈরি
        saved_db_tracker = {
            str(r['emp_id']): {
                "present_days": r.get('present_days', 0), 
                "absent_days": r.get('absent_days', 0), 
                "fine_amount": r.get('fine_amount', 0), 
                "overtime_hours": r.get('overtime_hours', 0), 
                "overtime_rate": r.get('overtime_rate', 0), 
                "bonus_amount": r.get('bonus_amount', 0), 
                "advance_cut": r.get('advance_cut', 0)
            } for r in db_records
        }

        total_payout = 0.0
        total_bonus = 0.0
        total_ot = 0.0
        total_deductions = 0.0
        total_advance = 0.0

        for r in rows:
            # Supabase থেকে ডাটা এক্সেস করার সঠিক পদ্ধতি
            eid = str(r['emp_id'])
            cat = r['category']
            base_sal = r['salary']
            
            # ডাটা ট্র্যাকার থেকে রেকর্ড নেওয়া
            rec = saved_db_tracker.get(eid, {
                "present_days": days_in_month if cat == 'Worker (Daily Basis)' else 26, 
                "absent_days": 0, 
                "fine_amount": 0.0, 
                "overtime_hours": 0.0, 
                "overtime_rate": 0.0, 
                "bonus_amount": 0.0, 
                "advance_cut": 0.0
            })
            
            # ক্যালকুলেশন ফাংশনে নতুন কীগুলো পাস করুন
            _, _, _, _, absent_cut, net_p, adv_paid = calculate_salary_breakdown(
                base_sal, rec['absent_days'], rec['fine_amount'], cat, rec['present_days'], rec['advance_cut']
            )
            
            ot_earned = rec['overtime_hours'] * rec['overtime_rate']
            final_payable = net_p + ot_earned + rec['bonus_amount']
            
            total_payout += final_payable
            total_bonus += rec['bonus_amount']
            total_ot += ot_earned
            total_deductions += (absent_cut + rec['fine_amount'])
            total_advance += adv_paid

        st.markdown("### 📊 Financial Dashboard Summary")
        m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
        m_col1.metric("Total Employees", len(rows))
        m_col2.metric("Total Bonus (Tk)", f"{total_bonus:,.2f}")
        m_col3.metric("Total Overtime (Tk)", f"{total_ot:,.2f}")
        m_col4.metric("Total Fine & Abs Cut (Tk)", f"{total_deductions:,.2f}")
        m_col5.metric("Total Advance Cut (Tk)", f"{total_advance:,.2f}")
        m_col6.metric("Total Payout (Tk)", f"{total_payout:,.2f}")
        st.markdown("---")

        tab_emp, tab0, tab1, tab2 = st.tabs(["👥 All Employees", "🔍 Search Employee", "📄 Individual Pay Slip", "📊 Attendance & Payroll Processor"])
        
        with tab_emp:
            categories_map = {"💼 Managers": "Manager", "👔 Officers": "Officer", "🛠️ Workers (Permanent)": "Worker (Permanent)", "📆 Workers (Daily Basis)": "Worker (Daily Basis)"}
            for title, cat_value in categories_map.items():
                cat_members = [r for r in rows if r[3] == cat_value]
                with st.expander(f"{title} ({len(cat_members)})", expanded=False):
                    if not cat_members: st.info("No records.")
                    else:
                        for r in cat_members: render_inline_management(r, prefix="all_tab")

        with tab0:
            search_query = st.text_input("Enter Employee ID or Name to search", placeholder="Type here...", key="search_tab_input")
            if search_query:
                search_results = [r for r in rows if search_query.lower() in r[0].lower() or search_query.lower() in r[1].lower()]
                for emp in search_results: render_inline_management(emp, prefix="search_tab")

        # --- TAB 1: INDIVIDUAL PAY SLIP (CLASSIC OFFICE TABLE DESIGN) ---
        with tab1:
            pay_search = st.text_input("Enter Employee ID or Name for Pay Slip", key="pay_slip_search_input")
            if pay_search:
                pay_results = [r for r in rows if pay_search.lower() in r[0].lower() or pay_search.lower() in r[1].lower()]
                if pay_results:
                    selected_emp = pay_results[0]
                    rec = saved_db_tracker.get(str(selected_emp[0]), {"present": days_in_month if selected_emp[3] == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                    
                    st.success(f"Selected: {selected_emp[1]} ({selected_emp[0]})")
                    
                    gross, house_rent, medical, _, absent_cut, net_p, adv_paid = calculate_salary_breakdown(
                        selected_emp[5], rec['absent'], rec['fine'], selected_emp[3], rec['present'], rec['advance']
                    )
                    
                    total_ot_emp = rec['ot_hrs'] * rec['ot_rate']
                    net_final = net_p + total_ot_emp + rec['bonus']
                    
                    sig_html_element = ""
                    if seal_base64_str:
                        sig_html_element += f"<img src='data:image/png;base64,{seal_base64_str}' style='max-height: 75px; width: auto; display: block; margin: 0 auto -45px auto; z-index: 8; position: relative; opacity: 0.85;' alt='Seal'>"
                    if sig_base64_str:
                        sig_html_element += f"<img src='data:image/png;base64,{sig_base64_str}' style='max-height: 60px; width: auto; display: block; margin: 0 auto -25px auto; z-index: 12; position: relative;' alt='Signature'>"
                    
                    if not sig_base64_str and not seal_base64_str:
                        sig_html_element = "<div style='height: 57px; color:#aaa; font-size:11px; padding-top:20px;'>[Images Not Found]</div>"

                    # 💎 CLASSIC OFFICE TABLE DESIGN (EMPLOYEE INFO INSIDE A STRUCTURED TABLE)
                    payslip_preview_html = f"""
                    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 35px; background: white; color: black; border: 1px solid #c8d6e5; border-radius: 8px; max-width: 700px; margin: 15px auto; box-sizing: border-box; box-shadow: 0 4px 20px rgba(0,0,0,0.06);">
                        
                        <div style="text-align: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #1F4E78;">
                            {"<div style='margin-bottom: 5px; display: block;'><img src='data:image/png;base64," + logo_base64_str + "' style='max-height: 65px; width: auto; object-fit: contain; display: inline-block;' alt='RECON Logo'></div>" if logo_base64_str else ""}
                        </div>
                        
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; width: 100%;">
                            <div style="width: 25%;"></div>
                            <div style="width: 50%; text-align: center;">
                                <span style="font-size: 16px; color: #1F4E78; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Employee Pay Slip</span>
                            </div>
                            <div style="width: 25%; text-align: right;">
                                <span style="font-size: 12px; color: #1F4E78; font-weight: 700; background-color: #f0f4f8; padding: 4px 10px; border-radius: 4px; border: 1px solid #b4c6e7; text-transform: uppercase;">{select_m[:3]} {select_y}</span>
                            </div>
                        </div>
                        
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 13px; border: 1px solid #cbd5e1;">
                            <tr style="background-color: #f8fafc;">
                                <td style="padding: 10px; font-weight: 600; color: #475569; width: 25%; border: 1px solid #cbd5e1;">Employee ID</td>
                                <td style="padding: 10px; font-weight: 700; color: #0f172a; width: 25%; border: 1px solid #cbd5e1;">#{selected_emp[0]}</td>
                                <td style="padding: 10px; font-weight: 600; color: #475569; width: 25%; border: 1px solid #cbd5e1;">Department</td>
                                <td style="padding: 10px; font-weight: 600; color: #1F4E78; width: 25%; border: 1px solid #cbd5e1;">{selected_emp[4]}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; font-weight: 600; color: #475569; border: 1px solid #cbd5e1;">Full Name</td>
                                <td style="padding: 10px; font-weight: 700; color: #0f172a; border: 1px solid #cbd5e1;">{selected_emp[1]}</td>
                                <td style="padding: 10px; font-weight: 600; color: #475569; border: 1px solid #cbd5e1;">Designation</td>
                                <td style="padding: 10px; font-weight: 600; color: #1F4E78; border: 1px solid #cbd5e1;">{selected_emp[2]}</td>
                            </tr>
                            <tr style="background-color: #f8fafc;">
                                <td style="padding: 10px; font-weight: 600; color: #475569; border: 1px solid #cbd5e1;">Category</td>
                                <td style="padding: 10px; font-weight: 600; color: #334155; border: 1px solid #cbd5e1;">{selected_emp[3]}</td>
                                <td style="padding: 10px; font-weight: 600; color: #475569; border: 1px solid #cbd5e1;">Attendance Status</td>
                                <td style="padding: 10px; font-weight: 700; color: #2563eb; border: 1px solid #cbd5e1;">{rec['present']} P  /  {rec['absent']} A</td>
                            </tr>
                        </table>
                        
                        <table style="width: 100%; font-size: 13px; border-collapse: collapse; margin-bottom: 25px;">
                            <thead>
                                <tr style="background-color: #F8FAFC; border-top: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;">
                                    <th style="padding: 10px 8px; text-align: left; color: #1F4E78; font-weight: 700; width: 30%; border-right: 1px solid #EDF2F7;">Earnings</th>
                                    <th style="padding: 10px 8px; text-align: right; color: #1F4E78; font-weight: 700; width: 20%; border-right: 2px solid #E2E8F0;">Amount (Tk)</th>
                                    <th style="padding: 10px 8px; text-align: left; color: #9B2C2C; font-weight: 700; width: 30%; padding-left: 15px; border-right: 1px solid #EDF2F7;">Deductions</th>
                                    <th style="padding: 10px 8px; text-align: right; color: #9B2C2C; font-weight: 700; width: 20%;">Amount (Tk)</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="padding: 9px 8px; border-bottom: 1px dashed #E2E8F0; border-right: 1px solid #EDF2F7;">Base Pay</td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px dashed #E2E8F0; font-weight: 500; border-right: 2px solid #E2E8F0;">{gross:,.2f}</td>
                                    <td style="padding: 9px 8px; border-bottom: 1px dashed #E2E8F0; padding-left: 15px; color: #C53030; border-right: 1px solid #EDF2F7;">Absent Cut</td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px dashed #E2E8F0; color: #C53030; font-weight: 500;">{absent_cut:,.2f}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 9px 8px; border-bottom: 1px dashed #E2E8F0; color: #4A5568; border-right: 1px solid #EDF2F7;">House Rent</td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px dashed #E2E8F0; color: #4A5568; border-right: 2px solid #E2E8F0;">{house_rent:,.2f}</td>
                                    <td style="padding: 9px 8px; border-bottom: 1px dashed #E2E8F0; padding-left: 15px; color: #C53030; border-right: 1px solid #EDF2F7;">Fine / Penalty</td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px dashed #E2E8F0; color: #C53030; font-weight: 500;">{rec['fine']:,.2f}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 9px 8px; border-bottom: 1px dashed #E2E8F0; color: #4A5568; border-right: 1px solid #EDF2F7;">Medical</td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px dashed #E2E8F0; color: #4A5568; border-right: 2px solid #E2E8F0;">{medical:,.2f}</td>
                                    <td style="padding: 9px 8px; border-bottom: 1px dashed #E2E8F0; padding-left: 15px; color: #C53030; border-right: 1px solid #EDF2F7;">Advance Cut</td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px dashed #E2E8F0; color: #C53030; font-weight: 500;">{adv_paid:,.2f}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 9px 8px; border-bottom: 1px dashed #E2E8F0; color: #2F855A; font-weight: 500; border-right: 1px solid #EDF2F7;">Overtime ({rec['ot_hrs']} hrs)</td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px dashed #E2E8F0; color: #2F855A; font-weight: 500; border-right: 2px solid #E2E8F0;">{total_ot_emp:,.2f}</td>
                                    <td style="padding: 9px 8px; border-bottom: 1px dashed #E2E8F0; border-right: 1px solid #EDF2F7; padding-left: 15px;"></td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px dashed #E2E8F0;"></td>
                                </tr>
                                <tr>
                                    <td style="padding: 9px 8px; border-bottom: 1px solid #E2E8F0; color: #2F855A; font-weight: 500; border-right: 1px solid #EDF2F7;">Bonus</td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px solid #E2E8F0; color: #2F855A; font-weight: 500; border-right: 2px solid #E2E8F0;">{rec['bonus']:,.2f}</td>
                                    <td style="padding: 9px 8px; border-bottom: 1px solid #E2E8F0; border-right: 1px solid #EDF2F7; padding-left: 15px;"></td>
                                    <td style="padding: 9px 8px; text-align: right; border-bottom: 1px solid #E2E8F0;"></td>
                                </tr>
                                <tr style="background-color: #F8FAFC; font-weight: bold; border-top: 2px solid #E2E8F0;">
                                    <td style="padding: 12px 8px; color: #1F4E78; font-size: 14px;" colspan="2">Net Payable Salary:</td>
                                    <td style="padding: 12px 8px; text-align: right; color: #1F4E78; font-size: 15px; font-weight: 700;" colspan="2">Tk {net_final:,.2f}</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <div style="margin-top: 50px; display: flex; justify-content: flex-end;">
                            <div style="text-align: center; width: 190px; position: relative;">
                                {sig_html_element}
                                <div style="border-top: 1.5px solid #333; padding-top: 6px; font-size: 12px; font-weight: 600; color: #333; position: relative; z-index: 5; letter-spacing: 0.3px;">Authorized Signature</div>
                            </div>
                        </div>
                    </div>
                    """
                    st.components.v1.html(payslip_preview_html, height=560, scrolling=True)
                    
                    pdf_emp_data = (
                        selected_emp[0], selected_emp[1], selected_emp[2], selected_emp[3], selected_emp[4],
                        house_rent, medical, adv_paid, net_final
                    )
                    
                    pdf_buf = BytesIO()
                    generate_pdf_bytes(pdf_emp_data, full_month, rec['absent'], rec['fine'], rec['present'], pdf_buf)
                    st.download_button("📥 Download Pay Slip (PDF)", data=pdf_buf.getvalue(), file_name=f"PaySlip_{selected_emp[0]}_{select_m}.pdf", mime="application/pdf", use_container_width=True)

        # --- TAB 2: ATTENDANCE & PROCESSOR ---
with tab2:
            view_cat = st.selectbox("Select Category to Process", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"], key="att_sheet_cat")
            # Supabase এর ক্ষেত্রে filtered_rows এ r['category'] ব্যবহার করতে হবে
            filtered_rows = [r for r in rows if r['category'] == view_cat]
            
            sheet_data = []
            if filtered_rows:
                with st.form("bulk_sheet_form_v5"):
                    for r in filtered_rows:
                        # Supabase এর কী (keys) ব্যবহার করা হয়েছে
                        st.markdown(f"**🔹 {r['emp_id']} - {r['name']}** ({r['designation']})")
                        rec = saved_db_tracker.get(str(r['emp_id']), {"present": days_in_month if r['category'] == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                        
                        col_in1, col_in2, col_in3 = st.columns(3)
                        with col_in1:
                            total_target_days = st.number_input("Total Target Days", 1, 100, int(rec['present'] + rec['absent']) if rec['absent'] > 0 else (days_in_month if r['category'] == 'Worker (Daily Basis)' else max(26, int(rec['present']))), key=f"target_{r['emp_id']}")
                            a_d = st.number_input("Absent Days", 0, total_target_days, int(rec['absent']), key=f"a_{r['emp_id']}")
                            p_d = total_target_days - a_d
                            f_d = st.number_input("Penalty/Fine (Tk)", 0.0, value=float(rec['fine']), key=f"f_{r['emp_id']}")
                        
                        with col_in2:
                            ot_h = st.number_input("Overtime Hours", 0.0, 200.0, value=float(rec['ot_hrs']), key=f"oth_{r['emp_id']}")
                            ot_r = st.number_input("OT Rate per Hour (Tk)", 0.0, 1000.0, value=float(rec['ot_rate']), key=f"otr_{r['emp_id']}")
                        
                        with col_in3:
                            bonus_amt = st.number_input("Bonus Amount (Tk)", 0.0, 200000.0, value=float(rec['bonus']), key=f"bn_{r['emp_id']}")
                            adv_cut = st.number_input("Advanced Salary Cut (Tk)", 0.0, 200000.0, value=float(rec['advance']), key=f"adv_{r['emp_id']}")
                        
                        sheet_data.append({'eid': r['emp_id'], 'p': p_d, 'a': a_d, 'f': f_d, 'oth': ot_h, 'otr': ot_r, 'bonus': bonus_amt, 'adv': adv_cut})
                        st.markdown("<hr style='margin:2px 0; border-color:#eee;'>", unsafe_allow_html=True)
                    
                    st.markdown("#### 🔒 Data Saving Security Verification")
                    confirm_save = st.checkbox(f"I intentionally want to save/overwrite data for **{full_month}**.")
                    
if st.form_submit_button("💾 Save Entry to Database", use_container_width=True, type="primary"):
                        if not confirm_save:
                            st.error(f"❌ Action Denied! Please check the permission box above.")
                        else:
                            # 'else' এর পরের ব্লকটি অবশ্যই ডানে সরাতে হবে
                            for item in sheet_data:
                                supabase.table("monthly_attendance_records").upsert({
                                    "month_year": full_month,
                                    "emp_id": item['eid'],
                                    "present_days": item['p'],
                                    "absent_days": item['a'],
                                    "fine_amount": item['f'],
                                    "overtime_hours": item['oth'],
                                    "overtime_rate": item['otr'],
                                    "bonus_amount": item['bonus'],
                                    "advance_cut": item['adv']
                                }).execute()
                            st.success(f"✅ Successfully saved records for {full_month}!")
                            st.rerun()
st.markdown("---")
st.markdown("### 🖨️ Print Preview Panel (Live Database Sheet)")

            # --- MAIN SUMMARY SHEET WITH MATCHING ALIGNMENT FOR BULK VIEW ---
print_html = f"""
<div style="font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; padding: 25px; background: white; color: black; border-radius: 12px;">
                <div style="text-align: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #1F4E78;">
                    {"<div style='margin-bottom: 5px; display: block;'><img src='data:image/png;base64," + logo_base64_str + "' style='max-height: 70px; width: auto; object-fit: contain; display: inline-block;' alt='RECON Logo'></div>" if logo_base64_str else ""}
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; width: 100%;">
                    <div style="width: 20%;"></div>
                    <div style="width: 60%; text-align: center;">
                        <span style="font-size: 17px; color: #1F4E78; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;">Employee Monthly Payroll Statement Sheet</span>
                    </div>
                    <div style="width: 20%; text-align: right;">
                        <span style="font-size: 13px; color: #555; font-weight: 600; background-color: #f8f9fa; padding: 4px 10px; border-radius: 6px; border: 1px solid #e9ecef;">Period: {full_month}</span>
                    </div>
                </div>
            """

categories_list = ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"]
display_titles = ["💼 Managers Summary", "👔 Officers Summary", "🛠️ Workers (Permanent) Summary", "📆 Workers (Daily Basis) Summary"]
            
has_any_data = False
            for cat_name, title_text in zip(categories_list, display_titles):
                cat_rows = [r for r in rows if r[3] == cat_name]
                if not cat_rows: continue
                
                has_any_data = True
                print_html += f"""
                <h3 style="color: #1F4E78; border-left: 5px solid #1F4E78; padding-left: 10px; margin-top: 30px; margin-bottom: 12px; font-size: 16px; font-weight: 700;">{title_text}</h3>
                <div style="overflow-x: auto; max-width: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.02); border-radius: 6px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 12.5px; margin-bottom: 20px; background: white; min-width: 1150px;">
                        <thead>
                            <tr style="background-color: #1F4E78; color: white; text-align: center; font-weight: 600;">
                                <th style="border: 1px solid #dee2e6; padding: 8px;">ID</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left; width: 15%;">Employee Name</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Department</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px;">Base Pay</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px;">H.Rent</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px;">Medical</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px;">P/A Days</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; color: #ffbcbc;">Abs Cut</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; color: #ffbcbc;">Fine</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; color: #b4ffb4;">OT Earn</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; color: #b4ffb4;">Bonus</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; color: #ffbcbc;">Adv Cut</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; background-color: #163654; font-weight: 700;">Net Payable</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                for r in cat_rows:
                    eid, name, desg, cat, dept, base_sal = r
                    rec = saved_db_tracker.get(str(eid), {"present": days_in_month if cat == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                    
                    gross, house_rent, medical, _, ab_cut, net_p, adv_paid = calculate_salary_breakdown(base_sal, rec['absent'], rec['fine'], cat, rec['present'], rec['advance'])
                    ot_total = rec['ot_hrs'] * rec['ot_rate']
                    final_payable = net_p + ot_total + rec['bonus']
                    
                    print_html += f"""
                            <tr style="text-align: center; background-color: white; border-bottom: 1px solid #efefef;">
                                <td style="border: 1px solid #e9ecef; padding: 8px; font-weight: 700; color: #333;">{str(eid)}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: left; font-weight: 700; color: #1F4E78;">{name}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: left; color: #555;">{dept}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: right; font-weight: 500;">{base_sal:,.2f}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: right; color: #666;">{house_rent:,.2f}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: right; color: #666;">{medical:,.2f}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; font-weight: 500; color: #495057;">{rec['present']}P / {rec['absent']}A</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: right; color: #c00; font-weight: 500;">{ab_cut:,.2f}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: right; color: #c00; font-weight: 500;">{rec['fine']:,.2f}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: right; color: #1e7e34; font-weight: 500;">{ot_total:,.2f}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: right; color: #1e7e34; font-weight: 500;">{rec['bonus']:,.2f}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px; text-align: right; color: #c00; font-weight: 500;">{adv_paid:,.2f}</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right; font-weight: 700; color: #1F4E78; background-color: #f8f9fa; font-size: 13px;">{final_payable:,.2f}</td>
                            </tr>
                    """
                print_html += "</tbody></table></div>"
            print_html += "</div>"

# মূল ব্লক (যেকোনো একটি লেভেলে)
if rows: 
    # ব্লকের ভেতরের কোড (৪ স্পেস ডানে)
    if has_any_data:
        # আরও ৪ স্পেস ডানে
        st.components.v1.html(print_html, height=600, scrolling=True)
    else:
        # else টি if এর সাথে একই লাইনে
        st.info("No records loaded yet.")
else: 
    # মেইন if এর সাথে else টি সোজাসুজি
    st.info("Database is empty. Please add people from the left panel.")
