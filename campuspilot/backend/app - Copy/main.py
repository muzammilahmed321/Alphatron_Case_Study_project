from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    documents, chat, plans, courses, tasks,
    quizzes, progress, agent, usage, history,
)

app = FastAPI(title="CampusPilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(plans.router)
app.include_router(courses.router)
app.include_router(tasks.router)
app.include_router(quizzes.router)
app.include_router(progress.router)
app.include_router(agent.router)
app.include_router(usage.router)
app.include_router(history.router)


@app.get("/")
def root():
    return {"message": "CampusPilot API is running. See /docs"}


@app.get("/health")
def health():
    return {"status": "ok"}