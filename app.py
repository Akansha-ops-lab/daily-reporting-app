import streamlit as st
import sqlite3
import datetime
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Daily Reporting Platform", layout="wide")

# Database Connection Helper
def get_db():
    conn = sqlite3.connect('reporting.db', check_same_thread=False)
    return conn

conn = get_db()
c = conn.cursor()

# Init Database Tables
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, name TEXT, role TEXT, is_admin INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS reports 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, report_date TEXT, work_done TEXT)''')
conn.commit()

# Ensure Default Boss Account Exists
c.execute("INSERT OR IGNORE INTO users (id, email, name, role, is_admin) VALUES (1, 'boss@company.com', 'Boss', 'Admin', 1)")
conn.commit()

# Sidebar Authentication
st.sidebar.title("🔐 Login Portal")
user_email = st.sidebar.text_input("Enter Email").strip().lower()

user = None
if user_email:
    c.execute("SELECT id, email, name, role, is_admin FROM users WHERE LOWER(email) = ?", (user_email,))
    user = c.fetchone()
    if not user:
        st.sidebar.error("Email not found. Contact Admin.")

if user:
    user_id, email, name, role, is_admin = user
    st.sidebar.success(f"Logged in: {name} ({role})")
    
    # ------------------ ADMIN VIEW ------------------
    if is_admin == 1:
        st.title("📊 Boss Admin Dashboard")
        
        tab1, tab2 = st.tabs(["7-Day Attendance Matrix", "Add New Employee"])
        
        with tab1:
            st.subheader("Daily Submissions Overview")
            df_users = pd.read_sql_query("SELECT id, name, role FROM users WHERE is_admin = 0", conn)
            df_reports = pd.read_sql_query("SELECT user_id, report_date, work_done FROM reports", conn)
            
            dates = [(datetime.date.today() - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
            
            if df_users.empty:
                st.info("No employees registered yet. Go to 'Add New Employee' tab to add your team.")
            else:
                matrix_data = []
                for _, emp in df_users.iterrows():
                    row = {'Employee': emp['name'], 'Role': emp['role']}
                    for d in dates:
                        submitted = not df_reports[(df_reports['user_id'] == emp['id']) & (df_reports['report_date'] == d)].empty
                        row[d] = "✅ Done" if submitted else "❌ Missing"
                    matrix_data.append(row)
                    
                st.dataframe(pd.DataFrame(matrix_data), use_container_width=True)
                
                if st.button("🔔 Check Missing Reports Today"):
                    today_str = datetime.date.today().strftime('%Y-%m-%d')
                    missing = [row['Employee'] for row in matrix_data if row[today_str] == "❌ Missing"]
                    if missing:
                        st.warning(f"Missing reports today from: {', '.join(missing)}")
                    else:
                        st.success("Everyone has submitted their report today!")
                
        with tab2:
            st.subheader("Register Employee")
            with st.form("add_emp_form"):
                emp_name = st.text_input("Employee Name")
                emp_email = st.text_input("Employee Email").strip().lower()
                emp_role = st.text_input("Job Role")
                submitted = st.form_submit_button("Create Account")
                
                if submitted:
                    if emp_name and emp_email:
                        try:
                            c.execute("INSERT INTO users (email, name, role, is_admin) VALUES (?, ?, ?, 0)", (emp_email, emp_name, emp_role))
                            conn.commit()
                            st.success(f"Added {emp_name} successfully!")
                        except Exception as e:
                            st.error("Email already exists or invalid entry.")
                    else:
                        st.error("Please fill in Name and Email.")

    # ------------------ EMPLOYEE VIEW ------------------
    else:
        st.title(f"📝 Daily Report Submission — {name}")
        st.info(f"Role: {role} | Date: {datetime.date.today()}")
        
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        c.execute("SELECT work_done FROM reports WHERE user_id = ? AND report_date = ?", (user_id, today_str))
        existing_report = c.fetchone()
        
        if existing_report:
            st.success("✅ You have already submitted your daily report for today!")
            st.text_area("Submitted Work:", value=existing_report[0], disabled=True, height=150)
        else:
            with st.form("report_form"):
                work_text = st.text_area("What did you accomplish today?", height=150, help="You can use your browser or device voice dictation microphone button to type automatically.")
                submit_btn = st.form_submit_button("Submit Daily Report")
                
                if submit_btn:
                    if len(work_text.strip()) < 10:
                        st.error("Report must be at least 10 characters long.")
                    else:
                        c.execute("INSERT INTO reports (user_id, report_date, work_done) VALUES (?, ?, ?)", (user_id, today_str, work_text.strip()))
                        conn.commit()
                        st.success("Submitted successfully!")
                        st.rerun()

else:
    st.title("Company Daily Reporting System")
    st.info("👈 Please enter your email in the left sidebar to log in.")
