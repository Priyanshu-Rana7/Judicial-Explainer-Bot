import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Scale, 
  Trash2, 
  Send, 
  Info, 
  Lightbulb, 
  AlertTriangle, 
  ThumbsUp,
  ThumbsDown,
  Loader2,
  FileText,
  Upload,
  ChevronRight,
  Languages
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactiveBackground from './components/ReactiveBackground';

const CaseFlow = ({ stages }) => {
  if (!stages || stages.length === 0) return null;
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="case-flow"
      style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '0.5rem', 
        margin: '1.5rem 0',
        padding: '1rem',
        background: 'rgba(255,255,255,0.02)',
        borderRadius: '8px',
        border: '1px solid rgba(255,255,255,0.05)',
        overflowX: 'auto'
      }}
    >
      {stages.map((stage, i) => (
        <React.Fragment key={i}>
          <div style={{ 
            padding: '0.5rem 1rem', 
            background: '#fff', 
            color: '#000', 
            borderRadius: '4px',
            fontSize: '0.75rem',
            fontWeight: '700',
            whiteSpace: 'nowrap',
            textTransform: 'uppercase'
          }}>
            {stage}
          </div>
          {i < stages.length - 1 && <ChevronRight size={14} color="#444" />}
        </React.Fragment>
      ))}
    </motion.div>
  );
};

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: 'Welcome to the **Judicial Court Process & Case Flow Explainer**. How can I help you navigate the Indian court system today?',
      id: 'welcome'
    }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [agentStatus, setAgentStatus] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Mobile toggle
  const chatEndRef = useRef(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    setIsUploading(true);

    try {
      await axios.post(`${API_BASE}/upload`, formData);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ **System Updated**: Successfully indexed and added **${file.name}** to the judicial knowledge base.`,
        id: Date.now()
      }]);
    } catch (error) {
      alert("Upload failed: " + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (text) => {
    const messageText = text || input.trim();
    if (!messageText || isProcessing) return;

    const userMsg = { role: 'user', content: messageText, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsProcessing(true);
    setAgentStatus('DRAFTING PROCEDURAL EXPLANATION...');

    try {
      // Transition status mid-flight
      setTimeout(() => setAgentStatus('AUDITING COMPLIANCE & GUARDRAILS...'), 1200);

      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const response = await axios.post(`${API_BASE}/chat`, {
        message: messageText,
        history: history
      });

      setAgentStatus('FINALIZING RESPONSE...');
      setTimeout(() => setAgentStatus(''), 500);

      const assistantMsg = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        flow: response.data.flow, // Capture the visualization stages
        id: Date.now() + 1
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      setAgentStatus('');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Error connecting to the judicial database.",
        id: Date.now() + 1
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const sendFeedback = async (msgId, rating) => {
    const msg = messages.find(m => m.id === msgId);
    const index = messages.indexOf(msg);
    const question = messages[index - 1]?.content || "";

    try {
      await axios.post(`${API_BASE}/feedback`, {
        question,
        answer: msg.content,
        rating
      });
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, feedbackGiven: rating } : m
      ));
    } catch (error) {
      console.error("Feedback error", error);
    }
  };

  const handleTranslate = async (msgId, language) => {
    const msg = messages.find(m => m.id === msgId);
    if (!msg) return;

    // 1. Initialize originalContent and translations cache if they don't exist
    const original = msg.originalContent || msg.content;
    const cache = msg.translations || { "English": original };

    // 2. Check if the requested language is already cached
    if (cache[language]) {
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, content: cache[language], translations: cache, originalContent: original } : m
      ));
      return;
    }

    // 3. If not cached, show loading and fetch
    setMessages(prev => prev.map(m => 
      m.id === msgId ? { ...m, isTranslating: true, originalContent: original, translations: cache } : m
    ));

    try {
      const response = await axios.post(`${API_BASE}/translate`, {
        text: original,
        language: language
      });
      
      const translatedText = response.data.translated_text;
      
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { 
          ...m, 
          content: translatedText, 
          isTranslating: false,
          translations: { ...cache, [language]: translatedText } // Update cache
        } : m
      ));
    } catch (error) {
      alert("Translation failed");
      setMessages(prev => prev.map(m => m.id === msgId ? { ...m, isTranslating: false } : m));
    }
  };

  const clearChat = () => {
    if (window.confirm("Clear conversation?")) {
      setMessages([{ 
        role: 'assistant', 
        content: 'Conversation cleared. How else can I help you?',
        id: Date.now()
      }]);
    }
  };

  return (
    <div className="main-wrapper" style={{ width: '100%', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <ReactiveBackground />
      
      <div className="app-shell">
        <AnimatePresence>
          {isSidebarOpen && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="sidebar-overlay"
              onClick={() => setIsSidebarOpen(false)}
            />
          )}
        </AnimatePresence>

        <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
          <div className="sidebar-header">
            <div className="logo">
              <Scale size={24} color="#fff" />
              <span>JUDICIAL AI</span>
            </div>
            {/* Mobile close button */}
            <button className="menu-toggle" onClick={() => setIsSidebarOpen(false)} style={{ marginRight: 0 }}>
              <X size={18} />
            </button>
          </div>
          {/* ... existing sidebar content ... */}

          <div className="sidebar-content">
            <div className="info-card">
              <h3><Info size={14} /> SYSTEM MISSION</h3>
              <p>Factual Indian court procedures strictly via RAG-verified legal manuals.</p>
            </div>

            <div className="suggested-topics">
              <h4>SUGGESTED</h4>
              {[
                "Bail Process in India",
                "Stages of a civil suit",
                "What is a summons?",
                "Process of filing an FIR"
              ].map((topic, i) => (
                <button 
                  key={i} 
                  className="topic-chip"
                  onClick={() => handleSend(topic)}
                >
                  {topic}
                </button>
              ))}
            </div>

            <div className="info-card" style={{ marginTop: '2rem' }}>
              <h3><Upload size={14} /> KNOWLEDGE BASE</h3>
              <p>Add official PDFs to extend the system's intelligence.</p>
              <label className="topic-chip" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '1rem', cursor: isUploading ? 'not-allowed' : 'pointer', opacity: isUploading ? 0.5 : 1 }}>
                <input 
                  type="file" 
                  accept=".pdf" 
                  style={{ display: 'none' }} 
                  onChange={handleFileUpload}
                  disabled={isUploading}
                />
                {isUploading ? <Loader2 size={16} className="animate-spin" /> : "Upload PDF"}
              </label>
            </div>
          </div>

          <div className="sidebar-footer">
            <div className="disclaimer-mini">
              <p>© 2024 JUDICIAL AI EXPLAINER</p>
              <p>PROCEDURAL GUIDANCE ONLY</p>
            </div>
          </div>
        </aside>

        <main className="chat-container">
          <header className="chat-header">
            <div className="header-left" style={{ display: 'flex', alignItems: 'center' }}>
              <button className="menu-toggle" onClick={() => setIsSidebarOpen(true)}>
                <Menu size={20} />
              </button>
              <div>
                <h1>PROCESS DASHBOARD</h1>
                <div className="status">
                  <div className="status-dot"></div>
                  <span>LOCAL INSTANCE READY</span>
                </div>
              </div>
            </div>
            <div className="header-right">
              <button id="clear-chat" onClick={clearChat} title="Delete History">
                <Trash2 size={18} />
              </button>
            </div>
          </header>

          <div className="chat-messages">
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div 
                  key={msg.id}
                  initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`message ${msg.role}`}
                >
                  <div className="message-content">
                    {msg.role === 'assistant' && msg.id !== 'welcome' && (
                      <div className="lang-picker">
                        <div className="lang-trigger">
                          <Languages size={14} />
                        </div>
                        <div className="lang-dropdown">
                          <div style={{ padding: '4px 8px', fontSize: '0.65rem', color: '#444', fontWeight: 'bold' }}>TRANSLATE TO:</div>
                          {["Hindi", "Marathi", "Bengali", "Tamil", "Telugu", "Gujarati", "English"].map(lang => (
                            <button key={lang} className="lang-option" onClick={() => handleTranslate(msg.id, lang)}>
                              {lang}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {msg.isTranslating ? (
                      <p><Loader2 size={12} className="animate-spin" /> Translating...</p>
                    ) : (
                      <p dangerouslySetInnerHTML={{ 
                        __html: (msg.content || "")
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\n/g, '<br>') 
                      }} />
                    )}
                    
                    {msg.role === 'assistant' && !msg.feedbackGiven && msg.id !== 'welcome' && (
                      <div className="feedback-tools">
                        <button onClick={() => sendFeedback(msg.id, 'pos')}><ThumbsUp size={12} /></button>
                        <button onClick={() => sendFeedback(msg.id, 'neg')}><ThumbsDown size={12} /></button>
                      </div>
                    )}
                    {msg.feedbackGiven && (
                      <div className="feedback-tools">
                        <span style={{ fontSize: '0.75rem', color: 'var(--primary)' }}>
                          Feedback saved! {msg.feedbackGiven === 'pos' ? '👍' : '👎'}
                        </span>
                      </div>
                    )}
                  </div>

                  <CaseFlow stages={msg.flow} />

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources">
                      {Array.from(new Set(msg.sources.map(s => `${s.metadata.source}-${s.metadata.page}`)))
                        .map((key, i) => {
                          const source = msg.sources.find(s => `${s.metadata.source}-${s.metadata.page}` === key);
                          return (
                            <span key={i} className="source-tag">
                              <FileText size={10} /> {source.metadata.source}
                            </span>
                          );
                        })
                      }
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            
            {isProcessing && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="message assistant">
                <div className="message-content">
                  <p><Loader2 size={14} className="animate-spin" style={{ display: 'inline', marginRight: '8px' }} /> {agentStatus}</p>
                </div>
              </motion.div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="input-container">
            <div className="disclaimer-banner">
              NON-ADVISORY • PROCEDURAL ONLY • NO LEGAL PRIVILEGE
            </div>
            <div className="input-wrapper">
              <textarea 
                placeholder="Query judicial database..." 
                rows="1"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
              />
              <button 
                className="send-btn" 
                disabled={!input.trim() || isProcessing}
                onClick={() => handleSend()}
              >
                {isProcessing ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
