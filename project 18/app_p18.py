"""
Project 18: Self-Healing AI Coder Agent
--------------------------------------------
Goal: Gemini writes a Python function, the app runs it against
HIDDEN assertion-based edge case tests in a sandbox, and if it
fails, the traceback is fed back to Gemini for automatic repair —
up to 3 attempts — until the tests pass or attempts run out.

Run with:
    python -m streamlit run app_p18.py
"""

import traceback

import streamlit as st
from google import genai

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Self-Healing Coder Agent",
    page_icon="🩹",
    layout="centered",
)

st.title("🩹 Self-Healing AI Coder Agent")
st.caption("Describe an algorithm — Gemini writes it, hidden tests probe edge cases, and the agent self-repairs failing code automatically.")

GEN_MODEL = "gemini-3.7-flash"
MAX_ATTEMPTS = 3

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    st.markdown(
        f"**Pipeline:**\n"
        f"1️⃣ Gemini writes an initial solution\n"
        f"2️⃣ Code runs in a sandbox (`exec()`) against hidden edge-case assertions\n"
        f"3️⃣ On failure, the traceback is sent back to Gemini\n"
        f"4️⃣ Repeats up to **{MAX_ATTEMPTS} attempts** until tests pass\n\n"
        "⚠️ `exec()` runs arbitrary generated code. This demo sandboxes it "
        "in a restricted namespace, but never run this pattern against "
        "untrusted production input."
    )

# ---------------------------------------------------------
# STEP 1: Pre-defined tasks with HIDDEN test assertions
# The user never sees these tests — they exist purely to catch edge
# cases a naive first-draft implementation commonly misses.
# ---------------------------------------------------------
TASKS = {
    "Find the second largest number in a list": {
        "function_name": "second_largest",
        "signature": "def second_largest(nums: list[int]) -> int:",
        "description": "Given a list of integers, return the second largest UNIQUE value.",
        "hidden_tests": [
            ("assert second_largest([5, 1, 4, 2, 8]) == 5", None),
            ("assert second_largest([1, 1, 1, 2]) == 1", None),
            ("assert second_largest([10, 10, 9]) == 9", None),
            ("assert second_largest([-5, -1, -3]) == -3", None),
        ],
    },
    "Reverse words in a sentence": {
        "function_name": "reverse_words",
        "signature": "def reverse_words(sentence: str) -> str:",
        "description": "Reverse the ORDER of words in a sentence (not the letters), collapsing extra whitespace.",
        "hidden_tests": [
            ('assert reverse_words("hello world") == "world hello"', None),
            ('assert reverse_words("  a   b  c ") == "c b a"', None),
            ('assert reverse_words("single") == "single"', None),
            ('assert reverse_words("") == ""', None),
        ],
    },
    "Check if a number is a palindrome": {
        "function_name": "is_palindrome_number",
        "signature": "def is_palindrome_number(n: int) -> bool:",
        "description": "Return True if the integer reads the same forwards and backwards. Negative numbers are never palindromes.",
        "hidden_tests": [
            ("assert is_palindrome_number(121) == True", None),
            ("assert is_palindrome_number(-121) == False", None),
            ("assert is_palindrome_number(10) == False", None),
            ("assert is_palindrome_number(0) == True", None),
        ],
    },
    "Find the first non-repeating character": {
        "function_name": "first_unique_char",
        "signature": "def first_unique_char(s: str) -> str:",
        "description": "Return the first character in the string that does not repeat. Return an empty string if none exists.",
        "hidden_tests": [
            ('assert first_unique_char("swiss") == "w"', None),
            ('assert first_unique_char("aabbcc") == ""', None),
            ('assert first_unique_char("z") == "z"', None),
            ('assert first_unique_char("aabbc") == "c"', None),
        ],
    },
}

