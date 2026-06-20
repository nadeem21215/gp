from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
import models


def get_student_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.firebase_uid == firebase_uid).first()


def get_course(db: Session, code: str) -> Optional[models.Course]:
    return db.query(models.Course).filter(models.Course.code == code).first()


def get_passed_history(db: Session, student_id: int) -> List[models.StudentHistory]:
    return db.query(models.StudentHistory).filter(
        models.StudentHistory.student_id == student_id,
        models.StudentHistory.status == "passed"
    ).all()


def get_failed_history(db: Session, student_id: int) -> List[models.StudentHistory]:
    return db.query(models.StudentHistory).filter(
        models.StudentHistory.student_id == student_id,
        models.StudentHistory.status == "failed"
    ).all()


def get_passed_courses(db: Session, student_id: int) -> List[models.Course]:
    passed_history = get_passed_history(db, student_id)
    codes = [h.course_code for h in passed_history]
    return db.query(models.Course).filter(models.Course.code.in_(codes)).all()


def get_failed_courses(db: Session, student_id: int) -> List[models.Course]:
    failed_history = get_failed_history(db, student_id)
    codes = [h.course_code for h in failed_history]
    return db.query(models.Course).filter(models.Course.code.in_(codes)).all()


def get_current_registrations(db: Session, student_id: int) -> List[models.Registration]:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return []
    return db.query(models.Registration).filter(
        models.Registration.student_id   == student_id,
        models.Registration.academic_year == student.current_year,
        models.Registration.term          == student.current_term,
    ).all()


def get_registrations_for_term(db: Session, student_id: int, academic_year: int, term: int) -> List[models.Registration]:
    return db.query(models.Registration).filter(
        models.Registration.student_id   == student_id,
        models.Registration.academic_year == academic_year,
        models.Registration.term          == term,
    ).all()


# ─────────────────────────────────────────────
#  NEW HELPERS
# ─────────────────────────────────────────────

def get_max_allowed_hours(gpa: float) -> int:
    """
    Returns the maximum credit hours a student is allowed to register
    in a single term, based on their cumulative GPA (official bylaw):

    GPA >= 3.0          → 21 hours   (3 فأكثر)
    2.0 <= GPA < 3.0    → 18 hours   (من 2 لأقل من 3)
    1.0 <= GPA < 2.0    → 15 hours   (من 1 لأقل من 2)
    GPA < 1.0           → 12 hours   (أقل من 1)
    """
    if gpa >= 3.0:
        return 21
    elif gpa >= 2.0:
        return 18
    elif gpa >= 1.0:
        return 15
    else:
        return 12


def get_next_term_info(current_year: int, current_term: int) -> Tuple[int, int]:
    """
    Returns (next_academic_year, next_term) given the student's current position.

    Term numbering used in the DB:
        Year 1 Term 1  → target_term = 1
        Year 1 Term 2  → target_term = 2
        Year 2 Term 1  → target_term = 3
        Year 2 Term 2  → target_term = 4
        …etc.

    Progression rule:
        current_term == 1  →  stay in same year, move to term 2
        current_term == 2  →  advance year, move to term 1
    """
    if current_term == 1:
        return current_year, 2
    else:
        return current_year + 1, 1


def compute_next_target_term(next_year: int, next_term: int) -> int:
    """Convert (academic_year, term_within_year) to the flat target_term integer."""
    return (next_year - 1) * 2 + next_term


def get_doctor_names_map(db: Session) -> dict:
    """Returns {firebase_uid: name} for every registered instructor account."""
    doctors = db.query(models.Student).filter(models.Student.role == "doctor").all()
    return {d.firebase_uid: d.name for d in doctors}


def should_promote_student(db: Session, student: models.Student) -> bool:
    """
    Determines whether the student has met the criteria to be considered
    as 'having completed' their current term so they can advance.
    """
    current_target_term = (student.current_year - 1) * 2 + student.current_term

    # Fetch all courses that belong to the current term
    term_courses = db.query(models.Course).filter(
        models.Course.target_term == current_target_term
    ).all()

    if not term_courses:
        # No courses defined for this term — allow progression
        return True

    term_codes = [c.code for c in term_courses] # تحويلها لـ list لضمان التوافق

    # [تأمين الكود] إذا كانت القائمة فارغة لأي سبب لا تبحث في الـ in_
    if not term_codes:
        return True

    # Check if any of these courses appear in the student's history
    history_for_term = db.query(models.StudentHistory).filter(
        models.StudentHistory.student_id == student.id,
        models.StudentHistory.course_code.in_(term_codes)
    ).count()

    return history_for_term > 0