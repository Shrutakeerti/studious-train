const NODE_SEQUENCE = [
  { key: "plan_research", label: "Planning research approach", short: "Plan" },
  { key: "fetch_website", label: "Fetching company website", short: "Fetch" },
  { key: "analyze_company", label: "Analyzing company overview & products", short: "Analyze" },
  { key: "assess_business", label: "Assessing business signals & risks", short: "Assess" },
  { key: "quality_check", label: "Reviewing research quality", short: "Quality" },
  { key: "generate_report", label: "Generating final report", short: "Report" },
];

function iconFor(status) {
  if (status === "completed") return "✓";
  if (status === "failed") return "!";
  if (status === "running") return "…";
  return "";
}

function formatTime(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function WorkflowProgress({ steps, status, currentNode }) {
  const byNode = {};
  (steps || []).forEach((s) => {
    byNode[s.node_name] = s;
  });

  const retryHappened = (steps || []).some((s) => s.node_name === "increment_retry");

  function statusOf(nodeKey) {
    const record = byNode[nodeKey];
    if (record) return record.status;
    if (status === "running" && currentNode === nodeKey) return "running";
    return "pending";
  }

  return (
    <div className="folder">
      <div className="folder-tab">
        <span className="folder-tab-title">Workflow progress</span>
        <span className="eyebrow" style={{ margin: 0 }}>LangGraph run log</span>
      </div>
      <div className="folder-body">
        <div className="node-flow">
          {NODE_SEQUENCE.map((n, i) => (
            <span key={n.key} style={{ display: "flex", alignItems: "center" }}>
              <span className={`node-chip ${statusOf(n.key)}`}>{n.short}</span>
              {i < NODE_SEQUENCE.length - 1 && <span className="node-arrow">→</span>}
            </span>
          ))}
          {retryHappened && (
            <>
              <span className="node-arrow">↺</span>
              <span className="node-chip completed">Retry: Analyze</span>
              <span className="node-arrow">→</span>
            </>
          )}
        </div>

        <ul className="timeline">
          {NODE_SEQUENCE.map((n) => {
            const record = byNode[n.key];
            const nodeStatus = statusOf(n.key);

            return (
              <li className="timeline-item" key={n.key}>
                <span className={`timeline-dot ${nodeStatus}`}>{iconFor(nodeStatus)}</span>
                <div className="timeline-label">{n.label}</div>
                {record?.finished_at && (
                  <div className="timeline-time">{formatTime(record.finished_at)}</div>
                )}
                {record?.status === "failed" && (
                  <div className="timeline-time" style={{ color: "var(--alert)" }}>
                    Node reported an error — pipeline continued with fallback content.
                  </div>
                )}
              </li>
            );
          })}
        </ul>
        {retryHappened && (
          <p className="quality-note">
            Quality reviewer requested a refinement pass — company analysis was re-run once before the final report was generated.
          </p>
        )}
      </div>
    </div>
  );
}