# ---------------------------------------------------------
# STEP 2: Sandbox execution helper
# ---------------------------------------------------------
def run_in_sandbox(code_str: str, function_name: str, test_lines: list) -> tuple[bool, str]:
    """
    Executes generated code + hidden assertions in a restricted namespace.
    Returns (passed: bool, error_trace: str). error_trace is "" if passed.
    """
    # Restricted globals: no access to real builtins like open(), __import__, etc.
    safe_builtins = {
        "range": range, "len": len, "list": list, "dict": dict, "set": set,
        "str": str, "int": int, "float": float, "bool": bool, "sorted": sorted,
        "min": min, "max": max, "sum": sum, "abs": abs, "enumerate": enumerate,
        "reversed": reversed, "zip": zip, "map": map, "filter": filter,
        "True": True, "False": False, "None": None,
    }
    sandbox_globals = {"__builtins__": safe_builtins}
    sandbox_locals = {}

    try:
        # Load the generated function definition into the sandbox
        exec(code_str, sandbox_globals, sandbox_locals)

        if function_name not in sandbox_locals:
            return False, f"Function '{function_name}' was not defined by the generated code."

        # Make the function callable from within the assertion strings
        sandbox_globals.update(sandbox_locals)

        # Run each hidden assertion
        for test_line, _ in test_lines:
            exec(test_line, sandbox_globals, sandbox_locals)

        return True, ""

    except Exception:
        return False, traceback.format_exc()


# ---------------------------------------------------------
# Main: Task Selection
# ---------------------------------------------------------
st.subheader("Step 1 · Choose a Task")

task_name = st.selectbox("Algorithm to implement:", options=list(TASKS.keys()))
task = TASKS[task_name]

st.info(f"**Signature:** `{task['signature']}`\n\n{task['description']}")

run_clicked = st.button("🩹 Generate & Self-Heal", type="primary")

# ---------------------------------------------------------
# Core Logic: Generate -> Test -> Repair Loop
# ---------------------------------------------------------
if run_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    else:
        try:
            client = genai.Client(api_key=api_key)

            base_prompt = f"""
            Write a single Python function matching this exact signature:
            {task['signature']}

            Task: {task['description']}

            Rules:
            - Return ONLY the raw Python code for the function. No explanation,
              no markdown fences, no example usage below it.
            - Do not use any imports.
            """

            current_code = None
            passed = False
            attempt_log = []

            for attempt in range(1, MAX_ATTEMPTS + 1):
                with st.status(f"🔧 Attempt {attempt}/{MAX_ATTEMPTS}", expanded=True) as status:

                    if attempt == 1:
                        status.write("Generating initial solution...")
                        prompt = base_prompt
                    else:
                        status.write("Repairing based on previous failure...")
                        prompt = f"""
                        Your previous solution for this task failed testing.

                        Task: {task['description']}
                        Required signature: {task['signature']}

                        Previous code:
                        ```
                        {current_code}
                        ```

                        Error / traceback from running hidden tests:
                        ```
                        {attempt_log[-1]['error']}
                        ```

                        Fix the bug and return ONLY the corrected raw Python code
                        for the function. No explanation, no markdown fences.
                        """

                    response = client.models.generate_content(model=GEN_MODEL, contents=prompt)
                    current_code = response.text.strip()

                    # Strip stray markdown fences if the model adds them anyway
                    if current_code.startswith("```"):
                        current_code = current_code.split("```")[1]
                        if current_code.startswith("python"):
                            current_code = current_code[len("python"):]
                        current_code = current_code.strip()

                    status.write("Running against hidden edge-case tests in sandbox...")
                    passed, error_trace = run_in_sandbox(current_code, task["function_name"], task["hidden_tests"])

                    attempt_log.append({"attempt": attempt, "code": current_code, "passed": passed, "error": error_trace})

                    if passed:
                        status.write("✅ All hidden tests passed!")
                        status.update(label=f"✅ Passed on attempt {attempt}", state="complete")
                        break
                    else:
                        status.write(f"❌ Failed: `{error_trace.strip().splitlines()[-1] if error_trace else 'Unknown error'}`")
                        status.update(label=f"❌ Attempt {attempt} failed", state="error" if attempt == MAX_ATTEMPTS else "complete")

            # -----------------------------------------------------
            # Final result
            # -----------------------------------------------------
            st.markdown("---")
            if passed:
                st.success(f"✅ Self-healed successfully in {attempt_log[-1]['attempt']} attempt(s)")
            else:
                st.error(f"❌ Could not fix the code within {MAX_ATTEMPTS} attempts.")

            st.markdown("### 💻 Final Code")
            st.code(current_code, language="python")

            with st.expander("🔍 Full attempt history"):
                for log in attempt_log:
                    st.markdown(f"**Attempt {log['attempt']}** — {'✅ Passed' if log['passed'] else '❌ Failed'}")
                    st.code(log["code"], language="python")
                    if not log["passed"]:
                        st.code(log["error"], language="text")
                    st.markdown("---")

        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 18 · Self-Healing AI Coder Agent · Built with Streamlit + Gemini")