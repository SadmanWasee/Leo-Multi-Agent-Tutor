
import re
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from crewai import Crew, Process

from agents.explainer import explainer
from agents.quiz_master import quiz_master
from agents.evaluator import evaluator
from agents.coordinator import coordinator

from tasks.coordinator_task import coordinator_task
from tasks.explanation_task import explanation_task
from tasks.quiz_task import quiz_task
from tasks.evaluation_task import evaluation_task
from tasks.reteaching_task import reteaching_task


def handle_agent_error(stage, error):
    """Display a helpful message when an agent fails."""
    error_message = str(error).lower()

    print(f"\nLeo encountered a problem during: {stage}")

    if (
        "429" in error_message
        or "resource_exhausted" in error_message
        or "quota" in error_message
        or "rate limit" in error_message
    ):
        print(
            "\nThe Gemini API quota or rate limit has been reached.\n"
            "Please check your Gemini API usage and wait until "
            "your quota resets before trying again."
        )
    else:
        print(
            "\nThe agent could not complete this stage.\n"
            "Please check your internet connection, API configuration, "
            "and terminal error details."
        )

    print(f"\nError type: {type(error).__name__}")


def extract_questions(quiz_text):
    """Extract and clean the numbered quiz questions."""
    parts = re.split(
        r"(?m)^\s*\d+[.)]\s+",
        quiz_text.strip()
    )

    questions = []

    for part in parts[1:]:
        question = part.strip()

        question = re.sub(
            r"(?im)^\s*(?:#{1,6}\s*)?"
            r"(?:\*\*)?"
            r"(?:conceptual questions|practical questions)"
            r"(?:\*\*)?\s*$",
            "",
            question
        )

        question = re.sub(
            r"(?m)^\s*[-*_]{3,}\s*$",
            "",
            question
        )

        question = question.strip()

        if question:
            questions.append(question)

    return questions


def extract_score(feedback):
    """Extract a score such as 7/10 or 7 out of 10."""
    score_match = re.search(
        r"(?i)(\d+(?:\.\d+)?)\s*(?:/|out of)\s*10\b",
        feedback
    )

    if score_match:
        score = float(score_match.group(1))

        if 0 <= score <= 10:
            return score

    return None


def should_trigger_feedback_loop(score):
    """Return True when a valid score is below 6/10."""
    return score is not None and score < 6


def extract_follow_up_question(reteaching_text):
    """Extract the final follow-up question from reteaching output."""
    text = str(reteaching_text).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in reversed(lines):
        cleaned_line = re.sub(
            r"^\s*(?:[-*]|\d+[.)])\s*",
            "",
            line
        )

        cleaned_line = re.sub(
            r"^\s*\*\*(?:follow-up question|question)\s*:\*\*\s*",
            "",
            cleaned_line,
            flags=re.IGNORECASE
        )

        if "?" in cleaned_line:
            question_parts = re.findall(r"[^.!?]*\?", cleaned_line)

            if question_parts:
                return question_parts[-1].strip()

            return cleaned_line

    question_matches = re.findall(r"[^.!?\n]*\?", text)

    if question_matches:
        return question_matches[-1].strip()

    return None


