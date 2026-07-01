import os
import json
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas

# Define paths
LOG_FILE_PATH = "/Users/tejasmahadik/Downloads/TCS_ION_PERFORMANCE_LOG_TEJAS_MAHADIK_2026_1782054961031.json"
PDF_FILE_PATH = "/Users/tejasmahadik/Downloads/TCS_ION_EXAM_REPORT_TEJAS_MAHADIK_2026.pdf"

class NumberedCanvas(canvas.Canvas):
    """Custom canvas to compute total page numbers and add headers/footers dynamically."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#2C3E50"))
        
        # Header (Only on page 2 and later)
        if self._pageNumber > 1:
            self.drawString(54, 750, "TCS iON MOCK ASSESSMENT PERFORMANCE REPORT")
            self.drawRightString(558, 750, "CANDIDATE ID: TEJAS_MAHADIK_2026")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 34, "Confidential - For Personal Review Only")
        self.drawRightString(558, 34, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def clean_html(raw_html):
    """Clean HTML tags like <br> from question text."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', raw_html)
    return cleantext.replace('Directions: Find out the part which is grammatically wrong. In case the sentence is alright (No Error), mark E as your answer. ', '').strip()

def generate_report():
    if not os.path.exists(LOG_FILE_PATH):
        print(f"Error: Log file not found at {LOG_FILE_PATH}")
        return

    with open(LOG_FILE_PATH, "r") as f:
        data = json.load(f)

    # 1. Calculate stats
    questions = data["questions"]
    total_q = len(questions)
    attempted = 0
    correct = 0
    incorrect = 0
    score = 0.0

    category_stats = {}

    for q in questions:
        cat = q["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0, "incorrect": 0, "attempted": 0}
        category_stats[cat]["total"] += 1

        ans = q["userAnswer"]
        if ans:
            attempted += 1
            category_stats[cat]["attempted"] += 1
            if ans == q["correct"]:
                correct += 1
                score += 1.0
                category_stats[cat]["correct"] += 1
            else:
                incorrect += 1
                score -= 0.25
                category_stats[cat]["incorrect"] += 1

    accuracy = (correct / attempted * 100) if attempted > 0 else 0.0

    # 2. Build Document Setup
    doc = SimpleDocTemplate(
        PDF_FILE_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=25
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2C3E50"),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    story = []

    # --- PAGE 1: TITLE & EXECUTIVE SUMMARY ---
    # Title Block
    story.append(Paragraph("TCS iON MOCK ASSESSMENT REPORT", title_style))
    story.append(Paragraph("EXAM SPECIFICATION: IBPS SO ENGLISH LANGUAGE FOCUS MOCK", subtitle_style))
    story.append(Spacer(1, 10))

    # Candidate Meta Details Block
    meta_data = [
        [Paragraph("Candidate Name:", bold_body_style), Paragraph("Tejas Mahadik", body_style), Paragraph("Exam Session ID:", bold_body_style), Paragraph(data["session"]["examId"], body_style)],
        [Paragraph("Candidate ID:", bold_body_style), Paragraph(data["session"]["candidateId"], body_style), Paragraph("Attempt Timestamp:", bold_body_style), Paragraph("June 21, 2026", body_style)],
        [Paragraph("Time Remaining:", bold_body_style), Paragraph(f"{data['session']['timerRemainingSeconds']} seconds", body_style), Paragraph("Assessment Status:", bold_body_style), Paragraph("Submitted / Graded", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[110, 140, 110, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # Executive Summary Card
    story.append(Paragraph("Executive Performance Metrics", h2_style))
    metrics_data = [
        [
            Paragraph("Total Score", table_header_style), 
            Paragraph("Correct", table_header_style), 
            Paragraph("Incorrect", table_header_style), 
            Paragraph("Attempted", table_header_style), 
            Paragraph("Accuracy", table_header_style)
        ],
        [
            Paragraph(f"<b>{score:.2f} / {total_q:.2f}</b>", body_style),
            Paragraph(str(correct), body_style),
            Paragraph(str(incorrect), body_style),
            Paragraph(f"{attempted} / {total_q}", body_style),
            Paragraph(f"<b>{accuracy:.1f}%</b>", body_style)
        ]
    ]
    metrics_table = Table(metrics_data, colWidths=[100, 100, 100, 100, 100])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F0FDFA") if score >= 7.5 else colors.HexColor("#FFF8F8")),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 25))

    # Category Breakdown Table
    story.append(Paragraph("Syllabus Category Breakdown", h2_style))
    cat_data = [
        [
            Paragraph("Syllabus Category", table_header_style),
            Paragraph("Questions", table_header_style),
            Paragraph("Correct", table_header_style),
            Paragraph("Incorrect", table_header_style),
            Paragraph("Accuracy", table_header_style)
        ]
    ]
    
    for cat, stats in category_stats.items():
        cat_acc = (stats["correct"] / stats["attempted"] * 100) if stats["attempted"] > 0 else 0.0
        acc_text = f"{cat_acc:.0f}%" if stats["attempted"] > 0 else "0% (Unattempted)"
        cat_data.append([
            Paragraph(cat, body_style),
            Paragraph(str(stats["total"]), body_style),
            Paragraph(str(stats["correct"]), body_style),
            Paragraph(str(stats["incorrect"]), body_style),
            Paragraph(f"<b>{acc_text}</b>", body_style)
        ])
        
    cat_table = Table(cat_data, colWidths=[200, 75, 75, 75, 75])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(cat_table)
    story.append(PageBreak())

    # --- PAGES 2+: ANSWERS LEDGER & ITEM ANALYSIS ---
    story.append(Paragraph("Detailed Question-by-Question Replay Ledger", h2_style))
    
    for i, q in enumerate(questions):
        q_num = i + 1
        q_text = clean_html(q["question"])
        user_ans = q["userAnswer"] or "Not Attempted"
        correct_key = q["correct"]
        is_correct = user_ans == correct_key
        
        # Color coding response
        if not q["userAnswer"]:
            status_text = "<font color='#64748B'><b>UNATTEMPTED</b></font>"
            score_text = "0.00"
            bg_color = colors.HexColor("#F8FAFC")
            border_color = colors.HexColor("#E2E8F0")
        elif is_correct:
            status_text = "<font color='#10B981'><b>CORRECT</b></font>"
            score_text = "+1.00"
            bg_color = colors.HexColor("#F0FDFA")
            border_color = colors.HexColor("#B9F6CA")
        else:
            status_text = "<font color='#EF4444'><b>INCORRECT</b></font>"
            score_text = "-0.25"
            bg_color = colors.HexColor("#FEF2F2")
            border_color = colors.HexColor("#FFCDD2")

        q_header = f"Question {q_num} &mdash; Category: <i>{q['category']}</i>"
        
        story.append(Paragraph(q_header, h2_style))
        
        # Question Detail Box
        details = [
            [Paragraph("Question Text:", bold_body_style), Paragraph(q_text, body_style)],
            [Paragraph("Your Selection:", bold_body_style), Paragraph(f"Option {user_ans}", body_style)],
            [Paragraph("Correct Answer:", bold_body_style), Paragraph(f"Option {correct_key}", body_style)],
            [Paragraph("Evaluation Status:", bold_body_style), Paragraph(f"{status_text} (Points: {score_text})", body_style)],
            [Paragraph("Grammar Breakdown:", bold_body_style), Paragraph(q["explanation"], body_style)]
        ]
        
        q_table = Table(details, colWidths=[120, 380])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('GRID', (0,0), (-1,-1), 1.0, border_color),
            ('PADDING', (0,0), (-1,-1), 7),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        story.append(q_table)
        story.append(Spacer(1, 15))
        
        # Add page break every 3 questions to prevent ugly flow cuts
        if q_num % 3 == 0 and q_num < 15:
            story.append(PageBreak())

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully compiled and written to {PDF_FILE_PATH}")

if __name__ == "__main__":
    generate_report()
