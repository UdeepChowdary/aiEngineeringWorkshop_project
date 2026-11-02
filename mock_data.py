"""Provides high-quality mock data for instant preview/demo of both multi-agent systems."""
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

def get_mock_sparring_data():
    """Returns authentic pre-computed mock data for the Adversarial Exam Committee."""
    blueprint = ExamBlueprint(
        exam_name="GATE CS (Graduate Aptitude Test in Engineering)",
        topic="Operating Systems: Deadlock Detection & Banker's Algorithm",
        question_style="MCQ (Single Correct) / Numerical",
        marking_scheme="+2 for correct, -0.66 for incorrect",
        difficulty_tier="Advanced / Multi-Step Trap",
        hallmark_examiner_tricks=[
            "Confusing Total System Resources with Available Vector",
            "Safe state vs Deadlock-free state distinction",
            "Permutation counting trap without verifying sequential vector addition"
        ]
    )

    question = QuestionItem(
        question=(
            "Consider a system with four processes $\\{P_0, P_1, P_2, P_3\\}$ and three resource types "
            "$(R_1, R_2, R_3)$. Total system resources are $(R_1=9, R_2=3, R_3=6)$. The current Allocation "
            "and Max need matrices are:\n\n"
            "| Process | Allocation $(R_1, R_2, R_3)$ | Max $(R_1, R_2, R_3)$ |\n"
            "| :---: | :---: | :---: |\n"
            "| $P_0$ | $(1, 0, 1)$ | $(4, 1, 2)$ |\n"
            "| $P_1$ | $(2, 1, 1)$ | $(3, 2, 1)$ |\n"
            "| $P_2$ | $(3, 0, 2)$ | $(4, 1, 3)$ |\n"
            "| $P_3$ | $(1, 1, 0)$ | $(2, 1, 1)$ |\n\n"
            "How many distinct valid safe execution sequences exist for this system state?"
        ),
        options={
            "A": "2 safe sequences",
            "B": "6 safe sequences",
            "C": "12 safe sequences",
            "D": "0 (System is in an Unsafe State)"
        },
        correct_answer="A",
        official_explanation=(
            "**Step 1: Compute Currently Available Resources ($Available = Total - \\sum Allocation$)**\n"
            "- $\\sum Allocation = (1+2+3+1, 0+1+0+1, 1+1+2+0) = (7, 2, 4)$\n"
            "- $Available = (9-7, 3-2, 6-4) = (2, 1, 2)$\n\n"
            "**Step 2: Compute Need Matrix ($Need = Max - Allocation$)**\n"
            "- $Need(P_0) = (3, 1, 1)$\n"
            "- $Need(P_1) = (1, 1, 0)$\n"
            "- $Need(P_2) = (1, 1, 1)$\n"
            "- $Need(P_3) = (1, 0, 1)$\n\n"
            "**Step 3: Test Safe Sequence Permutations**\n"
            "- Initially, with $Available = (2, 1, 2)$, both $P_1$ and $P_3$ can execute because their Need $\\le Available$.\n"
            "- If $P_1$ executes first $\\rightarrow$ Releases $(2, 1, 1) \\rightarrow Available = (4, 2, 3)$. Then $P_3$ runs $\\rightarrow Available = (5, 3, 3)$. Then $P_0$ and $P_2$ can run in either order.\n"
            "- Tracing all execution trees yields exactly **2 valid safe paths**: $\\langle P_1, P_3, P_0, P_2 \\rangle$ and $\\langle P_1, P_3, P_2, P_0 \\rangle$.\n"
            "- Starting with $P_3$ deadlocks because $P_1$'s remaining $R_2$ requirement cannot be satisfied."
        )
    )

    audit_result = {
        "is_sound": True,
        "audit_verdict": "VERIFIED",
        "math_verification": "Vector arithmetic verified. Total resources (9,3,6) minus sum of allocations (7,2,4) equals Available (2,1,2). Exactly 2 safe sequences exist.",
        "critique": "Approved: Question is mathematically sound with unambiguous distractors."
    }

    distractor_map = DistractorMap(
        key_concept_tested="Sequential Vector Inequality & Running Available Accumulation",
        option_traps={
            "A": "Logically sound derivation tracing the exact dependency tree.",
            "B": "Aspirant assumes that once P1 finishes, all 3 remaining processes can be permuted in 3! = 6 ways without checking P0's R1 constraint.",
            "C": "Aspirant mistakenly assumes both P1 and P3 branches lead to full permutations (2 * 3! = 12).",
            "D": "Aspirant forgot to subtract Total Allocation from Total Resources, thinking Available is (0, 0, 0)."
        }
    )

    socratic_challenge = SocraticChallenge(
        probe=(
            "You selected Option B (6 sequences) assuming that once process P1 finishes, the remaining 3 processes can run "
            "in any order (3! = 6). But check process P0's resource requirement for R1: does the Available vector after P1 finishes "
            "satisfy P0 immediately if P3 has not yet released its allocation?"
        ),
        focus_area="Sequential Vector Dependency & Premature Combinatorial Multiplications"
    )

    diagnostic_report = DiagnosticReport(
        is_correct=False,
        error_category="Trap Victim",
        diagnosis_summary=(
            "You fell for the classic GATE combinatorial trap: multiplying remaining process counts (3! = 6) "
            "instead of sequentially testing vector inequalities at every step."
        ),
        prescription=(
            "Rule of Thumb for Exam Day: In Banker's algorithm questions, NEVER use factorial permutation shortcuts. "
            "Always draw the search tree and verify vector addition step-by-step."
        ),
        micro_drill_question=(
            "Quick Drill: Available = (1, 2, 1). Need(P_A) = (1, 1, 1) with Allocation=(1, 0, 0); "
            "Need(P_B) = (2, 0, 1). Can P_B execute immediately if P_A has not finished?"
        ),
        micro_drill_answer=(
            "No. Need(P_B) requires 2 units of R1, but current Available has only 1 unit of R1. "
            "P_A must execute first and release its allocation."
        )
    )

    execution_trace = [
        "Node 1 [profiler]: Calibrated blueprint for GATE CS (Operating Systems)",
        "Node 2 [setter]: Drafted Banker's Algorithm allocation problem",
        "Node 3 [auditor]: Quality Gate verified vector mathematics (0 errors detected)",
        "Node 4 [trap_analyst]: Deconstructed factorial permutation trap",
        "Node 5 [socratic]: Generated challenge on sequential dependency vs combinatorial multiplication",
        "Node 6 [diagnostic]: Categorized cognitive error as 'Trap Victim' with micro-drill"
    ]

    return blueprint, question, audit_result, distractor_map, socratic_challenge, diagnostic_report, execution_trace


