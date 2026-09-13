import streamlit as st
import sqlite3
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Enterprise Workspace", page_icon="🏢", layout="wide")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('zoho_erp.db', check_same_thread=False)
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, name TEXT, role TEXT, is_admin INTEGER)''')
    # Projects Table (Advanced)
    c.execute('''CREATE TABLE IF NOT EXISTS projects 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, status TEXT, created_at TEXT)''')
    # Timesheet/Reports Table
    c.execute('''CREATE TABLE IF NOT EXISTS timesheets 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, 
                  shift TEXT, project TEXT, hours REAL, description TEXT, logged_at TEXT)''')
    conn.commit()
    
    # Defaults
    c.execute("INSERT OR IGNORE INTO users (email, name, role, is_admin) VALUES ('boss@company.com', 'System Admin', 'CEO', 1)")
    c.execute("INSERT OR IGNORE INTO projects (name, status, created_at) VALUES ('Internal Administration', 'Active', ?)", (datetime.date.today().strftime('%Y-%m-%d'),))
    conn.commit()
    return conn, c

conn, c = init_db()

# --- AUTHENTICATION ---
if 'user' not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🏢 Enterprise Workspace Login")
    st.markdown("### Sign in to access your dashboard")
    
    with st.form("login_form"):
        email_input = st.text_input("Work Email Address").strip().lower()
        submitted = st.form_submit_button("Secure Login")
        
        if submitted:
            c.execute("SELECT id, email, name, role, is_admin FROM users WHERE LOWER(email) = ?", (email_input,))
            user_data = c.fetchone()
            if user_data:
                st.session_state.user = {
                    'id': user_data[0], 'email': user_data[1], 
                    'name': user_data[2], 'role': user_data[3], 'is_admin': user_data[4]
                }
                st.rerun()
            else:
                st.error("Authentication failed. Contact your administrator.")
    st.stop() # Stop rendering the rest of the app until logged in

# --- LOGGED IN VARIABLES ---
user = st.session_state.user
today_str = datetime.date.today().strftime('%Y-%m-%d')

# --- ZOHO-STYLE SIDEBAR MENU ---
with st.sidebar:
    st.title(f"🏢 Workspace")
    st.info(f"👤 **{user['name']}**\n\n💼 {user['role']}")
    
    if user['is_admin']:
        st.subheader("Admin Modules")
        menu = st.radio("Navigation", ["📊 Command Center", "📋 Timesheets & Reports", "📁 Project Portfolio", "👥 Team Directory"])
    else:
        st.subheader("My Apps")
        menu = st.radio("Navigation", ["🏠 My Desk", "⏱️ Log Time", "📅 My Timesheets"])
        
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# ==========================================
#             ADMINISTRATOR APP
# ==========================================
if user['is_admin']:
    
    if menu == "📊 Command Center":
        st.title("Command Center")
        st.markdown("Overview of today's operations.")
        
        # Calculate KPIs
        c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
        total_emps = c.fetchone()[0]
        
        c.execute("SELECT COUNT(DISTINCT user_id) FROM timesheets WHERE date = ?", (today_str,))
        active_today = c.fetchone()[0]
        
        c.execute("SELECT SUM(hours) FROM timesheets WHERE date = ?", (today_str,))
        total_hours = c.fetchone()[0] or 0.0

        # Draw Zoho-style KPI Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Employees", total_emps)
        col2.metric("Checked In Today", f"{active_today} / {total_emps}")
        col3.metric("Missing Reports", total_emps - active_today)
        col4.metric("Total Hours Logged Today", f"{total_hours} hrs")
        
        st.divider()
        st.subheader("Recent Activity Stream")
        c.execute('''SELECT users.name, timesheets.project, timesheets.hours, timesheets.logged_at 
                     FROM timesheets JOIN users ON timesheets.user_id = users.id 
                     ORDER BY timesheets.logged_at DESC LIMIT 5''')
        recent = c.fetchall()
        for r in recent:
            st.info(f"**{r[0]}** logged **{r[2]} hrs** on project **{r[1]}** at {r[3]}")

    elif menu == "📋 Timesheets & Reports":
        st.title("Enterprise Timesheets")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            filter_date = st.date_input("Filter by Date", datetime.date.today())
            filter_date_str = filter_date.strftime('%Y-%m-%d')
            
        with col2:
            c.execute('''SELECT users.name, timesheets.project, timesheets.shift, timesheets.hours, timesheets.description 
                         FROM timesheets JOIN users ON timesheets.user_id = users.id 
                         WHERE timesheets.date = ? ORDER BY timesheets.logged_at DESC''', (filter_date_str,))
            records = c.fetchall()
            
            if records:
                data = [{"Employee": r[0], "Project": r[1], "Shift": r[2], "Hours": r[3], "Task": r[4]} for r in records]
                st.dataframe(data, use_container_width=True)
            else:
                st.warning(f"No timesheets found for {filter_date_str}.")

    elif menu == "📁 Project Portfolio":
        st.title("Project Management")
        
        with st.expander("➕ Create New Project", expanded=True):
            with st.form("new_proj"):
                p_name = st.text_input("Project / Client Name")
                p_status = st.selectbox("Status", ["Active", "On Hold", "Completed"])
                if st.form_submit_button("Launch Project"):
                    if p_name:
                        try:
                            c.execute("INSERT INTO projects (name, status, created_at) VALUES (?, ?, ?)", (p_name, p_status, today_str))
                            conn.commit()
                            st.success("Project created!")
                        except:
                            st.error("Project name already exists.")
                            
        st.subheader("Active Projects")
        c.execute("SELECT name, status, created_at FROM projects")
        projs = [{"Project": p[0], "Status": p[1], "Created": p[2]} for p in c.fetchall()]
        st.dataframe(projs, use_container_width=True)

    elif menu == "👥 Team Directory":
        st.title("Team Directory & Access Control")
        
        with st.expander("➕ Onboard New Employee", expanded=False):
            with st.form("new_emp"):
                e_name = st.text_input("Full Name")
                e_email = st.text_input("Corporate Email").strip().lower()
                e_role = st.text_input("Job Title")
                if st.form_submit_button("Onboard"):
                    if e_name and e_email:
                        try:
                            c.execute("INSERT INTO users (email, name, role, is_admin) VALUES (?, ?, ?, 0)", (e_email, e_name, e_role))
                            conn.commit()
                            st.success("User onboarded successfully!")
                        except:
                            st.error("Email is already registered.")
                            
        st.subheader("Active Personnel")
        c.execute("SELECT name, role, email FROM users WHERE is_admin = 0")
        emps = [{"Name": e[0], "Title": e[1], "Email": e[2]} for e in c.fetchall()]
        st.dataframe(emps, use_container_width=True)

# ==========================================
#             EMPLOYEE APP
# ==========================================
else:
    if menu == "🏠 My Desk":
        st.title(f"Good morning, {user['name'].split()[0]}! 👋")
        
        c.execute("SELECT SUM(hours) FROM timesheets WHERE user_id = ? AND date = ?", (user['id'], today_str))
        today_hrs = c.fetchone()[0] or 0.0
        
        st.metric("Hours Logged Today", f"{today_hrs} hrs", delta=None)
        
        if today_hrs == 0:
            st.warning("You haven't logged any time today. Head over to 'Log Time' before your shift ends.")
        else:
            st.success("You have successfully submitted work for today.")

    elif menu == "⏱️ Log Time":
        st.title("Log Timesheet")
        st.markdown("Record your shift, project, and deliverables.")
        
        with st.form("timesheet_form"):
            col1, col2 = st.columns(2)
            with col1:
                t_date = st.date_input("Work Date", datetime.date.today())
                t_shift = st.selectbox("Shift Schedule", ["10:00 AM - 07:00 PM", "12:00 PM - 09:00 PM", "02:00 PM - 11:00 PM", "Custom / Overtime"])
            with col2:
                c.execute("SELECT name FROM projects WHERE status = 'Active'")
                active_projects = [p[0] for p in c.fetchall()]
                t_project = st.selectbox("Project / Client", active_projects)
                t_hours = st.number_input("Hours Worked", min_value=0.5, max_value=24.0, value=8.0, step=0.5)
                
            t_desc = st.text_area("Task Description & Deliverables", height=150, help="What did you specifically achieve during these hours?")
            
            if st.form_submit_button("Submit Timesheet"):
                if len(t_desc.strip()) < 10:
                    st.error("Please provide a detailed description of your tasks (min 10 characters).")
                else:
                    t_date_str = t_date.strftime('%Y-%m-%d')
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    c.execute('''INSERT INTO timesheets (user_id, date, shift, project, hours, description, logged_at) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                              (user['id'], t_date_str, t_shift, t_project, t_hours, t_desc.strip(), now))
                    conn.commit()
                    st.success("Timesheet logged successfully!")

    elif menu == "📅 My Timesheets":
        st.title("My Timesheet History")
        
        c.execute('''SELECT date, project, shift, hours, description 
                     FROM timesheets WHERE user_id = ? ORDER BY date DESC LIMIT 30''', (user['id'],))
        my_logs = c.fetchall()
        
        if my_logs:
            logs_data = [{"Date": l[0], "Project": l[1], "Shift": l[2], "Hours": l[3], "Notes": l[4]} for l in my_logs]
            st.dataframe(logs_data, use_container_width=True)
        else:
            st.info("No timesheets logged yet.")
