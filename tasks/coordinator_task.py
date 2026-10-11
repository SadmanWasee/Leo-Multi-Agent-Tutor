from crewai import Task
from agents.coordinator import coordinator

coordinator_task = Task(
    description=(
        "Plan a beginner-friendly learning session about {topic}. "
        "Create a clear sequence with these stages: "
        "1. Explain the topic. "
        "2. Generate practice questions. "
        "3. Evaluate the student's answers. "
        "4. Identify possible review activities. "
        "Describe the responsibility of each stage."
    ),
    expected_output=(
        "A structured learning plan containing all four stages, "
        "the responsible agent for each stage, and the purpose "
        "of each stage."
    ),
    agent=coordinator
)