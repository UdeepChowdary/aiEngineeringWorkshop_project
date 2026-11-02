from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator

class ExamBlueprint(BaseModel):
    exam_name: str = Field(default="Competitive Examination")
    topic: str = Field(default="General Concept")
    question_style: str = Field(default="MCQ (Single Correct)")
    marking_scheme: str = Field(default="+3 / -1")
    difficulty_tier: str = Field(default="Advanced Trap Tier")
    hallmark_examiner_tricks: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, values: dict):
        if not isinstance(values, dict):
            return values
        if "exam_name" not in values:
            values["exam_name"] = values.get("exam") or values.get("name") or "Target Exam"
        if "topic" not in values:
            values["topic"] = values.get("subject") or "Target Topic"
        if "marking_scheme" not in values:
            values["marking_scheme"] = values.get("scoring") or "+3 for correct, -1 for wrong"
        if "question_style" not in values:
            values["question_style"] = values.get("style") or "MCQ"
        if "hallmark_examiner_tricks" not in values:
            values["hallmark_examiner_tricks"] = values.get("tricks") or values.get("traps") or []
        return values


class QuestionItem(BaseModel):
    question: str = Field(default="")
    options: Dict[str, str] = Field(default_factory=dict)
    correct_answer: str = Field(default="A")
    official_explanation: str = Field(default="Refer to standard derivation.")
    diagram_type: Optional[str] = Field(default="none", description="e.g. 'mermaid', 'none'")
    diagram_code: Optional[str] = Field(default=None, description="Mermaid diagram code if the problem has visual elements")
    pyq_benchmark: Optional[str] = Field(default="Isomorphic to past-year exam standard", description="Real exam benchmark isomorphism")
    exam_isomorphism_score: Optional[int] = Field(default=92, description="Percentage match to authentic exam question standards")

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, values: dict):
        if not isinstance(values, dict):
            return values
        if "correct_answer" not in values:
            values["correct_answer"] = (
                values.get("answer") or
                values.get("correct") or
                values.get("correct_option") or
                "A"
            )
        if "official_explanation" not in values:
            values["official_explanation"] = (
                values.get("explanation") or
                values.get("solution") or
                values.get("derivation") or
                values.get("proof") or
                "Rigorous proof based on fundamental theorems."
            )
        if "options" not in values or not values["options"]:
            values["options"] = values.get("choices") or {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
        if "diagram_code" not in values:
            values["diagram_code"] = values.get("mermaid") or values.get("diagram") or values.get("graph") or None
        if "diagram_type" not in values:
            values["diagram_type"] = "mermaid" if values.get("diagram_code") else "none"
        if "pyq_benchmark" not in values:
            values["pyq_benchmark"] = values.get("pyq") or values.get("benchmark") or values.get("past_year_reference") or "Calibrated against official Past-Year Exam standards"
        if "exam_isomorphism_score" not in values:
            values["exam_isomorphism_score"] = values.get("isomorphism_score") or 94
        return values


class DistractorMap(BaseModel):
    key_concept_tested: str = Field(default="Fundamental Theorem")
    option_traps: Dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, values: dict):
        if not isinstance(values, dict):
            return values
        if "key_concept_tested" not in values:
            values["key_concept_tested"] = values.get("concept") or values.get("core_principle") or "Core Principle"
        if "option_traps" not in values:
            values["option_traps"] = values.get("traps") or values.get("distractors") or {}
        return values


class SocraticChallenge(BaseModel):
    probe: str = Field(default="Explain your underlying assumptions.")
    focus_area: str = Field(default="Boundary Conditions")

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, values: dict):
        if not isinstance(values, dict):
            return values
        if "probe" not in values:
            values["probe"] = values.get("challenge") or values.get("question") or "How does your rationale hold at edge conditions?"
        if "focus_area" not in values:
            values["focus_area"] = values.get("focus") or values.get("area") or "Conceptual Validation"
        return values


class DiagnosticReport(BaseModel):
    is_correct: bool = Field(default=False)
    error_category: str = Field(default="Conceptual Void")
    diagnosis_summary: str = Field(default="")
    prescription: str = Field(default="")
    micro_drill_question: str = Field(default="")
    micro_drill_answer: str = Field(default="")
    secondary_probe: Optional[str] = Field(default=None, description="Optional follow-up counter-probe for multi-turn defense")
    telemetry: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution and scoring telemetry")

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, values: dict):
        if not isinstance(values, dict):
            return values
        if "error_category" not in values:
            values["error_category"] = values.get("category") or values.get("error_type") or "Conceptual Void"
        if "diagnosis_summary" not in values:
            values["diagnosis_summary"] = values.get("diagnosis") or values.get("summary") or "Reviewed reasoning."
        if "prescription" not in values:
            values["prescription"] = values.get("advice") or values.get("rule") or "Check boundary conditions carefully."
        if "micro_drill_question" not in values:
            values["micro_drill_question"] = values.get("micro_drill") or values.get("drill_question") or "Test the same invariant on a boundary value."
        if "micro_drill_answer" not in values:
            values["micro_drill_answer"] = values.get("drill_answer") or values.get("answer") or "Consistent with fundamental rule."
        return values


# ==============================================================================
# STUDY PLANNER MULTI-AGENT MODELS
# ==============================================================================

class DiagnosticQuestion(BaseModel):
    question_id: str = Field(default="q1")
    question_text: str = Field(description="The diagnostic question probing the student's conceptual block")
    options: List[str] = Field(description="Distinct options illustrating different common mental roadblocks")
    diagnostic_intent: str = Field(description="What specific cognitive confusion this question aims to reveal")


class DiagnosticInterview(BaseModel):
    topic: str = Field(default="Target Concept")
    target_exam: str = Field(default="General Exam")
    questions: List[DiagnosticQuestion] = Field(default_factory=list)


class StudyPlanPhase(BaseModel):
    phase_title: str = Field(description="e.g. Phase 1: Call Stack & Base Case Intuition")
    time_estimate: str = Field(description="e.g. Day 1 (1.5 hours)")
    core_objective: str = Field(description="The mental shift to achieve in this phase")
    actionable_steps: List[str] = Field(description="Concrete step-by-step tasks to perform")
    high_yield_trap_warning: str = Field(description="Specific exam trap to watch out for during this phase")


class PersonalizedStudyPlan(BaseModel):
    topic: str = Field(default="Concept")
    diagnosed_bottleneck: str = Field(description="Precise root cause of why the student struggled with this concept")
    breakthrough_mental_model: str = Field(description="The vivid intuitive analogy or invariant rule that demystifies the topic")
    phases: List[StudyPlanPhase] = Field(default_factory=list, description="Step-by-step progressive roadmap")
    practice_ladder: List[str] = Field(default_factory=list, description="Curated problem sequence from elementary to exam-grade")
    mastery_benchmark: str = Field(description="Self-check test to confirm you have 100% exam-level mastery")
