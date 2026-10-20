import re
import streamlit as st
from crewai import Crew, Process
from dotenv import load_dotenv

load_dotenv()

from agents.explainer import explainer
from agents.quiz_master import quiz_master
from agents.evaluator import evaluator
from agents.coordinator import coordinator

from tasks.coordinator_task import coordinator_task
from tasks.explanation_task import explanation_task
from tasks.quiz_task import quiz_task
from tasks.evaluation_task import evaluation_task
from tasks.reteaching_task import reteaching_task

st.set_page_config(page_title="Leo AI Tutor", page_icon="🎓", layout="wide")


def extract_questions(quiz_text):
    parts = re.split(r"(?m)^\s*\d+[.)]\s+", str(quiz_text).strip())
    questions = []
    for part in parts[1:]:
        question = part.strip()
        question = re.sub(
            r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?"
            r"(?:conceptual questions|practical questions)(?:\*\*)?\s*$",
            "", question
        )
        question = re.sub(r"(?m)^\s*[-*_]{3,}\s*$", "", question).strip()
        if question:
            questions.append(question)
    return questions


def extract_score(feedback):
    match = re.search(r"(?i)(\d+(?:\.\d+)?)\s*(?:/|out of)\s*10\b", str(feedback))
    if match:
        score = float(match.group(1))
        if 0 <= score <= 10:
            return score
    return None


def is_quota_error(error):
    message = str(error).lower()
    return any(term in message for term in ("429", "resource_exhausted", "quota", "rate limit"))


def show_error(stage, error):
    if is_quota_error(error):
        st.error(
            f"Gemini quota/rate limit reached during **{stage}**. "
            "Completed results are preserved. Wait for the quota to reset, "
            "or use Demo Mode to record the UI without API calls."
        )
    else:
        st.error(f"Leo could not complete **{stage}**: {error}")


def create_demo_session(topic):
    return {
        "topic": topic,
        "lesson": (
            "Python is a beginner-friendly programming language used to build websites, "
            "automate tasks, analyze data, and create AI applications.\n\n"
            "A **variable** stores a value under a name. For example:\n\n"
            "```python\nname = \"Leo\"\nage = 2\nprint(name)\n```\n\n"
            "Python is case-sensitive, so `print()` is different from `Print()`."
        ),
        "questions": [
            "What is a variable in Python, and why is it useful?",
            "Why does Python treat `name` and `Name` as different identifiers?",
            "What data type does `input()` return by default?",
            "Write a Python statement that stores the number 19.99 in a variable named `item_price`.",
            "Given `temperature = 72`, write a single `print()` statement using string concatenation to display `The temperature is 72 degrees.`",
        ],
        "demo": True,
    }


def start_real_session(topic):
    crew = Crew(
        agents=[coordinator, explainer, quiz_master],
        tasks=[coordinator_task, explanation_task, quiz_task],
        process=Process.sequential,
        verbose=True,
    )
    crew.kickoff(inputs={"topic": topic})
    lesson = explanation_task.output.raw
    quiz_text = quiz_task.output.raw
    questions = extract_questions(quiz_text)
    if not lesson or not quiz_text:
        raise ValueError("Leo did not return both a lesson and a quiz.")
    if len(questions) != 5:
        raise ValueError(
            f"Expected 5 quiz questions but extracted {len(questions)}. "
            "Check tasks/quiz_task.py and try again."
        )
    return {"topic": topic, "lesson": lesson, "questions": questions, "demo": False}


def evaluate_one(topic, question, answer):
    crew = Crew(
        agents=[evaluator], tasks=[evaluation_task],
        process=Process.sequential, verbose=True
    )
    result = crew.kickoff(inputs={
        "topic": topic, "question": question, "student_answer": answer
    })
    return str(result)


def demo_feedback(i):
    examples = [
        "Score: 8/10\n\n**What you understood:** Variables store values that can be reused.\n\n**To improve:** Explain that a variable name refers to a stored value.",
        "Score: 10/10\n\n**What you understood:** Python is case-sensitive, so `name` and `Name` are different identifiers.",
        "Score: 10/10\n\n**What you understood:** `input()` returns a string by default. Convert it if you need a number.",
        "Score: 9/10\n\n**Example:** `item_price = 19.99`",
        "Score: 4/10\n\n**Review:** String concatenation joins text with `+`. Convert the number with `str()`.\n\n```python\ntemperature = 72\nprint(\"The temperature is \" + str(temperature) + \" degrees.\")\n```\n\nA score below 6/10 would normally trigger targeted reteaching in live mode."
    ]
    return examples[i]


st.markdown("""
<style>
.block-container {padding-top: 1.7rem; max-width: 1150px;}
.hero {padding: 1.5rem 1.7rem; border-radius: 18px; background: linear-gradient(120deg,#12213a,#244f75); color: white; margin-bottom: 1rem;}
.hero h1 {color:white; margin-bottom:.3rem; font-size:2.25rem;}
.hero p {color:#e3edf7; margin-bottom:0;}
.agent-card {border:1px solid rgba(128,128,128,.28); border-radius:14px; padding:1rem; min-height:120px;}
.agent-card h4 {margin:.2rem 0 .4rem 0;}
.muted {opacity:.75; font-size:.92rem;}
</style>
""", unsafe_allow_html=True)

