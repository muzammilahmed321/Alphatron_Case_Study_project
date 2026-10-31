import { useEffect, useState } from "react";
import { api } from "../api/client";
import Icon from "../components/common/Icon";
import { Badge, Bar, Card, PageHeader, Notice, Ring } from "../components/common/Ui";

const BAR_COLOR = {
  weak: "linear-gradient(90deg,#f87171,#fb923c)",
  untested: "linear-gradient(90deg,#fbbf24,#fde68a)",
  on_track: "linear-gradient(90deg,#34d399,#22d3ee)",
};

export default function Progress() {
  const [report, setReport] = useState([]);
  const [summary, setSummary] = useState(null);
  const [usage, setUsage] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setReport(await api("/progress/topics"));
      setSummary(await api("/tasks/summary"));
      setUsage(await api("/usage"));
      setError("");
    } catch (e) {
      setError("Error: " + e.message);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <>
      <PageHeader title="Progress" subtitle="Quiz accuracy, missed tasks, and what the AI has cost so far." />
      <Notice text={error} />

      <div className="grid two">
        <Card title="Study tasks" icon="check">
          {summary ? (
            <div className="row" style={{ justifyContent: "space-around" }}>
              <Ring value={summary.completion_rate} size={120} label="completion" />
              <div>
                <p>Pending <b>{summary.pending}</b></p>
                <p>Done <b>{summary.done}</b></p>
                <p>Missed <b>{summary.missed}</b></p>
              </div>
            </div>
          ) : <p className="muted">Loading...</p>}
        </Card>

        <Card title="AI usage" icon="zap">
          {usage && (
            <>
              <p><b>{usage.total_calls}</b> calls</p>
              <p><b>{usage.total_input_tokens + usage.total_output_tokens}</b> tokens</p>
              <p>About <b>${usage.total_cost_usd}</b></p>
              <div style={{ marginTop: 10 }}>
                {Object.entries(usage.by_feature).map(([name, f]) => (
                  <small key={name}>{name}: {f.calls} calls, avg {f.avg_seconds}s<br /></small>
                ))}
              </div>
            </>
          )}
        </Card>
      </div>

      <Card title="Topics" icon="chart">
        <div className="row" style={{ marginBottom: 14 }}>
          <button className="btn btn-sm" onClick={load}><Icon name="sparkle" size={14} /> Refresh</button>
        </div>
        {report.length === 0 && <p className="muted">No topics yet.</p>}
        {report.map((r) => (
          <div key={r.topic_id} style={{ marginBottom: 18 }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
              <b>{r.topic}</b>
              <Badge kind={r.status}>{r.status.replace("_", " ")}</Badge>
            </div>
            <Bar value={r.accuracy} color={BAR_COLOR[r.status]} />
            <small>
              {r.questions_answered} answered, accuracy {r.accuracy === null ? "n/a" : `${Math.round(r.accuracy * 100)}%`},
              {" "}{r.missed_tasks} missed tasks
              {r.reasons.length > 0 && ` - ${r.reasons.join(", ")}`}
            </small>
          </div>
        ))}
      </Card>
    </>
  );
}