"""
app.py – Judicial Court Process & Case Flow Explainer
Chat-first Streamlit UI with auto-seeded built-in judicial knowledge base.
Users just type questions — no PDF upload required.
"""

import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from ingest import (
    INDEX_PATH,
    seed_builtin_index,
    build_or_update_index,
    load_and_split_pdf,
)
from rag import DEFAULT_MODEL, get_answer_with_sources

# ── Bootstrap ─────────────────────────────────────────────────────────────────
load_dotenv()

st.set_page_config(
    page_title="Judicial Process Explainer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Main background */
.main .block-container { padding-top: 1rem; }

/* Disclaimer banner */
.disclaimer {
    background: linear-gradient(135deg, #7f1d1d, #991b1b);
    color: #fee2e2;
    padding: 0.7rem 1.2rem;
    border-radius: 10px;
    border-left: 5px solid #f87171;
    font-size: 0.88rem;
    font-weight: 500;
    margin-bottom: 1.2rem;
}

/* Header card */
.header-card {
    background: linear-gradient(135deg, #0f2044 0%, #1e3a5f 50%, #1e293b 100%);
    padding: 1.4rem 2rem;
    border-radius: 14px;
    border: 1px solid #2d4a6e;
    margin-bottom: 1.2rem;
}
.header-card h1 { color: #f0f6ff; margin: 0; font-size: 1.75rem; font-weight: 700; }
.header-card p  { color: #94a3b8; margin: 0.3rem 0 0; font-size: 0.92rem; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1120 0%, #0f172a 100%);
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown { color: #94a3b8 !important; }
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #e2e8f0 !important; }

/* Status badges */
.badge-on  { background:#14532d; color:#86efac; border:1px solid #16a34a; border-radius:20px; padding:0.2rem 0.85rem; font-size:0.78rem; font-weight:600; }
.badge-off { background:#431407; color:#fdba74; border:1px solid #ea580c; border-radius:20px; padding:0.2rem 0.85rem; font-size:0.78rem; font-weight:600; }

/* Source attribution cards */
.src-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.5rem 0.9rem;
    margin: 0.25rem 0;
    font-size: 0.81rem;
    color: #94a3b8;
}
.src-card strong { color: #60a5fa; }

/* Suggestion chips */
.chip-row { display:flex; flex-wrap:wrap; gap:0.5rem; margin:1rem 0 0.5rem; }
.chip {
    background: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #2563eb;
    border-radius: 20px;
    padding: 0.3rem 0.9rem;
    font-size: 0.82rem;
    cursor: pointer;
    transition: background 0.2s;
}
.chip:hover { background: #1d4ed8; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "chat_history"     not in st.session_state: st.session_state.chat_history     = []
if "vector_store"     not in st.session_state: st.session_state.vector_store     = None
if "index_ready"      not in st.session_state: st.session_state.index_ready      = False
if "extra_docs"       not in st.session_state: st.session_state.extra_docs       = []
if "pending_question" not in st.session_state: st.session_state.pending_question = None

# ── Auto-seed index on first load ─────────────────────────────────────────────
if not st.session_state.index_ready:
    with st.spinner("⚖️ Loading judicial knowledge base… (first run downloads embedding model ~80 MB)"):
        vs = seed_builtin_index()
        if vs:
            st.session_state.vector_store = vs
            st.session_state.index_ready  = True

# ── Config (from .env only) ───────────────────────────────────────────────────
openrouter_key  = os.getenv("OPENROUTER_API_KEY", "")
selected_model  = DEFAULT_MODEL

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ Judicial Explainer")
    st.markdown("---")

    # Knowledge base status
    st.markdown("### 📚 Knowledge Base")
    if st.session_state.index_ready:
        st.markdown('<span class="badge-on">● Ready — Built-in Knowledge Loaded</span>', unsafe_allow_html=True)
        st.caption("Covers: CPC, CrPC, court stages, bail, summons, hearings, terminology, appeals.")
    else:
        st.markdown('<span class="badge-off">○ Not Ready</span>', unsafe_allow_html=True)
        if st.button("🔄 Retry Loading Knowledge Base", use_container_width=True):
            st.session_state.index_ready  = False
            st.session_state.vector_store = None
            st.rerun()

    st.markdown("---")

    # Optional PDF upload to extend knowledge base
    with st.expander("📤 Add Your Own PDFs (Optional)", expanded=False):
        st.caption("Upload additional PDFs to extend the knowledge base with your own documents.")
        uploaded_files = st.file_uploader(
            "Upload PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if st.button("⚡ Process & Add PDFs", use_container_width=True):
            if not uploaded_files:
                st.warning("Please select at least one PDF.")
            else:
                all_chunks = []
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name
                    try:
                        chunks = load_and_split_pdf(tmp_path, display_name=uploaded_file.name)
                        all_chunks.extend(chunks)
                        if uploaded_file.name not in st.session_state.extra_docs:
                            st.session_state.extra_docs.append(uploaded_file.name)
                    except Exception as e:
                        st.error(f"Error: {uploaded_file.name} – {e}")
                    finally:
                        os.unlink(tmp_path)

                if all_chunks:
                    with st.spinner("Indexing additional documents…"):
                        st.session_state.vector_store = build_or_update_index(all_chunks)
                    st.success(f"✅ Added {len(all_chunks)} chunks!")
                    st.rerun()

        if st.session_state.extra_docs:
            st.markdown("**Extra docs indexed:**")
            for d in st.session_state.extra_docs:
                st.caption(f"📄 {d}")

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.caption(f"🤖 Model: `{DEFAULT_MODEL}`")
    st.caption("🔒 Embeddings run locally. Only your question reaches OpenRouter.")

# ── Main Area ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
  <h1>⚖️ Judicial Court Process & Case Flow Explainer</h1>
  <p>Ask anything about Indian court procedures, case stages, filing steps, bail, summons, hearings, and more.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
  ⚠️ <strong>DISCLAIMER:</strong> This AI explains procedural workflows only.
  It is <u>NOT a substitute for legal counsel</u>. Always consult a qualified advocate for legal advice.
</div>
""", unsafe_allow_html=True)

# ── Suggested Questions (shown when chat is empty) ────────────────────────────
SUGGESTIONS = [
    "Explain the court case filing process",
    "What happens during a hearing?",
    "What are the stages of a criminal case?",
    "What is a summons and how is it served?",
    "How does bail work in India?",
    "How do I file an appeal?",
    "What is an FIR and how is it filed?",
    "What is the difference between civil and criminal cases?",
]

if not st.session_state.chat_history:
    with st.chat_message("assistant", avatar="⚖️"):
        st.markdown(
            "👋 **Welcome!** I'm your **Judicial Process Explainer**.\n\n"
            "I'm loaded with knowledge about Indian court procedures — CPC, CrPC, "
            "court stages, bail, hearings, summons, and more.\n\n"
            "**Just type your question below, or click a suggestion to get started:**"
        )

    # Suggestion chips via buttons
    cols = st.columns(2)
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(f"💬 {suggestion}", key=f"sugg_{i}", use_container_width=True):
                st.session_state.pending_question = suggestion
                st.rerun()

else:
    # Render full chat history
    for message in st.session_state.chat_history:
        avatar = "⚖️" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            # Source attribution for assistant messages
            if message["role"] == "assistant" and message.get("sources"):
                sources = message["sources"]
                with st.expander(f"📄 Sources ({len(sources)} passages retrieved)", expanded=False):
                    seen = set()
                    for doc in sources:
                        src  = doc.metadata.get("source", "Built-in Knowledge")
                        page = doc.metadata.get("page", "—")
                        key  = f"{src}|{page}"
                        if key not in seen:
                            seen.add(key)
                            st.markdown(
                                f'<div class="src-card">📄 <strong>{src}</strong>'
                                f' &nbsp;|&nbsp; Section/Page: <strong>{page}</strong></div>',
                                unsafe_allow_html=True,
                            )

# ── Chat Input ────────────────────────────────────────────────────────────────
chat_disabled = not st.session_state.index_ready
user_input = st.chat_input(
    "Ask about court procedures, case stages, bail, summons, filing steps…",
    disabled=chat_disabled,
)

# Handle either direct input or suggestion click
question = user_input or st.session_state.pending_question
if st.session_state.pending_question:
    st.session_state.pending_question = None   # clear it

if question:
    if not openrouter_key:
        st.error("⚠️ OPENROUTER_API_KEY not found. Please add it to your `.env` file and restart the app.")
        st.stop()

    if not st.session_state.index_ready or st.session_state.vector_store is None:
        st.error("⚠️ Knowledge base is not ready. Please wait or click 'Retry' in the sidebar.")
        st.stop()

    # Append and display user message
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="👤"):
        st.markdown(question)

    # Generate AI response
    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Searching knowledge base and generating answer…"):
            try:
                answer, source_docs = get_answer_with_sources(
                    vector_store       = st.session_state.vector_store,
                    question           = question,
                    history            = st.session_state.chat_history[:-1],
                    openrouter_api_key = openrouter_key,
                    model_name         = selected_model,
                )
                st.markdown(answer)

                if source_docs:
                    with st.expander(f"📄 Sources ({len(source_docs)} passages retrieved)", expanded=False):
                        seen = set()
                        for doc in source_docs:
                            src  = doc.metadata.get("source", "Built-in Knowledge")
                            page = doc.metadata.get("page", "—")
                            key  = f"{src}|{page}"
                            if key not in seen:
                                seen.add(key)
                                st.markdown(
                                    f'<div class="src-card">📄 <strong>{src}</strong>'
                                    f' &nbsp;|&nbsp; Section/Page: <strong>{page}</strong></div>',
                                    unsafe_allow_html=True,
                                )

            except Exception as e:
                answer      = f"❌ Error: {str(e)}"
                source_docs = []
                st.error(answer)

    st.session_state.chat_history.append({
        "role":    "assistant",
        "content": answer,
        "sources": source_docs,
    })
