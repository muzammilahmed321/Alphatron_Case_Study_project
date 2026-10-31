import { useState } from "react";
import { sendJson } from "../api/client";
import Icon from "../components/common/Icon";
import { Card, PageHeader, Notice, Spinner } from "../components/common/Ui";

const STEPS = ["Analyze", "Retrieve", "Plan", "Validate", "Review"];

export default function PlanReview() {
  const [dailyHours, setDailyHours] = useState(3);
  const [today, setToday] = useState("");      // optional: pretend it is a later date
  const [state, setState] = useState(null);    // the agent's last response
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    setError("");
    setState(null);
    try {
      const body = { daily_hours: Number(dailyHours) };
      if (today) body.today = today;
      setState(await sendJson("/agent/run", body));
    } catch (e) {
      setError("Error: " + e.message);
    }
    setLoading(false);
  }

  async function decide(approve) {
    setLoading(true);
    setError("");
    try {
      setState(await sendJson(`/agent/${state.thread_id}/decision`, { approve }));
    } catch (e) {
      setError("Error: " + e.message);
    }
    setLoading(false);
  }

  // Decide how each step in the pipeline graphic should look
  const waiting = state?.status === "waiting_for_approval";
  const finished = state?.status === "finished";
  const stepClass = (i) => {
    if (loading) return "";
    if (finished) return i < 4 && state.route === "revise" ? "done" : "";
    if (waiting) return i < 4 ? "done" : "now";
    return "";
  };

  return (
    <>
      <PageHeader title="Recovery Agent" subtitle="The agent finds weak topics, rebuilds your plan, and waits for your approval." />
      <Notice text={error} />

      <Card title="Run the agent" icon="zap">
        <div className={`pipeline ${loading ? "working" : ""}`}>
          {STEPS.map((s, i) => <span key={s} className={`step ${stepClass(i)}`}>{s}</span>)}
        </div>
        <p className="hint" style={{ marginTop: 14 }}>
          Tip: choosing a later date makes old pending tasks count as missed, so you can test it.
        </p>
        <div className="row">
          <input className="input num" type="number" min="0.5" step="0.5" value={dailyHours}
                 onChange={(e) => setDailyHours(e.target.value)} />
          <span className="muted">hours per day</span>
          <label className="muted">Pretend today is</label>
          <input className="input" type="date" value={today} onChange={(e) => setToday(e.target.value)} />
          <button className="btn btn-primary" onClick={run} disabled={loading}>
            {loading ? <Spinner /> : <Icon name="zap" size={16} />}
            {loading ? "Working..." : "Run agent"}
          </button>
        </div>
      </Card>

      {finished && (
        <Card title="Result" icon="check">
          <p>{state.message}</p>
          <small>Route taken: {state.route}</small>
        </Card>
      )}

      {waiting && (
        <Card title="Proposed new plan" icon="sparkle">
          <p className="answer">{state.explanation}</p>

          <div className="chips">
            {state.weak_topics.map((t) => <span key={t} className="chip">Weak: {t}</span>)}
          </div>

          {state.warnings.length > 0 && <div className="notice error" style={{ marginTop: 14 }}>{state.warnings.join(" ")}</div>}
          {state.problems.length > 0 && <div className="notice error" style={{ marginTop: 14 }}>{state.problems.join(" ")}</div>}

          {state.review_material.length > 0 && (
            <>
              <h4 style={{ margin: "18px 0 8px" }}>Review these pages</h4>
              <div className="chips">
                {state.review_material.map((m, i) => (
                  <span key={i} className="chip">{m.topic}: {m.source}, p.{m.page}</span>
                ))}
              </div>
            </>
          )}

          <h4 style={{ margin: "18px 0 8px" }}>New schedule</h4>
          {state.proposed_tasks.length === 0 && <p className="muted">No tasks proposed.</p>}
          {state.proposed_tasks.map((t, i) => (
            <div key={i} className="task">
              <span className="dot pending" />
              <span className="task-main"><b>{t.topic}</b> <small>{t.course}</small></span>
              <small>{t.date} - {t.hours}h</small>
            </div>
          ))}

          <div className="row" style={{ marginTop: 18 }}>
            <button className="btn btn-good" onClick={() => decide(true)} disabled={loading}>
              <Icon name="check" size={16} /> Approve
            </button>
            <button className="btn btn-bad" onClick={() => decide(false)} disabled={loading}>
              <Icon name="x" size={16} /> Reject
            </button>
          </div>
        </Card>
      )}
    </>
  );
}