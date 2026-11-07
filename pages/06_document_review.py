import streamlit as st

from core.database import init_db


init_db()

st.title("材料自动审核")
st.caption("行政服务系统 | 负责人：Wang")

st.info(
    "页面框架已建立。后续在此实现规则审核、"
    "人工复核分流和独立签发。"
)