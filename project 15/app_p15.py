"""
Project 15: Visual AI Vision Inspector & OCR Agent
--------------------------------------------------------
Goal: Inspect camera-captured or uploaded images (receipts, bills,
documents), extract itemized line data via OCR, and render it as
a clean structured table — no manual data entry.

Run with:
    python -m streamlit run app_p15.py
"""

# Force UTF-8 so emoji/special characters in prompts and responses never
# crash on Windows terminals using a legacy (non-UTF-8) codepage.
import sys
import io
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import json

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Vision Inspector & OCR Agent",
    page_icon="🧾",
    layout="centered",
)

st.title("🧾 Visual AI Vision Inspector & OCR Agent")
st.caption("Snap a photo or upload a receipt/bill — Gemini reads it and extracts a clean itemized table.")

GEN_MODEL = "gemini-3.7-flash"

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    st.markdown(
        "**How it works:**\n"
        "1️⃣ Capture or upload an image\n"
        "2️⃣ Image bytes sent directly to Gemini (multimodal)\n"
        "3️⃣ Gemini returns strict JSON line items\n"
        "4️⃣ App renders it as a markdown table + totals"
    )

# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------
if "receipt_data" not in st.session_state:
    st.session_state.receipt_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------
# STEP 1: Image Input — camera OR file upload
# ---------------------------------------------------------
st.subheader("Step 1 · Capture or Upload")

input_mode = st.radio("Image source:", options=["📷 Camera", "📁 Upload File"], horizontal=True)

image_bytes = None
image_mime = "image/jpeg"

if input_mode == "📷 Camera":
    camera_image = st.camera_input("Take a photo of the receipt")
    if camera_image is not None:
        image_bytes = camera_image.getvalue()
        image_mime = "image/jpeg"
else:
    uploaded_image = st.file_uploader("Upload a receipt/bill image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_image is not None:
        image_bytes = uploaded_image.getvalue()
        ext = uploaded_image.name.rsplit(".", 1)[-1].lower()
        image_mime = "image/png" if ext == "png" else ("image/webp" if ext == "webp" else "image/jpeg")

if image_bytes:
    st.image(image_bytes, caption="Captured/Uploaded Image", use_container_width=True)

st.markdown("---")

extract_clicked = st.button("🔍 Extract Table", type="primary")

# ---------------------------------------------------------
# STEP 2: OCR + Structured Extraction
# ---------------------------------------------------------
if extract_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif image_bytes is None:
        st.warning("⚠️ Please capture or upload an image first.")
    else:
        try:
            with st.spinner("Reading the image and extracting line items..."):
                client = genai.Client(api_key=api_key)

                image_part = types.Part.from_bytes(data=image_bytes, mime_type=image_mime)

                extraction_prompt = """
                You are an OCR and receipt-parsing assistant. Carefully read the
                attached receipt/bill image and extract its contents.

                Return ONLY valid JSON, no markdown fences, no preamble, in this
                exact schema:
                {
                  "merchant_name": "string or null if not visible",
                  "date": "string or null if not visible",
                  "items": [
                    {"description": "string", "quantity": number, "unit_price": number, "line_total": number}
                  ],
                  "subtotal": number or null,
                  "tax": number or null,
                  "total": number or null
                }

                Rules:
                - If a field is not visible/legible in the image, use null — never guess.
                - quantity defaults to 1 if not explicitly shown.
                - Numbers must be plain numbers (no currency symbols, no commas).
                """

                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                )

                response = client.models.generate_content(
                    model=GEN_MODEL,
                    contents=[image_part, extraction_prompt],
                    config=config,
                )

                receipt_data = json.loads(response.text)

            st.success("✅ Extraction complete")

            # -----------------------------------------------------
            # STEP 3: Display merchant/date info
            # -----------------------------------------------------
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Merchant", receipt_data.get("merchant_name") or "Not detected")
            with col2:
                st.metric("Date", receipt_data.get("date") or "Not detected")

            # -----------------------------------------------------
            # STEP 4: Render itemized table (markdown table via st.table)
            # -----------------------------------------------------
            items = receipt_data.get("items", [])
            if items:
                st.markdown("### 🧾 Itemized Bill")
                table_rows = []
                for item in items:
                    table_rows.append({
                        "Description": item.get("description", ""),
                        "Qty": item.get("quantity", ""),
                        "Unit Price": item.get("unit_price", ""),
                        "Line Total": item.get("line_total", ""),
                    })
                st.table(table_rows)
            else:
                st.info("No line items were detected in the image.")

            # -----------------------------------------------------
            # STEP 5: Totals
            # -----------------------------------------------------
            st.markdown("### 💰 Totals")
            t1, t2, t3 = st.columns(3)
            t1.metric("Subtotal", receipt_data.get("subtotal") if receipt_data.get("subtotal") is not None else "N/A")
            t2.metric("Tax", receipt_data.get("tax") if receipt_data.get("tax") is not None else "N/A")
            t3.metric("Total", receipt_data.get("total") if receipt_data.get("total") is not None else "N/A")

            with st.expander("🧾 Raw extracted JSON"):
                st.json(receipt_data)

            # Save for the Q&A assistant below
            st.session_state.receipt_data = receipt_data
            st.session_state.chat_history = []  # reset chat whenever a new bill is extracted

            # Offer a markdown-table download for easy pasting elsewhere
            if items:
                md_lines = ["| Description | Qty | Unit Price | Line Total |", "|---|---|---|---|"]
                for item in items:
                    md_lines.append(
                        f"| {item.get('description','')} | {item.get('quantity','')} | "
                        f"{item.get('unit_price','')} | {item.get('line_total','')} |"
                    )
                md_table = "\n".join(md_lines)
                st.download_button(
                    "⬇️ Download as Markdown Table",
                    data=md_table,
                    file_name="receipt_items.md",
                    mime="text/markdown",
                )

        except json.JSONDecodeError:
            st.error("❌ The model did not return valid JSON. Try again — retake the photo with better lighting/focus if it keeps failing.")
        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# STEP 6: Ask-the-Bill Q&A Assistant
