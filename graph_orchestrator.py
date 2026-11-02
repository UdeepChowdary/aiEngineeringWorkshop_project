"""LangGraph StateGraph Multi-Agent Orchestration for ExamSentinel.
Implements cyclic verification loops, state persistence, and autonomous self-correction.
"""
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, START, END

from config import get_gemini_client
from agents import (
    ExamProfilerAgent,
    QuestionSetterAgent,
    ExamAuditorAgent,
    TrapAnalystAgent,
    SocraticInterrogatorAgent,
    DiagnosticEvaluatorAgent
)
from models import (
    ExamBlueprint,
    QuestionItem,
    DistractorMap,
    SocraticChallenge,
    DiagnosticReport
)


class ExamGraphState(TypedDict):
    """The central state dictionary passed across all nodes in the LangGraph."""
    exam_name: str
    topic: str
    blueprint: Optional[ExamBlueprint]
    question: Optional[QuestionItem]
    audit_result: Optional[Dict[str, Any]]
    audit_retries: int
    distractor_map: Optional[DistractorMap]
    user_choice: Optional[str]
    user_reasoning: Optional[str]
    socratic_challenge: Optional[SocraticChallenge]
    defense_response: Optional[str]
    report: Optional[DiagnosticReport]
    execution_trace: List[str]


def create_exam_sparring_graph(api_key: str = None):
    """Constructs and compiles the full cyclic LangGraph for Exam Sparring."""
    client = get_gemini_client(api_key)

    # Initialize specialized agents
    profiler_agent = ExamProfilerAgent(client)
    setter_agent = QuestionSetterAgent(client)
    auditor_agent = ExamAuditorAgent(client)
    trap_agent = TrapAnalystAgent(client)
    socratic_agent = SocraticInterrogatorAgent(client)
    diagnostic_agent = DiagnosticEvaluatorAgent(client)

    # --- Node Definitions ---

    def node_profiler(state: ExamGraphState) -> Dict[str, Any]:
        blueprint = profiler_agent.run(state["exam_name"], state["topic"])
        trace = state.get("execution_trace", []) + ["1. Exam Profiler Node: Blueprint calibrated"]
        return {"blueprint": blueprint, "execution_trace": trace, "audit_retries": 0}

    def node_setter(state: ExamGraphState) -> Dict[str, Any]:
        critique = ""
        audit_res = state.get("audit_result")
        if audit_res and not audit_res.get("is_sound", True):
            critique = audit_res.get("critique", "")

        question = setter_agent.run(state["blueprint"], critique=critique)
        trace = state.get("execution_trace", [])
        if critique:
            trace.append("2. Question Setter Node: Revised question based on Auditor feedback")
        else:
            trace.append("2. Question Setter Node: Drafted initial exam problem")
        return {"question": question, "execution_trace": trace}

    def node_auditor(state: ExamGraphState) -> Dict[str, Any]:
        audit_result = auditor_agent.run(state["blueprint"], state["question"])
        retries = state.get("audit_retries", 0)
        verdict = "VERIFIED" if audit_result.get("is_sound", True) else "REJECTED (Needs Revision)"
        trace = state.get("execution_trace", []) + [f"3. Exam Auditor Node: Quality Gate -> {verdict}"]
        return {
            "audit_result": audit_result,
            "audit_retries": retries + 1,
            "execution_trace": trace
        }

    def node_trap_analyst(state: ExamGraphState) -> Dict[str, Any]:
        distractor_map = trap_agent.run(state["blueprint"], state["question"])
        trace = state.get("execution_trace", []) + ["4. Trap Analyst Node: Deconstructed distractor psychology"]
        return {"distractor_map": distractor_map, "execution_trace": trace}

    def node_socratic(state: ExamGraphState) -> Dict[str, Any]:
        challenge = socratic_agent.run(
            blueprint=state["blueprint"],
            question=state["question"],
            distractor_map=state["distractor_map"],
            user_choice=state.get("user_choice", "A"),
            user_reasoning=state.get("user_reasoning", "Standard reasoning")
        )
        trace = state.get("execution_trace", []) + ["5. Socratic Interrogator Node: Formulated challenge probe"]
        return {"socratic_challenge": challenge, "execution_trace": trace}

    def node_diagnostic(state: ExamGraphState) -> Dict[str, Any]:
        report = diagnostic_agent.run(
            blueprint=state["blueprint"],
            question=state["question"],
            distractor_map=state["distractor_map"],
            initial_choice=state.get("user_choice", "A"),
            initial_reasoning=state.get("user_reasoning", ""),
            defense_response=state.get("defense_response", "")
        )
        trace = state.get("execution_trace", []) + [f"6. Diagnostic Evaluator Node: Categorized as '{report.error_category}'"]
        return {"report": report, "execution_trace": trace}

    # --- Conditional Edge Logic (The Self-Healing Loop) ---

    def route_after_audit(state: ExamGraphState) -> str:
        audit_res = state.get("audit_result", {})
        is_sound = audit_res.get("is_sound", True)
        retries = state.get("audit_retries", 0)

        # If mathematically verified, or reached max self-correction budget (2 cycles)
        if is_sound or retries >= 2:
            return "trap_analyst"
        
        # Self-correction: Route BACK to setter
        return "setter"

    # --- Build the StateGraph ---
    workflow = StateGraph(ExamGraphState)

    workflow.add_node("profiler", node_profiler)
    workflow.add_node("setter", node_setter)
    workflow.add_node("auditor", node_auditor)
    workflow.add_node("trap_analyst", node_trap_analyst)
    workflow.add_node("socratic", node_socratic)
    workflow.add_node("diagnostic", node_diagnostic)

    # Edges
    workflow.add_edge(START, "profiler")
    workflow.add_edge("profiler", "setter")
    workflow.add_edge("setter", "auditor")

    # Cyclic conditional edge
    workflow.add_conditional_edges(
        "auditor",
        route_after_audit,
        {
            "setter": "setter",
            "trap_analyst": "trap_analyst"
        }
    )

    workflow.add_edge("trap_analyst", END)
    workflow.add_edge("socratic", END)
    workflow.add_edge("diagnostic", END)

    return workflow.compile()


def get_langgraph_mermaid_diagram() -> str:
    """Returns the visual Mermaid diagram syntax representing the compiled LangGraph architecture."""
    return """```mermaid
flowchart TD
    START([Start Session]) --> profiler[1. Exam Profiler Node<br/><i>Calibrates Exam Blueprint</i>]
    profiler --> setter[2. Question Setter Node<br/><i>Drafts authentic problem</i>]
    setter --> auditor[3. Exam Auditor Node<br/><i>Audits math & answer keys</i>]
    
    auditor -- "Rejected (Self-Healing Loop)" --> setter
    auditor -- "Approved / Verified" --> trap_analyst[4. Trap Analyst Node<br/><i>Deconstructs cognitive traps</i>]
    
    trap_analyst --> HumanInput([Human-in-the-Loop: Candidate Input & Reasoning])
    HumanInput --> socratic[5. Socratic Interrogator Node<br/><i>Oral defense probe</i>]
    
    socratic --> CandidateDefense([Human-in-the-Loop: Candidate Defense])
    CandidateDefense --> diagnostic[6. Diagnostic Evaluator Node<br/><i>Root-cause triage & micro-drill</i>]
    diagnostic --> END([Post-Mortem & Session Complete])
```"""
