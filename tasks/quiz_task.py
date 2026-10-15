
from crewai import Task

from agents.quiz_master import quiz_master
from tasks.coordinator_task import coordinator_task
from tasks.explanation_task import explanation_task


quiz_task = Task(
    description=(
        "Create exactly 5 quiz questions about {topic} "
        "for a beginner student.\n\n"

        "Use the Coordinator's learning plan and the Explainer's "
        "lesson to keep the questions relevant to the learning session.\n\n"

        "Follow this exact format:\n"
        "1. First conceptual question\n"
        "2. Second conceptual question\n"
        "3. Third conceptual question\n"
        "4. First practical question\n"
        "5. Second practical question\n\n"

        "Questions 1-3 must test conceptual understanding.\n"
        "Questions 4-5 must ask the student to apply the topic "
        "in a practical situation or write Python code.\n\n"

        "Do not add section headings, introductions, answers, "
        "or any text outside the five numbered questions."
    ),
    expected_output=(
        "Exactly five questions numbered 1. through 5. "
        "Each question must be on its own line or paragraph. "
        "Questions 1-3 are conceptual, and questions 4-5 are practical. "
        "No headings, answers, or extra text."
    ),
    agent=quiz_master,
    context=[coordinator_task, explanation_task]
)
