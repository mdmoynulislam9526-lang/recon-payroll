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
local_sig_path = os.path.join(current_dir, "signature.png")
if os.path.exists(local_sig_path):
    with open(local_sig_path, "rb") as img_file:
        sig_base64_str = base64.b64encode(img_file.read()).decode('utf-8')

seal_base64_str = ""
local_seal_path = os.path.join(current_dir, "seal.png")
if os.path.exists(local_seal_path):
    with open(local_seal_path, "rb") as img_file:
        seal_base64_str = base64.b64encode(img_file.read()).decode('utf-8')

st.title("💼 RECON LABORATORIES LTD - Advanced Payroll Management System")
st.markdown("---")

col1, col2 = st.columns([1, 2.3])

with col1:
    st.header("➕ Add New Person")
    if "emp_id_val" not in st.session_state: st.session_state.emp_id_val = ""
    if "name_val" not in st.session_state: st.session_state.name_val = ""
    if "desg_val" not in st.session_state: st.session_state.desg_val = ""
    if "salary_val" not in st.session_state: st.session_state.salary_val = ""

    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("ID (Numbers only)", value=st.session_state.emp_id_val).strip()
        name = st.text_input("Name", value=st.session_state.name_val)
        department = st.selectbox("Select Department", ["Production", "Quality Control", "Development", "Maintenance", "Accounts & Finance", "HR & Admin", "Store & Inventory", "Sales & Marketing"])
        category = st.selectbox("Select Category", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
        designation = st.text_input("Designation", value=st.session_state.desg_val)
        salary = st.text_input("Gross Salary / Daily Wage Rate (Tk)", value=st.session_state.salary_val)
        
        if st.form_submit_button("Add to Database", use_container_width=True, type="primary"):
            st.session_state.emp_id_val = input_id
            st.session_state.name_val = name
            st.session_state.desg_val = designation
            st.session_state.salary_val = salary
            if not (input_id and name and designation and salary):
                st.error("Please fill all fields!")
            elif not re.match(r"^[0-9]+$", input_id):
                st.error("⚠️ Invalid ID Format!")
            else:
                try:
                    # Supabase Insert Operation
                    supabase.table("employees_final_version").insert({
                        "emp_id": input_id, 
                        "name": name, 
                        "designation": designation, 
                        "category": category, 
                        "department": department, 
                        "salary": float(salary)
                    }).execute()
                    st.success(f"{name} added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Error: {e}")

def render_inline_management(r, prefix=""):
    # Dictionary access for Supabase response
    eid, ename, edesg, ecat, edept, esalary = r['emp_id'], r['name'], r['designation'], r['category'], r['department'], r['salary']
    with st.container():
        col_info, col_act1, col_act2 = st.columns([3, 0.6, 0.6])
        with col_info:
            st.markdown(f"**[{eid}] {ename}** — {edesg} ({edept}) | Tk {esalary:,.2f}")
        with col_act1:
            if st.button("Edit 📝", key=f"{prefix}_edit_{eid}"): st.session_state[f"emode_{prefix}_{eid}"] = True
        with col_act2:
            if st.button("Delete ❌", key=f"{prefix}_del_{eid}", type="secondary"):
                # Supabase Delete Operation
                supabase.table("employees_final_version").delete().eq("emp_id", eid).execute()
                supabase.table("monthly_attendance_records").delete().eq("emp_id", eid).execute()
                st.rerun()
        if st.session_state.get(f"emode_{prefix}_{eid}", False):
            with st.form(key=f"form_{prefix}_{eid}"):
                ch_name = st.text_input("Name", value=ename)
                ch_salary = st.text_input("Salary", value=str(esalary))
                if st.form_submit_button("Save"):
                    # Supabase Update Operation
                    supabase.table("employees_final_version").update({
                        "name": ch_name, 
                        "salary": float(ch_salary)
                    }).eq("emp_id", eid).execute()
                    st.session_state[f"emode_{prefix}_{eid}"] = False
                    st.rerun()
# --- TAB 1: INDIVIDUAL PAY SLIP (CLASSIC OFFICE TABLE DESIGN) ---
        with tab1:
            pay_search = st.text_input("Enter Employee ID or Name for Pay Slip", key="pay_slip_search_input")
            if pay_search:
                # Supabase ফিল্টার ব্যবহার করা হয়েছে
                pay_results = [r for r in rows if pay_search.lower() in str(r['emp_id']).lower() or pay_search.lower() in r['name'].lower()]
                if pay_results:
                    selected_emp = pay_results[0]
                    # ডিকশনারি কী ব্যবহার করা হয়েছে
                    rec = saved_db_tracker.get(str(selected_emp['emp_id']), {"present": days_in_month if selected_emp['category'] == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                    
                    st.success(f"Selected: {selected_emp['name']} ({selected_emp['emp_id']})")
                    
                    gross, house_rent, medical, _, absent_cut, net_p, adv_paid = calculate_salary_breakdown(
                        selected_emp['salary'], rec['absent'], rec['fine'], selected_emp['category'], rec['present'], rec['advance']
                    )
                    
                    total_ot_emp = rec['ot_hrs'] * rec['ot_rate']
                    net_final = net_p + total_ot_emp + rec['bonus']
                    
                    # ... (sig_html_element লজিক একই থাকবে)

                    payslip_preview_html = f"""
                    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 35px; background: white; color: black; border: 1px solid #c8d6e5; border-radius: 8px; max-width: 700px; margin: 15px auto;">
                        <div style="text-align: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #1F4E78;">
                            {"<img src='data:image/png;base64," + logo_base64_str + "' style='max-height: 65px;'>" if logo_base64_str else ""}
                        </div>
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px; border: 1px solid #cbd5e1;">
                            <tr>
                                <td style="padding: 10px; border: 1px solid #cbd5e1;">Employee ID</td>
                                <td style="padding: 10px; border: 1px solid #cbd5e1;">#{selected_emp['emp_id']}</td>
                                <td style="padding: 10px; border: 1px solid #cbd5e1;">Department</td>
                                <td style="padding: 10px; border: 1px solid #cbd5e1;">{selected_emp['department']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #cbd5e1;">Full Name</td>
                                <td style="padding: 10px; border: 1px solid #cbd5e1;">{selected_emp['name']}</td>
                                <td style="padding: 10px; border: 1px solid #cbd5e1;">Designation</td>
                                <td style="padding: 10px; border: 1px solid #cbd5e1;">{selected_emp['designation']}</td>
                            </tr>
                        </table>
                        <p>Net Payable Salary: Tk {net_final:,.2f}</p>
                    </div>
                    """
                    st.components.v1.html(payslip_preview_html, height=560, scrolling=True)

      # --- TAB 2: ATTENDANCE & PROCESSOR ---
with tab2:
    view_cat = st.selectbox("Select Category to Process", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"], key="att_sheet_cat")
    filtered_rows = [r for r in rows if r['category'] == view_cat]
    
    sheet_data = [] # এটি লুপের বাইরে থাকবে
    
    if filtered_rows:
        with st.form("bulk_sheet_form_v5"):
            for r in filtered_rows:
                st.markdown(f"**🔹 {r['emp_id']} - {r['name']}** ({r['designation']})")
                rec = saved_db_tracker.get(str(r['emp_id']), {"present": days_in_month if r['category'] == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                
                col_in1, col_in2, col_in3 = st.columns(3)
                with col_in1:
                    total_target_days = st.number_input("Total Target Days", 1, 100, int(rec['present'] + rec['absent']) if rec['absent'] > 0 else (days_in_month if r['category'] == 'Worker (Daily Basis)' else 26), key=f"target_{r['emp_id']}")
                    a_d = st.number_input("Absent Days", 0, total_target_days, int(rec['absent']), key=f"a_{r['emp_id']}")
                    f_d = st.number_input("Penalty/Fine (Tk)", 0.0, value=float(rec['fine']), key=f"f_{r['emp_id']}")
                with col_in2:
                    ot_h = st.number_input("Overtime Hours", 0.0, 200.0, value=float(rec['ot_hrs']), key=f"oth_{r['emp_id']}")
                    ot_r = st.number_input("OT Rate per Hour (Tk)", 0.0, 1000.0, value=float(rec['ot_rate']), key=f"otr_{r['emp_id']}")
                with col_in3:
                    bonus_amt = st.number_input("Bonus Amount (Tk)", 0.0, 200000.0, value=float(rec['bonus']), key=f"bn_{r['emp_id']}")
                    adv_cut = st.number_input("Advanced Salary Cut (Tk)", 0.0, 200000.0, value=float(rec['advance']), key=f"adv_{r['emp_id']}")
                
                p_d = total_target_days - a_d
                
                # সঠিক সিনট্যাক্স:
                sheet_data.append({
                    'eid': r['emp_id'], 
                    'p': p_d, 
                    'a': a_d, 
                    'f': f_d, 
                    'oth': ot_h, 
                    'otr': ot_r, 
                    'bonus': bonus_amt, 
                    'adv': adv_cut
                })
                st.markdown("<hr style='margin:2px 0; border-color:#eee;'>", unsafe_allow_html=True)
            
            if st.form_submit_button("💾 Save Entry to Database", use_container_width=True, type="primary"):
                for item in sheet_data:
                    supabase.table("monthly_attendance_records").upsert({
                        "month_year": full_month,
                        "emp_id": item['eid'],
                        "present": item['p'],
                        "absent": item['a'],
                        "fine": item['f'],
                        "ot_hrs": item['oth'],
                        "ot_rate": item['otr'],
                        "bonus": item['bonus'],
                        "advance": item['adv']
                    }).execute()
                st.success(f"✅ Successfully saved records for {full_month}!")
                st.rerun()
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
                # Supabase ফিল্টারিং
                cat_rows = [r for r in rows if r['category'] == cat_name]
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
                    # ডিকশনারি কী এক্সেস
                    eid, name, dept, cat, base_sal = r['emp_id'], r['name'], r['department'], r['category'], r['salary']
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

            if has_any_data:
                st.components.v1.html(print_html, height=600, scrolling=True)
                if st.button("🖨️ CLICK HERE TO PRINT THIS FULL SHEET", use_container_width=True, type="primary"):
                    st.components.v1.html(f"{print_html}<script>window.print();</script>", height=0)
            else:
                st.info("No records loaded yet.")
                
    else: st.info("Database is empty. Please add people from the left panel.")