def get_mock_study_plan_data():
    """Returns authentic pre-computed mock data for the Multi-Agent Diagnostic Study Planner."""
    interview = DiagnosticInterview(
        topic="Recursion & Backtracking",
        target_exam="Computer Science Competitive Entrance (GATE / Coding / Technical)",
        questions=[
            DiagnosticQuestion(
                question_id="q1",
                question_text="When you look at a recursive function, what does your brain naturally attempt to do first?",
                options=[
                    "I try to mentally simulate every single nested call stack frame down to the base case, and my brain gets overwhelmed.",
                    "I struggle to write the base case and often get off-by-one errors or infinite recursion.",
                    "I understand simple recursion (like factorial), but multi-branch recursion (like tree traversals or subsets) confuses me.",
                    "I don't know when to use recursion versus an iterative while-loop."
                ],
                diagnostic_intent="Evaluates whether the student suffers from the Call-Stack Micromanagement Fallacy vs Base-Case formulation."
            ),
            DiagnosticQuestion(
                question_id="q2",
                question_text="When designing a backtracking solution (e.g. Subsets, Permutations), where does your logic break down?",
                options=[
                    "I forget to undo the state change (backtrack step), causing mutations to leak into sibling branches.",
                    "I struggle to figure out what parameters need to be passed into the recursive signature.",
                    "I don't understand how the call stack 'unwinds' and returns values back up the tree.",
                    "I don't know how to prune invalid branches with bounding conditions."
                ],
                diagnostic_intent="Isolates state restoration mechanics vs branch pruning."
            ),
            DiagnosticQuestion(
                question_id="q3",
                question_text="How do you feel about the 'Recursive Leap of Faith' (Mathematical Induction)?",
                options=[
                    "I feel extremely anxious unless I manually trace at least 3-4 levels of the tree.",
                    "I understand the concept in theory, but I can't formulate the recurrence relation $T(n) = aT(n/b) + f(n)$.",
                    "I can write the code, but I fail when examiners ask for the exact recursion tree depth or stack space."
                ],
                diagnostic_intent="Tests confidence in inductive subproblem assumption."
            )
        ]
    )

    user_answers = {
        "q1": "I try to mentally simulate every single nested call stack frame down to the base case, and my brain gets overwhelmed.",
        "q2": "I forget to undo the state change (backtrack step), causing mutations to leak into sibling branches.",
        "q3": "I feel extremely anxious unless I manually trace at least 3-4 levels of the tree."
    }

    study_plan = PersonalizedStudyPlan(
        topic="Recursion & Backtracking",
        diagnosed_bottleneck=(
            "The 'Call-Stack Micro-Manager' Fallacy: You are attempting to act like the CPU hardware by manually simulating "
            "every memory stack frame in your biological working memory. Because human working memory can only hold 4-7 chunks, "
            "you experience cognitive overload. Additionally, you lack a disciplined 'Take/Don't Take' mental template for backtracking state undoing."
        ),
        breakthrough_mental_model=(
            "The Corporate CEO Delegation Principle: A CEO never micromanages what their regional VP does. "
            "To solve problem size N, you assume on blind faith that your subordinate already correctly solved size (N-1). "
            "Your ONLY job as CEO is: (1) Handle the trivial base case (e.g. empty input), and (2) Combine that (N-1) result with the current element. "
            "Rule: NEVER trace deeper than 1 level in your head!"
        ),
        phases=[
            StudyPlanPhase(
                phase_title="Phase 1: Single-Level Inductive Trust & The Base Case Contract",
                time_estimate="Day 1 (2 Hours)",
                core_objective="Break the manual tracing habit. Formulate pure mathematical induction without tracing stack frames.",
                actionable_steps=[
                    "Write out the 3 Laws of Recursion on an index card: Base Case, Progress toward Base Case, Subproblem Trust.",
                    "Solve 5 linear recursive problems (Factorial, Array Sum, Palindrome String, Power x^n, Reverse Stack).",
                    "Hard Rule: You are strictly forbidden from drawing more than 1 level of recursion. Trust the subproblem contract."
                ],
                high_yield_trap_warning="Do not place print statements inside every recursive call; it reinforces the micromanagement habit."
            ),
            StudyPlanPhase(
                phase_title="Phase 2: The Binary Choice Tree & Backtracking State Restoration",
                time_estimate="Day 2 (2.5 Hours)",
                core_objective="Master the 'Choose -> Explore -> Unchoose' pattern for combinatorial branching.",
                actionable_steps=[
                    "Draw the explicit 2-branch 'Include vs Exclude' state tree on paper for `[1, 2, 3]`.",
                    "Implement Subsets (Power Set) using the exact 3-line pattern: `path.append(x) -> recurse() -> path.pop()`.",
                    "Implement Combination Sum with candidate reuse and duplicate handling."
                ],
                high_yield_trap_warning="Beware of passing mutable lists in Python/Java: always pass a copy or remember to `pop()` after the return."
            ),
            StudyPlanPhase(
                phase_title="Phase 3: Branch Pruning, Memoization & Exam-Grade PYQs",
                time_estimate="Day 3 (3 Hours)",
                core_objective="Conquer complex multi-branching with bounding constraints under timed exam conditions.",
                actionable_steps=[
                    "Solve N-Queens or Sudoku Solver focusing strictly on the `is_valid()` bounding function.",
                    "Convert a branching recursion tree into a memoized Top-Down DP table (0/1 Knapsack).",
                    "Timed drill: Solve 3 Previous Year Questions (PYQs) from GATE/Coding exams in under 45 minutes."
                ],
                high_yield_trap_warning="In competitive exams, examiners intentionally set constraints where unpruned recursion causes Time Limit Exceeded (TLE)."
            )
        ],
        practice_ladder=[
            "Level 1 (Elementary): String Reversal & Array Binary Search via pure recursion",
            "Level 2 (Combinatorial): Subsets I (LeetCode 78) & Combination Sum (LeetCode 39)",
            "Level 3 (Permutations): Permutations with duplicates (LeetCode 47)",
            "Level 4 (Complex Backtracking): Word Search & N-Queens (LeetCode 51)",
            "Level 5 (Exam Peak): Target Sum & 0/1 Knapsack recurrence tree bounding"
        ],
        mastery_benchmark=(
            "The 15-Minute Litmus Test: Given the problem 'Generate all valid Parentheses of length 2N', "
            "can you formulate the state variables (open, close), write the base case, and code the solution in under 12 minutes "
            "without drawing more than 2 levels of a tree? If yes, you have 100% exam-grade mastery."
        )
    )

    return interview, user_answers, study_plan
