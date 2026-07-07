# Product & Business Thinking

## Weaknesses in the current design

1. **Research is limited to one website and the model's own knowledge.** There's no
   news search, LinkedIn/company-database lookup, or recent-funding/hiring signal
   source. For a company with a thin website, the report will be thin, and "Business
   Signals" in particular will often be underwhelming or generic.

2. **No source-level confidence or citation linking.** The report lists sources as a
   flat list ("company website", "general knowledge") rather than attributing each
   individual claim to where it came from. A seller can't tell which sentence in the
   overview came from the actual site versus the model's prior knowledge, which matters
   a lot if they're about to repeat it to a prospect.

3. **No team or organization features.** Sessions belong to an individual user, but
   there's no concept of an organization, shared session history across a sales team,
   or the ability for a manager to see what research their reps have run.

4. **No editing of the generated report.** Once generated, the report is read-only
   (aside from asking the chat follow-up). A seller who spots something wrong or wants
   to add a note has no way to annotate or correct the report in place — they'd have to
   just remember the correction going into the call.

5. **No re-use across similar research objectives.** If a seller researches the same
   company twice for two different deals, or a whole team researches companies in the
   same vertical, none of that prior research is surfaced or reused — every session
   starts from zero.

6. **Chat can't trigger new research.** If a follow-up question needs information not in
   the original report (e.g. "who is their VP of Ops?"), the chat node can only reason
   over the existing report — it has no way to kick off a targeted mini-research pass.

7. **No cost/latency visibility to the user.** The user has no sense of how long the
   workflow will take or what it costs to run (LLM calls), which matters a lot once this
   is a real paid feature.

## Top 3 priorities to build next

1. **Add a real research/search step.** This is the single highest-leverage fix — it
   directly improves report quality on every dimension (Business Signals, Risks, even
   Discovery Questions), and slots cleanly into the existing graph as a new node between
   `plan_research` and `analyze_company` without restructuring anything else.

2. **Per-claim source attribution.** Have `analyze_company` and `assess_business` return
   sources tied to individual claims (not just a global list) so a seller can trust and
   verify specific statements before repeating them to a prospect. This is a trust and
   liability issue as much as a UX one — the worst outcome for this product is a seller
   confidently stating something wrong in a live meeting.

3. **Editable report + team session sharing.** Let a user correct or annotate the
   generated report, and give teams a shared session view keyed by company name so
   research isn't re-done from scratch. This turns the tool from "a one-off report
   generator" into a living, reusable research asset for a sales org.

---

## Bonus: business thinking

**Who buys, who uses, why they'd pay.** The buyer is a sales or RevOps leader (VP of
Sales, Sales Enablement) who wants their team spending less time on manual pre-call
research and showing up to meetings better prepared. The day-to-day user is an
individual AE or SDR. They'd pay because manual account research (LinkedIn digging,
reading the "About" page, guessing at pain points) is a real, recurring time cost per
meeting, and a mediocre discovery call is a lost or delayed deal — the ROI case is
"save 20–30 minutes per meeting and show up sharper," multiplied across every rep's
every meeting per week.

**Success metrics.** Leading indicators: sessions created per active user per week,
% of sessions where the user opens follow-up chat (signals the report was trusted
enough to dig deeper into), time-to-first-report. Lagging/business indicators: seller
self-reported meeting-prep time saved, and ideally a downstream link to win-rate or
meeting-to-next-step conversion for meetings that used a briefing versus ones that
didn't.

**Biggest cost, scaling, and reliability risks.** Cost: LLM spend scales linearly with
sessions, and generating a full report is currently 4–5 sequential LLM calls (plus
possible retries) — that's meaningfully more expensive per session than a single call,
so unit economics need real attention as usage grows. Scaling: `BackgroundTasks` and
SQLite are fine for a prototype but won't survive concurrent load or multi-instance
deployment — a durable task queue and a real database are required before this can be a
multi-tenant product. Reliability: the product's core value proposition is trustworthy
research; a hallucinated fact stated confidently in a live sales call is the worst
failure mode, worse than the tool being slow or occasionally down.

**What I'd remove.** The "re-run research" button as currently implemented — it
silently discards the entire previous report and steps rather than versioning or diffing
against the prior run, which risks losing research a seller already relied on or shared.

**What I'd add.** A "brief me" mode: a condensed, scan-in-30-seconds summary view at the
top of the report (3 bullets: who they are, what to lead with, biggest risk) for a
seller checking the tool 5 minutes before a call, with the full 9-section report
available below for anyone with more prep time.

**What I'd change first if I owned this product.** I'd prioritize the real search/data
source integration (#1 above) over any UI polish — right now the product's report
quality is capped by what a single company website says, and no amount of frontend
work fixes that ceiling.