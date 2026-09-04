import streamlit as st
import pandas as pd
import random
import os

# Set page configuration
st.set_page_config(page_title="Quiz Master Bot", page_icon="🤖", layout="centered")

# --- QUESTION BANK ---
QUIZ_BANK = {
    "Maths": [
        {"question": "What is 2 + 2?", "answer": "4"},
        {"question": "What is 10 - 3?", "answer": "7"},
        {"question": "What is 5 * 6?", "answer": "30"},
        {"question": "What is 12 / 4?", "answer": "3"},
        {"question": "What is the square root of 16?", "answer": "4"},
        {"question": "What is 15 + 27?", "answer": "42"},
        {"question": "What is 9 * 9?", "answer": "81"},
        {"question": "What is 100 - 45?", "answer": "55"}
    ],
    "Geography": [
        {"question": "What is the capital of Japan?", "answer": "Tokyo"},
        {"question": "What is the capital of France?", "answer": "Paris"},
        {"question": "Which ocean is the largest?", "answer": "Pacific"},
        {"question": "How many continents are there?", "answer": "7"},
        {"question": "What is the capital of Germany?", "answer": "Berlin"},
        {"question": "Which country has the Pyramids of Giza?", "answer": "Egypt"},
        {"question": "What is the capital of Italy?", "answer": "Rome"},
        {"question": "What is the longest river in the world?", "answer": "Nile"}
    ]
}

FILE_NAME = "scores.txt"

# --- HELPER FUNCTIONS ---
def save_score(player_name, score, total, category, rank):
    """Appends score data to persistent text storage safely."""
    with open(FILE_NAME, "a", encoding="utf-8") as file:
        file.write(f"{player_name} | {category} | {score}/{total} | Rank: {rank}\n")

def get_rank(percentage):
    """Calculates player badge based on percentage."""
    if percentage == 100:
        return "🏆 Grandmaster"
    elif percentage >= 75:
        return "🥇 Quiz Expert"
    elif percentage >= 50:
        return "🥈 Knowledge Seeker"
    else:
        return "🥉 Rookie"

# --- SESSION STATE INITIALIZATION ---
if "game_stage" not in st.session_state:
    st.session_state.game_stage = "START"  # Stages: START, QUIZ, RESULTS
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "questions" not in st.session_state:
    st.session_state.questions = []
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "chosen_category" not in st.session_state:
    st.session_state.chosen_category = ""
if "user_answer" not in st.session_state:
    st.session_state.user_answer = ""

# --- UI HEADER ---
st.title("🤖 Quiz Master Bot")
st.caption("Test your knowledge and climb the leaderboard!")
st.divider()

# --- SIDEBAR LEADERBOARD ---
st.sidebar.header("📜 Leaderboard")
if os.path.exists(FILE_NAME):
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            scores = [line.strip() for line in f.readlines() if line.strip()]
        if scores:
            parsed_data = [s.split(" | ") for s in scores if len(s.split(" | ")) == 4]
            if parsed_data:
                df = pd.DataFrame(parsed_data, columns=["Player", "Category", "Score", "Rank"])
                st.sidebar.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.sidebar.write("No valid score records yet!")
        else:
            st.sidebar.write("No scores saved yet!")
    except Exception:
        st.sidebar.write("Unable to load scores.")
else:
    st.sidebar.write("No scores saved yet!")

# --- GAME STAGES ---

# STAGE 1: SETUP SCREEN
if st.session_state.game_stage == "START":
    st.subheader("Welcome! Configure your quiz to begin.")
    
    player_input = st.text_input("Enter your contestant name:", value=st.session_state.player_name, placeholder="e.g. Alex")
    category = st.selectbox("Select Quiz Category:", list(QUIZ_BANK.keys()))
    
    if st.button("🚀 Start Quiz", type="primary"):
        if not player_input.strip():
            st.warning("Please enter your name before starting.")
        else:
            st.session_state.player_name = player_input.strip()
            st.session_state.chosen_category = category
            
            # Prepare randomized questions
            questions = QUIZ_BANK[category].copy()
            random.shuffle(questions)
            st.session_state.questions = questions
            
            # Reset pointers
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.user_answer = ""
            st.session_state.game_stage = "QUIZ"
            st.rerun()

# STAGE 2: ACTIVE QUIZ SCREEN
elif st.session_state.game_stage == "QUIZ":
    index = st.session_state.current_index
    total = len(st.session_state.questions)
    current_q = st.session_state.questions[index]
    
    # Visual Progress Bar
    st.progress((index) / total)
    st.write(f"**Question {index + 1} of {total}** ({st.session_state.chosen_category})")
    
    # Display Question
    st.info(f"❓ {current_q['question']}")
    
    ans_input = st.text_input("Your Answer:", key="quiz_answer_input").strip()
    
    if st.button("Submit Answer", type="primary"):
        if ans_input:
            if ans_input.lower() == current_q["answer"].lower():
                st.session_state.score += 1
                st.toast("Correct answer! 🎉", icon="✅")
            else:
                st.toast(f"Wrong! Correct answer was: {current_q['answer']}", icon="❌")
            
            # Advance to next question or complete quiz
            if index + 1 < total:
                st.session_state.current_index += 1
            else:
                # Save final score once when transitioning
                rank = get_rank(int((st.session_state.score / total) * 100))
                save_score(st.session_state.player_name, st.session_state.score, total, st.session_state.chosen_category, rank)
                st.session_state.game_stage = "RESULTS"
            
            st.rerun()
        else:
            st.warning("Please enter an answer before submitting.")

# STAGE 3: RESULTS SCREEN
elif st.session_state.game_stage == "RESULTS":
    score = st.session_state.score
    total = len(st.session_state.questions)
    percentage = int((score / total) * 100)
    rank = get_rank(percentage)
    
    st.balloons()
    st.subheader("🎉 Quiz Completed!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Final Score", f"{score}/{total}")
    col2.metric("Accuracy", f"{percentage}%")
    col3.metric("Rank Awarded", rank)
    
    st.divider()
    
    if percentage == 100:
        st.success("🤖 **Quiz Master:** Flawless victory! Perfect score!")
    elif percentage >= 50:
        st.info("🤖 **Quiz Master:** Good job! Solid performance.")
    else:
        st.error("🤖 **Quiz Master:** Practice makes perfect! Give it another try.")
        
    if st.button("Play Again 🔄", type="primary"):
        st.session_state.game_stage = "START"
        st.rerun()