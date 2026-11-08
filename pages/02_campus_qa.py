from uuid import uuid4

import streamlit as st

from core.campus_qa import answer_question, get_api_key, load_messages, save_turn
from core.database import init_db


def show_message(role, content, sources="", mode="fallback"):
    with st.chat_message(role):
        if role == "assistant":
            st.caption("DeepSeek response" if mode == "ai" else "Local response")
        st.write(content)
        if sources:
            st.caption("Demo knowledge base references: " + sources.replace("、", ", "))


init_db()
st.title("Campus Q&A Assistant")
st.caption("Learning Support | Module owner: Song")

api_key = get_api_key()
st.caption("DeepSeek mode" if api_key else "Local mode. Set DEEPSEEK_API_KEY to enable DeepSeek.")
st.info("Ask about courses, enrolment or learning resources. This assistant currently uses demonstration materials.")

if "campus_qa_session_id" not in st.session_state:
    st.session_state.campus_qa_session_id = uuid4().hex
session_id = st.session_state.campus_qa_session_id

messages = load_messages(session_id)
for row in messages:
    show_message(row["role"], row["content"], row["sources"], row["mode"])

question = st.chat_input("Ask a campus question", max_chars=500)
if question and question.strip():
    question = question.strip()
    show_message("user", question)
    with st.spinner("Looking up campus information…"):
        answer, mode, sources, notice = answer_question(question, messages, api_key)
        save_turn(session_id, question, answer, sources, mode)
    if notice:
        st.warning(notice + " Using the local knowledge base for this response.")
    show_message("assistant", answer, ", ".join(sources), mode)
