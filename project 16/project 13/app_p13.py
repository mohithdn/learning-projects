"""
Project 13: Autonomous Function Calling Agent
----------------------------------------------------
Goal: Let Gemini autonomously decide WHEN and WITH WHAT ARGUMENTS
to call local Python functions (Loan EMI calculator, Stock metric
lookup), then execute them deterministically and return real results.

Run with:
    python -m streamlit run app_p13.py
"""

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Function Calling Agent",
    page_icon="🛠️",
    layout="centered",
)

st.title("🛠️ Autonomous Function Calling Agent")
st.caption("Ask a finance question in plain English — Gemini decides which tool to call and with what numbers.")

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    st.markdown(
        "**Available tools:**\n"
        "- `calculate_loan_emi` — monthly EMI for a loan\n"
        "- `get_stock_metric` — mock stock price/PE lookup\n\n"
        "Gemini reads your question, decides which function (if any) "
        "applies, extracts the right arguments, and this app runs the "
        "real Python function locally — the math is never guessed by the model."
    )

# ---------------------------------------------------------
# STEP 1: Define local Python functions
# Google-style docstrings + type hints are what the SDK reads
# to auto-generate the function-calling schema for Gemini.
# ---------------------------------------------------------

def calculate_loan_emi(principal: float, annual_rate_percent: float, tenure_years: int) -> dict:
    """Calculates the monthly EMI (Equated Monthly Installment) for a loan.

    Args:
        principal: The loan amount borrowed, in currency units.
        annual_rate_percent: The annual interest rate as a percentage (e.g. 8.5 for 8.5%).
        tenure_years: The loan repayment duration in years.

    Returns:
        A dictionary containing the monthly EMI, total payment, and total interest.
    """
    monthly_rate = (annual_rate_percent / 100) / 12
    months = tenure_years * 12

    if monthly_rate == 0:
        emi = principal / months
    else:
        emi = principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)

    total_payment = emi * months
    total_interest = total_payment - principal

    return {
        "monthly_emi": round(emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "months": months,
    }


def get_stock_metric(ticker: str, metric: str) -> dict:
    """Looks up a financial metric for a given stock ticker symbol.

    Args:
        ticker: The stock ticker symbol, e.g. 'AAPL', 'GOOGL', 'TSLA'.
        metric: The metric to retrieve. One of: 'price', 'pe_ratio', 'market_cap'.

    Returns:
        A dictionary containing the ticker, the requested metric, and its mock value.
    """
    # NOTE: This is a MOCK dataset for demo purposes (no live market data).
    mock_data = {
        "AAPL": {"price": 227.50, "pe_ratio": 34.2, "market_cap": "3.4T"},
        "GOOGL": {"price": 178.20, "pe_ratio": 27.8, "market_cap": "2.2T"},
        "TSLA": {"price": 265.10, "pe_ratio": 68.5, "market_cap": "850B"},
        "MSFT": {"price": 415.30, "pe_ratio": 36.1, "market_cap": "3.1T"},
        "AMZN": {"price": 186.90, "pe_ratio": 42.7, "market_cap": "1.9T"},
    }

    ticker = ticker.upper()
    if ticker not in mock_data:
        return {"error": f"No mock data available for ticker '{ticker}'."}

    if metric not in mock_data[ticker]:
        return {"error": f"Unknown metric '{metric}'. Choose from: price, pe_ratio, market_cap."}

    return {"ticker": ticker, "metric": metric, "value": mock_data[ticker][metric]}


# Map function names (as strings) to the actual callables, for dispatch
AVAILABLE_FUNCTIONS = {
    "calculate_loan_emi": calculate_loan_emi,
    "get_stock_metric": get_stock_metric,
}

# ---------------------------------------------------------
# Main Input
# ---------------------------------------------------------
query = st.text_area(
    "Ask a finance question:",
    placeholder="e.g. What's the monthly EMI for a 500000 loan at 8.5% over 10 years?",
    height=100,
)

run_clicked = st.button("Run Agent", type="primary")

# ---------------------------------------------------------
# Core Logic: Autonomous Function Calling
# ---------------------------------------------------------
if run_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif not query.strip():
        st.warning("⚠️ Please type a question first.")
    else:
        try:
            client = genai.Client(api_key=api_key)

            # STEP 2: Register the Python functions as tools.
            # The SDK automatically builds the schema from type hints + docstrings.
            config = types.GenerateContentConfig(
                tools=[calculate_loan_emi, get_stock_metric],
            )

            with st.spinner("Gemini is deciding which tool to use..."):
                response = client.models.generate_content(
                    model="gemini-3.7-flash",
                    contents=query,
                    config=config,
                )

            # ---------------------------------------------
            # STEP 3: Inspect whether Gemini triggered a function call
            # (Using automatic function calling via the SDK's client
            # already executes it — but we also show the trace manually
            # for transparency using the low-level path below.)
            # ---------------------------------------------
            st.success("✅ Agent finished")
            st.markdown("### 🧠 Final Answer")
            st.write(response.text)

            # Show which function call(s) Gemini triggered, if traceable
            with st.expander("🔍 Function call trace"):
                found_call = False
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if getattr(part, "function_call", None):
                            found_call = True
                            fn_call = part.function_call
                            st.markdown(f"**Function called:** `{fn_call.name}`")
                            st.json(dict(fn_call.args))

                            # Manually dispatch locally as a deterministic double-check
                            if fn_call.name in AVAILABLE_FUNCTIONS:
                                result = AVAILABLE_FUNCTIONS[fn_call.name](**fn_call.args)
                                st.markdown("**Local execution result:**")
                                st.json(result)

                if not found_call:
                    st.info("No explicit function call detected in the trace (the SDK may have auto-executed it inline).")

        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 13 · Autonomous Function Calling Agent · Built with Streamlit + Gemini")