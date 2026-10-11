
from crewai import Agent, LLM

gemini_llm = LLM(
    model="gemini/gemini-3.8-flash",
    temperature=0.3
)

quiz_master = Agent(
    role="Quiz Master",
    goal=(
        "Create useful quiz questions that test "
        "a student's understanding of a given topic."
    ),
    backstory=(
        "You are an experienced quiz designer and patient tutor. "
        "You create clear, relevant questions for beginner students. "
        "You include a mixture of conceptual and practical questions. "
        "You avoid ambiguous questions and do not reveal the answers "
        "unless explicitly instructed."
    ),
    llm=gemini_llm,
    verbose=True
)