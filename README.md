# 🏫 Smart Classroom

A simple digital classroom management system built as a hackathon prototype.
It brings attendance, timetable, assignments, notes, quizzes, and an
anonymous doubt-solving system into one lightweight app — **no external AI
API required**, everything runs fully offline using rule-based logic.

---

## ✨ Features

### 👨‍🎓 Student
- **Dashboard** — attendance %, pending assignments, quizzes attempted
- **Attendance** — view subject-wise attendance %
- **Timetable** — view weekly class schedule
- **Assignments** — view deadlines with auto-calculated priority (🔴/🟠/🟢), mark as completed
- **Smart Study Planner** — rule-based planner that ranks pending assignments by urgency and suggests how much time to give each
- **Today's Notes** — view topic briefings posted by the teacher before class
- **Quiz** — attempt quizzes published by the teacher, get instant score
- **Ask a Doubt (Anonymous)** — ask a doubt without revealing identity, browse a community wall of answered doubts

### 👩‍🏫 Teacher
- **Dashboard** — assignment count, attendance records, quizzes created, pending doubts
- **Mark Attendance** — record attendance against a specific registered student
- **Timetable / Manage Timetable** — view and add classes
- **Manage Assignments** — create assignments with deadlines
- **AI Notes Summary** — enter today's topic, get an instant structured briefing (template-based generator), publish it for students
- **Create Quiz** — pick questions from a predefined question bank per subject and publish
- **Quiz Analytics** — see how many students attempted a quiz, average/highest score, and each student's individual score
- **Doubt Box** — view pending doubts (student identity hidden), get a keyword-based suggested answer, edit and send a reply

---

## 🧠 "Smart" Logic — How It Works (No External AI API)

Everything labeled "smart" or "AI" in this app is **rule-based Python logic**,
not a call to an LLM/AI service. This keeps the prototype fully offline,
free, and instantly demoable:

| Feature | How it works |
|---|---|
| Assignment priority | Deadline vs. today's date → High/Medium/Low |
| Smart Study Planner | Days-left buckets → urgency label + suggestion |
| AI Notes Summary | Fixed template filled in with subject/topic |
| Quiz | Predefined question bank (dictionary), no dynamic generation |
| Doubt suggestions | Keyword match against a predefined answer bank |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| UI / Frontend | [Streamlit](https://streamlit.io/) |
| Database | SQLite3 (built-in, file-based — `smart_classroom.db`) |
| Auth / Security | `hashlib` (SHA-256 password hashing) |
| Date/Time | Python `datetime` module |
| "AI" logic | Pure Python (dictionaries, conditionals) — no external API |

No paid services, no API keys, no internet connection needed to run it.

---

## 🚀 Getting Started

### 1. Install dependencies
```bash
pip install streamlit
```

### 2. Run the app
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.
A `smart_classroom.db` SQLite file will be auto-created in the same folder
on first run.

### 3. Demo Login Credentials

Predefined accounts are auto-seeded on first run — no signup needed:

| Role | Email | Password |
|---|---|---|
| Student | `student@demo.com` | `student123` |
| Teacher | `teacher@demo.com` | `teacher123` |

You can also sign up new accounts from the Signup tab.

---

## 🗄️ Database Schema (SQLite)

- `users` — id, name, email, password (hashed), role
- `attendance` — student_id, subject, total_classes, attended
- `timetable` — day, subject, teacher, room, time
- `assignments` — title, subject, deadline, description, completed
- `notes` — subject, topic, content, teacher_name, created_at
- `quizzes` — subject, title, teacher_name, created_at, active
- `quiz_questions` — quiz_id, question, option_a–d, correct_index
- `quiz_attempts` — quiz_id, student_id, student_name, score, total, submitted_at
- `doubts` — subject, question, answer, answered, created_at

---

## 📌 Known Limitations (Prototype Scope)

- Assignments are shared across all students (not per-student tracked)
- Single SQLite file — not built for concurrent multi-user production load
- Notes/Quiz "AI" content is template/bank-based, not generative

---

## 📄 License

Hackathon prototype — free to use, modify, and extend.
https://smartclassroom-ejwshepq7lnw2xrur7h5df.streamlit.app/
