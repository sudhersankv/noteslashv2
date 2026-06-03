"use client";

import { useEffect, useRef, useState } from "react";
import { api, ChatMessage, Citation } from "@/lib/api";
import { Button } from "./ui/button";
import { Spinner } from "./ui/spinner";

const STARTERS = [
  "What are the main topics covered?",
  "Summarize the key takeaways.",
  "What stood out most?",
];

export function ChatPanel({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.chatHistory(projectId).then((r) => setMessages(r.messages)).catch(() => {});
  }, [projectId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    setLoading(true);
    setError(null);
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: text.trim(),
      citations: [],
    };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    try {
      const res = await api.chat(projectId, text.trim());
      const assistant: ChatMessage = {
        id: res.message_id || `a-${Date.now()}`,
        role: "assistant",
        content: res.answer,
        citations: res.citations,
      };
      setMessages((m) => [...m, assistant]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[520px] flex-col">
      <p className="mb-3 text-sm text-neutral-600">
        Ask anything about your library. Answers include cited passages from your content.
      </p>
      <div className="mb-2 flex flex-wrap gap-2">
        {STARTERS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => send(s)}
            className="rounded-full border border-neutral-200 bg-white px-3 py-1 text-xs hover:bg-neutral-50"
          >
            {s}
          </button>
        ))}
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto rounded-lg border border-neutral-200 bg-white p-4">
        {messages.length === 0 && (
          <p className="text-sm text-neutral-400">Start a conversation about your content.</p>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {loading && (
          <div className="flex justify-center py-2">
            <Spinner className="h-5 w-5" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
          placeholder="Ask Noteslash…"
          className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm"
        />
        <Button onClick={() => send(input)} disabled={loading}>
          Send
        </Button>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
          isUser ? "bg-neutral-900 text-white" : "bg-neutral-100 text-neutral-900"
        }`}
      >
        <p>{message.content}</p>
        {!isUser && message.citations.length > 0 && (
          <div className="mt-2 space-y-1 border-t border-neutral-200 pt-2">
            {message.citations.map((c: Citation) => (
              <p key={c.chunk_id} className="text-xs text-neutral-600">
                <span className="font-medium">{c.filename || "source"}:</span> &ldquo;
                {c.text.slice(0, 120)}
                {c.text.length > 120 ? "…" : ""}&rdquo;
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
