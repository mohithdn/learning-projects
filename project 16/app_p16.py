"""
Project 16: In-Memory RAG & Knowledge Base Agent
--------------------------------------------------------
Goal: A lightweight Retrieval-Augmented Generation system that:
  1. Chunks an uploaded/pasted policy document
  2. Embeds each chunk + the user's query
  3. Retrieves the most relevant chunks via cosine similarity
  4. Forces Gemini to answer STRICTLY from retrieved context
     (or say "Not found in knowledge base" if it isn't there)

Run with:
    python -m streamlit run app_p16.py
"""

import numpy as np
import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="In-Memory RAG Agent",
    page_icon="📚",
    layout="centered",
)

st.title("📚 In-Memory RAG & Knowledge Base Agent")
st.caption("Paste a policy document, ask a question — the agent answers strictly from the retrieved text, and refuses to hallucinate.")

EMBED_MODEL = "gemini-embedding-001"
GEN_MODEL = "gemini-3.7-flash"
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50     # overlap between consecutive chunks
TOP_K = 3              # how many chunks to retrieve per query

# ---------------------------------------------------------
# Sidebar: API Key
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here")
    st.markdown("---")
    if st.button("🗑️ Clear Knowledge Base"):
        st.session_state.pop("chunks", None)
        st.session_state.pop("chunk_embeddings", None)
        st.rerun()
    st.markdown("---")
    st.markdown(
        f"**How it works:**\n"
        f"- Document is split into ~{CHUNK_SIZE}-char chunks\n"
        f"- Each chunk is embedded with `{EMBED_MODEL}`\n"
        f"- Your question is embedded and compared via cosine similarity\n"
        f"- Top {TOP_K} chunks are injected into the prompt as strict context"
    )

# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "chunk_embeddings" not in st.session_state:
    st.session_state.chunk_embeddings = None  # numpy array, shape (n_chunks, dim)

# ---------------------------------------------------------
# STEP 1: Chunking helper
# ---------------------------------------------------------
def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Splits text into overlapping fixed-size character chunks."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

# ---------------------------------------------------------
# STEP 2: Embedding helpers
# ---------------------------------------------------------
def embed_texts(client: genai.Client, texts: list[str], task_type: str) -> np.ndarray:
    """Embeds a list of texts and returns a (n, dim) numpy array."""
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    vectors = [e.values for e in result.embeddings]
    return np.array(vectors)

def cosine_similarity(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    """Returns cosine similarity between one query vector and a matrix of doc vectors."""
    query_norm = query_vec / np.linalg.norm(query_vec)
    doc_norms = doc_matrix / np.linalg.norm(doc_matrix, axis=1, keepdims=True)
    return doc_norms @ query_norm

# ---------------------------------------------------------
# Knowledge Base Ingestion
# ---------------------------------------------------------
st.subheader("Step 1 · Build the Knowledge Base")

doc_text = st.text_area(
    "Paste your policy document text here:",
    height=200,
    placeholder="e.g. Refund Policy: Customers may request a refund within 30 days of purchase...",
)

if st.button("📥 Ingest Document"):
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif not doc_text.strip():
        st.warning("⚠️ Please paste some document text first.")
    else:
        with st.spinner("Chunking and embedding document..."):
            try:
                client = genai.Client(api_key=api_key)

                chunks = chunk_text(doc_text, CHUNK_SIZE, CHUNK_OVERLAP)
                embeddings = embed_texts(client, chunks, task_type="RETRIEVAL_DOCUMENT")

                st.session_state.chunks = chunks
                st.session_state.chunk_embeddings = embeddings

                st.success(f"✅ Ingested {len(chunks)} chunks into the in-memory knowledge base.")
            except Exception as e:
                st.error(f"❌ Something went wrong during ingestion: {e}")

if st.session_state.chunks:
    with st.expander(f"📦 Knowledge base contents ({len(st.session_state.chunks)} chunks)"):
        for i, c in enumerate(st.session_state.chunks):
            st.markdown(f"**Chunk {i+1}:** {c[:150]}{'...' if len(c) > 150 else ''}")

st.markdown("---")

# ---------------------------------------------------------
# Query & Grounded Answer
# ---------------------------------------------------------
st.subheader("Step 2 · Ask a Question")

query = st.text_input("Your question:", placeholder="e.g. What is the refund window?")
ask_clicked = st.button("🔎 Ask", type="primary")

if ask_clicked:
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
    elif st.session_state.chunk_embeddings is None or len(st.session_state.chunks) == 0:
        st.warning("⚠️ Please ingest a document first.")
    elif not query.strip():
        st.warning("⚠️ Please type a question.")
    else:
        try:
            with st.spinner("Retrieving relevant chunks and generating grounded answer..."):
                client = genai.Client(api_key=api_key)

                # STEP 3: Embed the query and retrieve top-K most similar chunks
                query_vec = embed_texts(client, [query], task_type="RETRIEVAL_QUERY")[0]
                similarities = cosine_similarity(query_vec, st.session_state.chunk_embeddings)

                top_indices = np.argsort(similarities)[::-1][:TOP_K]
                retrieved_chunks = [st.session_state.chunks[i] for i in top_indices]
                retrieved_scores = [similarities[i] for i in top_indices]

                # STEP 4: Build strict, hallucination-preventing prompt
                context_block = "\n\n---\n\n".join(
                    f"[Excerpt {i+1}]\n{chunk}" for i, chunk in enumerate(retrieved_chunks)
                )

                grounded_prompt = f"""
                You are a strict knowledge-base assistant. Answer the user's question
                using ONLY the excerpts below. Do not use any outside knowledge or
                assumptions.

                Rules:
                - If the answer is present in the excerpts, answer clearly and cite
                  which excerpt(s) it came from, e.g. "(Excerpt 2)".
                - If the answer is NOT present in the excerpts, respond exactly with:
                  "Not found in knowledge base."
                - Never guess or fill in gaps with general knowledge.

                Excerpts:
                {context_block}

                Question: {query}
                """

                response = client.models.generate_content(
                    model=GEN_MODEL,
                    contents=grounded_prompt,
                )

            st.markdown("### 🧠 Answer")
            st.write(response.text)

            with st.expander("🔍 Retrieved excerpts used for this answer"):
                for chunk, score in zip(retrieved_chunks, retrieved_scores):
                    st.markdown(f"**Similarity: {score:.3f}**")
                    st.write(chunk)
                    st.markdown("---")

        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Project 16 · In-Memory RAG & Knowledge Base Agent · Built with Streamlit + Gemini")