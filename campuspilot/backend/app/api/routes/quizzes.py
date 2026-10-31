from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.routes.documents import retriever
from app.db.memory_store import store
from app.services.progress.quiz_generator import QuizGenerator

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

quiz_generator = QuizGenerator()


class QuizRequest(BaseModel):
    topic_id: str
    num_questions: int = 3


class Answer(BaseModel):
    question_id: str
    selected_index: int


class SubmitRequest(BaseModel):
    answers: list[Answer]


@router.post("/generate")
def generate_quiz(body: QuizRequest):
    topic = store.get_topic(body.topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if not 1 <= body.num_questions <= 10:
        raise HTTPException(status_code=400, detail="num_questions must be 1 to 10")

    # Find passages in the uploaded PDFs about this topic
    chunks = retriever.search(topic["name"], top_k=5)
    if not chunks:
        raise HTTPException(status_code=404, detail="Upload a document first")

    try:
        result = quiz_generator.generate(topic["name"], chunks, body.num_questions)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Quiz generation failed: {error}")

    quiz = store.add_quiz(body.topic_id, result["questions"])

    # Hide the right answers from the student
    visible = [
        {"id": q["id"], "question": q["question"], "options": q["options"]}
        for q in quiz["questions"]
    ]
    return {
        "quiz_id": quiz["id"],
        "topic": topic["name"],
        "questions": visible,
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }


@router.post("/{quiz_id}/submit")
def submit_quiz(quiz_id: str, body: SubmitRequest):
    quiz = store.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz["submitted"]:
        raise HTTPException(status_code=400, detail="This quiz was already submitted")

    questions = {q["id"]: q for q in quiz["questions"]}
    feedback = []
    correct_count = 0

    for answer in body.answers:
        question = questions.get(answer.question_id)
        if not question:
            continue
        is_correct = answer.selected_index == question["correct_index"]
        correct_count += 1 if is_correct else 0

        store.add_quiz_result(quiz["topic_id"], quiz_id, question["id"], is_correct)
        feedback.append({
            "question_id": question["id"],
            "correct": is_correct,
            "right_answer": question["options"][question["correct_index"]],
            "explanation": question["explanation"],
        })

    quiz["submitted"] = True
    total = len(feedback)
    return {
        "score": f"{correct_count}/{total}",
        "accuracy": round(correct_count / total, 2) if total else 0,
        "feedback": feedback,
    }