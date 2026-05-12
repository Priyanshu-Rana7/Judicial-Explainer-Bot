import os
import json
import shutil
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Security & Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ingest import seed_builtin_index, build_or_update_index, load_and_split_pdf
from rag import get_answer_with_sources, DEFAULT_MODEL
from dotenv import load_dotenv

load_dotenv()

# Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Judicial Explainer API (Hardened)")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── 1. STRICT CORS CONFIGURATION ──────────────────────────────────────────────
allowed_origins = [
    "https://judicial-explainer-bot.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000"
]

# Support dynamic origins from ENV if provided
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    allowed_origins.extend(env_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 2. PII SCRUBBER (Privacy Protection) ──────────────────────────────────────
def scrub_pii(text: str) -> str:
    """Masks emails, phone numbers, and potential names to protect user privacy."""
    # Mask Emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', text)
    # Mask Phone Numbers (International & Indian formats)
    text = re.sub(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[PHONE_REDACTED]', text)
    return text

# Global vector store instance
vector_store = None

@app.on_event("startup")
async def startup_event():
    global vector_store
    print("Initializing hardened vector store...")
    vector_store = seed_builtin_index()
    
    # ── PRE-WARM HUGGINGFACE ──────────────────────────────────────────────────
    # This wakes up the model in the cloud so the user doesn't wait 60s
    if vector_store:
        print("Pre-warming cloud embedding model...")
        try:
            vector_store.embeddings.embed_query("warmup")
            print("Cloud model is READY.")
        except Exception as e:
            print(f"[WARN] Pre-warm failed (normal if model is still loading): {e}")

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@app.get("/")
async def root():
    return {"status": "online", "security": "hardened"}

@app.post("/chat")
@limiter.limit("10/minute") # Protect against API abuse
async def chat(request: Request, chat_req: ChatRequest):
    global vector_store
    if not vector_store:
        vector_store = seed_builtin_index()
        if not vector_store:
            raise HTTPException(status_code=500, detail="Vector store not initialized.")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API Configuration missing")

    try:
        answer, sources, flow = get_answer_with_sources(
            vector_store=vector_store,
            question=chat_req.message,
            history=chat_req.history,
            openrouter_api_key=api_key,
            model_name=DEFAULT_MODEL
        )
        
        formatted_sources = [{"content": d.page_content, "metadata": d.metadata} for d in sources]
        return {"answer": answer, "sources": formatted_sources, "flow": flow}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
@limiter.limit("3/minute") # Strict limit for file processing
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    # ── 3. UPLOAD SANITIZATION ────────────────────────────────────────────────
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed for security.")
    
    # Limit file size to 10MB
    MAX_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max limit is 10MB.")
    await file.seek(0)

    global vector_store
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        chunks = load_and_split_pdf(temp_path, display_name=file.filename)
        vector_store = build_or_update_index(chunks)
        return {"message": f"Successfully indexed {len(chunks)} chunks"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/feedback")
@limiter.limit("20/minute")
async def save_feedback(request: Request, data: dict):
    """Save user feedback with PII Scrubbing."""
    try:
        # Scrub PII from both question and answer before logging
        clean_data = {
            "question": scrub_pii(data.get("question", "")),
            "answer": scrub_pii(data.get("answer", "")),
            "rating": data.get("rating")
        }
        with open("feedback_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(clean_data) + "\n")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate")
@limiter.limit("15/minute")
async def translate_text(request: Request, data: dict):
    text = data.get("text")
    target_lang = data.get("language")
    
    if not text or not target_lang:
        raise HTTPException(status_code=400, detail="Text and language required")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    try:
        from rag import get_llm
        llm = get_llm(api_key, DEFAULT_MODEL, temp=0.3)
        prompt = f"Translate the following legal procedure text into {target_lang}. Preserve markdown. \n\nText: {text}"
        response = llm.invoke([("human", prompt)])
        return {"translated_text": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
