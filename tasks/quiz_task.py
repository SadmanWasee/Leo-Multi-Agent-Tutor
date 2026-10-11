
from crewai import Task
from agents.quiz_master import quiz_master

quiz_task = Task(
    description=(
        "Create 5 quiz questions about {topic} "
        "for a beginner student. "
        "Include 3 conceptual questions and 2 practical questions. "
        "Number the questions clearly. "
        "Do not provide the answers."
    ),
    expected_output=(
        "Exactly 5 numbered quiz questions about the requested topic: "
        "3 conceptual questions and 2 practical questions. "
        "Do not include answers or hints."
    ),
    agent=quiz_master
)