import streamlit as st

st.set_page_config(
    page_title="Prediction Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Prediction Agent")
st.write("Train a prediction model from scratch using Gradient Descent")

# DATA
hours = [1, 2, 3, 4, 5]
scores = [52, 58, 62, 71, 78]


# PREDICTION
def predict(x, m, c):
    return m * x + c


# LOSS
def calculate_loss(m, c):
    total = 0

    for x, real in zip(hours, scores):
        prediction = predict(x, m, c)
        error = prediction - real
        total += error ** 2

    return total / len(hours)


# GRADIENTS
def calculate_gradients(m, c):
    grad_m = 0
    grad_c = 0

    n = len(hours)

    for x, real in zip(hours, scores):
        prediction = predict(x, m, c)
        error = prediction - real

        grad_m += 2 * error * x
        grad_c += 2 * error

    return grad_m / n, grad_c / n


# TRAIN MODEL
def train_model(learning_rate, steps):

    m = 0
    c = 0

    history = []

    for step in range(steps):

        gm, gc = calculate_gradients(m, c)

        m = m - learning_rate * gm
        c = c - learning_rate * gc

        history.append(calculate_loss(m, c))

    return m, c, history


# SIDEBAR
st.sidebar.header("⚙️ Model Settings")

learning_rate = st.sidebar.number_input(
    "Learning Rate",
    min_value=0.0001,
    max_value=0.1,
    value=0.01,
    step=0.001
)

steps = st.sidebar.number_input(
    "Training Steps",
    min_value=100,
    max_value=10000,
    value=1000,
    step=100
)


# TABS
tab1, tab2, tab3 = st.tabs([
    "📊 Data",
    "🧠 Train Model",
    "🔮 Predict"
])


# DATA TAB
with tab1:

    st.header("📊 Training Data")

    st.write("Study Hours → Exam Score")

    for h, s in zip(hours, scores):
        st.write(f"📚 {h} hours → 🎯 {s} marks")

    st.info(
        "The model learns the relationship between study hours and exam scores."
    )


# TRAIN TAB
with tab2:

    st.header("🧠 Train Prediction Agent")

    if st.button("🚀 Train Model", type="primary"):

        m, c, history = train_model(
            learning_rate,
            int(steps)
        )

        st.session_state.m = m
        st.session_state.c = c
        st.session_state.history = history

        st.success("🎉 Model trained successfully!")

    if "m" in st.session_state:

        m = st.session_state.m
        c = st.session_state.c
        history = st.session_state.history

        col1, col2, col3 = st.columns(3)

        col1.metric("Slope (m)", f"{m:.2f}")
        col2.metric("Intercept (c)", f"{c:.2f}")
        col3.metric("Final Loss", f"{history[-1]:.2f}")

        st.subheader("📐 Learned Equation")

        st.code(
            f"Score = {m:.2f} × Hours + {c:.2f}"
        )

        st.subheader("📉 Training Progress")

        # Show selected training steps
        for i in range(0, len(history), max(1, len(history) // 10)):
            st.write(
                f"Step {i}: Loss = {history[i]:.2f}"
            )

        st.success(
            "The model reduced its loss using Gradient Descent."
        )


# PREDICT TAB
with tab3:

    st.header("🔮 Predict Exam Score")

    if "m" not in st.session_state:

        st.warning(
            "⚠️ Please train the model first."
        )

    else:

        m = st.session_state.m
        c = st.session_state.c

        study_hours = st.number_input(
            "Enter Study Hours",
            min_value=0.0,
            max_value=100.0,
            value=6.0,
            step=0.5
        )

        if st.button(
            "🔮 Predict Score",
            type="primary"
        ):

            result = predict(
                study_hours,
                m,
                c
            )

            st.success(
                f"🎯 Predicted Exam Score: {result:.1f}"
            )

            st.metric(
                "Predicted Score",
                f"{result:.1f}"
            )

        st.divider()

        st.subheader("Try Examples")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("📚 2 Hours")
            st.write(f"{predict(2, m, c):.1f} marks")

        with col2:
            st.write("📚 5 Hours")
            st.write(f"{predict(5, m, c):.1f} marks")

        with col3:
            st.write("📚 8 Hours")
            st.write(f"{predict(8, m, c):.1f} marks")


st.divider()

st.caption(
    "Month 6 Prediction Agent • Gradient Descent • Built from Scratch"
)