"use client";
import React, { useState, useRef, useEffect } from "react";
import Message from "@/components/Message";
import SourceCard, { type Source } from "@/components/SourceCard";

type Msg = { role: "user" | "assistant"; content: string; citations?: any[] };

export default function Page() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function onAsk() {
    const q = input.trim();
    if (!q) return;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");

    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    });

    // placeholder assistant message
    setMessages((m) => [...m, { role: "assistant", content: "" }]);

    let partial = "";
    let finalAnswer = "";
    let citations: Source[] = [] as any;
    if (res.body) {
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        partial += decoder.decode(value, { stream: true });
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { ...copy[copy.length - 1], content: partial } as Msg;
          return copy;
        });
      }
      try {
        const data = JSON.parse(partial);
        finalAnswer = data.answer || "";
        citations = data.citations || [];
      } catch {
        finalAnswer = partial;
      }
    } else {
      const data = await res.json();
      finalAnswer = data.answer || "";
      citations = data.citations || [];
    }

    setMessages((m) => {
      const copy = [...m];
      copy[copy.length - 1] = { role: "assistant", content: finalAnswer, citations } as any;
      return copy;
    });
  }

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const fd = new FormData();
    for (const f of Array.from(files as FileList)) fd.append("files", f as File);
    await fetch("/api/upload", { method: "POST", body: fd });
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white">
      <main className="container mx-auto px-6 py-12 max-w-4xl">
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold text-purple-800 mb-4">RAG Chatbot</h1>
          <p className="text-xl text-purple-600">Upload documents and ask questions</p>
        </div>
        
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-purple-800 mb-4">Upload Documents</h2>
            <div className="flex justify-center">
              <label className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-4 px-8 rounded-xl cursor-pointer text-lg transition-colors duration-200 shadow-lg">
                Choose Files
                <input
                  type="file"
                  multiple
                  onChange={onUpload}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-semibold text-purple-800 mb-6 text-center">Chat</h2>
          <div className="border-2 border-purple-200 rounded-xl p-6 min-h-[400px] bg-purple-50">
            {messages.length === 0 ? (
              <div className="text-center text-purple-600 text-lg">
                Start a conversation by asking a question!
              </div>
            ) : (
              messages.map((m, i) => (
                <div key={i} className="mb-6">
                  <Message role={m.role} content={m.content} />
                  {m.role === "assistant" && m.citations && m.citations.length > 0 && (
                    <div className="flex gap-2 flex-wrap mt-2">
                      {m.citations.map((c: Source, j: number) => (
                        <React.Fragment key={j}>
                          <SourceCard source={c} />
                        </React.Fragment>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex gap-4">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onAsk()}
              placeholder="Ask a question about your documents..."
              className="flex-1 border-2 border-purple-300 p-4 rounded-xl text-lg focus:border-purple-500 focus:outline-none"
            />
            <button 
              onClick={onAsk} 
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-4 px-8 rounded-xl text-lg transition-colors duration-200 shadow-lg"
            >
              Ask
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
