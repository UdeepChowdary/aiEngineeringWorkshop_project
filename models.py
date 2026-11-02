from typing import Dict, List, Optional
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
            # If options were nested or missing
            values["options"] = values.get("choices") or {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
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
