"""
Project 19: Autonomous Customer Support & Ticket Routing Agent
----------------------------------------------------------------
Goal: Ingest a raw customer email, have Gemini classify it into
strict JSON (department, priority, sentiment, SLA), route it
conditionally, track the SLA deadline, and auto-draft an
empathetic reply.

Run with:
    python -m streamlit run app_p19.py
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Support Ticket Router",
    page_icon="🎫",
    layout="centered",
)

st.title("🎫 Autonomous Support & Ticket Routing Agent")
st.caption("Paste a customer email — Gemini classifies it, routes it to the right department, tracks the SLA, and drafts a reply.")

GEN_MODEL = "gemini-3.7-flash"

# SLA policy: hours allowed to respond, per priority level
SLA_HOURS = {
    "Critical": 2,
    "High": 8,
    "Medium": 24,
    "Low": 72,
}

# Where each department "receives" tickets, for the optional real-email path
DEPARTMENT_EMAILS = {
    "Billing": "billing@yourcompany.example",
    "Technical": "techsupport@yourcompany.example",
    "Shipping": "shipping@yourcompany.example",
    "Account": "accounts@yourcompany.example",
    "General": "support@yourcompany.example",
}

INBOX_FILE = "department_inbox.json"

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    st.markdown(
        "**Departments:** Billing, Technical, Shipping, Account, General\n\n"
        "**Priority → SLA:**\n"
        + "\n".join(f"- {p}: {h}h" for p, h in SLA_HOURS.items())
    )
    st.markdown("---")
    st.subheader("📤 Delivery Method")
    delivery_mode = st.radio(
        "How should tickets be sent?",
        options=["Local inbox (simulated)", "Real email (SMTP)"],
        help="Local inbox writes to a JSON file on disk — no setup needed. Real email actually sends via your SMTP provider.",
    )

    smtp_config = {}
    if delivery_mode == "Real email (SMTP)":
        st.caption("⚠️ Uses your real email credentials. For Gmail, use an App Password, not your normal password.")
        smtp_config["host"] = st.text_input("SMTP host", placeholder="smtp.gmail.com")
        smtp_config["port"] = st.number_input("SMTP port", value=587)
        smtp_config["sender_email"] = st.text_input("Sender email")
        smtp_config["sender_password"] = st.text_input("Sender app password", type="password")

# ---------------------------------------------------------
# STEP 1: Strict JSON classification schema (as a prompt instruction)
# ---------------------------------------------------------
CLASSIFICATION_SCHEMA = """
Return ONLY valid JSON, no markdown fences, no preamble, in this exact schema:
{
  "department": "Billing" | "Technical" | "Shipping" | "Account" | "General",
  "priority": "Critical" | "High" | "Medium" | "Low",
  "sentiment": "Positive" | "Neutral" | "Negative" | "Angry",
  "summary": "one sentence summary of the customer's issue",
  "reasoning": "one sentence explaining why this priority/department was chosen"
}

Classification guidance:
- "Critical": unauthorized charges, security issues, complete service outage, legal threats
- "High": account access issues, significant financial impact, repeated unresolved issues
- "Medium": standard bugs, shipping delays, billing questions
- "Low": general questions, feature requests, feedback
"""

# ---------------------------------------------------------
# Delivery helpers
# ---------------------------------------------------------
def send_to_local_inbox(ticket: dict, email_text: str, draft_reply: str, deadline: datetime) -> None:
    """Appends the ticket to a per-department JSON inbox file on disk."""
    inbox = {}
    if os.path.exists(INBOX_FILE):
        with open(INBOX_FILE, "r", encoding="utf-8") as f:
            try:
                inbox = json.load(f)
            except json.JSONDecodeError:
                inbox = {}

    department = ticket.get("department", "General")
    inbox.setdefault(department, [])

    inbox[department].append({
        "received_at": datetime.now().isoformat(timespec="seconds"),
        "sla_deadline": deadline.isoformat(timespec="seconds"),
        "priority": ticket.get("priority"),
        "sentiment": ticket.get("sentiment"),
        "summary": ticket.get("summary"),
        "original_email": email_text,
        "draft_reply": draft_reply,
    })

    with open(INBOX_FILE, "w", encoding="utf-8") as f:
        json.dump(inbox, f, indent=2)


def load_local_inbox() -> dict:
    if not os.path.exists(INBOX_FILE):
        return {}
    with open(INBOX_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def send_real_email(smtp_config: dict, to_address: str, subject: str, body: str) -> None:
    """Sends an actual email via SMTP using the provided credentials."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_config["sender_email"]
    msg["To"] = to_address

    with smtplib.SMTP(smtp_config["host"], int(smtp_config["port"])) as server:
        server.starttls()
        server.login(smtp_config["sender_email"], smtp_config["sender_password"])
        server.send_message(msg)


