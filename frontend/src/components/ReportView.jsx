function Section({ idx, icon, title, wide, children }) {
  return (
    <div className={`report-section${wide ? " wide" : ""}`}>
      <div className="report-section-head">
        <span className="idx">{idx}</span>
        <span className="icon">{icon}</span>
        <span className="report-section-title">{title}</span>
      </div>
      <div className="report-section-body">{children}</div>
    </div>
  );
}

function ListOrEmpty({ items, emptyText }) {
  if (!items || items.length === 0) {
    return <p style={{ color: "var(--muted)" }}>{emptyText}</p>;
  }
  return (
    <ul>
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

export default function ReportView({ report }) {
  if (!report) return null;

  return (
    <div>
      <div className="report-grid">
        <Section idx="01" icon="◆" title="Company overview" wide>
          <p>{report.company_overview || "Not available."}</p>
        </Section>

        <Section idx="02" icon="▣" title="Products & services">
          <ListOrEmpty items={report.products_services} emptyText="No products/services identified." />
        </Section>

        <Section idx="03" icon="◎" title="Target customers">
          <ListOrEmpty items={report.target_customers} emptyText="No target customer segments identified." />
        </Section>

        <Section idx="04" icon="↗" title="Business signals">
          <ListOrEmpty items={report.business_signals} emptyText="No notable business signals surfaced." />
        </Section>

        <Section idx="05" icon="⚠" title="Risks & challenges">
          <ListOrEmpty items={report.risks_challenges} emptyText="No specific risks surfaced." />
        </Section>

        <Section idx="06" icon="?" title="Suggested discovery questions" wide>
          <ListOrEmpty items={report.discovery_questions} emptyText="No discovery questions generated." />
        </Section>

        <Section idx="07" icon="➤" title="Suggested outreach strategy" wide>
          <p>{report.outreach_strategy || "Not available."}</p>
        </Section>

        <Section idx="08" icon="…" title="Unknowns">
          <ListOrEmpty items={report.unknowns} emptyText="No open unknowns flagged." />
        </Section>

        <Section idx="09" icon="※" title="Sources">
          <ListOrEmpty items={report.sources} emptyText="No sources recorded." />
        </Section>
      </div>

      {report.quality && (
        <p className="quality-note">
          Quality confidence: {report.quality.confidence != null ? Math.round(report.quality.confidence * 100) + "%" : "n/a"}
          {" · "}
          Refinement passes: {report.quality.retries ?? 0}
          {report.quality.feedback ? ` · Reviewer note: ${report.quality.feedback}` : ""}
        </p>
      )}
    </div>
  );
}