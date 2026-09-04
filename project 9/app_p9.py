"""
Project 9: Tool Calling & Live Google Search Grounding
--------------------------------------------------------
Goal: Turn Gemini into a grounded web research assistant that accesses
real-time live data via Google Search grounding and cites clickable sources.

Run with:
    streamlit run app_p9.py
"""

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Grounded Search Agent",
    page_icon="🔎",
    layout="centered",
)

st.title("🔎 Live Google Search Grounding Agent")
st.caption("Ask about current events — Gemini will search the live web and cite its sources.")

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    st.markdown(
        "This agent uses Gemini's **native Google Search tool** "
        "to ground answers in real-time web data, instead of relying "
        "purely on the model's training data."
    )
    st.markdown("Get a key from [Google AI Studio](https://aistudio.google.com/apikey).")

# ---------------------------------------------------------
# Main Input
# ---------------------------------------------------------
query = st.text_area(
    "Ask something time-sensitive:",
    placeholder="e.g. What happened in the stock market today?",
    height=100,
)

col1, col2 = st.columns([1, 5])
with col1:
    run_clicked = st.button("Search & Answer", type="primary")

# ---------------------------------------------------------
# Core Logic
# ---------------------------------------------------------
if run_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif not query.strip():
        st.warning("⚠️ Please type a question first.")
    else:
        try:
            with st.spinner("Searching the live web and synthesizing an answer..."):
                client = genai.Client(api_key=api_key)

                # Define the native Google Search grounding tool
                grounding_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )

                config = types.GenerateContentConfig(
                    tools=[grounding_tool],
                )

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=query,
                    config=config,
                )

            # ---------------------------------------------
            # Display the synthesized answer
            # ---------------------------------------------
            st.success("✅ Grounded answer generated")
            st.markdown("### 🧠 Answer")
            st.write(response.text)

            # ---------------------------------------------
            # Parse and display grounding metadata (citations)
            # ---------------------------------------------
            st.markdown("### 🔗 Sources")

            try:
                candidate = response.candidates[0]
                grounding_metadata = candidate.grounding_metadata

                if grounding_metadata and grounding_metadata.grounding_chunks:
                    chunks = grounding_metadata.grounding_chunks
                    seen_urls = set()

                    for i, chunk in enumerate(chunks, start=1):
                        web_info = getattr(chunk, "web", None)
                        if web_info and web_info.uri:
                            if web_info.uri not in seen_urls:
                                seen_urls.add(web_info.uri)
                                title = web_info.title or web_info.uri
                                st.markdown(f"**{i}.** [{title}]({web_info.uri})")

                    if not seen_urls:
                        st.info("No distinct source URLs were returned for this query.")

                    # Optional: show the search queries Gemini actually ran
                    if grounding_metadata.web_search_queries:
                        with st.expander("🔍 Search queries used by Gemini"):
                            for q in grounding_metadata.web_search_queries:
                                st.code(q)
                else:
                    st.info("This response did not include grounding sources (the model may have answered from prior knowledge).")

            except (AttributeError, IndexError):
                st.info("No grounding metadata available for this response.")

        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 9 · Tool Calling & Live Google Search Grounding · Built with Streamlit + Gemini")