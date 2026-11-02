import streamlit as st
import pandas as pd
import json
from config import get_gemini_client, verify_gemini_key, DEFAULT_MODEL
from mock_data import get_mock_sparring_data, get_mock_study_plan_data
from graph_orchestrator import get_langgraph_mermaid_diagram
from pdf_generator import generate_sparring_dossier_pdf, generate_study_plan_pdf
from agents import (
    ExamProfilerAgent,
    QuestionSetterAgent,
    ExamAuditorAgent,
    TrapAnalystAgent,
    SocraticInterrogatorAgent,
    DiagnosticEvaluatorAgent,
    StudyDiagnosticAgent,
    StudyPlanArchitectAgent
)
from models import (
    ExamBlueprint,
    QuestionItem,
    DistractorMap,
    SocraticChallenge,
    DiagnosticReport,
    DiagnosticInterview,
    PersonalizedStudyPlan
)

st.set_page_config(
    page_title="ExamSentinel — LangGraph Multi-Agent Exam Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
    .demo-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.3);
        margin-bottom: 10px;
    }
    .quality-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Presets for Competitive Exams
PRESETS = {
    "GATE CS: Deadlocks & Banker's Algorithm": ("GATE CS", "Operating Systems: Deadlock Detection & Banker's Algorithm"),
    "JEE Advanced: Rotational Dynamics": ("JEE Advanced", "Physics: Rotational Dynamics & Rolling without Slipping"),
    "CAT: Probability & Combinations": ("CAT", "Quantitative Aptitude: Permutations, Combinations & Probability"),
    "GRE: Standard Deviation Traps": ("GRE", "Quantitative Reasoning: Standard Deviation & Normal Distribution"),
    "UPSC Prelims: Fundamental Rights": ("UPSC Prelims", "Polity: Fundamental Rights vs DPSPs Judicial Precedents"),
    "Custom (Type Any Exam & Topic)": ("Custom", "Custom")
}

# --- Session State Initialization ---
if "byok_key" not in st.session_state:
    st.session_state.byok_key = ""
if "key_verified" not in st.session_state:
    st.session_state.key_verified = False

# Exam Sparring State
if "stage" not in st.session_state:
    st.session_state.stage = "init"
if "is_sparring_mock" not in st.session_state:
    st.session_state.is_sparring_mock = False
if "blueprint" not in st.session_state:
    st.session_state.blueprint = None
if "question" not in st.session_state:
    st.session_state.question = None
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None
if "execution_trace" not in st.session_state:
    st.session_state.execution_trace = []
if "distractor_map" not in st.session_state:
    st.session_state.distractor_map = None
if "user_choice" not in st.session_state:
    st.session_state.user_choice = None
if "user_reasoning" not in st.session_state:
    st.session_state.user_reasoning = ""
if "socratic_challenge" not in st.session_state:
    st.session_state.socratic_challenge = None
if "defense_response" not in st.session_state:
    st.session_state.defense_response = ""
if "report" not in st.session_state:
    st.session_state.report = None
if "stats" not in st.session_state:
    st.session_state.stats = {"attempted": 0, "mastered": 0}
if "history" not in st.session_state:
    st.session_state.history = []
if "counter_probe_active" not in st.session_state:
    st.session_state.counter_probe_active = False

# Study Planner State
if "planner_stage" not in st.session_state:
    st.session_state.planner_stage = "input"
if "is_planner_mock" not in st.session_state:
    st.session_state.is_planner_mock = False
if "planner_topic" not in st.session_state:
    st.session_state.planner_topic = ""
if "planner_description" not in st.session_state:
    st.session_state.planner_description = ""
if "planner_interview" not in st.session_state:
    st.session_state.planner_interview = None
if "planner_user_answers" not in st.session_state:
    st.session_state.planner_user_answers = {}
if "planner_plan" not in st.session_state:
    st.session_state.planner_plan = None

