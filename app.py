import streamlit as st
import sqlite3
from datetime import datetime
import calendar
import base64
from io import BytesIO
import pandas as pd
from calculations import calculate_salary_breakdown, generate_pdf_bytes

st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")

def init_db():
    conn = sqlite3.connect("payroll_v5.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees_final_version (
            emp_id TEXT PRIMARY KEY, name TEXT NOT NULL, designation TEXT NOT NULL,
            category TEXT NOT NULL, department TEXT NOT NULL, salary REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("payroll_v5.db", check_same_thread=False)

st.title("💼 RECON LABORATORIES LTD - Professional Payroll System")
st.markdown("---")

col1, col2 = st.columns([1, 2.3])

# --- LEFT SIDE: ADD EMPLOYEE ---
with col1:
    st.header("➕ Add New Person")
    
    if "form_id" not in st.session_state: st.session_state.form_id = ""
    if "form_name" not in st.session_state: st.session_state.form_name = ""
    if "form_desg" not in st.session_state: st.session_state.form_desg = ""
    if "form_salary" not in st.session_state: st.session_state.form_salary = ""

    with st.form("employee_form", clear_on_submit=False):
        input_id = st.text_input("ID (e.g., RECON-01)", value=st.session_state.form_id)
        name = st.text_input("Name", value=st.session_state.form_name)
        department = st.selectbox("Select Department", [
            "Production", "Quality Control", "Development",
            "Maintenance", "Accounts & Finance", "HR & Admin", "Store & Inventory", "Sales & Marketing"
        ])
        category = st.selectbox("Select Category", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
        designation = st.text_input("Designation", value=st.session_state.form_desg)
        salary = st.text_input("Gross Salary / Daily Wage Rate (Tk)", value=st.session_state.form_salary)
        
        if st.form_submit_button("Add to Database", use_container_width=True, type="primary"):
            if not (input_id and name and designation and salary):
                st.error("Please fill all fields!")
            else:
                try:
                    conn = get_db_connection()
                    conn.cursor().execute("INSERT INTO employees_final_version VALUES (?, ?, ?, ?, ?, ?)",
                                   (input_id, name, designation, category, department, float(salary)))
                    conn.commit()
                    conn.close()
                    st.success(f"{name} successfully added!")
                    st.session_state.form_id = ""
                    st.session_state.form_name = ""
                    st.session_state.form_desg = ""
                    st.session_state.form_salary = ""
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.session_state.form_id = input_id
                    st.session_state.form_name = name
                    st.session_state.form_desg = designation
                    st.session_state.form_salary = salary
                    st.error(f"⚠️ Warning: Employee ID '{input_id}' already exists! Please change the ID. Your typed data is safe.")
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
                st.markdown(f"##### 📝 Editing: {ename} ({eid})")
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
                        try:
                            conn = get_db_connection()
                            conn.cursor().execute("UPDATE employees_final_version SET name=?, designation=?, category=?, department=?, salary=? WHERE emp_id=?", (ch_name, ch_desg, ch_cat, ch_dept, float(ch_salary), eid))
                            conn.commit()
                            conn.close()
                            st.session_state[f"emode_{prefix}_{eid}"] = False
                            st.success("Updated successfully!")
                            st.rerun()
                        except ValueError: st.error("Salary must be a number!")
                with b2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state[f"emode_{prefix}_{eid}"] = False
                        st.rerun()

        if st.session_state.get(f"dmode_{prefix}_{eid}", False):
            st.warning(f"Are you sure you want to completely remove **{ename} ({eid})**?")
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("Yes, Confirm Delete", key=f"c_del_{prefix}_{eid}", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    conn.cursor().execute("DELETE FROM employees_final_version WHERE emp_id = ?", (eid,))
                    conn.commit()
                    conn.close()
                    st.session_state[f"dmode_{prefix}_{eid}"] = False
                    st.success("Employee removed successfully!")
                    st.rerun()
            with dc2:
                if st.button("Cancel Delete", key=f"c_can_{prefix}_{eid}", use_container_width=True):
                    st.session_state[f"dmode_{prefix}_{eid}"] = False
                    st.rerun()
        st.markdown("<hr style='margin:4px 0px; border-color:#eee;'>", unsafe_allow_html=True)


# --- RIGHT SIDE: ALL MANAGEMENT, SEARCH & PAYROLL ---
with col2:
    st.header("📋 Payroll Calculation & Reports")
    conn = get_db_connection()
    rows = conn.cursor().execute("SELECT * FROM employees_final_version").fetchall()
    conn.close()
    
    if rows:
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        select_m = st.selectbox("Select Month", months_list, index=int(datetime.now().strftime("%m")) - 1)
        select_y = st.selectbox("Select Year", [str(y) for y in range(2024, 2031)], index=2)
        full_month = f"{select_m}, {select_y}"
        
        # 🆕 এখানে পাইথন অটোমেটিক সিলেক্ট করা মাসের দিন সংখ্যা (২৮/২৯/৩০/৩১) বের করে নেবে
        month_num = months_list.index(select_m) + 1
        days_in_month = calendar.monthrange(int(select_y), month_num)[1]
        
        tab_emp, tab0, tab1, tab2 = st.tabs(["👥 All Employees", "🔍 Search Employee", "📄 Individual Pay Slip", "📊 Categorized Salary Sheet"])
        
        # TAB 1: ALL EMPLOYEES
        with tab_emp:
            st.markdown("### 👥 Manage Employees (By Category)")
            categories_map = {
                "💼 Managers": "Manager",
                "👔 Officers": "Officer",
                "🛠️ Workers (Permanent)": "Worker (Permanent)",
                "📆 Workers (Daily Basis)": "Worker (Daily Basis)"
            }
            for title, cat_value in categories_map.items():
                cat_members = [r for r in rows if r[3] == cat_value]
                with st.expander(f"{title} ({len(cat_members)})", expanded=True):
                    if not cat_members: st.info(f"No employees registered under {cat_value}.")
                    else:
                        for r in cat_members: render_inline_management(r, prefix="all_tab")

        # TAB 2: SEARCH FEATURE
        with tab0:
            st.markdown("### 🔍 Live Search & Quick Action")
            search_query = st.text_input("Enter Employee ID or Name to search", placeholder="Type here...", key="search_tab_input")
            if search_query:
                search_results = [r for r in rows if search_query.lower() in r[0].lower() or search_query.lower() in r[1].lower()]
                if search_results:
                    st.success(f"Found {len(search_results)} result(s):")
                    for emp in search_results:
                        st.markdown(f"**Current Category:** *{emp[3]}*")
                        render_inline_management(emp, prefix="search_tab")
                else: st.error("No employee found with that ID or Name.")
            else: st.info("Type an ID or Name above to instantly check details, edit or remove.")

        # TAB 3: INDIVIDUAL PAY SLIP
        with tab1:
            st.markdown("### 🔍 Search Employee for Pay Slip")
            pay_search = st.text_input("Enter Employee ID or Name to generate pay slip", placeholder="e.g., RECON-01 or Satter", key="pay_slip_search_input")
            
            if pay_search:
                pay_results = [r for r in rows if pay_search.lower() in r[0].lower() or pay_search.lower() in r[1].lower()]
                
                if pay_results:
                    if len(pay_results) > 1:
                        st.info(f"Multiple matches found ({len(pay_results)}). Please select the correct person below:")
                        emp_options = {f"[{r[3]}] {r[0]} - {r[1]} ({r[2]})": r for r in pay_results}
                        selected_emp = emp_options[st.selectbox("Select Person", list(emp_options.keys()), key="pay_slip_multiple_select")]
                    else:
                        selected_emp = pay_results[0]
                        st.success(f"Selected: **{selected_emp[1]} ({selected_emp[0]})** — *{selected_emp[3]}*")
                    
                    with st.form("calculation_form_search"):
                        st.markdown(f"##### Calculate Pay Slip for **{selected_emp[1]}** ({full_month}) — Total Days: {days_in_month}")
                        c1, c2 = st.columns(2)
                        with c1:
                            if selected_emp[3] == 'Worker (Daily Basis)':
                                # 🆕 মাসের মোট দিন (days_in_month) অনুযায়ী ডিফল্ট এবং ম্যাক্সিমাম লিমিট সেট হবে
                                p_days = st.number_input("Total Present Days", 0, days_in_month, days_in_month, key="ind_p_search")
                                a_days = 0
                            else:
                                a_days = st.number_input("Absent Days", 0, days_in_month, 0, key="ind_a_search")
                                p_days = 0
                        with c2: 
                            f_amt = st.number_input("Fine / Penalty (Tk)", 0.0, value=0.0, step=10.0, key="ind_f_search")
                        
                        if st.form_submit_button("🔄 Calculate Slip", use_container_width=True):
                            st.session_state['s_abs'], st.session_state['s_pres'], st.session_state['s_fine'] = a_days, p_days, f_amt

                    sa = st.session_state.get('s_abs', 0)
                    sp = st.session_state.get('s_pres', days_in_month if selected_emp[3] == 'Worker (Daily Basis)' else 0)
                    sf = st.session_state.get('s_fine', 0.0)
                    
                    _, _, _, _, _, net_payable, _ = calculate_salary_breakdown(selected_emp[5], sa, sf, selected_emp[3], sp)
                    
                    st.markdown(f"#### **Net Payable Amount:** Tk {net_payable:,.2f}")
                    
                    pdf_buf = BytesIO()
                    generate_pdf_bytes(selected_emp, full_month, sa, sf, sp, pdf_buf)
                    pdf_bytes = pdf_buf.getvalue()
                    st.download_button(
                        "📥 Download Pay Slip (PDF)", 
                        data=pdf_bytes, 
                        file_name=f"PaySlip_{selected_emp[0]}_{select_m}.pdf", 
                        mime="application/pdf", 
                        use_container_width=True,
                        type="primary"
                    )
                else: st.error("No employee found matching your input.")
            else: st.info("Type an Employee ID or Name above to quickly load their details and download the PDF pay slip.")

        # TAB 4: SEPARATED & CATEGORIZED SALARY SHEET
        with tab2:
            st.markdown(f"### 📋 Salary Sheet Generator for {full_month} (Total Days: {days_in_month})")
            view_cat = st.selectbox("Select Category to Input Attendance", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
            filtered_rows = [r for r in rows if r[3] == view_cat]
            
            sheet_data = []
            with st.form("bulk_sheet_form"):
                st.markdown(f"##### Input Attendance Data for: **{view_cat}**")
                if not filtered_rows: st.warning(f"No employees found in '{view_cat}' category.")
                else:
                    for r in filtered_rows:
                        st.markdown(f"**🔹 [{r[4]}] {r[0]} - {r[1]}** ({r[2]})")
                        col_in1, col_in2 = st.columns(2)
                        with col_in1:
                            if r[3] == 'Worker (Daily Basis)':
                                # 🆕 এখানেও ফর্ম ইনপুটে মাসের দিন অনুযায়ী অটো সেট হবে (২৮/২৯/৩০/৩১)
                                p_d = st.number_input(f"Present Days", 0, days_in_month, days_in_month, key=f"p_{r[0]}")
                                a_d = 0
                            else:
                                a_d = st.number_input(f"Absent Days", 0, days_in_month, 0, key=f"a_{r[0]}")
                                p_d = 0
                        with col_in2: f_d = st.number_input(f"Penalty/Fine (Tk)", 0.0, value=0.0, key=f"f_{r[0]}")
                        sheet_data.append({'emp_data': r, 'absent_days': a_d, 'present_days': p_d, 'fine_amount': f_d})
                
                submit_sheet = st.form_submit_button(f"📊 Process & Preview {view_cat} Sheet", use_container_width=True)
            
            if submit_sheet and sheet_data:
                if 'attendance_tracker' not in st.session_state: st.session_state['attendance_tracker'] = {}
                for item in sheet_data:
                    eid = item['emp_data'][0]
                    st.session_state['attendance_tracker'][eid] = {'absent': item['absent_days'], 'present': item['present_days'], 'fine': item['fine_amount']}
                st.success(f"Calculated and saved current inputs for {view_cat} successfully!")

            st.markdown("---")
            st.markdown("### 👁️ Current Month Attendance & Net Salary Overview (All Database)")
            
            tracker_table = []
            current_tracker = st.session_state.get('attendance_tracker', {})
            
            for r in rows:
                eid, name, desg, cat, dept, base_sal = r
                
                if eid in current_tracker:
                    saved_data = current_tracker[eid]
                else:
                    if cat == 'Worker (Daily Basis)':
                        # 🆕 ওভারভিউ লাইভ টেবিলে প্রথমবার দেখানোর সময় অটোমেটিক মাসের মোট দিন চলে আসবে
                        saved_data = {'absent': 0, 'present': days_in_month, 'fine': 0.0} 
                    else:
                        saved_data = {'absent': 0, 'present': 0, 'fine': 0.0}
                
                _, _, _, _, ab_cut, net_p, _ = calculate_salary_breakdown(
                    base_sal, saved_data['absent'], saved_data['fine'], cat, saved_data['present']
                )
                
                tracker_table.append({
                    "ID": eid, "Name": name, "Category": cat, "Base Salary/Rate": f"Tk {base_sal:,.2f}",
                    "Present Days": saved_data['present'] if cat == 'Worker (Daily Basis)' else f"N/A (Fixed {days_in_month} Days)",
                    "Absent Days": saved_data['absent'] if cat != 'Worker (Daily Basis)' else 0,
                    "Absent Cut (Tk)": f"Tk {ab_cut:,.2f}", "Fine/Penalty (Tk)": f"Tk {saved_data['fine']:,.2f}",
                    "Net Salary (Tk)": f"Tk {net_p:,.2f}"
                })
                
            if tracker_table: st.dataframe(pd.DataFrame(tracker_table), use_container_width=True)

            st.markdown("---")
            st.markdown("##### 📥 Download Full Combined Excel Sheet (Separated by Tabs)")
            if st.button("🚀 Prepare & Download Full Excel Report", use_container_width=True, type="primary"):
                ex_buf = BytesIO()
                with pd.ExcelWriter(ex_buf, engine='openpyxl') as writer:
                    categories_list = ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"]
                    sheet_names = ["Managers", "Officers", "Workers_Permanent", "Workers_Daily"]
                    
                    for cat_name, s_name in zip(categories_list, sheet_names):
                        cat_employees = [r for r in rows if r[3] == cat_name]
                        cat_table = []
                        for r in cat_employees:
                            if r[0] in st.session_state.get('attendance_tracker', {}):
                                saved_att = st.session_state['attendance_tracker'][r[0]]
                            else:
                                # 🆕 এক্সেল শিটের ডিফল্ট জেনারেটরেও কারেন্ট মাসের মোট দিন সংখ্যা এসাইন হবে
                                saved_att = {'absent': 0, 'present': days_in_month if r[3] == 'Worker (Daily Basis)' else 0, 'fine': 0.0}
                                
                            _, _, _, _, ab_cut, net_p, total_earn = calculate_salary_breakdown(r[5], saved_att['absent'], saved_att['fine'], r[3], saved_att['present'])
                            cat_table.append({
                                "Employee ID": r[0], "Name": r[1], "Department": r[4], "Category": r[3], "Designation": r[2],
                                "Base Salary/Rate": r[5], "Total Earnings": round(total_earn, 2), "Absent Cut": round(ab_cut, 2),
                                "Fine/Penalty": saved_att['fine'], "Net Payable (Tk)": round(net_p, 2)
                            })
                        df_cat = pd.DataFrame(cat_table) if cat_table else pd.DataFrame(columns=["Employee ID", "Name", "Department", "Category", "Designation", "Base Salary/Rate", "Total Earnings", "Absent Cut", "Fine/Penalty", "Net Payable (Tk)"])
                        df_cat.to_excel(writer, index=False, sheet_name=s_name)
                
                st.download_button(label="📥 Download Now", data=ex_buf.getvalue(), file_name=f"RECON_Payroll_Sheet_{select_m}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else: st.info("Database is empty. Please add people from the left panel.")
