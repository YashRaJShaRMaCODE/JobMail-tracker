import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gmail_service import get_gmail_service, get_unread_messages
from email_parser import parse_email
from sheets_service import get_sheets_service, append_row
from state_manager import load_state, save_state, is_processed, mark_processed
from config import SPREADSHEET_ID, SHEET_NAME
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


def main():
    try:
        gmail_service = get_gmail_service()
        sheets_service = get_sheets_service()
    except FileNotFoundError:
        logger.error(
            "credentials/credentials.json not found. "
            "Download OAuth credentials from Google Cloud Console and place them there."
        )
        return

    state = load_state()

    messages = get_unread_messages(gmail_service, max_results=10)

    if not messages:
        logger.info("No new unread emails found.")
        return

    for msg in messages:
        msg_id = msg['id']

        if is_processed(state, msg_id):
            continue

        email_data = parse_email(gmail_service, msg_id)

        # 🔎 Filter blocked senders
        if is_blocked_sender(email_data["from"]):
            logger.info(f"⛔ Skipping newsletter/spam from: {email_data['from']}")
            mark_email_as_read(gmail_service, msg_id)
            mark_processed(state, msg_id)
            continue

        # 🔎 Filter non-job emails
        if not is_job_related(email_data):
            logger.info(f"🚫 Skipping non-job email: {email_data['subject']}")
            mark_email_as_read(gmail_service, msg_id)
            mark_processed(state, msg_id)
            continue

        # ✅ Append only job-related emails
        row = [
            email_data['from'],
            email_data['subject'],
            email_data['date'],
            email_data['content']
        ]

        append_row(
            sheets_service,
            SPREADSHEET_ID,
            SHEET_NAME,
            row
        )

        logger.info(f"✅ Logged job email: {email_data['subject']}")

        mark_email_as_read(gmail_service, msg_id)
        mark_processed(state, msg_id)

    save_state(state)
    logger.info("🎉 Processing completed successfully.")


if __name__ == "__main__":
    main()