import streamlit as st
from google import genai
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

st.set_page_config(
    page_title="P3: Persona Translator",
    page_icon="🎭"
)

st.title("🎭 Persona Translator Agent")

persona = st.selectbox(
    "Select Persona",
    ["ELI5", "Ranked Gamer", "Gen Z Slang"]
)

topic = st.text_input(
    "Enter a complex topic (e.g., Inflation):"
)

if st.button("Translate"):

    if not api_key:
        st.error("Gemini API key is missing. Check your .env file.")

    elif not topic.strip():
        st.warning("Please enter a topic.")

    else:
        with st.spinner("Generating explanation..."):

            try:
                client = genai.Client(api_key=api_key)

                prompt = f"""
Explain the following topic in the style of {persona}.

Topic: {topic}

Rules:
- If the persona is ELI5, explain it like you are talking to a 5-year-old.
- If the persona is Ranked Gamer, explain it using gaming/ranked-game terminology.
- If the persona is Gen Z Slang, explain it using understandable Gen Z-style language.
- Keep the explanation simple and easy to understand.
"""

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )

                st.subheader(f"Explanation in {persona} style:")
                st.info(response.text)

            except Exception as e:
                st.error(f"Error: {e}")