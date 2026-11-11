from datetime import datetime, timedelta, timezone

import streamlit as st


FAULT_TYPES = {
    "Electrical": ["Power outage", "Broken outlet", "Lighting fault", "Damaged light cover"],
    "Air Conditioning": ["Not cooling or heating", "Water leak", "Unusual noise"],
    "Water and Plumbing": ["Water dispenser fault", "No hot water", "Blocked drain", "Leaking fixture"],
    "Doors and Windows": ["Broken lock", "Damaged door", "Damaged window"],
    "Walls, Floors and Ceilings": ["Crack or damage", "Water seepage"],
    "Furniture": ["Broken desk or chair", "Damaged cabinet or bed"],
    "Other": ["Other maintenance issue"],
}

st.title("Fault Reporting and Maintenance")
st.caption("Facilities Services | Maintainer: Yang")

reports = st.session_state.setdefault("fault_reports", [])
new_report, my_reports = st.tabs(["Report a Fault", "My Reports"])

with new_report:
    st.info("Tell us where the fault is and what needs repair.")

    with st.container(border=True):
        st.subheader("Fault Type")
        category_column, issue_column = st.columns([1, 2])
        category = category_column.radio("Category", list(FAULT_TYPES))
        issue = issue_column.radio("Specific Issue", FAULT_TYPES[category], horizontal=True)

    with st.form("fault_report", clear_on_submit=False):
        st.subheader("Location")
        campus = st.text_input("Campus / Area", placeholder="e.g. Main Campus")
        location = st.text_input("Building, Floor and Room", placeholder="e.g. Residence Hall 3, Floor 7, Room 715")

        st.subheader("Contact Details")
        name_column, id_column = st.columns(2)
        name = name_column.text_input("Student Name")
        student_id = id_column.text_input("Student ID")
        contact = st.text_input("Phone or Email")

        st.subheader("Fault Details")
        description = st.text_area(
            "Fault Description",
            placeholder="Describe what happened so maintenance staff can prepare.",
        )
        photo = st.file_uploader("Fault Photo (Optional)", type=["jpg", "jpeg", "png"])
        st.caption("All fields except the photo are required.")
        submitted = st.form_submit_button("Submit Report", type="primary", use_container_width=True)

    if submitted:
        if all(value.strip() for value in (campus, location, name, student_id, contact, description)):
            reports.append({
                "campus": campus.strip(),
                "location": location.strip(),
                "name": name.strip(),
                "student_id": student_id.strip(),
                "contact": contact.strip(),
                "category": category,
                "issue": issue,
                "description": description.strip(),
                "photo": photo.getvalue() if photo else None,
                "photo_name": photo.name if photo else None,
                "status": "Submitted",
                "submitted_at": datetime.now(timezone(timedelta(hours=8))),
            })
            st.success(f"Report FR-{len(reports):03d} submitted successfully. See My Reports for details.")
        else:
            st.error("Please complete all required fields before submitting.")

with my_reports:
    st.caption("Reports are available in this session only.")
    if not reports:
        st.info("You have no fault reports yet.")

    for index in reversed(range(len(reports))):
        report = reports[index]
        with st.expander(
            f'FR-{index + 1:03d} | {report["issue"]} | {report["location"]} | {report["status"]}'
        ):
            if submitted_at := report.get("submitted_at"):
                st.caption(f"Submitted {submitted_at:%Y-%m-%d %H:%M} (UTC+8)")
            st.text(f'Category: {report["category"]}')
            st.text(f'Location: {report["campus"]}, {report["location"]}')
            st.text(f'Student: {report["name"]} ({report["student_id"]})')
            st.text(f'Contact: {report["contact"]}')
            st.write("**Fault Description**")
            st.text(report["description"])
            if report["photo"]:
                try:
                    st.image(report["photo"], caption=report["photo_name"], width=240)
                except (OSError, ValueError):
                    st.caption("Photo preview unavailable.")
                st.download_button(
                    "Download Fault Photo",
                    report["photo"],
                    file_name=report["photo_name"],
                    key=f"fault_photo_{index}",
                )

            if report["status"] == "Cancelled":
                continue
            if st.session_state.get("fault_cancel_index") == index:
                st.warning("Cancel this fault report?")
                confirm, keep = st.columns(2)
                if confirm.button("Confirm Cancellation", key=f"fault_confirm_{index}"):
                    report["status"] = "Cancelled"
                    del st.session_state.fault_cancel_index
                    st.rerun()
                if keep.button("Keep Report", key=f"fault_keep_{index}"):
                    del st.session_state.fault_cancel_index
                    st.rerun()
            elif st.button("Cancel Report", key=f"fault_cancel_{index}"):
                st.session_state.fault_cancel_index = index
                st.rerun()
