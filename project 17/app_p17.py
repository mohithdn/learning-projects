"""
Project 17: Natural Language SQL & Database Query Agent
-----------------------------------------------------------
Goal: Translate a plain-English question into SQL, run it safely
against a real SQLite database, and visualize the result — without
the user ever writing SQL themselves.

Run with:
    python -m streamlit run app_p17.py
"""

import re
import sqlite3

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="NL-to-SQL Agent",
    page_icon="🗄️",
    layout="centered",
)

st.title("🗄️ Natural Language SQL & Database Query Agent")
st.caption("Ask a plain-English question about the sales data — Gemini writes the SQL, the app runs it safely, and charts the result.")

GEN_MODEL = "gemini-3.7-flash"
DB_PATH = ":memory:"  # in-memory SQLite for this demo; swap for a file path to persist

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    st.markdown(
        "**Pipeline:**\n"
        "1️⃣ Extract schema automatically from SQLite\n"
        "2️⃣ Gemini translates your question → SQL\n"
        "3️⃣ App validates it's read-only, then executes\n"
        "4️⃣ Results shown as a table + bar chart"
    )

# ---------------------------------------------------------
# STEP 1: Set up a demo SQLite database (sales reps table)
# In-memory + cached so it persists across reruns within one session
# but resets if the app restarts.
# ---------------------------------------------------------
@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_reps (
            id INTEGER PRIMARY KEY,
            name TEXT,
            region TEXT,
            deals_closed INTEGER,
            total_revenue REAL,
            commission_rate REAL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM sales_reps")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            (1, "Ananya Rao",    "South",  42, 315000, 0.08),
            (2, "Vikram Shetty", "West",   35, 278000, 0.07),
            (3, "Priya Nair",    "South",  51, 402000, 0.09),
            (4, "Rahul Mehta",   "North",  29, 198000, 0.06),
            (5, "Sneha Iyer",    "East",   38, 265000, 0.07),
            (6, "Karthik Reddy", "South",  47, 356000, 0.085),
            (7, "Divya Menon",   "West",   33, 241000, 0.065),
            (8, "Arjun Kumar",   "North",  25, 175000, 0.06),
            (9, "Meera Pillai",  "East",   40, 289000, 0.075),
            (10, "Rohan Das",    "North",  31, 210000, 0.065),
        ]
        cursor.executemany(
            "INSERT INTO sales_reps VALUES (?, ?, ?, ?, ?, ?)", sample_data
        )
        conn.commit()

    return conn


conn = get_connection()

# ---------------------------------------------------------
# STEP 2: Automated schema extraction
# ---------------------------------------------------------
def get_schema_description(conn: sqlite3.Connection) -> str:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    schema_lines = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        col_descriptions = ", ".join(f"{col[1]} ({col[2]})" for col in columns)
        schema_lines.append(f"Table '{table}': columns = {col_descriptions}")

    return "\n".join(schema_lines)


schema_description = get_schema_description(conn)

with st.expander("📋 Database schema (auto-extracted)"):
    st.code(schema_description)
    st.dataframe(pd.read_sql_query("SELECT * FROM sales_reps", conn), use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------
# STEP 3: Safe query execution guard
# Only allow SELECT statements — block anything that could mutate
# or damage the database (INSERT, UPDATE, DELETE, DROP, ALTER, etc.)
# ---------------------------------------------------------
FORBIDDEN_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "ATTACH", "PRAGMA"]

def is_safe_select(sql: str) -> bool:
    stripped = sql.strip().rstrip(";").upper()
    if not stripped.startswith("SELECT"):
        return False
    if any(keyword in stripped for keyword in FORBIDDEN_KEYWORDS):
        return False
    if ";" in sql.strip().rstrip(";"):  # block stacked/multiple statements
        return False
    return True

def extract_sql(raw_text: str) -> str:
    """Strips markdown code fences if the model adds them despite instructions."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_text.strip()

# ---------------------------------------------------------
# Main Input
# ---------------------------------------------------------
st.subheader("Ask a Question")

question = st.text_input(
    "Your question about the sales data:",
    placeholder="e.g. Top 3 highest paid reps",
)

run_clicked = st.button("🔎 Run Query", type="primary")

# ---------------------------------------------------------
# Core Logic
# ---------------------------------------------------------
if run_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif not question.strip():
        st.warning("⚠️ Please type a question first.")
    else:
        try:
            client = genai.Client(api_key=api_key)

            # -----------------------------------------------------
            # STEP 4: Generate SQL from natural language
            # -----------------------------------------------------
            with st.spinner("Translating your question into SQL..."):
                sql_prompt = f"""
                You are a SQL expert working with a SQLite database.

                Schema:
                {schema_description}

                Write a single, valid, read-only SQLite SELECT query that answers
                this question: "{question}"

                Rules:
                - Return ONLY the raw SQL query. No explanation, no markdown fences.
                - Only use SELECT — never modify data.
                - Use only the columns/tables shown in the schema above.
                """

                sql_response = client.models.generate_content(
                    model=GEN_MODEL,
                    contents=sql_prompt,
                )

                generated_sql = extract_sql(sql_response.text)

            st.markdown("### 🧾 Generated SQL")
            st.code(generated_sql, language="sql")

            # -----------------------------------------------------
            # STEP 5: Safety validation before execution
            # -----------------------------------------------------
            if not is_safe_select(generated_sql):
                st.error("🚫 Blocked: the generated query failed the safety check (must be a single, read-only SELECT statement).")
            else:
                with st.spinner("Executing query..."):
                    result_df = pd.read_sql_query(generated_sql, conn)

                if result_df.empty:
                    st.info("Query ran successfully but returned no rows.")
                else:
                    st.markdown("### 📊 Results")
                    st.dataframe(result_df, use_container_width=True)

                    # -------------------------------------------------
                    # STEP 6: Auto-chart if there's a sensible numeric column
                    # -------------------------------------------------
                    numeric_cols = result_df.select_dtypes(include="number").columns.tolist()
                    label_cols = result_df.select_dtypes(exclude="number").columns.tolist()

                    if numeric_cols and label_cols:
                        chart_df = result_df.set_index(label_cols[0])[numeric_cols[0]]
                        st.markdown(f"### 📈 {numeric_cols[0]} by {label_cols[0]}")
                        st.bar_chart(chart_df)
                    elif numeric_cols:
                        st.bar_chart(result_df[numeric_cols])

        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 17 · Natural Language SQL & Database Query Agent · Built with Streamlit + Gemini + SQLite")