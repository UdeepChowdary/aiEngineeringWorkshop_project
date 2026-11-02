from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich import box

from config import get_gemini_client
from agents import (
    ExamProfilerAgent,
    QuestionSetterAgent,
    TrapAnalystAgent,
    SocraticInterrogatorAgent,
    DiagnosticEvaluatorAgent
)
from models import ExamBlueprint, QuestionItem, DistractorMap

console = Console()

class ExamSentinelOrchestrator:
    """Coordinates the multi-agent pipeline and the interactive terminal experience."""

    def __init__(self):
        self.client = get_gemini_client()
        self.profiler = ExamProfilerAgent(self.client)
        self.setter = QuestionSetterAgent(self.client)
        self.trap_analyst = TrapAnalystAgent(self.client)
        self.socratic = SocraticInterrogatorAgent(self.client)
        self.evaluator = DiagnosticEvaluatorAgent(self.client)

    def run_round(self, exam_name: str, topic: str):
        # 1. Calibration Phase
        with console.status("[bold cyan]Calibrating Exam Blueprint via Exam Profiler Agent...", spinner="dots"):
            blueprint: ExamBlueprint = self.profiler.run(exam_name, topic)

        blueprint_table = Table(title="[bold green]Dynamic Exam Blueprint[/bold green]", box=box.ROUNDED)
        blueprint_table.add_column("Property", style="cyan", no_wrap=True)
        blueprint_table.add_column("Specification", style="white")
        blueprint_table.add_row("Exam Name", blueprint.exam_name)
        blueprint_table.add_row("Target Topic", blueprint.topic)
        blueprint_table.add_row("Question Style", blueprint.question_style)
        blueprint_table.add_row("Marking Scheme", blueprint.marking_scheme)
        blueprint_table.add_row("Difficulty Tier", blueprint.difficulty_tier)
        blueprint_table.add_row("Examiner Traps", ", ".join(blueprint.hallmark_examiner_tricks))
        console.print(blueprint_table)
        console.print()

        # 2. Question Generation & Trap Deconstruction
        with console.status("[bold magenta]Question Setter & Trap Analyst Agents composing problem...", spinner="dots"):
            question: QuestionItem = self.setter.run(blueprint)
            distractor_map: DistractorMap = self.trap_analyst.run(blueprint, question)

        # 3. Present Question to Candidate
        options_text = ""
        for key, val in question.options.items():
            options_text += f"\n  [bold yellow]({key})[/bold yellow] {val}"

        console.print(Panel(
            f"[bold white]{question.question}[/bold white]\n{options_text}",
            title=f"[bold yellow]{blueprint.exam_name} Challenge[/bold yellow]",
            subtitle=f"[dim]Marking: {blueprint.marking_scheme}[/dim]",
            border_style="yellow",
            box=box.DOUBLE
        ))

        # 4. Candidate Response & Justification
        valid_choices = list(question.options.keys())
        user_choice = Prompt.ask(
            "\n[bold green]Enter your answer[/bold green]",
            choices=valid_choices,
            default=valid_choices[0]
        )
        user_reasoning = Prompt.ask(
            "[bold green]Explain your reasoning / formula in 1-2 lines (Required for Sparring)[/bold green]"
        )

        # 5. Socratic Sparring Phase
        with console.status("[bold red]Socratic Interrogator analyzing your rationale...", spinner="dots"):
            socratic_challenge = self.socratic.run(
                blueprint=blueprint,
                question=question,
                distractor_map=distractor_map,
                user_choice=user_choice,
                user_reasoning=user_reasoning
            )

        console.print(Panel(
            f"[bold red]Examiner's Probe:[/bold red]\n{socratic_challenge.probe}\n\n[dim cyan]Focus Area Under Test: {socratic_challenge.focus_area}[/dim cyan]",
            title="[bold red]Socratic Defense & Conviction Check[/bold red]",
            border_style="red",
            box=box.ROUNDED
        ))

        defense_response = Prompt.ask(
            "[bold yellow]Do you stand by your answer or change it? Defend your position[/bold yellow]"
        )

        # 6. Post-Mortem & Diagnostic Phase
        with console.status("[bold green]Diagnostic & Remediation Agent generating root-cause analysis...", spinner="dots"):
            report = self.evaluator.run(
                blueprint=blueprint,
                question=question,
                distractor_map=distractor_map,
                initial_choice=user_choice,
                initial_reasoning=user_reasoning,
                defense_response=defense_response
            )

        console.print()
        status_color = "green" if report.is_correct else "red"
        status_text = "CORRECT! CONCEPT SOUND." if report.is_correct else "INCORRECT / COMPROMISED."

        console.print(Panel(
            f"[{status_color} bold]Result: {status_text}[/{status_color} bold]\n"
            f"[bold]Official Answer:[/bold] [yellow]{question.correct_answer}[/yellow]\n"
            f"[bold]Cognitive Category:[/bold] [magenta]{report.error_category}[/magenta]\n\n"
            f"[bold]Diagnosis:[/bold] {report.diagnosis_summary}\n\n"
            f"[bold]Exam-Day Prescription:[/bold] {report.prescription}",
            title=f"[bold {status_color}]Performance Post-Mortem[/bold {status_color}]",
            border_style=status_color,
            box=box.HEAVY
        ))

        # 7. Examiner Trap Breakdown Table
        trap_table = Table(title="[bold yellow]Examiner Trap Deconstruction[/bold yellow]", box=box.SIMPLE_HEAVY)
        trap_table.add_column("Option", style="bold cyan", width=8)
        trap_table.add_column("Psychological / Mathematical Trap Dissected", style="white")

        for opt, trap in distractor_map.option_traps.items():
            is_correct_opt = (opt.strip().upper() == question.correct_answer.strip().upper())
            prefix = "[green]✓ CORRECT[/green]" if is_correct_opt else "[red]✗ TRAP[/red]"
            trap_table.add_row(f"{opt} {prefix}", trap)

        console.print(trap_table)

        # 8. Official Solution Markdown
        console.print(Panel(
            Markdown(question.official_explanation),
            title="[bold cyan]Official Rigorous Derivation[/bold cyan]",
            border_style="cyan"
        ))

        # 9. 60-Second Counter Micro-Drill
        console.print(Panel(
            f"[bold white]{report.micro_drill_question}[/bold white]\n\n[dim cyan]Press Enter to reveal micro-drill solution...[/dim cyan]",
            title="[bold magenta]Instant 60-Second Micro-Drill (Retain the Concept)[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED
        ))
        Prompt.ask("")
        console.print(Panel(
            f"[bold green]Micro-Drill Solution:[/bold green]\n{report.micro_drill_answer}",
            border_style="green"
        ))
