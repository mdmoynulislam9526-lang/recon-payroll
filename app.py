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

# --- MAIN DASHBOARD ---
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
        
        with tab_emp:
            categories_map = {"💼 Managers": "Manager", "👔 Officers": "Officer", "🛠️ Workers (Permanent)": "Worker (Permanent)", "📆 Workers (Daily Basis)": "Worker (Daily Basis)"}
            for title, cat_value in categories_map.items():
                cat_members = [r for r in rows if r['category'] == cat_value]
                with st.expander(f"{title} ({len(cat_members)})", expanded=False):
                    if not cat_members: st.info("No records.")
                    else:
                        for r in cat_members: render_inline_management(r, prefix="all_tab")

        with tab0:
            st.subheader("🔍 Search Employee")
            search_query = st.text_input("Enter Employee ID or Name to search", placeholder="Type here...", key="search_tab_input")
            if search_query:
                search_results = [r for r in rows if search_query.lower() in str(r['emp_id']).lower() or search_query.lower() in r['name'].lower()]
                for emp in search_results: render_inline_management(emp, prefix="search_tab")       

with tab1:
            st.subheader("📄 Employee Pay Slip Preview")
            
            # এমপ্লয়ি সিলেকশন
            emp_options = [f"{r['emp_id']} - {r['name']}" for r in rows]
            selected_emp_id = st.selectbox("Select Employee", emp_options, key="ps_select")
            
            # আইডি আলাদা করা
            selected_id = selected_emp_id.split(" - ")[0]
            
            # এমপ্লয়ি ডাটা খোঁজা
            selected_emp = next(r for r in rows if str(r['emp_id']) == selected_id)
            
            # ডাটাবেস থেকে ট্র্যাকার ডাটা নেয়া
            rec = saved_db_tracker.get(str(selected_id), {
                "present_days": 26, 
                "absent_days": 0, 
                "fine_amount": 0.0, 
                "overtime_hours": 0.0, 
                "overtime_rate": 0.0, 
                "bonus_amount": 0.0, 
                "advance_cut": 0.0
            })
            
            # স্যালারি ক্যালকুলেশন
            gross, house_rent, medical, _, absent_cut, net_p, adv_paid = calculate_salary_breakdown(
                selected_emp['salary'], 
                rec['absent_days'], 
                rec['fine_amount'], 
                selected_emp['category'], 
                rec['present_days'], 
                rec['advance_cut']
            )
            total_ot_emp = rec['overtime_hours'] * rec['overtime_rate']
            net_final = net_p + total_ot_emp + rec['bonus_amount']
            
            # সিগনেচার লজিক
            sig_html_element = f"<img src='data:image/png;base64,{sig_base64_str}' style='width: 150px;'>" if 'sig_base64_str' in locals() and sig_base64_str else "____________________"
            
            # Pay Slip HTML Design (সংশোধিত টেবিল অংশ)
            payslip_preview_html = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 35px; background: white; color: black; border: 1px solid #c8d6e5; border-radius: 8px; max-width: 700px; margin: 15px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.06);">
                <div style="text-align: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #1F4E78;">
                    {"<img src='data:image/png;base64," + logo_base64_str + "' style='max-height: 65px;'>" if 'logo_base64_str' in locals() and logo_base64_str else ""}
                </div>
                <div style="text-align: center; font-weight: 700; color: #1F4E78; margin-bottom: 20px;">EMPLOYEE PAY SLIP - {full_month}</div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px;">
                    <tr><td style="padding: 5px; border: 1px solid #ddd;">ID: #{selected_emp['emp_id']}</td><td style="padding: 5px; border: 1px solid #ddd;">Dept: {selected_emp['department']}</td></tr>
                    <tr><td style="padding: 5px; border: 1px solid #ddd;">Name: {selected_emp['name']}</td><td style="padding: 5px; border: 1px solid #ddd;">Desig: {selected_emp['designation']}</td></tr>
                </table>

                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr style="background-color: #f8fafc;"><th>Earnings</th><th>Amount</th><th>Deductions</th><th>Amount</th></tr>
                    <tr><td>Base Pay</td><td>{selected_emp['salary']:,.2f}</td><td>Absent Cut</td><td>{absent_cut:,.2f}</td></tr>
                    <tr><td>OT Earned</td><td>{total_ot_emp:,.2f}</td><td>Fine</td><td>{rec['fine_amount']:,.2f}</td></tr>
                    <tr><td>Bonus</td><td>{rec['bonus_amount']:,.2f}</td><td>Advance</td><td>{adv_paid:,.2f}</td></tr>
                    <tr style="border-top: 2px solid #1F4E78; font-weight: bold;"><td>Net Payable</td><td>Tk {net_final:,.2f}</td><td></td><td></td></tr>
                </table>

                <div style="margin-top: 40px; text-align: right;">{sig_html_element}<br>Authorized Signature</div>
            </div>
            """
            st.components.v1.html(payslip_preview_html, height=560, scrolling=True)
            
            # PDF Download Button
            pdf_emp_data = (selected_emp['emp_id'], selected_emp['name'], selected_emp['designation'], selected_emp['category'], selected_emp['department'], house_rent, medical, adv_paid, net_final)
            pdf_buf = BytesIO()
            generate_pdf_bytes(pdf_emp_data, full_month, rec['absent_days'], rec['fine_amount'], rec['present_days'], pdf_buf)
            st.download_button(
                label="📥 Download Pay Slip",
                data=pdf_buf.getvalue(),
                file_name=f"Pay_Slip_{selected_emp['name']}_{full_month}.pdf",
                mime="application/pdf"
            )                
with tab2:
    view_cat = st.selectbox("Select Category to Process", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"], key="att_sheet_cat")
    
    # ডাটাবেসের ক্যাটাগরির সাথে মিলানোর জন্য .strip() ব্যবহার করা ভালো
    filtered_rows = [r for r in rows if r['category'] == view_cat]
    
    if filtered_rows:
        # ফর্ম শুরু হচ্ছে
        with st.form(key=f"bulk_sheet_form_{view_cat.replace(' ', '_')}"):
            sheet_data = [] 
            
            for r in filtered_rows:
                st.markdown(f"**🔹 {r['emp_id']} - {r['name']}**")
                
                # ডাটাবেস থেকে বর্তমান মানগুলো নেওয়া
                rec = saved_db_tracker.get(str(r['emp_id']), {"present_days": days_in_month, "absent_days": 0, "fine_amount": 0.0, "overtime_hours": 0.0, "overtime_rate": 0.0, "bonus_amount": 0.0, "advance_cut": 0.0})
                
                col_in1, col_in2, col_in3 = st.columns(3)
                with col_in1:
                    a_d = st.number_input("Absent Days", 0, 31, int(rec.get('absent_days', 0)), key=f"a_{r['emp_id']}")
                    f_d = st.number_input("Fine (Tk)", 0.0, value=float(rec.get('fine_amount', 0.0)), key=f"f_{r['emp_id']}")
                with col_in2:
                    ot_h = st.number_input("OT Hours", 0.0, 200.0, value=float(rec.get('overtime_hours', 0.0)), key=f"oth_{r['emp_id']}")
                    ot_r = st.number_input("OT Rate", 0.0, 1000.0, value=float(rec.get('overtime_rate', 0.0)), key=f"otr_{r['emp_id']}")
                with col_in3:
                    bonus_amt = st.number_input("Bonus", 0.0, 200000.0, value=float(rec.get('bonus_amount', 0.0)), key=f"bn_{r['emp_id']}")
                    adv_cut = st.number_input("Adv Cut", 0.0, 200000.0, value=float(rec.get('advance_cut', 0.0)), key=f"adv_{r['emp_id']}")
                
                sheet_data.append({
                    'eid': r['emp_id'], 'p': days_in_month - a_d, 'a': a_d, 
                    'f': f_d, 'oth': ot_h, 'otr': ot_r, 'bonus': bonus_amt, 'adv': adv_cut
                })
            
            # সাবমিট বাটনটি অবশ্যই ফর্মের ভেতরে থাকতে হবে
            submitted = st.form_submit_button("💾 Save Entry to Database")
        
        # ফর্ম সাবমিট হলে ডাটাবেসে আপডেট করা (ফর্মের বাইরে)
        if submitted:
            try:
                for item in sheet_data:
                    supabase.table("monthly_attendance_records").upsert({
                        "month_year": str(full_month), 
                        "emp_id": int(item['eid']), 
                        "present_days": int(item['p']),
                        "absent_days": int(item['a']),
                        "fine_amount": float(item['f']),
                        "overtime_hours": float(item['oth']),
                        "overtime_rate": float(item['otr']),
                        "bonus_amount": float(item['bonus']),
                        "advance_cut": float(item['adv'])
                    }).execute()
                st.success("সফলভাবে সেভ হয়েছে! 🎉")
                st.rerun()
            except Exception as e:
                st.error(f"❌ ডাটাবেস এরর: {e}")
    else:
        st.info("এই ক্যাটাগরিতে কোনো এমপ্লয়ি নেই।")
with tab3:
            st.subheader("📊 Attendance & Processor")
            
            # Form starts here
            with st.form("attendance_processor_form"):
                cat_to_process = st.selectbox("Select Category to Process", 
                                            ["Officer", "Manager", "Worker (Permanent)", "Worker (Daily Basis)"])
                
                # Submit button (Form এর ভেতরে)
                submitted = st.form_submit_button("Process Attendance")
            
            # Logic starts here (Form এর বাইরে, কিন্তু ট্যাব এর ভেতরে)
            if submitted:
                st.write(f"Processing data for: {cat_to_process}...")
                
                # --- MAIN SUMMARY SHEET ---
                print_html = f"""
                <div style="font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; padding: 25px; background: white; color: black; border-radius: 12px;">
                    <div style="text-align: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #1F4E78;">
                        {"<div style='margin-bottom: 5px; display: block;'><img src='data:image/png;base64," + logo_base64_str + "' style='max-height: 70px; width: auto; object-fit: contain; display: inline-block;' alt='RECON Logo'></div>" if 'logo_base64_str' in locals() else ""}
                    </div>
                    <div style="text-align: center; font-weight: 700; color: #1F4E78; margin-bottom: 20px;">Employee Monthly Payroll Statement Sheet</div>
                """

                categories_list = ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"]
                display_titles = ["💼 Managers Summary", "👔 Officers Summary", "🛠️ Workers (Permanent) Summary", "📆 Workers (Daily Basis) Summary"]
                
                for cat_name, title_text in zip(categories_list, display_titles):
                    cat_rows = [r for r in rows if r['category'] == cat_name]
                    if not cat_rows: continue
                    
                    print_html += f"""
                    <h3 style="color: #1F4E78; border-left: 5px solid #1F4E78; padding-left: 10px; margin-top: 30px; margin-bottom: 12px; font-size: 16px; font-weight: 700;">{title_text}</h3>
                    <div style="overflow-x: auto; max-width: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.02); border-radius: 6px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 12.5px; margin-bottom: 20px; background: white; min-width: 1150px;">
                            <thead>
                                <tr style="background-color: #1F4E78; color: white; text-align: center; font-weight: 600;">
                                    <th style="border: 1px solid #dee2e6; padding: 8px;">ID</th>
                                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Name</th>
                                    <th style="border: 1px solid #dee2e6; padding: 8px;">Net Payable</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                    
                    for r in cat_rows:
                        eid, name = r['emp_id'], r['name']
                        # Data check
                        rec = saved_db_tracker.get(str(eid), {"present_days": 26, "absent_days": 0, "fine_amount": 0.0, "overtime_hours": 0.0, "overtime_rate": 0.0, "bonus_amount": 0.0, "advance_cut": 0.0})
                        
                        gross, house_rent, medical, _, ab_cut, net_p, adv_paid = calculate_salary_breakdown(
                            r['salary'], rec['absent_days'], rec['fine_amount'], cat_name, rec['present_days'], rec['advance_cut']
                        )
                        final_payable = net_p + (rec['overtime_hours'] * rec['overtime_rate']) + rec['bonus_amount']

                        print_html += f"""
                            <tr>
                                <td style="border: 1px solid #e9ecef; padding: 8px;">{eid}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px;">{name}</td>
                                <td style="border: 1px solid #e9ecef; padding: 8px;">{final_payable:,.2f}</td>
                            </tr>
                        """
                    print_html += "</tbody></table></div>"
                
                print_html += "</div>"
                st.components.v1.html(print_html, height=800, scrolling=True)
            
            else:
                st.info("Please select a category and click 'Process Attendance' to start.")
