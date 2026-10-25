import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gmail_service import get_gmail_service, get_unread_messages
from email_parser import parse_email
from sheets_service import get_sheets_service, append_row, get_logged_message_ids
from state_manager import (
    load_state, save_state, is_processed, mark_processed,
    mark_pending, clear_pending,
)
from config import SPREADSHEET_ID, SHEET_NAME, STORE_EMAIL_BODY
from logger import logger


# ✅ Mark email as read
def mark_email_as_read(service, message_id):
    service.users().messages().modify(
        userId='me',
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


# ✅ Job-related keyword filter
def is_job_related(email_data):
    keywords = [
        "interview",
        "application",
        "job",
        "internship",
        "hiring",
        "offer",
        "shortlisted",
        "opportunity",
        "career",
        "assessment",
        "position",
        "role"
    ]

    combined_text = (
        email_data["subject"] + " " + email_data["content"]
    ).lower()

    return any(keyword in combined_text for keyword in keywords)


# ✅ Block common newsletter / spam senders
def is_blocked_sender(sender):
    blocked_keywords = [
        "noreply",
        "newsletter",
        "linkedin",
        "internshala",
        "unstop",
        "fastweb",
        "beehiiv",
        "academy",
        "alerts"
    ]

    sender = sender.lower()
    return any(word in sender for word in blocked_keywords)


def process_messages(gmail_service, sheets_service, messages, state, spreadsheet_id, sheet_name, store_email_body=False):
    message_ids = []
    seen_ids = set()
    for message in messages:
        message_id = message["id"]
        if message_id not in seen_ids:
            message_ids.append(message_id)
            seen_ids.add(message_id)

    pending_ids = state["pending_ids"]
    if pending_ids:
        logged_ids = get_logged_message_ids(sheets_service, spreadsheet_id, sheet_name)
        for message_id in pending_ids & logged_ids:
            mark_processed(state, message_id)
            clear_pending(state, message_id)
        if pending_ids:
            message_ids.extend(sorted(pending_ids - seen_ids))
        save_state(state)

    for msg_id in message_ids:
        if is_processed(state, msg_id):
            mark_email_as_read(gmail_service, msg_id)
            continue

        email_data = parse_email(gmail_service, msg_id)
        if is_blocked_sender(email_data["from"]) or not is_job_related(email_data):
            mark_email_as_read(gmail_service, msg_id)
            mark_processed(state, msg_id)
            save_state(state)
            continue

        if msg_id not in state["pending_ids"]:
            mark_pending(state, msg_id)
            save_state(state)

        append_row(sheets_service, spreadsheet_id, sheet_name, [
            email_data["from"],
            email_data["subject"],
            email_data["date"],
            email_data["content"][:1000] if store_email_body else "",
            msg_id,
        ])
        mark_processed(state, msg_id)
        clear_pending(state, msg_id)
        save_state(state)
        logger.info("Logged a job email")
        mark_email_as_read(gmail_service, msg_id)


def main():
    if not SPREADSHEET_ID:
        logger.error("Set SPREADSHEET_ID before running the tracker.")
        return

    try:
        gmail_service = get_gmail_service()
        sheets_service = get_sheets_service()
    except FileNotFoundError:
        logger.error(
            "credentials/credentials.json not found. "
            "Download OAuth credentials from Google Cloud Console and place them there."
        )
        return

    messages = get_unread_messages(gmail_service, max_results=10)
    state = load_state()
    if not messages and not state["pending_ids"]:
        logger.info("No new unread emails found.")
        return

    process_messages(
        gmail_service, sheets_service, messages, state,
        SPREADSHEET_ID, SHEET_NAME, STORE_EMAIL_BODY,
    )
    logger.info("🎉 Processing completed successfully.")


if __name__ == "__main__":
    main()
