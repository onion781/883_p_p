import streamlit as st

from core.database import init_db


init_db()

st.title("学业预警")
st.caption("学习支持系统 | 负责人：Huang")

st.write(
    "使用课程早期的成绩、作业提交和学习平台活动，"
    "辅助识别需要进一步关注的学生。"
)

st.info(
    "页面框架已建立。后续在此实现评估表单、模型预测、"
    "风险解释和预警记录。"
)

st.subheader("计划输入")
st.write(
    "匿名编号、出勤率、平均成绩、作业提交率、"
    "平台总点击量、活跃天数和测验点击量。"
)

st.subheader("计划输出")
st.write("模型概率、出勤修正、综合风险、风险等级和干预建议。")