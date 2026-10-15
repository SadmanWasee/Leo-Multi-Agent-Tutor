
from crewai import Task
from agents.explainer import explainer

reteaching_task = Task(
    description=(
        "You are helping a beginner student improve their "
        "understanding of {topic}.\n\n"
        "Original question: {question}\n"
        "Student's original answer: {student_answer}\n"
        "Evaluator's feedback: {feedback}\n\n"
        "Explain the specific concepts the student misunderstood "
        "or omitted. Use simple language and a practical example. "
        "Do not repeat the entire original lesson. Focus only on "
        "the weaknesses identified in the feedback.\n\n"
        "At the end, provide exactly one new follow-up question "
        "to check whether the student now understands the concept. "
        "Do not provide the answer to that follow-up question."
    ),
    expected_output=(
        "A short targeted explanation of the student's "
        "misunderstood concepts, a practical example, and exactly "
        "one follow-up question without its answer."
    ),
    agent=explainer
)