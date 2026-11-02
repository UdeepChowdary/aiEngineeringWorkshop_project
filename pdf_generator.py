"""PDF Generator for ExamSentinel: Creates publication-grade Dossier reports."""
import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from models import (
    ExamBlueprint,
    QuestionItem,
    DistractorMap,
    DiagnosticReport,
    PersonalizedStudyPlan
)

def _clean_markdown_to_xml(text: str) -> str:
    """Converts basic markdown bold/italic/code syntax to ReportLab XML tags."""
    if not text:
        return ""
    # Remove complex LaTeX math dollars or replace with clean markers
    text = re.sub(r'\$\$(.*?)\$\$', r'<b>[\1]</b>', text)
    text = re.sub(r'\$(.*?)\$', r'<b>\1</b>', text)
    # Convert markdown bold **text** to <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert *text* to <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Convert `code` to <font name="Courier">\1</font>
    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
    # Clean up bare ampersands
    text = re.sub(r'&(?!amp;|lt;|gt;)', '&amp;', text)
    # Convert newlines to breaks
    text = text.replace('\n', '<br/>')
    return text

def generate_sparring_dossier_pdf(
    blueprint: ExamBlueprint,
    question: QuestionItem,
    distractor_map: DistractorMap,
    user_choice: str,
    user_reasoning: str,
    defense_response: str,
    report: DiagnosticReport
) -> bytes:
    """Generates an executive PDF report of the candidate's exam sparring performance."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )

    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # 1. Header
    story.append(Paragraph("🛡️ ExamSentinel — Candidate Mastery Dossier", title_style))
    story.append(Paragraph("Adversarial Examination & Socratic Sparring Committee Post-Mortem", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#38bdf8'), spaceAfter=10))

    # 2. Executive Metadata Box
    is_correct = report.is_correct
    status_text = "PASSED / CONCEPT SOUND" if is_correct else "FLAGGED / CONCEPT TRAP DETECTED"
    status_bg = colors.HexColor('#dcfce7') if is_correct else colors.HexColor('#fee2e2')
    status_fg = colors.HexColor('#166534') if is_correct else colors.HexColor('#991b1b')

    meta_data = [
        [
            Paragraph(f"<b>Exam:</b> {blueprint.exam_name}", body_style),
            Paragraph(f"<b>Marking:</b> {blueprint.marking_scheme}", body_style)
        ],
        [
            Paragraph(f"<b>Topic:</b> {blueprint.topic}", body_style),
            Paragraph(f"<b>Difficulty:</b> {blueprint.difficulty_tier}", body_style)
        ],
        [
            Paragraph(f"<b>Cognitive Tier:</b> {report.error_category}", body_style),
            Paragraph(f"<b>Candidate Status:</b> {status_text}", ParagraphStyle('Stat', parent=body_style, textColor=status_fg, fontName='Helvetica-Bold'))
        ],
        [
            Paragraph(f"<b>Real Exam Benchmark:</b> {getattr(question, 'pyq_benchmark', 'Standard Exam Benchmark')}", body_style),
            Paragraph(f"<b>Isomorphism Score:</b> {getattr(question, 'exam_isomorphism_score', 94)}%", body_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. Problem Statement & Options
    story.append(Paragraph("1. Audited Problem Statement", h2_style))
    story.append(Paragraph(_clean_markdown_to_xml(question.question), body_style))
    story.append(Spacer(1, 6))

    opt_rows = []
    for k, v in question.options.items():
        is_official = (k.strip().upper() == question.correct_answer.strip().upper())
        is_user = (k.strip().upper() == user_choice.strip().upper())
        tag = ""
        if is_official and is_user:
            tag = " <b>(Official Answer & Your Choice ✅)</b>"
        elif is_official:
            tag = " <b>(Official Answer ✅)</b>"
        elif is_user:
            tag = " <b>(Your Selected Choice ❌)</b>"
            
        opt_rows.append([
            Paragraph(f"<b>({k})</b>", body_style),
            Paragraph(f"{_clean_markdown_to_xml(v)}{tag}", body_style)
        ])

    opt_table = Table(opt_rows, colWidths=[30, 510])
    opt_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(opt_table)
    story.append(Spacer(1, 8))

    # 4. Socratic Defense Transcript
    story.append(Paragraph("2. Candidate Socratic Defense Record", h2_style))
    defense_data = [
        [Paragraph("<b>Initial Rationale:</b>", body_style), Paragraph(_clean_markdown_to_xml(user_reasoning), body_style)],
        [Paragraph("<b>Oral Defense:</b>", body_style), Paragraph(_clean_markdown_to_xml(defense_response), body_style)]
    ]
    def_table = Table(defense_data, colWidths=[110, 430])
    def_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(def_table)
    story.append(Spacer(1, 8))

    # 5. Diagnostic Evaluation & Prescription
    story.append(Paragraph("3. Committee Diagnostic Evaluation & Prescription", h2_style))
    diag_box = [
        [Paragraph(f"<b>Diagnostic Assessment:</b><br/>{_clean_markdown_to_xml(report.diagnosis_summary)}", callout_style)],
        [Paragraph(f"<b>Exam-Day Rule of Thumb:</b><br/>{_clean_markdown_to_xml(report.prescription)}", callout_style)]
    ]
    diag_table = Table(diag_box, colWidths=[540])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dbeafe')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 8))

    # 6. Examiner Trap Deconstruction
    story.append(Paragraph("4. Examiner Trap Psychology Matrix", h2_style))
    trap_rows = [["Option", "Trap / Psychological Vulnerability"]]
    for opt, trap in distractor_map.option_traps.items():
        trap_rows.append([
            f"Option {opt}",
            Paragraph(_clean_markdown_to_xml(trap), body_style)
        ])
    trap_table = Table(trap_rows, colWidths=[65, 475])
    trap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94a3b8')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(trap_table)
    story.append(Spacer(1, 8))

    # 7. Official Step-by-Step Proof
    story.append(Paragraph("5. Rigorous Step-by-Step Proof", h2_style))
    story.append(Paragraph(_clean_markdown_to_xml(question.official_explanation), body_style))
    story.append(Spacer(1, 8))

    # 8. 60-Second Micro Remediation Drill
    story.append(Paragraph("6. Targeted 60-Second Micro-Remediation Drill", h2_style))
    drill_content = [
        [Paragraph(f"<b>Follow-Up Drill:</b> {report.micro_drill_question}", body_style)],
        [Paragraph(f"<b>Proof & Answer:</b> {report.micro_drill_answer}", body_style)]
    ]
    drill_table = Table(drill_content, colWidths=[540])
    drill_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fefce8')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#fef08a')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fef9c3')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(drill_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_study_plan_pdf(topic: str, exam: str, plan: PersonalizedStudyPlan) -> bytes:
    """Generates an executive PDF roadmap of the personalized study plan."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # 1. Header
    story.append(Paragraph(f"🗺️ ExamSentinel — Personalized Mastery Plan", title_style))
    story.append(Paragraph(f"Diagnostic Curriculum for {topic} ({exam})", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#818cf8'), spaceAfter=10))

    # 2. Diagnosed Bottleneck & Breakthrough Analogy
    story.append(Paragraph("1. Cognitive Diagnostics & Mental Shift", h2_style))
    shift_table = Table([
        [Paragraph(f"<b>⚠️ Diagnosed Cognitive Bottleneck:</b><br/>{_clean_markdown_to_xml(plan.diagnosed_bottleneck)}", body_style)],
        [Paragraph(f"<b>💡 Breakthrough Mental Model:</b><br/>{_clean_markdown_to_xml(plan.breakthrough_mental_model)}", body_style)]
    ], colWidths=[540])
    shift_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(shift_table)
    story.append(Spacer(1, 10))

    # 3. Progressive Phases
    story.append(Paragraph("2. Progressive Scaffolded Roadmap", h2_style))
    for idx, phase in enumerate(plan.phases, start=1):
        steps_xml = "<br/>".join([f"• {_clean_markdown_to_xml(s)}" for s in phase.actionable_steps])
        phase_rows = [
            [Paragraph(f"<b>{phase.phase_title}</b> <i>({phase.time_estimate})</i>", ParagraphStyle('PhTitle', parent=body_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#1e40af')))],
            [Paragraph(f"<b>🎯 Core Milestone:</b> {_clean_markdown_to_xml(phase.core_objective)}", body_style)],
            [Paragraph(f"<b>Actionable Steps:</b><br/>{steps_xml}", body_style)]
        ]
        if phase.high_yield_trap_warning:
            phase_rows.append([Paragraph(f"<b>⚠️ High-Yield Trap Warning:</b> {_clean_markdown_to_xml(phase.high_yield_trap_warning)}", ParagraphStyle('Warn', parent=body_style, textColor=colors.HexColor('#b45309')))])
        
        ph_table = Table(phase_rows, colWidths=[540])
        ph_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(ph_table)
        story.append(Spacer(1, 6))

    # 4. Practice Ladder & Mastery Benchmark
    story.append(Paragraph("3. Practice Ladder & Exam Benchmark", h2_style))
    ladder_xml = "<br/>".join([f"{i}. {_clean_markdown_to_xml(p)}" for i, p in enumerate(plan.practice_ladder, start=1)])
    benchmark_data = [
        [Paragraph(f"<b>Recommended Practice Problem Ladder:</b><br/>{ladder_xml}", body_style)],
        [Paragraph(f"<b>Final Exam-Level Mastery Benchmark:</b><br/>{_clean_markdown_to_xml(plan.mastery_benchmark)}", body_style)]
    ]
    b_table = Table(benchmark_data, colWidths=[540])
    b_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dbeafe')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(b_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
