"""
Project 11: Stateful Conversational Chatbot with Memory
------------------------------------------------------------
Goal: A multi-turn conversational chat interface that remembers
facts across turns, using Gemini's native chat session object.

Run with:
    python -m streamlit run app_p11.py
"""

import streamlit as st
from google import genai

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Memory Chatbot",
    page_icon="💬",
    layout="centered",
)

st.title("💬 Stateful Chatbot with Memory")
st.caption("A conversation that remembers what you told it — try stating a preference, then ask about it a few turns later.")

# ---------------------------------------------------------
# Sidebar: API Key + Clear Chat
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.pop("chat_session", None)
        st.session_state.pop("genai_client", None)
        st.session_state.pop("messages", None)
        st.rerun()
    st.markdown("---")
    st.markdown(
        "This app uses `client.chats.create()` to maintain a live "
        "chat object server-side, so Gemini sees the *entire* "
        "conversation history on every turn — not just your latest message."
    )

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []   # list of {"role": "user"/"assistant", "content": str}

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None  # holds the live Gemini chat object

if "genai_client" not in st.session_state:
    st.session_state.genai_client = None  # holds the client itself, kept alive across reruns

# ---------------------------------------------------------
# Guard: require API key before allowing chat
# ---------------------------------------------------------
if not api_key:
    st.info("👈 Enter your Gemini API key in the sidebar to start chatting.")
    st.stop()

# ---------------------------------------------------------
# Lazily create the chat session (only once per API key / session)
# ---------------------------------------------------------
if st.session_state.chat_session is None:
    try:
        st.session_state.genai_client = genai.Client(api_key=api_key)
        st.session_state.chat_session = st.session_state.genai_client.chats.create(model="gemini-3.7-flash")
    except Exception as e:
        st.error(f"❌ Could not start chat session: {e}")
        st.stop()

# ---------------------------------------------------------
# Render existing conversation history
# ---------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------
# Chat Input & Response
# ---------------------------------------------------------
user_input = st.chat_input("Type a message...")

if user_input:
    # 1. Show and store the user's message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Send to Gemini via the persistent chat object (it carries prior turns automatically)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat_session.send_message(user_input)
                reply_text = response.text
                st.markdown(reply_text)
            except Exception as e:
                reply_text = f"❌ Something went wrong: {e}"
                st.error(reply_text)

    # 3. Store assistant's reply in our own display history
    st.session_state.messages.append({"role": "assistant", "content": reply_text})

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 11 · Stateful Conversational Chatbot with Memory · Built with Streamlit + Gemini")