for key, default in {
    "leo_session": None, "leo_answers": {}, "leo_evaluations": [],
    "leo_scores": [], "leo_reteaching": {}, "leo_followup_answers": {},
    "leo_followup_evaluations": {}
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

with st.sidebar:
    st.title("🎓 Leo AI Tutor")
    st.caption("A multi-agent learning assistant")
    st.divider()
    st.subheader("Session settings")
    demo_mode = st.toggle(
        "Demo Mode (no API calls)", value=True,
        help="Show prepared sample content and feedback without using Gemini."
    )
    topic = st.text_input("Learning topic", value="Python programming")
    st.info("Demo Mode uses prepared examples. Turn it off to run your CrewAI agents.")
    start_button = st.button("Start learning session", type="primary", use_container_width=True)
    if st.button("Clear session", use_container_width=True):
        for key in ("leo_session", "leo_answers", "leo_evaluations", "leo_scores", "leo_reteaching", "leo_followup_answers", "leo_followup_evaluations"):
            st.session_state[key] = None if key == "leo_session" else {}
            if key in ("leo_evaluations", "leo_scores"):
                st.session_state[key] = []
        st.rerun()

st.markdown("""
<div class="hero">
<h1>Learn smarter with Leo</h1>
<p>Plan a lesson, learn from an AI Explainer, test your knowledge, and receive constructive feedback.</p>
</div>
""", unsafe_allow_html=True)

st.subheader("Meet your AI team")
cols = st.columns(4)
agents = [
    ("🧭", "Coordinator", "Plans the learning session"),
    ("📘", "Explainer", "Teaches with clear examples"),
    ("🧠", "Quiz Master", "Creates five practice questions"),
    ("📝", "Evaluator", "Grades answers and suggests improvements"),
]
for col, (emoji, name, desc) in zip(cols, agents):
    with col:
        st.markdown(
            f'<div class="agent-card"><div style="font-size:1.7rem">{emoji}</div>'
            f'<h4>{name}</h4><div class="muted">{desc}</div></div>',
            unsafe_allow_html=True,
        )

if start_button:
    if not topic.strip():
        st.warning("Please enter a learning topic first.")
    else:
        st.session_state.leo_answers = {}
        st.session_state.leo_evaluations = []
        st.session_state.leo_scores = []
        st.session_state.leo_reteaching = {}
        if demo_mode:
            st.session_state.leo_session = create_demo_session(topic.strip())
            st.success("Demo session loaded. No Gemini API requests were made.")
        else:
            with st.spinner("Coordinator, Explainer, and Quiz Master are working..."):
                try:
                    st.session_state.leo_session = start_real_session(topic.strip())
                    st.success("Your lesson and quiz are ready.")
                except Exception as error:
                    show_error("lesson and quiz generation", error)

session = st.session_state.leo_session

if session:
    st.divider()
    st.subheader("📚 Your lesson")
    st.caption(f"Topic: {session['topic']}")
    if session["demo"]:
        st.info("Demo content — prepared examples, not a live Gemini response.")
    st.markdown(session["lesson"])

    st.divider()
    st.subheader("✍️ Knowledge check")
    st.write("Answer all five questions, then submit them for evaluation.")
    with st.form("leo_quiz_form"):
        answers = {}
        for i, question in enumerate(session["questions"]):
            # Show the actual question text above the answer box.
            st.markdown(f"**Question {i + 1}.** {question}")
            answers[i] = st.text_area(
                f"Your answer to Question {i + 1}",
                value=st.session_state.leo_answers.get(i, ""),
                placeholder="Write your answer here...",
                key=f"leo_answer_{i}",
                height=100,
                label_visibility="collapsed",
            )
        submitted = st.form_submit_button("Submit answers", type="primary")

    if submitted:
        missing = [i + 1 for i, answer in answers.items() if not answer.strip()]
        if missing:
            st.warning("Please answer every question before submitting.")
        else:
            st.session_state.leo_answers = answers
            if session["demo"]:
                st.session_state.leo_evaluations = [demo_feedback(i) for i in range(5)]
                st.session_state.leo_scores = [
                    extract_score(item) for item in st.session_state.leo_evaluations
                ]
                st.success("Example feedback displayed. No API calls were made.")
            else:
                evaluations, scores = [], []
                progress = st.progress(0, text="Evaluator is reviewing your answers...")
                failed = False
                for i, question in enumerate(session["questions"]):
                    try:
                        feedback = evaluate_one(session["topic"], question, answers[i].strip())
                        evaluations.append(feedback)
                        scores.append(extract_score(feedback))
                        progress.progress((i + 1) / 5, text=f"Evaluated answer {i + 1} of 5")
                    except Exception as error:
                        show_error(f"evaluation of answer {i + 1}", error)
                        evaluations.append(None)
                        scores.append(None)
                        failed = True
                        break
                st.session_state.leo_evaluations = evaluations
                st.session_state.leo_scores = scores
                if not failed and len(evaluations) == 5:
                    st.success("Evaluation complete.")
                elif evaluations:
                    st.warning("Partial results are saved. Remaining evaluations were stopped.")

    evaluations = st.session_state.leo_evaluations
    scores = st.session_state.leo_scores
    if evaluations:
        st.divider()
        st.subheader("📊 Evaluation and feedback")
        for i, feedback in enumerate(evaluations):
            score = scores[i] if i < len(scores) else None
            heading = f"Question {i + 1} · {score:g}/10" if score is not None else f"Question {i + 1} · Score unavailable"
            with st.expander(heading, expanded=(i == 0)):
                st.markdown(f"**Question:** {session['questions'][i]}")
                if feedback:
                    st.markdown(feedback)
                else:
                    st.warning("No evaluation was returned for this question.")

        valid = [s for s in scores if s is not None]
        if valid:
            total = sum(valid)
            possible = 10 * len(valid)
            percentage = total / possible * 100
            c1, c2, c3 = st.columns(3)
            c1.metric("Total score", f"{total:g}/{possible}")
            c2.metric("Average", f"{total / len(valid):.1f}/10")
            c3.metric("Percentage", f"{percentage:.1f}%")
            st.progress(min(percentage / 100, 1.0))

        if not session["demo"]:
            low_scores = [
                i for i, score in enumerate(scores)
                if score is not None and score < 6 and i < len(evaluations) and evaluations[i]
            ]
            if low_scores:
                st.divider()
                st.subheader("🔁 Targeted reteaching")
                st.write("Reteaching uses extra Gemini requests, so it runs only when requested.")
                selected = st.selectbox(
                    "Choose an answer to review", low_scores,
                    format_func=lambda i: f"Question {i + 1} — {scores[i]:g}/10"
                )
                if st.button("Start targeted reteaching"):
                    with st.spinner("Explainer is preparing a focused review..."):
                        try:
                            crew = Crew(
                                agents=[explainer], tasks=[reteaching_task],
                                process=Process.sequential, verbose=True
                            )
                            result = crew.kickoff(inputs={
                                "topic": session["topic"],
                                "question": session["questions"][selected],
                                "student_answer": st.session_state.leo_answers[selected],
                                "feedback": evaluations[selected],
                            })
                            st.session_state.leo_reteaching[selected] = str(result)
                        except Exception as error:
                            show_error("targeted reteaching", error)
                if selected in st.session_state.leo_reteaching:
                    st.markdown(st.session_state.leo_reteaching[selected])
                    st.markdown("**Your turn:** Answer the follow-up question from the Explainer.")
                    followup_key = f"leo_followup_answer_{selected}"
                    with st.form(key=f"leo_followup_form_{selected}"):
                        followup_answer = st.text_area(
                            "Your follow-up answer",
                            value=st.session_state.leo_followup_answers.get(selected, ""),
                            placeholder="Write your answer here...",
                            key=followup_key,
                            height=120,
                        )
                        submitted_followup = st.form_submit_button(
                            "Submit follow-up answer for evaluation", type="primary"
                        )
                    if submitted_followup:
                        if not followup_answer.strip():
                            st.warning("Please write an answer before submitting.")
                        else:
                            st.session_state.leo_followup_answers[selected] = followup_answer.strip()
                            with st.spinner("Evaluator is reviewing your follow-up answer..."):
                                try:
                                    followup_question = "Follow-up question from targeted reteaching:\n" + st.session_state.leo_reteaching[selected]
                                    followup_result = evaluate_one(
                                        session["topic"], followup_question, followup_answer.strip()
                                    )
                                    st.session_state.leo_followup_evaluations[selected] = followup_result
                                except Exception as error:
                                    show_error("follow-up answer evaluation", error)
                    if selected in st.session_state.leo_followup_evaluations:
                        st.markdown("#### Follow-up evaluation")
                        st.markdown(st.session_state.leo_followup_evaluations[selected])

    with st.expander("🧠 Session memory"):
        st.write(f"**Topic:** {session['topic']}")
        st.write(f"**Lesson stored:** {'Yes' if session['lesson'] else 'No'}")
        st.write(f"**Questions stored:** {len(session['questions'])}")
        st.write(f"**Answers submitted:** {len(st.session_state.leo_answers)}")
        st.write(f"**Evaluations returned:** {sum(x is not None for x in st.session_state.leo_evaluations)}")
        st.write(f"**Reteaching results stored:** {len(st.session_state.leo_reteaching)}")
        st.write(f"**Follow-up answers submitted:** {len(st.session_state.leo_followup_answers)}")

st.caption("Leo AI Tutor · CrewAI + Gemini + Streamlit")
