
from dotenv import load_dotenv

load_dotenv()

from crewai import Crew, Process

from agents.explainer import explainer
from agents.quiz_master import quiz_master

from tasks.explanation_task import explanation_task
from tasks.quiz_task import quiz_task

# Run the lesson first, then generate the quiz.
crew = Crew(
    agents=[explainer, quiz_master],
    tasks=[explanation_task, quiz_task],
    process=Process.sequential,
    verbose=True
)

result = crew.kickoff(
    inputs={
        "topic": "Python decorators"
    }
)

print("\n===== COMPLETE LEARNING SESSION =====\n")
print(result)