import streamlit as st
import sqlite3
from datetime import date, datetime
import hashlib
import json

# =========================================================
# DATABASE
# =========================================================

DB = "smart_classroom.db"


def connect():
    return sqlite3.connect(DB, check_same_thread=False)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_tables():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            total_classes INTEGER DEFAULT 0,
            attended INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS timetable(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            subject TEXT,
            teacher TEXT,
            room TEXT,
            time TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subject TEXT,
            deadline TEXT,
            description TEXT,
            completed INTEGER DEFAULT 0
        )
    """)

    # ---- NEW TABLES ----

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            topic TEXT,
            content TEXT,
            teacher_name TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quizzes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            title TEXT,
            teacher_name TEXT,
            created_at TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_index INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            student_name TEXT,
            score INTEGER,
            total INTEGER,
            submitted_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doubts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            question TEXT,
            answer TEXT,
            answered INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def seed_demo_accounts():
    """Predefined student/teacher accounts so the hackathon demo
    can be shown instantly without needing signup."""
    conn = connect()
    cur = conn.cursor()

    demo_users = [
        ("Demo Student", "student@demo.com", "student123", "Student"),
        ("Demo Teacher", "teacher@demo.com", "teacher123", "Teacher"),
    ]

    for name, email, pwd, role in demo_users:
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                (name, email, hash_password(pwd), role)
            )

    conn.commit()
    conn.close()


create_tables()
seed_demo_accounts()


# =========================================================
# AUTHENTICATION
# =========================================================

def signup(name, email, password, role):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            (name, email, hash_password(password), role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def login(email, password):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id,name,email,role FROM users WHERE email=? AND password=?",
        (email, hash_password(password))
    )
    result = cur.fetchone()
    conn.close()
    return result


def get_all_students():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id,name FROM users WHERE role='Student' ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows


# =========================================================
# SMART / RULE-BASED LOGIC (no external AI API used anywhere)
# =========================================================

def calculate_priority(deadline, subject):
    today = date.today()
    due = datetime.strptime(deadline, "%Y-%m-%d").date()
    days = (due - today).days

    if days <= 1:
        return "🔴 HIGH"
    elif days <= 3:
        return "🟠 MEDIUM"
    else:
        return "🟢 LOW"


def smart_study_plan(assignments):
    """Rule-based intelligent planner. No API or external AI required."""
    today = date.today()
    plan = []

    for task in assignments:
        deadline = datetime.strptime(task[2], "%Y-%m-%d").date()
        days_left = (deadline - today).days

        if days_left <= 0:
            priority = "URGENT"
            suggestion = "Complete this task today."
        elif days_left <= 2:
            priority = "HIGH"
            suggestion = "Give this task the highest study priority."
        elif days_left <= 5:
            priority = "MEDIUM"
            suggestion = "Work on this task for 30-45 minutes today."
        else:
            priority = "LOW"
            suggestion = "Start early and divide the task into smaller parts."

        plan.append({
            "title": task[0],
            "subject": task[1],
            "priority": priority,
            "suggestion": suggestion
        })

    return plan


def generate_ai_notes(subject, topic):
    """
    Template-based 'smart briefing' generator.
    Purely offline/rule-based - no external AI API call.
    Produces a structured note for the topic a teacher is about to teach.
    """
    content = f"""
### 📌 Topic: {topic}
**Subject:** {subject}

**1. Introduction**
Today's session introduces *{topic}*. Students should focus on understanding
the core idea before jumping into examples.

**2. Key Points to Cover**
- Definition and basic explanation of {topic}
- Why {topic} is important in {subject}
- Common mistakes students make with {topic}
- A real-life or practical example related to {topic}

**3. Suggested Activity**
Give students 1-2 quick questions on {topic} at the end of class to check
understanding on the spot.

