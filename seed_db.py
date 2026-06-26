# text/x-python (seed_db.py)
from database import SessionLocal, engine
import models
models.Base.metadata.create_all(bind=engine)


ELECTIVE_COURSES_CODES = {
    "CS 311", "CS 313", "CS 314", "CS 315", "CS 316",
    "CS 405", "CS 406", "CS 407", "CS 408", "CS 410", "CS 416",
    "CS 411", "CS 412", "CS 414", "CS 415", "CS 417", "CS 418", "CS 420"
}

COURSES = [
    # --- مقررات السنة الأولى ---
    {"code":"H 101",  "name":"English",                            "hours":2,"year":1,"term":1,"prereq":None,      "doctor_uid":"doctor_omaima"},
    {"code":"BS 104", "name":"Electronics",                        "hours":3,"year":1,"term":1,"prereq":None,      "doctor_uid":"doctor_ashraf"},
    {"code":"CS 102", "name":"Computer Programming",               "hours":3,"year":1,"term":1,"prereq":None,      "doctor_uid":"doctor_amira"},
    {"code":"CS 101", "name":"Intro To Computer Science",          "hours":3,"year":1,"term":1,"prereq":None,      "doctor_uid":"doctor_omaima"},
    {"code":"IS 105", "name":"Intro To Information System",        "hours":3,"year":1,"term":1,"prereq":None,      "doctor_uid":"doctor_ashraf"},
    {"code":"BS 101", "name":"Calculus",                           "hours":3,"year":1,"term":1,"prereq":None,      "doctor_uid":"doctor_amira"},

    {"code":"H 203",  "name":"Technical Report Writing",           "hours":2,"year":1,"term":2,"prereq":"H 101",   "doctor_uid":"doctor_omaima"},
    {"code":"CS 104", "name":"Intro To Software Engineering",      "hours":3,"year":1,"term":2,"prereq":"CS 102",  "doctor_uid":"doctor_ashraf"},
    {"code":"BS 103", "name":"Probability and Statistics",         "hours":3,"year":1,"term":2,"prereq":"BS 101",  "doctor_uid":"doctor_amira"},
    {"code":"H 202",  "name":"Human Rights",                       "hours":2,"year":1,"term":2,"prereq":None,      "doctor_uid":"doctor_omaima"},
    {"code":"CS 103", "name":"Object-Oriented Programming",        "hours":3,"year":1,"term":2,"prereq":"CS 102",  "doctor_uid":"doctor_ashraf"},
    {"code":"H 103",  "name":"Creative Thinking and Communication","hours":2,"year":1,"term":2,"prereq":None,      "doctor_uid":"doctor_amira"},
    {"code":"BS 102", "name":"Discrete Mathematics",               "hours":3,"year":1,"term":2,"prereq":"BS 101",  "doctor_uid":"doctor_omaima"},

    # --- مقررات السنة الثانية ---
    {"code":"IS 207", "name":"Web Technology",                     "hours":3,"year":2,"term":3,"prereq":"CS 103",  "doctor_uid":"doctor_ashraf"},
    {"code":"IS 206", "name":"Intro To Database",                  "hours":3,"year":2,"term":3,"prereq":"IS 105",  "doctor_uid":"doctor_amira"},
    {"code":"CS 202", "name":"Computer Architecture",              "hours":3,"year":2,"term":3,"prereq":"BS 104",  "doctor_uid":"doctor_omaima"},
    {"code":"BS 202", "name":"Operations Research",                "hours":3,"year":2,"term":3,"prereq":"BS 101",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 201", "name":"Data Structures",                    "hours":3,"year":2,"term":3,"prereq":"CS 103",  "doctor_uid":"doctor_amira"},
    {"code":"BS 201", "name":"Linear Algebra",                     "hours":3,"year":2,"term":3,"prereq":"BS 101",  "doctor_uid":"doctor_omaima"},

    {"code":"CS 203", "name":"Algorithms Analysis and Design",     "hours":3,"year":2,"term":4,"prereq":"CS 201",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 204", "name":"Operating Systems",                  "hours":3,"year":2,"term":4,"prereq":"CS 202",  "doctor_uid":"doctor_amira"},
    {"code":"CS 205", "name":"Computer Networks Technology",       "hours":3,"year":2,"term":4,"prereq":"CS 202",  "doctor_uid":"doctor_omaima"},
    {"code":"CS 310", "name":"Selected Topics in Computer Science - Level 3","hours":3,"year":2,"term":4,"prereq":None,"doctor_uid":"doctor_ashraf"},
    {"code":"CS 413", "name":"Human Computer Interaction",         "hours":3,"year":2,"term":4,"prereq":None,      "doctor_uid":"doctor_amira"},
    {"code":"H 102",  "name":"Ethics and Professionalism",         "hours":2,"year":2,"term":4,"prereq":None,      "doctor_uid":"doctor_omaima"},

    # --- مقررات السنة الثالثة ---
    {"code":"CS 301", "name":"Theory of Programming Languages",    "hours":3,"year":3,"term":5,"prereq":None,      "doctor_uid":"doctor_ashraf"},
    {"code":"CS 303", "name":"Advanced Operating System",          "hours":3,"year":3,"term":5,"prereq":None,      "doctor_uid":"doctor_amira"},
    {"code":"CS 304", "name":"Advanced Software Engineering",      "hours":3,"year":3,"term":5,"prereq":None,      "doctor_uid":"doctor_omaima"},
    {"code":"CS 307", "name":"Computer Graphics",                  "hours":3,"year":3,"term":5,"prereq":"CS 310",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 312", "name":"Logic Programming",                  "hours":3,"year":3,"term":5,"prereq":None,      "doctor_uid":"doctor_amira"},
    {"code":"CS 311", "name":"Dynamic Languages",                  "hours":3,"year":3,"term":5,"prereq":"IS 207",  "doctor_uid":"doctor_omaima"},
    {"code":"CS 313", "name":"Cloud Computing",                    "hours":3,"year":3,"term":5,"prereq":"CS 303",  "doctor_uid":"doctor_amira"},

    {"code":"CS 305", "name":"Advanced Computer Networks",         "hours":3,"year":3,"term":6,"prereq":"CS 205",  "doctor_uid":"doctor_omaima"},
    {"code":"CS 306", "name":"Theory & Design of Compilers",       "hours":3,"year":3,"term":6,"prereq":None,      "doctor_uid":"doctor_ashraf"},
    {"code":"CS 308", "name":"Digital Image Processing",           "hours":3,"year":3,"term":6,"prereq":"CS 307",  "doctor_uid":"doctor_amira"},
    {"code":"CS 309", "name":"Microprocessor and Assembly Language","hours":3,"year":3,"term":6,"prereq":"CS 202",  "doctor_uid":"doctor_omaima"},
    {"code":"CS 404", "name":"Distributed Computing",              "hours":3,"year":3,"term":6,"prereq":"CS 303",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 314", "name":"Digital Signal Processing",          "hours":3,"year":3,"term":6,"prereq":"CS 203",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 315", "name":"Mobile App Development",             "hours":3,"year":3,"term":6,"prereq":"IS 207",  "doctor_uid":"doctor_amira"},
    {"code":"CS 316", "name":"Modeling and Simulation",            "hours":3,"year":3,"term":6,"prereq":"CS 203",  "doctor_uid":"doctor_omaima"},

    # --- مقررات السنة الرابعة ---
    {"code":"BS 203", "name":"Differential Equations",             "hours":3,"year":4,"term":7,"prereq":"BS 101",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 401", "name":"Artificial Intelligence",            "hours":3,"year":4,"term":7,"prereq":"CS 203",  "doctor_uid":"doctor_amira"},
    {"code":"H 201",  "name":"Quality Assurance & Control",        "hours":3,"year":4,"term":7,"prereq":None,      "doctor_uid":"doctor_omaima"},
    {"code":"CS 402", "name":"Information and Computer Networks Security","hours":3,"year":4,"term":7,"prereq":"CS 305","doctor_uid":"doctor_ashraf"},
    {"code":"CS 403", "name":"Machine Learning",                   "hours":3,"year":4,"term":7,"prereq":"BS 103",  "doctor_uid":"doctor_amira"},
    {"code":"CS 405", "name":"Selected Topics in computer science - level 4","hours":3,"year":4,"term":7,"prereq":None,"doctor_uid":"doctor_omaima"},
    {"code":"CS 406", "name":"Big Data Analysis",                  "hours":3,"year":4,"term":7,"prereq":"IS 206",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 407", "name":"Computer Arabization",               "hours":3,"year":4,"term":7,"prereq":"CS 203",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 408", "name":"Virtual Reality",                    "hours":3,"year":4,"term":7,"prereq":"CS 203",  "doctor_uid":"doctor_amira"},
    {"code":"CS 410", "name":"Internet of Things (IoT)",           "hours":3,"year":4,"term":7,"prereq":"CS 305",  "doctor_uid":"doctor_omaima"},
    {"code":"CS 416", "name":"Knowledge Discovery",                "hours":3,"year":4,"term":7,"prereq":"IS 206",  "doctor_uid":"doctor_amira"},
    {"code":"CS 498", "name":"Graduation Project 1",               "hours":3,"year":4,"term":7,"prereq":None,      "doctor_uid":"doctor_amira"},

    {"code":"CS 302", "name":"Parallel Programming",               "hours":3,"year":4,"term":8,"prereq":"CS 203",  "doctor_uid":"doctor_omaima"},
    {"code":"CS 419", "name":"Deep Learning",                      "hours":3,"year":4,"term":8,"prereq":"CS 403",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 409", "name":"Computer Vision Systems",            "hours":3,"year":4,"term":8,"prereq":"CS 308",  "doctor_uid":"doctor_amira"},
    {"code":"CS 411", "name":"Software Testing and Quality Assurance","hours":3,"year":4,"term":8,"prereq":"CS 304","doctor_uid":"doctor_ashraf"},
    {"code":"CS 412", "name":"Cyber Security",                     "hours":3,"year":4,"term":8,"prereq":"CS 402",  "doctor_uid":"doctor_amira"},
    {"code":"CS 414", "name":"Natural Language Processing",        "hours":3,"year":4,"term":8,"prereq":"CS 403",  "doctor_uid":"doctor_omaima"},
    {"code":"CS 415", "name":"Soft Computing",                     "hours":3,"year":4,"term":8,"prereq":"BS 103",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 417", "name":"Pattern Recognition",                "hours":3,"year":4,"term":8,"prereq":"CS 308",  "doctor_uid":"doctor_omaima"},
    {"code":"CS 418", "name":"Game Programming",                   "hours":3,"year":4,"term":8,"prereq":"CS 307",  "doctor_uid":"doctor_ashraf"},
    {"code":"CS 420", "name":"Data Communications",                "hours":3,"year":4,"term":8,"prereq":"CS 305",  "doctor_uid":"doctor_amira"},
    {"code":"CS 499", "name":"Graduation Project 2",               "hours":3,"year":4,"term":8,"prereq":"CS 498",  "doctor_uid":"doctor_omaima"},
]

STUDENTS = [
    {"firebase_uid":"220423", "name":"Yasser Mohamed",  "gpa":3.90,"current_year":2,"current_term":1,"password":"Yasser@220423",  "role":"student","warnings":0,"is_suspended":"active"},
    {"firebase_uid":"221798", "name":"Osama Mohamed",   "gpa":1.60,"current_year":2,"current_term":2,"password":"Osama@221798",   "role":"student","warnings":2,"is_suspended":"active"},
    {"firebase_uid":"223012", "name":"Mohanad Taha",    "gpa":2.60,"current_year":3,"current_term":2,"password":"Mohanad@223012", "role":"student","warnings":0,"is_suspended":"active"},
    {"firebase_uid":"222072", "name":"Moaz Ashraf",     "gpa":2.1, "current_year":2,"current_term":2,"password":"Moaz@222072",    "role":"student","warnings":0,"is_suspended":"active"},
    {"firebase_uid":"221730", "name":"Nadeem Tarek",    "gpa":2.40,"current_year":3,"current_term":1,"password":"Nadeem@221730",  "role":"student","warnings":0,"is_suspended":"active"},
    {"firebase_uid":"221037", "name":"Basmalah Hany",   "gpa":3.20,"current_year":3,"current_term":1,"password":"Basmalah@221037","role":"student","warnings":0,"is_suspended":"active"},
    {"firebase_uid":"221737", "name":"Manar Hafez",     "gpa":2.90,"current_year":4,"current_term":2,"password":"Manar@221737",   "role":"student","warnings":0,"is_suspended":"active"},

    {"firebase_uid":"doctor_omaima","name":"Dr. Omaima Goher","gpa":4.0,"current_year":4,"current_term":2,"password":"doc",  "role":"doctor","warnings":0,"is_suspended":"active"},
    {"firebase_uid":"doctor_ashraf",  "name":"Dr. Ashraf","gpa":4.0,"current_year":4,"current_term":2,"password":"doc",  "role":"doctor","warnings":0,"is_suspended":"active"},
    {"firebase_uid":"doctor_amira",   "name":"Dr. Amira","gpa":4.0,"current_year":4,"current_term":2,"password":"doc",  "role":"doctor","warnings":0,"is_suspended":"active"},

    {"firebase_uid":"admin_nadem", "name":"Admin Nadem", "gpa":4.0,"current_year":4,"current_term":2,"password":"admin","role":"admin","warnings":0,"is_suspended":"active"},
    {"firebase_uid":"admin_yasser","name":"Admin Yasser","gpa":4.0,"current_year":4,"current_term":2,"password":"admin","role":"admin","warnings":0,"is_suspended":"active"},
]

STUDENTS_HISTORY = {

    "220423": {
        "الترم الأول (السنة الأولى)": [
            {"code": "H 101",  "grade": "A+", "status": "passed"},
            {"code": "BS 104", "grade": "A",  "status": "passed"},
            {"code": "CS 102", "grade": "A+", "status": "passed"},
            {"code": "CS 101", "grade": "A",  "status": "passed"},
            {"code": "IS 105", "grade": "A+", "status": "passed"},
            {"code": "BS 101", "grade": "A-", "status": "passed"},
        ],
        "الترم الثاني (السنة الأولى)": [
            {"code": "H 203",  "grade": "A",  "status": "passed"},
            {"code": "CS 104", "grade": "A+", "status": "passed"},
            {"code": "BS 103", "grade": "A",  "status": "passed"},
            {"code": "H 202",  "grade": "B+", "status": "passed"},
            {"code": "CS 103", "grade": "A",  "status": "passed"},
            {"code": "H 103",  "grade": "A",  "status": "passed"},
            {"code": "BS 102", "grade": "A+", "status": "passed"},
        ],
    },


    "221798": {
        "الترم الأول (السنة الأولى)": [
            {"code": "H 101",  "grade": "C",  "status": "passed"},
            {"code": "BS 104", "grade": "C",  "status": "passed"},
            {"code": "CS 102", "grade": "D+", "status": "passed"},
            {"code": "CS 101", "grade": "C",  "status": "passed"},
            {"code": "IS 105", "grade": "C",  "status": "passed"},
            {"code": "BS 101", "grade": "D",  "status": "passed"},
        ],
        "الترم الثاني (السنة الأولى)": [
            {"code": "H 203",  "grade": "C",  "status": "passed"},
            {"code": "CS 104", "grade": "D",  "status": "passed"},
            {"code": "BS 103", "grade": "D",  "status": "passed"},
            {"code": "H 202",  "grade": "C",  "status": "passed"},
            {"code": "CS 103", "grade": "D",  "status": "passed"},
            {"code": "H 103",  "grade": "C",  "status": "passed"},
            {"code": "BS 102", "grade": "F",  "status": "failed"},
        ],
        "الترم الثالث (السنة الثانية)": [
            {"code": "IS 207", "grade": "D+", "status": "passed"},
            {"code": "IS 206", "grade": "D",  "status": "passed"},
            {"code": "CS 202", "grade": "F",  "status": "failed"},
            {"code": "BS 202", "grade": "D",  "status": "passed"},
            {"code": "CS 201", "grade": "F",  "status": "failed"},
            {"code": "BS 201", "grade": "C-", "status": "passed"},
        ],
    },


    "221737": {
        "الترم الأول (السنة الأولى)": [
            {"code": "H 101",  "grade": "B+", "status": "passed"},
            {"code": "BS 104", "grade": "A",  "status": "passed"},
            {"code": "CS 102", "grade": "B",  "status": "passed"},
            {"code": "CS 101", "grade": "B+", "status": "passed"},
            {"code": "IS 105", "grade": "A-", "status": "passed"},
            {"code": "BS 101", "grade": "B+", "status": "passed"},
        ],
        "الترم الثاني (السنة الأولى)": [
            {"code": "H 203",  "grade": "A",  "status": "passed"},
            {"code": "CS 104", "grade": "B+", "status": "passed"},
            {"code": "BS 103", "grade": "B",  "status": "passed"},
            {"code": "H 202",  "grade": "A",  "status": "passed"},
            {"code": "CS 103", "grade": "B",  "status": "passed"},
            {"code": "H 103",  "grade": "B+", "status": "passed"},
            {"code": "BS 102", "grade": "A-", "status": "passed"},
        ],
        "الترم الثالث (السنة الثانية)": [
            {"code": "IS 207", "grade": "B+", "status": "passed"},
            {"code": "IS 206", "grade": "A-", "status": "passed"},
            {"code": "CS 202", "grade": "B",  "status": "passed"},
            {"code": "BS 202", "grade": "B+", "status": "passed"},
            {"code": "CS 201", "grade": "B",  "status": "passed"},
            {"code": "BS 201", "grade": "B+", "status": "passed"},
        ],
        "الترم الرابع (السنة الثانية)": [
            {"code": "CS 203", "grade": "A",  "status": "passed"},
            {"code": "CS 204", "grade": "B+", "status": "passed"},
            {"code": "CS 205", "grade": "B",  "status": "passed"},
            {"code": "CS 310", "grade": "A-", "status": "passed"},
            {"code": "CS 413", "grade": "B+", "status": "passed"},
            {"code": "H 102",  "grade": "A",  "status": "passed"},
        ],
        "الترم الخامس (السنة الثالثة)": [
            {"code": "CS 301", "grade": "B",  "status": "passed"},
            {"code": "CS 303", "grade": "B+", "status": "passed"},
            {"code": "CS 304", "grade": "A-", "status": "passed"},
            {"code": "CS 307", "grade": "B",  "status": "passed"},
            {"code": "CS 312", "grade": "B+", "status": "passed"},
            {"code": "CS 311", "grade": "B+", "status": "passed"},
        ],
        "الترم السادس (السنة الثالثة)": [
            {"code": "CS 305", "grade": "A-", "status": "passed"},
            {"code": "CS 306", "grade": "B",  "status": "passed"},
            {"code": "CS 308", "grade": "B+", "status": "passed"},
            {"code": "CS 309", "grade": "A",  "status": "passed"},
            {"code": "CS 404", "grade": "B+", "status": "passed"},
            {"code": "CS 315", "grade": "A-", "status": "passed"},
        ],
        "الترم السابع (السنة الرابعة)": [
            {"code": "BS 203", "grade": "B",  "status": "passed"},
            {"code": "CS 401", "grade": "B+", "status": "passed"},
            {"code": "H 201",  "grade": "A-", "status": "passed"},
            {"code": "CS 402", "grade": "A",  "status": "passed"},
            {"code": "CS 403", "grade": "B+", "status": "passed"},
            {"code": "CS 498", "grade": "A",  "status": "passed"},
        ],
    },


    "221730": {
        "الترم الأول (السنة الأولى)": [
            {"code": "H 101",  "grade": "B",  "status": "passed"},
            {"code": "BS 104", "grade": "B+", "status": "passed"},
            {"code": "CS 102", "grade": "B",  "status": "passed"},
            {"code": "CS 101", "grade": "C+", "status": "passed"},
            {"code": "IS 105", "grade": "B",  "status": "passed"},
            {"code": "BS 101", "grade": "B",  "status": "passed"},
        ],
        "الترم الثاني (السنة الأولى)": [
            {"code": "H 203",  "grade": "B+", "status": "passed"},
            {"code": "CS 104", "grade": "B",  "status": "passed"},
            {"code": "BS 103", "grade": "C",  "status": "passed"},
            {"code": "H 202",  "grade": "B",  "status": "passed"},
            {"code": "CS 103", "grade": "C+", "status": "passed"},
            {"code": "H 103",  "grade": "B",  "status": "passed"},
            {"code": "BS 102", "grade": "B",  "status": "passed"},
        ],
        "الترم الثالث (السنة الثانية)": [
            {"code": "IS 207", "grade": "C+", "status": "passed"},
            {"code": "IS 206", "grade": "B-", "status": "passed"},
            {"code": "CS 202", "grade": "C",  "status": "passed"},
            {"code": "BS 202", "grade": "B",  "status": "passed"},
            {"code": "CS 201", "grade": "C+", "status": "passed"},
            {"code": "BS 201", "grade": "B",  "status": "passed"},
        ],
        "الترم الرابع (السنة الثانية)": [
            {"code": "CS 203", "grade": "F",  "status": "failed"},
            {"code": "CS 204", "grade": "C",  "status": "passed"},
            {"code": "CS 205", "grade": "B",  "status": "passed"},
            {"code": "CS 310", "grade": "B+", "status": "passed"},
            {"code": "CS 413", "grade": "B",  "status": "passed"},
            {"code": "H 102",  "grade": "F",  "status": "failed"},
        ],
    },

    "223012": {
        "الترم الأول (السنة الأولى)": [
            {"code": "H 101",  "grade": "B+", "status": "passed"},
            {"code": "BS 104", "grade": "B",  "status": "passed"},
            {"code": "CS 102", "grade": "B",  "status": "passed"},
            {"code": "CS 101", "grade": "B+", "status": "passed"},
            {"code": "IS 105", "grade": "B",  "status": "passed"},
            {"code": "BS 101", "grade": "B",  "status": "passed"},
        ],
        "الترم الثاني (السنة الأولى)": [
            {"code": "CS 104", "grade": "B",  "status": "passed"},
            {"code": "BS 103", "grade": "C+", "status": "passed"},
            {"code": "CS 103", "grade": "B",  "status": "passed"},
            {"code": "H 103",  "grade": "B+", "status": "passed"},
            {"code": "BS 102", "grade": "B",  "status": "passed"},
        ],
        "الترم الثالث (السنة الثانية)": [
            {"code": "IS 207", "grade": "B",  "status": "passed"},
            {"code": "IS 206", "grade": "B+", "status": "passed"},
            {"code": "CS 202", "grade": "B",  "status": "passed"},
            {"code": "BS 202", "grade": "C+", "status": "passed"},
            {"code": "CS 201", "grade": "B",  "status": "passed"},
            {"code": "BS 201", "grade": "B",  "status": "passed"},
        ],
        "الترم الرابع (السنة الثانية)": [
            {"code": "CS 203", "grade": "B+", "status": "passed"},
            {"code": "CS 204", "grade": "B",  "status": "passed"},
            {"code": "CS 205", "grade": "B",  "status": "passed"},
            {"code": "CS 310", "grade": "A-", "status": "passed"},
            {"code": "CS 413", "grade": "B+", "status": "passed"},
            {"code": "H 102",  "grade": "C+", "status": "passed"},
        ],
        "الترم الخامس (السنة الثالثة)": [
            {"code": "CS 301", "grade": "C+", "status": "passed"},
            {"code": "CS 303", "grade": "B",  "status": "passed"},
            {"code": "CS 304", "grade": "B+", "status": "passed"},
            {"code": "CS 307", "grade": "A-", "status": "passed"},
            {"code": "CS 312", "grade": "C",  "status": "passed"},
            {"code": "CS 311", "grade": "B",  "status": "passed"},
        ],
    },

    "221037": {
        "الترم الأول (السنة الأولى)": [
            {"code": "H 101",  "grade": "A-", "status": "passed"},
            {"code": "BS 104", "grade": "B+", "status": "passed"},
            {"code": "CS 102", "grade": "A",  "status": "passed"},
            {"code": "CS 101", "grade": "B",  "status": "passed"},
            {"code": "IS 105", "grade": "B+", "status": "passed"},
            {"code": "BS 101", "grade": "A-", "status": "passed"},
        ],
        "الترم الثاني (السنة الأولى)": [
            {"code": "H 203",  "grade": "B+", "status": "passed"},
            {"code": "CS 104", "grade": "A",  "status": "passed"},
            {"code": "BS 103", "grade": "B",  "status": "passed"},
            {"code": "H 202",  "grade": "A-", "status": "passed"},
            {"code": "CS 103", "grade": "B+", "status": "passed"},
            {"code": "H 103",  "grade": "A",  "status": "passed"},
            {"code": "BS 102", "grade": "B",  "status": "passed"},
        ],
        "الترم الثالث (السنة الثانية)": [
            {"code": "IS 207", "grade": "A",  "status": "passed"},
            {"code": "IS 206", "grade": "B+", "status": "passed"},
            {"code": "CS 202", "grade": "B",  "status": "passed"},
            {"code": "BS 202", "grade": "B+", "status": "passed"},
            {"code": "CS 201", "grade": "A-", "status": "passed"},
            {"code": "BS 201", "grade": "B+", "status": "passed"},
        ],
        "الترم الرابع (السنة الثانية)": [
            {"code": "CS 203", "grade": "B+", "status": "passed"},
            {"code": "CS 204", "grade": "A-", "status": "passed"},
            {"code": "CS 205", "grade": "A",  "status": "passed"},
            {"code": "CS 310", "grade": "B",  "status": "passed"},
            {"code": "CS 413", "grade": "B+", "status": "passed"},
            {"code": "H 102",  "grade": "A-", "status": "passed"},
        ],
    },


    "222072": {
        "الترم الأول (السنة الأولى)": [
            {"code": "H 101",  "grade": "B",  "status": "passed"},
            {"code": "BS 104", "grade": "B+", "status": "passed"},
            {"code": "CS 102", "grade": "C+", "status": "passed"},
            {"code": "CS 101", "grade": "B",  "status": "passed"},
            {"code": "IS 105", "grade": "B",  "status": "passed"},
            {"code": "BS 101", "grade": "C+", "status": "passed"},
        ],
        "الترم الثاني (السنة الأولى)": [
            {"code": "H 203",  "grade": "B",  "status": "passed"},
            {"code": "CS 104", "grade": "C+", "status": "passed"},
            {"code": "BS 103", "grade": "C",  "status": "passed"},
            {"code": "H 202",  "grade": "B+", "status": "passed"},
            {"code": "CS 103", "grade": "C+", "status": "passed"},
            {"code": "H 103",  "grade": "B",  "status": "passed"},
            {"code": "BS 102", "grade": "C",  "status": "passed"},
        ],
        "الترم الثالث (السنة الثانية)": [
            {"code": "IS 207", "grade": "C+", "status": "passed"},
            {"code": "IS 206", "grade": "B",  "status": "passed"},
            {"code": "CS 202", "grade": "C",  "status": "passed"},
            {"code": "BS 202", "grade": "C+", "status": "passed"},
            {"code": "CS 201", "grade": "C",  "status": "passed"},
            {"code": "BS 201", "grade": "C+", "status": "passed"},
        ],
    },
}


def seed():
    db = SessionLocal()
    try:

        course_map = {c["code"]: c for c in COURSES}
        inserted_codes = set()

        def insert_course(code):
            if code in inserted_codes:
                return
            c = course_map[code]
            
            if c["prereq"] and c["prereq"] not in inserted_codes:
                insert_course(c["prereq"])
            
            if code not in inserted_codes:

                is_elective = c["code"] in ELECTIVE_COURSES_CODES

                db.add(models.Course(
                    code              = c["code"],
                    name              = c["name"],
                    credit_hours      = c["hours"],
                    target_year       = c["year"],
                    target_term       = c["term"],
                    prerequisite_code = c["prereq"],
                    doctor_uid        = c.get("doctor_uid"),
                    is_elective       = is_elective 
                ))
                inserted_codes.add(code)

        for c in COURSES:
            insert_course(c["code"])
        db.commit()
        print(f"✓ {len(COURSES)} courses inserted with elective information")

        student_objs = {}
        for s in STUDENTS:
            obj = models.Student(
                firebase_uid = s["firebase_uid"],
                name         = s["name"],
                gpa          = s["gpa"],
                current_year = s["current_year"],
                current_term = s["current_term"],
                password     = s["password"],
                role         = s["role"],
                warnings     = s["warnings"],
                is_suspended = s["is_suspended"],
            )
            db.add(obj)
            db.flush()
            student_objs[s["firebase_uid"]] = obj
        db.commit()
        print(f"✓ {len(STUDENTS)} users inserted")

        history_count = 0
        for uid, terms in STUDENTS_HISTORY.items():
            if uid not in student_objs:
                continue
            student_id = student_objs[uid].id
            for term_name, courses_in_term in terms.items():
                for c_info in courses_in_term:
                    db.add(models.StudentHistory(
                        student_id  = student_id,
                        course_code = c_info["code"],
                        status      = c_info["status"],
                        grade       = c_info.get("grade"),
                    ))
                    history_count += 1

        db.commit()
        print(f"✓ {history_count} history records inserted")
        print("\n✅ Seed completed successfully!\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
