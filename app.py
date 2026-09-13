import streamlit as st
import sqlite3
import datetime

# --- PAGE CONFIGURATION & ENTERPRISE CSS ---
st.set_page_config(page_title="Enterprise HRMS & Workspace", page_icon="💠", layout="wide")

st.markdown("""
    <style>
    /* Sleek Enterprise Styling */
    .stApp { background-color: #f8f9fa; }
    .css-1d391kg { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #1e1e1e; }
    .stButton>button { border-radius: 6px; font-weight: 600; border: none; transition: 0.2s; }
    .stButton>button:hover { box-shadow: 0 4px 6px rgba(0,0,0,0.1); transform: translateY(-1px); }
    .task-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #4F46E5; margin-bottom: 10px; }
    .nudge-alert { padding: 15px; background-color: #fee2e2; border-left: 5px solid #ef4444; color: #991b1b; border-radius: 4px; margin-bottom: 15px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE ARCHITECTURE ---
def init_db():
    conn = sqlite3.connect('hrms_enterprise.db', check_same_thread=False)
    c = conn.cursor()
    # Core Tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT, role TEXT, is_admin INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS timesheets (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, project TEXT, hours REAL, work_done TEXT, timestamp TEXT)''')
    
    # Advanced SaaS Tables
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, project TEXT, title TEXT, status TEXT, assigned_to TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS links (id INTEGER PRIMARY KEY, title TEXT, url TEXT, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, user_id INTEGER, message TEXT, is_read INTEGER)''')
    conn.commit()

    # Seed Admin
    c.execute("INSERT OR IGNORE INTO users (email, name, role, is_admin) VALUES ('hr@company.com', 'HR Director', 'HR Manager', 1)")
    conn.commit()
    return conn, c

conn, c = init_db()

# --- AUTHENTICATION ---
if 'user' not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br><h1 style='text-align: center; color: #4F46E5;'>💠 Nexus HRMS</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Enterprise Resource & Project Management</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            email_input = st.text_input("Work Email").strip().lower()
            if st.form_submit_button("Authenticate", use_container_width=True):
                c.execute("SELECT id, email, name, role, is_admin FROM users WHERE LOWER(email) = ?", (email_input,))
                user_data = c.fetchone()
                if user_data:
                    st.session_state.user = {'id': user_data[0], 'email': user_data[1], 'name': user_data[2], 'role': user_data[3], 'is_admin': user_data[4]}
                    st.rerun()
                else:
                    st.error("Access Denied. Contact HR.")
    st.stop()

user = st.session_state.user
today_str = datetime.date.today().strftime('%Y-%m-%d')

# --- NOTIFICATION CHECK ---
c.execute("SELECT id, message FROM notifications WHERE user_id = ? AND is_read = 0", (user['id'],))
my_alerts = c.fetchall()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(f"### 👤 {user['name']}")
    st.caption(f"🛡️ {user['role']}")
    
    if my_alerts:
        st.error(f"🔔 {len(my_alerts)} Unread Notifications")
    
    st.divider()
    
    if user['is_admin']:
        menu = st.radio("HR & Admin Apps", ["📈 HR Command Center", "📋 Timesheet Audit", "kanban Project Board", "🔗 Resource Hub", "👥 Team Management"])
    else:
        menu = st.radio("My Workspace", ["🏠 My Dashboard", "kanban Project Board", "🔗 Resource Hub"])
        
    st.divider()
    if st.button("🚪 Secure Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# ==========================================
#             HR / ADMIN VIEWS
# ==========================================
if user['is_admin']:
    
    if menu == "📈 HR Command Center":
        st.title("HR Command Center")
        st.markdown("Track daily compliance and nudge employees instantly.")
        
        c.execute("SELECT id, name FROM users WHERE is_admin = 0")
        employees = c.fetchall()
        
        st.subheader(f"Attendance & Reports for {today_str}")
        
        # Display each employee and their status
        for emp_id, emp_name in employees:
            col1, col2, col3 = st.columns([3, 2, 2])
            c.execute("SELECT id FROM timesheets WHERE user_id = ? AND date = ?", (emp_id, today_str))
            has_reported = c.fetchone()
            
            with col1:
                st.markdown(f"**{emp_name}**")
            with col2:
                if has_reported:
                    st.success("✅ Submitted")
                else:
                    st.error("❌ Pending")
            with col3:
                if not has_reported:
                    if st.button(f"🔔 Nudge {emp_name}", key=f"nudge_{emp_id}"):
                        msg = f"⚠️ Reminder: Please submit your daily report for {today_str} immediately."
                        c.execute("INSERT INTO notifications (user_id, message, is_read) VALUES (?, ?, 0)", (emp_id, msg))
                        conn.commit()
                        st.toast(f"Nudge sent to {emp_name}!", icon="📨")
            st.divider()

    elif menu == "📋 Timesheet Audit":
        st.title("Timesheet Audit")
        target_date = st.date_input("Select Date", datetime.date.today()).strftime('%Y-%m-%d')
        
        c.execute('''SELECT users.name, timesheets.project, timesheets.hours, timesheets.work_done 
                     FROM timesheets JOIN users ON timesheets.user_id = users.id WHERE timesheets.date = ?''', (target_date,))
        reports = c.fetchall()
        
        if reports:
            st.dataframe([{"Employee": r[0], "Project": r[1], "Hours": r[2], "Details": r[3]} for r in reports], use_container_width=True)
        else:
            st.info("No logs found for this date.")

    elif menu == "👥 Team Management":
        st.title("Team Management")
        with st.form("onboard"):
            st.subheader("Onboard New Employee")
            e_name = st.text_input("Full Name")
            e_email = st.text_input("Email")
            e_role = st.text_input("Designation")
            if st.form_submit_button("Create Account"):
                try:
                    c.execute("INSERT INTO users (email, name, role, is_admin) VALUES (?, ?, ?, 0)", (e_email, e_name, e_role))
                    conn.commit()
                    st.success("Account created.")
                except:
                    st.error("Email already in system.")

# ==========================================
#             EMPLOYEE VIEWS
# ==========================================
else:
    if menu == "🏠 My Dashboard":
        st.title(f"Welcome back, {user['name'].split()[0]}")
        
        # Display HR Nudges/Notifications
        if my_alerts:
            for alert in my_alerts:
                st.markdown(f"<div class='nudge-alert'>{alert[1]}</div>", unsafe_allow_html=True)
                if st.button("Acknowledge & Dismiss", key=f"dismiss_{alert[0]}"):
                    c.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (alert[0],))
                    conn.commit()
                    st.rerun()

        st.subheader("📝 Submit Daily Report")
        with st.form("daily_report"):
            col1, col2 = st.columns(2)
            with col1:
                rep_date = st.date_input("Report Date", datetime.date.today())
                c.execute("SELECT name FROM projects")
                proj_list = [p[0] for p in c.fetchall()]
                rep_proj = st.selectbox("Project", proj_list if proj_list else ["General"])
            with col2:
                rep_hours = st.number_input("Hours Worked", 1.0, 24.0, 8.0, 0.5)
            
            rep_details = st.text_area("Detailed Work Summary (minimum 20 chars)")
            
            if st.form_submit_button("Submit to HR", use_container_width=True):
                if len(rep_details) < 20:
                    st.error("Please provide more detail.")
                else:
                    c.execute("INSERT INTO timesheets (user_id, date, project, hours, work_done, timestamp) VALUES (?, ?, ?, ?, ?, ?)", 
                              (user['id'], rep_date.strftime('%Y-%m-%d'), rep_proj, rep_hours, rep_details, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    st.success("Report securely submitted to HR.")

# ==========================================
#             SHARED VIEWS (HR & Emp)
# ==========================================
if menu == "kanban Project Board":
    st.title("Project Workspace (Kanban)")
    
    # Add new task (Everyone can add tasks, or you can restrict it)
    with st.expander("➕ Add New Task"):
        with st.form("add_task"):
            c.execute("SELECT name FROM users")
            all_users = [u[0] for u in c.fetchall()]
            
            t_title = st.text_input("Task Title")
            t_assignee = st.selectbox("Assign To", all_users)
            t_status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            
            if st.form_submit_button("Create Task"):
                c.execute("INSERT INTO tasks (project, title, status, assigned_to) VALUES ('General', ?, ?, ?)", (t_title, t_status, t_assignee))
                conn.commit()
                st.success("Task Added!")
                st.rerun()

    # KANBAN BOARD RENDERING
    col_todo, col_prog, col_done = st.columns(3)
    
    c.execute("SELECT id, title, assigned_to, status FROM tasks")
    all_tasks = c.fetchall()
    
    def render_task(task_id, title, assignee, current_status):
        st.markdown(f"<div class='task-card'><b>{title}</b><br><small>👤 {assignee}</small></div>", unsafe_allow_html=True)
        # Quick status change dropdown
        new_stat = st.selectbox("Move", ["To Do", "In Progress", "Done"], index=["To Do", "In Progress", "Done"].index(current_status), key=f"stat_{task_id}", label_visibility="collapsed")
        if new_stat != current_status:
            c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_stat, task_id))
            conn.commit()
            st.rerun()

    with col_todo:
        st.subheader("📋 To Do")
        for t in [t for t in all_tasks if t[3] == "To Do"]: render_task(t[0], t[1], t[2], t[3])
            
    with col_prog:
        st.subheader("⏳ In Progress")
        for t in [t for t in all_tasks if t[3] == "In Progress"]: render_task(t[0], t[1], t[2], t[3])
            
    with col_done:
        st.subheader("✅ Done")
        for t in [t for t in all_tasks if t[3] == "Done"]: render_task(t[0], t[1], t[2], t[3])

elif menu == "🔗 Resource Hub":
    st.title("Resource & Link Hub")
    st.markdown("Company links, HR policies, and project documents.")
    
    with st.form("add_link"):
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1: l_title = st.text_input("Title (e.g., Leave Policy)")
        with col2: l_url = st.text_input("URL Link (https://...)")
        with col3: l_cat = st.selectbox("Category", ["HR", "Tools", "Projects"])
        if st.form_submit_button("Save Link"):
            c.execute("INSERT INTO links (title, url, category) VALUES (?, ?, ?)", (l_title, l_url, l_cat))
            conn.commit()
            st.rerun()
            
    st.divider()
    c.execute("SELECT title, url, category FROM links ORDER BY category")
    saved_links = c.fetchall()
    if saved_links:
        st.dataframe([{"Category": l[2], "Title": l[0], "Link": l[1]} for l in saved_links], use_container_width=True)
