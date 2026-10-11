
from crewai import Agent, LLM

gemini_llm = LLM(
    model="gemini/gemini-3.8-flash",
    temperature=0.3
)

coordinator = Agent(
    role="Learning Session Coordinator",
    goal=(
        "Organize a structured learning session by identifying "
        "the student's topic and coordinating teaching, practice, "
        "and evaluation activities."
    ),
    backstory=(
        "You are an educational coordinator who organizes learning "
        "activities for beginner students. You break a learning "
        "session into clear stages, keep activities focused on "
        "the student's chosen topic, and use evaluation feedback "
        "to identify what the student should review."
    ),
    llm=gemini_llm,
    verbose=True
)