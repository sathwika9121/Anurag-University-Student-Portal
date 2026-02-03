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
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 3px solid #facc15;
    }
    
    /* Navigation Text */
    section[data-testid="stSidebar"] .stRadio label p {
        color: #1e293b !important;
        font-weight: bold !important;
    }

    /* Form Design */
    [data-testid="stForm"] { 
        background-color: #ffffff !important; 
        padding: 40px !important; 
        border-radius: 20px !important; 
        border-top: 10px solid #facc15 !important; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.5) !important; 
    }
    [data-testid="stForm"] label p { color: #1e293b !important; font-weight: 700 !important; }
    
    /* Premium Gold Buttons */
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
            host="localhost", 
            user="root", 
            password="root", 
            database="student_portal"
        )
    except Exception:
        return None

# --- 4. SIDEBAR LOGO & NAVIGATION ---
# Anurag University Logo
st.sidebar.image("https://anurag.edu.in/wp-content/uploads/2020/05/logo.png", use_container_width=True)
st.sidebar.markdown("<hr style='border:1px solid #facc15'>", unsafe_allow_html=True)
menu = ["Home", "Student Enrollment", "Daily Attendance", "Marks Entry", "Academic Reports"]
choice = st.sidebar.radio("CAMPUS NAV", menu)

conn = get_db_connection()

if conn is None:
    st.error("❌ Database Connection Failed! Ensure MySQL is running with password 'root' and database 'student_portal' exists.")
else:
    # --- 1. HOME PAGE ---
    if choice == "Home":
        st.markdown("<h1>🏛️ ANURAG UNIVERSITY DASHBOARD</h1>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image("https://anurag.edu.in/wp-content/uploads/2020/05/slide-1.jpg", caption="Anurag University Campus")
            st.markdown("### Academic Excellence")
            st.write("Welcome to the B.Tech Management System. Authorized staff can manage student enrollment, attendance, and internal assessments.")
        
        with col2:
            st.image("https://anurag.edu.in/wp-content/uploads/2021/04/research-1.jpg", caption="Innovation & Research")
            st.markdown("### Current Enrollment Status")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]
            st.metric("Total Students Registered", total_students)

    # --- 2. STUDENT ENROLLMENT ---
    elif choice == "Student Enrollment":
        st.subheader("📝 B.Tech Admission Form")
        with st.form("enroll_form"):
            roll = st.text_input("Hall Ticket No (Numbers only)")
            name = st.text_input("Student Name (Single Perfect Word)")
            sem = st.text_input("Current Semester (e.g. Sem 3)")
            
            if st.form_submit_button("ENROLL STUDENT"):
                if not roll.isdigit():
                    st.error("❌ Invalid Roll No: Please enter numeric digits only!")
                elif len(name.split()) > 1 or not name.isalpha():
                    st.error("❌ Invalid Name: Provide a single name perfectly (A-Z only)!")
                elif not sem:
                    st.error("❌ Semester field is mandatory!")
                else:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO students (roll_no, name, class) VALUES (%s, %s, %s)", (roll, name, sem))
                        conn.commit()
                        st.success(f"✅ B.Tech Student {name} Enrolled Successfully!")
                    except mysql.connector.Error as err:
                        if err.errno == 1062:
                            st.error(f"❌ Error: Hall Ticket No '{roll}' is already in use!")
                        else:
                            st.error(f"❌ Database Error: {err}")

    # --- 3. DAILY ATTENDANCE ---
    elif choice == "Daily Attendance":
        st.subheader("📅 Lecture Attendance Logger")
        df = pd.read_sql("SELECT id, roll_no, name FROM students", conn)
        if not df.empty:
            with st.form("att_form"):
                att_date = st.date_input("Session Date", date.today())
                records = []
                for _, row in df.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"<span style='color:black'>**{row['roll_no']}** | {row['name']}</span>", unsafe_allow_html=True)
                    status = c2.radio("Status", ["Present", "Absent"], key=row['id'], horizontal=True)
                    records.append((row['id'], att_date, status))
                
                if st.form_submit_button("SAVE ATTENDANCE"):
                    cursor = conn.cursor()
                    cursor.executemany("INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)", records)
                    conn.commit()
                    st.success("✅ Attendance Synchronized with Database!")
        else:
            st.info("No students enrolled yet.")

    # --- 4. MARKS ENTRY ---
    elif choice == "Marks Entry":
        st.subheader("📊 Course Internal Marks")
        df = pd.read_sql("SELECT id, name FROM students", conn)
        if not df.empty:
            with st.form("marks_entry_form"):
                s_id = st.selectbox("Select Student", df['id'], format_func=lambda x: df[df.id==x].name.values[0])
                subject = st.text_input("Course Name (Characters only)")
                mks = st.number_input("Assessment Score", 0, 100)
                
                if st.form_submit_button("COMMIT MARKS"):
                    if not re.match("^[a-zA-Z\s]+$", subject):
                        st.error("❌ Invalid Course Name: Numbers are not allowed!")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO marks (student_id, subject, marks) VALUES (%s, %s, %s)", (s_id, subject, mks))
                        conn.commit()
                        st.success("✅ Internal marks recorded successfully!")
        else:
            st.info("Enroll students before entering marks.")

    # --- 5. ACADEMIC REPORTS ---
    elif choice == "Academic Reports":
        st.subheader("📈 Campus Performance Analytics")
        query = """
            SELECT s.roll_no as HallTicket, s.name as StudentName, s.class as Semester, 
            AVG(m.marks) as Avg_GPA,
            (COUNT(CASE WHEN a.status = 'Present' THEN 1 END) / NULLIF(COUNT(a.id), 0)) * 100 as Att_Percentage
            FROM students s 
            LEFT JOIN marks m ON s.id = m.student_id 
            LEFT JOIN attendance a ON s.id = a.student_id
            GROUP BY s.id
        """
        report = pd.read_sql(query, conn)
        if not report.empty:
            report['Result'] = report['Avg_GPA'].apply(lambda x: '✅ PASS' if x >= 40 else '❌ FAIL')
            st.dataframe(report.style.format({"Att_Percentage": "{:.2f}%"}), use_container_width=True)
            st.divider()
            st.bar_chart(report.set_index('StudentName')['Avg_GPA'])
        else:
            st.info("No records available to generate reports.")

    conn.close()