import { useEffect, useState } from "react";
import { api, sendJson } from "../api/client";
import Icon from "../components/common/Icon";
import { Bar, Card, PageHeader, Notice, Spinner } from "../components/common/Ui";

export default function Quiz() {
  const [topics, setTopics] = useState([]);
  const [topicId, setTopicId] = useState("");
  const [count, setCount] = useState(3);
  const [quiz, setQuiz] = useState(null);
  const [picked, setPicked] = useState({});    
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api("/progress/topics").then(setTopics).catch((e) => setError("Error: " + e.message));
  }, []);

  async function generate() {
    if (!topicId) return setError("Error: choose a topic first");
    setLoading(true);
    setError("");
    setQuiz(null);
    setResult(null);
    setPicked({});
    try {
      setQuiz(await sendJson("/quizzes/generate", { topic_id: topicId, num_questions: Number(count) }));
    } catch (e) {
      setError("Error: " + e.message);
    }
    setLoading(false);
  }

  async function submit() {
    if (Object.keys(picked).length < quiz.questions.length) {
      return setError("Error: answer every question first");
    }
    setError("");
    const answers = quiz.questions.map((q) => ({ question_id: q.id, selected_index: picked[q.id] }));
    try {
      setResult(await sendJson(`/quizzes/${quiz.quiz_id}/submit`, { answers }));
    } catch (e) {
      setError("Error: " + e.message);
    }
  }

  const feedbackFor = (id) => result?.feedback.find((f) => f.question_id === id);
  const answered = quiz ? Object.keys(picked).length / quiz.questions.length : 0;

  return (
    <>
      <PageHeader title="Practice Quiz" subtitle="Questions are written from your uploaded PDFs and graded exactly." />
      <Notice text={error} />

      <Card title="Choose a topic" icon="quiz">
        <p className="hint">Upload a PDF in the Chat tab first, so there is material to quiz on.</p>
        <div className="row">
          <select className="input grow" value={topicId} onChange={(e) => setTopicId(e.target.value)}>
            <option value="">Choose topic</option>
            {topics.map((t) => <option key={t.topic_id} value={t.topic_id}>{t.topic}</option>)}
          </select>
          <input className="input num" type="number" min="1" max="10" value={count}
                 onChange={(e) => setCount(e.target.value)} />
          <small>questions</small>
          <button className="btn btn-primary" onClick={generate} disabled={loading}>
            {loading ? <Spinner /> : <Icon name="sparkle" size={16} />}
            {loading ? "Writing questions..." : "Generate quiz"}
          </button>
        </div>
        {topics.length === 0 && <p className="muted" style={{ marginTop: 10 }}>No topics yet. Add some in the Planner.</p>}
      </Card>

      {quiz && (
        <Card title={`Quiz: ${quiz.topic}`} icon="quiz">
          {!result && <div style={{ marginBottom: 18 }}><Bar value={answered} /></div>}

          {quiz.questions.map((q, n) => {
            const fb = feedbackFor(q.id);
            return (
              <div key={q.id} className="q">
                <h4>{n + 1}. {q.question}</h4>
                {q.options.map((option, i) => {
                  let state = "";
                  if (fb) {
                    if (option === fb.right_answer) state = "right";
                    else if (picked[q.id] === i) state = "wrong";
                  }
                  return (
                    <button key={i} type="button" disabled={!!result}
                            className={`option ${picked[q.id] === i ? "picked" : ""} ${state}`}
                            onClick={() => setPicked({ ...picked, [q.id]: i })}>
                      <span className="letter">{"ABCD"[i]}</span>
                      {option}
                    </button>
                  );
                })}
                {fb && <div className="explain">{fb.correct ? "Correct. " : "Not quite. "}{fb.explanation}</div>}
              </div>
            );
          })}

          {!result && (
            <button className="btn btn-primary" onClick={submit}><Icon name="check" size={16} /> Submit answers</button>
          )}
          {result && (
            <div className="score">{result.score} <small>({Math.round(result.accuracy * 100)}%)</small></div>
          )}
        </Card>
      )}
    </>
  );
}