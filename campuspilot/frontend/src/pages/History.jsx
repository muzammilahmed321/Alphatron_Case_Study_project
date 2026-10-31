import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Badge, Card, PageHeader, Notice } from "../components/common/Ui";

// Turns "2026-11-01T10:30:00" into something readable
const when = (iso) => (iso ? iso.replace("T", " ").slice(0, 16) : "");

export default function History() {
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/history").then(setHistory).catch((e) => setError("Error: " + e.message));
  }, []);

  return (
    <>
      <PageHeader title="Study History" subtitle="Your past quizzes, plan changes, and finished tasks." />
      <Notice text={error} />
      {!history && !error && <p className="muted">Loading...</p>}

      {history && (
        <>
          <Card title="Quiz attempts" icon="quiz">
            {history.quizzes.length === 0 && <p className="muted">No quizzes taken yet.</p>}
            {history.quizzes.map((q) => (
              <div key={q.quiz_id} className="task">
                <span className="task-main"><b>{q.topic}</b><br /><span className="time">{when(q.time)}</span></span>
                <b>{q.score}</b>
                <Badge kind={q.accuracy >= 0.6 ? "done" : "missed"}>{Math.round(q.accuracy * 100)}%</Badge>
              </div>
            ))}
          </Card>

          <Card title="Plan revisions by the agent" icon="zap">
            {history.revisions.length === 0 && <p className="muted">The recovery agent has not proposed any changes yet.</p>}
            {history.revisions.map((r) => (
              <div key={r.id} style={{ marginBottom: 16 }}>
                <div className="row between">
                  <span className="time">{when(r.time)} - {r.task_count} tasks proposed</span>
                  <Badge kind={r.status === "approved" ? "done" : r.status === "rejected" ? "missed" : "pending"}>
                    {r.status}
                  </Badge>
                </div>
                {r.weak_topics.length > 0 && (
                  <div className="chips">
                    {r.weak_topics.map((t) => <span key={t} className="chip">Weak: {t}</span>)}
                  </div>
                )}
                <p className="answer" style={{ marginTop: 8, fontSize: 14 }}>{r.explanation}</p>
              </div>
            ))}
          </Card>

          <Card title="Finished tasks" icon="check">
            {history.tasks.length === 0 && <p className="muted">No tasks marked done or missed yet.</p>}
            {history.tasks.map((t) => (
              <div key={t.id} className="task">
                <span className={`dot ${t.status}`} />
                <span className="task-main"><b>{t.topic}</b> <small>{t.course}</small><br />
                  <small>{t.date} - {t.hours}h</small></span>
                <Badge kind={t.status}>{t.status}</Badge>
              </div>
            ))}
          </Card>
        </>
      )}
    </>
  );
}