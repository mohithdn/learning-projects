"""
Project 7: Smart Recommender Agent (South Indian Cinema Edition)
--------------------------------------------------------------------
Goal: Recommend catalog items using pure mathematical vector similarity
(no LLM needed) — establishing how modern AI represents semantic
meaning as numbers, and how similarity search actually works under
the hood (this is the same core math behind embeddings-based RAG,
like Project 16).

Catalog: 40 well-known Telugu, Kannada, and Tamil films, each
represented as a genre-strength vector.

Run with:
    python -m streamlit run app_p7.py
"""

import numpy as np
import streamlit as st

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Smart Recommender Agent",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 Smart Recommender Agent")
st.caption("Pick a Telugu, Kannada, or Tamil film — the agent ranks the rest of the catalog by mathematical similarity, not an LLM guess.")

# ---------------------------------------------------------
# STEP 1: Represent catalog items as vectors
# Each film is a point in "genre space" — a vector of how strongly
# it fits each genre, on a 0–5 scale. This is a simplified,
# human-readable stand-in for what a real embedding model produces.
# Genre strengths below are approximate, illustrative ratings for
# demo purposes, not official classifications.
# ---------------------------------------------------------
GENRES = ["Action", "Comedy", "Romance", "Thriller", "Drama", "Horror"]

# Each entry: title -> {"language": ..., "vector": [Action, Comedy, Romance, Thriller, Drama, Horror]}
CATALOG = {
    # --- TELUGU ---
    "Baahubali: The Beginning": {"language": "Telugu", "vector": [5, 0, 2, 2, 3, 0]},
    "RRR":                      {"language": "Telugu", "vector": [5, 1, 1, 3, 3, 0]},
    "Pushpa: The Rise":         {"language": "Telugu", "vector": [5, 1, 2, 3, 2, 0]},
    "Arjun Reddy":              {"language": "Telugu", "vector": [2, 0, 4, 2, 5, 0]},
    "Eega":                     {"language": "Telugu", "vector": [3, 3, 3, 2, 2, 0]},
    "Jersey":                   {"language": "Telugu", "vector": [1, 1, 2, 1, 5, 0]},
    "Ala Vaikunthapurramuloo":  {"language": "Telugu", "vector": [3, 4, 3, 1, 3, 0]},
    "Sye":                      {"language": "Telugu", "vector": [4, 2, 1, 2, 2, 0]},
    "Sita Ramam":               {"language": "Telugu", "vector": [1, 1, 5, 1, 4, 0]},
    "HIT: The First Case":      {"language": "Telugu", "vector": [2, 0, 0, 5, 3, 0]},
    "Agent Sai Srinivasa Athreya":{"language": "Telugu","vector": [1, 4, 0, 4, 2, 0]},
    "Anji":                     {"language": "Telugu", "vector": [4, 1, 1, 3, 2, 2]},
    "Arundhati":                {"language": "Telugu", "vector": [3, 0, 1, 4, 3, 5]},
    "Magadheera":               {"language": "Telugu", "vector": [5, 1, 4, 2, 3, 0]},
    "Mathu Vadalara":           {"language": "Telugu", "vector": [1, 5, 0, 4, 1, 0]},

    # --- KANNADA ---
    "KGF: Chapter 1":           {"language": "Kannada", "vector": [5, 0, 1, 3, 3, 0]},
    "KGF: Chapter 2":           {"language": "Kannada", "vector": [5, 0, 1, 4, 3, 0]},
    "Kantara":                  {"language": "Kannada", "vector": [4, 0, 1, 4, 3, 2]},
    "Ugramm":                   {"language": "Kannada", "vector": [4, 0, 0, 4, 2, 1]},
    "Lucia":                    {"language": "Kannada", "vector": [1, 1, 2, 5, 3, 1]},
    "Rangitaranga":             {"language": "Kannada", "vector": [1, 0, 2, 5, 3, 1]},
    "777 Charlie":              {"language": "Kannada", "vector": [1, 3, 1, 1, 5, 0]},
    "Ulidavaru Kandanthe":      {"language": "Kannada", "vector": [3, 1, 1, 4, 4, 0]},
    "Kirik Party":              {"language": "Kannada", "vector": [1, 5, 3, 0, 3, 0]},
    "Mufti":                    {"language": "Kannada", "vector": [4, 0, 0, 4, 3, 0]},
    "6-5=2":                    {"language": "Kannada", "vector": [0, 0, 0, 4, 1, 5]},
    "Dia":                      {"language": "Kannada", "vector": [0, 1, 5, 1, 5, 0]},
    "Love Mocktail":            {"language": "Kannada", "vector": [0, 4, 5, 0, 3, 0]},

    # --- TAMIL ---
    "Vikram":                   {"language": "Tamil", "vector": [5, 0, 0, 5, 2, 0]},
    "Kaithi":                   {"language": "Tamil", "vector": [5, 0, 0, 5, 2, 0]},
    "Master":                   {"language": "Tamil", "vector": [4, 2, 0, 3, 3, 0]},
    "96":                       {"language": "Tamil", "vector": [0, 1, 5, 0, 4, 0]},
    "Soorarai Pottru":          {"language": "Tamil", "vector": [1, 1, 2, 2, 5, 0]},
    "Jai Bhim":                 {"language": "Tamil", "vector": [1, 0, 0, 3, 5, 0]},
    "Ratsasan":                 {"language": "Tamil", "vector": [2, 0, 0, 5, 3, 2]},
    "Pizzas":                    {"language": "Tamil", "vector": [1, 1, 1, 4, 2, 5]},
    "Super Deluxe":             {"language": "Tamil", "vector": [2, 3, 1, 4, 4, 0]},
    "Asuran":                   {"language": "Tamil", "vector": [4, 0, 1, 3, 5, 0]},
    "Thani Oruvan":             {"language": "Tamil", "vector": [4, 1, 1, 5, 3, 0]},
    "Love Today":               {"language": "Tamil", "vector": [1, 5, 4, 1, 2, 0]},
}

