import streamlit as st
from supabase import create_client
from datetime import datetime
import calendar
from io import BytesIO
import pandas as pd
import base64
from calculations import calculate_salary_breakdown, generate_pdf_bytes

# --- SUPABASE CONFIGURATION ---
# আপনার প্রজেক্ট থেকে পাওয়া লিংক এবং কি (Key) এখানে দিন
SUPABASE_URL = "https://supabase.com/dashboard/project/qoelqzaodnxjfsmsyvhc/auth/policies?search=employees_final_version&schema=public"
SUPABASE_KEY = "sb_publishable_polNmuBnDGzfd91wFvCozw_eUJUtGrx"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ডাটা লোড করার ফাংশন ---
def get_data(table_name):
    response = supabase.table(table_name).select("*").execute()
    return response.data

st.set_page_config(page_title="RECON Payroll System", layout="wide", page_icon="💼")
st.title("💼 RECON LABORATORIES LTD")

# বাম পাশে ডাটা যোগ করার ফর্ম
with st.sidebar:
    st.header("➕ নতুন এমপ্লয়ি যোগ করুন")
    with st.form("employee_form", clear_on_submit=True):
        input_id = st.text_input("ID (সংখ্যা)")
        name = st.text_input("নাম")
        dept = st.selectbox("বিভাগ", ["Production", "Quality Control", "Development", "Accounts & Finance"])
        cat = st.selectbox("ক্যাটাগরি", ["Manager", "Officer", "Worker (Permanent)"])
        desg = st.text_input("পদবি")
        salary = st.number_input("বেতন", min_value=0.0)
        
        if st.form_submit_button("সেভ করুন"):
            data = {"emp_id": input_id, "name": name, "department": dept, "category": cat, "designation": desg, "salary": salary}
            supabase.table("employees_final_version").insert(data).execute()
            st.success("সফলভাবে সেভ হয়েছে!")
            st.rerun()

# মূল ডাটা টেবিল দেখানো
st.subheader("এমপ্লয়ি লিস্ট")
employees = get_data("employees_final_version")
if employees:
    st.dataframe(pd.DataFrame(employees))
else:
    st.info("ডাটাবেজে কোনো এমপ্লয়ি নেই।")
