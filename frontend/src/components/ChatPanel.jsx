import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { ErrorBanner, Spinner } from "./Common.jsx";

export default function ChatPanel({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const logRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getChatHistory(sessionId)
      .then((history) => {
        if (!cancelled) setMessages(history);
      })
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setMessages((m) => [...m, { role: "user", content: text, created_at: new Date().toISOString() }]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const reply = await api.sendChatMessage(sessionId, text);
      setMessages((m) => [...m, reply]);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="folder">
      <div className="folder-tab">
        <span className="folder-tab-title">Follow-up chat</span>
        <span className="eyebrow" style={{ margin: 0 }}>Grounded in this report</span>
      </div>
      <div className="folder-body">
        <ErrorBanner message={error} />
        {loading ? (
          <p style={{ color: "var(--muted)" }}>
            <Spinner /> Loading conversation…
          </p>
        ) : (
          <>
            <div className="chat-log" ref={logRef}>
              {messages.length === 0 && (
                <p style={{ color: "var(--muted)", fontSize: 13 }}>
                  Ask a follow-up — e.g. "What's the strongest talking point for the first call?"
                </p>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`chat-bubble ${m.role}`}>
                  <span className="chat-bubble-role">{m.role === "user" ? "You" : "Copilot"}</span>
                  {m.content}
                </div>
              ))}
              {sending && (
                <div className="chat-bubble assistant">
                  <span className="chat-bubble-role">Copilot</span>
                  <Spinner /> thinking…
                </div>
              )}
            </div>
            <form className="chat-input-row" onSubmit={handleSend}>
              <textarea
                placeholder="Ask about this company's report…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(e);
                  }
                }}
              />
              <button className="btn" type="submit" disabled={sending || !input.trim()}>
                Send
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
