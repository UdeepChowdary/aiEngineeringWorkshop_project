import json
import re
import time
from typing import Dict, Any, List
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from config import MODELS
from models import (
    ExamBlueprint,
    QuestionItem,
    DistractorMap,
    SocraticChallenge,
    DiagnosticReport,
    DiagnosticQuestion,
    DiagnosticInterview,
    StudyPlanPhase,
    PersonalizedStudyPlan
)

def _clean_json_str(text: str) -> str:
    """Extracts valid JSON substring from LLM response, stripping markdown blocks."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

def _call_gemini_json(client: genai.Client, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Invokes Google Gemini with JSON mode enabled and automatic model failover."""
    last_err = None
    for model in MODELS:
        for attempt in range(2):
            try:
                config = types.GenerateContentConfig(
                    system_instruction=f"{system_prompt}\nIMPORTANT: Respond ONLY with a valid JSON object matching the requested schema. No conversational filler, no markdown fences.",
                    response_mime_type="application/json",
                    temperature=0.2,
                )
                response = client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=config
                )
                raw_content = response.text or ""
                cleaned = _clean_json_str(raw_content)
                return json.loads(cleaned)
            except (ClientError, ServerError) as e:
                last_err = e
                time.sleep(1.0)
            except json.JSONDecodeError:
                continue
            except Exception as e:
                last_err = e
                break

    raise RuntimeError(f"All Gemini models exhausted. Last error: {last_err}")


class ExamProfilerAgent:
    """Agent 0: Calibrates the exam parameters, question style, marking rules, and difficulty dynamically."""
    
    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Exam Profiler"

    def run(self, exam_name: str, topic: str) -> ExamBlueprint:
        system_prompt = """You are an Exam Blueprint Architect for competitive examinations worldwide (GATE, JEE, CAT, GRE, GMAT, UPSC, USMLE, CFA, SAT, etc.).
Analyze the exam and topic.
Output a JSON object:
{
  "exam_name": "Official name",
  "topic": "Target topic",
  "question_style": "e.g. MCQ (Single Correct), MSQ, or Numerical",
  "marking_scheme": "Scoring rules (e.g. +3 for correct, -1 for negative marking)",
  "difficulty_tier": "Advanced / Concept Trap",
  "hallmark_examiner_tricks": ["trick 1", "trick 2"]
}"""
        user_prompt = f"Target Exam: {exam_name}\nTarget Topic: {topic}"
        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return ExamBlueprint(**data)


class QuestionSetterAgent:
    """Agent 1: Crafts exam-grade authentic problems with deliberate distractors, visual diagrams (Mermaid), and real PYQ benchmarks."""

    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Question Setter (Chief Examiner)"

    def run(self, blueprint: ExamBlueprint, critique: str = "") -> QuestionItem:
        system_prompt = f"""You are the Chief Question Setter for {blueprint.exam_name}.
Compose an authentic, high-caliber problem on '{blueprint.topic}'.
Difficulty Tier: {blueprint.difficulty_tier}
Question Style: {blueprint.question_style}

Rules:
1. No simple trivia. The problem must require multi-step reasoning or mathematical application.
2. Provide 4 distinct options: A, B, C, D with 3 deceptive distractor traps.
3. If the topic involves states, transitions, resource allocation, networks, trees, or flowcharts, generate a valid, clean Mermaid diagram in `diagram_code` and set `diagram_type` to "mermaid". If purely text/algebraic, set `diagram_type` to "none" and `diagram_code` to null.
4. Reference an authentic past-year exam standard in `pyq_benchmark` (e.g. "Isomorphic to GATE CS 2021 Question 44 on Banker's Safety Invariants") with an `exam_isomorphism_score` between 90 and 98.
5. Keep the problem and explanation concise and mathematically rigorous.

Output JSON:
{{
  "question": "Problem statement (use LaTeX $...$ or tabular formatting where helpful)",
  "diagram_type": "mermaid or none",
  "diagram_code": "mermaid string without markdown backticks, e.g. 'graph TD\\n  P0 --> R1' or null",
  "pyq_benchmark": "Real past exam isomorphism benchmark",
  "exam_isomorphism_score": 94,
  "options": {{
    "A": "Option text",
    "B": "Option text",
    "C": "Option text",
    "D": "Option text"
  }},
  "correct_answer": "A/B/C/D",
  "official_explanation": "Concise step-by-step mathematical/logical proof"
}}"""
        user_prompt = f"Generate an authentic {blueprint.exam_name} problem on '{blueprint.topic}' testing traps: {', '.join(blueprint.hallmark_examiner_tricks)}."
        if critique and critique.strip():
            user_prompt += f"\n\nCRITICAL AUDITOR FEEDBACK FROM PREVIOUS DRAFT:\n{critique}\nYou MUST fix this issue in your revised problem!"

        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return QuestionItem(**data)


