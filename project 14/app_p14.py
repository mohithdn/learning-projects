"""
Project 14: Autonomous Multi-Tool ReAct Agent Loop
---------------------------------------------------------
Goal: A manual ReAct loop (Reason -> Act -> Observe -> repeat) that
chains multiple tool calls in sequence to solve compound queries,
e.g. "Look up BTC price, then tell me my ROI if I bought at $30,000."

Run with:
    python -m streamlit run app_p14.py
"""

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="ReAct Multi-Tool Agent",
    page_icon="🔁",
    layout="centered",
)

st.title("🔁 Autonomous Multi-Tool ReAct Agent")
st.caption("Ask a compound crypto question — the agent will reason, call tools, observe results, and loop until it has your final answer.")

MAX_STEPS = 5

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    st.markdown(
        "**Available tools:**\n"
        "- `get_crypto_price` — mock live price lookup\n"
        "- `calculate_roi` — % return given buy price & current price\n\n"
        f"The agent loops up to **{MAX_STEPS} steps**, chaining tool calls "
        "in sequence (ReAct pattern: Reason → Act → Observe → repeat) until "
        "it produces a final answer with no more tool calls needed."
    )

# ---------------------------------------------------------
# STEP 1: Define local tool functions
# ---------------------------------------------------------

def get_crypto_price(symbol: str) -> dict:
    """Looks up the current mock price of a cryptocurrency.

    Args:
        symbol: The crypto ticker symbol, e.g. 'BTC', 'ETH', 'SOL'.

    Returns:
        A dictionary with the symbol and its current mock USD price.
    """
    mock_prices = {
        "BTC": 68500.00,
        "ETH": 3450.00,
        "SOL": 158.20,
        "DOGE": 0.14,
    }
    symbol = symbol.upper()
    if symbol not in mock_prices:
        return {"error": f"No mock price available for '{symbol}'."}
    return {"symbol": symbol, "price_usd": mock_prices[symbol]}


def calculate_roi(buy_price: float, current_price: float, quantity: float = 1.0) -> dict:
    """Calculates the return on investment (ROI) between a buy price and current price.

    Args:
        buy_price: The price per unit paid at purchase.
        current_price: The current price per unit.
        quantity: The number of units held. Defaults to 1.0.

    Returns:
        A dictionary with profit/loss in dollars and ROI as a percentage.
    """
    invested = buy_price * quantity
    current_value = current_price * quantity
    profit = current_value - invested
    roi_percent = (profit / invested) * 100 if invested != 0 else 0

    return {
        "invested_usd": round(invested, 2),
        "current_value_usd": round(current_value, 2),
        "profit_usd": round(profit, 2),
        "roi_percent": round(roi_percent, 2),
    }


AVAILABLE_FUNCTIONS = {
    "get_crypto_price": get_crypto_price,
    "calculate_roi": calculate_roi,
}

TOOLS = [get_crypto_price, calculate_roi]

# ---------------------------------------------------------
# Main Input
# ---------------------------------------------------------
query = st.text_area(
    "Ask a compound crypto question:",
    placeholder="e.g. I bought 2 BTC at $30,000 each. What's my ROI at today's price?",
    height=100,
)

run_clicked = st.button("Run ReAct Agent", type="primary")

# ---------------------------------------------------------
# Core Logic: Manual ReAct Loop
# ---------------------------------------------------------
if run_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif not query.strip():
        st.warning("⚠️ Please type a question first.")
    else:
        try:
            client = genai.Client(api_key=api_key)

            config = types.GenerateContentConfig(tools=TOOLS)

            # Conversation history built manually so we control the loop ourselves
            contents = [
                types.Content(role="user", parts=[types.Part(text=query)])
            ]

            final_answer = None

            with st.status("🤖 Agent reasoning loop starting...", expanded=True) as status:
                for step in range(1, MAX_STEPS + 1):
                    status.write(f"**Step {step}** — sending conversation state to Gemini...")

                    response = client.models.generate_content(
                        model="gemini-3.7-flash",
                        contents=contents,
                        config=config,
                    )

                    candidate = response.candidates[0]
                    parts = candidate.content.parts

                    # Collect any function calls Gemini wants to make this turn
                    function_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]

                    if not function_calls:
                        # No more tool calls -> Gemini has produced its final answer
                        final_answer = response.text
                        status.write(f"**Step {step}** — no further tool calls. Final answer ready.")
                        break

                    # Append the model's turn (including its function call requests) to history
                    contents.append(candidate.content)

                    # STEP 2: Execute each requested function locally, log it, and pack the result back in
                    response_parts = []
                    for fn_call in function_calls:
                        fn_name = fn_call.name
                        fn_args = dict(fn_call.args)

                        status.write(f"🔧 Calling `{fn_name}({fn_args})`")

                        if fn_name in AVAILABLE_FUNCTIONS:
                            result = AVAILABLE_FUNCTIONS[fn_name](**fn_args)
                        else:
                            result = {"error": f"Unknown function '{fn_name}'"}

                        status.write(f"👀 Observed result: `{result}`")

                        # Pack the function's result into a tool-response Part
                        response_parts.append(
                            types.Part.from_function_response(
                                name=fn_name,
                                response={"result": result},
                            )
                        )

                    # Add the tool results back into the conversation as the next turn
                    contents.append(types.Content(role="tool", parts=response_parts))

                else:
                    # Loop exhausted MAX_STEPS without a final answer
                    status.write(f"⚠️ Reached max steps ({MAX_STEPS}) without a final answer.")
                    final_answer = "The agent could not reach a final answer within the step limit."

                status.update(label="✅ Agent loop complete", state="complete")

            st.markdown("### 🧠 Final Answer")
            st.write(final_answer)

        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 14 · Autonomous Multi-Tool ReAct Agent Loop · Built with Streamlit + Gemini")