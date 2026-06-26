from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Tuple, Optional
from datetime import datetime
import os, uuid, shutil

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key    = os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure     = True,
)

from database import SessionLocal, engine
import models, crud

models.Base.metadata.create_all(bind=engine)

# ── Lightweight migration: add courses.description if missing (SQLite) ──
with engine.connect() as _conn:
    _cols = [row[1] for row in _conn.execute(text("PRAGMA table_info(courses)"))]
    if "description" not in _cols:
        _conn.execute(text("ALTER TABLE courses ADD COLUMN description VARCHAR"))
        _conn.commit()
    # ── Migration: add students.profile_picture if missing ──
    _student_cols = [row[1] for row in _conn.execute(text("PRAGMA table_info(students)"))]
    if "profile_picture" not in _student_cols:
        _conn.execute(text("ALTER TABLE students ADD COLUMN profile_picture VARCHAR"))
        _conn.commit()

# ── Auto-seed: always reseed if doctor names are outdated ──
def _auto_seed():
    db = SessionLocal()
    try:
        count = db.query(models.Student).count()
        if count == 0:
            print("[SEED] Database is empty — running seed...")
            from seed_db import seed
            seed()
            print("[SEED] Done.")
        else:
            # Check if old doctor names exist — reseed if so
            old_doctor = db.query(models.Student).filter(
                models.Student.firebase_uid.in_(["doctor_ahmed", "doctor_sara"])
            ).first()
            if old_doctor:
                print("[SEED] Old doctor UIDs detected — force reseeding...")
                db.query(models.StudentHistory).delete()
                db.query(models.Registration).delete()
                db.query(models.Submission).delete()
                db.query(models.Assignment).delete()
                db.query(models.CourseSchedule).delete()
                db.query(models.Course).delete()
                db.query(models.Student).delete()
                db.commit()
                db.close()
                from seed_db import seed
                seed()
                print("[SEED] Done.")
            else:
                print(f"[SEED] Skipped — {count} users already in DB.")
    finally:
        try:
            db.close()
        except:
            pass

_auto_seed()

app = FastAPI(title="Smart Institute API", version="7.0.0")

