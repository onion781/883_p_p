import streamlit as st

from core.database import init_db


init_db()

st.title("校园智能问答")
st.caption("学习支持系统 | 负责人：Song")

st.info(
    "页面框架已建立。后续在此实现校园知识检索、"
    "智能问答、来源展示和对话记录。"
)