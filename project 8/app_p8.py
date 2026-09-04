import streamlit as st
import math
import re
import random


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Sentiment Analyzer Agent",
    page_icon="😊",
    layout="centered"
)


# =========================================================
# TITLE
# =========================================================

st.title("😊 Sentiment Analyzer Agent")

st.caption(
    "A machine-learning sentiment classifier using Naive Bayes"
)


# =========================================================
# TRAINING DATA
# =========================================================

positive_reviews = [
    "I love this product",
    "This product is excellent",
    "Amazing quality and great service",
    "I am very happy with this purchase",
    "The product is fantastic",
    "Really good experience",
    "Excellent customer service",
    "I highly recommend this product",
    "The quality is amazing",
    "Very useful and easy to use",
    "I am satisfied with the product",
    "Wonderful experience",
    "Great product and great quality",
    "This was an excellent purchase",
    "Absolutely loved it",
]

negative_reviews = [
    "I hate this product",
    "This product is terrible",
    "Very bad quality and poor service",
    "I am unhappy with this purchase",
    "The product is horrible",
    "Really bad experience",
    "Terrible customer service",
    "I do not recommend this product",
    "The quality is very poor",
    "Very difficult to use",
    "I am disappointed with the product",
    "Awful experience",
    "Bad product and bad quality",
    "This was a terrible purchase",
    "I absolutely hated it",
]


# =========================================================
# TEXT TOKENIZATION
# =========================================================

def tokenize(text):

    text = text.lower()

    words = re.findall(r"\b[a-z]+\b", text)

    return words


# =========================================================
# TRAIN NAIVE BAYES MODEL
# =========================================================

def train_model():

    vocabulary = set()

    positive_word_counts = {}
    negative_word_counts = {}

    positive_total_words = 0
    negative_total_words = 0

    # ---------------------------------------------
    # Count positive words
    # ---------------------------------------------

    for review in positive_reviews:

        words = tokenize(review)

        for word in words:

            vocabulary.add(word)

            positive_word_counts[word] = (
                positive_word_counts.get(word, 0) + 1
            )

            positive_total_words += 1

    # ---------------------------------------------
    # Count negative words
    # ---------------------------------------------

    for review in negative_reviews:

        words = tokenize(review)

        for word in words:

            vocabulary.add(word)

            negative_word_counts[word] = (
                negative_word_counts.get(word, 0) + 1
            )

            negative_total_words += 1

    return (
        vocabulary,
        positive_word_counts,
        negative_word_counts,
        positive_total_words,
        negative_total_words,
    )


# =========================================================
# TRAIN MODEL
# =========================================================

(
    vocabulary,
    positive_word_counts,
    negative_word_counts,
    positive_total_words,
    negative_total_words,
) = train_model()


# =========================================================
# NAIVE BAYES PREDICTION
# =========================================================

def predict_sentiment(text):

    words = tokenize(text)

    if not words:

        return "Unknown", 0.0

    vocab_size = len(vocabulary)

    # Equal class priors
    positive_log_probability = math.log(0.5)
    negative_log_probability = math.log(0.5)

    for word in words:

        # Laplace smoothing
        positive_probability = (
            positive_word_counts.get(word, 0) + 1
        ) / (
            positive_total_words + vocab_size
        )

        negative_probability = (
            negative_word_counts.get(word, 0) + 1
        ) / (
            negative_total_words + vocab_size
        )

        positive_log_probability += math.log(
            positive_probability
        )

        negative_log_probability += math.log(
            negative_probability
        )

    # Convert log probabilities to comparable values

    max_log = max(
        positive_log_probability,
        negative_log_probability
    )

    positive_score = math.exp(
        positive_log_probability - max_log
    )

    negative_score = math.exp(
        negative_log_probability - max_log
    )

    total = positive_score + negative_score

    positive_confidence = (
        positive_score / total
    )

    negative_confidence = (
        negative_score / total
    )

    if positive_confidence >= negative_confidence:

        return (
            "Positive",
            positive_confidence * 100
        )

    else:

        return (
            "Negative",
            negative_confidence * 100
        )


