import streamlit as st
import sqlite3
import datetime
import pandas as pd

# Initialize SQLite Database
conn = sqlite3.connect('reporting.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT, role TEXT, is_admin INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS reports 
             (id INTEGER PRIMARY KEY, user_id INTEGER, report_date TEXT, work_done TEXT)''')
conn.commit()

# Ensure default Admin account exists
c.execute("INSERT OR IGNORE INTO users (id, email, name, role, is_admin) VALUES (1, 'boss@company.com', 'Boss', 'Admin', 1)")
conn.commit()

st.set_page_config(page_title="Daily Reporting Platform", layout="wide")

# Sidebar Authentication
st.sidebar.title("🔐 Login Portal")
user_email = st.sidebar.text_input("Enter Email")
user = None

if user_email:
    c.execute("SELECT id, email, name, role, is_admin FROM users WHERE email = ?", (user_email,))
    user = c.fetchone()
    if not user:
        st.sidebar.error("Email not found. Contact Admin.")

if user:
    user_id, email, name, role, is_admin = user
    st.sidebar.success(f"Logged in as: {name} ({role})")
    
    # ------------------ ADMIN VIEW ------------------
    if is_admin:
        st.title("📊 Boss Admin Dashboard")
        
        tab1, tab2 = st.tabs(["7-Day Attendance Matrix", "Add New Employee"])
        
        with tab1:
            st.subheader("Daily Submissions Overview")
            # Fetch last 7 days reports
            df_users = pd.read_sql_query("SELECT id, name, role FROM users WHERE is_admin = 0", conn)
            df_reports = pd.read_sql_query("SELECT user_id, report_date, work_done FROM reports", conn)
            
            dates = [(datetime.date.today() - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
            
            matrix_data = []
            for _, emp in df_users.iterrows():
                row = {'Employee': emp['name'], 'Role': emp['role']}
                for d in dates:
                    submitted = not df_reports[(df_reports['user_id'] == emp['id']) & (df_reports['report_date'] == d)].empty
                    row[d] = "✅ Done" if submitted else "❌ Missing"
                matrix_data.append(row)
                
            st.dataframe(pd.DataFrame(matrix_data), use_container_width=True)
            
            if st.button("🔔 Trigger Missing Report Alerts"):
                missing = [row['Employee'] for row in matrix_data if row[dates[-1]] == "❌ Missing"]
                st.warning(f"Reminders needed for today: {', '.join(missing)}")
                
        with tab2:
            st.subheader("Register Employee (Total: 20)")
            emp_name = st.text_input("Employee Name")
            emp_email = st.text_input("Employee Email")
            emp_role = st.text_input("Job Role")
            if st.button("Create Account"):
                try:
                    c.execute("INSERT INTO users (email, name, role, is_admin) VALUES (?, ?, ?, 0)", (emp_email, emp_name, emp_role))
                    conn.commit()
                    st.success(f"Added {emp_name} successfully!")
                except:
                    st.error("Email already exists.")

    # ------------------ EMPLOYEE VIEW ------------------
    else:
        st.title(f"📝 Daily Report Submission — {name}")
        st.info(f"Role: {role} | Date: {datetime.date.today()}")
        
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        c.execute("SELECT work_done FROM reports WHERE user_id = ? AND report_date = ?", (user_id, today_str))
        existing_report = c.fetchone()
        
        if existing_report:
            st.success("✅ You have already submitted your daily report for today!")
            st.text_area("Submitted Work:", value=existing_report[0], disabled=True)
        else:
            work_text = st.text_area("What did you accomplish today? (Supports browser voice dictation)", height=150)
            if st.button("Submit Daily Report"):
                if len(work_text.strip()) < 10:
                    st.error("Report must be at least 10 characters long.")
                else:
                    c.execute("INSERT INTO reports (user_id, report_date, work_done) VALUES (?, ?, ?)", (user_id, today_str, work_text))
                    conn.commit()
                    st.experimental_rerun()
else:
    st.title("Daily Reporting System")
    st.info("Please enter your email in the sidebar to log in.")
