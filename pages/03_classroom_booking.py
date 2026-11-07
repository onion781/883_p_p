import streamlit as st

from core.database import init_db


init_db()

st.title("教室预约")
st.caption("设施服务系统 | 负责人：Yang")

st.info(
    "页面框架已建立。后续在此实现教室查询、"
    "时间冲突检查、预约和取消。"
)