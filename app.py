import streamlit as st
import sqlite3
import datetime

st.set_page_config(page_title="CRM Reporting Dashboard", layout="wide")

# ----------------- DATABASE SETUP -----------------
conn = sqlite3.connect('crm_reporting.db', check_same_thread=False)
c = conn.cursor()

# Create Tables
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, name TEXT, role TEXT, is_admin INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS reports 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, report_date TEXT, 
              shift TEXT, project TEXT, hours REAL, work_done TEXT, submitted_at TEXT)''')
conn.commit()

# Default Admin & Default Project
c.execute("INSERT OR IGNORE INTO users (id, email, name, role, is_admin) VALUES (1, 'boss@company.com', 'Admin Boss', 'Admin', 1)")
c.execute("INSERT OR IGNORE INTO projects (project_name) VALUES ('General / Internal Tasks')")
conn.commit()

# ----------------- LOGIN SYSTEM -----------------
st.sidebar.title("🔐 CRM Login")
user_email = st.sidebar.text_input("Enter your Email").strip().lower()

user = None
if user_email:
    c.execute("SELECT id, email, name, role, is_admin FROM users WHERE LOWER(email) = ?", (user_email,))
    user = c.fetchone()
    if not user:
        st.sidebar.error("Email not found. Contact Admin.")

if user:
    user_id, email, name, role, is_admin = user
    st.sidebar.success(f"Welcome, {name}!")
    
    # ==========================================
    #             ADMIN DASHBOARD
    # ==========================================
    if is_admin == 1:
        st.title("⚙️ Admin CRM Dashboard")
        tab1, tab2, tab3 = st.tabs(["📊 Daily Reports & History", "📁 Manage Projects", "👥 Manage Team"])
        
        # TAB 1: VIEW REPORTS
        with tab1:
            st.subheader("Employee Reports Hub")
            col1, col2 = st.columns([1, 3])
            
            with col1:
                view_date = st.date_input("Select Date to View", datetime.date.today())
                view_date_str = view_date.strftime('%Y-%m-%d')
                
            with col2:
                c.execute('''SELECT users.name, reports.project, reports.shift, reports.hours, reports.work_done 
                             FROM reports 
                             JOIN users ON reports.user_id = users.id 
                             WHERE reports.report_date = ?''', (view_date_str,))
                daily_reports = c.fetchall()
                
                if daily_reports:
                    # Convert to list of dictionaries for beautiful Streamlit dataframe rendering
                    report_data = [{"Employee": r[0], "Project": r[1], "Shift": r[2], "Hours": r[3], "Work Done": r[4]} for r in daily_reports]
                    st.dataframe(report_data, use_container_width=True)
                else:
                    st.info(f"No reports submitted yet for {view_date_str}.")

        # TAB 2: MANAGE PROJECTS
        with tab2:
            st.subheader("Add CRM Projects")
            with st.form("add_project"):
                new_project = st.text_input("Project Name")
                if st.form_submit_button("Add Project"):
                    if new_project:
                        try:
                            c.execute("INSERT INTO projects (project_name) VALUES (?)", (new_project.strip(),))
                            conn.commit()
                            st.success(f"Project '{new_project}' added!")
                        except:
                            st.error("Project already exists.")
                            
            st.divider()
            st.markdown("**Current Active Projects:**")
            c.execute("SELECT project_name FROM projects")
            projects = c.fetchall()
            for p in projects:
                st.caption(f"🔹 {p[0]}")

        # TAB 3: MANAGE TEAM
        with tab3:
            st.subheader("Register Employee")
            with st.form("add_emp"):
                ename = st.text_input("Name")
                eemail = st.text_input("Email").strip().lower()
                erole = st.text_input("Role")
                if st.form_submit_button("Create Account"):
                    if ename and eemail:
                        try:
                            c.execute("INSERT INTO users (email, name, role, is_admin) VALUES (?, ?, ?, 0)", (eemail, ename, erole))
                            conn.commit()
                            st.success(f"Added {ename} to the team!")
                        except:
                            st.error("Email already exists.")

    # ==========================================
    #           EMPLOYEE DASHBOARD
    # ==========================================
    else:
        st.title(f"👋 {name}'s Workspace")
        st.caption(f"Role: {role}")
        
        tab_submit, tab_history = st.tabs(["📝 Log Work", "📅 My Previous Reports"])
        
        # TAB 1: SUBMIT REPORT
        with tab_submit:
            # Allows selecting past dates if they forgot!
            selected_date = st.date_input("Report Date", datetime.date.today(), help="Change the date if you forgot to submit yesterday's report.")
            date_str = selected_date.strftime('%Y-%m-%d')
            
            c.execute("SELECT project, shift, hours, work_done FROM reports WHERE user_id = ? AND report_date = ?", (user_id, date_str))
            existing = c.fetchone()
            
            if existing:
                st.success(f"✅ You already submitted your report for {date_str}.")
                st.write(f"**Project:** {existing[0]} | **Shift:** {existing[1]} | **Hours:** {existing[2]}")
                st.text_area("Your Submission:", value=existing[3], disabled=True, height=100)
            else:
                with st.form("report_form"):
                    col1, col2, col3 = st.columns(3)
                    
                    # Fetch projects for dropdown
                    c.execute("SELECT project_name FROM projects")
                    proj_list = [p[0] for p in c.fetchall()]
                    
                    with col1:
                        proj_sel = st.selectbox("Select Project", proj_list)
                    with col2:
                        shift_sel = st.selectbox("Your Shift", [
                            "10:00 AM - 07:00 PM", 
                            "12:00 PM - 09:00 PM", 
                            "02:00 PM - 11:00 PM", 
                            "Other / Flexible"
                        ])
                    with col3:
                        hours_worked = st.number_input("Hours Worked", min_value=1.0, max_value=24.0, value=8.0, step=0.5)
                        
                    work_text = st.text_area("What did you accomplish?", height=150)
                    
                    if st.form_submit_button("Submit CRM Report"):
                        if len(work_text.strip()) >= 10:
                            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            c.execute('''INSERT INTO reports (user_id, report_date, shift, project, hours, work_done, submitted_at) 
                                         VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                                      (user_id, date_str, shift_sel, proj_sel, hours_worked, work_text.strip(), now))
                            conn.commit()
                            st.success("Report saved successfully!")
                            st.rerun()
                        else:
                            st.error("Please write at least 10 characters describing your work.")
                            
        # TAB 2: HISTORY (See previous days)
        with tab_history:
            st.subheader("Your Last 10 Submissions")
            c.execute('''SELECT report_date, project, shift, hours, work_done 
                         FROM reports WHERE user_id = ? ORDER BY report_date DESC LIMIT 10''', (user_id,))
            my_history = c.fetchall()
            
            if my_history:
                history_data = [{"Date": r[0], "Project": r[1], "Shift": r[2], "Hrs": r[3], "Task": r[4]} for r in my_history]
                st.dataframe(history_data, use_container_width=True)
            else:
                st.info("No past reports found.")

else:
    st.title("Company CRM Portal")
    st.info("👈 Please enter your email in the sidebar to access your dashboard.")
