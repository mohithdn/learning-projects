import streamlit as st
import re

# --- 1. EXPANDED RULE-BASED KNOWLEDGE BASE ---
# Each intent has a list of keywords and a specific response.
FAQ_DATA = {
    "greeting": {
        "keywords": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"],
        "response": "Hello! Welcome to our customer support. How can I help you today?"
    },
    "identity": {
        "keywords": ["who are you", "what is your name", "your name", "about you"],
        "response": "I am a rule-based customer service chatbot built for Project 4. I don't use LLMs, I just match keywords!"
    },
    "pricing": {
        "keywords": ["price", "cost", "how much", "pricing", "subscription", "plan", "fee", "pay"],
        "response": "Our standard plan starts at $9.99/month. We also offer a premium plan at $19.99/month. Would you like to know more?"
    },
    "refund": {
        "keywords": ["refund", "money back", "return", "cancel", "guarantee"],
        "response": "We offer a 30-day money-back guarantee. Please provide your order number to start the refund process."
    },
    "shipping": {
        "keywords": ["shipping", "delivery", "how long", "arrive", "ship", "tracking"],
        "response": "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days. You will receive a tracking number once shipped."
    },
    "contact": {
        "keywords": ["contact", "support", "help", "phone", "email", "talk to human", "representative"],
        "response": "You can reach our human support team at support@example.com or call 1-800-555-0199 between 9 AM and 5 PM EST."
    },
    "hours": {
        "keywords": ["hours", "open", "close", "time", "when are you open"],
        "response": "Our customer service hours are Monday to Friday, 9:00 AM to 5:00 PM EST."
    },
    "product_info": {
        "keywords": ["product", "features", "what do you sell", "service", "software", "app"],
        "response": "We sell a cloud-based productivity suite that helps teams manage tasks, track time, and collaborate seamlessly."
    },
    "complaint": {
        "keywords": ["complaint", "bad", "terrible", "awful", "issue", "problem", "broken"],
        "response": "I'm very sorry to hear you're experiencing issues. Please email support@example.com with your order number, and we will prioritize your case."
    },
    "thanks": {
        "keywords": ["thank", "thanks", "appreciate", "helpful"],
        "response": "You're very welcome! Is there anything else I can help you with today?"
    },
    "goodbye": {
        "keywords": ["bye", "goodbye", "see you", "exit", "quit"],
        "response": "Thank you for chatting with us. Have a wonderful day!"
    }
}

# --- 2. SMART MATCHING & SANITIZATION FUNCTION ---
def get_bot_response(user_input):
    # Sanitization: Remove leading/trailing whitespace, convert to lowercase
    clean_input = user_input.strip().lower()
    
    # Remove punctuation to make matching easier (e.g., "price?" -> "price")
    clean_input_no_punct = re.sub(r'[^\w\s]', '', clean_input)
    
    best_intent = None
    highest_score = 0
    
    # Intent pattern matching with a scoring system
    for intent, data in FAQ_DATA.items():
        score = 0
        for keyword in data["keywords"]:
            # Check if the keyword phrase exists in the cleaned user input
            if keyword in clean_input_no_punct:
                # Give higher priority to longer, more specific keyword matches
                score += len(keyword.split())
                
        if score > highest_score:
            highest_score = score
            best_intent = intent

    # If we found a match, return the corresponding response
    if best_intent:
        return FAQ_DATA[best_intent]["response"]
    
    # --- 3. DYNAMIC GRACEFUL FALLBACK ---
    # If no keywords matched, reply based on what the user asked.
    if len(clean_input_no_punct.split()) > 2:
        # Extract the first few words to acknowledge what they asked
        topic = " ".join(clean_input_no_punct.split()[:4]) + "..."
        return f"I'm a rule-based bot, so I don't have information about '{topic}'. I can currently help with: Pricing, Shipping, Refunds, Hours, Contact Info, or Product Details. What would you like to know?"
    else:
        return "I didn't quite understand that. Could you try rephrasing? You can ask me about our pricing, shipping, refunds, or support hours."

# --- 4. STREAMLIT UI SETUP ---
st.set_page_config(page_title="Customer FAQ Bot", page_icon="🤖")
st.title("🤖 Customer FAQ Chatbot")
st.caption("Project 4: Rule-Based Conversational Chatbot (Procedural Logic)")

# Sidebar to show the user what they can ask
with st.sidebar:
    st.header("💡 Try Asking:")
    st.markdown("""
    - Hello!
    - What is your name?
    - How much does it cost?
    - What is your refund policy?
    - How long does shipping take?
    - How can I contact support?
    - What are your hours?
    - What features do you have?
    """)
    st.divider()
    st.caption("This bot uses deterministic keyword matching, not an LLM.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! Ask me any question about our products or services (e.g., pricing, shipping, refunds, support)."}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Type your question here..."):
    # 1. Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    
    # 2. Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 3. Get bot response using our rule-based function
    response = get_bot_response(prompt)

    # 4. Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
        
    # 5. Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})