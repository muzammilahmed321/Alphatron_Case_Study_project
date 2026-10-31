import { useEffect, useRef, useState } from "react";
import { api, del, sendJson } from "../api/client";
import Icon from "../components/common/Icon";
import { Card, PageHeader, Notice, Spinner } from "../components/common/Ui";

export default function Chat() {
  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [documents, setDocuments] = useState([]);
  const [question, setQuestion] = useState("");
  const [thread, setThread] = useState([]);
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { loadDocuments(); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [thread, loading]);

  async function loadDocuments() {
    try {
      setDocuments(await api("/documents"));
    } catch (e) {
      setUploadMsg("Error: " + e.message);
    }
  }

  function pick(f) {
    if (f && f.name.toLowerCase().endsWith(".pdf")) { setFile(f); setUploadMsg(""); }
    else setUploadMsg("Error: please choose a PDF file");
  }

  async function upload() {
    if (!file) return setUploadMsg("Error: choose a PDF first");
    setUploading(true);
    setUploadMsg("");
    const form = new FormData();
    form.append("file", file);
    try {
      const d = await api("/documents/upload", { method: "POST", body: form });
      setUploadMsg(`Uploaded ${d.filename}: ${d.pages_with_text} pages, ${d.chunk_count} chunks`);
      setFile(null);
    } catch (e) {
      setUploadMsg("Error: " + e.message);
    }
    setUploading(false);
    loadDocuments();
  }

  async function removeDocument(name) {
    if (!window.confirm(`Remove "${name}" from the assistant's knowledge?`)) return;
    try {
      await del(`/documents/${encodeURIComponent(name)}`);
      setUploadMsg(`Removed ${name}`);
    } catch (e) {
      setUploadMsg("Error: " + e.message);
    }
    loadDocuments();
  }

  async function ask() {
    const q = question.trim();
    if (!q || loading) return;
    setQuestion("");
    setThread((t) => [...t, { q }]);
    setLoading(true);
    try {
      const result = await sendJson("/chat/ask", { question: q });
      setThread((t) => [...t, { result }]);
    } catch (e) {
      setThread((t) => [...t, { error: e.message }]);
    }
    setLoading(false);
  }

  return (
    <>
      <PageHeader title="Course Assistant" subtitle="Upload your notes and ask questions. Answers come only from your material." />

      <Card title="Upload course material" icon="upload">
        <label className={`dropzone ${drag ? "drag" : ""}`}
               onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
               onDragLeave={() => setDrag(false)}
               onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}>
          <span className="big"><Icon name="upload" size={34} /></span>
          <b>{file ? file.name : "Drop a PDF here or click to browse"}</b>
          <small>Text-based PDFs only</small>
          <input type="file" accept=".pdf" hidden onChange={(e) => pick(e.target.files[0])} />
        </label>
        <div className="row" style={{ marginTop: 14 }}>
          <button className="btn btn-primary" onClick={upload} disabled={uploading}>
            {uploading ? <Spinner /> : <Icon name="check" size={16} />}
            {uploading ? "Processing..." : "Upload"}
          </button>
          <small>The first upload is slower while the embedding model warms up.</small>
        </div>
        <div style={{ marginTop: 12 }}><Notice text={uploadMsg} /></div>

        <h4 style={{ margin: "18px 0 10px" }}>Uploaded documents</h4>
        {documents.length === 0 && <p className="muted">Nothing uploaded yet.</p>}
        {documents.map((d) => (
          <div key={d.filename} className="task">
            <Icon name="file" size={18} />
            <span className="task-main"><b>{d.filename}</b><br />
              <small>{d.pages} pages, {d.chunks} chunks</small></span>
            <button className="icon-btn danger" title="Remove document" onClick={() => removeDocument(d.filename)}>
              <Icon name="trash" size={15} />
            </button>
          </div>
        ))}
      </Card>

      <Card title="Ask a question" icon="chat">
        <div className="thread">
          {thread.length === 0 && <p className="muted">Try: "Summarize the main topics in this document".</p>}

          {thread.map((m, i) => {
            if (m.q) return <div key={i} className="bubble user">{m.q}</div>;
            if (m.error) return <div key={i} className="bubble err">Error: {m.error}</div>;
            return (
              <div key={i} className="bubble ai">
                <div className="answer">{m.result.answer}</div>
                <div className="chips">
                  {m.result.sources.map((s, j) => (
                    <span key={j} className="chip">{s.source}, p.{s.page}</span>
                  ))}
                </div>
                <div className="meta">
                  {m.result.input_tokens} tokens in, {m.result.output_tokens} out, {m.result.seconds}s
                </div>
              </div>
            );
          })}

          {loading && <div className="bubble ai typing"><i /><i /><i /></div>}
          <div ref={endRef} />
        </div>

        <div className="composer">
          <input className="input grow" value={question} placeholder="Ask about your course material..."
                 onChange={(e) => setQuestion(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && ask()} />
          <button className="btn btn-primary" onClick={ask} disabled={loading}>
            <Icon name="send" size={16} /> Ask
          </button>
        </div>
      </Card>
    </>
  );
}