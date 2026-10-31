import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Badge, Bar, Card, PageHeader, Notice, Ring } from "../components/common/Ui";

const BAR_COLOR = {
  weak: "linear-gradient(90deg,#f87171,#fb923c)",
  untested: "linear-gradient(90deg,#fbbf24,#fde68a)",
  on_track: "linear-gradient(90deg,#34d399,#22d3ee)",
};

const daysLeft = (date) => Math.ceil((new Date(date) - new Date()) / 86400000);

export default function CourseDetail() {
  const [courses, setCourses] = useState([]);
  const [courseId, setCourseId] = useState("");
  const [topics, setTopics] = useState([]);   
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState("");

  // Load the course list once and pick the first course
  useEffect(() => {
    api("/courses")
      .then((list) => {
        setCourses(list);
        if (list.length > 0) setCourseId(list[0].id);
      })
      .catch((e) => setError("Error: " + e.message));
  }, []);

  // Load the details whenever the selected course changes
  useEffect(() => {
    if (!courseId) return;
    async function load() {
      try {
        const report = await api("/progress/topics");
        setTopics(report.filter((r) => r.course_id === courseId));
        setTasks(await api(`/tasks?course_id=${courseId}`));
        setError("");
      } catch (e) {
        setError("Error: " + e.message);
      }
    }
    load();
  }, [courseId]);

  const course = courses.find((c) => c.id === courseId);
  const done = tasks.filter((t) => t.status === "done").length;
  const completion = tasks.length ? done / tasks.length : null;
  const hoursLeft = tasks
    .filter((t) => t.status === "pending")
    .reduce((sum, t) => sum + t.hours, 0);

  return (
    <>
      <PageHeader title="Course Details" subtitle="Everything about one course in a single place." />
      <Notice text={error} />

      {courses.length === 0 && (
        <Card><p className="muted">No courses yet. Add one in the Planner tab.</p></Card>
      )}

      {courses.length > 0 && (
        <>
          <Card>
            <select className="input" value={courseId} onChange={(e) => setCourseId(e.target.value)}>
              {courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </Card>

          {course && (
            <div className="grid two">
              <Card title="Exam" icon="calendar">
                <p style={{ fontSize: 34, fontWeight: 700 }}>{daysLeft(course.exam_date)} days</p>
                <p className="muted">until {course.exam_date}</p>
                <p style={{ marginTop: 10 }}>
                  <b>{hoursLeft}h</b> of study still planned
                </p>
              </Card>

              <Card title="Plan completion" icon="check">
                <div className="row" style={{ justifyContent: "center" }}>
                  <Ring value={completion} size={120} label={`${done}/${tasks.length} tasks`} />
                </div>
              </Card>
            </div>
          )}

          <Card title="Topics" icon="chart">
            {topics.length === 0 && <p className="muted">No topics in this course yet.</p>}
            {topics.map((r) => (
              <div key={r.topic_id} style={{ marginBottom: 18 }}>
                <div className="row between" style={{ marginBottom: 6 }}>
                  <b>{r.topic}</b>
                  <Badge kind={r.status}>{r.status.replace("_", " ")}</Badge>
                </div>
                <Bar value={r.accuracy} color={BAR_COLOR[r.status]} />
                <small>
                  {r.questions_answered} answered, accuracy{" "}
                  {r.accuracy === null ? "n/a" : `${Math.round(r.accuracy * 100)}%`}, {r.missed_tasks} missed tasks
                  {r.reasons.length > 0 && ` - ${r.reasons.join(", ")}`}
                </small>
              </div>
            ))}
          </Card>

          <Card title="Tasks" icon="calendar">
            {tasks.length === 0 && <p className="muted">No tasks for this course yet.</p>}
            {tasks.map((t) => (
              <div key={t.id} className="task">
                <span className={`dot ${t.status}`} />
                <span className="task-main"><b>{t.topic}</b><br /><small>{t.date} - {t.hours}h</small></span>
                <Badge kind={t.status}>{t.status}</Badge>
              </div>
            ))}
          </Card>
        </>
      )}
    </>
  );
}