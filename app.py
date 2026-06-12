import streamlit as st
import sqlite3
from datetime import datetime
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

col1, col2 = st.columns([1.3, 2])

# --- LEFT SIDE: EMPLOYEE MANAGEMENT ---
with col1:
    # 1. ADD EMPLOYEE
    st.header("➕ Add New Person")
    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("ID (e.g., RECON-01)")
        name = st.text_input("Name")
        department = st.selectbox("Select Department", [
            "Production", "Quality Control", "Development",
            "Maintenance", "Accounts & Finance", "HR & Admin", "Store & Inventory", "Sales & Marketing"
        ])
        category = st.selectbox("Select Category", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
        designation = st.text_input("Designation")
        salary = st.text_input("Gross Salary / Daily Wage Rate (Tk)")
        
        if st.form_submit_button("Add to Database"):
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
                    st.rerun()
                except sqlite3.IntegrityError: st.error("This ID already exists!")
                except ValueError: st.error("Salary must be a number!")

    st.markdown("---")
    
    # 2. EDIT EMPLOYEE
    st.header("📝 Edit Employee Info")
    conn = get_db_connection()
    all_rows = conn.cursor().execute("SELECT * FROM employees_final_version").fetchall()
    conn.close()
    
    if all_rows:
        edit_options = {f"[{r[3]}] {r[0]} - {r[1]}": r for r in all_rows}
        selected_edit_key = st.selectbox("Select Person to Edit", list(edit_options.keys()))
        emp_to_edit = edit_options[selected_edit_key]
        
        with st.form("edit_employee_form"):
            edit_name = st.text_input("Edit Name", value=emp_to_edit[1])
            dept_list = ["Production", "Quality Control", "Development", "Maintenance", "Accounts & Finance", "HR & Admin", "Store & Inventory", "Sales & Marketing"]
            edit_dept = st.selectbox("Edit Department", dept_list, index=dept_list.index(emp_to_edit[4]) if emp_to_edit[4] in dept_list else 0)
            cat_list = ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"]
            edit_cat = st.selectbox("Edit Category", cat_list, index=cat_list.index(emp_to_edit[3]) if emp_to_edit[3] in cat_list else 0)
            edit_desg = st.text_input("Edit Designation", value=emp_to_edit[2])
            edit_salary = st.text_input("Edit Gross Salary / Daily Rate", value=str(emp_to_edit[5]))
            
            if st.form_submit_button("Update Employee Info", use_container_width=True):
                try:
                    conn = get_db_connection()
                    conn.cursor().execute("""
                        UPDATE employees_final_version 
                        SET name=?, designation=?, category=?, department=?, salary=? 
                        WHERE emp_id=?
                    """, (edit_name, edit_desg, edit_cat, edit_dept, float(edit_salary), emp_to_edit[0]))
                    conn.commit()
                    conn.close()
                    st.success("Employee information updated successfully!")
                    st.rerun()
                except ValueError: st.error("Salary must be a number!")
    else: st.info("No employee available to edit.")

    st.markdown("---")
    
    # 3. REMOVE EMPLOYEE
    st.header("❌ Remove Person")
    if all_rows:
        del_options = {f"[{r[3]}] {r[0]} - {r[1]}": r[0] for r in all_rows}
        selected_del = st.selectbox("Select Person to Remove", list(del_options.keys()))
        if st.button("Delete Person", type="primary", use_container_width=True):
            conn = get_db_connection()
            conn.cursor().execute("DELETE FROM employees_final_version WHERE emp_id = ?", (del_options[selected_del],))
            conn.commit()
            conn.close()
            st.success("Successfully deleted from database!")
            st.rerun()

# --- RIGHT SIDE: CALCULATIONS & REPORTING ---
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
        
        tab1, tab2 = st.tabs(["📄 Individual Pay Slip", "📊 Categorized Salary Sheet"])
        
        # TAB 1: INDIVIDUAL PAY SLIP
        with tab1:
            emp_options = {f"[{r[3]}] {r[0]} - {r[1]}": r for r in rows}
            selected_emp = emp_options[st.selectbox("Select Person for Pay Slip", list(emp_options.keys()))]
            
            with st.form("calculation_form"):
                c1, c2 = st.columns(2)
                with c1:
                    if selected_emp[3] == 'Worker (Daily Basis)':
                        p_days = st.number_input("Total Present Days", 0, 31, 26, key="ind_p")
                        a_days = 0
                    else:
                        a_days = st.number_input("Absent Days", 0, 26, 0, key="ind_a")
                        p_days = 0
                with c2: f_amt = st.number_input("Fine / Penalty (Tk)", 0.0, value=0.0, step=10.0, key="ind_f")
                if st.form_submit_button("🔄 Calculate Slip"):
                    st.session_state['f_abs'], st.session_state['f_pres'], st.session_state['f_fine'] = a_days, p_days, f_amt

            fa, fp, ff = st.session_state.get('f_abs', 0), st.session_state.get('f_pres', 26 if selected_emp[3] == 'Worker (Daily Basis)' else 0), st.session_state.get('f_fine', 0.0)
            _, _, _, _, _, net_payable, _ = calculate_salary_breakdown(selected_emp[5], fa, ff, selected_emp[3], fp)
            
            st.write(f"**Net Payable:** Tk {net_payable:,.2f}")
            pdf_buf = BytesIO()
            generate_pdf_bytes(selected_emp, full_month, fa, ff, fp, pdf_buf)
            pdf_bytes = pdf_buf.getvalue()
            st.download_button("📥 Download Pay Slip (PDF)", data=pdf_bytes, file_name=f"PaySlip_{selected_emp[0]}.pdf", mime="application/pdf", use_container_width=True)

        # TAB 2: SEPARATED & CATEGORIZED SALARY SHEET
        with tab2:
            st.markdown(f"### 📋 Salary Sheet Generator for {full_month}")
            
            # ক্যাটাগরি ফিল্টার করার জন্য ড্রপডাউন (সিলেকশন আলাদা করার জন্য)
            view_cat = st.selectbox("Select Category to Input Attendance", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
            
            # শুধুমাত্র সিলেক্টেড ক্যাটাগরির লোকদের আলাদা করা
            filtered_rows = [r for r in rows if r[3] == view_cat]
            
            sheet_data = []
            with st.form("bulk_sheet_form"):
                st.markdown(f"##### Showing Employees for: **{view_cat}**")
                if not filtered_rows:
                    st.warning(f"No employees found in '{view_cat}' category.")
                else:
                    for r in filtered_rows:
                        st.markdown(f"**🔹 [{r[4]}] {r[0]} - {r[1]}** ({r[2]})")
                        col_in1, col_in2 = st.columns(2)
                        with col_in1:
                            if r[3] == 'Worker (Daily Basis)':
                                p_d = st.number_input(f"Present Days", 0, 31, 26, key=f"p_{r[0]}")
                                a_d = 0
                            else:
                                a_d = st.number_input(f"Absent Days", 0, 26, 0, key=f"a_{r[0]}")
                                p_d = 0
                        with col_in2: 
                            f_d = st.number_input(f"Penalty/Fine (Tk)", 0.0, value=0.0, key=f"f_{r[0]}")
                        
                        sheet_data.append({'emp_data': r, 'absent_days': a_d, 'present_days': p_d, 'fine_amount': f_d})
                
                submit_sheet = st.form_submit_button(f"📊 Process & View {view_cat} Sheet", use_container_width=True)
            
            # প্রসেস করার পর স্ক্রিনে আলাদা টেবিল দেখানো
            if submit_sheet and sheet_data:
                final_table = []
                for item in sheet_data:
                    eid, name, desg, cat, dept, s_rate = item['emp_data']
                    _, _, _, _, ab_cut, net_p, total_earn = calculate_salary_breakdown(s_rate, item['absent_days'], item['fine_amount'], cat, item['present_days'])
                    final_table.append({
                        "Employee ID": eid, "Name": name, "Department": dept, "Category": cat, "Designation": desg,
                        "Base Salary/Rate": s_rate, "Total Earnings": round(total_earn, 2), "Absent Cut": round(ab_cut, 2),
                        "Fine/Penalty": round(item['fine_amount'], 2), "Net Payable (Tk)": round(net_p, 2)
                    })
                df = pd.DataFrame(final_table)
                st.dataframe(df, use_container_width=True)
            
            # 📥 এক্সেল জেনারেটর (এক্সেলে ৪টি আলাদা শিট তৈরি হবে অটোমেটিক)
            st.markdown("---")
            st.markdown("##### 📥 Download Full Combined Excel Sheet (Separated by Tabs)")
            st.info("Click the button below to download the complete monthly report. Managers, Officers, and Workers will be saved in separate tabs inside the same Excel file.")
            
            if st.button("🚀 Prepare & Download Full Excel Report", use_container_width=True, type="primary"):
                ex_buf = BytesIO()
                with pd.ExcelWriter(ex_buf, engine='openpyxl') as writer:
                    # ৪টি ক্যাটাগরির জন্য আলাদা লুপ চালিয়ে আলাদা শিট তৈরি
                    categories_list = ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"]
                    sheet_names = ["Managers", "Officers", "Workers_Permanent", "Workers_Daily"]
                    
                    for cat_name, s_name in zip(categories_list, sheet_names):
                        cat_employees = [r for r in rows if r[3] == cat_name]
                        cat_table = []
                        for r in cat_employees:
                            # এখানে ডিফল্ট হাজিরার ভিত্তিতে এক্সেলের ফুল ডাটা রেডি হবে
                            fa_d = 0
                            fp_d = 26 if r[3] == 'Worker (Daily Basis)' else 0
                            _, _, _, _, ab_cut, net_p, total_earn = calculate_salary_breakdown(r[5], fa_d, 0.0, r[3], fp_d)
                            cat_table.append({
                                "Employee ID": r[0], "Name": r[1], "Department": r[4], "Category": r[3], "Designation": r[2],
                                "Base Salary/Rate": r[5], "Total Earnings": round(total_earn, 2), "Absent Cut": round(ab_cut, 2),
                                "Fine/Penalty": 0.0, "Net Payable (Tk)": round(net_p, 2)
                            })
                        
                        if cat_table:
                            df_cat = pd.DataFrame(cat_table)
                        else:
                            df_cat = pd.DataFrame(columns=["Employee ID", "Name", "Department", "Category", "Designation", "Base Salary/Rate", "Total Earnings", "Absent Cut", "Fine/Penalty", "Net Payable (Tk)"])
                        
                        df_cat.to_excel(writer, index=False, sheet_name=s_name)
                
                st.download_button(
                    label="📥 Download Now", 
                    data=ex_buf.getvalue(), 
                    file_name=f"RECON_All_Categories_Sheet_{select_m}.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    else: st.info("Database is empty. Please add people from the left panel.")