# (only appears once a receipt has been extracted)
# ---------------------------------------------------------
if st.session_state.receipt_data:
    st.markdown("---")
    st.subheader("💬 Ask About This Bill")
    st.caption("Ask things like \"How much did I spend on drinks?\" or \"What's the tax amount?\" — answers are grounded strictly in the extracted data above.")

    # Render prior chat turns
    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    bill_question = st.chat_input("Ask a question about this bill...")

    if bill_question:
        if not api_key:
            st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
        else:
            # Show the user's question immediately
            st.session_state.chat_history.append({"role": "user", "content": bill_question})
            with st.chat_message("user"):
                st.markdown(bill_question)

            with st.chat_message("assistant"):
                with st.spinner("Checking the bill..."):
                    try:
                        client = genai.Client(api_key=api_key)

                        # Ground the answer strictly in the extracted JSON —
                        # same hallucination-prevention pattern as Project 16.
                        qa_prompt = f"""
                        You are a helpful assistant that answers questions about a
                        SINGLE receipt/bill. Answer using ONLY the data below. Do
                        not guess or use outside knowledge about prices.

                        If the answer cannot be determined from this data, say so
                        clearly instead of guessing.

                        Receipt data (JSON):
                        {json.dumps(st.session_state.receipt_data, indent=2)}

                        Question: {bill_question}
                        """

                        qa_response = client.models.generate_content(
                            model=GEN_MODEL,
                            contents=qa_prompt,
                        )
                        answer_text = qa_response.text
                        st.markdown(answer_text)
                    except Exception as e:
                        answer_text = f"❌ Something went wrong: {e}"
                        st.error(answer_text)

            st.session_state.chat_history.append({"role": "assistant", "content": answer_text})

    if st.session_state.chat_history and st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 15 · Visual AI Vision Inspector & OCR Agent · Built with Streamlit + Gemini")