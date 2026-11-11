import streamlit as st
import sqlite3
from pathlib import Path
import uuid

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "smartcampus.db"


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def auto_check(document_type, applicant_name, email):
    errors = []
    allow_docs = ["transcript", "enrolment_certificate", "degree_certificate"]
    if document_type not in allow_docs:
        errors.append("Invalid document type")
    if len(applicant_name.strip()) < 2:
        errors.append("Applicant name cannot be empty")
    if "@" not in email:
        errors.append("Email format is invalid")

    if len(errors) == 0:
        return True, "Auto‑check passed, waiting for administrator review"
    else:
        return False, "; ".join(errors)


st.title("Unified Document Application")
st.subheader("Administrative Service Module")

student_ref = st.session_state.get("student_ref", "stu_001")

st.markdown("### 📝 Create New Application")

doc_map_display = {
    "transcript": "Academic Transcript",
    "enrolment_certificate": "Enrolment Certificate",
    "degree_certificate": "Degree Certificate"
}
show_list = list(doc_map_display.values())
select_show = st.selectbox("Select Document Type", show_list)
reverse_map = {v: k for k, v in doc_map_display.items()}
document_type = reverse_map[select_show]

delivery_method = st.radio("Delivery Method", ["digital", "printed"],
                           format_func=lambda x: "Digital" if x == "digital" else "Printed")
applicant_name = st.text_input("Applicant Name", value="Demo Student")
email = st.text_input("Contact Email", value="demo@university.edu")


if st.button("Submit Application"):
    ok, msg = auto_check(document_type, applicant_name, email)
    ref_id = f"APP-{uuid.uuid4().hex[:8].upper()}"

    conn = get_db_conn()
    if ok:
        app_status = "auto_approved"
        cur = conn.execute('''
        INSERT INTO applications
        (reference,applicant_name,student_ref,document_type,delivery_method,email,status)
        VALUES (?,?,?,?,?,?,?)
        ''', (ref_id, applicant_name, student_ref, document_type, delivery_method, email, app_status))
        app_id = cur.lastrowid
        conn.execute('''
        INSERT INTO document_reviews (application_id,review_status,review_reasons)
        VALUES (?,?,?)
        ''', (app_id, "auto_approved", msg))
        conn.commit()
        st.success(f"{msg}. Application Reference: {ref_id}")
    else:
        app_status = "needs_review"
        cur = conn.execute('''
        INSERT INTO applications
        (reference,applicant_name,student_ref,document_type,delivery_method,email,status)
        VALUES (?,?,?,?,?,?,?)
        ''', (ref_id, applicant_name, student_ref, document_type, delivery_method, email, app_status))
        app_id = cur.lastrowid
        conn.execute('''
        INSERT INTO document_reviews (application_id,review_status,review_reasons)
        VALUES (?,?,?)
        ''', (app_id, "needs_review", msg))
        conn.commit()
        st.error(f"Auto‑check failed: {msg}. Manual administrator review required. Application Reference: {ref_id}")
    conn.close()


st.divider()
st.markdown("### 📋 My Application Records")

conn = get_db_conn()
rows = conn.execute("SELECT * FROM applications WHERE student_ref=? ORDER BY created_at DESC", (student_ref,)).fetchall()
conn.close()

status_cn = {
    "submitted": "Submitted",
    "auto_approved": "Auto‑approved, pending manual review",
    "needs_review": "Pending manual review",
    "issued": "Document issued"
}

if not rows:
    st.info("No application records found")
else:
    for r in rows:
        st.write(f"**Reference ID**: {r['reference']}")
        st.write(f"Document Type: {doc_map_display[r['document_type']]}")
        st.write(f"Delivery: {'Digital' if r['delivery_method']=='digital' else 'Printed'}")
        st.write(f"Status: {status_cn[r['status']]}")
        st.write(f"Submitted At: {r['created_at']}")
        st.divider()

