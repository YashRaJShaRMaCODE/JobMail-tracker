import json
import os

STATE_FILE = "data/state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"processed_ids": []}

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_processed(state, message_id):
    return message_id in state["processed_ids"]


def mark_processed(state, message_id):
    state["processed_ids"].append(message_id)
