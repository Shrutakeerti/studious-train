import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { ErrorBanner } from "./Common.jsx";
import SessionForm from "./SessionForm.jsx";
import SessionList from "./SessionList.jsx";

export default function HomePage() {
  const [sessions, setSessions] = useState(null);
  const [error, setError] = useState(null);

  async function load() {
    try {
      const data = await api.listSessions();
      setSessions(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    const list = sessions || [];
    return {
      total: list.length,
      completed: list.filter((s) => s.status === "completed").length,
      running: list.filter((s) => s.status === "running" || s.status === "pending").length,
      failed: list.filter((s) => s.status === "failed").length,
    };
  }, [sessions]);

  return (
    <div>
      <p className="eyebrow">Sales research copilot</p>
      <h1 className="page-title">Prepare for your next meeting</h1>
      <p className="page-sub">
        Give the copilot a company and an objective — it researches, drafts a structured
        briefing, and stays on hand for follow-up questions.
      </p>

      {sessions && sessions.length > 0 && (
        <div className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total sessions</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.completed}</div>
            <div className="stat-label">Completed</div>
          </div>
          <div className="stat-card stat-running">
            <div className="stat-value">{stats.running}</div>
            <div className="stat-label">In progress</div>
          </div>
          <div className="stat-card stat-failed">
            <div className="stat-value">{stats.failed}</div>
            <div className="stat-label">Failed</div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: 28 }}>
        <SessionForm />
      </div>

      <ErrorBanner message={error} onRetry={load} />
      {sessions === null && !error ? (
        <p style={{ color: "var(--muted)" }}>Loading sessions…</p>
      ) : (
        <SessionList sessions={sessions} />
      )}
    </div>
  );
}