**4. Quick Recap**
Summarize {topic} in one line before ending the session and connect it to
what will be taught next class.
"""
    return content.strip()


# Predefined quiz question bank (used by teacher while creating a quiz)
QUIZ_BANK = {
    "Math": [
        {"q": "What is the value of pi (approx)?", "options": ["3.14", "2.71", "1.41", "1.61"], "answer": 0},
        {"q": "What is 7 x 8?", "options": ["54", "56", "58", "64"], "answer": 1},
        {"q": "Square root of 144 is?", "options": ["10", "11", "12", "14"], "answer": 2},
        {"q": "What is the sum of angles in a triangle?", "options": ["90°", "180°", "270°", "360°"], "answer": 1},
    ],
    "Science": [
        {"q": "What is the chemical symbol for water?", "options": ["H2O", "O2", "CO2", "NaCl"], "answer": 0},
        {"q": "Which organ pumps blood in the human body?", "options": ["Lungs", "Brain", "Heart", "Liver"], "answer": 2},
        {"q": "Photosynthesis occurs in which part of a plant?", "options": ["Root", "Stem", "Leaf", "Flower"], "answer": 2},
        {"q": "What gas do humans exhale the most?", "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"], "answer": 1},
    ],
    "Computer Science": [
        {"q": "What does CPU stand for?", "options": ["Central Process Unit", "Central Processing Unit", "Computer Personal Unit", "Central Processor Utility"], "answer": 1},
        {"q": "Which data structure uses FIFO?", "options": ["Stack", "Queue", "Tree", "Graph"], "answer": 1},
        {"q": "HTML is used for?", "options": ["Styling", "Structure of web pages", "Database", "Networking"], "answer": 1},
        {"q": "Which of these is a programming language?", "options": ["HTTP", "Python", "HTML", "CSS"], "answer": 1},
    ],
    "English": [
        {"q": "Identify the noun: 'The dog barked loudly.'", "options": ["dog", "barked", "loudly", "the"], "answer": 0},
        {"q": "What is a synonym for 'happy'?", "options": ["Sad", "Joyful", "Angry", "Tired"], "answer": 1},
        {"q": "Which is a verb: 'She runs every morning.'", "options": ["She", "runs", "every", "morning"], "answer": 1},
        {"q": "Antonym of 'ancient' is?", "options": ["Old", "Modern", "Historic", "Vintage"], "answer": 1},
    ],
}


# Predefined keyword-based canned answers to help the teacher answer doubts
# quickly. This is a rule-based suggestion helper, not a real AI model.
DOUBT_SUGGESTIONS = {
    "recursion": "Recursion is when a function calls itself with a smaller version of the problem, until it hits a base case that stops it.",
    "pointer": "A pointer stores the memory address of another variable instead of a value directly.",
    "photosynthesis": "Photosynthesis is the process plants use to convert sunlight, water and CO2 into glucose and oxygen.",
    "integration": "Integration is the reverse of differentiation - it helps find the area under a curve.",
    "derivative": "A derivative measures how a function's output changes as its input changes - i.e. its rate of change.",
    "default": "That's a good question! Let's go over this together in the next class with an example."
}


def suggest_doubt_answer(question_text):
    q = question_text.lower()
    for keyword, answer in DOUBT_SUGGESTIONS.items():
        if keyword != "default" and keyword in q:
            return answer
    return DOUBT_SUGGESTIONS["default"]


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Smart Classroom",
    page_icon="🏫",
    layout="wide"
)


# =========================================================
# LOGIN / SIGNUP
# =========================================================

if not st.session_state.logged_in:

    st.title("🏫 Smart Classroom")
    st.write("### A simple digital classroom management system")

    st.info(
        "**Demo Logins (Hackathon Prototype)**\n\n"
        "👨‍🎓 Student → `student@demo.com` / `student123`\n\n"
        "👩‍🏫 Teacher → `teacher@demo.com` / `teacher123`"
    )

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Signup"])

    with tab1:
        st.subheader("Login")

        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True):
            if not email or not password:
                st.warning("Please enter email and password.")
            else:
                user = login(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with tab2:
        st.subheader("Create Account")

        name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        role = st.selectbox("Choose Role", ["Student", "Teacher"])

        if st.button("Create Account", use_container_width=True):
            if not name or not email or not password:
                st.warning("Please fill all fields.")
            elif signup(name, email, password, role):
                st.success("Account created! Now login.")
            else:
                st.error("This email already exists.")


# =========================================================
# MAIN APPLICATION
# =========================================================

else:

    user = st.session_state.user
    user_id = user[0]
    name = user[1]
    role = user[3]

    st.sidebar.title("🏫 Smart Classroom")
    st.sidebar.success(f"Welcome, {name}")
    st.sidebar.write(f"Role: **{role}**")

    if role == "Student":
        menu = st.sidebar.radio(
            "Navigation",
            [
                "Dashboard",
                "Attendance",
                "Timetable",
                "Assignments",
                "Smart Study Planner",
                "Today's Notes",
                "Quiz",
                "Ask a Doubt",
            ]
        )
    else:
        menu = st.sidebar.radio(
            "Navigation",
            [
                "Dashboard",
                "Mark Attendance",
                "Timetable",
                "Manage Timetable",
                "Manage Assignments",
                "AI Notes Summary",
                "Create Quiz",
                "Quiz Analytics",
                "Doubt Box",
            ]
        )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    # =====================================================
    # DASHBOARD (role-aware, single branch - bug fixed)
    # =====================================================

    if menu == "Dashboard":

        if role == "Student":
            st.title("🎓 Student Dashboard")

            conn = connect()
            cur = conn.cursor()

            cur.execute(
                "SELECT SUM(total_classes), SUM(attended) FROM attendance WHERE student_id=?",
                (user_id,)
            )
            attendance = cur.fetchone()

            cur.execute("SELECT COUNT(*) FROM assignments WHERE completed=0")
            pending = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM quiz_attempts WHERE student_id=?", (user_id,))
            quizzes_taken = cur.fetchone()[0]

            conn.close()

            total = attendance[0] or 0
            attended = attendance[1] or 0
            percentage = round((attended / total) * 100, 1) if total else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Attendance", f"{percentage}%")
            col2.metric("📝 Pending Assignments", pending)
            col3.metric("🧾 Quizzes Attempted", quizzes_taken)

            st.divider()
            st.subheader("✨ Smart Classroom")
            st.info(
                "Use the Smart Study Planner to automatically prioritize your "
                "assignments, check Today's Notes before class, and try the Quiz "
                "section once your teacher publishes one."
            )

        else:
            st.title("👩‍🏫 Teacher Dashboard")

            conn = connect()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM assignments")
            assignments_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM attendance")
            attendance_records = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM quizzes")
            quiz_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM doubts WHERE answered=0")
            pending_doubts = cur.fetchone()[0]

            conn.close()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📝 Assignments", assignments_count)
            col2.metric("📊 Attendance Records", attendance_records)
            col3.metric("🧠 Quizzes Created", quiz_count)
            col4.metric("🙋 Pending Doubts", pending_doubts)

            st.info(
                "Use the sidebar to mark attendance, manage the timetable, "
                "post AI-style notes before class, create quizzes and check "
                "student analytics."
            )

    # =====================================================
    # TIMETABLE (view - both roles)
    # =====================================================

    elif menu == "Timetable":
        st.title("📅 Timetable")

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT day,subject,teacher,room,time FROM timetable ORDER BY id")
        rows = cur.fetchall()
        conn.close()

        if rows:
            for row in rows:
                day, subject, teacher, room, time = row
                with st.container(border=True):
                    st.write(f"### {subject}")
                    st.write(f"📅 {day}   ⏰ {time}")
                    st.write(f"👩‍🏫 Teacher: {teacher}")
                    st.write(f"🚪 Room: {room}")
        else:
            st.info("Timetable is empty.")

    # =====================================================
    # TEACHER: MANAGE TIMETABLE (add classes) - was dead code before
    # =====================================================

    elif menu == "Manage Timetable":
        st.title("📅 Manage Timetable")

        day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        subject = st.text_input("Subject")
        teacher = st.text_input("Teacher", value=name)
        room = st.text_input("Room")
        time = st.text_input("Time")

        if st.button("Add Class"):
            if subject and teacher and room and time:
                conn = connect()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO timetable(day,subject,teacher,room,time) VALUES(?,?,?,?,?)",
                    (day, subject, teacher, room, time)
                )
                conn.commit()
                conn.close()
                st.success("Class added!")
                st.rerun()
            else:
                st.warning("Fill all fields.")

    # =====================================================
    # ASSIGNMENTS (student view)
    # =====================================================

    elif menu == "Assignments":
        st.title("📝 Assignments")

        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT id,title,subject,deadline,description,completed
            FROM assignments ORDER BY deadline
        """)
        rows = cur.fetchall()
        conn.close()

        if rows:
            for row in rows:
                assignment_id, title, subject, deadline, description, completed = row
                priority = calculate_priority(deadline, subject)

                with st.container(border=True):
                    st.subheader(title)
                    st.write(f"📚 Subject: {subject}")
                    st.write(f"📅 Deadline: {deadline}")
                    st.write(f"🎯 Priority: {priority}")

                    if description:
                        st.write(description)

                    if completed:
                        st.success("✅ Completed")
                    else:
                        if st.button("Mark as Completed", key=f"complete_{assignment_id}"):
                            conn = connect()
                            cur = conn.cursor()
                            cur.execute("UPDATE assignments SET completed=1 WHERE id=?", (assignment_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()
        else:
            st.info("No assignments available.")

    # =====================================================
    # SMART STUDY PLANNER
    # =====================================================

    elif menu == "Smart Study Planner":
        st.title("🧠 Smart Study Planner")
        st.write("This intelligent planner automatically analyzes assignment deadlines and suggests priorities.")

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT title,subject,deadline FROM assignments WHERE completed=0 ORDER BY deadline")
        assignments = cur.fetchall()
        conn.close()

        if assignments:
            plan = smart_study_plan(assignments)
            for item in plan:
                with st.container(border=True):
                    st.subheader(item["title"])
                    st.write(f"📚 **Subject:** {item['subject']}")
                    st.write(f"🎯 **Priority:** {item['priority']}")
                    st.info(f"💡 {item['suggestion']}")
        else:
            st.success("🎉 No pending assignments! You're all caught up.")

    # =====================================================
    # STUDENT: TODAY'S NOTES (view what teacher posted)
    # =====================================================

    elif menu == "Today's Notes":
        st.title("📖 Today's Notes")

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT subject,topic,content,teacher_name,created_at FROM notes ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        if rows:
            for subject, topic, content, teacher_name, created_at in rows:
                with st.container(border=True):
                    st.subheader(f"{subject} — {topic}")
                    st.caption(f"Posted by {teacher_name} on {created_at}")
                    st.markdown(content)
        else:
            st.info("No notes have been posted yet.")

    # =====================================================
    # TEACHER: AI NOTES SUMMARY (template based, offline)
    # =====================================================

    elif menu == "AI Notes Summary":
        st.title("🧠 AI Notes Summary")
        st.write(
            "Enter today's topic and instantly generate a structured briefing "
            "for students. (Rule-based generator — works fully offline, no AI API used.)"
        )

        subject = st.text_input("Subject")
        topic = st.text_input("Topic to be taught today")

        if st.button("Generate Notes"):
            if subject and topic:
                st.session_state["generated_note"] = generate_ai_notes(subject, topic)
            else:
                st.warning("Please enter both subject and topic.")

        if "generated_note" in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state["generated_note"])

            if st.button("📤 Publish to Students"):
                conn = connect()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO notes(subject,topic,content,teacher_name,created_at) VALUES(?,?,?,?,?)",
                    (subject, topic, st.session_state["generated_note"], name,
                     datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                conn.close()
                del st.session_state["generated_note"]
                st.success("Notes published to students!")
                st.rerun()

    # =====================================================
    # TEACHER: CREATE QUIZ (predefined question bank)
    # =====================================================

    elif menu == "Create Quiz":
        st.title("📝 Create Quiz")

        subject = st.selectbox("Subject", list(QUIZ_BANK.keys()))
        title = st.text_input("Quiz Title", value=f"{subject} Quiz")

        st.write("Select questions to include from the predefined bank:")

        bank = QUIZ_BANK[subject]
        selected = []

        for i, item in enumerate(bank):
            if st.checkbox(item["q"], key=f"qbank_{subject}_{i}", value=True):
                selected.append(item)

        if st.button("Publish Quiz"):
            if not selected:
                st.warning("Select at least one question.")
            else:
                conn = connect()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO quizzes(subject,title,teacher_name,created_at,active) VALUES(?,?,?,?,1)",
                    (subject, title, name, datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                quiz_id = cur.lastrowid

                for item in selected:
                    opts = item["options"]
                    cur.execute("""
                        INSERT INTO quiz_questions
                        (quiz_id,question,option_a,option_b,option_c,option_d,correct_index)
                        VALUES(?,?,?,?,?,?,?)
                    """, (quiz_id, item["q"], opts[0], opts[1], opts[2], opts[3], item["answer"]))

                conn.commit()
                conn.close()
                st.success(f"Quiz '{title}' published with {len(selected)} questions!")
                st.rerun()

    # =====================================================
    # STUDENT: TAKE QUIZ
    # =====================================================

    elif menu == "Quiz":
        st.title("🧾 Quiz")

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id,subject,title FROM quizzes WHERE active=1 ORDER BY id DESC")
        quizzes = cur.fetchall()

        cur.execute("SELECT quiz_id FROM quiz_attempts WHERE student_id=?", (user_id,))
        attempted_ids = {row[0] for row in cur.fetchall()}
        conn.close()

        if not quizzes:
            st.info("No quizzes available right now.")
        else:
            options_map = {f"{q[2]} ({q[1]})": q[0] for q in quizzes}
            choice = st.selectbox("Select a quiz", list(options_map.keys()))
            quiz_id = options_map[choice]

            if quiz_id in attempted_ids:
                st.success("✅ You have already attempted this quiz.")

                conn = connect()
                cur = conn.cursor()
                cur.execute(
                    "SELECT score,total,submitted_at FROM quiz_attempts WHERE quiz_id=? AND student_id=?",
                    (quiz_id, user_id)
                )
                result = cur.fetchone()
                conn.close()

                if result:
                    st.write(f"Your Score: **{result[0]} / {result[1]}** (submitted {result[2]})")
            else:
                conn = connect()
                cur = conn.cursor()
                cur.execute("""
                    SELECT id,question,option_a,option_b,option_c,option_d
                    FROM quiz_questions WHERE quiz_id=?
                """, (quiz_id,))
                questions = cur.fetchall()
                conn.close()

                answers = {}
                for q_id, question, a, b, c, d in questions:
                    st.write(f"**{question}**")
                    answers[q_id] = st.radio(
                        "Choose one:", [a, b, c, d],
                        key=f"quiz_{quiz_id}_{q_id}",
                        label_visibility="collapsed"
                    )
                    st.write("")

                if st.button("Submit Quiz"):
                    conn = connect()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT id,option_a,option_b,option_c,option_d,correct_index
                        FROM quiz_questions WHERE quiz_id=?
                    """, (quiz_id,))
                    q_rows = cur.fetchall()

                    score = 0
                    for q_id, a, b, c, d, correct_index in q_rows:
                        options = [a, b, c, d]
                        if answers.get(q_id) == options[correct_index]:
                            score += 1

                    cur.execute("""
                        INSERT INTO quiz_attempts(quiz_id,student_id,student_name,score,total,submitted_at)
                        VALUES(?,?,?,?,?,?)
                    """, (quiz_id, user_id, name, score, len(q_rows), datetime.now().strftime("%Y-%m-%d %H:%M")))

                    conn.commit()
                    conn.close()

                    st.success(f"Quiz submitted! Your score: {score} / {len(q_rows)}")
                    st.rerun()

    # =====================================================
    # TEACHER: QUIZ ANALYTICS
    # =====================================================

    elif menu == "Quiz Analytics":
        st.title("📊 Quiz Analytics")

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id,subject,title FROM quizzes ORDER BY id DESC")
        quizzes = cur.fetchall()
        conn.close()

        if not quizzes:
            st.info("No quizzes created yet.")
        else:
            options_map = {f"{q[2]} ({q[1]})": q[0] for q in quizzes}
            choice = st.selectbox("Select a quiz", list(options_map.keys()))
            quiz_id = options_map[choice]

            conn = connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT student_name,score,total,submitted_at FROM quiz_attempts WHERE quiz_id=? ORDER BY score DESC",
                (quiz_id,)
            )
            attempts = cur.fetchall()
            conn.close()

            if attempts:
                total_attempts = len(attempts)
                avg_score = sum(a[1] for a in attempts) / total_attempts
                max_total = attempts[0][2]

                col1, col2, col3 = st.columns(3)
                col1.metric("👥 Students Attempted", total_attempts)
                col2.metric("📈 Average Score", f"{round(avg_score, 1)} / {max_total}")
                col3.metric("🏆 Highest Score", f"{max(a[1] for a in attempts)} / {max_total}")

                st.divider()
                st.subheader("Individual Results")

                for student_name, score, total, submitted_at in attempts:
                    with st.container(border=True):
                        st.write(f"**{student_name}** — {score}/{total}")
                        st.caption(f"Submitted: {submitted_at}")
            else:
                st.info("No students have attempted this quiz yet.")

    # =====================================================
    # STUDENT: ASK A DOUBT (anonymous)
    # =====================================================

    elif menu == "Ask a Doubt":
        st.title("🙈 Ask a Doubt (Anonymous)")
        st.write("Your identity is never shown to the teacher. Ask freely!")

        subject = st.text_input("Subject")
        question = st.text_area("Your doubt")

        if st.button("Submit Doubt"):
            if subject and question:
                conn = connect()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO doubts(subject,question,answer,answered,created_at) VALUES(?,?,?,0,?)",
                    (subject, question, "", datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                conn.close()
                st.success("Your doubt has been submitted anonymously!")
                st.rerun()
            else:
                st.warning("Please fill subject and doubt.")

        st.divider()
        st.subheader("📚 Answered Doubts (Community Wall)")

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT subject,question,answer FROM doubts WHERE answered=1 ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        if rows:
            for subject, question, answer in rows:
                with st.container(border=True):
                    st.write(f"**[{subject}]** {question}")
                    st.info(f"💬 {answer}")
        else:
            st.info("No answered doubts yet.")

    # =====================================================
    # TEACHER: DOUBT BOX (anonymous - no student identity shown)
    # =====================================================

    elif menu == "Doubt Box":
        st.title("🙋 Doubt Box")
        st.write("Student identity is hidden — you only see the question.")

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id,subject,question,created_at FROM doubts WHERE answered=0 ORDER BY id")
        pending = cur.fetchall()
        conn.close()

        if not pending:
            st.info("No pending doubts. 🎉")
        else:
            for doubt_id, subject, question, created_at in pending:
                with st.container(border=True):
                    st.write(f"**[{subject}]** {question}")
                    st.caption(f"Asked anonymously on {created_at}")

                    suggestion_key = f"suggestion_{doubt_id}"
                    answer_key = f"answer_{doubt_id}"

                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("💡 Get Suggestion", key=f"sugg_btn_{doubt_id}"):
                            st.session_state[suggestion_key] = suggest_doubt_answer(question)

                    default_text = st.session_state.get(suggestion_key, "")

                    answer_text = st.text_area(
                        "Your reply", value=default_text, key=answer_key
                    )

                    if st.button("Send Reply", key=f"send_{doubt_id}"):
                        if answer_text.strip():
                            conn = connect()
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE doubts SET answer=?, answered=1 WHERE id=?",
                                (answer_text.strip(), doubt_id)
                            )
                            conn.commit()
                            conn.close()
                            st.success("Reply sent!")
                            st.rerun()
                        else:
                            st.warning("Write a reply before sending.")

        st.divider()
        st.subheader("✅ Already Answered")

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT subject,question,answer FROM doubts WHERE answered=1 ORDER BY id DESC")
        answered = cur.fetchall()
        conn.close()

        if answered:
            for subject, question, answer in answered:
                with st.container(border=True):
                    st.write(f"**[{subject}]** {question}")
                    st.write(f"💬 {answer}")
        else:
            st.caption("Nothing answered yet.")

    # =====================================================
    # TEACHER: MARK ATTENDANCE (now tied to an actual student)
    # =====================================================

    elif menu == "Mark Attendance":
        st.title("📊 Mark Attendance")

        students = get_all_students()

        if not students:
            st.warning("No students registered yet.")
        else:
            student_map = {s[1]: s[0] for s in students}
            student_choice = st.selectbox("Student", list(student_map.keys()))
            subject = st.text_input("Subject")

            total = st.number_input("Total Classes", min_value=1, step=1)
            attended = st.number_input("Classes Attended", min_value=0, max_value=int(total), step=1)

            if st.button("Save Attendance"):
                if not subject:
                    st.warning("Enter subject name.")
                else:
                    conn = connect()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO attendance(student_id,subject,total_classes,attended) VALUES(?,?,?,?)",
                        (student_map[student_choice], subject, total, attended)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Attendance saved successfully!")

    # =====================================================
    # STUDENT: ATTENDANCE (view own records)
    # =====================================================

    elif menu == "Attendance":
        st.title("📊 My Attendance")

        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT subject,total_classes,attended FROM attendance WHERE student_id=?",
            (user_id,)
        )
        rows = cur.fetchall()
        conn.close()

        if rows:
            for subject, total_classes, attended in rows:
                pct = round((attended / total_classes) * 100, 1) if total_classes else 0
                with st.container(border=True):
                    st.write(f"### {subject}")
                    st.progress(min(pct / 100, 1.0))
                    st.write(f"{attended} / {total_classes} classes ({pct}%)")
        else:
            st.info("No attendance records yet.")

    # =====================================================
    # TEACHER: MANAGE ASSIGNMENTS
    # =====================================================

    elif menu == "Manage Assignments":
        st.title("📝 Manage Assignments")

        title = st.text_input("Assignment Title")
        subject = st.text_input("Subject")
        deadline = st.date_input("Deadline", min_value=date.today())
        description = st.text_area("Description")

        if st.button("Add Assignment"):
            if title and subject:
                conn = connect()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO assignments(title,subject,deadline,description) VALUES(?,?,?,?)",
                    (title, subject, deadline.strftime("%Y-%m-%d"), description)
                )
                conn.commit()
                conn.close()
                st.success("Assignment added successfully!")
            else:
                st.warning("Please enter title and subject.")


# ---------------- FOOTER ----------------

st.sidebar.markdown("---")
st.sidebar.caption("Smart Classroom • Hackathon Project")