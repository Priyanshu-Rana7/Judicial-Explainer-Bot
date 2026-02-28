# ⚖️ Judicial Court Process & Case Flow Explainer Bot

A **Retrieval-Augmented Generation (RAG)** chatbot that explains Indian judicial court procedures, case flow stages, and filing steps. Powered by **OpenRouter LLMs** and **local HuggingFace embeddings** — no Google API quota concerns.

> ⚠️ **This tool explains procedural workflows only. It is NOT a substitute for legal counsel.**

---

## 🧠 Architecture

```
PDF Documents  ──►  PyPDFLoader  ──►  RecursiveCharacterTextSplitter (1000/200)
                                              │
                                    HuggingFaceEmbeddings
                                    (all-MiniLM-L6-v2, local)
                                              │
                                         FAISS Index  ◄──── Vector Store
                                              │
User Question  ──►  Retriever (top-4 chunks) ─┘
                         │
                    ChatOpenAI via OpenRouter  ──►  Answer + Source Attribution
```

| Component | Technology |
|---|---|
| UI | Streamlit |
| LLM | OpenRouter (any model: DeepSeek, LLaMA, Mistral…) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, free) |
| Vector Store | FAISS CPU |
| Orchestration | LangChain |

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- An [OpenRouter API key](https://openrouter.ai) (free tier available)

### 2. Install dependencies
```bash
cd "Judicial-Explainer-Bot"
pip install -r requirements.txt
```
> The HuggingFace embedding model (~80MB) is downloaded automatically on first run.

### 3. Set your API key
```bash
# Copy the example file
copy .env.example .env

# Edit .env and paste your OpenRouter key:
# OPENROUTER_API_KEY=sk-or-...
```

### 4. Run the app
```bash
streamlit run app.py
```
The app opens at **http://localhost:8501**

---

## 📖 How to Use

1. **Enter your OpenRouter API Key** in the sidebar
2. **Select a model** from the dropdown (default: `deepseek/deepseek-chat`)
3. **Upload PDF documents** (CPC, CrPC, Judicial Manuals, etc.)
4. Click **"Process & Index Documents"** — waits ~30s on first run to download the embedding model
5. **Ask questions** about court procedures in the chat window
6. Each answer shows a **📄 Sources** expander listing the document name and page number

---

## 📁 Project Structure

```
Judicial-Explainer-Bot/
├── app.py          # Streamlit UI
├── ingest.py       # PDF loading, chunking, FAISS indexing
├── rag.py          # OpenRouter LLM chain + guardrails
├── requirements.txt
├── .env.example    # API key template
├── .env            # Your actual keys (git-ignored)
├── faiss_index/    # Auto-created: local vector database
└── uploaded_docs/  # (Optional) store your PDFs here
```

---

## 🔒 Guardrails

The system prompt strictly enforces:
- ✅ Explain court procedures, case stages, filing steps
- ❌ No legal advice
- ❌ No case outcome predictions
- ❌ No lawyer impersonation
- ✅ Always cite source document + page number

---

## 🔑 Available OpenRouter Models

| Model | Notes |
|---|---|
| `deepseek/deepseek-chat` | Excellent default, very affordable |
| `deepseek/deepseek-r1` | Strongest reasoning |
| `meta-llama/llama-3.3-70b-instruct` | High quality open model |
| `mistralai/mistral-7b-instruct` | Fast and lightweight |
| `google/gemma-3-27b-it:free` | Free tier option |

---

## ⚙️ Configuration

| Parameter | Value | Location |
|---|---|---|
| Chunk size | 1000 chars | `ingest.py` |
| Chunk overlap | 200 chars | `ingest.py` |
| Top-k retrieval | 4 chunks | `rag.py` |
| LLM temperature | 0.2 | `rag.py` |
| Embedding model | `all-MiniLM-L6-v2` | `ingest.py` |
