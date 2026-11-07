import streamlit as st

from core.database import init_db


init_db()

st.title("统一材料申请")
st.caption("行政服务系统 | 负责人：Wang")

st.info(
    "页面框架已建立。后续在此实现成绩单、"
    "在读证明和学位证明申请。"
)