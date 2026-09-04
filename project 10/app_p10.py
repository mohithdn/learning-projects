"""
Project 10: Multi-Step Interactive Study Buddy
--------------------------------------------------
Goal: A 3-stage state machine that:
  Stage 1 -> Explains a concept (topic overview)
  Stage 2 -> Generates an interactive 3-question MCQ quiz
  Stage 3 -> Grades the submission and shows rationales

Run with:
    python -m streamlit run app_p10.py
"""

import json
import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Study Buddy Agent",
    page_icon="📘",
    layout="centered",
)

st.title("📘 Multi-Step Study Buddy")
st.caption("Learn a topic, take a quiz, and get graded — all in one flow.")

# ---------------------------------------------------------
# Sidebar: API Key + Reset
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    if st.button("🔄 Restart Session"):
        for key in ["stage", "overview", "quiz", "answers"]:
            st.session_state.pop(key, None)
        st.rerun()
    st.markdown("---")
    st.markdown(
        "**Stages:**\n"
        "1️⃣ Overview\n"
        "2️⃣ Quiz\n"
        "3️⃣ Grading"
    )

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "stage" not in st.session_state:
    st.session_state.stage = 1          # 1 = overview, 2 = quiz, 3 = graded
if "overview" not in st.session_state:
    st.session_state.overview = ""
if "quiz" not in st.session_state:
    st.session_state.quiz = None        # parsed JSON quiz object
if "answers" not in st.session_state:
    st.session_state.answers = {}       # user's selected answers

# ---------------------------------------------------------
# Helper: get a configured client
# ---------------------------------------------------------
def get_client():
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------
# STAGE 1: Topic Input & Overview Generation
# ---------------------------------------------------------
if st.session_state.stage == 1:
    st.subheader("Step 1 · Choose a Topic")

    topic = st.text_input("What do you want to study?", placeholder="e.g. Photosynthesis, Newton's Laws, HTTP Basics")

    if st.button("Generate Overview", type="primary"):
        if not api_key:
            st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
        elif not topic.strip():
            st.warning("⚠️ Please enter a topic first.")
        else:
            with st.spinner("Preparing your study overview..."):
                try:
                    client = get_client()
                    prompt = f"Explain the topic '{topic}' clearly in 4-6 short paragraphs for a student learning it for the first time."
                    response = client.models.generate_content(
                        model="gemini-3.7-flash",
                        contents=prompt,
                    )
                    st.session_state.overview = response.text
                    st.session_state.topic = topic
                    st.session_state.stage = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# STAGE 2: Show Overview + Generate & Display Quiz
# ---------------------------------------------------------
elif st.session_state.stage == 2:
    st.subheader(f"Step 2 · Overview: {st.session_state.topic}")
    st.markdown(st.session_state.overview)
    st.markdown("---")

    if st.session_state.quiz is None:
        if st.button("Generate Quiz (3 Questions)", type="primary"):
            with st.spinner("Writing your quiz questions..."):
                try:
                    client = get_client()

                    quiz_prompt = f"""
                    Create exactly 3 multiple-choice questions to test understanding of: {st.session_state.topic}

                    Return ONLY valid JSON, no markdown fences, no preamble, in this exact schema:
                    {{
                      "questions": [
                        {{
                          "question": "string",
                          "options": ["A", "B", "C", "D"],
                          "correct_index": 0,
                          "rationale": "string explaining why the correct answer is right"
                        }}
                      ]
                    }}
                    """

                    config = types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )

                    response = client.models.generate_content(
                        model="gemini-3.7-flash",
                        contents=quiz_prompt,
                        config=config,
                    )

                    quiz_data = json.loads(response.text)
                    st.session_state.quiz = quiz_data["questions"]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Something went wrong generating the quiz: {e}")
    else:
        st.subheader("📝 Quiz Time")
        for i, q in enumerate(st.session_state.quiz):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            choice = st.radio(
                label=f"question_{i}",
                options=list(range(len(q["options"]))),
                format_func=lambda idx, opts=q["options"]: opts[idx],
                key=f"radio_{i}",
                label_visibility="collapsed",
            )
            st.session_state.answers[i] = choice
            st.markdown("")

        if st.button("Submit Quiz", type="primary"):
            st.session_state.stage = 3
            st.rerun()

# ---------------------------------------------------------
# STAGE 3: Grade Submission
# ---------------------------------------------------------
elif st.session_state.stage == 3:
    st.subheader("✅ Step 3 · Results")

    quiz = st.session_state.quiz
    answers = st.session_state.answers
    score = 0

    for i, q in enumerate(quiz):
        user_choice = answers.get(i)
        correct_idx = q["correct_index"]
        is_correct = user_choice == correct_idx

        if is_correct:
            score += 1

        st.markdown(f"**Q{i+1}. {q['question']}**")
        st.write(f"Your answer: {q['options'][user_choice]}")

        if is_correct:
            st.success(f"✔️ Correct!")
        else:
            st.error(f"❌ Incorrect. Correct answer: {q['options'][correct_idx]}")

        with st.expander("💡 Why?"):
            st.write(q["rationale"])

        st.markdown("---")

    st.metric("Final Score", f"{score} / {len(quiz)}")

    if st.button("🔁 Study a New Topic"):
        for key in ["stage", "overview", "quiz", "answers"]:
            st.session_state.pop(key, None)
        st.rerun()

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 10 · Multi-Step Interactive Study Buddy · Built with Streamlit + Gemini")