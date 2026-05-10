"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { chatApi } from "@/lib/api";
import type { ChatMessage, ChatRequest } from "@/types/agent";

interface ChatAgentProps {
  repoId: string;
}

export function ChatAgent({ repoId }: ChatAgentProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setError(null);

    const payload: ChatRequest = {
      message: userMessage.content,
      conversationHistory: messages,
      repoScope: [repoId],
    };

    try {
      const reply = await chatApi.send(payload);
      setMessages((prev) => [...prev, reply]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get response");
    } finally {
      setLoading(false);
    }
  }

  const EXAMPLE_QUERIES = [
    "Which images have critical CVEs?",
    "What would my image size be with distroless?",
    "Show me all high severity findings from this week",
    "Has this CVE appeared in other images?",
  ];

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl flex flex-col h-[600px]">
      <div className="px-5 py-4 border-b border-surface-border flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-accent-purple/10 border border-accent-purple/30 flex items-center justify-center">
          <div className="w-3 h-3 rounded-full bg-accent-purple/50" />
        </div>
        <div>
          <p className="text-sm font-semibold text-text-primary">Chat Agent</p>
          <p className="text-xs text-text-secondary">ReAct pattern with full scan context</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="py-8 space-y-4">
            <p className="text-text-secondary text-sm text-center">
              Ask anything about your scan results
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {EXAMPLE_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="text-left px-3 py-2.5 rounded-lg border border-surface-border text-xs text-text-secondary hover:text-text-primary hover:border-surface-border-bright hover:bg-bg-elevated transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-accent-cyan/10 border border-accent-cyan/20 text-text-primary"
                  : "bg-bg-elevated border border-surface-border text-text-primary"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-surface-border">
                  <p className="text-xs text-text-muted">
                    Sources: {msg.sources.join(", ")}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-bg-elevated border border-surface-border rounded-xl px-4 py-3">
              <div className="flex items-center gap-1.5">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-accent-purple animate-bounce"
                    style={{ animationDelay: `${i * 150}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="text-xs text-accent-red text-center">{error}</div>
        )}

        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={sendMessage}
        className="px-4 py-3 border-t border-surface-border flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your scan results..."
          className="flex-1 px-3 py-2 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm focus:outline-none focus:border-accent-purple/60 transition-colors"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded-lg bg-accent-purple text-white text-sm font-semibold hover:bg-accent-purple-dim transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
}
