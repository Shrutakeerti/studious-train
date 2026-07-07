import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";
import ChatPanel from "./ChatPanel.jsx";
import { ErrorBanner, StatusStamp } from "./Common.jsx";
import ReportView from "./ReportView.jsx";
import WorkflowProgress from "./WorkflowProgress.jsx";

const POLL_INTERVAL_MS = 1500;

export default function SessionDetail() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [error, setError] = useState(null);
  const [rerunning, setRerunning] = useState(false);
  const pollRef = useRef(null);

  async function fetchSession() {
    try {
      const data = await api.getSession(sessionId);
      setSession(data);
      setError(null);
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const data = await fetchSession();
      if (cancelled) return;
      if (data && (data.status === "pending" || data.status === "running")) {
        pollRef.current = setTimeout(poll, POLL_INTERVAL_MS);
      }
    }
    poll();

    return () => {
      cancelled = true;
      clearTimeout(pollRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  async function handleRerun() {
    setRerunning(true);
    try {
      const data = await api.rerunSession(sessionId);
      setSession(data);
      pollRef.current = setTimeout(async function poll() {
        const d = await fetchSession();
        if (d && (d.status === "pending" || d.status === "running")) {
          pollRef.current = setTimeout(poll, POLL_INTERVAL_MS);
        }
      }, POLL_INTERVAL_MS);
    } catch (err) {
      setError(err.message);
    } finally {
      setRerunning(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this session permanently?")) return;
    try {
      await api.deleteSession(sessionId);
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  }

  if (error && !session) {
    return (
      <div>
        <Link to="/" className="back-link">← Back to sessions</Link>
        <div style={{ marginTop: 16 }}>
          <ErrorBanner message={error} onRetry={fetchSession} />
        </div>
      </div>
    );
  }

  if (!session) {
    return <p style={{ color: "var(--muted)" }}>Loading session…</p>;
  }

  const isActive = session.status === "pending" || session.status === "running";

  return (
    <div>
      <Link to="/" className="back-link">← Back to sessions</Link>

      <div className="top-actions" style={{ marginTop: 12 }}>
        <div>
          <p className="eyebrow">Case file · {session.id}</p>
          <h1 className="page-title">{session.company_name}</h1>
        </div>
        <StatusStamp status={session.status} />
      </div>

      <div className="session-meta-row">
        <span><strong>Objective:</strong> {session.objective}</span>
        {session.website && <span><strong>Website:</strong> {session.website}</span>}
      </div>

      <ErrorBanner message={error} />

      {session.status === "failed" && (
        <ErrorBanner
          message={session.error_message || "The research workflow failed unexpectedly."}
        />
      )}

      <div style={{ marginBottom: 20 }}>
        <WorkflowProgress
          steps={session.steps}
          status={session.status}
          currentNode={session.current_node}
        />
      </div>

      {session.status === "completed" && session.report && (
        <div style={{ marginBottom: 20 }}>
          <ReportView report={session.report} />
        </div>
      )}

      <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
        <button className="btn btn-ghost" onClick={handleRerun} disabled={rerunning || isActive}>
          {rerunning ? "Restarting…" : "Re-run research"}
        </button>
        <button className="btn btn-danger" onClick={handleDelete}>
          Delete session
        </button>
      </div>

      {session.status === "completed" && <ChatPanel sessionId={session.id} />}
    </div>
  );
}
