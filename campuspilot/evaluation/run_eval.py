"""Evaluation script for CampusPilot.

Start the server first (without --reload):
    uvicorn app.main:app --port 8000
Then, from the backend folder with the venv active:
    python ..\\evaluation\\run_eval.py
"""
import json
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

API = "http://localhost:8000"
HERE = Path(__file__).parent
client = httpx.Client(base_url=API, timeout=300)

PAUSE = 12          # seconds between Gemini questions (avoids rate limits)
ASK_TRIES = 3       # how many times to retry a busy/rate-limited question
ASK_WAIT = 20       # seconds to wait before retrying

results = []        # every check is stored here
api_errors = 0      # Gemini failures that are not the app's fault


def check(name, passed, detail=""):
    results.append({"check": name, "passed": bool(passed), "detail": str(detail)})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}  {detail}")


def skipped(name, detail=""):
    """Used when the Gemini API failed, so the check could not be judged."""
    global api_errors
    api_errors += 1
    results.append({"check": name, "passed": None, "detail": str(detail)})
    print(f"[SKIP] {name}  (Gemini API error) {detail}")


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def pending_count():
    return len(client.get("/tasks", params={"status": "pending"}).json())


def is_api_busy(text):
    return any(w in text for w in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"))


def ask(question):
    """Ask the chat endpoint. Retry if Gemini is busy or rate limited."""
    response = None
    for attempt in range(1, ASK_TRIES + 1):
        response = client.post("/chat/ask", json={"question": question})
        if response.status_code == 200 or not is_api_busy(response.text):
            return response
        if attempt < ASK_TRIES:
            print(f"   Gemini busy, waiting {ASK_WAIT}s then retrying ({attempt}/{ASK_TRIES})")
            time.sleep(ASK_WAIT)
    return response


# ---------------------------------------------------------------
# 1. Schedule feasibility
# ---------------------------------------------------------------
def test_schedule():
    print("\n--- Schedule feasibility ---")
    body = {
        "daily_hours": 3,
        "start_date": day(1),
        "courses": [{
            "name": "Databases", "exam_date": day(10),
            "topics": [
                {"name": "Normalization", "priority": 3, "hours": 4},
                {"name": "SQL Joins", "priority": 2, "hours": 3},
            ],
        }],
    }
    data = client.post("/plans/generate", json=body).json()
    check("Valid plan has no rule violations", data["validation_problems"] == [])
    check("Valid plan schedules all hours", data["total_hours_scheduled"] == 7,
          f"scheduled {data['total_hours_scheduled']}h")

    body["daily_hours"] = 0.5   # impossible: 7 hours in 9 days of 0.5h
    data = client.post("/plans/generate", json=body).json()
    check("Impossible plan gives a warning", len(data["warnings"]) > 0)


# ---------------------------------------------------------------
# 2. Agent routing, approval, and persistence
# ---------------------------------------------------------------
def test_agent():
    print("\n--- Agent routing and persistence ---")
    client.post("/usage/reset-all-data")

    # No data -> agent should stop
    r = client.post("/agent/run", json={"daily_hours": 3}).json()
    check("No data -> route 'no_data'", r.get("route") == "no_data", r.get("route"))

    # Course with a topic but no quizzes -> practice
    course = client.post("/courses", json={"name": "Databases", "exam_date": day(30)}).json()
    client.post(f"/courses/{course['id']}/topics",
                json={"name": "Normalization", "priority": 2, "hours": 4})
    r = client.post("/agent/run", json={"daily_hours": 3}).json()
    check("Untested topic -> route 'practice'", r.get("route") == "practice", r.get("route"))

    # Save a plan and confirm it was really saved
    save = client.post("/plans/generate-and-save",
                       json={"daily_hours": 3, "start_date": day(1)})
    saved = save.json().get("saved_tasks", 0) if save.status_code == 200 else 0
    check("Plan saved before the agent test", saved > 0,
          f"status={save.status_code} saved_tasks={saved}")
    if saved == 0:
        print("   Cannot test the agent without saved tasks:", save.text[:200])
        return

    # Pretend 10 days passed so the tasks are missed -> revise
    r = client.post("/agent/run", json={"daily_hours": 3, "today": day(10)}).json()
    summary = client.get("/tasks/summary").json()
    check("Missed tasks -> waits for approval",
          r.get("status") == "waiting_for_approval",
          f"status={r.get('status')} route={r.get('route')} "
          f"message={r.get('message')} detail={r.get('detail')} tasks={summary}")
    if r.get("status") != "waiting_for_approval":
        return

    check("Revision includes an explanation", len(r.get("explanation", "")) > 20)
    check("Revision proposes tasks", len(r.get("proposed_tasks", [])) > 0)

    # While waiting, the proposed plan must NOT be active yet
    check("Proposed plan not applied while waiting", pending_count() == 0,
          f"pending={pending_count()}")

    # Approve -> new plan saved
    done = client.post(f"/agent/{r['thread_id']}/decision", json={"approve": True}).json()
    check("Approve finishes the agent", done.get("status") == "finished", done.get("message", ""))
    after_approve = pending_count()
    check("Approved plan is saved (pending tasks exist)", after_approve > 0,
          f"{after_approve} tasks")

    # Reject -> current plan stays the same
    r2 = client.post("/agent/run", json={"daily_hours": 3, "today": day(10)}).json()
    check("Second run waits for approval", r2.get("status") == "waiting_for_approval",
          f"status={r2.get('status')} route={r2.get('route')}")
    if r2.get("status") == "waiting_for_approval":
        before = pending_count()
        client.post(f"/agent/{r2['thread_id']}/decision", json={"approve": False})
        after = pending_count()
        check("Reject keeps the current plan", before == after, f"{before} -> {after}")


# ---------------------------------------------------------------
# 3. RAG accuracy and grounding (needs a PDF)
# ---------------------------------------------------------------
def test_rag():
    print("\n--- RAG accuracy and grounding ---")
    pdfs = list((HERE / "test_documents").glob("*.pdf"))
    if not pdfs:
        print("Skipped: put a PDF in evaluation/test_documents/")
        return

    for pdf in pdfs:
        with open(pdf, "rb") as f:
            r = client.post("/documents/upload", files={"file": (pdf.name, f, "application/pdf")})
        check(f"Upload {pdf.name}", r.status_code == 200, f"status {r.status_code}")

    questions = json.loads((HERE / "scenarios" / "rag_questions.json").read_text())

    for item in questions["in_scope"]:
        time.sleep(PAUSE)
        r = ask(item["question"])
        if r.status_code != 200:
            if is_api_busy(r.text):
                skipped(f"Answer: {item['question']}", r.text[:300])
            else:
                check(f"Answer: {item['question']}", False, r.text[:300])
            continue
        answer = r.json()["answer"].lower()
        check(f"Accurate: {item['question']}",
              any(k.lower() in answer for k in item["keywords"]))
        check(f"Cited sources: {item['question']}", "page" in answer)

    refusal_phrases = ("could not find", "not find", "not contain", "does not mention",
                       "not provided", "no information", "cannot find")
    for question in questions["out_of_scope"]:
        time.sleep(PAUSE)
        r = ask(question)
        if r.status_code != 200:
            if is_api_busy(r.text):
                skipped(f"Grounded (refuses): {question}", r.text[:300])
            else:
                check(f"Grounded (refuses): {question}", False, r.text[:300])
            continue
        answer = r.json().get("answer", "").lower()
        check(f"Grounded (refuses): {question}",
              any(p in answer for p in refusal_phrases), answer[:80])


# ---------------------------------------------------------------
# 4. Latency and cost
# ---------------------------------------------------------------
def report_usage():
    print("\n--- Latency and cost ---")
    usage = client.get("/usage").json()
    print(json.dumps(usage, indent=2))
    return usage


if __name__ == "__main__":
    try:
        client.get("/health")
    except httpx.ConnectError:
        raise SystemExit("Server is not running. Start it first on port 8000.")

    test_schedule()
    test_agent()
    test_rag()
    usage = report_usage()

    judged = [r for r in results if r["passed"] is not None]
    passed = sum(1 for r in judged if r["passed"])
    print(f"\nRESULT: {passed}/{len(judged)} checks passed")
    if api_errors:
        print(f"{api_errors} check(s) skipped because the Gemini API was busy or "
              f"rate limited. Wait a few minutes and run again.")

    out = HERE / "results" / "eval_results.json"
    out.write_text(json.dumps({"checks": results, "usage": usage}, indent=2))
    print(f"Saved to {out}")