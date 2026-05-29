import os
import re
from typing import Optional

from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


# Ensure .env is loaded if present at repo root
# project_manager/settings.py already calls load_dotenv, but this is a safe fallback.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT_DIR, '.env'), override=False)


def _get_openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    if OpenAI is None:
        raise RuntimeError("openai package is not installed. Add it to requirements.txt")
    return OpenAI(api_key=api_key)


def _clean_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def suggest_task_priority(*, title: str, deadline: Optional[str], workload_hint: Optional[str] = None) -> str:
    """Return one of: Low/Medium/High/Critical."""
    client = _get_openai_client()
    if client is None:
        # Fallback heuristic
        if deadline:
            return "High"  # optimistic default
        return "Medium"

    deadline_part = f"Deadline: {deadline}" if deadline else "No deadline"
    workload_part = f"Workload: {workload_hint}" if workload_hint else "Workload: unknown"

    system = "You are a project management assistant. " \
              "Given a task, suggest the most appropriate priority among: Low, Medium, High, Critical. " \
              "Respond with ONLY the single word: Low or Medium or High or Critical."

    user = f"Task title: {title}\n{deadline_part}\n{workload_part}"

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    content = _clean_text(resp.choices[0].message.content)
    # Normalize potential formatting
    for candidate in ["Low", "Medium", "High", "Critical"]:
        if candidate.lower() in content.lower():
            return candidate
    return "Medium"


def generate_task_description(*, title: str) -> str:
    client = _get_openai_client()
    if client is None:
        # Fallback
        return f"Work on: {title}."

    system = "You are an expert project coordinator. " \
              "Generate a clear, actionable task description for the given task title. " \
              "Return 3-6 sentences."

    user = f"Task title: {title}"

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.5,
    )

    return _clean_text(resp.choices[0].message.content)


def suggest_team_member(*, title: str, members_payload: list) -> Optional[int]:
    """members_payload: list of dicts {id, username, skills(list/str), workload(int/str)}.
    Returns suggested member user id or None.
    """
    client = _get_openai_client()
    if client is None:
        # Fallback: first member
        if members_payload:
            return members_payload[0].get("id")
        return None

    system = "You are an AI resource planner. " \
              "Pick the best team member for the task. " \
              "Return ONLY the member id as an integer. If no suitable member exists, return 0."

    user = (
        f"Task title: {title}\n"
        f"Team members (JSON): {members_payload}"
    )

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    content = _clean_text(resp.choices[0].message.content)
    # Extract first integer
    m = re.search(r"-?\d+", content)
    if not m:
        return None
    value = int(m.group(0))
    return None if value == 0 else value


def generate_project_summary(*, project_title: str, progress_percent: int, top_tasks: list) -> str:
    client = _get_openai_client()
    if client is None:
        summary = f"{project_title}: {progress_percent}% complete."
        if top_tasks is None:
            summary += " No additional AI summary available."
        return summary

    system = "You are an AI project manager. " \
              "Create a concise status report summary for a project. " \
              "Use a professional tone, 5-8 bullet points."

    user = (
        f"Project: {project_title}\n"
        f"Progress: {progress_percent}%\n"
        f"Notable tasks (JSON): {top_tasks}"
    )

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
    )

    return _clean_text(resp.choices[0].message.content)


def answer_project_chatbot(*, question: str, context: str) -> str:
    client = _get_openai_client()
    if client is None:
        return "AI is not configured. Please set OPENAI_API_KEY in .env."

    system = "You are a helpful assistant for collaborative project management. " \
              "Answer the user question using the provided context. If context is missing, say so."

    user = f"Context:\n{context}\n\nQuestion: {question}"

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )

    return resp.choices[0].message.content.strip()