# ---------------------------------------------------------
# Main Input
# ---------------------------------------------------------
st.subheader("Step 1 · Paste the Customer Email")

email_text = st.text_area(
    "Customer email:",
    height=180,
    placeholder="e.g. I was charged twice for my subscription this month and no one has responded to my last two emails. This is unacceptable...",
)

process_clicked = st.button("🚦 Classify & Route Ticket", type="primary")

# ---------------------------------------------------------
# Core Logic
# ---------------------------------------------------------
if process_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif not email_text.strip():
        st.warning("⚠️ Please paste a customer email first.")
    else:
        try:
            client = genai.Client(api_key=api_key)

            # -----------------------------------------------------
            # STEP 2: Classify the email into strict JSON
            # -----------------------------------------------------
            with st.spinner("Classifying ticket..."):
                classification_prompt = f"""
                Classify the following customer support email.

                {CLASSIFICATION_SCHEMA}

                Customer email:
                \"\"\"
                {email_text}
                \"\"\"
                """

                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                )

                classify_response = client.models.generate_content(
                    model=GEN_MODEL,
                    contents=classification_prompt,
                    config=config,
                )

                ticket = json.loads(classify_response.text)

            # -----------------------------------------------------
            # STEP 3: Conditional routing + SLA calculation
            # -----------------------------------------------------
            priority = ticket.get("priority", "Medium")
            department = ticket.get("department", "General")
            sla_hours = SLA_HOURS.get(priority, 24)
            deadline = datetime.now() + timedelta(hours=sla_hours)

            # -----------------------------------------------------
            # Display the classification
            # -----------------------------------------------------
            st.success("✅ Ticket classified")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Department", department)
            with col2:
                priority_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
                st.metric("Priority", f"{priority_color.get(priority, '')} {priority}")
            with col3:
                st.metric("Sentiment", ticket.get("sentiment", "N/A"))

            st.markdown("### 📋 Ticket Summary")
            st.write(ticket.get("summary", ""))
            st.caption(f"Reasoning: {ticket.get('reasoning', '')}")

            st.markdown("### ⏱️ SLA")
            st.warning(f"Response due by **{deadline.strftime('%A, %d %B %Y — %I:%M %p')}** ({sla_hours}h SLA for {priority} priority)")

            # -----------------------------------------------------
            # STEP 4: Conditional routing logic
            # (in a real system, this is where you'd push to a queue,
            #  Slack channel, or ticketing API based on department)
            # -----------------------------------------------------
            with st.expander("🔀 Routing decision"):
                st.write(f"Ticket routed to: **{department} team queue**")
                if priority == "Critical":
                    st.error("🚨 Critical priority — this would trigger an immediate on-call page in production.")
                elif priority == "High":
                    st.warning("⚠️ High priority — flagged for same-shift handling.")

            # -----------------------------------------------------
            # STEP 5: Auto-draft an empathetic reply
            # -----------------------------------------------------
            with st.spinner("Drafting reply..."):
                draft_prompt = f"""
                You are a customer support agent for the {department} department.
                Write a warm, empathetic, professional reply to the customer below.
                Acknowledge their specific issue, avoid generic corporate language,
                and if it involves a billing/refund issue, state that it is being
                escalated and give a realistic next step. Keep it under 150 words.
                Do not invent specific transaction numbers or dates not mentioned
                by the customer.

                Customer email:
                \"\"\"
                {email_text}
                \"\"\"

                Ticket context: priority={priority}, sentiment={ticket.get('sentiment')}, summary={ticket.get('summary')}
                """

                draft_response = client.models.generate_content(
                    model=GEN_MODEL,
                    contents=draft_prompt,
                )

            st.markdown("### ✉️ Draft Reply")
            draft_edited = st.text_area("Editable draft:", value=draft_response.text, height=200, key="draft_edit_area")

            with st.expander("🧾 Raw classification JSON"):
                st.json(ticket)

            # Persist everything needed for the Send step across reruns
            st.session_state.pending_ticket = ticket
            st.session_state.pending_email_text = email_text
            st.session_state.pending_draft = draft_response.text
            st.session_state.pending_deadline = deadline.isoformat()

        except json.JSONDecodeError:
            st.error("❌ The model did not return valid JSON. Try again — occasionally the model adds stray text despite instructions.")
        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# Step 6: Send the ticket to the routed department
