import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, PageHeader, Notice, Ring } from "../components/common/Ui";

const daysLeft = (date) => Math.ceil((new Date(date) - new Date()) / 86400000);

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

export default function Dashboard() {
  const [courses, setCourses] = useState([]);
  const [summary, setSummary] = useState(null);
  const [weak, setWeak] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        setCourses(await api("/courses"));
        setSummary(await api("/tasks/summary"));
        setWeak((await api("/progress/weak-topics")).weak_topics);
        setUpcoming((await api("/tasks?status=pending")).slice(0, 5));
      } catch (e) {
        setError("Error: " + e.message);
      }
    }
    load();
  }, []);

  return (
    <>
      <PageHeader title={`${greeting()}!`} subtitle="Here is where your studies stand today." />
      <Notice text={error} />

      <div className="grid grid-4" style={{ marginBottom: 18 }}>
        {[
          ["Courses", courses.length],
          ["Pending", summary?.pending ?? 0],
          ["Done", summary?.done ?? 0],
          ["Missed", summary?.missed ?? 0],
        ].map(([label, value]) => (
          <div key={label} className="card stat"><b>{value}</b><span>{label}</span></div>
        ))}
      </div>

      <div className="grid two">
        <Card title="Completion" icon="check">
          <div className="row" style={{ justifyContent: "center" }}>
            <Ring value={summary?.completion_rate ?? null} label="of finished tasks" />
          </div>
        </Card>

        <Card title="Upcoming exams" icon="calendar">
          {courses.length === 0 && <p className="muted">No courses yet. Add one in the Planner.</p>}
          {courses.map((c) => (
            <div key={c.id} className="task">
              <span className="task-main"><b>{c.name}</b><br /><small>{c.exam_date}</small></span>
              <span className={`badge ${daysLeft(c.exam_date) <= 7 ? "weak" : "pending"}`}>
                {daysLeft(c.exam_date)} days
              </span>
            </div>
          ))}
        </Card>
      </div>

      <Card title="Next tasks" icon="calendar">
        {upcoming.length === 0 && <p className="muted">No pending tasks.</p>}
        {upcoming.map((t) => (
          <div key={t.id} className="task">
            <span className="dot pending" />
            <span className="task-main"><b>{t.topic}</b> <small>{t.course}</small></span>
            <small>{t.date} - {t.hours}h</small>
          </div>
        ))}
      </Card>

      <Card title="Topics that need attention" icon="zap">
        {weak.length === 0 && <p className="muted">Nothing is flagged right now.</p>}
        {weak.map((w) => (
          <div key={w.topic_id} className="task">
            <span className="dot missed" />
            <span className="task-main"><b>{w.topic}</b><br /><small>{w.reasons.join(", ")}</small></span>
          </div>
        ))}
      </Card>
    </>
  );
}