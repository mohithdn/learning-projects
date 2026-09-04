import streamlit as st
import sqlite3
import pandas as pd

# -----------------------------
# Database setup
# -----------------------------
DB_NAME = "university.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                roll_no INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                course TEXT NOT NULL,
                marks REAL NOT NULL,
                grade TEXT NOT NULL
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database initialization error: {e}")
    finally:
        conn.close()

def calculate_grade(marks: float) -> str:
    if marks >= 90:
        return "A"
    elif marks >= 75:
        return "B"
    elif marks >= 60:
        return "C"
    else:
        return "D"

def insert_student(roll_no, name, department, course, marks, grade):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO students (roll_no, name, department, course, marks, grade)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (roll_no, name, department, course, marks, grade),
        )
        conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)
    finally:
        conn.close()

def run_query(query: str):
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        return df, None
    except sqlite3.Error as e:
        return None, str(e)
    except pd.errors.DatabaseError as e:
        return None, str(e)
    finally:
        conn.close()

# -----------------------------
# App configuration
# -----------------------------
st.set_page_config(page_title="Student Academic Records & Report Studio", layout="wide")
st.title("🎓 Student Academic Records & Report Studio")

init_db()

tab1, tab2 = st.tabs(["🎓 Register Student", "📊 Academic Reports"])

# -----------------------------
# TAB 1: Register Student
# -----------------------------
with tab1:
    st.subheader("Register a New Student")

    with st.form("registration_form", clear_on_submit=True):
        roll_no = st.number_input("Roll Number", min_value=1, step=1, format="%d")
        name = st.text_input("Full Name")
        department = st.selectbox(
            "Department",
            ["Computer Science", "Data Science", "Electronics", "Mechanical"]
        )
        course = st.text_input("Course Name")
        marks = st.number_input("Marks", min_value=0.0, max_value=100.0, step=0.5)

        submitted = st.form_submit_button("Register Student")

        if submitted:
            if not name.strip() or not course.strip():
                st.warning("Please fill in all fields before submitting.")
            else:
                grade = calculate_grade(marks)
                success, error = insert_student(
                    int(roll_no), name.strip(), department, course.strip(), marks, grade
                )
                if success:
                    st.success(
                        f"✅ Student '{name}' registered successfully with Grade '{grade}'!"
                    )
                else:
                    st.error(f"❌ Could not register student. Error: {error}")

# -----------------------------
# TAB 2: Academic Reports
# -----------------------------
with tab2:
    st.subheader("Generate Academic Reports")

    report_options = {
        "All Students List": "SELECT * FROM students;",
        "Top Performers (>= 75 Marks)": (
            "SELECT name, department, marks, grade FROM students "
            "WHERE marks >= 75 ORDER BY marks DESC;"
        ),
        "Department-wise Average Marks": (
            "SELECT department, AVG(marks) AS avg_marks FROM students "
            "GROUP BY department;"
        ),
        "Grade Breakdown Count": (
            "SELECT grade, COUNT(*) AS total_students FROM students "
            "GROUP BY grade;"
        ),
        "Custom SQL Query": None,
    }

    selected_report = st.selectbox("Select a Report", list(report_options.keys()))

    if selected_report == "Custom SQL Query":
        query = st.text_area(
            "Enter your custom SQL query (SELECT statements recommended):",
            value="SELECT * FROM students;",
            height=120,
        )
    else:
        query = report_options[selected_report]

    generate_chart = st.checkbox("Generate Chart Visualization")

    run_report = st.button("Run Report")

    if run_report:
        st.code(query, language="sql")

        df, error = run_query(query)

        if error:
            st.error(f"❌ Query failed: {error}")
        elif df is None or df.empty:
            st.info("No data returned for this query.")
        else:
            st.dataframe(df, use_container_width=True)

            if generate_chart:
                numeric_cols = df.select_dtypes(include="number").columns.tolist()

                if not numeric_cols:
                    st.warning("No numeric columns available to chart.")
                else:
                    # Try to find a good label column (non-numeric, e.g. name/department/grade)
                    label_cols = [c for c in df.columns if c not in numeric_cols]

                    chart_df = df.copy()
                    if label_cols:
                        chart_df = chart_df.set_index(label_cols[0])

                    st.bar_chart(chart_df[numeric_cols])