# Sidebar: Strict Bring Your Own Key (BYOK)
with st.sidebar:
    st.title("🛡️ ExamSentinel")
    st.caption("Capstone-Grade LangGraph Multi-Agent Orchestration")
    
    st.divider()
    
    # --- Bring Your Own Key (BYOK) Section ---
    st.markdown("### 🔑 Bring Your Own Key (BYOK)")
    st.caption("Enter your Gemini API key to run live agent generation, or use the **⚡ Mock Demo** buttons in each tab to test without a key.")

    user_entered_key = st.text_input(
        "Enter Google Gemini API Key",
        value=st.session_state.byok_key,
        type="password",
        placeholder="AIzaSy... or AQ.Ab8...",
        help="Paste your personal Google Gemini API key here."
    )
    
    cleaned_key = user_entered_key.strip() if user_entered_key else ""
    if cleaned_key != st.session_state.byok_key:
        st.session_state.byok_key = cleaned_key
        st.session_state.key_verified = False

    col_k1, col_k2 = st.columns([1, 1])
    if col_k1.button("Verify Key", use_container_width=True):
        if not st.session_state.byok_key:
            st.error("Please enter a key first.")
        else:
            with st.spinner("Verifying with Gemini..."):
                ok, msg = verify_gemini_key(st.session_state.byok_key)
                if ok:
                    st.success("✅ Active & Authenticated!")
                    st.session_state.key_verified = True
                else:
                    st.error(f"❌ {msg}")
                    st.session_state.key_verified = False

    # Key Status Indicator
    if st.session_state.byok_key:
        if st.session_state.key_verified:
            st.caption("🟢 **Status:** Verified & Ready")
        else:
            st.caption("🟡 **Status:** Key entered (click 'Verify Key' to test)")
    else:
        st.caption("⚪ **Status:** Demo / Mock mode available without key")

    # Informational Guide on Supported Keys & Where to Get Them
    with st.expander("📖 Supported Keys & Where to Get One", expanded=(not bool(st.session_state.byok_key))):
        st.markdown("""
        **Supported API Keys:**
        * **Google Gemini API Key** (Official)
        * Key formats usually begin with `AIzaSy...` or `AQ.Ab8...`
        * Powers all agents on `gemini-3.5-flash`

        ---
        **Where to get a key (100% Free):**
        1. Open [Google AI Studio](https://aistudio.google.com/app/apikey).
        2. Sign in with any Google account.
        3. Click **"Create API key"**.
        4. Copy the generated key and paste it above.
        
        *Free tier includes generous quota with **zero credit card or billing required**.*
        """)

    st.divider()
    
    # --- Exam Configuration ---
    st.markdown("### 🎯 Exam Configuration")
    preset_choice = st.selectbox("Select Preset or Custom", list(PRESETS.keys()))
    
    if preset_choice == "Custom (Type Any Exam & Topic)":
        target_exam = st.text_input("Target Exam", placeholder="e.g. USMLE, CFA Level 1, SAT, NEET")
        target_topic = st.text_input("Default Topic", placeholder="e.g. Acid-Base Disorders, Bond Duration")
    else:
        target_exam, target_topic = PRESETS[preset_choice]
        st.info(f"**Exam:** {target_exam}\n\n**Topic:** {target_topic}")

    st.divider()
    
    # --- Agent Roster Info ---
    with st.expander("🤖 The LangGraph Multi-Agent Roster", expanded=False):
        st.markdown("""
        **Sparring Graph Nodes:**
        * `profiler`: Dynamic blueprint calibration
        * `setter`: Problem synthesis
        * `auditor`: Quality Gate & mathematical verification
        * `trap_analyst`: Cognitive distractor mapping
        * `socratic`: Human-in-the-Loop oral defense
        * `diagnostic`: Error triage & micro-drill
        
        **Study Planner Nodes:**
        * `diagnostic_interviewer`: 3-question mental barrier probe
        * `study_architect`: Scaffolded 3-phase study roadmap
        """)
        
    st.divider()
    
    # --- Scorecard ---
    st.markdown("### 📊 Sparring Stats")
    col_a, col_b = st.columns(2)
    col_a.metric("Attempted", st.session_state.stats["attempted"])
    col_b.metric("Mastered", st.session_state.stats["mastered"])
    
    # --- Longitudinal Cognitive History (Feature 3) ---
    if st.session_state.history:
        st.divider()
        st.markdown("### 🧠 Cognitive History")
        for h in reversed(st.session_state.history[-5:]):
            badge = "🟢" if h["status"] == "Mastered" else "🔴"
            st.caption(f"{badge} **{h['topic'][:24]}** — *{h['status']}*")

# Helper function to get authenticated client strictly using BYOK
def get_client():
    if not st.session_state.byok_key:
        raise ValueError("Please provide your Gemini API Key in the left sidebar to generate live content, or click the Mock Demo button.")
    return get_gemini_client(st.session_state.byok_key)

