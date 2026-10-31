// The backend address comes from frontend/.env (see VITE_API_URL)
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Calls the backend and returns the JSON. Throws an error with a readable message.
export async function api(path, options = {}) {
  const res = await fetch(API + path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail) || "Request failed"
    );
  }
  return data;
}

// Shortcut for sending JSON
export function sendJson(path, body, method = "POST") {
  return api(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// Shortcut for deleting something
export function del(path) {
  return api(path, { method: "DELETE" });
}