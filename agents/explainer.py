from crewai import Agent, LLM


gemini_llm = LLM(
    model="gemini/gemini-3.8-flash",
    temperature=0.7
)


explainer = Agent(
    role="Expert Teacher",

    goal="Explain technical topics clearly to beginner students.",

    backstory=(
        "You are a patient and knowledgeable teacher. "
        "You explain difficult technical concepts using simple language "
        "and practical examples."
    ),

    llm=gemini_llm,

    verbose=True
)