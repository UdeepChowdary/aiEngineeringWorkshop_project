"""Headless test script to verify that all agents in the pipeline execute end-to-end cleanly."""
from config import get_gemini_client
from agents import (
    ExamProfilerAgent,
    QuestionSetterAgent,
    TrapAnalystAgent,
    SocraticInterrogatorAgent,
    DiagnosticEvaluatorAgent
)

def test_pipeline():
    print("1. Initializing Gemini client...")
    client = get_gemini_client()

    print("2. Testing ExamProfilerAgent...")
    profiler = ExamProfilerAgent(client)
    blueprint = profiler.run("GATE CS", "Deadlock Detection & Banker's Algorithm")
    print(f"   [+] Exam: {blueprint.exam_name}, Style: {blueprint.question_style}")

    print("3. Testing QuestionSetterAgent...")
    setter = QuestionSetterAgent(client)
    question = setter.run(blueprint)
    print(f"   [+] Question Generated: {question.question[:60]}...")
    print(f"   [+] Options: {list(question.options.keys())}, Correct: {question.correct_answer}")

    print("4. Testing TrapAnalystAgent...")
    trap_analyst = TrapAnalystAgent(client)
    distractor_map = trap_analyst.run(blueprint, question)
    print(f"   [+] Traps Analyzed: {list(distractor_map.option_traps.keys())}")

    print("5. Testing SocraticInterrogatorAgent...")
    socratic = SocraticInterrogatorAgent(client)
    probe = socratic.run(
        blueprint=blueprint,
        question=question,
        distractor_map=distractor_map,
        user_choice="B",
        user_reasoning="Because Banker's algorithm requires allocation to not exceed maximum claim."
    )
    print(f"   [+] Socratic Probe: {probe.probe[:80]}...")

    print("6. Testing DiagnosticEvaluatorAgent...")
    evaluator = DiagnosticEvaluatorAgent(client)
    report = evaluator.run(
        blueprint=blueprint,
        question=question,
        distractor_map=distractor_map,
        initial_choice="B",
        initial_reasoning="Because Banker's algorithm requires allocation to not exceed maximum claim.",
        defense_response="I stick with B because safety state check is guaranteed."
    )
    print(f"   [+] Category: {report.error_category}")
    print(f"   [+] Micro-Drill: {report.micro_drill_question[:60]}...")
    print("\n>>> ALL 5 AGENTS EXECUTED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_pipeline()
