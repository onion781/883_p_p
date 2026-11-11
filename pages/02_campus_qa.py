from uuid import uuid4

import streamlit as st

from core.campus_qa import answer_question, get_api_key, load_messages, save_turn
from core.database import init_db


SESSION_KEY = "campus_qa_session_id"
PENDING_KEY = "campus_qa_pending_question"
WELCOME_INPUT = "campus_qa_welcome_input"
CHAT_INPUT = "campus_qa_chat_input"
STARTERS = (
    ("Course information", "Explore the demo course catalogue.", "What is the assessment for GCU101?"),
    ("Enrolment", "Find out how to confirm your place.", "How do I know if my enrolment was successful?"),
    ("Learning resources", "Find course materials and recordings.", "Where can I find lecture recordings?"),
)

PAGE_STYLES = """
<style>
  .campus-qa-hero {
    background: linear-gradient(115deg, #e9f1ff, #f6f9ff 65%, #e9f5ff);
    border: 1px solid #d6e4fb;
    border-radius: 24px;
    color: #183055;
    padding: clamp(1.5rem, 5vw, 3rem);
    text-align: center;
  }
  .campus-qa-hero h1 {
    color: #172e54;
    font-size: clamp(2rem, 5vw, 3.25rem);
    line-height: 1.15;
    margin: .7rem 0;
    padding: 0;
  }
  .campus-qa-hero p {
    color: #355270;
    margin: .5rem auto 0;
    max-width: 34rem;
  }
  .campus-qa-hero .campus-qa-eyebrow {
    color: #2455a5;
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
  }
  .st-key-campus_qa_header h1 {
    font-size: clamp(1.5rem, 4vw, 2.2rem);
    padding-top: 0;
  }
</style>
"""

WELCOME = """
<section class="campus-qa-hero" aria-labelledby="campus-qa-welcome-title">
  <div class="campus-qa-eyebrow">GlobalConnect University · Learning Support</div>
  <h1 id="campus-qa-welcome-title">What can I help you with?</h1>
  <p>Ask about courses, enrolment and learning resources in the SmartCampus demo.</p>
</section>
"""


def queue_question(question):
    question = question.strip()
    if question:
        st.session_state[PENDING_KEY] = question


def submit_input(widget_key):
    queue_question(st.session_state.get(widget_key) or "")


def start_new_chat():
    st.session_state[SESSION_KEY] = uuid4().hex
    st.session_state.pop(PENDING_KEY, None)


def show_message(role, content, sources="", mode="fallback", notice=""):
    with st.chat_message(role):
        if role == "assistant":
            st.caption("DeepSeek response" if mode == "ai" else "Local response")
        if notice:
            st.warning(notice + " Using the local knowledge base for this response.")
        st.write(content)
        if sources:
            st.caption("Demo knowledge base references: " + sources.replace("、", ", "))


def show_welcome(mode_label):
    with st.container(key="campus_qa_welcome"):
        st.html(WELCOME)
        st.chat_input(
            "Ask a campus question",
            key=WELCOME_INPUT,
            max_chars=500,
            on_submit=submit_input,
            args=(WELCOME_INPUT,),
        )
        st.caption(f"{mode_label} · Fictional GCU demonstration data")
        st.subheader("Suggested questions")
        for column, (title, description, question) in zip(st.columns(3), STARTERS):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.caption(description)
                    st.button(question, on_click=queue_question, args=(question,), use_container_width=True)


def show_chat(mode_label, session_id, messages, question, api_key):
    with st.container(key="campus_qa_header"):
        title, actions = st.columns([4, 1])
        with title:
            st.title("Campus Q&A Assistant")
            st.caption(f"{mode_label} · GCU demonstration data")
        with actions:
            st.button("New chat", on_click=start_new_chat, use_container_width=True)
        st.divider()

    for row in messages:
        show_message(row["role"], row["content"], row["sources"], row["mode"])

    if question:
        show_message("user", question)
        with st.spinner("Looking up campus information…"):
            answer, mode, sources, notice = answer_question(question, messages, api_key)
            save_turn(session_id, question, answer, sources, mode)
        show_message("assistant", answer, ", ".join(sources), mode, notice)

    st.chat_input(
        "Ask a follow-up question",
        key=CHAT_INPUT,
        max_chars=500,
        on_submit=submit_input,
        args=(CHAT_INPUT,),
    )


init_db()
if SESSION_KEY not in st.session_state:
    start_new_chat()

session_id = st.session_state[SESSION_KEY]
messages = load_messages(session_id)
question = st.session_state.pop(PENDING_KEY, "")
api_key = get_api_key()
mode_label = "DeepSeek mode" if api_key else "Local mode"
st.html(PAGE_STYLES)

if messages or question:
    show_chat(mode_label, session_id, messages, question, api_key)
else:
    show_welcome(mode_label)
