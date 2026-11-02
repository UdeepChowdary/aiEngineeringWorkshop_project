# 🛡️ ExamSentinel: Universal Multi-Agent Competitive Exam Sparring Engine

An adversarial, multi-agent AI system designed specifically for **competitive exam preparation** (e.g., GATE, JEE, CAT, GRE, GMAT, UPSC, USMLE, CFA, SAT).

Unlike standard "EdTech" apps that serve passive videos or trivial quizzes, **ExamSentinel** simulates a full **Examiner Committee** that crafts high-difficulty problems with deliberate traps, interrogates your thought process in a live Socratic oral defense, deconstructs the psychology of every distractor option, and diagnoses your exact cognitive failure modes.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([User / Aspirant]) --> Controller[Orchestrator]

    subgraph "Multi-Agent Committee"
        Controller --> Agent0[0. Exam Profiler Agent<br/>Dynamically creates Exam Blueprint]
        Agent0 --> Agent1[1. Question Setter Agent<br/>Crafts exam-grade problem with deliberate traps]
        Agent1 --> Agent2[2. Trap & Distractor Analyst<br/>Deconstructs candidate fallacies & psychological traps]
        Agent2 --> Agent3[3. Socratic Interrogator Agent<br/>Conducts live oral defense & conviction test]
        Agent3 --> Agent4[4. Diagnostic & Remediation Agent<br/>Root-cause error categorization + 60s micro-drill]
    end

    User <-->|Live Defense Sparring| Agent3
    Agent4 --> UserSummary([Post-Mortem Dossier & Targeted Drill])
```

---

## 🤖 The Multi-Agent Roster

| Agent | Responsibility | Why It Needs to Be a Dedicated Agent |
| :--- | :--- | :--- |
| **0. Exam Profiler** | Exam Calibration | Ingests *any* exam name (e.g. "GATE CS", "USMLE Step 1") and automatically infers marking schemes (e.g., negative marking penalties), question styles (MCQ, MSQ, NAT), and difficulty standards. |
| **1. Question Setter (Chief Examiner)** | Problem Generation | Specialized in crafting multi-step, multi-concept problems with realistic boundary conditions rather than simple trivia. |
| **2. Trap & Distractor Analyst** | Psychological Deconstruction | Pre-computes why each incorrect option is seductive (e.g. forgetting a unit conversion, assuming linear approximation, neglecting $x \ge 0$). |
| **3. Socratic Interrogator** | Interactive Sparring | Never immediately says "Right" or "Wrong". It aggressively probes your assumptions and boundary conditions to verify you didn't make a lucky guess. |
| **4. Diagnostic & Remediation Evaluator** | Root-Cause Post-Mortem | Classifies errors into 5 cognitive categories: *Mastered*, *Trap Victim*, *Conceptual Void*, *Calculation Slip*, or *Unjustified Guess*, and prescribes an instant 60-second micro-drill. |

---

## 🚀 Quickstart Guide

### 1. Requirements
Ensure you have the required packages installed:
```bash
pip install groq rich pydantic python-dotenv
```

### 2. Environment Setup
Your Groq API key can be set in an `.env` file or exported as an environment variable:
```bash
# Optional if set in config.py
export GROQ_API_KEY="your-groq-api-key"
```

### 3. Launch the Sparring Engine
Run the main interactive entry point:
```bash
python main.py
```

You can choose from popular exam presets or type **`C`** to test **ANY exam and topic** on the planet!

---

## 📁 Project Structure

```
aiEngineeringWorkshop/
├── config.py           # Groq client initialization, model defaults, API key handling
├── models.py           # Pydantic data schemas enforcing strict agent-to-agent contracts
├── agents.py           # Implementations of the 5 specialized AI agents
├── orchestrator.py     # State machine and rich terminal UI interaction loop
├── main.py             # CLI entrypoint with presets, custom exam mode, and session tracking
├── script.py           # Original single-agent baseline script
└── README.md           # Architecture documentation & workshop guide
```

---

## 💡 AI Engineering Workshop Talking Points

1. **Why Multi-Agent beats Single-Prompt LLMs:**
   * A single prompt asked to *"Make an exam question, quiz the user, be Socratic, and analyze mistakes"* degrades in quality due to attention fragmentation.
   * By separating concerns into **Question Setter $\rightarrow$ Trap Analyst $\rightarrow$ Socratic Interrogator $\rightarrow$ Diagnostic Evaluator**, each agent operates with a focused system prompt and zero persona bleed.
2. **Deterministic Schemas via Pydantic:**
   * Agents pass typed, validated JSON structures (`ExamBlueprint`, `DistractorMap`, `DiagnosticReport`), preventing hallucinations from breaking the execution pipeline.
3. **High-Speed Official Google GenAI SDK:**
   * Running on official Google Gemini models (`gemini-3.5-flash`) ensures robust reasoning, native JSON schema support, and rapid turnaround for conversational sparring.
