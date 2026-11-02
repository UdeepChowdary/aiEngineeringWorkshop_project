import json
import re
import time
from typing import Dict, Any
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from config import MODELS
from models import (
    ExamBlueprint,
    QuestionItem,
    DistractorMap,
    SocraticChallenge,
    DiagnosticReport
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
    """Agent 1: Crafts exam-grade authentic problems with deliberate distractors."""

    def __init__(self, client: genai.Client):
        self.client = client
        self.name = "Question Setter (Chief Examiner)"

    def run(self, blueprint: ExamBlueprint) -> QuestionItem:
        system_prompt = f"""You are the Chief Question Setter for {blueprint.exam_name}.
Compose an authentic, high-caliber question on '{blueprint.topic}'.
Difficulty Tier: {blueprint.difficulty_tier}
Question Style: {blueprint.question_style}

Rules:
1. No simple trivia. The problem must require multi-step reasoning or mathematical application.
2. Provide 4 distinct options: A, B, C, D with 3 deceptive distractor traps.
3. Keep the problem and explanation concise and precise.

Output JSON:
{{
  "question": "Problem statement",
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
        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return QuestionItem(**data)


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
Provide a 60-second micro-drill question with answer.

Output JSON:
{{
  "is_correct": {str(is_correct).lower()},
  "error_category": "One of the 5 categories above",
  "diagnosis_summary": "1-2 sentence diagnosis",
  "prescription": "Exam-day rule of thumb",
  "micro_drill_question": "Short 1-minute problem testing the exact point of confusion",
  "micro_drill_answer": "Answer and brief proof"
}}"""
        user_prompt = f"Question: {question.question}\nOfficial Explanation: {question.official_explanation}"
        data = _call_gemini_json(self.client, system_prompt, user_prompt)
        return DiagnosticReport(**data)