class ExamAuditorAgent:
    """Agent 1.5 (LangGraph Quality Gate): Mathematical and Logical Quality Auditor."""

    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Exam Auditor & Verifier"

    def run(self, blueprint: ExamBlueprint, question: QuestionItem) -> Dict[str, Any]:
        system_prompt = f"""You are the Senior Mathematical & Logical Quality Auditor for {blueprint.exam_name}.
Your job is to independently audit the drafted question and answer key for mathematical precision, unambiguous wording, and correctness.

Evaluate:
1. Is the question mathematically sound and unambiguous?
2. Does the stated correct answer unequivocally match the rigorous derivation?
3. Are the options mutually distinct without duplicates or multiple correct answers?

Output JSON:
{{
  "is_sound": true or false,
  "audit_verdict": "VERIFIED" or "NEEDS_REVISION",
  "math_verification": "1-2 sentence verification breakdown",
  "critique": "Specific feedback if rejected, or 'Approved: Concept and mathematics sound' if verified"
}}"""
        user_prompt = f"""Exam: {blueprint.exam_name}
Question: {question.question}
Options: {json.dumps(question.options)}
Stated Answer: {question.correct_answer}
Derivation: {question.official_explanation}"""
        return _call_gemini_json(self.client, system_prompt, user_prompt)


class TrapAnalystAgent:
    """Agent 2: Dissects the psychological and cognitive traps behind each distractor."""

    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Trap & Distractor Analyst"

    def run(self, blueprint: ExamBlueprint, question: QuestionItem) -> DistractorMap:
        system_prompt = """You are an Expert Cognitive Trap Analyst.
Examine the question, options, and correct answer.
Map out the trap in each incorrect option and the core invariant concept.

Output JSON:
{
  "key_concept_tested": "Core fundamental principle",
  "option_traps": {
    "A": "Reason why a student picks this error",
    "B": "...",
    "C": "...",
    "D": "..."
  }
}"""
        user_prompt = f"""Exam: {blueprint.exam_name}
Question: {question.question}
Options: {json.dumps(question.options)}
Correct Answer: {question.correct_answer}"""
        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return DistractorMap(**data)


class SocraticInterrogatorAgent:
    """Agent 3: Spars with the candidate, challenging their rationale without giving away the answer."""

    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Socratic Sparring Partner"

    def run(self, blueprint: ExamBlueprint, question: QuestionItem, distractor_map: DistractorMap, user_choice: str, user_reasoning: str) -> SocraticChallenge:
        system_prompt = f"""You are the Socratic Interrogator in a live oral defense for {blueprint.exam_name}.
A student selected an answer and provided their reasoning.

Rules:
1. NEVER reveal if they are correct or incorrect.
2. Probe their reasoning in 2 sharp sentences. Stress-test their boundary condition or implicit assumptions.

Output JSON:
{{
  "probe": "2-sentence direct challenge to student",
  "focus_area": "Boundary condition or theorem probed"
}}"""
        user_prompt = f"""Question: {question.question}
Options: {json.dumps(question.options)}
Correct Answer: {question.correct_answer}
Candidate Choice: {user_choice}
Candidate Reasoning: {user_reasoning}"""
        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return SocraticChallenge(**data)


class DiagnosticEvaluatorAgent:
    """Agent 4: Evaluates final performance, diagnoses cognitive root cause, and generates targeted remediation."""

    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Diagnostic & Remediation Evaluator"

    def run(self, blueprint: ExamBlueprint, question: QuestionItem, distractor_map: DistractorMap, initial_choice: str, initial_reasoning: str, defense_response: str) -> DiagnosticReport:
        is_correct = (initial_choice.strip().upper() == question.correct_answer.strip().upper())

        system_prompt = f"""You are the Chief Diagnostic Evaluator for competitive exams.
Evaluate the candidate:
- Choice: {initial_choice} | Reasoning: {initial_reasoning}
- Defense: {defense_response}
- Correct Answer: {question.correct_answer}

Categorize into ONE: 'Mastered', 'Trap Victim', 'Conceptual Void', 'Calculation Slip', or 'Unjustified Guess'.
Provide a 60-second micro-drill question with answer, and formulate a follow-up secondary counter-probe for multi-turn sparring.

Output JSON:
{{
  "is_correct": {str(is_correct).lower()},
  "error_category": "One of the 5 categories above",
  "diagnosis_summary": "1-2 sentence diagnosis",
  "prescription": "Exam-day rule of thumb",
  "micro_drill_question": "Short 1-minute problem testing the exact point of confusion",
  "micro_drill_answer": "Answer and brief proof",
  "secondary_probe": "A sharp 1-sentence counter-challenge probing the candidate's remaining boundary blindspot"
}}"""
        user_prompt = f"Question: {question.question}\nOfficial Explanation: {question.official_explanation}"
        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return DiagnosticReport(**data)


# ==============================================================================
# STUDY PLANNER MULTI-AGENT COMMITTEE
# ==============================================================================

