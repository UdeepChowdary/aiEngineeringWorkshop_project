import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

from orchestrator import ExamSentinelOrchestrator

console = Console()

POPULAR_PRESETS = [
    ("GATE CS", "Operating Systems: Deadlock Detection & Banker's Algorithm"),
    ("JEE Advanced", "Physics: Rotational Dynamics & Rolling without Slipping"),
    ("CAT", "Quantitative Aptitude: Permutations, Combinations & Probability"),
    ("GRE", "Quantitative Reasoning: Standard Deviation & Normal Distribution Traps"),
    ("UPSC Prelims", "Polity: Fundamental Rights vs Directive Principles Landmark Precedents")
]

def print_banner():
    console.print(Panel(
        """[bold cyan]╔════════════════════════════════════════════════════════════════╗
║     EXAM SENTINEL : MULTI-AGENT ADVERSARIAL SPARRING ENGINE   ║
╚════════════════════════════════════════════════════════════════╝[/bold cyan]
[dim yellow]Universal Cognitive Sparring System for Competitive Examinations[/dim yellow]
[dim white]Powered by Google Gemini Models & Multi-Agent Collaboration[/dim white]""",
        border_style="cyan",
        box=box.DOUBLE
    ))

def main():
    print_banner()
    try:
        orchestrator = ExamSentinelOrchestrator()
    except Exception as e:
        console.print(f"[bold red]Initialization Error:[/bold red] {e}")
        sys.exit(1)

    session_count = 0

    while True:
        console.print("\n[bold yellow]Select Mode:[/bold yellow]")
        for idx, (exam, topic) in enumerate(POPULAR_PRESETS, start=1):
            console.print(f"  [bold cyan][{idx}][/bold cyan] {exam} — [white]{topic}[/white]")
        console.print("  [bold cyan][C][/bold cyan] Custom Exam & Topic [italic](Type ANY exam and ANY topic)[/italic]")
        console.print("  [bold red][Q][/bold red] Quit Session")

        choice = Prompt.ask("\nChoose an option", default="C").strip().upper()

        if choice == "Q":
            console.print("[bold green]All the best for your competitive exams! Keep drilling your weak points.[/bold green]")
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(POPULAR_PRESETS):
            selected_exam, selected_topic = POPULAR_PRESETS[int(choice) - 1]
        elif choice == "C":
            selected_exam = Prompt.ask("[bold green]Enter Exam Name (e.g. GATE, JEE, CAT, USMLE, CFA, SAT, UPSC)[/bold green]")
            selected_topic = Prompt.ask("[bold green]Enter Specific Topic / Concept[/bold green]")
        else:
            console.print("[bold red]Invalid option. Please try again.[/bold red]")
            continue

        session_count += 1
        console.rule(f"[bold magenta]Sparring Round #{session_count}: {selected_exam} — {selected_topic}[/bold magenta]")

        try:
            orchestrator.run_round(selected_exam, selected_topic)
        except Exception as e:
            console.print(f"[bold red]Error running sparring session:[/bold red] {e}")
            import traceback
            traceback.print_exc()

        again = Prompt.ask("\n[bold cyan]Drill another concept?[/bold cyan]", choices=["y", "n"], default="y")
        if again.lower() != "y":
            console.print(f"\n[bold green]Session completed! Total concepts drilled: {session_count}. Keep up the discipline![/bold green]")
            break

if __name__ == "__main__":
    main()