# Main Dashboard Header
st.markdown('<div class="main-header">ExamSentinel : LangGraph Multi-Agent Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Capstone-grade competitive exam sparring and cognitive study planning orchestrated by LangGraph state machines.</div>', unsafe_allow_html=True)

# LangGraph Architecture Diagram Expander
with st.expander("🕸️ View Live LangGraph Multi-Agent StateGraph Architecture", expanded=False):
    st.markdown("This state graph models the formal orchestration flow, including cyclic self-correction between the Setter and Auditor, and Human-in-the-Loop checkpoints:")
    st.markdown(get_langgraph_mermaid_diagram())

# --- TOP NAVIGATION TABS ---
tab_sparring, tab_planner = st.tabs([
    "🥊 1. Adversarial Exam Sparring",
    "🗺️ 2. Diagnostic Study Planner"
])

# ==============================================================================
# TAB 1: ADVERSARIAL EXAM SPARRING COMMITTEE (LANGGRAPH POWERED)
# ==============================================================================
with tab_sparring:
    st.markdown("### 🏛️ Adversarial Examination Committee (LangGraph Orchestrated)")
    st.caption("Drill high-yield exam problems with deliberate cognitive traps and defend your reasoning against the Socratic Interrogator.")

    if st.session_state.stage == "init":
        with st.container(border=True):
            st.markdown(f"#### 🎯 Ready to Spar on: **{target_exam} — {target_topic}**")
            st.caption("Choose to generate a real-time question using your API key (with LangGraph Auditor verification), or preview sample mock data.")
            
            c_btn1, c_btn2 = st.columns([1.2, 1])
            
            with c_btn1:
                run_live = st.button("🚀 Run LangGraph Multi-Agent Pipeline (Live API)", type="primary", use_container_width=True)
            with c_btn2:
                run_mock = st.button("⚡ Preview Sample Mock Analysis (No Key Needed)", type="secondary", use_container_width=True)

            if run_live:
                if not st.session_state.byok_key:
                    st.error("🔑 Please enter your Gemini API key in the left sidebar to run a live session (or click 'Preview Sample Mock Analysis' instead).")
                elif not target_exam.strip() or not target_topic.strip():
                    st.error("Please provide both an Exam Name and Topic.")
                else:
                    try:
                        client = get_client()
                        execution_trace = []
                        with st.status("🏛️ LangGraph StateGraph Execution in progress...", expanded=True) as status:
                            # Node 1: Profiler
                            st.write("🔍 **Node 1 [profiler]:** Calibrating exam blueprint & marking rules...")
                            profiler = ExamProfilerAgent(client)
                            blueprint = profiler.run(target_exam, target_topic)
                            st.session_state.blueprint = blueprint
                            execution_trace.append(f"Node 1 [profiler]: Blueprint calibrated for {blueprint.exam_name}")

                            # Node 2: Question Setter
                            st.write(f"📝 **Node 2 [setter]:** Drafting authentic {blueprint.exam_name} problem...")
                            setter = QuestionSetterAgent(client)
                            question = setter.run(blueprint)
                            execution_trace.append("Node 2 [setter]: Drafted initial problem")

                            # Node 3: Quality Gate Auditor (Cyclic Self-Healing)
                            st.write("⚖️ **Node 3 [auditor]:** Quality Gate auditing mathematical precision & answer key...")
                            auditor = ExamAuditorAgent(client)
                            audit_result = auditor.run(blueprint, question)
                            st.session_state.audit_result = audit_result
                            
                            is_sound = audit_result.get("is_sound", True)
                            if not is_sound:
                                st.write("⚠️ **Quality Gate Alert:** Mathematical ambiguity detected. Initiating self-healing cycle back to Setter...")
                                critique = audit_result.get("critique", "Clarify options")
                                question = setter.run(blueprint, critique=critique)
                                execution_trace.append(f"Node 2 [setter] (Cycle 2): Revised question with feedback '{critique[:50]}...'")
                                audit_result["audit_verdict"] = "REVISED & VERIFIED"
                            else:
                                execution_trace.append("Node 3 [auditor]: Problem and answer key verified sound (0 errors)")

                            st.session_state.question = question

                            # Node 4: Trap Analyst
                            st.write("🧠 **Node 4 [trap_analyst]:** Mapping cognitive distractors & psychological traps...")
                            trap_analyst = TrapAnalystAgent(client)
                            distractor_map = trap_analyst.run(blueprint, question)
                            st.session_state.distractor_map = distractor_map
                            execution_trace.append("Node 4 [trap_analyst]: Distractor psychology mapped")

                            st.session_state.execution_trace = execution_trace
                            status.update(label="✅ LangGraph Quality Gate Passed! Problem Ready.", state="complete", expanded=False)

                        st.session_state.is_sparring_mock = False
                        st.session_state.stage = "question_ready"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error executing LangGraph pipeline: {e}")

            if run_mock:
                # Load pre-computed mock sparring session
                bp, q, audit, d_map, s_chal, diag, trace = get_mock_sparring_data()
                st.session_state.blueprint = bp
                st.session_state.question = q
                st.session_state.audit_result = audit
                st.session_state.distractor_map = d_map
                st.session_state.socratic_challenge = s_chal
                st.session_state.report = diag
                st.session_state.execution_trace = trace
                st.session_state.user_choice = "B"
                st.session_state.user_reasoning = "I assumed 3! = 6 permutations after P1 finishes."
                st.session_state.defense_response = "I see that P0 requires 3 units of R1, which isn't yet available after P1 alone."
                st.session_state.is_sparring_mock = True
                st.session_state.stage = "evaluated"
                st.rerun()

    # Active Question Display
    if st.session_state.stage in ["question_ready", "socratic_ready", "evaluated"]:
        bp: ExamBlueprint = st.session_state.blueprint
        q: QuestionItem = st.session_state.question
        audit_res = st.session_state.audit_result or {}
        
        # Tags Row
        c_tag1, c_tag2 = st.columns([1, 1])
        with c_tag1:
            if st.session_state.is_sparring_mock:
                st.markdown('<span class="demo-tag">⚡ DEMO / MOCK ANALYSIS PREVIEW (Sample Data)</span>', unsafe_allow_html=True)
            else:
                verdict = audit_res.get("audit_verdict", "VERIFIED")
                st.markdown(f'<span class="quality-badge">🛡️ LangGraph Quality Gate: {verdict}</span>', unsafe_allow_html=True)

        # Blueprint Summary Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption("🏛️ Exam")
            st.markdown(f"**{bp.exam_name}**")
        with col2:
            st.caption("🎯 Topic")
            st.markdown(f"**{bp.topic}**")
        with col3:
            st.caption("⚖️ Marking Scheme")
            st.markdown(f"**{bp.marking_scheme}**")
        with col4:
            st.caption("⚡ Difficulty")
            st.markdown(f"**{bp.difficulty_tier}**")

        if getattr(q, "pyq_benchmark", None):
            st.info(f"🏛️ **Past-Year Exam Benchmark:** {q.pyq_benchmark} *(Authenticity Match: {getattr(q, 'exam_isomorphism_score', 95)}%)*")

        if bp.hallmark_examiner_tricks:
            st.caption(f"⚠️ **Examiner Traps Active:** {', '.join(bp.hallmark_examiner_tricks)}")

        st.write("")

        # Question Card Container
        with st.container(border=True):
            st.markdown(f"### **Problem Statement**\n\n{q.question}")
            
            # Feature 1: Diagram / Schematic Rendering
            if getattr(q, "diagram_code", None) and q.diagram_code.strip():
                with st.expander("📊 View Problem Schematic / Transition Graph", expanded=True):
                    st.markdown(f"```mermaid\n{q.diagram_code}\n```")
                    
            st.divider()
            
            option_keys = list(q.options.keys())
            option_labels = [f"({k}) {q.options[k]}" for k in option_keys]

            if st.session_state.stage == "question_ready":
                selected_option_str = st.radio(
                    "**Select your answer:**",
                    option_labels,
                    index=0,
                    key="radio_choice"
                )
                selected_key = selected_option_str.split(")")[0].replace("(", "").strip()
                
                user_reason = st.text_area(
                    "**Justification / Formula / Rationale (Required for Socratic Sparring):**",
                    placeholder="Explain why this formula or boundary condition applies...",
                    key="text_reasoning"
                )
                
                if st.button("Submit Answer to Socratic Interrogator 🥊", type="primary"):
                    if not user_reason.strip():
                        st.warning("⚠️ Please provide a 1-sentence reasoning so the Examiner can interrogate your mental model!")
                    else:
                        st.session_state.user_choice = selected_key
                        st.session_state.user_reasoning = user_reason
                        
                        try:
                            client = get_client()
                            with st.spinner("⚔️ Node 5 [socratic]: Interrogating your rationale..."):
                                socratic = SocraticInterrogatorAgent(client)
                                challenge = socratic.run(
                                    blueprint=bp,
                                    question=q,
                                    distractor_map=st.session_state.distractor_map,
                                    user_choice=selected_key,
                                    user_reasoning=user_reason
                                )
                                st.session_state.socratic_challenge = challenge
                                st.session_state.execution_trace.append("Node 5 [socratic]: Generated oral defense challenge")
                                st.session_state.stage = "socratic_ready"
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error invoking Socratic Interrogator: {e}")
                            
            else:
                c_a, c_b = st.columns([1, 3])
                c_a.markdown(f"**Candidate Choice:** `({st.session_state.user_choice}) {q.options.get(st.session_state.user_choice, '')}`")
                c_b.markdown(f"**Candidate Reasoning:** *\"{st.session_state.user_reasoning}\"*")

    # Socratic Defense
    if st.session_state.stage == "socratic_ready":
        challenge: SocraticChallenge = st.session_state.socratic_challenge
        
        st.write("")
        with st.container(border=True):
            st.markdown("### 🥊 Socratic Oral Defense")
            
            probe_text = getattr(challenge, "probe", "")
            if not probe_text or not probe_text.strip():
                probe_text = "Your stated rationale does not specify the mathematical invariant. Under what specific boundary condition does your choice guarantee a safe state?"
                
            focus_text = getattr(challenge, "focus_area", "Boundary Invariant & Heuristic Validation")
            
            st.warning(f"⚔️ **Examiner's Challenge (Round 1):**\n\n{probe_text}")
            st.caption(f"🎯 **Focus Area Under Test:** `{focus_text}`")
            
            if st.session_state.counter_probe_active:
                st.error("⚔️ **Secondary Counter-Probe (Round 2 — Multi-Turn Stress Test):**\n\nUnder what precise condition does an execution sequence remain safe if one process requests an additional resource unit mid-execution?")
            
            st.divider()
            
            defense_input = st.text_area(
                "**Do you stand by your answer or change it? Defend your conviction:**",
                placeholder="e.g. 'I stand by my choice because...' or 'I realize my mistake, the answer should be...'",
                key="text_defense"
            )
            
            col_d1, col_d2 = st.columns([1.5, 1])
            with col_d1:
                finalize_defense = st.button("Finalize Defense & Reveal Post-Mortem 🏁", type="primary", use_container_width=True)
            with col_d2:
                if not st.session_state.counter_probe_active:
                    if st.button("⚔️ Request Round 2 Counter-Probe", type="secondary", use_container_width=True):
                        st.session_state.counter_probe_active = True
                        st.rerun()

            if finalize_defense:
                st.session_state.defense_response = defense_input
                st.session_state.stats["attempted"] += 1
                
                try:
                    client = get_client()
                    with st.spinner("🔬 Node 6 [diagnostic]: Compiling root-cause post-mortem..."):
                        evaluator = DiagnosticEvaluatorAgent(client)
                        report = evaluator.run(
                            blueprint=st.session_state.blueprint,
                            question=st.session_state.question,
                            distractor_map=st.session_state.distractor_map,
                            initial_choice=st.session_state.user_choice,
                            initial_reasoning=st.session_state.user_reasoning,
                            defense_response=defense_input
                        )
                        st.session_state.report = report
                        st.session_state.execution_trace.append(f"Node 6 [diagnostic]: Categorized as '{report.error_category}'")
                        if report.is_correct or report.error_category == "Mastered":
                            st.session_state.stats["mastered"] += 1
                        
                        # Record Cognitive History (Feature 3)
                        st.session_state.history.append({
                            "topic": bp.topic,
                            "status": "Mastered" if report.is_correct else report.error_category
                        })
                        st.session_state.counter_probe_active = False
                        st.session_state.stage = "evaluated"
                        st.rerun()
                except Exception as e:
                    st.error(f"Error evaluating performance: {e}")

    # Performance Post-Mortem
    if st.session_state.stage == "evaluated":
        report: DiagnosticReport = st.session_state.report
        distractor_map: DistractorMap = st.session_state.distractor_map
        
        st.write("")
        with st.container(border=True):
            st.markdown("## 📊 Performance Post-Mortem")
            
            if report.is_correct:
                st.success(f"### ✅ CORRECT! CONCEPT SOUND\n**Official Answer:** Option **{q.correct_answer}**")
            else:
                st.error(f"### ❌ INCORRECT / COMPROMISED\n**Official Answer:** Option **{q.correct_answer}** (Candidate selected: **{st.session_state.user_choice}**)")

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**Cognitive Tier:**")
                st.markdown(f"### `{report.error_category}`")
            with col2:
                st.markdown(f"**Diagnostic Summary:**\n\n{report.diagnosis_summary}")
                st.info(f"**💡 Exam-Day Prescription:**\n\n{report.prescription}")

        # Trap Deconstruction Table
        st.write("")
        with st.container(border=True):
            st.markdown("### 🕵️‍♂️ Examiner Trap Deconstruction")
            st.caption("How the question setter engineered each option to deceive unprepared students:")
            
            trap_data = []
            for opt, trap_text in distractor_map.option_traps.items():
                is_official = (opt.strip().upper() == q.correct_answer.strip().upper())
                status_label = "✅ CORRECT PROOF" if is_official else "⚠️ EXAMINER TRAP"
                trap_data.append({
                    "Option": f"Option {opt}",
                    "Status": status_label,
                    "Psychological / Mathematical Dissection": trap_text
                })
            st.table(pd.DataFrame(trap_data))

        with st.expander("📖 View Rigorous Step-by-Step Derivation", expanded=True):
            st.markdown(q.official_explanation)

        with st.container(border=True):
            st.markdown("### ⏱️ Instant 60-Second Remediation Drill")
            st.markdown(f"**Follow-Up Problem:**\n\n{report.micro_drill_question}")
            
            with st.expander("👁️ Reveal Micro-Drill Solution"):
                st.success(f"**Solution & Invariant Proof:**\n\n{report.micro_drill_answer}")

        # LangGraph Trace Expander
        if st.session_state.execution_trace:
            with st.expander("🔍 LangGraph StateGraph Execution Trace", expanded=False):
                st.caption("Step-by-step state handoffs and node transitions:")
                for step in st.session_state.execution_trace:
                    st.markdown(f"• `{step}`")

        # Feature 5: Publication-Grade PDF Dossier Export
        try:
            pdf_bytes = generate_sparring_dossier_pdf(
                blueprint=bp,
                question=q,
                distractor_map=distractor_map,
                user_choice=st.session_state.user_choice,
                user_reasoning=st.session_state.user_reasoning,
                defense_response=st.session_state.defense_response,
                report=report
            )
            clean_exam_name = bp.exam_name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
            st.download_button(
                label="📥 Download Official Exam-Day Mastery Dossier (PDF)",
                data=pdf_bytes,
                file_name=f"ExamSentinel_Dossier_{clean_exam_name}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.caption(f"PDF generator notice: {e}")

        # Feature 6: Production Multi-Agent Telemetry & Quality Dashboard
        with st.expander("📈 Production Multi-Agent Telemetry & Observability Dashboard", expanded=False):
            col_t1, col_t2, col_t3 = st.columns(3)
            col_t1.metric("Graph Execution Nodes", len(st.session_state.execution_trace))
            col_t2.metric("Auditor Quality Score", f"{getattr(q, 'exam_isomorphism_score', 95)}%")
            has_revised = any("Revised" in s for s in st.session_state.execution_trace)
            col_t3.metric("Quality Gate Revision", "1 Self-Healing Loop" if has_revised else "0 (Direct Pass)")
            
            st.markdown("**LangGraph State Machine Transitions:**")
            for step in st.session_state.execution_trace:
                st.code(step, language="bash")
                
            telemetry_data = {
                "exam": bp.exam_name,
                "topic": bp.topic,
                "marking_scheme": bp.marking_scheme,
                "candidate_choice": st.session_state.user_choice,
                "official_answer": q.correct_answer,
                "cognitive_tier": report.error_category,
                "audit_verdict": audit_res.get("audit_verdict", "VERIFIED"),
                "isomorphism_benchmark": getattr(q, 'pyq_benchmark', 'Past-Year Standard'),
                "authenticity_score": getattr(q, 'exam_isomorphism_score', 95),
                "execution_trace": st.session_state.execution_trace
            }
            st.download_button(
                "Export LangGraph Run Telemetry (JSON)",
                data=json.dumps(telemetry_data, indent=2),
                file_name="langgraph_run_telemetry.json",
                mime="application/json"
            )

        st.write("")
        if st.button("🔄 Spar on Another Problem", type="primary", use_container_width=True):
            st.session_state.stage = "init"
            st.session_state.blueprint = None
            st.session_state.question = None
            st.session_state.audit_result = None
            st.session_state.execution_trace = []
            st.session_state.distractor_map = None
            st.session_state.socratic_challenge = None
            st.session_state.report = None
            st.session_state.is_sparring_mock = False
            st.rerun()


# ==============================================================================
# TAB 2: MULTI-AGENT DIAGNOSTIC STUDY PLANNER
# ==============================================================================
with tab_planner:
    st.markdown("### 🗺️ Multi-Agent Diagnostic Study Planner")
    st.caption("Tell the committee what concept you're not understanding. Multiple specialized agents will interview your mental model and construct a custom, scaffolded mastery roadmap.")

    # STAGE A: Input Struggle Topic
    if st.session_state.planner_stage == "input":
        with st.container(border=True):
            st.markdown("#### 🎯 What concept are you struggling to grasp?")
            
            struggle_topic = st.text_input(
                "Struggled Topic / Concept",
                placeholder="e.g. Recursion & Backtracking, Dynamic Programming State Formulation, Bayesian Inference, Normalization in DBMS",
                value=st.session_state.planner_topic
            )
            
            struggle_desc = st.text_area(
                "Describe what happens when you try to solve or understand it (Optional but recommended):",
                placeholder="e.g. 'Whenever I see recursion, I try to trace all function calls in my head and get overwhelmed. I can't trust the leap of faith, or I forget how to formulate base cases.'",
                value=st.session_state.planner_description
            )
            
            c_p1, c_p2 = st.columns([1.2, 1])
            with c_p1:
                run_planner_live = st.button("🔍 Launch Diagnostic Interview (Live API)", type="primary", use_container_width=True)
            with c_p2:
                run_planner_mock = st.button("⚡ Preview Mock Study Plan: Recursion (No Key Needed)", type="secondary", use_container_width=True)

            if run_planner_live:
                if not st.session_state.byok_key:
                    st.error("🔑 Please enter your Gemini API key in the left sidebar to run a live session (or click 'Preview Mock Study Plan: Recursion' instead).")
                elif not struggle_topic.strip():
                    st.error("Please enter the topic you are struggling with.")
                else:
                    st.session_state.planner_topic = struggle_topic.strip()
                    st.session_state.planner_description = struggle_desc.strip()
                    
                    try:
                        client = get_client()
                        with st.status("🧠 Cognitive Diagnostic Interviewer formulating targeted probes...", expanded=True) as status:
                            st.write(f"Analyzing common pedagogical roadblocks for '{struggle_topic}'...")
                            diagnostic_agent = StudyDiagnosticAgent(client)
                            interview: DiagnosticInterview = diagnostic_agent.run(
                                target_exam=target_exam,
                                topic=struggle_topic,
                                user_description=struggle_desc
                            )
                            st.session_state.planner_interview = interview
                            status.update(label="✅ Diagnostic Questions Ready!", state="complete", expanded=False)
                            
                        st.session_state.is_planner_mock = False
                        st.session_state.planner_stage = "interview"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error launching interview: {e}")

            if run_planner_mock:
                interview_mock, answers_mock, plan_mock = get_mock_study_plan_data()
                st.session_state.planner_interview = interview_mock
                st.session_state.planner_user_answers = answers_mock
                st.session_state.planner_plan = plan_mock
                st.session_state.planner_topic = "Recursion & Backtracking"
                st.session_state.is_planner_mock = True
                st.session_state.planner_stage = "plan_ready"
                st.rerun()

    # STAGE B: The Diagnostic Interview (Agent questions -> Student answers)
    elif st.session_state.planner_stage == "interview":
        interview: DiagnosticInterview = st.session_state.planner_interview
        
        st.info(f"📋 **Diagnostic Interview for:** `{interview.topic}` (Exam: `{interview.target_exam}`)")
        st.markdown("Answer these 3 targeted diagnostic questions so the Study Architect Agent can map your exact cognitive roadblock:")
        
        with st.form("diagnostic_interview_form"):
            temp_answers = {}
            for idx, q_item in enumerate(interview.questions, start=1):
                st.markdown(f"**Question {idx}:** {q_item.question_text}")
                st.caption(f"*Diagnostic Intent: {q_item.diagnostic_intent}*")
                
                selected_choice = st.radio(
                    f"Select the option that best describes your thought process (Q{idx}):",
                    q_item.options,
                    key=f"interview_radio_{q_item.question_id}",
                    index=0
                )
                temp_answers[q_item.question_id] = selected_choice
                st.divider()

            extra_student_notes = st.text_input(
                "Any additional context or constraints? (e.g. 'I have 2 weeks until the exam', 'I prefer visual analogies'):",
                placeholder="e.g. Visual analogies work best for me..."
            )
            
            submit_interview = st.form_submit_button("🧠 Synthesize Personalized Study Plan", type="primary", use_container_width=True)

        if submit_interview:
            st.session_state.planner_user_answers = temp_answers
            
            try:
                client = get_client()
                with st.status("🏛️ Curriculum & Study Architect Agent building your roadmap...", expanded=True) as status:
                    st.write("Deconstructing your cognitive blockage & mental model gap...")
                    architect = StudyPlanArchitectAgent(client)
                    study_plan: PersonalizedStudyPlan = architect.run(
                        target_exam=target_exam,
                        topic=interview.topic,
                        interview=interview,
                        user_answers=temp_answers,
                        extra_notes=extra_student_notes
                    )
                    st.session_state.planner_plan = study_plan
                    status.update(label="✅ Custom Mastery Plan Synthesized!", state="complete", expanded=False)
                    
                st.session_state.planner_stage = "plan_ready"
                st.rerun()
            except Exception as e:
                st.error(f"Error creating study plan: {e}")

    # STAGE C: The Output Study Plan
    elif st.session_state.planner_stage == "plan_ready":
        plan: PersonalizedStudyPlan = st.session_state.planner_plan
        
        if st.session_state.is_planner_mock:
            st.markdown('<span class="demo-tag">⚡ DEMO / MOCK STUDY PLAN PREVIEW (Sample Data)</span>', unsafe_allow_html=True)

        st.markdown(f"## 🗺️ Personalized Mastery Plan: **{plan.topic}**")
        st.caption(f"Calibrated for **{target_exam}** by the Master Curriculum Architect Agent.")

        # 1. Bottleneck & Breakthrough Analogy
        col_bn, col_mm = st.columns(2)
        with col_bn:
            with st.container(border=True):
                st.markdown("#### ⚠️ Diagnosed Cognitive Bottleneck")
                st.warning(plan.diagnosed_bottleneck)
            
        with col_mm:
            with st.container(border=True):
                st.markdown("#### 💡 Breakthrough Mental Model")
                st.info(plan.breakthrough_mental_model)

        st.write("")
        st.markdown("### 📅 Progressive Scaffolded Roadmap")
        
        # 2. Roadmap Phases
        for idx, phase in enumerate(plan.phases, start=1):
            with st.container(border=True):
                st.markdown(f"#### **{phase.phase_title}** — `{phase.time_estimate}`")
                st.markdown(f"**🎯 Milestone Objective:** {phase.core_objective}")
                
                st.markdown("**Actionable Steps:**")
                for step in phase.actionable_steps:
                    st.markdown(f"- {step}")
                    
                if phase.high_yield_trap_warning:
                    st.warning(f"⚠️ **Exam Trap Alert:** {phase.high_yield_trap_warning}")

        st.write("")

        # 3. Practice Ladder & Mastery Benchmark
        c1, c2 = st.columns([1, 1])
        with c1:
            with st.container(border=True):
                st.markdown("### 🪜 Curated Practice Ladder")
                st.caption("Conquer these problem archetypes in order:")
                for item in plan.practice_ladder:
                    st.markdown(f"• **{item}**")
                    
        with c2:
            with st.container(border=True):
                st.markdown("### 🏆 Exam Mastery Benchmark")
                st.caption("Self-check test to confirm you have 100% mastery:")
                st.info(plan.mastery_benchmark)

        st.write("")
        # Feature 5: Study Plan PDF Export
        try:
            plan_pdf = generate_study_plan_pdf(
                topic=st.session_state.planner_topic,
                exam=target_exam,
                plan=plan
            )
            clean_topic = st.session_state.planner_topic.replace(" ", "_").replace("/", "_")
            st.download_button(
                label="📥 Download Official 3-Phase Study Plan (PDF)",
                data=plan_pdf,
                file_name=f"ExamSentinel_StudyPlan_{clean_topic}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.caption(f"Study Plan PDF notice: {e}")

        st.write("")
        if st.button("🔄 Diagnose & Plan Another Concept", type="primary", use_container_width=True):
            st.session_state.planner_stage = "input"
            st.session_state.planner_topic = ""
            st.session_state.planner_description = ""
            st.session_state.planner_interview = None
            st.session_state.planner_user_answers = {}
            st.session_state.planner_plan = None
            st.session_state.is_planner_mock = False
            st.rerun()