catalog_titles = sorted(list(CATALOG.keys()))
catalog_languages = sorted(set(item["language"] for item in CATALOG.values()))

# ---------------------------------------------------------
# Sidebar: explanation + language filter
# ---------------------------------------------------------
with st.sidebar:
    st.header("📐 How it works")
    st.markdown(
        "Each film is represented as a **vector** across 6 genre "
        "dimensions (0–5 strength each). Selecting a film compares "
        "its vector against every other film using three classic "
        "similarity/distance metrics:\n\n"
        "- **Cosine similarity** — angle between vectors (ignores magnitude, "
        "captures *proportion* of genres)\n"
        "- **Dot product** — raw directional agreement (rewards magnitude too)\n"
        "- **Euclidean distance** — straight-line distance (lower = more similar)"
    )
    st.markdown("---")
    language_filter = st.multiselect(
        "Filter recommendations by language:",
        options=catalog_languages,
        default=catalog_languages,
    )
    st.markdown("---")
    with st.expander("📊 Full catalog vectors"):
        for title, info in CATALOG.items():
            st.write(f"**{title}** ({info['language']}): {dict(zip(GENRES, info['vector']))}")

# ---------------------------------------------------------
# STEP 2: Pure Python/NumPy similarity functions
# ---------------------------------------------------------
def cosine_similarity(u: np.ndarray, v: np.ndarray) -> float:
    """cos(theta) = dot(u, v) / (norm(u) * norm(v))"""
    dot = np.dot(u, v)
    norm_u = np.linalg.norm(u)
    norm_v = np.linalg.norm(v)
    if norm_u == 0 or norm_v == 0:
        return 0.0
    return dot / (norm_u * norm_v)


def dot_product(u: np.ndarray, v: np.ndarray) -> float:
    return float(np.dot(u, v))


def euclidean_distance(u: np.ndarray, v: np.ndarray) -> float:
    return float(np.linalg.norm(u - v))


# ---------------------------------------------------------
# Main: Item Selection
# ---------------------------------------------------------
st.subheader("Step 1 · Pick a Film You Like")

selected_title = st.selectbox(
    "Choose a film from the catalog:",
    options=catalog_titles,
    format_func=lambda t: f"{t} ({CATALOG[t]['language']})",
)

top_n = st.slider("How many recommendations?", min_value=1, max_value=10, value=5)

recommend_clicked = st.button("🔎 Find Similar Films", type="primary")

# ---------------------------------------------------------
# STEP 3: Compute similarity against every other item, rank, display
# ---------------------------------------------------------
if recommend_clicked:
    query_vector = np.array(CATALOG[selected_title]["vector"], dtype=float)

    results = []
    for title, info in CATALOG.items():
        if title == selected_title:
            continue
        if info["language"] not in language_filter:
            continue

        candidate_vector = np.array(info["vector"], dtype=float)

        cos_sim = cosine_similarity(query_vector, candidate_vector)
        dot = dot_product(query_vector, candidate_vector)
        dist = euclidean_distance(query_vector, candidate_vector)

        results.append({
            "title": title,
            "language": info["language"],
            "cosine_similarity": cos_sim,
            "dot_product": dot,
            "euclidean_distance": dist,
        })

    if not results:
        st.warning("⚠️ No films match the selected language filter. Adjust the filter in the sidebar.")
    else:
        # Rank by cosine similarity (highest = most similar), descending
        results.sort(key=lambda r: r["cosine_similarity"], reverse=True)
        top_results = results[:top_n]

        st.success(f"✅ Top {len(top_results)} recommendations for **{selected_title}** ({CATALOG[selected_title]['language']})")

        st.markdown(f"**Query vector:** `{dict(zip(GENRES, CATALOG[selected_title]['vector']))}`")
        st.markdown("---")

        for rank, r in enumerate(top_results, start=1):
            similarity_percent = max(0, r["cosine_similarity"]) * 100  # clamp negative to 0 for display

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**#{rank} · {r['title']}** _({r['language']})_")
                    st.progress(similarity_percent / 100)
                with col2:
                    st.metric("Similarity", f"{similarity_percent:.1f}%")

                with st.expander("📐 Raw metrics"):
                    st.write(f"Cosine similarity: `{r['cosine_similarity']:.4f}`")
                    st.write(f"Dot product: `{r['dot_product']:.2f}`")
                    st.write(f"Euclidean distance: `{r['euclidean_distance']:.2f}` (lower = closer)")

        # -----------------------------------------------------
        # Comparison table across all metrics, for the full ranked list
        # -----------------------------------------------------
        st.markdown("---")
        with st.expander("📋 Full ranked comparison table (filtered catalog)"):
            table_rows = []
            for r in results:
                table_rows.append({
                    "Title": r["title"],
                    "Language": r["language"],
                    "Cosine Similarity": round(r["cosine_similarity"], 4),
                    "Dot Product": round(r["dot_product"], 2),
                    "Euclidean Distance": round(r["euclidean_distance"], 2),
                })
            st.table(table_rows)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 7 · Smart Recommender Agent · Telugu/Kannada/Tamil catalog · Built with Streamlit + NumPy (no LLM needed)")