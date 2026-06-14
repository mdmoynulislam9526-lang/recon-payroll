import streamlit as st
import sqlite3
from datetime import datetime
import calendar
from io import BytesIO
import pandas as pd
import re  # আইডি ফরম্যাট চেক করার জন্য রেগুলার এক্সপ্রেশন লাইব্রেরি
from calculations import calculate_salary_breakdown, generate_pdf_bytes

st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect("payroll_v5.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees_final_version (
            emp_id TEXT PRIMARY KEY, name TEXT NOT NULL, designation TEXT NOT NULL,
            category TEXT NOT NULL, department TEXT NOT NULL, salary REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_attendance_records (
            month_year TEXT, emp_id TEXT, present_days INTEGER, absent_days INTEGER, 
            fine_amount REAL, overtime_hours REAL, overtime_rate REAL, bonus_amount REAL, advance_cut REAL,
            PRIMARY KEY (month_year, emp_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("payroll_v5.db", check_same_thread=False)

st.title("💼 RECON LABORATORIES LTD - Advanced Payroll Management System")
st.markdown("---")

col1, col2 = st.columns([1, 2.3])

# --- LEFT SIDE: ADD EMPLOYEE ---
with col1:
    st.header("➕ Add New Person")
    
    # ইনপুট ভ্যালুগুলো সেশন স্টেটে ধরে রাখার ব্যবস্থা (যাতে ভুলের কারণে মুছে না যায়)
    if "emp_id_val" not in st.session_state: st.session_state.emp_id_val = ""
    if "name_val" not in st.session_state: st.session_state.name_val = ""
    if "desg_val" not in st.session_state: st.session_state.desg_val = ""
    if "salary_val" not in st.session_state: st.session_state.salary_val = ""

    # clear_on_submit=True দেওয়া হলো যাতে সাবমিট সফল হলে স্ট্রিমলিট অটো ফরম খালি করে দেয়
    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("ID (Numbers only, e.g., 101)", value=st.session_state.emp_id_val).strip()
        name = st.text_input("Name", value=st.session_state.name_val)
        department = st.selectbox("Select Department", [
            "Production", "Quality Control", "Development",
            "Maintenance", "Accounts & Finance", "HR & Admin", "Store & Inventory", "Sales & Marketing"
        ])
        category = st.selectbox("Select Category", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
        designation = st.text_input("Designation", value=st.session_state.desg_val)
        salary = st.text_input("Gross Salary / Daily Wage Rate (Tk)", value=st.session_state.salary_val)
        
        if st.form_submit_button("Add to Database", use_container_width=True, type="primary"):
            # ভ্যালিডেশন চেক করার সময় সাময়িকভাবে সেশন স্টেটে ডাটা ধরে রাখা (যাতে ভুল হলে ইনপুট মুছে না যায়)
            st.session_state.emp_id_val = input_id
            st.session_state.name_val = name
            st.session_state.desg_val = designation
            st.session_state.salary_val = salary
            
            if not (input_id and name and designation and salary):
                st.error("Please fill all fields!")
            
            # আইডি ভ্যালিডেশন: শুধু সংখ্যা হতে হবে
            elif not re.match(r"^[0-9]+$", input_id):
                st.error("⚠️ Invalid ID Format! ID must only contain numbers (No letters or spaces allowed). e.g., 101, 2045")
                
            else:
                try:
                    conn = get_db_connection()
                    conn.cursor().execute("INSERT INTO employees_final_version VALUES (?, ?, ?, ?, ?, ?)",
                                   (input_id, name, designation, category, department, float(salary)))
                    conn.commit()
                    conn.close()
                    
                    st.success(f"{name} successfully added!")
                    
                    # ডাটাবেজে সফলভাবে যুক্ত হওয়ার পরই কেবল সেশন স্টেট পুরো খালি করে দেওয়া হবে
                    st.session_state.emp_id_val = ""
                    st.session_state.name_val = ""
                    st.session_state.desg_val = ""
                    st.session_state.salary_val = ""
                    
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"⚠️ Warning: Employee ID '{input_id}' already exists!")
                except ValueError: 
                    st.error("Salary must be a number!")

# --- REUSABLE FUNCTION FOR EDIT/DELETE ---
def render_inline_management(r, prefix=""):
    eid, ename, edesg, ecat, edept, esalary = r
    with st.container():
        col_info, col_act1, col_act2 = st.columns([3, 0.6, 0.6])
        with col_info:
            st.markdown(f"**[{eid}] {ename}** — {edesg} ({edept}) | Salary: Tk {esalary:,.2f}")
        with col_act1:
            if st.button("Edit 📝", key=f"{prefix}_edit_{eid}", use_container_width=True):
                st.session_state[f"emode_{prefix}_{eid}"] = True
        with col_act2:
            if st.button("Delete ❌", key=f"{prefix}_del_{eid}", use_container_width=True, type="secondary"):
                st.session_state[f"dmode_{prefix}_{eid}"] = True

        if st.session_state.get(f"emode_{prefix}_{eid}", False):
            with st.form(key=f"form_{prefix}_{eid}"):
                ch_name = st.text_input("Edit Name", value=ename)
                dept_list = ["Production", "Quality Control", "Development", "Maintenance", "Accounts & Finance", "HR & Admin", "Store & Inventory", "Sales & Marketing"]
                ch_dept = st.selectbox("Edit Department", dept_list, index=dept_list.index(edept) if edept in dept_list else 0)
                cat_list = ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"]
                ch_cat = st.selectbox("Edit Category", cat_list, index=cat_list.index(ecat) if ecat in cat_list else 0)
                ch_desg = st.text_input("Edit Designation", value=edesg)
                ch_salary = st.text_input("Edit Salary/Rate", value=str(esalary))
                
                b1, b2 = st.columns(2)
                with b1:
                    if st.form_submit_button("Save Changes", use_container_width=True):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE employees_final_version SET name=?, designation=?, category=?, department=?, salary=? WHERE emp_id=?", (ch_name, ch_desg, ch_cat, ch_dept, float(ch_salary), eid))
                        conn.commit()
                        conn.close()
                        st.session_state[f"emode_{prefix}_{eid}"] = False
                        st.success("Updated!")
                        st.rerun()
                with b2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state[f"emode_{prefix}_{eid}"] = False
                        st.rerun()

        if st.session_state.get(f"dmode_{prefix}_{eid}", False):
            st.warning(f"Remove **{ename} ({eid})**?")
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("Yes, Delete", key=f"c_del_{prefix}_{eid}", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    conn.cursor().execute("DELETE FROM employees_final_version WHERE emp_id = ?", (eid,))
                    conn.cursor().execute("DELETE FROM monthly_attendance_records WHERE emp_id = ?", (eid,))
                    conn.commit()
                    conn.close()
                    st.session_state[f"dmode_{prefix}_{eid}"] = False
                    st.rerun()
            with dc2:
                if st.button("Cancel", key=f"c_can_{prefix}_{eid}", use_container_width=True):
                    st.session_state[f"dmode_{prefix}_{eid}"] = False
                    st.rerun()
        st.markdown("<hr style='margin:4px 0px; border-color:#eee;'>", unsafe_allow_html=True)

# --- RIGHT SIDE: PAYROLL MANAGEMENT ---
with col2:
    conn = get_db_connection()
    rows = conn.cursor().execute("SELECT * FROM employees_final_version").fetchall()
    conn.close()
    
    if rows:
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        c_col1, c_col2 = st.columns(2)
        with c_col1: select_m = st.selectbox("Select Month", months_list, index=int(datetime.now().strftime("%m")) - 1)
        with c_col2: select_y = st.selectbox("Select Year", [str(y) for y in range(2024, 2031)], index=2)
        full_month = f"{select_m}, {select_y}"
        
        month_num = months_list.index(select_m) + 1
        days_in_month = calendar.monthrange(int(select_y), month_num)[1]
        
        conn = get_db_connection()
        db_records = conn.cursor().execute("SELECT * FROM monthly_attendance_records WHERE month_year=?", (full_month,)).fetchall()
        conn.close()
        
        saved_db_tracker = {r[1]: {"present": r[2], "absent": r[3], "fine": r[4], "ot_hrs": r[5], "ot_rate": r[6], "bonus": r[7], "advance": r[8]} for r in db_records}

        total_payout, total_fine, total_bonus, total_advance = 0.0, 0.0, 0.0, 0.0
        for r in rows:
            eid, _, _, cat, _, base_sal = r
            rec = saved_db_tracker.get(eid, {"present": days_in_month if cat == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
            
            calc_salary = base_sal
            if cat != 'Worker (Daily Basis)' and rec['present'] < 26:
                calc_salary = (base_sal / 26) * rec['present']
                
            _, _, _, _, ab_cut, net_p, _ = calculate_salary_breakdown(calc_salary, rec['absent'], rec['fine'], cat, rec['present'])
            net_final = net_p + (rec['ot_hrs'] * rec['ot_rate']) + rec['bonus'] - rec['advance']
            total_payout += net_final
            total_fine += rec['fine'] + ab_cut
            total_bonus += rec['bonus']
            total_advance += rec['advance']

        st.markdown("### 📊 Financial Dashboard Summary")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Employees", len(rows))
        m_col2.metric("Total Payout (Tk)", f"{total_payout:,.2f}")
        m_col3.metric("Total Deductions (Fine+Absent)", f"{total_fine:,.2f}")
        m_col4.metric("Total Bonuses Distributed", f"{total_bonus:,.2f}")
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

        with tab1:
            pay_search = st.text_input("Enter Employee ID or Name for Pay Slip", key="pay_slip_search_input")
            if pay_search:
                pay_results = [r for r in rows if pay_search.lower() in r[0].lower() or pay_search.lower() in r[1].lower()]
                if pay_results:
                    selected_emp = pay_results[0]
                    rec = saved_db_tracker.get(selected_emp[0], {"present": days_in_month if selected_emp[3] == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                    
                    st.success(f"Selected: {selected_emp[1]} ({selected_emp[0]})")
                    
                    calc_salary = selected_emp[5]
                    if selected_emp[3] != 'Worker (Daily Basis)' and rec['present'] < 26:
                        calc_salary = (selected_emp[5] / 26) * rec['present']

                    _, _, _, _, ab_cut, net_p, _ = calculate_salary_breakdown(calc_salary, rec['absent'], rec['fine'], selected_emp[3], rec['present'])
                    net_final = net_p + (rec['ot_hrs'] * rec['ot_rate']) + rec['bonus'] - rec['advance']
                    
                    st.markdown(f"#### **Net Payable Salary:** Tk {net_final:,.2f}")
                    
                    pdf_buf = BytesIO()
                    generate_pdf_bytes((selected_emp[0], selected_emp[1], selected_emp[2], selected_emp[3], selected_emp[4], calc_salary + (rec['ot_hrs'] * rec['ot_rate']) + rec['bonus'] - rec['advance']), full_month, rec['absent'], rec['fine'], rec['present'], pdf_buf)
                    st.download_button("📥 Download Pay Slip (PDF)", data=pdf_buf.getvalue(), file_name=f"PaySlip_{selected_emp[0]}_{select_m}.pdf", mime="application/pdf", use_container_width=True)

        with tab2:
            view_cat = st.selectbox("Select Category to Process", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"], key="att_sheet_cat")
            filtered_rows = [r for r in rows if r[3] == view_cat]
            
            search_emp_input = st.text_input(f"🔍 Search Person within {view_cat}", placeholder="Type Name/ID...", key="s_att_search_box")
            final_display_rows = [r for r in filtered_rows if search_emp_input.lower() in r[0].lower() or search_emp_input.lower() in r[1].lower()] if search_emp_input else filtered_rows

            sheet_data = []
            if final_display_rows:
                with st.form("bulk_sheet_form_v5"):
                    st.markdown(f"##### 📝 Editing Attendance & Financials for {len(final_display_rows)} Person(s)")
                    for r in final_display_rows:
                        st.markdown(f"**🔹 {r[0]} - {r[1]}** ({r[2]})")
                        rec = saved_db_tracker.get(r[0], {"present": days_in_month if r[3] == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                        
                        col_in1, col_in2, col_in3 = st.columns(3)
                        with col_in1:
                            if r[3] == 'Worker (Daily Basis)':
                                total_target_days = st.number_input("Total Target Month Days (Base)", 1, 100, int(rec['present'] + rec['absent']) if rec['absent'] > 0 else days_in_month, key=f"target_{r[0]}")
                                a_d = st.number_input("Absent Days", 0, total_target_days, int(rec['absent']), key=f"a_{r[0]}")
                                p_d = total_target_days - a_d
                                st.markdown(f"📊 *Auto Present Calculated:* **{p_d} Days**")
                            else:
                                total_target_days = st.number_input("Total Target Month Days (Base)", 1, 100, int(rec['present'] + rec['absent']) if rec['absent'] > 0 else max(26, int(rec['present'])), key=f"target_{r[0]}")
                                a_d = st.number_input("Absent Days", 0, total_target_days, int(rec['absent']), key=f"a_{r[0]}")
                                p_d = total_target_days - a_d
                                st.markdown(f"📊 *Auto Present Calculated:* **{p_d} Days**")
                                
                            f_d = st.number_input("Penalty/Fine (Tk)", 0.0, value=float(rec['fine']), key=f"f_{r[0]}")
                        
                        with col_in2:
                            ot_h = st.number_input("Overtime Hours", 0.0, 200.0, value=float(rec['ot_hrs']), key=f"oth_{r[0]}")
                            ot_r = st.number_input("OT Rate per Hour (Tk)", 0.0, 1000.0, value=float(rec['ot_rate']), key=f"otr_{r[0]}")
                        
                        with col_in3:
                            bonus_amt = st.number_input("Bonus Amount (Tk)", 0.0, 200000.0, value=float(rec['bonus']), key=f"bn_{r[0]}")
                            adv_cut = st.number_input("Advance Salary Cut (Tk)", 0.0, 200000.0, value=float(rec['advance']), key=f"adv_{r[0]}")
                        
                        sheet_data.append({'eid': r[0], 'p': p_d, 'a': a_d, 'f': f_d, 'oth': ot_h, 'otr': ot_r, 'bonus': bonus_amt, 'adv': adv_cut})
                        st.markdown("<hr style='margin:2px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("💾 Save Entry to Database", use_container_width=True, type="primary"):
                        conn = get_db_connection()
                        for item in sheet_data:
                            conn.cursor().execute("""
                                INSERT OR REPLACE INTO monthly_attendance_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (full_month, item['eid'], item['p'], item['a'], item['f'], item['oth'], item['otr'], item['bonus'], item['adv']))
                        conn.commit()
                        conn.close()
                        st.success(f"Successfully saved records for {full_month} into system permanent storage!")
                        st.rerun()

            st.markdown("### 👁️ Current Month Full Payroll Sheets Overview")
            categories_list = ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"]
            display_titles = ["💼 Managers", "👔 Officers", "🛠️ Workers - Permanent", "📆 Workers - Daily Basis"]
            
            for cat_name, title_text in zip(categories_list, display_titles):
                cat_rows = [r for r in rows if r[3] == cat_name]
                tracker_table = []
                
                for r in cat_rows:
                    eid, name, desg, cat, dept, base_sal = r
                    rec = saved_db_tracker.get(eid, {"present": days_in_month if cat == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                    
                    calc_salary = base_sal
                    if cat != 'Worker (Daily Basis)' and rec['present'] < 26:
                        calc_salary = (base_sal / 26) * rec['present']

                    _, _, _, _, ab_cut, net_p, _ = calculate_salary_breakdown(calc_salary, rec['absent'], rec['fine'], cat, rec['present'])
                    
                    display_absent = rec['absent']
                    ot_total = rec['ot_hrs'] * rec['ot_rate']
                    final_payable = net_p + ot_total + rec['bonus'] - rec['advance']
                    
                    tracker_table.append({
                        "ID": eid, "Name": name, "Designation": desg, "Base Salary/Rate": f"Tk {base_sal:,.2f}",
                        "Present Days": rec['present'], 
                        "Absent Days": display_absent,
                        "Absent Cut": f"Tk {ab_cut:,.2f}", "Fine": f"Tk {rec['fine']:,.2f}",
                        "OT Earn": f"Tk {ot_total:,.2f}", "Bonus": f"Tk {rec['bonus']:,.2f}", "Advance Cut": f"Tk {rec['advance']:,.2f}",
                        "Net Payable": f"Tk {final_payable:,.2f}"
                    })
                if tracker_table:
                    st.markdown(f"##### {title_text}")
                    st.dataframe(pd.DataFrame(tracker_table), use_container_width=True)

            st.markdown("---")
            if st.button("🚀 Prepare & Download Full Excel Report", use_container_width=True):
                ex_buf = BytesIO()
                with pd.ExcelWriter(ex_buf, engine='openpyxl') as writer:
                    sheet_names = ["Managers", "Officers", "Workers_Permanent", "Workers_Daily"]
                    for cat_name, s_name in zip(categories_list, sheet_names):
                        cat_employees = [r for r in rows if r[3] == cat_name]
                        cat_table = []
                        for r in cat_employees:
                            rec = saved_db_tracker.get(r[0], {"present": days_in_month if r[3] == 'Worker (Daily Basis)' else 26, "absent": 0, "fine": 0.0, "ot_hrs": 0.0, "ot_rate": 0.0, "bonus": 0.0, "advance": 0.0})
                            calc_salary = r[5]
                            if r[3] != 'Worker (Daily Basis)' and rec['present'] < 26:
                                calc_salary = (r[5] / 26) * rec['present']

                            _, _, _, _, ab_cut, net_p, total_earn = calculate_salary_breakdown(calc_salary, rec['absent'], rec['fine'], r[3], rec['present'])
                            ot_total = rec['ot_hrs'] * rec['ot_rate']
                            final_payable = net_p + ot_total + rec['bonus'] - rec['advance']
                            display_absent = rec['absent']
                            
                            cat_table.append({
                                "Employee ID": r[0], "Name": r[1], "Department": r[4], "Category": r[3], "Designation": r[2],
                                "Base Salary/Rate": r[5], "Present Days": rec['present'], "Absent Days": display_absent,
                                "Absent Cut": round(ab_cut, 2), "Fine/Penalty": rec['fine'], "OT Earnings": round(ot_total, 2), 
                                "Bonus": rec['bonus'], "Advance Deduct": rec['advance'], "Net Payable (Tk)": round(final_payable, 2)
                            })
                        df_cat = pd.DataFrame(cat_table) if cat_table else pd.DataFrame()
                        df_cat.to_excel(writer, index=False, sheet_name=s_name)
                st.download_button(label="📥 Download Now", data=ex_buf.getvalue(), file_name=f"RECON_Advanced_Payroll_{select_m}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else: st.info("Database is empty. Please add people from the left panel.")