# =========================================================
# TEST ACCURACY
# =========================================================

test_data = [
    ("I really love this amazing product", "Positive"),
    ("Excellent and wonderful service", "Positive"),
    ("I am very happy with the quality", "Positive"),
    ("This product is fantastic", "Positive"),
    ("I hate this terrible product", "Negative"),
    ("Very poor and bad quality", "Negative"),
    ("I am unhappy with this purchase", "Negative"),
    ("This was a horrible experience", "Negative"),
]


def calculate_accuracy():

    correct = 0

    for review, actual_sentiment in test_data:

        predicted_sentiment, confidence = predict_sentiment(
            review
        )

        if predicted_sentiment == actual_sentiment:

            correct += 1

    accuracy = (
        correct / len(test_data)
    ) * 100

    return accuracy


accuracy = calculate_accuracy()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📊 Model Information")

    st.write(
        f"**Training Reviews:** "
        f"{len(positive_reviews) + len(negative_reviews)}"
    )

    st.write(
        f"**Positive Reviews:** "
        f"{len(positive_reviews)}"
    )

    st.write(
        f"**Negative Reviews:** "
        f"{len(negative_reviews)}"
    )

    st.write(
        f"**Vocabulary Size:** "
        f"{len(vocabulary)} words"
    )

    st.markdown("---")

    st.write("### 🧠 Algorithm")

    st.write("Naive Bayes")

    st.write("### 🔤 Processing")

    st.write("Text Tokenization")

    st.write("### 📈 Evaluation")

    st.write("Train/Test Accuracy")


# =========================================================
# MODEL PERFORMANCE
# =========================================================

st.subheader("📊 Model Performance")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Test Accuracy",
        f"{accuracy:.1f}%"
    )

with col2:

    st.metric(
        "Training Reviews",
        len(positive_reviews) + len(negative_reviews)
    )

with col3:

    st.metric(
        "Vocabulary",
        len(vocabulary)
    )


st.markdown("---")


# =========================================================
# USER INPUT
# =========================================================

st.subheader("✍️ Enter Customer Feedback")

user_text = st.text_area(
    "Write a review:",
    placeholder="Example: I really loved this product!",
    height=130
)


# =========================================================
# ANALYZE BUTTON
# =========================================================

if st.button(
    "🔍 Analyze Sentiment",
    type="primary",
    use_container_width=True
):

    if not user_text.strip():

        st.warning(
            "⚠️ Please enter some customer feedback."
        )

    else:

        sentiment, confidence = predict_sentiment(
            user_text
        )

        # ---------------------------------------------
        # Positive
        # ---------------------------------------------

        if sentiment == "Positive":

            st.success(
                f"😊 Positive\n\n"
                f"Confidence: {confidence:.2f}%"
            )

        # ---------------------------------------------
        # Negative
        # ---------------------------------------------

        elif sentiment == "Negative":

            st.error(
                f"😞 Negative\n\n"
                f"Confidence: {confidence:.2f}%"
            )

        else:

            st.warning(
                "Unable to determine sentiment."
            )

        # ---------------------------------------------
        # Confidence Progress Bar
        # ---------------------------------------------

        st.write("### Confidence")

        st.progress(
            int(confidence)
        )

        st.write(
            f"Model confidence: **{confidence:.2f}%**"
        )


# =========================================================
# ACCURACY SECTION
# =========================================================

st.markdown("---")

st.subheader("📈 Test Set Evaluation")

st.write(
    "The model is tested on reviews that were not used "
    "for the prediction interface."
)

st.metric(
    "Classification Accuracy",
    f"{accuracy:.1f}%"
)


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Project 8 · Sentiment Analyzer Agent · "
    "Naive Bayes Machine Learning"
)