@app.post("/admin/reseed")
def force_reseed():
    """Force re-seed the database — deletes all data and re-seeds."""
    import models as _models
    from seed_db import seed as _seed
    db = SessionLocal()
    try:
        db.query(_models.StudentHistory).delete()
        db.query(_models.Registration).delete()
        db.query(_models.Submission).delete()
        db.query(_models.Assignment).delete()
        db.query(_models.CourseSchedule).delete()
        db.query(_models.Course).delete()
        db.query(_models.Student).delete()
        db.commit()
    finally:
        db.close()
    _seed()
    return {"status": "reseeded successfully"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
#  Input models
# ─────────────────────────────────────────────────────────

class CourseAction(BaseModel):
    student_id: int
    course_code: str

class RegisterRequest(BaseModel):
    firebase_uid: str
    course_codes: List[str]


# ─────────────────────────────────────────────────────────
#  Helper: term lock check
# ─────────────────────────────────────────────────────────

def check_term_lock(db: Session, student: models.Student) -> Tuple[bool, str]:
    current_target_term = (student.current_year - 1) * 2 + student.current_term
    current_term_courses = db.query(models.Course).filter(
        models.Course.target_term == current_target_term
    ).all()
    if not current_term_courses:
        return False, ""
    ungraded_courses = []
    for course in current_term_courses:
        history = db.query(models.StudentHistory).filter(
            models.StudentHistory.student_id == student.id,
            models.StudentHistory.course_code == course.code
        ).first()
        if not history or history.status not in ["passed", "failed"] or not history.grade:
            ungraded_courses.append(course.code)
    if ungraded_courses:
        return True, f"Term is locked. Grade the following courses first: {', '.join(ungraded_courses)}"
    return False, ""


# ══════════════════════════════════════════════════════════
#  Auth & Profile
# ══════════════════════════════════════════════════════════

@app.post("/login")
def login(student_code: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.Student).filter(
    models.Student.firebase_uid == student_code.strip()
).first()
    if not user or user.password.strip() != password.strip():
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return {
        "status": "success",
        "name": user.name,
        "firebase_uid": user.firebase_uid,
        "role": user.role,
        "gpa": user.gpa,
        "current_year": user.current_year,
        "current_term": user.current_term,
    }


@app.get("/student/profile/{firebase_uid}")
def get_student_profile(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    passed  = crud.get_passed_courses(db, student.id)
    failed  = crud.get_failed_courses(db, student.id)
    total_hours = sum(c.credit_hours for c in passed)
    max_allowed_hours = crud.get_max_allowed_hours(student.gpa)
    warnings = student.warnings if student.warnings else 0

    next_year, next_term = crud.get_next_term_info(student.current_year, student.current_term)
    has_registered = db.query(models.Registration).filter(
        models.Registration.student_id    == student.id,
        models.Registration.academic_year == next_year,
        models.Registration.term          == next_term,
    ).first() is not None

    return {
        "firebase_uid":               student.firebase_uid,
        "name":                       student.name,
        "gpa":                        student.gpa,
        "current_year":               student.current_year,
        "current_term":               student.current_term,
        "total_passed_credit_hours":  total_hours,
        "credit_hours":               total_hours,
        "passed_courses_count":       len(passed),
        "failed_courses_count":       len(failed),
        "warnings":                   warnings,
        "is_suspended":               student.is_suspended,
        "max_allowed_hours":          max_allowed_hours,
        "has_registered":             has_registered,
        "profile_picture":            student.profile_picture or None,
    }


# ══════════════════════════════════════════════════════════
#  [FIX #1] Profile Picture Management
# ══════════════════════════════════════════════════════════

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "assignment_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/profile/picture/upload")
async def upload_profile_picture(
    firebase_uid: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload or update a user's profile picture (stored on Cloudinary)."""
    user = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete old Cloudinary image if exists
    if user.profile_picture and user.profile_picture.startswith("smart_institute/profile_"):
        try:
            public_id = user.profile_picture  # we store the public_id directly
            cloudinary.uploader.destroy(public_id)
        except Exception:
            pass

    public_id = f"smart_institute/profile_{user.id}_{uuid.uuid4().hex}"

    try:
        file_bytes = await file.read()
        result = cloudinary.uploader.upload(
            file_bytes,
            public_id   = public_id,
            overwrite   = True,
            folder      = "",          # folder already in public_id
            resource_type = "image",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {e}")

    # Store the Cloudinary public_id in the DB (URL is derived on download)
    user.profile_picture = public_id
    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "profile_picture": user.profile_picture,
        "download_url": f"/profile/picture/download/{firebase_uid}",
    }


@app.get("/profile/picture/download/{firebase_uid}")
def download_profile_picture(firebase_uid: str, db: Session = Depends(get_db)):
    """Return the Cloudinary URL for a user's profile picture."""
    from fastapi.responses import RedirectResponse
    user = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.profile_picture:
        raise HTTPException(status_code=404, detail="No profile picture found")

    # Build Cloudinary delivery URL from stored public_id
    url = cloudinary.utils.cloudinary_url(user.profile_picture)[0]
    return RedirectResponse(url=url)




def _build_schedule_for_uid(firebase_uid: str, db: Session) -> list:
    """
    Shared helper: returns schedule items for any user (student or doctor).
    For students  → uses their Registration rows.
    For doctors   → uses courses where doctor_uid matches.
    """
    user = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = []

    if user.role == "student":
        registrations = db.query(models.Registration).filter(
            models.Registration.student_id == user.id
        ).all()
        codes = [r.course_code for r in registrations]
    else:  # doctor or admin
        courses = db.query(models.Course).filter(
            models.Course.doctor_uid == firebase_uid
        ).all()
        codes = [c.code for c in courses]

    for code in codes:
        sched = db.query(models.CourseSchedule).filter(
            models.CourseSchedule.course_code == code
        ).first()
        if not sched:
            continue
        course = crud.get_course(db, code)
        doctor = None
        if course and course.doctor_uid:
            doctor = crud.get_student_by_firebase_uid(db, course.doctor_uid)
        enrolled_count = db.query(models.Registration).filter(
            models.Registration.course_code == code
        ).count()
        result.append({
            "course_code": code,
            "course_name": course.name if course else code,
            "days":        sched.days,
            "time_from":   sched.time_from,
            "time_to":     sched.time_to,
            "hall":        sched.hall or "",
            "doctor_name":    doctor.name if doctor else "",
            "enrolled_count": enrolled_count,
        })

    return result


@app.get("/student/schedule/{firebase_uid}")
def get_student_schedule(firebase_uid: str, db: Session = Depends(get_db)):
    return _build_schedule_for_uid(firebase_uid, db)


@app.get("/doctor/schedule/{doctor_uid}")
def get_doctor_schedule(doctor_uid: str, db: Session = Depends(get_db)):
    return _build_schedule_for_uid(doctor_uid, db)


# ══════════════════════════════════════════════════════════
#  Available courses for registration
# ══════════════════════════════════════════════════════════

@app.get("/courses")
def get_available_courses(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    registered_codes = {
        r.course_code for r in db.query(models.Registration)
        .filter(models.Registration.student_id == student.id)
        .all()
    }

    current_year = student.current_year
    current_term = student.current_term

    if current_year == 1 and current_term == 1:
        prev_target_term = None
    elif current_term == 1:
        prev_year = current_year - 1
        prev_target_term = (prev_year - 1) * 2 + 2
    else:
        prev_target_term = (current_year - 1) * 2 + 1

    target_term = (current_year - 1) * 2 + current_term

    passed_codes = {h.course_code for h in crud.get_passed_history(db, student.id)}
    failed_codes = {h.course_code for h in crud.get_failed_history(db, student.id)} - passed_codes

    retake_courses   = db.query(models.Course).filter(models.Course.code.in_(failed_codes)).all()
    scheduled_courses = db.query(models.Course).filter(models.Course.target_term == target_term).all()

    candidate_map = {}
    for c in retake_courses:
        if c.code not in passed_codes and c.code not in registered_codes:
            candidate_map[c.code] = c
    for c in scheduled_courses:
        if c.code not in passed_codes and c.code not in registered_codes:
            candidate_map[c.code] = c

    priority_1, priority_2, priority_3 = [], [], []
    for code, c in candidate_map.items():
        if c.prerequisite_code and c.prerequisite_code not in passed_codes:
            continue
        if c.code in failed_codes:
            priority_1.append(c)
        elif getattr(c, "is_elective", False):
            priority_3.append(c)
        else:
            priority_2.append(c)

    sorted_candidates = priority_1 + priority_2 + priority_3
    max_hours = crud.get_max_allowed_hours(student.gpa)
    used_hours = 0
    recommended_courses = []

    for c in sorted_candidates:
        fits_cap = (used_hours + c.credit_hours <= max_hours)

        # [FIX #5] Attach schedule info to each course
        sched = db.query(models.CourseSchedule).filter(
            models.CourseSchedule.course_code == c.code
        ).first()

        # Attach instructor name
        doctor = crud.get_student_by_firebase_uid(db, c.doctor_uid) if c.doctor_uid else None
        instructor_name = doctor.name if doctor else ""

        category = (
            "Failed (Retake)" if c.code in failed_codes else
            "Elective"        if getattr(c, "is_elective", False) else
            "Core"
        )

        recommended_courses.append({
            "id":                abs(hash(c.code)) % 1_000_000,
            "name":              c.name,
            "code":              c.code,
            "credit_hours":      c.credit_hours,
            "is_enrolled":       False,
            "is_available":      fits_cap,
            "is_retake":         c.code in failed_codes,
            "is_elective":       getattr(c, "is_elective", False),
            "priority_category": category,
            "priority_level":    1 if c.code in failed_codes else (3 if getattr(c, "is_elective", False) else 2),
            "prerequisite_code": c.prerequisite_code,
            # new schedule fields
            "doctor_name":       instructor_name,
            "days":              sched.days      if sched else "",
            "time_from":         sched.time_from if sched else "",
            "time_to":           sched.time_to   if sched else "",
            "hall":              sched.hall       if sched else "",
        })

        if fits_cap:
            used_hours += c.credit_hours

    return recommended_courses


# ══════════════════════════════════════════════════════════
#  Register courses
# ══════════════════════════════════════════════════════════

MIN_CREDIT_HOURS = 10  # Academic regulation: minimum credit hours per term


@app.get("/registration-limits/{firebase_uid}")
def get_registration_limits(firebase_uid: str, db: Session = Depends(get_db)):
    """Credit-hour limits for the registration page (GPA-based)."""
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {
        "gpa":       student.gpa,
        "min_hours": MIN_CREDIT_HOURS,
        "max_hours": crud.get_max_allowed_hours(student.gpa),
    }


@app.post("/register-courses")
def register_courses(request: RegisterRequest, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, request.firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.is_suspended == "suspended":
        raise HTTPException(status_code=400, detail="Student account is suspended. Please contact administration.")

    _check_next_year, _check_next_term = crud.get_next_term_info(student.current_year, student.current_term)
    already_registered = db.query(models.Registration).filter(
        models.Registration.student_id    == student.id,
        models.Registration.academic_year == _check_next_year,
        models.Registration.term          == _check_next_term,
    ).first()
    if already_registered:
        raise HTTPException(status_code=409, detail="You have already registered for this term.")

    next_year, next_term_within_year = crud.get_next_term_info(student.current_year, student.current_term)
    passed_codes = {h.course_code for h in crud.get_passed_history(db, student.id)}
    failed_codes = {h.course_code for h in crud.get_failed_history(db, student.id)} - passed_codes
    max_hours = crud.get_max_allowed_hours(student.gpa)
    total_requested_hours = 0
    courses_to_register = []

    for code in request.course_codes:
        course = crud.get_course(db, code)
        if not course:
            raise HTTPException(status_code=404, detail=f"Course {code} not found.")
        if course.prerequisite_code and course.prerequisite_code not in passed_codes:
            raise HTTPException(status_code=400, detail=f"Course {course.name} requires {course.prerequisite_code} first.")
        if course.code in passed_codes:
            raise HTTPException(status_code=400, detail=f"Course {course.name} already passed.")
        total_requested_hours += course.credit_hours
        courses_to_register.append(course)

    if total_requested_hours < MIN_CREDIT_HOURS:
        raise HTTPException(
            status_code=400,
            detail=f"You must register at least {MIN_CREDIT_HOURS} credit hours before submitting your registration. You selected {total_requested_hours}."
        )

    if total_requested_hours > max_hours:
        raise HTTPException(
            status_code=400,
            detail=f"Your GPA ({student.gpa:.2f}) allows a maximum of {max_hours} credit hours. You selected {total_requested_hours}."
        )

    mandatory_failed = []
    acc_hours = 0
    for code in failed_codes:
        course = crud.get_course(db, code)
        if course and (not course.prerequisite_code or course.prerequisite_code in passed_codes):
            if acc_hours + course.credit_hours <= max_hours:
                mandatory_failed.append(code)
                acc_hours += course.credit_hours

    skipped = [c for c in mandatory_failed if c not in request.course_codes]
    if skipped:
        raise HTTPException(status_code=400, detail=f"You must register failed courses first: {', '.join(skipped)}")

    db.query(models.Registration).filter(
        models.Registration.student_id    == student.id,
        models.Registration.academic_year == next_year,
        models.Registration.term          == next_term_within_year
    ).delete()

    for c in courses_to_register:
        db.add(models.Registration(
            student_id    = student.id,
            course_code   = c.code,
            academic_year = next_year,
            term          = next_term_within_year
        ))

    db.commit()

    return {
        "status": "success",
        "message": f"Successfully registered {len(courses_to_register)} courses.",
        "registered_courses": [c.code for c in courses_to_register],
        "total_credit_hours": total_requested_hours
    }


# ══════════════════════════════════════════════════════════
#  Student courses (registered)
# ══════════════════════════════════════════════════════════

@app.get("/student/courses/{firebase_uid}")
def get_student_courses(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    all_registrations = db.query(models.Registration).filter(
        models.Registration.student_id == student.id
    ).all()

    courses = []
    for reg in all_registrations:
        course = crud.get_course(db, reg.course_code)
        if course:
            sched = db.query(models.CourseSchedule).filter(
                models.CourseSchedule.course_code == reg.course_code
            ).first()
            doctor = crud.get_student_by_firebase_uid(db, course.doctor_uid) if course.doctor_uid else None
            courses.append({
                "id":           abs(hash(course.code)) % 1_000_000,
                "name":         course.name,
                "code":         course.code,
                "credit_hours": course.credit_hours,
                "term":         reg.term,
                "doctor_name":  doctor.name if doctor else "",
                "days":         sched.days      if sched else "",
                "time_from":    sched.time_from if sched else "",
                "time_to":      sched.time_to   if sched else "",
                "hall":         sched.hall       if sched else "",
            })

    return {
        "student_name":       student.name,
        "registered_courses": courses,
        "total_credit_hours": sum(c["credit_hours"] for c in courses),
    }


# ══════════════════════════════════════════════════════════
#  Curriculum
# ══════════════════════════════════════════════════════════

@app.get("/curriculum")
def get_curriculum(db: Session = Depends(get_db)):
    courses = db.query(models.Course).all()
    curriculum: dict = {}
    for c in courses:
        sched = db.query(models.CourseSchedule).filter(
            models.CourseSchedule.course_code == c.code
        ).first()
        doctor = crud.get_student_by_firebase_uid(db, c.doctor_uid) if c.doctor_uid else None
        k = f"Term_{c.target_term}"
        curriculum.setdefault(k, [])
        curriculum[k].append({
            "code":              c.code,
            "name":              c.name,
            "credit_hours":      c.credit_hours,
            "target_year":       c.target_year,
            "target_term":       c.target_term,
            "prerequisite_code": c.prerequisite_code,
            "is_elective":       getattr(c, "is_elective", False),
            "doctor_uid":        c.doctor_uid or "",
            "doctor_name":       doctor.name if doctor else "",
            "days":              sched.days      if sched else "",
            "time_from":         sched.time_from if sched else "",
            "time_to":           sched.time_to   if sched else "",
            "hall":              sched.hall       if sched else "",
        })
    return {
        "curriculum": dict(
            sorted(curriculum.items(), key=lambda x: int(x[0].split("_")[1]))
        )
    }


# ══════════════════════════════════════════════════════════
#  [FIX #8] Admin Stats — full statistics
# ══════════════════════════════════════════════════════════

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    student_count     = db.query(models.Student).filter(models.Student.role == "student").count()
    instructor_count  = db.query(models.Student).filter(models.Student.role == "doctor").count()
    course_count      = db.query(models.Course).count()
    enrollment_count  = db.query(models.Registration).count()
    # Departments: distinct prefixes from course codes (e.g. CS, BS, IS, H)
    from sqlalchemy import func
    all_codes = db.query(models.Course.code).all()
    departments = set()
    for (code,) in all_codes:
        prefix = code.split(" ")[0]
        departments.add(prefix)
    dept_count = len(departments)

    suspended_count = db.query(models.Student).filter(
        models.Student.role == "student",
        models.Student.is_suspended == "suspended"
    ).count()

    # Students who have at least one registration
    from sqlalchemy import distinct
    registered_count = db.query(models.Registration.student_id).distinct().count()

    return {
        "student_count":     student_count,
        "instructor_count":  instructor_count,
        "course_count":      course_count,
        "enrollment_count":  enrollment_count,
        "department_count":  dept_count,
        "suspended_count":   suspended_count,
        "registered_count":  registered_count,
        "academic_year":     "2025 / 2026",
    }


# ══════════════════════════════════════════════════════════
#  Students list & detail
# ══════════════════════════════════════════════════════════

@app.get("/students")
def get_all_students(db: Session = Depends(get_db)):
    students = db.query(models.Student).filter(models.Student.role == "student").all()
    result = []
    for s in students:
        passed = crud.get_passed_courses(db, s.id)
        registrations = db.query(models.Registration).filter(models.Registration.student_id == s.id).all()
        reg_courses = []
        for reg in registrations:
            course = crud.get_course(db, reg.course_code)
            if course:
                reg_courses.append({
                    "id":           abs(hash(course.code)) % 1_000_000,
                    "name":         course.name,
                    "code":         course.code,
                    "credit_hours": course.credit_hours,
                })
        result.append({
            "id":           s.id,
            "name":         s.name,
            "student_code": s.firebase_uid,
            "level":        f"Year {s.current_year}",
            "gpa":          s.gpa,
            "credit_hours": sum(c.credit_hours for c in passed),
            "warnings":     s.warnings if s.warnings else 0,
            "is_suspended": s.is_suspended,
            "courses":      reg_courses,
        })
    return result


@app.get("/instructors")
def get_all_instructors(db: Session = Depends(get_db)):
    """
    List every instructor (doctor) account so the admin UI can offer a
    proper name-based picker instead of requiring a raw firebase_uid.
    """
    doctors = db.query(models.Student).filter(models.Student.role == "doctor").all()
    return [
        {
            "firebase_uid": d.firebase_uid,
            "name": d.name,
            "profile_picture": d.profile_picture or None,
        }
        for d in doctors
    ]


@app.put("/instructors/{doctor_uid}")
def update_instructor_name(doctor_uid: str, name: str, db: Session = Depends(get_db)):
    """Update an instructor's name."""
    doctor = crud.get_student_by_firebase_uid(db, doctor_uid)
    if not doctor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    if doctor.role != "doctor":
        raise HTTPException(status_code=403, detail="Only instructors can be updated here")
    
    doctor.name = name.strip()
    db.commit()
    db.refresh(doctor)
    return {"status": "success", "firebase_uid": doctor.firebase_uid, "name": doctor.name}


# ══════════════════════════════════════════════════════════
#  [FIX #5] Doctor's Students — filtered by enrollment
# ══════════════════════════════════════════════════════════

@app.get("/doctor/students/{doctor_uid}")
def get_doctor_students(doctor_uid: str, db: Session = Depends(get_db)):
    """Get all students enrolled in courses taught by this doctor (instructor)."""
    doctor = crud.get_student_by_firebase_uid(db, doctor_uid)
    if not doctor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    if doctor.role != "doctor":
        raise HTTPException(status_code=403, detail="Only instructors have students")
    
    # Get all courses taught by this doctor
    doctor_courses = db.query(models.Course).filter(
        models.Course.doctor_uid == doctor_uid
    ).all()
    
    course_codes = [c.code for c in doctor_courses]
    if not course_codes:
        return []
    
    # Get all student registrations in those courses
    registrations = db.query(models.Registration).filter(
        models.Registration.course_code.in_(course_codes)
    ).all()
    
    student_ids = [r.student_id for r in registrations]
    if not student_ids:
        return []
    
    # Get unique students (remove duplicates from multiple course enrollments)
    unique_student_ids = list(set(student_ids))
    students = db.query(models.Student).filter(
        models.Student.id.in_(unique_student_ids),
        models.Student.role == "student"
    ).all()
    
    result = []
    for student in students:
        # Get only the courses this student takes with this doctor
        student_courses = [
            r.course_code for r in registrations
            if r.student_id == student.id
        ]
        student_course_objs = db.query(models.Course).filter(
            models.Course.code.in_(student_courses)
        ).all()
        
        courses = []
        for course in student_course_objs:
            courses.append({
                "id": abs(hash(course.code)) % 1_000_000,
                "name": course.name,
                "code": course.code,
                "credit_hours": course.credit_hours,
            })
        
        result.append({
            "id": student.id,
            "name": student.name,
            "student_code": student.firebase_uid,
            "level": f"Year {student.current_year} - Term {student.current_term}",
            "gpa": student.gpa,
            "warnings": student.warnings if student.warnings else 0,
            "credit_hours": sum(c["credit_hours"] for c in courses),
            "courses": courses,
        })
    
    return result



def get_student_detail(student_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    passed = crud.get_passed_courses(db, s.id)
    registrations = db.query(models.Registration).filter(models.Registration.student_id == s.id).all()
    reg_courses = []
    for reg in registrations:
        course = crud.get_course(db, reg.course_code)
        if course:
            reg_courses.append({
                "id":           abs(hash(course.code)) % 1_000_000,
                "name":         course.name,
                "code":         course.code,
                "credit_hours": course.credit_hours,
            })
    return {
        "id":           s.id,
        "name":         s.name,
        "student_code": s.firebase_uid,
        "level":        f"Year {s.current_year}",
        "gpa":          s.gpa,
        "credit_hours": sum(c.credit_hours for c in passed),
        "warnings":     s.warnings if s.warnings else 0,
        "is_suspended": s.is_suspended,
        "courses":      reg_courses,
    }


# ══════════════════════════════════════════════════════════
#  [FIX #6] Student history — includes grade field
# ══════════════════════════════════════════════════════════

@app.get("/student/history/{firebase_uid}")
def get_student_history(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    history = db.query(models.StudentHistory).filter(
        models.StudentHistory.student_id == student.id
    ).all()
    result = []
    for h in history:
        course = crud.get_course(db, h.course_code)
        result.append({
            "course_code":   h.course_code,
            "course_name":   course.name         if course else "Unknown",
            "credit_hours":  course.credit_hours  if course else 0,
            "target_year":   course.target_year   if course else None,
            "target_term":   course.target_term   if course else None,
            "status":        h.status,
            "grade":         h.grade,       # ← always included
        })
    return {"student": student.name, "history": result}


# ══════════════════════════════════════════════════════════
#  [FIX #7] Course detail endpoint — instructor + schedule
# ══════════════════════════════════════════════════════════

@app.get("/course/{course_code}")
def get_course_detail(course_code: str, db: Session = Depends(get_db)):
    course = crud.get_course(db, course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    sched  = db.query(models.CourseSchedule).filter(
        models.CourseSchedule.course_code == course_code
    ).first()
    doctor = crud.get_student_by_firebase_uid(db, course.doctor_uid) if course.doctor_uid else None

    prereq_name = None
    if course.prerequisite_code:
        prereq = crud.get_course(db, course.prerequisite_code)
        prereq_name = prereq.name if prereq else course.prerequisite_code

    return {
        "code":              course.code,
        "name":              course.name,
        "credit_hours":      course.credit_hours,
        "target_year":       course.target_year,
        "target_term":       course.target_term,
        "is_elective":       getattr(course, "is_elective", False),
        "prerequisite_code": course.prerequisite_code,
        "prerequisite_name": prereq_name,
        "doctor_uid":        course.doctor_uid or "",
        "doctor_name":       doctor.name if doctor else "",
        "days":              sched.days      if sched else "",
        "time_from":         sched.time_from if sched else "",
        "time_to":           sched.time_to   if sched else "",
        "hall":              sched.hall       if sched else "",
        "description":       course.description or "",
    }


class CourseDescriptionUpdate(BaseModel):
    doctor_uid: str
    description: str


@app.put("/course/{course_code}/description")
def update_course_description(course_code: str, payload: CourseDescriptionUpdate, db: Session = Depends(get_db)):
    course = crud.get_course(db, course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    doctor = crud.get_student_by_firebase_uid(db, payload.doctor_uid)
    if not doctor or doctor.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Only instructors may edit course descriptions.")
    if doctor.role == "doctor" and course.doctor_uid != payload.doctor_uid:
        raise HTTPException(status_code=403, detail="You are not the instructor of this course.")

    course.description = payload.description.strip() or None
    db.commit()
    return {"status": "success", "description": course.description or ""}


# ══════════════════════════════════════════════════════════
#  Doctor courses & schedule
# ══════════════════════════════════════════════════════════

@app.get("/doctor/courses/{doctor_uid}")
def get_doctor_courses(doctor_uid: str, db: Session = Depends(get_db)):
    doctor = crud.get_student_by_firebase_uid(db, doctor_uid)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    courses = db.query(models.Course).filter(models.Course.doctor_uid == doctor_uid).all()
    result = []
    for c in courses:
        sched = db.query(models.CourseSchedule).filter(
            models.CourseSchedule.course_code == c.code
        ).first()
        result.append({
            "code":              c.code,
            "name":              c.name,
            "credit_hours":      c.credit_hours,
            "target_year":       c.target_year,
            "target_term":       c.target_term,
            "prerequisite_code": c.prerequisite_code,
            "is_elective":       getattr(c, "is_elective", False),
            "days":              sched.days      if sched else "",
            "time_from":         sched.time_from if sched else "",
            "time_to":           sched.time_to   if sched else "",
            "hall":              sched.hall       if sched else "",
            "description":       c.description or "",
            "doctor_uid":        c.doctor_uid or "",
        })

    return {
        "doctor_uid":    doctor_uid,
        "doctor_name":   doctor.name,
        "courses":       result,
        "total_courses": len(result),
    }


# ══════════════════════════════════════════════════════════
#  Admin — add/remove course from student
# ══════════════════════════════════════════════════════════

@app.post("/add_course")
def add_course_to_student(action: CourseAction, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == action.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    course = crud.get_course(db, action.course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    existing = db.query(models.Registration).filter(
        models.Registration.student_id  == action.student_id,
        models.Registration.course_code == action.course_code,
    ).first()
    if not existing:
        db.add(models.Registration(
            student_id    = action.student_id,
            course_code   = action.course_code,
            academic_year = student.current_year,
            term          = student.current_term,
        ))
        db.commit()
    return {"status": "success"}


@app.post("/remove_course")
def remove_course(action: CourseAction, db: Session = Depends(get_db)):
    registration = db.query(models.Registration).filter(
        models.Registration.student_id  == action.student_id,
        models.Registration.course_code == action.course_code,
    ).first()
    if registration:
        db.delete(registration)
        db.commit()
        return {"status": "success"}
    history = db.query(models.StudentHistory).filter(
        models.StudentHistory.student_id  == action.student_id,
        models.StudentHistory.course_code == action.course_code,
    ).first()
    if history:
        db.delete(history)
        db.commit()
        return {"status": "success"}
    return {"status": "success"}


# ══════════════════════════════════════════════════════════
#  Utility / reset endpoints
# ══════════════════════════════════════════════════════════

@app.delete("/api/reset-all-registrations")
def reset_all_registrations(db: Session = Depends(get_db)):
    deleted = db.query(models.Registration).delete(synchronize_session=False)
    db.commit()
    return {"status": "success", "message": f"{deleted} registration rows cleared.", "deleted_rows": deleted}


@app.get("/api/clear-registration/{firebase_uid}")
def clear_registration(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    deleted_rows = db.query(models.Registration).filter(
        models.Registration.student_id == student.id
    ).delete(synchronize_session=False)
    db.commit()
    return {"firebase_uid": firebase_uid, "student_id": student.id, "deleted_rows": deleted_rows}


# ══════════════════════════════════════════════════════════
#  Assignments
# ══════════════════════════════════════════════════════════

@app.post("/assignments/upload")
async def upload_assignment(
    doctor_uid:   str        = Form(...),
    course_code:  str        = Form(...),
    title:        str        = Form(...),
    description:  str        = Form(""),
    due_date:     str        = Form(""),
    file:         UploadFile = File(...),
    db: Session = Depends(get_db),
):
    doctor = crud.get_student_by_firebase_uid(db, doctor_uid)
    if not doctor or doctor.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Only instructors may upload assignments.")
    course = crud.get_course(db, course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    if doctor.role == "doctor" and course.doctor_uid != doctor_uid:
        raise HTTPException(status_code=403, detail="You are not the instructor of this course.")

    ext = os.path.splitext(file.filename)[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOAD_DIR, stored_name)
    with open(dest, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out)

    assignment = models.Assignment(
        course_code  = course_code,
        doctor_uid   = doctor_uid,
        title        = title,
        description  = description,
        filename     = file.filename,
        stored_name  = stored_name,
        uploaded_at  = datetime.utcnow().isoformat(),
        due_date     = due_date or None,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    # Notify all students registered in this course (must never break the upload)
    try:
        send_new_assignment_notification(db, course_code)
    except Exception as e:
        print(f"[FCM] Notification error: {e}")

    return {"status": "success", "assignment_id": assignment.id}


@app.get("/assignments/student/{firebase_uid}")
def list_assignments_for_student(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    registrations = db.query(models.Registration).filter(
        models.Registration.student_id == student.id
    ).all()
    codes = [r.course_code for r in registrations]
    if not codes:
        return []
    assignments = db.query(models.Assignment).filter(
        models.Assignment.course_code.in_(codes)
    ).order_by(models.Assignment.uploaded_at.desc()).all()
    result = []
    for a in assignments:
        course = crud.get_course(db, a.course_code)
        result.append({
            "id": a.id, "title": a.title, "description": a.description or "",
            "filename": a.filename, "course_code": a.course_code,
            "course_name": course.name if course else a.course_code,
            "due_date": a.due_date or "", "uploaded_at": a.uploaded_at,
        })
    return result


@app.get("/assignments/doctor/{doctor_uid}")
def list_assignments_by_doctor(doctor_uid: str, db: Session = Depends(get_db)):
    assignments = db.query(models.Assignment).filter(
        models.Assignment.doctor_uid == doctor_uid
    ).order_by(models.Assignment.uploaded_at.desc()).all()
    result = []
    for a in assignments:
        course = crud.get_course(db, a.course_code)
        result.append({
            "id": a.id, "title": a.title, "description": a.description or "",
            "filename": a.filename, "course_code": a.course_code,
            "course_name": course.name if course else a.course_code,
            "due_date": a.due_date or "", "uploaded_at": a.uploaded_at,
        })
    return result


@app.get("/assignments/download/{assignment_id}")
def download_assignment(assignment_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    path = os.path.join(UPLOAD_DIR, a.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on server.")
    return FileResponse(path, media_type="application/octet-stream", filename=a.filename)


@app.delete("/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, doctor_uid: str, db: Session = Depends(get_db)):
    a = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    doctor = crud.get_student_by_firebase_uid(db, doctor_uid)
    if not doctor:
        raise HTTPException(status_code=403, detail="Unauthorized.")
    if doctor.role not in ("admin",) and a.doctor_uid != doctor_uid:
        raise HTTPException(status_code=403, detail="You can only delete your own assignments.")
    path = os.path.join(UPLOAD_DIR, a.stored_name)
    if os.path.exists(path):
        os.remove(path)
    db.delete(a)
    db.commit()
    return {"status": "success"}


# ══════════════════════════════════════════════════════════
#  Submissions (student answers to assignments)
# ══════════════════════════════════════════════════════════

SUBMISSION_DIR = os.path.join(os.path.dirname(__file__), "submission_files")
os.makedirs(SUBMISSION_DIR, exist_ok=True)


@app.post("/submissions/upload")
async def upload_submission(
    student_uid:   str        = Form(...),
    assignment_id: int        = Form(...),
    file:          UploadFile = File(...),
    db: Session = Depends(get_db),
):
    student = crud.get_student_by_firebase_uid(db, student_uid)
    if not student or student.role != "student":
        raise HTTPException(status_code=403, detail="Only students may submit solutions.")

    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    registered = db.query(models.Registration).filter(
        models.Registration.student_id  == student.id,
        models.Registration.course_code == assignment.course_code,
    ).first()
    if not registered:
        raise HTTPException(status_code=403, detail="You are not registered in this course.")

    ext = os.path.splitext(file.filename)[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(SUBMISSION_DIR, stored_name)
    with open(dest, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out)

    # Re-submission replaces the previous file for the same assignment
    existing = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment_id,
        models.Submission.student_id    == student.id,
    ).first()

    if existing:
        old_path = os.path.join(SUBMISSION_DIR, existing.stored_name)
        if os.path.exists(old_path):
            os.remove(old_path)
        existing.filename     = file.filename
        existing.stored_name  = stored_name
        existing.submitted_at = datetime.utcnow().isoformat()
        db.commit()
        db.refresh(existing)
        return {"status": "success", "submission_id": existing.id, "resubmitted": True}

    submission = models.Submission(
        assignment_id = assignment_id,
        student_id    = student.id,
        filename      = file.filename,
        stored_name   = stored_name,
        submitted_at  = datetime.utcnow().isoformat(),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return {"status": "success", "submission_id": submission.id, "resubmitted": False}


@app.get("/submissions/student/{firebase_uid}")
def list_submissions_for_student(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    submissions = db.query(models.Submission).filter(
        models.Submission.student_id == student.id
    ).order_by(models.Submission.submitted_at.desc()).all()
    result = []
    for s in submissions:
        result.append({
            "id": s.id, "assignment_id": s.assignment_id,
            "filename": s.filename, "submitted_at": s.submitted_at,
            "student_name": student.name, "student_code": student.firebase_uid,
        })
    return result


@app.get("/submissions/assignment/{assignment_id}")
def list_submissions_for_assignment(assignment_id: int, doctor_uid: str, db: Session = Depends(get_db)):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    doctor = crud.get_student_by_firebase_uid(db, doctor_uid)
    if not doctor or doctor.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Only instructors may view submissions.")
    if doctor.role == "doctor" and assignment.doctor_uid != doctor_uid:
        raise HTTPException(status_code=403, detail="You can only view submissions for your own assignments.")

    submissions = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment_id
    ).order_by(models.Submission.submitted_at.desc()).all()
    result = []
    for s in submissions:
        student = db.query(models.Student).filter(models.Student.id == s.student_id).first()
        result.append({
            "id": s.id, "assignment_id": s.assignment_id,
            "filename": s.filename, "submitted_at": s.submitted_at,
            "student_name": student.name if student else "Unknown",
            "student_code": student.firebase_uid if student else "",
        })
    return result


@app.get("/submissions/download/{submission_id}")
def download_submission(submission_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found.")
    path = os.path.join(SUBMISSION_DIR, s.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on server.")
    return FileResponse(path, media_type="application/octet-stream", filename=s.filename)


# ══════════════════════════════════════════════════════════
#  Push Notifications (Firebase Cloud Messaging)
# ══════════════════════════════════════════════════════════
#  Requires: pip install firebase-admin
#  Place your Firebase service account key file next to main.py
#  as "serviceAccountKey.json" (Firebase Console → Project Settings
#  → Service accounts → Generate new private key).

SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serviceAccountKey.json")
_fcm_ready = False

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    if os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            firebase_admin.initialize_app(credentials.Certificate(SERVICE_ACCOUNT_PATH))
            _fcm_ready = True
            print("[FCM] Firebase Admin initialized.")
        except Exception as e:
            print(f"[FCM] Initialization failed: {e}")
    else:
        print("[FCM] serviceAccountKey.json not found — push notifications disabled.")
except ImportError:
    print("[FCM] firebase-admin not installed — push notifications disabled.")


class TokenRegistration(BaseModel):
    firebase_uid: str
    fcm_token: str


@app.post("/notifications/register-token")
def register_fcm_token(payload: TokenRegistration, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, payload.firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="User not found.")

    existing = db.query(models.DeviceToken).filter(
        models.DeviceToken.token == payload.fcm_token
    ).first()

    if existing:
        # Token may have moved to another account on the same device
        existing.student_id = student.id
        existing.updated_at = datetime.utcnow().isoformat()
    else:
        db.add(models.DeviceToken(
            student_id = student.id,
            token      = payload.fcm_token,
            updated_at = datetime.utcnow().isoformat(),
        ))
    db.commit()
    return {"status": "success"}


def send_new_assignment_notification(db: Session, course_code: str):
    """Send an FCM push to every student registered in the given course."""
    if not _fcm_ready:
        return

    student_ids = [
        r.student_id for r in db.query(models.Registration).filter(
            models.Registration.course_code == course_code
        ).all()
    ]
    if not student_ids:
        return

    tokens = [
        t.token for t in db.query(models.DeviceToken).filter(
            models.DeviceToken.student_id.in_(student_ids)
        ).all()
    ]
    if not tokens:
        return

    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(
            title="New Assignment",
            body="A new assignment has been uploaded for your course.",
        ),
        data={
            "type": "new_assignment",
            "course_code": course_code,
        },
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id="assignments_channel",
                click_action="FLUTTER_NOTIFICATION_CLICK",
            ),
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message)
        print(f"[FCM] Sent: {response.success_count} ok, {response.failure_count} failed.")
        # Clean up invalid/expired tokens
        for idx, resp in enumerate(response.responses):
            if not resp.success and resp.exception is not None:
                code = getattr(getattr(resp.exception, "code", None), "name", str(resp.exception))
                if "UNREGISTERED" in str(resp.exception) or "INVALID" in str(resp.exception).upper():
                    db.query(models.DeviceToken).filter(
                        models.DeviceToken.token == tokens[idx]
                    ).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        print(f"[FCM] Send failed: {e}")


# ══════════════════════════════════════════════════════════
#  AI Chat (Smart Institute Assistant)
# ══════════════════════════════════════════════════════════
#  The model lives in ai_provider.py — swap it there without
#  touching these endpoints. Requires: pip install google-genai

from ai_provider import get_ai_provider, UNIVERSITY_SYSTEM_PROMPT


class ChatRequest(BaseModel):
    user_id: str          # student firebase_uid / student code
    message: str


def _build_student_context(db: Session, user_id: str) -> str:
    """
    Build the full Za3boula context: student status, full curriculum with prereqs,
    passed/failed history, all doctors and their courses, all students list.
    """
    student = crud.get_student_by_firebase_uid(db, user_id)
    if not student:
        return ""

    # -- بيانات الطالب الأساسية --
    passed_history = crud.get_passed_history(db, student.id)
    failed_history = crud.get_failed_history(db, student.id)
    passed_codes = [h.course_code for h in passed_history] or []
    failed_codes = [h.course_code for h in failed_history] or []

    student_gpa = float(student.gpa) if student.gpa is not None else 0.0
    max_allowed_hours = crud.get_max_allowed_hours(student_gpa)

    current_year = student.current_year
    current_term = student.current_term
    expected_term = (current_year * 2 - 1) if current_term == 1 else (current_year * 2)

    all_courses = db.query(models.Course).all()
    doctor_names = crud.get_doctor_names_map(db)

    # -- تحليل مواد الترم الحالي --
    failed_courses_to_register = []
    current_term_core_available = []
    current_term_elective_available = []
    current_term_locked = []

    for course in all_courses:
        code = course.code
        prereq = course.prerequisite_code
        if code in failed_codes:
            if prereq is None or prereq in passed_codes:
                failed_courses_to_register.append(f"{course.name} ({code})")
        elif int(course.target_year) == int(current_year) and int(course.target_term) == int(expected_term):
            if prereq is None or prereq in passed_codes:
                if course.is_elective:
                    current_term_elective_available.append(f"{course.name} ({code})")
                else:
                    current_term_core_available.append(f"{course.name} ({code})")
            else:
                current_term_locked.append(f"{course.name} ({code}) بسبب عدم اجتياز المتطلب ({prereq})")

    failed_reg_str = ", ".join(failed_courses_to_register) if failed_courses_to_register else "لا يوجد"
    core_str       = ", ".join(current_term_core_available) if current_term_core_available else "لا يوجد"
    elective_str   = ", ".join(current_term_elective_available) if current_term_elective_available else "لا يوجد"
    locked_str     = ", ".join(current_term_locked) if current_term_locked else "لا يوجد"

    # -- المواد المجتازة والراسب فيها --
    passed_str = ", ".join([f"{h.course_code} (درجة: {h.grade or 'غير مسجلة'})" for h in passed_history]) or "لا يوجد"
    failed_hist_str = ", ".join([f"{h.course_code} (درجة: {h.grade or 'غير مسجلة'})" for h in failed_history]) or "لا يوجد"

    student_info = f"""
=== بيانات الطالب الحالي ===
الاسم: {student.name}
كود الطالب: {student.firebase_uid}
المعدل التراكمي (GPA): {student_gpa}
السنة الدراسية: {current_year} | الترم: {current_term}
عدد الإنذارات: {student.warnings or 0}
الحد الأقصى للساعات: {max_allowed_hours} ساعة

المواد المجتازة: {passed_str}
المواد الراسب فيها: {failed_hist_str}

أولويات التسجيل للترم القادم:
- إعادة: {failed_reg_str}
- إجبارية متاحة: {core_str}
- اختيارية متاحة: {elective_str}
- مقفولة (المتطلب غير مكتمل): {locked_str}
"""

    # -- الدكاترة --
    doctors_section = "\n=== الدكاترة ===\n"
    all_doctors = db.query(models.Student).filter(models.Student.role == "doctor").all()
    for doc in all_doctors:
        doc_courses = [c for c in all_courses if c.doctor_uid == doc.firebase_uid]
        course_names = ", ".join([f"{c.name}({c.code})" for c in doc_courses]) or "لا يوجد"
        doctors_section += f"{doc.name}: {course_names}\n"

    # -- كل الطلاب --
    students_section = "\n=== الطلاب ===\n"
    all_students = db.query(models.Student).filter(models.Student.role == "student").all()
    for s in all_students:
        students_section += f"{s.name}({s.firebase_uid}) س{s.current_year}ت{s.current_term} GPA:{s.gpa} إنذارات:{s.warnings or 0}\n"

    # -- المنهج الكامل --
    curriculum_section = "\n=== المنهج ===\n"
    for c in sorted(all_courses, key=lambda x: (x.target_year, x.target_term)):
        prereq_info = f" متطلب:{c.prerequisite_code}" if c.prerequisite_code else ""
        elective_info = "اختياري" if c.is_elective else "إجباري"
        doc_name = doctor_names.get(c.doctor_uid, "؟") if c.doctor_uid else "؟"
        curriculum_section += f"{c.name}({c.code}) {c.credit_hours}س س{c.target_year}ت{c.target_term} {elective_info}{prereq_info} د.{doc_name}\n"

    return student_info + doctors_section + students_section + curriculum_section


@app.post("/chat/message")
def chat_message(payload: ChatRequest, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, payload.user_id)
    if not student:
        raise HTTPException(status_code=404, detail="User not found.")

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty.")

    system_instruction = UNIVERSITY_SYSTEM_PROMPT + _build_student_context(db, payload.user_id)

    # Save the user message first so history is never lost
    db.add(models.ChatMessage(
        student_id = student.id,
        role       = "user",
        content    = message,
        created_at = datetime.utcnow().isoformat(),
    ))
    db.commit()

    try:
        ai_response = get_ai_provider().generate(message, system_instruction)
    except Exception as e:
        print(f"[CHAT] AI provider error: {e}")
        raise HTTPException(status_code=500, detail="AI service is unavailable. Please try again.")

    db.add(models.ChatMessage(
        student_id = student.id,
        role       = "assistant",
        content    = ai_response,
        created_at = datetime.utcnow().isoformat(),
    ))
    db.commit()

    return {"status": "success", "ai_response": ai_response}


@app.get("/chat/history/{firebase_uid}")
def chat_history(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="User not found.")
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.student_id == student.id
    ).order_by(models.ChatMessage.id.asc()).all()
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at}
        for m in messages
    ]


@app.delete("/chat/history/{firebase_uid}")
def clear_chat_history(firebase_uid: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_firebase_uid(db, firebase_uid)
    if not student:
        raise HTTPException(status_code=404, detail="User not found.")
    deleted = db.query(models.ChatMessage).filter(
        models.ChatMessage.student_id == student.id
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "success", "deleted": deleted}


# ══════════════════════════════════════════════════════════
#  Admin: Course Management (Create / Update / Delete)
# ══════════════════════════════════════════════════════════

class CourseCreate(BaseModel):
    code: str
    name: str
    credit_hours: int
    target_year: int = 1
    term_in_year: int = 1          # 1 or 2 (within the year)
    prerequisite_code: Optional[str] = None
    is_elective: bool = False
    doctor_uid: Optional[str] = None
    description: Optional[str] = None
    # Lecture schedule (optional at creation; all four are required together
    # if the admin wants the course to show up on student/instructor schedules)
    hall: Optional[str] = None
    days: Optional[str] = None
    time_from: Optional[str] = None
    time_to: Optional[str] = None


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    credit_hours: Optional[int] = None
    target_year: Optional[int] = None
    term_in_year: Optional[int] = None
    prerequisite_code: Optional[str] = None   # send "" to clear
    is_elective: Optional[bool] = None
    doctor_uid: Optional[str] = None          # send "" to clear
    description: Optional[str] = None
    # Lecture schedule — send "" on any of these to leave that piece unchanged.
    # Schedule row is only written when at least one of these is supplied.
    hall: Optional[str] = None
    days: Optional[str] = None
    time_from: Optional[str] = None
    time_to: Optional[str] = None


def _validate_course_fields(db, name=None, credit_hours=None, target_year=None,
                            term_in_year=None, prerequisite_code=None,
                            doctor_uid=None, own_code=None,
                            hall=None, days=None, time_from=None, time_to=None):
    """Shared validation. Raises HTTPException(400) on the first problem."""
    if name is not None and not name.strip():
        raise HTTPException(status_code=400, detail="Course name is required.")
    if credit_hours is not None and not (1 <= credit_hours <= 6):
        raise HTTPException(status_code=400, detail="Credit hours must be between 1 and 6.")
    if target_year is not None and not (1 <= target_year <= 4):
        raise HTTPException(status_code=400, detail="Target year must be between 1 and 4.")
    if term_in_year is not None and term_in_year not in (1, 2):
        raise HTTPException(status_code=400, detail="Term must be 1 or 2.")
    if prerequisite_code:
        if own_code and prerequisite_code.strip() == own_code:
            raise HTTPException(status_code=400, detail="A course cannot be its own prerequisite.")
        if not crud.get_course(db, prerequisite_code.strip()):
            raise HTTPException(status_code=400, detail=f"Prerequisite course '{prerequisite_code}' does not exist.")
    if doctor_uid:
        doctor = crud.get_student_by_firebase_uid(db, doctor_uid.strip())
        if not doctor or doctor.role != "doctor":
            raise HTTPException(status_code=400, detail=f"Instructor '{doctor_uid}' does not exist.")
    # Lecture schedule: if the admin is setting a schedule, days/time_from/time_to
    # must all be present together (hall alone is allowed to stay blank/TBA).
    schedule_pieces = [days, time_from, time_to]
    if any(p for p in schedule_pieces) and not all(p for p in schedule_pieces):
        raise HTTPException(
            status_code=400,
            detail="Days, start time, and end time must all be provided together to set a lecture schedule."
        )


def _upsert_course_schedule(db, course_code, hall=None, days=None, time_from=None, time_to=None):
    """
    Create/update/clear the single CourseSchedule row for a course.
    Called only when the caller actually supplied at least one schedule field.
    """
    sched = db.query(models.CourseSchedule).filter(
        models.CourseSchedule.course_code == course_code
    ).first()

    has_full_schedule = bool(days and time_from and time_to)
    # The admin form sends days/time_from/time_to together as one block.
    # If all three were supplied (not None) but are blank, that's an explicit
    # "remove the schedule" — distinct from hall-only edits, which only
    # touch hall and leave the existing days/time alone.
    schedule_block_supplied = days is not None and time_from is not None and time_to is not None
    explicit_clear = schedule_block_supplied and not has_full_schedule

    if explicit_clear:
        if sched:
            db.delete(sched)
        return

    if not has_full_schedule and not (sched and hall is not None):
        # Nothing meaningful to persist (no existing row, no full schedule supplied)
        return

    if sched:
        if days is not None:
            sched.days = days.strip() if days.strip() else sched.days
        if time_from is not None:
            sched.time_from = time_from.strip() if time_from.strip() else sched.time_from
        if time_to is not None:
            sched.time_to = time_to.strip() if time_to.strip() else sched.time_to
        if hall is not None:
            sched.hall = hall.strip() or None
    elif has_full_schedule:
        db.add(models.CourseSchedule(
            course_code = course_code,
            days        = days.strip(),
            time_from   = time_from.strip(),
            time_to     = time_to.strip(),
            hall        = hall.strip() if hall else None,
        ))


@app.post("/courses")
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    code = payload.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="Course code is required.")
    if crud.get_course(db, code):
        raise HTTPException(status_code=409, detail=f"Course '{code}' already exists.")

    _validate_course_fields(
        db,
        name=payload.name, credit_hours=payload.credit_hours,
        target_year=payload.target_year, term_in_year=payload.term_in_year,
        prerequisite_code=payload.prerequisite_code,
        doctor_uid=payload.doctor_uid, own_code=code,
        hall=payload.hall, days=payload.days,
        time_from=payload.time_from, time_to=payload.time_to,
    )

    course = models.Course(
        code              = code,
        name              = payload.name.strip(),
        credit_hours      = payload.credit_hours,
        target_year       = payload.target_year,
        target_term       = (payload.target_year - 1) * 2 + payload.term_in_year,
        prerequisite_code = payload.prerequisite_code.strip() if payload.prerequisite_code else None,
        is_elective       = payload.is_elective,
        doctor_uid        = payload.doctor_uid.strip() if payload.doctor_uid else None,
        description       = payload.description.strip() if payload.description else None,
    )
    db.add(course)

    _upsert_course_schedule(
        db, code,
        hall=payload.hall, days=payload.days,
        time_from=payload.time_from, time_to=payload.time_to,
    )

    db.commit()
    return {"status": "success", "message": f"Course '{course.name}' created successfully.", "code": course.code}


@app.put("/courses/{course_code}")
def update_course(course_code: str, payload: CourseUpdate, db: Session = Depends(get_db)):
    course = crud.get_course(db, course_code)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_code}' not found.")

    _validate_course_fields(
        db,
        name=payload.name, credit_hours=payload.credit_hours,
        target_year=payload.target_year, term_in_year=payload.term_in_year,
        prerequisite_code=payload.prerequisite_code or None,
        doctor_uid=payload.doctor_uid or None, own_code=course.code,
        hall=payload.hall, days=payload.days,
        time_from=payload.time_from, time_to=payload.time_to,
    )

    if payload.name is not None:
        course.name = payload.name.strip()
    if payload.credit_hours is not None:
        course.credit_hours = payload.credit_hours
    if payload.target_year is not None or payload.term_in_year is not None:
        year = payload.target_year if payload.target_year is not None else course.target_year
        term = payload.term_in_year if payload.term_in_year is not None else (course.target_term - (course.target_year - 1) * 2)
        course.target_year = year
        course.target_term = (year - 1) * 2 + term
    if payload.prerequisite_code is not None:
        course.prerequisite_code = payload.prerequisite_code.strip() or None
    if payload.is_elective is not None:
        course.is_elective = payload.is_elective
    if payload.doctor_uid is not None:
        course.doctor_uid = payload.doctor_uid.strip() or None
    if payload.description is not None:
        course.description = payload.description.strip() or None

    if any(p is not None for p in (payload.hall, payload.days, payload.time_from, payload.time_to)):
        _upsert_course_schedule(
            db, course.code,
            hall=payload.hall, days=payload.days,
            time_from=payload.time_from, time_to=payload.time_to,
        )

    db.commit()
    return {"status": "success", "message": f"Course '{course.name}' updated successfully."}


@app.delete("/courses/{course_code}")
def delete_course(course_code: str, db: Session = Depends(get_db)):
    course = crud.get_course(db, course_code)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_code}' not found.")

    # Protect academic records
    history_count = db.query(models.StudentHistory).filter(
        models.StudentHistory.course_code == course.code).count()
    if history_count:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete '{course.name}': {history_count} academic record(s) reference it.")

    # Protect curriculum integrity (other courses depending on it)
    dependents = db.query(models.Course).filter(
        models.Course.prerequisite_code == course.code).all()
    if dependents:
        names = ", ".join(d.code for d in dependents)
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete '{course.name}': it is a prerequisite for {names}.")

    # Cascade: schedule, registrations, assignments (+files) and their submissions (+files)
    assignments = db.query(models.Assignment).filter(
        models.Assignment.course_code == course.code).all()
    for a in assignments:
        submissions = db.query(models.Submission).filter(
            models.Submission.assignment_id == a.id).all()
        for s in submissions:
            p = os.path.join(SUBMISSION_DIR, s.stored_name)
            if os.path.exists(p):
                os.remove(p)
            db.delete(s)
        p = os.path.join(UPLOAD_DIR, a.stored_name)
        if os.path.exists(p):
            os.remove(p)
        db.delete(a)

    db.query(models.CourseSchedule).filter(
        models.CourseSchedule.course_code == course.code).delete(synchronize_session=False)
    db.query(models.Registration).filter(
        models.Registration.course_code == course.code).delete(synchronize_session=False)

    name = course.name
    db.delete(course)
    db.commit()
    return {"status": "success", "message": f"Course '{name}' deleted successfully."}
