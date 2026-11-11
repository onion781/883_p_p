import streamlit as st
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "smartcampus.db"


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


st.title("Document Review Admin Panel")

conn = get_db_conn()
sql = '''
SELECT a.*, r.review_reasons, r.review_status, r.reviewed_at
FROM applications a
LEFT JOIN document_reviews r ON a.id = r.application_id
ORDER BY a.created_at DESC
'''
all_records = conn.execute(sql).fetchall()
conn.close()

doc_map_display = {
    "transcript": "Academic Transcript",
    "enrolment_certificate": "Enrolment Certificate",
    "degree_certificate": "Degree Certificate"
}

status_cn = {
    "submitted": "Submitted",
    "auto_approved": "Auto‑approved, pending manual review",
    "needs_review": "Pending manual review",
    "issued": "Document issued"
}


if not all_records:
    st.info("No application records available")
else:
    for item in all_records:
        st.markdown(f"""
> Reference ID：{item['reference']}
> Applicant：{item['applicant_name']} | Student ID：{item['student_ref']}
> Document：{doc_map_display[item['document_type']]}
> Delivery：{"Digital" if item["delivery_method"]=="digital" else "Printed"}
> Current Status：{status_cn[item['status']]}
> Auto‑check Note：{item['review_reasons'] or 'None'}
> Submitted Time：{item['created_at']}
""")

        new_status = st.radio(
            "Admin Operation",
            ["Keep current status", "needs_review (pending review)", "issued (issue document)"],
            key=f"rad_{item['id']}"
        )
        admin_note = st.text_input("Admin Review Note", key=f"note_{item['id']}")

        if st.button("Save Review Result", key=f"btn_{item['id']}"):
            final_st = item["status"]
            if new_status == "issued (issue document)":
                final_st = "issued"
            elif new_status == "needs_review (pending review)":
                final_st = "needs_review"

            conn2 = get_db_conn()
            conn2.execute('''
            UPDATE applications SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
            ''', (final_st, item["id"]))
            conn2.commit()
            conn2.close()
            st.success("Review result saved successfully!")
        st.divider()

