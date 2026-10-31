from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.memory_store import store

router = APIRouter(prefix="/courses", tags=["courses"])


class CourseCreate(BaseModel):
    name: str
    exam_date: date


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    exam_date: Optional[date] = None


class TopicCreate(BaseModel):
    name: str
    priority: int = 2     # 1 = low, 2 = medium, 3 = high
    hours: float          # estimated study hours


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = None
    hours: Optional[float] = None


def check_topic_values(priority, hours):
    if priority is not None and priority not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="priority must be 1, 2, or 3")
    if hours is not None and hours <= 0:
        raise HTTPException(status_code=400, detail="hours must be above 0")


def get_topic_of_course(course_id, topic_id):
    topic = store.get_topic(topic_id)
    if not store.get_course(course_id) or not topic or topic["course_id"] != course_id:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


#  Courses 
@router.post("")
def create_course(body: CourseCreate):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Course name is required")
    return store.add_course(body.name.strip(), body.exam_date)


@router.get("")
def list_courses():
    return store.list_courses()


@router.patch("/{course_id}")
def update_course(course_id: str, body: CourseUpdate):
    course = store.update_course(course_id, body.name, body.exam_date)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.delete("/{course_id}")
def delete_course(course_id: str):
    if not store.delete_course(course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted"}


# Topics 
@router.post("/{course_id}/topics")
def add_topic(course_id: str, body: TopicCreate):
    if not store.get_course(course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Topic name is required")
    check_topic_values(body.priority, body.hours)
    return store.add_topic(course_id, body.name.strip(), body.priority, body.hours)


@router.get("/{course_id}/topics")
def list_topics(course_id: str):
    if not store.get_course(course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    return store.list_topics(course_id)


@router.patch("/{course_id}/topics/{topic_id}")
def update_topic(course_id: str, topic_id: str, body: TopicUpdate):
    get_topic_of_course(course_id, topic_id)
    check_topic_values(body.priority, body.hours)
    return store.update_topic(topic_id, body.priority, body.hours, body.name)


@router.delete("/{course_id}/topics/{topic_id}")
def delete_topic(course_id: str, topic_id: str):
    get_topic_of_course(course_id, topic_id)
    store.delete_topic(topic_id)
    return {"message": "Topic deleted"}