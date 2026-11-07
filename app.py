import streamlit as st

from core.database import init_db


st.set_page_config(
    page_title="SmartCampus",
    layout="wide",
)

init_db()

st.title("SmartCampus 智慧校园服务系统")
st.caption("CSIT883 System Analysis and Project Management | Group G17")

st.write(
    "本系统面向 GlobalConnect University 原型场景，"
    "包括学习支持、设施服务和行政服务三个子系统。"
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("学习支持")
    st.write("学业预警：Huang")
    st.write("智能问答：Song")

with col2:
    st.subheader("设施服务")
    st.write("教室预约：Yang")
    st.write("故障报修与维护：Yang")

with col3:
    st.subheader("行政服务")
    st.write("统一申请门户：Wang")
    st.write("材料自动审核：Wang")

st.divider()

st.info("请通过左侧导航进入六个功能页面。")

st.warning(
    "当前为课程演示原型。校园业务记录均为演示数据，"
    "学业预警结果仅用于辅助人工复核。"
)