# --- NEW TAB: DASHBOARD SUMMARY ---
with tab4:
    st.subheader("📑 Summary Sheet")
    
    if rows:
        # টেবিল তৈরির জন্য HTML শুরু
        print_html = """
        <div style="font-family: Arial, sans-serif; padding: 15px;">
            <h2 style="color: #1F4E78;">Employee Monthly Summary</h2>
            <table border='1' style='width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;'>
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th>ID</th><th>Name</th><th>Category</th><th>Net Payable</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # ক্যালকুলেশন লজিক এবং টেবিল রো তৈরি
        for r in rows:
            # ডাটাবেস থেকে ট্র্যাকার ডাটা সংগ্রহ
            rec = saved_db_tracker.get(str(r['emp_id']), {
                "present_days": 26, "absent_days": 0, "fine_amount": 0.0, 
                "overtime_hours": 0.0, "overtime_rate": 0.0, "bonus_amount": 0.0, "advance_cut": 0.0
            })
            
            # ক্যালকুলেশন ফাংশন কল করা
            gross, house_rent, medical, _, ab_cut, net_p, adv_paid = calculate_salary_breakdown(
                r['salary'], 
                rec['absent_days'], 
                rec['fine_amount'], 
                r['category'], 
                rec['present_days'], 
                rec['advance_cut']
            )
            
            # চূড়ান্ত হিসাব
            final_payable = net_p + (rec['overtime_hours'] * rec['overtime_rate']) + rec['bonus_amount']
            
            # টেবিলের রো যোগ করা
            print_html += f"<tr><td>{r['emp_id']}</td><td>{r['name']}</td><td>{r['category']}</td><td>{final_payable:,.2f}</td></tr>"
        
        print_html += "</tbody></table></div>"
        
        # HTML ডিসপ্লে করা
        st.components.v1.html(print_html, height=500, scrolling=True)
        
        # প্রিন্ট বাটন
        if st.button("🖨️ Print Full Sheet"):
            st.components.v1.html(f"<script>window.print();</script>{print_html}", height=0)
    else:
        st.info("No records loaded yet.")
