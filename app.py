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

col1, col2 = st.columns([1.2, 2])

with col1:
    st.header("➕ Add New Person")
    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("ID (e.g., RECON-M01)")
        name = st.text_input("Name")
        department = st.selectbox("Select Department (বিভাগ)", [
            "Production (উৎপাদন)", "Quality Control (কিউসি)", "Development (ডেভেলপমেন্ট)",
            "Maintenance (মেইনটেইনেন্স)", "Accounts & Finance", "HR & Admin", "Store & Inventory", "Sales & Marketing"
        ])
        category = st.selectbox("Select Category", ["Manager", "Officer", "Worker (Permanent)", "Worker (Daily Basis)"])
        designation = st.text_input("Designation (পদবী)")
        salary = st.text_input("Gross Salary / Daily Wage Rate (Tk)")
        if st.form_submit_button("Add to Database"):
            if not (input_id and name and designation and salary):
                st.error("সব ঘর পূরণ করুন!")
            else:
                try:
                    conn = get_db_connection()
                    conn.cursor().execute("INSERT INTO employees_final_version VALUES (?, ?, ?, ?, ?, ?)",
                                   (input_id, name, designation, category, department, float(salary)))
                    conn.commit()
                    conn.close()
                    st.success(f"{name} সফলভাবে যুক্ত হয়েছেন!")
                    st.rerun()
                except sqlite3.IntegrityError: st.error("IDটি ইতিমধ্যে আছে!")
                except ValueError: st.error("টাকা সংখ্যায় দিন!")

    st.markdown("---")
    st.header("❌ Remove Person")
    conn = get_db_connection()
    del_rows = conn.cursor().execute("SELECT emp_id, name, department FROM employees_final_version").fetchall()
    conn.close()
    if del_rows:
        del_options = {f"[{r[2]}] {r[0]} - {r[1]}": r[0] for r in del_rows}
        selected_del = st.selectbox("Select Person to Remove", list(del_options.keys()))
        if st.button("Delete Person", type="primary", use_container_width=True):
            conn = get_db_connection()
            conn.cursor().execute("DELETE FROM employees_final_version WHERE emp_id = ?", (del_options[selected_del],))
            conn.commit()
            conn.close()
            st.success("মুছে ফেলা হয়েছে!")
            st.rerun()

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
        
        tab1, tab2 = st.tabs(["📄 Individual Pay Slip", "📊 Full Salary Sheet (সবার একসাথে)"])
        
        with tab1:
            emp_options = {f"[{r[4]}] {r[0]} - {r[1]}": r for r in rows}
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

        with tab2:
            st.markdown(f"### 📋 {full_month} এর স্যালারি শিট জেনারেটর")
            sheet_data = []
            with st.form("bulk_sheet_form"):
                for r in rows:
                    st.markdown(f"**🔹 [{r[4]}] {r[0]} - {r[1]}** ({r[2]})")
                    col_in1, col_in2 = st.columns(2)
                    with col_in1:
                        if r[3] == 'Worker (Daily Basis)':
                            p_d = st.number_input(f"Present Days", 0, 31, 26, key=f"p_{r[0]}")
                            a_d = 0
                        else:
                            a_d = st.number_input(f"Absent Days", 0, 26, 0, key=f"a_{r[0]}")
                            p_d = 0
                    with col_in2: f_d = st.number_input(f"Penalty/Fine (Tk)", 0.0, value=0.0, key=f"f_{r[0]}")
                    sheet_data.append({'emp_data': r, 'absent_days': a_d, 'present_days': p_d, 'fine_amount': f_d})
                submit_sheet = st.form_submit_button("📊 Generate Salary Sheet", use_container_width=True)
            
            if submit_sheet:
                final_table = []
                for item in sheet_data:
                    eid, name, desg, cat, dept, s_rate = item['emp_data']
                    _, _, _, _, ab_cut, net_p, total_earn = calculate_salary_breakdown(s_rate, item['absent_days'], item['fine_amount'], cat, item['present_days'])
                    final_table.append({
                        "Employee ID": eid, "Name": name, "Department": dept, "Category": cat, "Designation": desg,
                        "Base Salary/Rate": s_rate, "Total Earnings": round(total_earn, 2), "Absent Cut": round(ab_cut, 2),
                        "Fine/Penalty": round(item['fine_amount'], 2), "Net Payable (টাকা)": round(net_p, 2)
                    })
                df = pd.DataFrame(final_table)
                st.dataframe(df, use_container_width=True)
                ex_buf = BytesIO()
                with pd.ExcelWriter(ex_buf, engine='openpyxl') as writer: df.to_excel(writer, index=False, sheet_name="SalarySheet")
                st.download_button(label="📥 Download Full Salary Sheet (Excel)", data=ex_buf.getvalue(), file_name=f"RECON_Payroll_Sheet_{select_m}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary")
    else: st.info("ডাটাবেজ খালি। লোক যুক্ত করুন।")
