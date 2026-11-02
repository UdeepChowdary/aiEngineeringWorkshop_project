import streamlit as st
import pandas as pd
from config import get_gemini_client, get_gemini_api_key, DEFAULT_MODEL
from agents import (
    ExamProfilerAgent,
    QuestionSetterAgent,
    TrapAnalystAgent,
    SocraticInterrogatorAgent,
    DiagnosticEvaluatorAgent
)
from models import ExamBlueprint, QuestionItem, DistractorMap, SocraticChallenge, DiagnosticReport

st.set_page_config(
    page_title="ExamSentinel — Multi-Agent Exam Sparring",
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
        margin-bottom: 1.5rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .badge-cyan { background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .badge-purple { background-color: rgba(192, 132, 252, 0.15); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.3); }
    .badge-emerald { background-color: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
    .badge-amber { background-color: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
    .exam-card {
        padding: 20px;
        border-radius: 12px;
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.2);
        margin-bottom: 20px;
    }
    .socratic-card {
        padding: 18px;
        border-radius: 12px;
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.3);
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# Presets
PRESETS = {
    "GATE CS: Deadlocks & Banker's Algorithm": ("GATE CS", "Operating Systems: Deadlock Detection & Banker's Algorithm"),
    "JEE Advanced: Rotational Dynamics": ("JEE Advanced", "Physics: Rotational Dynamics & Rolling without Slipping"),
    "CAT: Probability & Combinations": ("CAT", "Quantitative Aptitude: Permutations, Combinations & Probability"),
    "GRE: Standard Deviation Traps": ("GRE", "Quantitative Reasoning: Standard Deviation & Normal Distribution"),
    "UPSC Prelims: Fundamental Rights": ("UPSC Prelims", "Polity: Fundamental Rights vs DPSPs Judicial Precedents"),
    "Custom (Type Any Exam & Topic)": ("Custom", "Custom")
}

# Session State Initialization
if "stage" not in st.session_state:
    st.session_state.stage = "init"  # init -> question_ready -> socratic_ready -> evaluated
if "blueprint" not in st.session_state:
    st.session_state.blueprint = None
if "question" not in st.session_state:
    st.session_state.question = None
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

# Sidebar
with st.sidebar:
    st.title("🛡️ ExamSentinel")
    st.caption("Universal Multi-Agent Competitive Exam Sparring System")
    
    st.markdown("---")
    
    # API Key Handling
    api_key_status = bool(get_gemini_api_key())
    manual_api_key = ""
    if not api_key_status:
        st.warning("No API key detected in environment.")
        manual_api_key = st.text_input("Enter Gemini API Key", type="password", help="Get a free key from Google AI Studio")
    else:
        st.success("API Key Loaded from Environment / Secrets")
    
    st.markdown("### 🎯 Exam Configuration")
    preset_choice = st.selectbox("Select Preset or Custom", list(PRESETS.keys()))
    
    if preset_choice == "Custom (Type Any Exam & Topic)":
        target_exam = st.text_input("Target Exam", placeholder="e.g. USMLE, CFA Level 1, SAT, NEET")
        target_topic = st.text_input("Specific Topic", placeholder="e.g. Acid-Base Disorders, Bond Duration")
    else:
        target_exam, target_topic = PRESETS[preset_choice]
        st.info(f"**Exam:** {target_exam}\n\n**Topic:** {target_topic}")

    st.markdown("---")
    
    # Agent Roster Info
    with st.expander("🤖 The 5-Agent Committee", expanded=False):
        st.markdown("""
        1. **Exam Profiler**: Blueprint & scoring calibration
        2. **Question Setter**: High-caliber problem synthesis
        3. **Trap Analyst**: Psychological distractor deconstruction
        4. **Socratic Interrogator**: Active oral defense & conviction test
        5. **Diagnostic Evaluator**: Root-cause categorization & micro-drill
        """)
        
    st.markdown("---")
    
    # Scorecard
    st.markdown("### 📊 Sparring Stats")
    col_a, col_b = st.columns(2)
    col_a.metric("Attempted", st.session_state.stats["attempted"])
    col_b.metric("Mastered", st.session_state.stats["mastered"])
    
    if st.button("🔄 Reset / New Problem", use_container_width=True):
        st.session_state.stage = "init"
        st.session_state.blueprint = None
        st.session_state.question = None
        st.session_state.distractor_map = None
        st.session_state.socratic_challenge = None
        st.session_state.report = None
        st.session_state.user_choice = None
        st.session_state.user_reasoning = ""
        st.session_state.defense_response = ""
        st.rerun()

# Main Dashboard Header
st.markdown('<div class="main-header">ExamSentinel : Multi-Agent Cognitive Sparring</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Simulating an adversarial examination committee that stress-tests your mental models and cognitive traps.</div>', unsafe_allow_html=True)

# Helper function to get client
def get_client():
    return get_gemini_client(manual_api_key)

# ----------------- STAGE 0: Initial Screen -----------------
if st.session_state.stage == "init":
    st.info("👋 Select an exam and topic on the left sidebar, then click **Generate Exam Problem** to summon the exam committee.")
    
    if st.button("🚀 Summon Committee & Generate Problem", type="primary", use_container_width=True):
        if not target_exam.strip() or not target_topic.strip():
            st.error("Please provide both an Exam Name and Topic.")
        else:
            try:
                client = get_client()
                with st.status("🏛️ Multi-Agent Committee in session...", expanded=True) as status:
                    st.write("🔍 **Agent 0 (Exam Profiler):** Calibrating exam blueprint, marking scheme & traps...")
                    profiler = ExamProfilerAgent(client)
                    blueprint = profiler.run(target_exam, target_topic)
                    st.session_state.blueprint = blueprint

                    st.write(f"📝 **Agent 1 (Question Setter):** Composing authentic {blueprint.exam_name} problem...")
                    setter = QuestionSetterAgent(client)
                    question = setter.run(blueprint)
                    st.session_state.question = question

                    st.write("🧠 **Agent 2 (Trap Analyst):** Deconstructing psychological distractors...")
                    trap_analyst = TrapAnalystAgent(client)
                    distractor_map = trap_analyst.run(blueprint, question)
                    st.session_state.distractor_map = distractor_map

                    status.update(label="✅ Problem and Trap Analysis Ready!", state="complete", expanded=False)

                st.session_state.stage = "question_ready"
                st.rerun()
            except Exception as e:
                st.error(f"Error initializing committee: {e}")

# ----------------- STAGE 1: Question Ready -----------------
if st.session_state.stage in ["question_ready", "socratic_ready", "evaluated"]:
    bp: ExamBlueprint = st.session_state.blueprint
    q: QuestionItem = st.session_state.question
    
    # Blueprint Banner
    st.markdown(f"""
    <span class="badge-pill badge-cyan">🏛️ {bp.exam_name}</span>
    <span class="badge-pill badge-purple">🎯 {bp.topic}</span>
    <span class="badge-pill badge-emerald">⚖️ Marking: {bp.marking_scheme}</span>
    <span class="badge-pill badge-amber">⚡ Difficulty: {bp.difficulty_tier}</span>
    """, unsafe_allow_html=True)
    
    if bp.hallmark_examiner_tricks:
        st.caption(f"**Examiner Traps Active:** {', '.join(bp.hallmark_examiner_tricks)}")

    # Question Display
    st.markdown('<div class="exam-card">', unsafe_allow_html=True)
    st.markdown(f"### **Problem Statement**\n\n{q.question}")
    st.markdown("---")
    
    # Options Display
    option_keys = list(q.options.keys())
    option_labels = [f"({k}) {q.options[k]}" for k in option_keys]

    if st.session_state.stage == "question_ready":
        selected_option_str = st.radio(
            "Select your answer:",
            option_labels,
            index=0,
            key="radio_choice"
        )
        selected_key = selected_option_str.split(")")[0].replace("(", "").strip()
        
        user_reason = st.text_area(
            "Justification / Formula / Rationale (Required for Socratic Sparring):",
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
                    with st.spinner("⚔️ Agent 3 (Socratic Interrogator) analyzing your thought process..."):
                        socratic = SocraticInterrogatorAgent(client)
                        challenge = socratic.run(
                            blueprint=bp,
                            question=q,
                            distractor_map=st.session_state.distractor_map,
                            user_choice=selected_key,
                            user_reasoning=user_reason
                        )
                        st.session_state.socratic_challenge = challenge
                        st.session_state.stage = "socratic_ready"
                        st.rerun()
                except Exception as e:
                    st.error(f"Error invoking Socratic Interrogator: {e}")
                    
    else:
        # Display submitted choice as read-only summary
        st.markdown(f"**Your Initial Choice:** `({st.session_state.user_choice}) {q.options.get(st.session_state.user_choice, '')}`")
        st.markdown(f"**Your Reasoning:** *\"{st.session_state.user_reasoning}\"*")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- STAGE 2: Socratic Defense -----------------
if st.session_state.stage == "socratic_ready":
    challenge: SocraticChallenge = st.session_state.socratic_challenge
    
    st.markdown('<div class="socratic-card">', unsafe_allow_html=True)
    st.markdown("### 🥊 Socratic Oral Defense")
    st.markdown(f"**Examiner's Probe:**\n\n> *\"{challenge.probe}\"*")
    st.caption(f"**Focus Area Under Test:** `{challenge.focus_area}`")
    st.markdown('</div>', unsafe_allow_html=True)
    
    defense_input = st.text_area(
        "Do you stand by your answer or change it? Defend your conviction:",
        placeholder="e.g. 'I stand by B because the boundary condition holds...' or 'I realize my mistake, the answer should be C because...'",
        key="text_defense"
    )
    
    if st.button("Finalize Defense & Reveal Post-Mortem 🏁", type="primary"):
        st.session_state.defense_response = defense_input
        st.session_state.stats["attempted"] += 1
        
        try:
            client = get_client()
            with st.spinner("🔬 Agent 4 (Diagnostic Evaluator) compiling root-cause analysis..."):
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
                if report.is_correct or report.error_category == "Mastered":
                    st.session_state.stats["mastered"] += 1
                st.session_state.stage = "evaluated"
                st.rerun()
        except Exception as e:
            st.error(f"Error evaluating performance: {e}")

# ----------------- STAGE 3: Performance Post-Mortem -----------------
if st.session_state.stage == "evaluated":
    report: DiagnosticReport = st.session_state.report
    distractor_map: DistractorMap = st.session_state.distractor_map
    
    st.markdown("## 📊 Performance Post-Mortem")
    
    # Result Banner
    if report.is_correct:
        st.success(f"### ✅ CORRECT! CONCEPT SOUND\n**Official Answer:** Option **{q.correct_answer}**")
    else:
        st.error(f"### ❌ INCORRECT / COMPROMISED\n**Official Answer:** Option **{q.correct_answer}** (You selected: **{st.session_state.user_choice}**)")

    # Category & Diagnosis Cards
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**Cognitive Tier:**")
        st.markdown(f"### `{report.error_category}`")
    with col2:
        st.markdown(f"**Diagnostic Summary:**\n\n{report.diagnosis_summary}")
        st.info(f"**💡 Exam-Day Prescription:**\n\n{report.prescription}")

    # Trap Deconstruction Table
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

    # Official Derivation
    with st.expander("📖 View Rigorous Step-by-Step Derivation", expanded=True):
        st.markdown(q.official_explanation)

    # 60-Second Micro-Drill
    st.markdown("### ⏱️ Instant 60-Second Remediation Drill")
    st.markdown(f"**Follow-Up Problem:**\n\n{report.micro_drill_question}")
    
    with st.expander("👁️ Reveal Micro-Drill Solution"):
        st.success(f"**Solution & Invariant Proof:**\n\n{report.micro_drill_answer}")

    if st.button("🔄 Drill Another Problem", type="primary"):
        st.session_state.stage = "init"
        st.session_state.blueprint = None
        st.session_state.question = None
        st.session_state.distractor_map = None
        st.session_state.socratic_challenge = None
        st.session_state.report = None
        st.rerun()
