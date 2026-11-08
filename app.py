import streamlit as st

from core.database import init_db


st.set_page_config(
    page_title="SmartCampus",
    layout="wide",
)

init_db()

st.title("SmartCampus System")
st.caption("CSIT883 System Analysis and Project Management | Group G17")

st.write(
    "This system is oriented towards the GlobalConnect University."
    "including three subsystems: Learning Support, Facility Services, and Administrative Services."
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Learning Support")
    st.write("Academic Warning: Huang")
    st.write("Intelligent Q&A: Song")

with col2:
    st.subheader("Facility Services")
    st.write("Classroom Reservation: Yang")
    st.write("Fault Reporting & Maintenance: Yang")

with col3:
    st.subheader("Administrative Services")
    st.write("Unified Application Portal: Wang")
    st.write("Automated Material Review: Wang")

st.divider()

st.info("Please use the left navigation to access the six functional pages.")

