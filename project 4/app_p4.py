import streamlit as st
from google import genai
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Page settings
st.set_page_config(
    page_title="P4: Rule-Based Chatbot",
    page_icon="🤖"
)

st.title("🤖 Customer Support FAQ Bot")
st.write("Ask me about hours, pricing, support, or any other question.")

# User input
user_input = st.text_input(
    "Ask a question:",
    placeholder="Example: What are your working hours?"
)

# FAQ rules
faq_rules = {
    "hours": "We are open 24/7 online!",
    "pricing": "Our basic tier starts at $0/month.",
    "support": "Contact us at support@example.com."
}


if st.button("Send"):

    if not user_input.strip():
        st.warning("Please enter a question.")

    else:
        query = user_input.strip().lower()

        # Check for FAQ keywords
        if "hour" in query or "open" in query or "timing" in query:
            response = faq_rules["hours"]

            st.success("FAQ Match Found!")
            st.write(f"**Bot:** {response}")

        elif "price" in query or "pricing" in query or "cost" in query:
            response = faq_rules["pricing"]

            st.success("FAQ Match Found!")
            st.write(f"**Bot:** {response}")

        elif "support" in query or "help" in query or "contact" in query:
            response = faq_rules["support"]

            st.success("FAQ Match Found!")
            st.write(f"**Bot:** {response}")

        else:
            # Fallback to Gemini
            st.info("No FAQ match found. Forwarding to fallback agent...")

            if not api_key:
                st.error("Gemini API key is missing. Check your .env file.")

            else:
                try:
                    with st.spinner("Fallback agent is thinking..."):

                        client = genai.Client(api_key=api_key)

                        prompt = f"""
You are a helpful customer support assistant.

The FAQ system could not answer this question.

User question:
{user_input}

Give a short, helpful and professional answer.
If you don't know the answer, clearly say that the customer should contact support.
"""

                        result = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=prompt
                        )

                        st.subheader("🤖 Fallback Agent")
                        st.write(result.text)

                except Exception as e:
                    st.error(f"Error: {e}")