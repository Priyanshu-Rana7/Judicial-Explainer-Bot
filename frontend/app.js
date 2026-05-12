// Configuration
const API_BASE = "http://localhost:8000"; // Local testing URL

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-chat');

// State
let chatHistory = [];
let isProcessing = false;

// Initialize
function init() {
    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Enable/disable send button
        sendBtn.disabled = !this.value.trim() || isProcessing;
    });

    // Send on Enter (but allow Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    sendBtn.addEventListener('click', handleSendMessage);
    clearBtn.addEventListener('click', clearConversation);
}

// Actions
async function handleSendMessage() {
    const text = userInput.value.trim();
    if (!text || isProcessing) return;

    // UI Updates
    setProcessing(true);
    appendMessage('user', text);
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Add temporary loading message
    const loadingId = appendLoadingMessage();

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: text, 
                history: chatHistory 
            })
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        
        // Remove loading and add actual response
        removeMessage(loadingId);
        appendMessage('assistant', data.answer, data.sources);
        
        // Update history for context
        chatHistory.push({ role: 'user', content: text });
        chatHistory.push({ role: 'assistant', content: data.answer });

    } catch (err) {
        console.error(err);
        removeMessage(loadingId);
        appendMessage('assistant', "I'm sorry, I encountered an error connecting to the judicial database. Please ensure the backend is running.");
    } finally {
        setProcessing(false);
    }
}

function setQuestion(text) {
    userInput.value = text;
    userInput.dispatchEvent(new Event('input'));
    userInput.focus();
}

function setProcessing(processing) {
    isProcessing = processing;
    sendBtn.disabled = processing || !userInput.value.trim();
    userInput.disabled = processing;
}

// UI Helpers
function appendMessage(role, text, sources = []) {
    const msgId = 'msg-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = msgId;
    msgDiv.className = `message ${role} animate-in`;
    
    let sourcesHtml = '';
    let feedbackHtml = '';

    if (role === 'assistant') {
        feedbackHtml = `
            <div class="feedback-tools">
                <button onclick="sendFeedback('${msgId}', 'pos')" title="Helpful"><i class="fa-regular fa-thumbs-up"></i></button>
                <button onclick="sendFeedback('${msgId}', 'neg')" title="Not Helpful / Incorrect"><i class="fa-regular fa-thumbs-down"></i></button>
            </div>
        `;

        if (sources && sources.length > 0) {
            const seen = new Set();
            const uniqueSources = sources.filter(s => {
                const key = `${s.metadata.source}-${s.metadata.page}`;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });

            sourcesHtml = `
                <div class="sources">
                    ${uniqueSources.map(s => `
                        <span class="source-tag">
                            <i class="fa-solid fa-file-lines"></i> ${s.metadata.source} (p. ${s.metadata.page})
                        </span>
                    `).join('')}
                </div>
            `;
        }
    }

    msgDiv.innerHTML = `
        <div class="message-content">
            <p>${formatText(text)}</p>
            ${feedbackHtml}
        </div>
        ${sourcesHtml}
    `;
    
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

async function sendFeedback(msgId, rating) {
    const msgEl = document.getElementById(msgId);
    const text = msgEl.querySelector('p').innerText;
    
    // Find the question that led to this answer (the last user message before this one)
    const messages = Array.from(document.querySelectorAll('.message'));
    const index = messages.indexOf(msgEl);
    let question = "";
    for (let i = index - 1; i >= 0; i--) {
        if (messages[i].classList.contains('user')) {
            question = messages[i].querySelector('p').innerText;
            break;
        }
    }

    try {
        const response = await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, answer: text, rating })
        });
        
        if (response.ok) {
            // Visual confirmation
            const tools = msgEl.querySelector('.feedback-tools');
            tools.innerHTML = `<span style="font-size:0.75rem; color:var(--primary)">Thank you for your feedback! ${rating === 'pos' ? '👍' : '👎'}</span>`;
        }
    } catch (err) {
        console.error("Feedback error:", err);
    }
}

function appendLoadingMessage() {
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = id;
    msgDiv.className = `message assistant animate-in`;
    msgDiv.innerHTML = `
        <div class="message-content">
            <p><i class="fa-solid fa-circle-notch fa-spin"></i> Consultating judicial manuals...</p>
        </div>
    `;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function clearConversation() {
    if (confirm('Clear entire conversation?')) {
        chatMessages.innerHTML = '';
        chatHistory = [];
        appendMessage('assistant', 'Conversation cleared. How else can I help you?');
    }
}

function scrollToBottom() {
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

function formatText(text) {
    // Basic formatting: bold and newlines
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

function setQuestion(text) {
    userInput.value = text;
    // Trigger input event to resize textarea
    const event = new Event('input', { bubbles: true });
    userInput.dispatchEvent(event);
    handleSendMessage();
}

// Start
init();
window.setQuestion = setQuestion; // Make globally accessible for chips
