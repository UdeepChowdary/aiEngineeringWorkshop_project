import streamlit as st
import pandas as pd
from config import get_gemini_client, verify_gemini_key, DEFAULT_MODEL
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
    .probe-text {
        font-size: 1.12rem;
        font-weight: 600;
        color: #f87171;
        line-height: 1.6;
        padding: 14px 18px;
        background: rgba(239, 68, 68, 0.08);
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        margin: 10px 0;
    }
    .byok-guide {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 8px;
        padding: 12px;
        font-size: 0.85rem;
        margin-top: 10px;
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
    st.session_state.stage = "init"
if "byok_key" not in st.session_state:
    st.session_state.byok_key = ""
if "key_verified" not in st.session_state:
    st.session_state.key_verified = False
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

# Sidebar: Strict Bring Your Own Key (BYOK)
with st.sidebar:
    st.title("🛡️ ExamSentinel")
    st.caption("Universal Multi-Agent Competitive Exam Sparring System")
    
    st.divider()
    
    # --- Bring Your Own Key (BYOK) Section ---
    st.markdown("### 🔑 Bring Your Own Key (BYOK)")
    st.caption("To use this multi-agent system, please provide your personal Google Gemini API key. Your key is stored solely in this browser session and is never saved to the server.")

    user_entered_key = st.text_input(
        "Enter Google Gemini API Key",
        value=st.session_state.byok_key,
        type="password",
        placeholder="AIzaSy... or AQ.Ab8...",
        help="Paste your personal Google Gemini API key here."
    )
    
    # Update session state if input changed
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
        st.caption("🔴 **Status:** Key required to run agents")

    # Informational Guide on Supported Keys & Where to Get Them
    with st.expander("📖 Supported Keys & Where to Get One", expanded=(not bool(st.session_state.byok_key))):
        st.markdown("""
        **Supported API Keys:**
        * **Google Gemini API Key** (Official)
        * Key formats usually begin with `AIzaSy...` or `AQ.Ab8...`
        * Powers all 5 agents on `gemini-3.5-flash`

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
        target_topic = st.text_input("Specific Topic", placeholder="e.g. Acid-Base Disorders, Bond Duration")
    else:
        target_exam, target_topic = PRESETS[preset_choice]
        st.info(f"**Exam:** {target_exam}\n\n**Topic:** {target_topic}")

    st.divider()
    
    # --- Agent Roster Info ---
    with st.expander("🤖 The 5-Agent Committee", expanded=False):
        st.markdown("""
        * **Exam Profiler**: Dynamic blueprint & scoring calibration
        * **Question Setter**: High-caliber problem synthesis
        * **Trap Analyst**: Psychological distractor deconstruction
        * **Socratic Interrogator**: Active oral defense & conviction test
        * **Diagnostic Evaluator**: Root-cause categorization & micro-drill
        """)
        
    st.divider()
    
    # --- Scorecard ---
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

# Helper function to get authenticated client strictly using BYOK
def get_client():
    if not st.session_state.byok_key:
        raise ValueError("Please provide your Gemini API Key in the left sidebar to start.")
    return get_gemini_client(st.session_state.byok_key)

# Main Dashboard Header
st.markdown('<div class="main-header">ExamSentinel : Multi-Agent Cognitive Sparring</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Simulating an adversarial examination committee that stress-tests your mental models and cognitive traps.</div>', unsafe_allow_html=True)

# ----------------- STAGE 0: Initial Screen -----------------
if st.session_state.stage == "init":
    if not st.session_state.byok_key:
        with st.container(border=True):
            st.warning("### 🔑 Bring Your Own Key Required to Spar")
            st.markdown("""
            **ExamSentinel** is completely free to use, but requires you to bring your own **Google Gemini API Key** to power the 5 specialized AI agents:
            
            1. **Get your free key**: Go to [Google AI Studio (aistudio.google.com)](https://aistudio.google.com/app/apikey) and click **"Create API key"** (free, no credit card required).
            2. **Paste your key**: Enter it into the **"Enter Google Gemini API Key"** field in the left sidebar.
            3. **Verify**: Click **"Verify Key"** in the sidebar to activate the committee.
            
            *Supported formats: keys starting with `AIzaSy...` or `AQ.Ab8...`.*
            """)
    else:
        st.info("👋 Select an exam and topic on the left sidebar, then click **Summon Committee & Generate Problem** below to begin.")
        
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

# ----------------- STAGES 1, 2, 3: Active Question Display -----------------
if st.session_state.stage in ["question_ready", "socratic_ready", "evaluated"]:
    bp: ExamBlueprint = st.session_state.blueprint
    q: QuestionItem = st.session_state.question
    
    # Blueprint Summary Row (Native Streamlit Columns)
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

    if bp.hallmark_examiner_tricks:
        st.caption(f"⚠️ **Examiner Traps Active:** {', '.join(bp.hallmark_examiner_tricks)}")

    st.write("")

    # Question Card Container
    with st.container(border=True):
        st.markdown(f"### **Problem Statement**\n\n{q.question}")
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
            # Display submitted choice as read-only summary inside the card
            c_a, c_b = st.columns([1, 3])
            c_a.markdown(f"**Your Initial Choice:** `({st.session_state.user_choice})`")
            c_b.markdown(f"**Your Stated Reasoning:** *\"{st.session_state.user_reasoning}\"*")

# ----------------- STAGE 2: Socratic Defense -----------------
if st.session_state.stage == "socratic_ready":
    challenge: SocraticChallenge = st.session_state.socratic_challenge
    
    st.write("")
    with st.container(border=True):
        st.markdown("### 🥊 Socratic Oral Defense")
        
        probe_text = getattr(challenge, "probe", "")
        if not probe_text or not probe_text.strip():
            probe_text = "Your stated rationale does not specify the mathematical invariant. Under what specific boundary condition does your choice guarantee a safe state?"
            
        focus_text = getattr(challenge, "focus_area", "Boundary Invariant & Heuristic Validation")
        
        st.markdown(f'<div class="probe-text">⚔️ <strong>Examiner\'s Challenge:</strong><br>{probe_text}</div>', unsafe_allow_html=True)
        st.caption(f"🎯 **Focus Area Under Test:** `{focus_text}`")
        
        st.divider()
        
        defense_input = st.text_area(
            "**Do you stand by your answer or change it? Defend your conviction:**",
            placeholder="e.g. 'I stand by my choice because...' or 'I realize my mistake, the answer should be...'",
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
    
    st.write("")
    with st.container(border=True):
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

    # Official Derivation
    with st.expander("📖 View Rigorous Step-by-Step Derivation", expanded=True):
        st.markdown(q.official_explanation)

    # 60-Second Micro-Drill
    with st.container(border=True):
        st.markdown("### ⏱️ Instant 60-Second Remediation Drill")
        st.markdown(f"**Follow-Up Problem:**\n\n{report.micro_drill_question}")
        
        with st.expander("👁️ Reveal Micro-Drill Solution"):
            st.success(f"**Solution & Invariant Proof:**\n\n{report.micro_drill_answer}")

    st.write("")
    if st.button("🔄 Drill Another Problem", type="primary", use_container_width=True):
        st.session_state.stage = "init"
        st.session_state.blueprint = None
        st.session_state.question = None
        st.session_state.distractor_map = None
        st.session_state.socratic_challenge = None
        st.session_state.report = None
        st.rerun()
