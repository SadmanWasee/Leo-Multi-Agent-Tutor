from crewai import Task

from agents.explainer import explainer


explanation_task = Task(
    description=(
        "Explain {topic} to a beginner student. "
        "Use simple language, explain the core idea first, "
        "and provide a practical example."
    ),
    expected_output=(
        "A clear beginner-friendly explanation of the topic "
        "with at least one practical example."
    ),
    agent=explainer
)