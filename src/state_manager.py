import json
import os
import tempfile

STATE_FILE = "data/state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"processed_ids": set(), "pending_ids": set()}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("JobMail checkpoint is unreadable; preserve and repair data/state.json before retrying.") from exc
    if not isinstance(saved, dict):
        raise ValueError("JobMail checkpoint must be a JSON object; preserve and repair data/state.json before retrying.")

    state = {}
    for key in ("processed_ids", "pending_ids"):
        values = saved.get(key, [])
        if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
            raise ValueError(f"JobMail checkpoint field {key} must be a list of message IDs.")
        state[key] = set(values)
    return state


def save_state(state):
    directory = os.path.dirname(STATE_FILE) or "."
    os.makedirs(directory, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=directory, delete=False, encoding="utf-8") as f:
        json.dump({key: sorted(value) for key, value in state.items()}, f, indent=2)
        temp_path = f.name
    os.replace(temp_path, STATE_FILE)


def is_processed(state, message_id):
    return message_id in state["processed_ids"]


def mark_processed(state, message_id):
    state["processed_ids"].add(message_id)


def mark_pending(state, message_id):
    state["pending_ids"].add(message_id)


def clear_pending(state, message_id):
    state["pending_ids"].discard(message_id)
