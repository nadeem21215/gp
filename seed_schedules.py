"""
Seed course_schedules table with lecture times.
Run once: python3 seed_schedules.py
"""
import sqlite3

SCHEDULES = [
    # Term 1
    ("H 101",  "Sun & Tue",  "08:00 AM", "09:30 AM", "A-101"),
    ("BS 104", "Mon & Wed",  "08:00 AM", "09:30 AM", "B-204"),
    ("CS 102", "Sun & Tue",  "10:00 AM", "11:30 AM", "C-301"),
    ("CS 101", "Mon & Wed",  "10:00 AM", "11:30 AM", "A-102"),
    ("IS 105", "Sun & Tue",  "12:00 PM", "01:30 PM", "B-101"),
    ("BS 101", "Mon & Wed",  "12:00 PM", "01:30 PM", "C-201"),
    # Term 2
    ("H 203",  "Sun & Tue",  "08:00 AM", "09:30 AM", "A-103"),
    ("CS 104", "Mon & Wed",  "08:00 AM", "09:30 AM", "B-205"),
    ("BS 103", "Sun & Tue",  "10:00 AM", "11:30 AM", "C-302"),
    ("H 202",  "Mon & Wed",  "10:00 AM", "11:30 AM", "A-104"),
    ("CS 103", "Sun & Tue",  "12:00 PM", "01:30 PM", "B-102"),
    ("H 103",  "Mon & Wed",  "12:00 PM", "01:30 PM", "C-202"),
    ("BS 102", "Thu",        "08:00 AM", "10:30 AM", "A-201"),
    # Term 3
    ("IS 207", "Sun & Tue",  "08:00 AM", "09:30 AM", "B-301"),
    ("IS 206", "Mon & Wed",  "08:00 AM", "09:30 AM", "C-401"),
    ("CS 202", "Sun & Tue",  "10:00 AM", "11:30 AM", "A-201"),
    ("BS 202", "Mon & Wed",  "10:00 AM", "11:30 AM", "B-302"),
    ("CS 201", "Sun & Tue",  "12:00 PM", "01:30 PM", "C-402"),
    ("BS 201", "Mon & Wed",  "12:00 PM", "01:30 PM", "A-202"),
    # Term 4
    ("CS 203", "Sun & Tue",  "08:00 AM", "09:30 AM", "B-401"),
    ("CS 204", "Mon & Wed",  "08:00 AM", "09:30 AM", "C-501"),
    ("CS 205", "Sun & Tue",  "10:00 AM", "11:30 AM", "A-301"),
    ("CS 310", "Mon & Wed",  "10:00 AM", "11:30 AM", "B-402"),
    ("CS 413", "Sun & Tue",  "12:00 PM", "01:30 PM", "C-502"),
    ("H 102",  "Thu",        "08:00 AM", "10:30 AM", "A-302"),
    # Term 5
    ("CS 301", "Sun & Tue",  "08:00 AM", "09:30 AM", "B-501"),
    ("CS 303", "Mon & Wed",  "08:00 AM", "09:30 AM", "C-601"),
    ("CS 304", "Sun & Tue",  "10:00 AM", "11:30 AM", "A-401"),
    ("CS 307", "Mon & Wed",  "10:00 AM", "11:30 AM", "B-502"),
    ("CS 312", "Sun & Tue",  "12:00 PM", "01:30 PM", "C-602"),
    ("CS 311", "Mon & Wed",  "12:00 PM", "01:30 PM", "A-402"),
    ("CS 313", "Thu",        "08:00 AM", "10:30 AM", "B-601"),
    # Term 6
    ("CS 305", "Sun & Tue",  "08:00 AM", "09:30 AM", "A-501"),
    ("CS 306", "Mon & Wed",  "08:00 AM", "09:30 AM", "B-601"),
    ("CS 308", "Sun & Tue",  "10:00 AM", "11:30 AM", "C-701"),
    ("CS 309", "Mon & Wed",  "10:00 AM", "11:30 AM", "A-502"),
    ("CS 404", "Sun & Tue",  "12:00 PM", "01:30 PM", "B-602"),
    ("CS 314", "Mon & Wed",  "12:00 PM", "01:30 PM", "C-702"),
    ("CS 315", "Thu",        "08:00 AM", "10:30 AM", "A-601"),
    ("CS 316", "Thu",        "10:30 AM", "01:00 PM", "A-602"),
    # Term 7
    ("BS 203", "Sun & Tue",  "08:00 AM", "09:30 AM", "B-701"),
    ("CS 401", "Mon & Wed",  "08:00 AM", "09:30 AM", "C-801"),
    ("H 201",  "Sun & Tue",  "10:00 AM", "11:30 AM", "A-701"),
    ("CS 402", "Mon & Wed",  "10:00 AM", "11:30 AM", "B-702"),
    ("CS 403", "Sun & Tue",  "12:00 PM", "01:30 PM", "C-802"),
    ("CS 405", "Mon & Wed",  "12:00 PM", "01:30 PM", "A-702"),
    ("CS 406", "Thu",        "08:00 AM", "10:30 AM", "B-801"),
    ("CS 407", "Thu",        "10:30 AM", "01:00 PM", "B-802"),
    ("CS 408", "Sun",        "02:00 PM", "04:30 PM", "C-901"),
    ("CS 410", "Tue",        "02:00 PM", "04:30 PM", "C-902"),
    ("CS 416", "Wed",        "12:00 PM", "02:30 PM", "A-801"),
    ("CS 498", "Thu",        "01:00 PM", "03:30 PM", "A-802"),
    # Term 8
    ("CS 302", "Sun & Tue",  "08:00 AM", "09:30 AM", "B-901"),
    ("CS 419", "Mon & Wed",  "08:00 AM", "09:30 AM", "C-1001"),
    ("CS 409", "Sun & Tue",  "10:00 AM", "11:30 AM", "A-901"),
    ("CS 411", "Mon & Wed",  "10:00 AM", "11:30 AM", "B-902"),
    ("CS 412", "Sun & Tue",  "12:00 PM", "01:30 PM", "C-1002"),
    ("CS 414", "Mon & Wed",  "12:00 PM", "01:30 PM", "A-902"),
    ("CS 415", "Thu",        "08:00 AM", "10:30 AM", "B-1001"),
    ("CS 417", "Thu",        "10:30 AM", "01:00 PM", "A-903"),
    ("CS 418", "Sun",        "02:00 PM", "04:30 PM", "C-1101"),
    ("CS 420", "Tue",        "02:00 PM", "04:30 PM", "C-1102"),
    ("CS 499", "Thu",        "01:00 PM", "03:30 PM", "A-1001"),
]

conn = sqlite3.connect('academic_advisor.db')
cur = conn.cursor()

# Create table if not exists (in case run before main.py auto-creates it)
cur.execute("""
CREATE TABLE IF NOT EXISTS course_schedules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code VARCHAR UNIQUE NOT NULL REFERENCES courses(code),
    days        VARCHAR NOT NULL,
    time_from   VARCHAR NOT NULL,
    time_to     VARCHAR NOT NULL,
    hall        VARCHAR
)
""")

inserted = 0
skipped = 0
for code, days, tf, tt, hall in SCHEDULES:
    cur.execute("SELECT 1 FROM courses WHERE code=?", (code,))
    if not cur.fetchone():
        skipped += 1
        continue
    cur.execute("""
        INSERT OR REPLACE INTO course_schedules (course_code, days, time_from, time_to, hall)
        VALUES (?,?,?,?,?)
    """, (code, days, tf, tt, hall))
    inserted += 1

conn.commit()
conn.close()
print(f"Done. Inserted/replaced: {inserted}, skipped (course not found): {skipped}")
