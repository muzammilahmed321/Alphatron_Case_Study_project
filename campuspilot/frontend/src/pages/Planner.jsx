import { useEffect, useState } from "react";
import { api, del, sendJson } from "../api/client";
import Icon from "../components/common/Icon";
import { Badge, Card, PageHeader, Notice } from "../components/common/Ui";

export default function Planner() {
  const [courses, setCourses] = useState([]);   
  const [tasks, setTasks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [message, setMessage] = useState("");

  // Add forms
  const [courseName, setCourseName] = useState("");
  const [examDate, setExamDate] = useState("");
  const [courseId, setCourseId] = useState("");
  const [topicName, setTopicName] = useState("");
  const [priority, setPriority] = useState(2);
  const [hours, setHours] = useState(2);
  const [dailyHours, setDailyHours] = useState(3);

  // Edit forms (null when nothing is being edited)
  const [editCourse, setEditCourse] = useState(null);   
  const [editTopic, setEditTopic] = useState(null);     

  async function load() {
    try {
      const list = await api("/courses");
      const withTopics = [];
      for (const c of list) {
        withTopics.push({ ...c, topics: await api(`/courses/${c.id}/topics`) });
      }
      setCourses(withTopics);
      setTasks(await api("/tasks"));
      setSummary(await api("/tasks/summary"));
    } catch (e) {
      setMessage("Error: " + e.message);
    }
  }

  useEffect(() => { load(); }, []);

  // Run an action, show a message, then reload the data
  async function run(action, okMessage) {
    try {
      const result = await action();
      setMessage(typeof okMessage === "function" ? okMessage(result) : okMessage);
    } catch (e) {
      setMessage("Error: " + e.message);
    }
    load();
  }

  const addCourse = () =>
    run(() => sendJson("/courses", { name: courseName, exam_date: examDate }), "Course added");

  const addTopic = () =>
    run(() => sendJson(`/courses/${courseId}/topics`, {
      name: topicName, priority: Number(priority), hours: Number(hours),
    }), "Topic added");

  const makePlan = () =>
    run(() => sendJson("/plans/generate-and-save", { daily_hours: Number(dailyHours) }),
        (r) => `Saved ${r.saved_tasks} tasks. ${r.warnings.join(" ")}`);

  const setStatus = (id, status) =>
    run(() => sendJson(`/tasks/${id}`, { status }, "PATCH"), `Task marked ${status}`);

  const saveCourse = () =>
    run(async () => {
      await sendJson(`/courses/${editCourse.id}`,
        { name: editCourse.name, exam_date: editCourse.exam_date }, "PATCH");
      setEditCourse(null);
    }, "Course updated. Generate the plan again to apply the new exam date.");

  const saveTopic = () =>
    run(async () => {
      await sendJson(`/courses/${editTopic.courseId}/topics/${editTopic.id}`, {
        name: editTopic.name,
        priority: Number(editTopic.priority),
        hours: Number(editTopic.hours),
      }, "PATCH");
      setEditTopic(null);
    }, "Topic updated. Generate the plan again to apply the new hours.");

  const removeCourse = (c) => {
    if (window.confirm(`Delete "${c.name}" with all its topics, tasks, and quiz results?`)) {
      run(() => del(`/courses/${c.id}`), "Course deleted");
    }
  };

  const removeTopic = (course, t) => {
    if (window.confirm(`Delete topic "${t.name}" with its tasks and quiz results?`)) {
      run(() => del(`/courses/${course.id}/topics/${t.id}`), "Topic deleted");
    }
  };

  const removeTask = (id) => run(() => del(`/tasks/${id}`), "Task deleted");

  return (
    <>
      <PageHeader title="Study Planner" subtitle="Add courses and topics, then let CampusPilot build a realistic schedule." />
      <Notice text={message} />

      <Card title="1. Add a course" icon="plus">
        <div className="row">
          <input className="input grow" placeholder="Course name" value={courseName}
                 onChange={(e) => setCourseName(e.target.value)} />
          <input className="input" type="date" value={examDate} onChange={(e) => setExamDate(e.target.value)} />
          <button className="btn btn-primary" onClick={addCourse}><Icon name="plus" size={16} /> Add course</button>
        </div>
      </Card>

      <Card title="2. Add topics" icon="file">
        <p className="hint">Use topic names that appear in your PDF, so quizzes can find the material.</p>
        <div className="row">
          <select className="input" value={courseId} onChange={(e) => setCourseId(e.target.value)}>
            <option value="">Choose course</option>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <input className="input grow" placeholder="Topic name" value={topicName}
                 onChange={(e) => setTopicName(e.target.value)} />
          <select className="input" value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value={1}>Low priority</option>
            <option value={2}>Medium priority</option>
            <option value={3}>High priority</option>
          </select>
          <input className="input num" type="number" min="0.5" step="0.5" value={hours}
                 onChange={(e) => setHours(e.target.value)} />
          <small>hours</small>
          <button className="btn btn-primary" onClick={addTopic}><Icon name="plus" size={16} /> Add topic</button>
        </div>

        <div style={{ marginTop: 18 }}>
          {courses.length === 0 && <p className="muted">No courses yet.</p>}

          {courses.map((c) => (
            <div key={c.id} className="course-block">
              {/* Course row: normal view or edit form */}
              {editCourse?.id === c.id ? (
                <div className="row">
                  <input className="input grow" value={editCourse.name}
                         onChange={(e) => setEditCourse({ ...editCourse, name: e.target.value })} />
                  <input className="input" type="date" value={editCourse.exam_date}
                         onChange={(e) => setEditCourse({ ...editCourse, exam_date: e.target.value })} />
                  <button className="btn btn-good btn-sm" onClick={saveCourse}><Icon name="check" size={14} /> Save</button>
                  <button className="btn btn-sm" onClick={() => setEditCourse(null)}>Cancel</button>
                </div>
              ) : (
                <div className="row between">
                  <span><b>{c.name}</b> <small>exam {c.exam_date}</small></span>
                  <span className="row">
                    <button className="icon-btn" title="Edit course"
                            onClick={() => setEditCourse({ id: c.id, name: c.name, exam_date: c.exam_date })}>
                      <Icon name="edit" size={16} />
                    </button>
                    <button className="icon-btn danger" title="Delete course" onClick={() => removeCourse(c)}>
                      <Icon name="trash" size={16} />
                    </button>
                  </span>
                </div>
              )}

              {/* Topics of this course */}
              <div className="sub" style={{ marginTop: 8 }}>
                {c.topics.length === 0 && <small>No topics yet.</small>}
                {c.topics.map((t) => (
                  editTopic?.id === t.id ? (
                    <div key={t.id} className="row" style={{ marginBottom: 8 }}>
                      <input className="input grow" value={editTopic.name}
                             onChange={(e) => setEditTopic({ ...editTopic, name: e.target.value })} />
                      <select className="input" value={editTopic.priority}
                              onChange={(e) => setEditTopic({ ...editTopic, priority: e.target.value })}>
                        <option value={1}>Low</option>
                        <option value={2}>Medium</option>
                        <option value={3}>High</option>
                      </select>
                      <input className="input num" type="number" min="0.5" step="0.5" value={editTopic.hours}
                             onChange={(e) => setEditTopic({ ...editTopic, hours: e.target.value })} />
                      <button className="btn btn-good btn-sm" onClick={saveTopic}><Icon name="check" size={14} /> Save</button>
                      <button className="btn btn-sm" onClick={() => setEditTopic(null)}>Cancel</button>
                    </div>
                  ) : (
                    <div key={t.id} className="task">
                      <span className="task-main">
                        <b>{t.name}</b>{" "}
                        <small>{t.hours}h, priority {["", "low", "medium", "high"][t.priority]}</small>
                      </span>
                      <button className="icon-btn" title="Edit topic"
                              onClick={() => setEditTopic({
                                id: t.id, courseId: c.id, name: t.name, priority: t.priority, hours: t.hours,
                              })}>
                        <Icon name="edit" size={15} />
                      </button>
                      <button className="icon-btn danger" title="Delete topic" onClick={() => removeTopic(c, t)}>
                        <Icon name="trash" size={15} />
                      </button>
                    </div>
                  )
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="3. Generate a study plan" icon="calendar">
        <div className="row">
          <input className="input num" type="number" min="0.5" step="0.5" value={dailyHours}
                 onChange={(e) => setDailyHours(e.target.value)} />
          <span className="muted">study hours per day</span>
          <button className="btn btn-primary" onClick={makePlan}><Icon name="sparkle" size={16} /> Generate plan</button>
        </div>
      </Card>

      <Card title="4. Your tasks" icon="check">
        {summary && (
          <div className="row" style={{ marginBottom: 14 }}>
            <Badge kind="pending">Pending {summary.pending}</Badge>
            <Badge kind="done">Done {summary.done}</Badge>
            <Badge kind="missed">Missed {summary.missed}</Badge>
          </div>
        )}
        {tasks.length === 0 && <p className="muted">No tasks yet. Generate a plan above.</p>}
        {tasks.map((t) => (
          <div key={t.id} className="task">
            <span className={`dot ${t.status}`} />
            <span className="task-main"><b>{t.topic}</b> <small>{t.course}</small><br />
              <small>{t.date} - {t.hours}h</small></span>
            <button className="btn btn-good btn-sm" onClick={() => setStatus(t.id, "done")}>
              <Icon name="check" size={14} /> Done
            </button>
            <button className="btn btn-bad btn-sm" onClick={() => setStatus(t.id, "missed")}>
              <Icon name="x" size={14} /> Missed
            </button>
            <button className="icon-btn danger" title="Delete task" onClick={() => removeTask(t.id)}>
              <Icon name="trash" size={15} />
            </button>
          </div>
        ))}
      </Card>
    </>
  );
}