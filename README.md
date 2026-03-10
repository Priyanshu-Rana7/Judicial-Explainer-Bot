# ⚖️ Judicial Court Process & Case Flow Explainer Bot

> An AI-powered RAG chatbot that explains Indian court procedures, case stages, and legal processes — powered by OpenRouter LLMs and a locally-indexed judicial knowledge base.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-green)](https://langchain.com)
[![OpenRouter](https://img.shields.io/badge/LLM-OpenRouter-orange)](https://openrouter.ai)

---

## 🧠 Overview

This project implements a **Retrieval-Augmented Generation (RAG)** pipeline to answer questions about the Indian judicial system. The bot retrieves relevant passages from a pre-built knowledge base (CPC, CrPC, court stages, bail, appeals, legal terminology) and uses an LLM to generate concise, cited answers — with strict guardrails that prevent legal advice.

---

## 🔑 Key Features

- **RAG Pipeline** — LangChain + FAISS vector search with source attribution (document name + section)
- **Pre-built Knowledge Base** — 6 curated `.txt` files covering Indian court hierarchy, civil/criminal procedures, hearings, bail, appeals, and legal terminology
- **Strict Guardrails** — System prompt enforces procedural-only answers; refuses legal advice, outcome predictions, or lawyer impersonation
- **Local Embeddings** — FastEmbed (`BAAI/bge-small-en-v1.5`, ONNX) runs offline with zero API cost
- **Chat Interface** — Streamlit UI with message history, source expanders, and 8 clickable suggestion chips
- **PDF Extension** — Optional sidebar uploader to extend the knowledge base with custom PDFs

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | DeepSeek Chat via OpenRouter API |
| RAG Framework | LangChain |
| Embeddings | FastEmbed (`BAAI/bge-small-en-v1.5`) — ONNX, local |
| Vector Store | FAISS (CPU) |
| Document Parsing | LangChain PyPDFLoader + TextLoader |
| Text Splitting | RecursiveCharacterTextSplitter (1000 / 200 overlap) |

---

## 🚀 Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API key
```bash
# Create a .env file
echo "OPENROUTER_API_KEY=your_key_here" > .env
```
> Get a free key at [openrouter.ai](https://openrouter.ai)

### 3. Run the app
```bash
streamlit run app.py
```

The app auto-builds the FAISS index from the built-in knowledge base on first launch (downloads ~66MB ONNX model once, then cached locally).

---

## 📂 Project Structure

```
Judicial-Explainer-Bot/
├── app.py              # Streamlit UI
├── rag.py              # RAG chain (LangChain + OpenRouter)
├── ingest.py           # Document ingestion & FAISS indexing
├── data/               # Built-in judicial knowledge base
│   ├── 01_court_hierarchy.txt
│   ├── 02_civil_case_filing.txt
│   ├── 03_criminal_case_process.txt
│   ├── 04_court_hearings.txt
│   ├── 05_legal_terminology.txt
│   └── 06_stages_appeals_bail.txt
├── requirements.txt
└── .env.example
```

---

## 📚 Knowledge Base Coverage

| File | Indian Law Referenced |
|---|---|
| Court Hierarchy | Constitution of India (Art. 124, 214, 226) |
| Civil Filing | Code of Civil Procedure, 1908 (CPC) |
| Criminal Process | Code of Criminal Procedure, 1973 (CrPC) |
| Court Hearings | CPC + CrPC procedures |
| Legal Terminology | CPC, CrPC, Constitution Art. 32 & 226 |
| Stages, Bail, Appeals | CrPC, Limitation Act 1963, Legal Services Authorities Act 1987 |

---

## ⚠️ Disclaimer

This application explains procedural workflows only. It is **not** a substitute for legal counsel. Always consult a qualified advocate for legal advice.
