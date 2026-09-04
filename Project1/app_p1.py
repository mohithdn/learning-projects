import streamlit as st

st.set_page_config(page_title="P1: Hello World", page_icon="👋")
st.title("👋 Interactive Greeting App")

name = st.text_input("Enter your name:")
if st.button("Submit"):
    if name.strip():
        st.success(f"Hello, {name}! Welcome to building AI apps.")
    else:
        st.warning("Please enter a valid name before submitting.")