import streamlit as st
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="P2: Gemini API Integration",
    page_icon="⚡"
)

st.title("⚡ Gemini Question Answering Assistant")

api_key = os.getenv("GEMINI_API_KEY")

question = st.text_area("Ask a question:")

if st.button("Ask AI"):

    if not api_key:
        st.error("Gemini API key is missing. Check your .env file.")

    elif not question.strip():
        st.warning("Please enter a question.")

    else:
        with st.spinner("Generating answer..."):

            try:
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=question
                )

                st.success("API Response:")
                st.write(response.text)

            except Exception as e:
                st.error(f"Error: {e}")