# (uses whatever was last classified, stored in session_state)
# ---------------------------------------------------------
if "pending_ticket" in st.session_state:
    st.markdown("---")
    st.subheader("Step 3 · Deliver the Ticket")

    ticket = st.session_state.pending_ticket
    department = ticket.get("department", "General")
    st.write(f"Ready to send to: **{department}** ({delivery_mode})")

    send_clicked = st.button("📨 Send to Department", type="primary")

    if send_clicked:
        deadline = datetime.fromisoformat(st.session_state.pending_deadline)
        draft_to_send = st.session_state.get("draft_edit_area", st.session_state.pending_draft)

        try:
            if delivery_mode == "Local inbox (simulated)":
                send_to_local_inbox(
                    ticket=ticket,
                    email_text=st.session_state.pending_email_text,
                    draft_reply=draft_to_send,
                    deadline=deadline,
                )
                st.success(f"✅ Ticket delivered to the **{department}** local inbox (`{INBOX_FILE}`).")

            else:  # Real email (SMTP)
                required = ["host", "sender_email", "sender_password"]
                if not all(smtp_config.get(k) for k in required):
                    st.error("⚠️ Please fill in all SMTP fields in the sidebar first.")
                else:
                    to_address = DEPARTMENT_EMAILS.get(department, DEPARTMENT_EMAILS["General"])
                    subject = f"[{ticket.get('priority')}] New {department} Ticket — {ticket.get('summary', '')[:60]}"
                    body = (
                        f"Priority: {ticket.get('priority')}\n"
                        f"Sentiment: {ticket.get('sentiment')}\n"
                        f"SLA Deadline: {deadline.strftime('%A, %d %B %Y — %I:%M %p')}\n\n"
                        f"Summary: {ticket.get('summary')}\n\n"
                        f"--- Original Customer Email ---\n{st.session_state.pending_email_text}\n\n"
                        f"--- Suggested Reply ---\n{draft_to_send}"
                    )
                    send_real_email(smtp_config, to_address, subject, body)
                    st.success(f"✅ Email sent to **{to_address}**.")

            # Clear pending state so the button doesn't accidentally re-send on rerun
            del st.session_state.pending_ticket

        except Exception as e:
            st.error(f"❌ Failed to send: {e}")

# ---------------------------------------------------------
# Department Inbox Viewer (local mode only)
# ---------------------------------------------------------
st.markdown("---")
with st.expander("📥 View Local Department Inboxes"):
    inbox = load_local_inbox()
    if not inbox:
        st.info("No tickets delivered to the local inbox yet.")
    else:
        dept_filter = st.selectbox("Department", options=list(inbox.keys()))
        for ticket_entry in reversed(inbox.get(dept_filter, [])):
            st.markdown(f"**{ticket_entry['priority']} · Received {ticket_entry['received_at']}**")
            st.write(ticket_entry["summary"])
            st.caption(f"SLA deadline: {ticket_entry['sla_deadline']}")
            with st.popover("View full ticket"):
                st.write("**Original email:**")
                st.write(ticket_entry["original_email"])
                st.write("**Draft reply sent:**")
                st.write(ticket_entry["draft_reply"])
            st.markdown("---")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 19 · Autonomous Customer Support & Ticket Routing Agent · Built with Streamlit + Gemini")