class StudyDiagnosticAgent:
    """Agent A: Formulates 3 diagnostic questions to pinpoint exactly where the student's mental model fails."""

    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Cognitive Diagnostic Interviewer"

    def run(self, target_exam: str, topic: str, user_description: str = "") -> DiagnosticInterview:
        system_prompt = f"""You are the Cognitive Diagnostic Interviewer Agent for competitive exams ({target_exam}).
A student is struggling with the topic: '{topic}'.
Their initial note: '{user_description}'

Your mission is NOT to explain the topic yet.
You must construct exactly 3 targeted multiple-choice diagnostic questions to pinpoint where their mental model collapses:
1. Question 1 (Intuition / Representation): How do they currently visualize or think about this concept?
2. Question 2 (The Cognitive Bottleneck): Where does their brain freeze? (e.g. for recursion: call stack visualization, trusting the induction hypothesis, formulating base cases).
3. Question 3 (Application / Boundary Traps): When problems get tricky in exams, what causes them to get stuck?

Each question must have 3-4 realistic options describing authentic student confusion.

Output JSON:
{{
  "topic": "{topic}",
  "target_exam": "{target_exam}",
  "questions": [
    {{
      "question_id": "q1",
      "question_text": "Diagnostic question 1...",
      "options": ["Option A...", "Option B...", "Option C...", "Option D..."],
      "diagnostic_intent": "What this reveals about their understanding"
    }},
    {{
      "question_id": "q2",
      "question_text": "Diagnostic question 2...",
      "options": ["Option A...", "Option B...", "Option C..."],
      "diagnostic_intent": "..."
    }},
    {{
      "question_id": "q3",
      "question_text": "Diagnostic question 3...",
      "options": ["Option A...", "Option B...", "Option C..."],
      "diagnostic_intent": "..."
    }}
  ]
}}"""
        user_prompt = f"Diagnose student roadblock on topic '{topic}' for exam '{target_exam}'. Additional context: '{user_description}'"
        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return DiagnosticInterview(**data)


class StudyPlanArchitectAgent:
    """Agent B: Synthesizes student interview answers into an actionable, scaffolded study plan."""

    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Master Curriculum & Study Architect"

    def run(self, target_exam: str, topic: str, interview: DiagnosticInterview, user_answers: Dict[str, str], extra_notes: str = "") -> PersonalizedStudyPlan:
        answers_summary = []
        for q in interview.questions:
            chosen = user_answers.get(q.question_id, "Not specified")
            answers_summary.append(f"- Question: {q.question_text}\n  Student's Answer: {chosen}\n  (Intent: {q.diagnostic_intent})")

        interview_context = "\n".join(answers_summary)

        system_prompt = f"""You are the Master Pedagogical & Curriculum Architect for competitive entrance exams ({target_exam}).
A student struggled with '{topic}', completed a diagnostic interview, and provided their exact responses.

Your task is to synthesize a high-impact, personalized, and non-generic study plan:
1. Diagnosed Bottleneck: Crisp, empathetic breakdown of their exact cognitive flaw (e.g., trying to trace recursion stack frames manually instead of mathematical induction).
2. Breakthrough Mental Model: A vivid, memorable analogy or rule-of-thumb that unlocks the concept instantly.
3. 3-Phase Progressive Study Roadmap:
   - Phase 1: Core Mental Shift & Invariant (Day 1)
   - Phase 2: Mechanics & Structural Pattern Recognition (Day 2)
   - Phase 3: Exam-Grade Traps & Timed PYQ Practice (Day 3)
4. Practice Ladder: 4-5 progressive problem archetypes to conquer in order.
5. Mastery Benchmark: An exact litmus test they can take to prove they're ready for {target_exam}.

Output JSON matching:
{{
  "topic": "{topic}",
  "diagnosed_bottleneck": "Clear diagnosis of why they were stuck",
  "breakthrough_mental_model": "Vivid intuition / mental model shift",
  "phases": [
    {{
      "phase_title": "Phase 1: ...",
      "time_estimate": "e.g. Day 1 (1.5 hrs)",
      "core_objective": "Specific milestone",
      "actionable_steps": ["Step 1", "Step 2", "Step 3"],
      "high_yield_trap_warning": "Watch out for..."
    }},
    {{
      "phase_title": "Phase 2: ...",
      "time_estimate": "e.g. Day 2 (2 hrs)",
      "core_objective": "...",
      "actionable_steps": ["Step 1", "Step 2"],
      "high_yield_trap_warning": "..."
    }},
    {{
      "phase_title": "Phase 3: ...",
      "time_estimate": "e.g. Day 3 (2 hrs)",
      "core_objective": "...",
      "actionable_steps": ["Step 1", "Step 2"],
      "high_yield_trap_warning": "..."
    }}
  ],
  "practice_ladder": ["Level 1: ...", "Level 2: ...", "Level 3: ...", "Level 4: ..."],
  "mastery_benchmark": "How to verify you have 100% exam-level mastery"
}}"""
        user_prompt = f"""Exam: {target_exam}
Topic: {topic}
Interview Diagnostic Responses:
{interview_context}
Additional Student Notes: {extra_notes}"""
        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return PersonalizedStudyPlan(**data)
