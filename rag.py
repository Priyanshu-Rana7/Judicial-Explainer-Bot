"""
rag.py – RAG pipeline using LangChain + OpenRouter.
Builds a question-answering chain with strict judicial-only guardrails.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.vectorstores import FAISS

# ── OpenRouter base URL ────────────────────────────────────────────────────────
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── System prompt with strict guardrails ──────────────────────────────────────
SYSTEM_PROMPT = """You are a Judicial Process Explainer Bot. Your sole purpose is to \
explain Indian court procedures, case flow stages, filing steps, and process timelines \
strictly based on the documents retrieved from the knowledge base.

STRICT RULES — YOU MUST FOLLOW THESE WITHOUT EXCEPTION:
1. ONLY explain procedural workflows, court stages, and administrative processes.
2. NEVER give legal advice, legal opinions, or strategic recommendations.
3. NEVER predict case outcomes or comment on the merits of any case.
4. NEVER claim to be a lawyer, legal representative, or legal expert.
5. If the user asks for legal advice or anything beyond procedural explanation, \
POLITELY REFUSE and clearly direct them to consult a qualified legal professional.
6. When answering, ALWAYS reference the document name and page number from the \
retrieved context (e.g., "According to [Document Name], Page X, ...").
7. If the information is not in the provided documents, respond EXACTLY with: \
"I could not find information about this in the provided documents. Please consult \
the relevant official legal manual or a legal professional."
8. Be CONCISE. Give clear, to-the-point answers. Avoid unnecessary elaboration. \
Use bullet points or numbered steps where appropriate.

Context from documents:
{context}
"""

# ── Default model ─────────────────────────────────────────────────────────────
# deepseek/deepseek-chat: best for structured factual Q&A — strong instruction
# following, consistent formatting, very affordable on OpenRouter.
DEFAULT_MODEL = "deepseek/deepseek-chat"


def get_llm(api_key: str, model_name: str) -> ChatOpenAI:
    """Create a ChatOpenAI instance pointed at OpenRouter."""
    return ChatOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        model=model_name,
        temperature=0.2,          # Low temp for factual, consistent answers
        max_tokens=2048,
    )


def format_context(docs: list) -> str:
    """Format retrieved documents into a context string for the prompt."""
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown Document")
        page   = doc.metadata.get("page", "N/A")
        parts.append(f"[Source: {source}, Page {page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def format_history(history: list[dict]) -> list:
    """Convert session history dicts to LangChain message objects."""
    messages = []
    for entry in history:
        if entry["role"] == "user":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry["role"] == "assistant":
            messages.append(AIMessage(content=entry["content"]))
    return messages


def get_answer_with_sources(
    vector_store: FAISS,
    question: str,
    history: list[dict],
    openrouter_api_key: str,
    model_name: str,
    k: int = 4,
) -> tuple[str, list]:
    """
    Run the RAG pipeline:
      1. Retrieve top-k relevant chunks from FAISS.
      2. Format them as context.
      3. Call OpenRouter LLM with system prompt + history + question.
      4. Return (answer_text, source_documents).
    """
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )

    # Retrieve relevant documents
    source_docs = retriever.invoke(question)
    context     = format_context(source_docs)

    # Build prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])

    llm = get_llm(openrouter_api_key, model_name)
    chain = prompt | llm

    response = chain.invoke({
        "context":  context,
        "history":  format_history(history),
        "question": question,
    })

    return response.content, source_docs
