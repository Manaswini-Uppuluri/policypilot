"""
Synthetic University Policy PDF Generator for PolicyPilot.
Generates multi-page, formatted PDF policy documents using PyMuPDF.
Clearly labeled as demonstration data for technical evaluation.
"""
import os
import sys
from pathlib import Path
import fitz  # PyMuPDF

# Ensure backend app is on sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.database import get_session, get_engine, Base
from app.services.ingestion import ingest_pdf_file

SAMPLE_DIR = Path(__file__).resolve().parent

POLICIES = [
    {
        "filename": "Attendance_and_Lab_Policy.pdf",
        "category": "Academic & Attendance",
        "version": "2026.1",
        "effective_date": "August 2026",
        "pages": [
            (
                "APEX UNIVERSITY - ACADEMIC ATTENDANCE POLICY (DEMO DATA)\n"
                "Document Reference: APEX-ACAD-2026-01 | Effective Date: August 1, 2026\n\n"
                "SECTION 1: STATUTORY ATTENDANCE THRESHOLDS\n"
                "1.1 Minimum Attendance Requirement:\n"
                "All registered undergraduate and postgraduate students must maintain a minimum attendance of 75% in each enrolled theory course and 80% in scheduled laboratory practicals.\n"
                "1.2 Calculation of Percentage:\n"
                "Attendance shall be computed from the date of commencement of instruction up to the final instructional day of the semester.\n"
                "1.3 Condonation of Shortage:\n"
                "The Academic Dean may condone attendance shortage between 65% and 74% strictly on genuine medical grounds upon submission of certified hospital records and payment of the prescribed condonation fee."
            ),
            (
                "APEX UNIVERSITY - LABORATORY AND PRACTICAL REGULATIONS\n\n"
                "SECTION 2: LABORATORY SESSION EXEMPTION AND COMPENSATORY MAKE-UP\n"
                "2.1 Mandatory Lab Attendance:\n"
                "Practical sessions and engineering laboratories are experiential learning components. Students requesting exemption from scheduled laboratory sessions must obtain prior authorization from the concerned faculty.\n"
                "2.2 Compensatory Make-Up Protocols:\n"
                "If an absence is sanctioned by the course coordinator due to unforeseen family obligations, cultural representation, or medical reasons, the student must apply for a compensatory lab session within five (5) working days.\n"
                "2.3 Unexcused Lab Absences:\n"
                "Unexcused non-attendance at more than two laboratory sessions shall result in a grade drop or cancellation of practical coursework evaluation.\n\n"
                "SECTION 3: MEDICAL LEAVE AND EXCUSED ABSENCE\n"
                "3.1 Notification: A student who falls ill must notify the academic mentor via the university portal within 48 hours of missing classes."
            )
        ]
    },
    {
        "filename": "Academic_Integrity_and_Exams.pdf",
        "category": "Examinations & Ethics",
        "version": "2026.2",
        "effective_date": "September 2026",
        "pages": [
            (
                "APEX UNIVERSITY - ACADEMIC INTEGRITY AND EXAMINATION CODE (DEMO DATA)\n"
                "Document Reference: APEX-EXAM-2026-04 | Effective Date: September 1, 2026\n\n"
                "SECTION 1: INTERNAL ASSESSMENTS AND MID-TERM EXAMINATIONS\n"
                "1.1 Continuous Internal Evaluation (CIE):\n"
                "Students must obtain a minimum of 40% aggregate marks in internal tests to qualify for appearing in the End-Semester Examination.\n"
                "1.2 Absence During Mid-Terms:\n"
                "A student who misses an internal assessment due to severe medical illness or approved inter-collegiate university sports/cultural representation may be granted a compensatory re-test, provided an authorized application with medical fitness certificate is submitted within three (3) working days."
            ),
            (
                "APEX UNIVERSITY - MALPRACTICE AND DISCIPLINARY ACTIONS\n\n"
                "SECTION 2: ACADEMIC MISCONDUCT DEFINITIONS\n"
                "2.1 Prohibited Acts in Examinations:\n"
                "Possession of mobile phones, smartwatches, programmable calculators, cheat sheets, or unauthorized digital communication (including messaging apps such as WhatsApp, Telegram, or Discord) during tests constitutes severe malpractice.\n"
                "2.2 Plagiarism in Submissions:\n"
                "All project reports, assignments, and dissertation theses must have a similarity index below 15% using standard institutional plagiarism detection software.\n"
                "2.3 Sanctions and Penalties:\n"
                "Students proven guilty of examination malpractice shall face immediate course cancellation, zero credit award for the semester, and possible one-year suspension upon recommendation of the Academic Disciplinary Board."
            )
        ]
    },
    {
        "filename": "Hostel_and_Campus_Conduct.pdf",
        "category": "Student Affairs & Residence",
        "version": "2026.1",
        "effective_date": "July 2026",
        "pages": [
            (
                "APEX UNIVERSITY - HOSTEL AND CAMPUS RESIDENCE MANUAL (DEMO DATA)\n"
                "Document Reference: APEX-HOSTEL-2026-02 | Effective Date: July 15, 2026\n\n"
                "SECTION 1: CURFEW AND ENTRY TIMINGS\n"
                "1.1 Daily Curfew:\n"
                "All resident students must return to their designated hostel premises by 10:00 PM on weekdays (Monday through Friday) and by 10:30 PM on weekends (Saturday and Sunday).\n"
                "1.2 Late Entry and Gate Pass:\n"
                "Students arriving after curfew without prior written permission from the Chief Warden shall have their biometric access flagged and face disciplinary notification to parents.\n"
                "1.3 Overnight Leave:\n"
                "Night-out leave requests must be submitted through the student hostel portal at least 24 hours in advance and requires digital parent/guardian consent."
            ),
            (
                "APEX UNIVERSITY - HOSTEL DISCIPLINE AND GUEST POLICY\n\n"
                "SECTION 2: VISITORS AND ROOM TRANSFERS\n"
                "2.1 Visitor Policy:\n"
                "External guests, day-scholars, and friends are permitted in common lounge areas between 10:00 AM and 6:00 PM only. Under no circumstances are overnight guests allowed inside student dorm rooms.\n"
                "2.2 Guest House Accommodations:\n"
                "Visiting parents or immediate family members may reserve guest rooms in the University International House subject to availability and payment of subsidized daily rates.\n"
                "2.3 Noise and Quiet Hours:\n"
                "Quiet hours are observed strictly between 11:00 PM and 6:00 AM daily. Violations of quiet hours or rowdy conduct will lead to eviction from university housing."
            )
        ]
    }
]

def generate_pdf(filename: str, pages: list[str]) -> str:
    out_path = SAMPLE_DIR / filename
    doc = fitz.open()
    for text_content in pages:
        page = doc.new_page(width=595, height=842) # A4 size
        rect = fitz.Rect(50, 50, 545, 792)
        page.insert_textbox(rect, text_content, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
    doc.save(str(out_path))
    doc.close()
    return str(out_path)

def build_and_ingest_all():
    print("Building synthetic sample policy PDFs...")
    eng = get_engine()
    Base.metadata.create_all(bind=eng)

    db = get_session()
    try:
        for p in POLICIES:
            pdf_path = generate_pdf(p["filename"], p["pages"])
            print(f"Generated: {pdf_path}")
            policy = ingest_pdf_file(
                file_path=pdf_path,
                original_filename=p["filename"],
                category=p["category"],
                version=p["version"],
                effective_date=p["effective_date"],
                db=db
            )
            print(f"Ingested policy '{policy.document_name}' ({policy.total_chunks} chunks).")
    finally:
        db.close()
    print("All sample policies successfully generated and indexed!")

if __name__ == "__main__":
    build_and_ingest_all()