def main():
    print("\n===== LEO: MULTI-AGENT AI TUTOR =====\n")
    print("Welcome! Leo will explain a topic, quiz you,")
    print("evaluate your answers, and provide feedback.\n")

    # Get the topic from the student.
    topic = input("What topic would you like to learn? ").strip()

    if not topic:
        print("\nPlease enter a topic and try again.")
        return

    # --------------------------------------------------
    # SESSION MEMORY
    # --------------------------------------------------
    # This dictionary stores information for the current run.
    session_memory = {
        "topic": topic,
        "lesson": "",
        "questions": [],
        "answers": [],
        "scores": [],
        "evaluations": [],
        "reteaching_sessions": []
    }

    print("\nSession memory initialized.")
    print(f"Learning topic: {session_memory['topic']}")

    # --------------------------------------------------
    # STAGE 1: PLAN, EXPLAIN, AND GENERATE THE QUIZ
    # --------------------------------------------------
    print("\n===== STAGE 1: LEARNING =====")
    print("Coordinator is planning your learning session...")
    print("Explainer will prepare your lesson.")
    print("Quiz Master will prepare your questions afterward.\n")

    learning_crew = Crew(
        agents=[
            coordinator,
            explainer,
            quiz_master
        ],
        tasks=[
            coordinator_task,
            explanation_task,
            quiz_task
        ],
        process=Process.sequential,
        verbose=True
    )

    try:
        learning_crew.kickoff(inputs={"topic": topic})

        lesson = explanation_task.output.raw
        quiz = quiz_task.output.raw

        # Store the generated lesson in session memory.
        session_memory["lesson"] = lesson

    except Exception as error:
        handle_agent_error("lesson and quiz generation", error)
        return

    if not lesson or not quiz:
        print("\nLeo could not generate the lesson or quiz.")
        print("Please try again later.")
        return

    print("\n===== YOUR LESSON =====\n")
    print(lesson)

    questions = extract_questions(quiz)

    if len(questions) != 5:
        print(
            f"\nLeo expected 5 quiz questions but found "
            f"{len(questions)}."
        )
        print("\nRaw quiz output:")
        print(quiz)
        print(
            "\nPlease check the prompt in tasks/quiz_task.py "
            "and try again."
        )
        return

    # Store the questions in session memory.
    session_memory["questions"] = questions.copy()

    print("\n===== YOUR QUIZ =====\n")

    for index, question in enumerate(questions, start=1):
        print(f"{index}. {question}\n")

    # --------------------------------------------------
    # STAGE 2: COLLECT STUDENT ANSWERS
    # --------------------------------------------------
    print("\n===== STAGE 2: ANSWER THE QUIZ =====")
    print("Answer each question in your own words.")
    print("Your answers will be evaluated individually.\n")

    student_answers = []

    for index, question in enumerate(questions, start=1):
        print(f"\nQuestion {index}:")
        print(question)

        answer = input("\nYour answer: ").strip()

        while not answer:
            print("Your answer cannot be empty.")
            answer = input("Your answer: ").strip()

        student_answers.append(answer)

        # Store each answer as it is submitted.
        session_memory["answers"].append(answer)

    # --------------------------------------------------
    # STAGE 3: EVALUATE STUDENT ANSWERS
    # --------------------------------------------------
    print("\n===== STAGE 3: EVALUATION =====")

    scores = []
    evaluation_results = []

    for index, question in enumerate(questions):
        question_number = index + 1

        print(
            f"\n===== EVALUATING ANSWER "
            f"{question_number} OF {len(questions)} =====\n"
        )

        evaluation_crew = Crew(
            agents=[evaluator],
            tasks=[evaluation_task],
            process=Process.sequential,
            verbose=True
        )

        try:
            result = evaluation_crew.kickoff(
                inputs={
                    "topic": topic,
                    "question": question,
                    "student_answer": student_answers[index]
                }
            )

            feedback = str(result)

        except Exception as error:
            handle_agent_error(
                f"evaluation of answer {question_number}",
                error
            )
            print(
                "\nThe evaluation stopped because the agent "
                "could not complete this answer."
            )
            print(
                "Run the program again when the issue is resolved."
            )
            return

        evaluation_results.append(feedback)

        print(
            f"\n--- Feedback for Question "
            f"{question_number} ---\n"
        )
        print(feedback)

        # Save evaluation feedback in session memory.
        session_memory["evaluations"].append(feedback)

        # Extract and save the score.
        score = extract_score(feedback)
        scores.append(score)
        session_memory["scores"].append(score)

        if score is None:
            print(
                "\nLeo could not automatically extract a score "
                "from this feedback."
            )

        elif should_trigger_feedback_loop(score):
            print("\n===== FEEDBACK LOOP ACTIVATED =====\n")
            print(
                f"Your score was {score:g}/10. "
                "Leo will review the concepts you found difficult."
            )

            reteaching_crew = Crew(
                agents=[explainer],
                tasks=[reteaching_task],
                process=Process.sequential,
                verbose=True
            )

            try:
                reteaching_result = reteaching_crew.kickoff(
                    inputs={
                        "topic": topic,
                        "question": question,
                        "student_answer": student_answers[index],
                        "feedback": feedback
                    }
                )

                reteaching_text = str(reteaching_result)

                print("\n===== TARGETED RETEACHING =====\n")
                print(reteaching_text)

                # Store reteaching details in session memory.
                reteaching_record = {
                    "question": question,
                    "original_answer": student_answers[index],
                    "original_score": score,
                    "explanation": reteaching_text,
                    "follow_up_question": None,
                    "follow_up_answer": None,
                    "follow_up_evaluation": None
                }

                session_memory["reteaching_sessions"].append(
                    reteaching_record
                )

                follow_up_question = extract_follow_up_question(
                    reteaching_text
                )

                if not follow_up_question:
                    print(
                        "\nLeo could not identify a separate follow-up "
                        "question in the reteaching response. "
                        "Skipping follow-up evaluation for this answer."
                    )
                    continue

                reteaching_record["follow_up_question"] = (
                    follow_up_question
                )

                print("\n===== FOLLOW-UP QUESTION =====\n")
                print(follow_up_question)

                follow_up_answer = input(
                    "\nYour answer to the follow-up question: "
                ).strip()

                while not follow_up_answer:
                    print("Please enter an answer before continuing.")
                    follow_up_answer = input(
                        "Your answer to the follow-up question: "
                    ).strip()

                reteaching_record["follow_up_answer"] = follow_up_answer

                follow_up_crew = Crew(
                    agents=[evaluator],
                    tasks=[evaluation_task],
                    process=Process.sequential,
                    verbose=True
                )

                follow_up_result = follow_up_crew.kickoff(
                    inputs={
                        "topic": topic,
                        "question": follow_up_question,
                        "student_answer": follow_up_answer
                    }
                )

                follow_up_feedback = str(follow_up_result)

                print("\n===== FOLLOW-UP EVALUATION =====\n")
                print(follow_up_feedback)

                # Save the follow-up evaluation.
                reteaching_record["follow_up_evaluation"] = (
                    follow_up_feedback
                )

            except Exception as error:
                handle_agent_error("feedback loop", error)
                print(
                    "\nLeo could not finish the feedback loop. "
                    "The original quiz results will still be reported."
                )

    # --------------------------------------------------
    # STAGE 4: DISPLAY THE FINAL REPORT
    # --------------------------------------------------
    print("\n===== FINAL QUIZ REPORT =====\n")

    for index, score in enumerate(scores, start=1):
        if score is not None:
            print(f"Question {index}: {score:g}/10")
        else:
            print(f"Question {index}: Score unavailable")

    available_scores = [
        score for score in scores
        if score is not None
    ]

    if len(available_scores) == len(questions):
        total_score = sum(available_scores)
        average_score = total_score / len(questions)

        print(f"\nTotal score: {total_score:g}/50")
        print(f"Average score: {average_score:.1f}/10")

        percentage = (total_score / 50) * 100
        print(f"Percentage: {percentage:.1f}%")

    else:
        print(
            "\nA complete total could not be calculated because "
            "one or more scores were unavailable."
        )

    # --------------------------------------------------
    # DISPLAY SESSION MEMORY SUMMARY
    # --------------------------------------------------
    print("\n===== SESSION MEMORY SUMMARY =====")
    print(f"Topic: {session_memory['topic']}")
    print(f"Lesson stored: {bool(session_memory['lesson'])}")
    print(f"Questions stored: {len(session_memory['questions'])}")
    print(f"Answers stored: {len(session_memory['answers'])}")
    print(f"Evaluations stored: {len(session_memory['evaluations'])}")
    print(f"Scores stored: {len(session_memory['scores'])}")
    print(
        "Reteaching sessions: "
        f"{len(session_memory['reteaching_sessions'])}"
    )

    print("\n===== LEARNING SESSION COMPLETE =====")
    print("Thank you for learning with Leo!")


if __name__ == "__main__":
    main()
