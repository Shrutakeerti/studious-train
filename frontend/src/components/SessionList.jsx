import { Link } from "react-router-dom";
import { StatusStamp } from "./Common.jsx";

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
    " · " +
    d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export default function SessionList({ sessions }) {
  if (!sessions || sessions.length === 0) {
    return (
      <div className="folder">
        <div className="empty-state">
          <div className="empty-state-title">No sessions yet</div>
          <p>Start your first research session above to build a briefing.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="folder">
      <div className="folder-tab">
        <span className="folder-tab-title">Session history</span>
        <span className="eyebrow" style={{ margin: 0 }}>{sessions.length} total</span>
      </div>
      <div>
        {sessions.map((s) => (
          <Link key={s.id} to={`/sessions/${s.id}`} className="session-row">
            <div className="session-row-main">
              <p className="session-row-company">{s.company_name}</p>
              <p className="session-row-objective">{s.objective}</p>
            </div>
            <div className="session-row-meta">
              <span className="session-row-date">{formatDate(s.created_at)}</span>
              <StatusStamp status={s.status} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
