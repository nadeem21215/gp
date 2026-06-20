# text/x-python (models.py)
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from database import Base


class Student(Base):
    __tablename__ = "students"

    id           = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, nullable=False, index=True)
    name         = Column(String, nullable=False)
    gpa          = Column(Float, nullable=False)
    current_year = Column(Integer, nullable=False)
    current_term = Column(Integer, nullable=False)
    password     = Column(String, nullable=False, default="123456")
    role         = Column(String, nullable=False, default="student")
    warnings     = Column(Integer, nullable=False, default=0)
    is_suspended = Column(String, nullable=False, default="active")

    history       = relationship("StudentHistory", back_populates="student")
    registrations = relationship("Registration", back_populates="student")


class Course(Base):
    __tablename__ = "courses"

    code              = Column(String, primary_key=True, index=True)
    name              = Column(String, nullable=False)
    credit_hours      = Column(Integer, nullable=False)
    target_year       = Column(Integer, nullable=False)
    target_term       = Column(Integer, nullable=False)
    prerequisite_code = Column(String, ForeignKey("courses.code"), nullable=True)
    doctor_uid        = Column(String, nullable=True)
    is_elective       = Column(Boolean, nullable=False, default=False)
    description       = Column(String, nullable=True)

    prerequisite = relationship("Course", remote_side=[code])
    schedule     = relationship("CourseSchedule", back_populates="course", uselist=False)


class CourseSchedule(Base):
    """Lecture time slot for a course. One row per course."""
    __tablename__ = "course_schedules"

    id          = Column(Integer, primary_key=True, index=True)
    course_code = Column(String, ForeignKey("courses.code"), unique=True, nullable=False)
    days        = Column(String, nullable=False)   # e.g. "Sun & Tue"
    time_from   = Column(String, nullable=False)   # e.g. "08:00 AM"
    time_to     = Column(String, nullable=False)   # e.g. "09:30 AM"
    hall        = Column(String, nullable=True)    # e.g. "B-204"

    course = relationship("Course", back_populates="schedule")


class StudentHistory(Base):
    __tablename__ = "student_history"

    id          = Column(Integer, primary_key=True, index=True)
    student_id  = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_code = Column(String, ForeignKey("courses.code"), nullable=False)
    status      = Column(String, nullable=False)
    grade       = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint("student_id", "course_code", name="uq_student_course"),)

    student = relationship("Student", back_populates="history")
    course  = relationship("Course")


class Registration(Base):
    __tablename__ = "registrations"

    id            = Column(Integer, primary_key=True, index=True)
    student_id    = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_code   = Column(String, ForeignKey("courses.code"), nullable=False)
    academic_year = Column(Integer, nullable=False)
    term          = Column(Integer, nullable=False)

    student = relationship("Student", back_populates="registrations")
    course  = relationship("Course")


class Assignment(Base):
    __tablename__ = "assignments"

    id           = Column(Integer, primary_key=True, index=True)
    course_code  = Column(String, ForeignKey("courses.code"), nullable=False)
    doctor_uid   = Column(String, ForeignKey("students.firebase_uid"), nullable=False)
    title        = Column(String, nullable=False)
    description  = Column(String, nullable=True)
    filename     = Column(String, nullable=False)
    stored_name  = Column(String, nullable=False, unique=True)
    uploaded_at  = Column(String, nullable=False)
    due_date     = Column(String, nullable=True)

    course = relationship("Course")
    doctor = relationship("Student", foreign_keys=[doctor_uid])


class Submission(Base):
    __tablename__ = "submissions"

    id            = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id    = Column(Integer, ForeignKey("students.id"), nullable=False)
    filename      = Column(String, nullable=False)
    stored_name   = Column(String, nullable=False, unique=True)
    submitted_at  = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),)

    assignment = relationship("Assignment")
    student    = relationship("Student")


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    token      = Column(String, nullable=False, unique=True, index=True)
    updated_at = Column(String, nullable=False)

    student = relationship("Student")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    role       = Column(String, nullable=False)   # "user" | "assistant"
    content    = Column(String, nullable=False)
    created_at = Column(String, nullable=False)

    student = relationship("Student")
