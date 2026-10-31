import { useEffect, useState } from "react";
import Icon from "./Icon";

export function PageHeader({ title, subtitle }) {
  return (
    <div className="page-head">
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
    </div>
  );
}

export function Card({ title, icon, children }) {
  return (
    <section className="card">
      {title && (
        <div className="card-title">
          {icon && <span className="ico"><Icon name={icon} size={17} /></span>}
          {title}
        </div>
      )}
      {children}
    </section>
  );
}

export function Spinner() {
  return <span className="spinner" />;
}

// Shows a message. Messages that start with "Error" are red.
export function Notice({ text }) {
  if (!text) return null;
  const isError = String(text).startsWith("Error");
  return <div className={`notice ${isError ? "error" : ""}`}>{text}</div>;
}

// Animated circular progress. value is 0 to 1, or null.
export function Ring({ value, size = 130, label }) {
  const [ready, setReady] = useState(false);
  useEffect(() => { const t = setTimeout(() => setReady(true), 80); return () => clearTimeout(t); }, []);

  const r = 46;
  const c = 2 * Math.PI * r;
  const pct = value == null ? 0 : Math.max(0, Math.min(1, value));

  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg viewBox="0 0 120 120">
        <defs>
          <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#7c5cff" />
            <stop offset="1" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
        <circle className="ring-bg" cx="60" cy="60" r={r} />
        <circle className="ring-fg" cx="60" cy="60" r={r} stroke="url(#ringGrad)"
                strokeDasharray={c} strokeDashoffset={ready ? c * (1 - pct) : c} />
      </svg>
      <div className="ring-text">
        <b>{value == null ? "-" : `${Math.round(pct * 100)}%`}</b>
        <small>{label}</small>
      </div>
    </div>
  );
}

// Horizontal progress bar. value is 0 to 1.
export function Bar({ value, color }) {
  const pct = value == null ? 0 : Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="bar">
      <i style={{ width: `${pct}%`, background: color || "linear-gradient(90deg,#7c5cff,#22d3ee)" }} />
    </div>
  );
}

export function Badge({ kind, children }) {
  return <span className={`badge ${kind}`}>{children}</span>;
}