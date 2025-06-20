from pydantic import BaseModel
from typing import List

class CourseRequest(BaseModel):
    course_name: str
    description: str
    duration_days: int
    total_hours: int
