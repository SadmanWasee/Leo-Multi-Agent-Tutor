
from crewai import Task
from agents.evaluator import evaluator

evaluation_task = Task(
    description=(
        "Evaluate a beginner student's answer about {topic}.\n\n"
        "Question: {question}\n"
        "Student answer: {student_answer}\n\n"
        "First, determine what a correct answer should contain. "
        "Then compare the student's answer with those concepts. "
        "Award a score from 0 to 10, allowing partial credit. "
        "Do not award full marks to an incorrect or incomplete answer. "
        "Explain what the student understood correctly, identify "
        "mistakes or missing concepts, and recommend what to review. "
        "Be fair, constructive, and beginner-friendly."
    ),
    expected_output=(
        "A structured evaluation containing:\n"
        "1. Score out of 10\n"
        "2. What the student understood correctly\n"
        "3. Mistakes or missing concepts\n"
        "4. Suggested improvement or review topic"
    ),
    agent=evaluator
)