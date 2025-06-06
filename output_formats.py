from typing import List
from pydantic import BaseModel

class Quiz_Question(BaseModel):
    question: str
    A: str
    B: str
    C: str
    D: str
    correct_answer: str
    explanation: str

class Quiz_V1(BaseModel):
    questions: List[Quiz_Question]