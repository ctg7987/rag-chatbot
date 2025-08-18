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
    <main className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">RAG Chatbot</h1>
      <div className="mb-4 flex gap-2 items-center">
        <input
          type="file"
          multiple
          onChange={onUpload}
          className="border p-2"
        />
      </div>
      <div className="border rounded p-3 min-h-[240px]">
        {messages.map((m, i) => (
          <div key={i} className="mb-3">
            <Message role={m.role} content={m.content} />
            {m.role === "assistant" && m.citations && m.citations.length > 0 && (
              <div className="flex gap-2 flex-wrap mt-1">
                {m.citations.map((c: Source, j: number) => (
                  <React.Fragment key={j}>
                    <SourceCard source={c} />
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onAsk()}
          placeholder="Ask a question about your docs..."
          className="flex-1 border p-2 rounded"
        />
        <button onClick={onAsk} className="border px-3 py-2 rounded">
          Ask
        </button>
      </div>
    </main>
  );
}
