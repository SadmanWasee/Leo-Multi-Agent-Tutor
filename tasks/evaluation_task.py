
from crewai import Task
from agents.evaluator import evaluator

evaluation_task = Task(
    description=(
        "Evaluate the student's answer to the following question.\n\n"
        "Question: {question}\n"
        "Expected answer: {expected_answer}\n"
        "Student answer: {student_answer}\n\n"
        "Compare the student's answer with the expected concepts. "
        "Award a score from 0 to 10, allowing partial credit. "
        "Explain what the student understood correctly, "
        "identify any mistakes or missing concepts, "
        "and recommend what the student should review. "
        "Be fair and constructive."
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