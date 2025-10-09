"use client";
import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Message from "@/components/Message";
import SourceCard, { type Source } from "@/components/SourceCard";
import SessionList from "@/components/SessionList";
import DocumentList from "@/components/DocumentList";
import CitationModal from "@/components/CitationModal";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorToast from "@/components/ErrorToast";

type Msg = { 
  role: "user" | "assistant"; 
  content: string; 
  citations?: any[];
  message_id?: string;
};

type Session = {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export default function Page() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Source | null>(null);
  const [showSessions, setShowSessions] = useState(false);
  const [showDocuments, setShowDocuments] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [useHistory, setUseHistory] = useState(true);
  
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    loadSessions();
    loadDocuments();
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Load sessions
  const loadSessions = async () => {
    try {
      const res = await fetch("http://localhost:8000/sessions");
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };

  // Load documents
  const loadDocuments = async () => {
    try {
      const res = await fetch("http://localhost:8000/documents");
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  };

  // Create new session
  const createNewSession = async () => {
    try {
      const res = await fetch("http://localhost:8000/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Conversation" }),
      });
      
      if (res.ok) {
        const session = await res.json();
        setCurrentSessionId(session.session_id);
        setMessages([]);
        loadSessions();
      }
    } catch (err) {
      setError("Failed to create new session");
    }
  };

  // Load session messages
  const loadSession = async (sessionId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/sessions/${sessionId}/messages`);
      if (res.ok) {
        const msgs = await res.json();
        setMessages(msgs);
        setCurrentSessionId(sessionId);
        setShowSessions(false);
      }
    } catch (err) {
      setError("Failed to load session");
    }
  };

  // Delete session
  const deleteSession = async (sessionId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/sessions/${sessionId}`, {
        method: "DELETE",
      });
      
      if (res.ok) {
        if (currentSessionId === sessionId) {
          setCurrentSessionId(null);
          setMessages([]);
        }
        loadSessions();
      }
    } catch (err) {
      setError("Failed to delete session");
    }
  };

  // Delete document
  const deleteDocument = async (docId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/documents/${docId}`, {
        method: "DELETE",
      });
      
      if (res.ok) {
        loadDocuments();
      }
    } catch (err) {
      setError("Failed to delete document");
    }
  };

  // Ask question
  async function onAsk() {
    const q = input.trim();
    if (!q || loading) return;

    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          question: q,
          session_id: currentSessionId,
          use_history: useHistory
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      
      setMessages((m) => [...m, { 
        role: "assistant", 
        content: data.answer, 
        citations: data.citations 
      }]);
      
      // Update session ID if new
      if (data.session_id && !currentSessionId) {
        setCurrentSessionId(data.session_id);
        loadSessions();
      }
      
    } catch (err: any) {
      setError(err.message || "Failed to get answer");
      setMessages((m) => [...m, { 
        role: "assistant", 
        content: "Sorry, I encountered an error. Please try again." 
      }]);
    } finally {
      setLoading(false);
    }
  }

  // Upload files
  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setUploading(true);
    setError(null);
    
    try {
      const fd = new FormData();
      for (const f of Array.from(files as FileList)) {
        fd.append("files", f as File);
      }
      
      const res = await fetch("http://localhost:8000/ingest", { 
        method: "POST", 
        body: fd 
      });
      
      if (!res.ok) {
        throw new Error(`Upload failed: ${res.status}`);
      }
      
      const result = await res.json();
      setError(null);
      
      // Show success message
      setMessages((m) => [...m, { 
        role: "assistant", 
        content: `✅ Successfully uploaded ${result.files_processed} file(s) and indexed ${result.chunks_indexed} chunks!` 
      }]);
      
      // Reload documents
      loadDocuments();
      
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  const bgClass = darkMode 
    ? "min-h-screen bg-gradient-to-br from-gray-900 to-gray-800" 
    : "min-h-screen bg-gradient-to-br from-purple-50 to-white";
  
  const cardClass = darkMode
    ? "bg-gray-800 rounded-2xl shadow-xl p-8 mb-8 border border-gray-700"
    : "bg-white rounded-2xl shadow-xl p-8 mb-8";
  
  const textClass = darkMode ? "text-gray-100" : "text-purple-800";
  const subtextClass = darkMode ? "text-gray-300" : "text-purple-600";

  return (
    <div className={bgClass}>
      {/* Error Toast */}
      {error && <ErrorToast message={error} onClose={() => setError(null)} />}
      
      {/* Citation Modal */}
      {selectedCitation && (
        <CitationModal 
          citation={selectedCitation} 
          onClose={() => setSelectedCitation(null)} 
        />
      )}

      <main className="container mx-auto px-6 py-12 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-between items-center mb-4">
            <div className="flex gap-4">
              <button
                onClick={() => setShowSessions(!showSessions)}
                className={`px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-purple-100 hover:bg-purple-200'} transition-colors`}
              >
                📚 Sessions
              </button>
              <button
                onClick={() => setShowDocuments(!showDocuments)}
                className={`px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-purple-100 hover:bg-purple-200'} transition-colors`}
              >
                📄 Documents
              </button>
              <button
                onClick={createNewSession}
                className={`px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-purple-100 hover:bg-purple-200'} transition-colors`}
              >
                ➕ New Chat
              </button>
            </div>
            
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`px-4 py-2 rounded-lg ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-purple-100 hover:bg-purple-200'} transition-colors`}
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
          
          <h1 className={`text-6xl font-bold ${textClass} mb-4`}>RAG Chatbot</h1>
          <p className={`text-xl ${subtextClass}`}>Upload documents and ask questions</p>
          
          {currentSessionId && (
            <p className={`text-sm ${subtextClass} mt-2`}>
              Session: {currentSessionId.slice(0, 8)}...
            </p>
          )}
        </div>

        {/* Sessions Sidebar */}
        {showSessions && (
          <SessionList
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelectSession={loadSession}
            onDeleteSession={deleteSession}
            onClose={() => setShowSessions(false)}
            darkMode={darkMode}
          />
        )}

        {/* Documents Sidebar */}
        {showDocuments && (
          <DocumentList
            documents={documents}
            onDeleteDocument={deleteDocument}
            onClose={() => setShowDocuments(false)}
            darkMode={darkMode}
          />
        )}

        {/* Upload Section */}
        <div className={cardClass}>
          <div className="text-center mb-8">
            <h2 className={`text-2xl font-semibold ${textClass} mb-4`}>Upload Documents</h2>
            <div className="flex justify-center gap-4 items-center">
              <label className={`${darkMode ? 'bg-purple-700 hover:bg-purple-600' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-4 px-8 rounded-xl cursor-pointer text-lg transition-colors duration-200 shadow-lg ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                {uploading ? 'Uploading...' : 'Choose Files'}
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={onUpload}
                  className="hidden"
                  disabled={uploading}
                  accept=".pdf,.txt,.md,.markdown"
                />
              </label>
              
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useHistory}
                  onChange={(e) => setUseHistory(e.target.checked)}
                  className="w-5 h-5"
                />
                <span className={textClass}>Use conversation history</span>
              </label>
            </div>
          </div>
        </div>

        {/* Chat Section */}
        <div className={cardClass}>
          <h2 className={`text-2xl font-semibold ${textClass} mb-6 text-center`}>Chat</h2>
          <div className={`border-2 ${darkMode ? 'border-gray-600 bg-gray-900' : 'border-purple-200 bg-purple-50'} rounded-xl p-6 min-h-[400px] max-h-[600px] overflow-y-auto`}>
            {messages.length === 0 ? (
              <div className={`text-center ${subtextClass} text-lg`}>
                Start a conversation by asking a question!
              </div>
            ) : (
              messages.map((m, i) => (
                <div key={i} className="mb-6">
                  <Message role={m.role} content={m.content} darkMode={darkMode} />
                  {m.role === "assistant" && m.citations && m.citations.length > 0 && (
                    <div className="flex gap-2 flex-wrap mt-2">
                      {m.citations.map((c: Source, j: number) => (
                        <div key={j} onClick={() => setSelectedCitation(c)}>
                          <SourceCard source={c} darkMode={darkMode} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-center">
                <LoadingSpinner />
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input Section */}
        <div className={cardClass}>
          <div className="flex gap-4">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && onAsk()}
              placeholder="Ask a question about your documents..."
              className={`flex-1 border-2 ${darkMode ? 'border-gray-600 bg-gray-700 text-white placeholder-gray-400' : 'border-purple-300 bg-white'} p-4 rounded-xl text-lg focus:border-purple-500 focus:outline-none`}
              disabled={loading}
            />
            <button 
              onClick={onAsk} 
              disabled={loading || !input.trim()}
              className={`${darkMode ? 'bg-purple-700 hover:bg-purple-600' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-4 px-8 rounded-xl text-lg transition-colors duration-200 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {loading ? '...' : 'Ask'}
            </button>
          </div>
          <div className={`text-xs ${subtextClass} mt-2 text-center`}>
            Press Enter to send • Shift+Enter for new line
          </div>
        </div>
      </main>
    </div>
  );
}

