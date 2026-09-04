"""
Project 12: Multimodal Document & Code Inspector
------------------------------------------------------
Goal: Ingest uploaded files (Python scripts, PDFs, text) directly
in memory and ask Gemini to audit bugs / summarize architecture,
using Gemini's large multimodal context window.

Run with:
    python -m streamlit run app_p12.py
"""

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Document & Code Inspector",
    page_icon="🕵️",
    layout="centered",
)

st.title("🕵️ Multimodal Document & Code Inspector")
st.caption("Upload a Python file, PDF, or text file — Gemini will audit it, find bugs, and summarize its structure.")

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    st.markdown(
        "Supported file types: `.py`, `.txt`, `.md`, `.pdf`\n\n"
        "Files are sent **in memory** as raw bytes — nothing is "
        "saved to disk."
    )

# ---------------------------------------------------------
# Helper: map file extension -> MIME type
# ---------------------------------------------------------
MIME_MAP = {
    "py": "text/x-python",
    "txt": "text/plain",
    "md": "text/markdown",
    "pdf": "application/pdf",
}

def get_mime_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return MIME_MAP.get(ext, "application/octet-stream")

# ---------------------------------------------------------
# Main: File Upload
# ---------------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload a file to inspect",
    type=["py", "txt", "md", "pdf"],
)

analysis_mode = st.radio(
    "What should Gemini focus on?",
    options=["🐛 Audit for bugs", "🏗️ Summarize architecture", "🔍 Both"],
    horizontal=True,
)

run_clicked = st.button("Inspect File", type="primary")

# ---------------------------------------------------------
# Core Logic
# ---------------------------------------------------------
if run_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif uploaded_file is None:
        st.warning("⚠️ Please upload a file first.")
    else:
        try:
            with st.spinner("Reading file and analyzing with Gemini..."):
                # Read the uploaded file directly into memory as bytes
                file_bytes = uploaded_file.getvalue()
                mime_type = get_mime_type(uploaded_file.name)

                # Build the multimodal "part" from raw bytes
                file_part = types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type,
                )

                # Build the instruction based on selected mode
                if analysis_mode == "🐛 Audit for bugs":
                    instruction = (
                        "You are a senior code/document reviewer. Carefully inspect the "
                        "attached file. If it is code, identify bugs, point to the exact "
                        "line number(s) where possible, explain why each is a problem, and "
                        "suggest a fix. If it is a document, point out factual, logical, or "
                        "structural issues."
                    )
                elif analysis_mode == "🏗️ Summarize architecture":
                    instruction = (
                        "You are a technical writer. Summarize the overall structure, "
                        "purpose, and key components of the attached file in clear, "
                        "organized prose. If it is code, describe its architecture "
                        "(functions/classes, data flow, dependencies)."
                    )
                else:
                    instruction = (
                        "You are a senior reviewer. First, summarize the overall "
                        "architecture/purpose of the attached file. Then, separately, "
                        "audit it for bugs or issues, citing exact line numbers where "
                        "possible and suggesting fixes."
                    )

                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model="gemini-3.7-flash",
                    contents=[file_part, instruction],
                )

            st.success(f"✅ Analysis complete for `{uploaded_file.name}`")
            st.markdown("### 📋 Inspection Report")
            st.markdown(response.text)

            with st.expander("📄 File details"):
                st.write(f"**Name:** {uploaded_file.name}")
                st.write(f"**Size:** {len(file_bytes):,} bytes")
                st.write(f"**MIME type used:** {mime_type}")

        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 12 · Multimodal Document & Code Inspector · Built with Streamlit + Gemini")