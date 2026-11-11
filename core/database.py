from pathlib import Path
import sqlite3


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "smartcampus.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS academic_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_ref TEXT NOT NULL,
    attendance_rate REAL NOT NULL,
    avg_score REAL NOT NULL,
    submission_rate REAL NOT NULL,
    total_clicks INTEGER NOT NULL,
    active_days INTEGER NOT NULL,
    quiz_clicks INTEGER NOT NULL,
    model_probability REAL NOT NULL,
    attendance_penalty REAL NOT NULL DEFAULT 0,
    risk_score REAL NOT NULL,
    risk_band TEXT NOT NULL CHECK (
        risk_band IN ('low', 'medium', 'high')
    ),
    recommendation TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL DEFAULT 'fallback' CHECK (
        mode IN ('ai', 'fallback')
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    building TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    equipment TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    requester_name TEXT NOT NULL,
    requester_email TEXT NOT NULL,
    booking_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    purpose TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'confirmed' CHECK (
        status IN ('confirmed', 'cancelled')
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

CREATE TABLE IF NOT EXISTS fault_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT NOT NULL UNIQUE,
    reporter_name TEXT NOT NULL,
    location TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (
        priority IN ('low', 'medium', 'high')
    ),
    status TEXT NOT NULL DEFAULT 'submitted' CHECK (
        status IN ('submitted', 'in_progress', 'resolved')
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT NOT NULL UNIQUE,
    applicant_name TEXT NOT NULL,
    student_ref TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (
        document_type IN (
            'transcript',
            'enrolment_certificate',
            'degree_certificate'
        )
    ),
    delivery_method TEXT NOT NULL CHECK (
        delivery_method IN ('digital', 'printed')
    ),
    email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted' CHECK (
        status IN (
            'submitted',
            'auto_approved',
            'needs_review',
            'issued'
        )
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL UNIQUE,
    review_status TEXT NOT NULL CHECK (
        review_status IN ('auto_approved', 'needs_review')
    ),
    review_reasons TEXT NOT NULL,
    reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    issued_at TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

INSERT OR IGNORE INTO rooms
    (code, name, building, capacity, equipment)
VALUES
    ('A101', 'A101 Lecture Room', 'Building A', 60, 'Projector'),
    ('A102', 'A102 Seminar Room', 'Building A', 30, 'Display screen'),
    ('B201', 'B201 Computer Lab', 'Building B', 45, 'Computers'),
    ('B202', 'B202 Classroom', 'Building B', 50, 'Projector'),
    ('C301', 'C301 Meeting Room', 'Building C', 20, 'Video conference'),
    ('C302', 'C302 Lecture Room', 'Building C', 80, 'Projector');
"""


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = get_connection()
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
    print(f"Dastreamlit run app.pytabase initialized: {DB_PATH}")