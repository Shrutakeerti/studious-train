import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { ErrorBanner } from "./Common.jsx";

export default function SessionForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ company_name: "", website: "", objective: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.company_name.trim() || !form.objective.trim()) {
      setError("Company name and research objective are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const session = await api.createSession({
        company_name: form.company_name.trim(),
        website: form.website.trim() || null,
        objective: form.objective.trim(),
      });
      navigate(`/sessions/${session.id}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="folder">
      <div className="folder-tab">
        <span className="folder-tab-title">New research session</span>
        <span className="eyebrow" style={{ margin: 0 }}>
          Case file — draft
        </span>
      </div>
      <div className="folder-body">
        <ErrorBanner message={error} />
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="company_name">Company name</label>
            <input
              id="company_name"
              placeholder="e.g. Acme Logistics"
              value={form.company_name}
              onChange={(e) => update("company_name", e.target.value)}
              maxLength={200}
              autoFocus
            />
          </div>
          <div className="field">
            <label htmlFor="website">Company website (optional)</label>
            <input
              id="website"
              placeholder="e.g. acmelogistics.com"
              value={form.website}
              onChange={(e) => update("website", e.target.value)}
              maxLength={500}
            />
            <div className="hint">
              If provided, the copilot will fetch and read the site as part of research.
            </div>
          </div>
          <div className="field">
            <label htmlFor="objective">Research objective</label>
            <textarea
              id="objective"
              placeholder="e.g. Prepare for a discovery call about their warehouse automation needs"
              value={form.objective}
              onChange={(e) => update("objective", e.target.value)}
              maxLength={1000}
            />
          </div>
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? "Starting workflow…" : "Start research"}
          </button>
        </form>
      </div>
    </div>
  );
}
