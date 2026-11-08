import json
import logging
import os
import re
from contextlib import closing
from pathlib import Path

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from core.database import get_connection


ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_PATH = ROOT / "data" / "campus_qa_knowledge.json"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
NO_INFORMATION = "The demo knowledge base has no information on that topic. Try asking about courses, enrolment or learning resources."
LOGGER = logging.getLogger(__name__)


def get_api_key():
    load_dotenv(ROOT / ".env")
    return os.getenv("DEEPSEEK_API_KEY", "").strip()


def search_knowledge(question, knowledge):
    query = question.casefold()
    ranked = []
    for entry in knowledge:
        score = max(
            (1 if keyword == "csit883" else len(keyword)
             for keyword in entry["keywords"]
             if re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", query)),
            default=0,
        )
        if score:
            ranked.append((score, entry))
    ranked.sort(key=lambda match: match[0], reverse=True)
    return [entry for _, entry in ranked]


def ask_deepseek(api_key, question, history, references):
    context = "\n".join(f"{entry['category']}: {entry['answer']}" for entry in references)
    instructions = (
        "You are the SmartCampus campus assistant. Always respond in English, even if the question is in another language. Use the conversation history to understand follow-up questions. "
        "Respond naturally to greetings. Base campus facts only on the demonstration materials below. "
        "If the materials are insufficient, say so and suggest checking the university's official channels. "
        "Do not invent dates, links, policies or course details.\n\n" + context
    )
    messages = [{"role": "system", "content": instructions}]
    messages.extend({"role": row["role"], "content": row["content"][:2000]} for row in history[-6:])
    messages.append({"role": "user", "content": question})
    body = {
        "model": "deepseek-flash",
        "messages": messages,
        "thinking": {"type": "disabled"},
        "max_tokens": 1200,
    }
    request = Request(
        DEEPSEEK_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        choice = json.load(response)["choices"][0]
    answer = choice["message"]["content"]
    if choice["finish_reason"] != "stop" or not isinstance(answer, str) or not answer.strip():
        raise ValueError("No completed DeepSeek answer")
    return answer.strip()


def answer_question(question, history, api_key):
    with KNOWLEDGE_PATH.open(encoding="utf-8") as file:
        knowledge = json.load(file)

    matches = search_knowledge(question, knowledge)
    notice = ""
    if api_key:
        references = matches or knowledge
        try:
            answer = ask_deepseek(api_key, question, history, references)
            return answer, "ai", [entry["category"] for entry in matches], notice
        except HTTPError as error:
            status = error.code
            reason = {
                401: "API key authentication failed", 402: "account balance is insufficient", 403: "access was denied",
                404: "endpoint or model was not found", 429: "request was rate-limited",
            }.get(status, "request failed")
            notice = f"DeepSeek {reason} (HTTP {status})."
        except TimeoutError:
            notice = "The DeepSeek request timed out."
        except URLError as error:
            LOGGER.warning("DeepSeek connection error: %s", type(error.reason).__name__)
            notice = "The connection to DeepSeek timed out." if isinstance(error.reason, TimeoutError) else "Unable to connect to DeepSeek."
        except OSError as error:
            LOGGER.warning("DeepSeek transport error: %s", type(error).__name__)
            notice = "Unable to connect to DeepSeek."
        except (ValueError, KeyError, IndexError, TypeError):
            notice = "DeepSeek did not return a complete response."

    if matches:
        return matches[0]["answer"], "fallback", [matches[0]["category"]], notice

    greeting = question.casefold().strip(" \t\r\n,.!?")
    if greeting in {"hi", "hello", "hey", "who are you", "what can you do"}:
        answer = "Hello! I am the campus assistant. You can ask me about courses, enrolment or learning resources."
    else:
        answer = NO_INFORMATION
    return answer, "fallback", [], notice


def load_messages(session_id):
    with closing(get_connection()) as connection:
        return connection.execute(
            "SELECT role, content, sources, mode FROM chat_messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()


def save_turn(session_id, question, answer, sources, mode):
    with closing(get_connection()) as connection, connection:
        connection.executemany(
            "INSERT INTO chat_messages (session_id, role, content, sources, mode) VALUES (?, ?, ?, ?, ?)",
            [
                (session_id, "user", question, "", mode),
                (session_id, "assistant", answer, ", ".join(sources), mode),
            ],
        )
