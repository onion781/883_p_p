import streamlit as st

from core.database import init_db


init_db()

st.title("故障报修与维护")
st.caption("设施服务系统 | 负责人：Yang")

st.info(
    "页面框架已建立。后续在此实现故障提交、"
    "编号生成和维护状态跟踪。"
)