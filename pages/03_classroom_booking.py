from datetime import time

import streamlit as st


st.title("Room Booking")
st.caption("Facilities Services | Maintainer: Yang")

bookings = st.session_state.setdefault("classroom_bookings", [])

ROOM_DETAILS = {
    "Classroom": (
        "Reserve a classroom for a study group, tutorial, or class activity.",
        "Class Activity",
        ("Group study", "Tutorial", "Class activity"),
    ),
    "Laboratory": (
        "Reserve a laboratory for practical work and indicate what equipment you need.",
        "Equipment Required",
        ("None", "Computers", "Lab instruments"),
    ),
    "Meeting Room": (
        "Reserve a meeting room for a discussion, interview, or presentation.",
        "Room Setup",
        ("Standard seating", "Presentation setup", "Video conference"),
    ),
}


def booking_period():
    booking_date = st.date_input("Booking Date")
    start_column, end_column = st.columns(2)
    start_time = start_column.time_input("Start Time", value=time(9))
    end_time = end_column.time_input("End Time", value=time(10))
    return booking_date, start_time, end_time


def overlaps(booking, booking_date, start_time, end_time):
    return (
        not booking["cancelled"]
        and booking["date"] == booking_date
        and start_time < booking["end"]
        and booking["start"] < end_time
    )


def show_booking(room_type):
    guidance, detail_label, detail_options = ROOM_DETAILS[room_type]
    st.info(guidance)
    rooms = [f"{room_type} {number}" for number in range(1, 6)]
    if room_type == "Classroom":
        if message := st.session_state.pop("classroom_booking_submitted", None):
            st.success(message)
        with st.container(border=True):
            st.subheader("Classroom Availability")
            st.caption("Choose a date and time to see which classrooms are free in this session.")
            booking_date, start_time, end_time = booking_period()
            if booking_date is None or end_time <= start_time:
                st.warning("Choose a date and an end time later than the start time.")
                rooms = []
            else:
                occupied = {
                    booking["classroom"] for booking in bookings
                    if overlaps(booking, booking_date, start_time, end_time)
                }
                for column, classroom in zip(st.columns(len(rooms)), rooms):
                    if classroom in occupied:
                        column.error(f"{classroom}\n\nBooked")
                    else:
                        column.success(f"{classroom}\n\nAvailable")
                        if column.button("Select", key=f"select_{classroom}"):
                            st.session_state.classroom_choice = classroom
                rooms = [classroom for classroom in rooms if classroom not in occupied]
                if st.session_state.get("classroom_choice") not in rooms:
                    st.session_state.pop("classroom_choice", None)
                if not rooms:
                    st.info("No classrooms are available for this time slot.")

    with st.form(f"booking_{room_type}"):
        st.subheader(f"{room_type} Booking Request")
        st.caption("All fields are required.")

        name = st.text_input("Student Name")
        student_id = st.text_input("Student ID")
        room = st.selectbox(
            room_type,
            rooms,
            index=None,
            placeholder=f"Select a {room_type.lower()}",
            key="classroom_choice" if room_type == "Classroom" else None,
        )
        if room_type != "Classroom":
            booking_date, start_time, end_time = booking_period()
        detail = st.selectbox(detail_label, detail_options)
        attendees = None
        if room_type == "Meeting Room":
            attendees = st.number_input("Number of Attendees", min_value=1, step=1)
        purpose = st.text_area("Booking Purpose")
        submitted = st.form_submit_button("Submit", type="primary")

    if submitted:
        student_ref = student_id.strip()
        if room is None or booking_date is None or not all(
            field.strip() for field in (name, student_id, purpose)
        ):
            st.error("Please complete all fields before submitting.")
        elif end_time <= start_time:
            st.error("End time must be later than start time.")
        elif any(
            booking["classroom"] == room
            and overlaps(booking, booking_date, start_time, end_time)
            for booking in bookings
        ):
            st.error("This room is already booked for part of that time.")
        elif any(
            booking.get("student_ref") == student_ref
            and overlaps(booking, booking_date, start_time, end_time)
            for booking in bookings
        ):
            st.error("This student ID already has a booking during that time.")
        else:
            bookings.append({
                "student_ref": student_ref,
                "classroom": room,
                "room_type": room_type,
                "date": booking_date,
                "start": start_time,
                "end": end_time,
                "purpose": purpose.strip(),
                "detail": detail,
                "attendees": attendees,
                "cancelled": False,
            })
            message = (
                f"Booked {room} on {booking_date:%Y-%m-%d}, "
                f"{start_time:%H:%M} to {end_time:%H:%M}. Open My Bookings to view or cancel."
            )
            if room_type == "Classroom":
                st.session_state.classroom_booking_submitted = message
                st.rerun()
            st.success(message)

def show_bookings():
    st.subheader("My Bookings")
    st.caption("Bookings are available in this session only.")
    status_filter = st.selectbox("Booking Status", ["All", "Active", "Cancelled"])
    visible_bookings = [
        (index, booking)
        for index, booking in reversed(list(enumerate(bookings)))
        if status_filter == "All"
        or booking["cancelled"] == (status_filter == "Cancelled")
    ]
    if not visible_bookings:
        st.info("No bookings match this status.")

    for index, booking in visible_bookings:
        st.write(
            f'**{booking["classroom"]}** · {booking["date"]:%Y-%m-%d} · '
            f'{booking["start"]:%H:%M}–{booking["end"]:%H:%M}'
        )
        st.caption("Cancelled" if booking["cancelled"] else "Active")
        st.text(booking["purpose"])
        if booking.get("attendees"):
            st.text(f'Attendees: {booking["attendees"]}')
        if "detail" in booking:
            detail_label = ROOM_DETAILS[booking["room_type"]][1]
            st.text(f'{detail_label}: {booking["detail"]}')
        if booking["cancelled"]:
            continue
        if st.session_state.get("classroom_cancel_index") == index:
            st.warning("Cancel this booking?")
            confirm, keep = st.columns(2)
            if confirm.button("Confirm Cancellation", key=f"confirm_booking_{index}"):
                booking["cancelled"] = True
                del st.session_state.classroom_cancel_index
                st.rerun()
            if keep.button("Keep Booking", key=f"keep_booking_{index}"):
                del st.session_state.classroom_cancel_index
                st.rerun()
        elif st.button("Cancel Booking", key=f"cancel_booking_{index}"):
            st.session_state.classroom_cancel_index = index
            st.rerun()


room_types = ("Classroom", "Laboratory", "Meeting Room")
tabs = st.tabs([f"{room_type} Booking" for room_type in room_types] + ["My Bookings"])
for tab, room_type in zip(tabs[:-1], room_types):
    with tab:
        show_booking(room_type)

with tabs[-1]:
    show_bookings()
