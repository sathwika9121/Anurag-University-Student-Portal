import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Anurag University | Academic Portal", layout="wide")

# --- 2. ELITE UNIVERSITY THEME (CSS) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; }
    
    /* Sidebar styling with Logo Space */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 3px solid #facc15;
    }
    
    /* Navigation Text in Sidebar */
    section[data-testid="stSidebar"] .stRadio label p {
        color: #1e293b !important;
        font-weight: bold !important;
    }

    /* Form Container */
    [data-testid="stForm"] { 
        background-color: #ffffff !important; 
        padding: 40px !important; 
        border-radius: 20px !important; 
        border-top: 10px solid #facc15 !important; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.5) !important; 
    }
    [data-testid="stForm"] label p { color: #1e293b !important; font-weight: 700 !important; }
    
    /* Premium Buttons */
    div.stButton > button { 
        background: linear-gradient(90deg, #facc15 0%, #eab308 100%) !important; 
        color: #1e293b !important; font-weight: 800 !important; 
        border-radius: 50px !important; width: 100% !important; height: 3.5em !important; 
    }
    
    h1 { color: #facc15; text-shadow: 2px 2px #000; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost", user="root", password="root", database="student_portal"
        )
    except Exception:
        return None

# --- 4. SIDEBAR LOGO & NAV ---
# Official Anurag University Logo link
st.sidebar.image("https://anurag.edu.in/wp-content/uploads/2020/05/logo.png", width=250)
st.sidebar.markdown("<hr style='border:1px solid #facc15'>", unsafe_allow_html=True)
menu = ["Home", "Student Enrollment", "Daily Attendance", "Marks Entry", "Academic Reports"]
choice = st.sidebar.radio("CAMPUS NAV", menu)

conn = get_db_connection()

if conn is None:
    st.error("❌ Database Connection Failed! Ensure MySQL is running with password 'root'.")
else:
    # --- HOME PAGE ---
    if choice == "Home":
        st.markdown("<h1>🏛️ ANURAG UNIVERSITY DASHBOARD</h1>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # Campus View
            st.image("https://anurag.edu.in/wp-content/uploads/2020/05/slide-1.jpg", caption="Main Campus")
            st.markdown("### Welcome to the Academic Portal")
            st.write("Authorized access for managing B.Tech student records, lecture attendance, and internal assessment analytics.")
        
        with col2:
            # Students/Research View
            st.image("https://anurag.edu.in/wp-content/uploads/2021/04/research-1.jpg", caption="Excellence in Engineering")
            st.markdown("### Quick Statistics")
            df_count = pd.read_sql("SELECT COUNT(*) as total FROM students", conn)
            st.metric("Total Enrolled Students", df_count['total'][0])

    # --- STUDENT ENROLLMENT ---
    elif choice == "Student Enrollment":
        st.subheader("📝 B.Tech Admission Form")
        with st.form("enroll_form"):
            roll = st.text_input("Hall Ticket No (Digits only)")
            name = st.text_input("Student Name (Single Perfect Word)")
            sem = st.text_input("Current Semester")
            
            if st.form_submit_button("ENROLL STUDENT"):
                if not roll.isdigit():
                    st.error("❌ Invalid Roll No: Use numeric digits only!")
                elif len(name.split()) > 1 or not name.isalpha():
                    st.error("❌ Invalid Name: Provide a single word (A-Z only)!")
                else:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO students (roll_no, name, class) VALUES (%s, %s, %s)", (roll, name, sem))
                        conn.commit()
                        st.success(f"✅ Student {name} Enrolled!")
                    except mysql.connector.Error as err:
                        if err.errno == 1062:
                            st.error(f"❌ Error: Hall Ticket '{roll}' is already registered.")
                        else:
                            st.error(f"❌ Database Error: {err}")

    # --- DAILY ATTENDANCE ---
    elif choice == "Daily Attendance":
        st.subheader("📅 Lecture Attendance Logger")
        df = pd.read_sql("SELECT id, roll_no, name FROM students", conn)
        if not df.empty:
            with st.form("att_form"):
                att_date = st.date_input("Session Date", date.today())
                records = []
                for _, row in df.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"<span style='color:#1e293b'>**{row['roll_no']}** | {row['name']}</span>", unsafe_allow_html=True)
                    status = c2.radio("Status", ["Present", "Absent"], key=row['id'], horizontal=True)
                    records.append((row['id'], att_date, status))
                if st.form_submit_button("SYNC ATTENDANCE"):
                    cursor = conn.cursor()
                    cursor.executemany("INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)", records)
                    conn.commit()
                    st.success("✅ Attendance Synchronized!")
        else:
            st.info("No students found.")

    # --- MARKS ENTRY ---
    elif choice == "Marks Entry":
        st.subheader("📊 Course Internal Marks")
        df = pd.read_sql("SELECT id, name FROM students", conn)
        if not df.empty:
            with st.form("marks_entry"):
                s_id = st.selectbox("Select Student", df['id'], format_func=lambda x: df[df.id==x].name.values[0])
                subject = st.text_input("Course Name (Text only)")
                mks = st.number_input("Score", 0, 100)
                if st.form_submit_button("SAVE MARKS"):
                    if not re.match("^[a-zA-Z\s]+$", subject):
                        st.error("❌ Error: Course name must be text only!")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO marks (student_id, subject, marks) VALUES (%s, %s, %s)", (s_id, subject, mks))
                        conn.commit()
                        st.success("✅ Marks recorded!")

    # --- ACADEMIC REPORTS ---
    elif choice == "Academic Reports":
        st.subheader("📈 Campus Performance Dashboard")
        query = """
            SELECT s.roll_no, s.name, s.class as Semester, 
            AVG(m.marks) as Avg_GPA,
            (COUNT(CASE WHEN a.status = 'Present' THEN 1 END) / NULLIF(COUNT(a.id), 0)) * 100 as Att_Pct
            FROM students s 
            LEFT JOIN marks m ON s.id = m.student_id 
            LEFT JOIN attendance a ON s.id = a.student_id
            GROUP BY s.id
        """
        report = pd.read_sql(query, conn)
        if not report.empty:
            report['Result'] = report['Avg_GPA'].apply(lambda x: '✅ PASS' if x >= 40 else '❌ FAIL')
            st.dataframe(report.style.format({"Att_Pct": "{:.2f}%"}), use_container_width=True)
            st.bar_chart(report.set_index('name')['Avg_GPA'])

    conn.close()