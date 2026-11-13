import argparse
import csv
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gmail_service import MAX_UNREAD_MESSAGES, get_gmail_service, get_unread_messages
from email_parser import parse_email
from sheets_service import get_sheets_service, append_row, get_logged_message_ids
from state_manager import (
    load_state, save_state, is_processed, mark_processed,
    mark_pending, clear_pending,
)
from config import SPREADSHEET_ID, SHEET_NAME, STORE_EMAIL_BODY
from logger import logger


def parse_batch_size(value):
    try:
        size = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("limit must be a whole number") from exc
    if not 1 <= size <= MAX_UNREAD_MESSAGES:
        raise argparse.ArgumentTypeError(f"limit must be between 1 and {MAX_UNREAD_MESSAGES}")
    return size


def parse_since_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("since date must use YYYY-MM-DD format") from exc


# ✅ Mark email as read
def mark_email_as_read(service, message_id):
    service.users().messages().modify(
        userId='me',
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


# ✅ Job-related keyword filter
def is_job_related(email_data, extra_keywords=()):
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

    custom_keywords = [str(keyword).strip().lower() for keyword in extra_keywords]
    return any(keyword.lower() in combined_text for keyword in (*keywords, *custom_keywords) if keyword)


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


def preview_messages(gmail_service, messages, state, export_path=None, extra_keywords=()):
    seen_ids = set()
    matched = filtered = already_processed = pending = blocked_senders = no_job_signal = 0
    output = open(export_path, "w", newline="", encoding="utf-8") if export_path else None
    try:
        writer = csv.writer(output) if output else None
        if writer:
            writer.writerow(["From", "Subject", "Date", "Content", "Gmail message ID"])
        for message in messages:
            message_id = message.get("id")
            if not message_id or message_id in seen_ids:
                continue
            seen_ids.add(message_id)
            if is_processed(state, message_id):
                already_processed += 1
                continue
            if message_id in state["pending_ids"]:
                pending += 1
                continue
            email_data = parse_email(gmail_service, message_id)
            if is_blocked_sender(email_data["from"]):
                filtered += 1
                blocked_senders += 1
                continue
            if not is_job_related(email_data, extra_keywords):
                filtered += 1
                no_job_signal += 1
                continue
            matched += 1
            if writer:
                values = [email_data["from"], email_data["subject"], email_data["date"],
                          email_data["content"][:1000] if STORE_EMAIL_BODY else "", message_id]
                writer.writerow([f"'{value}" if str(value).startswith(("=", "+", "-", "@", "\t", "\r")) else value for value in values])
    finally:
        if output:
            output.close()
    return matched, filtered, already_processed, pending, blocked_senders, no_job_signal


def process_messages(
    gmail_service, sheets_service, messages, state, spreadsheet_id, sheet_name,
    store_email_body=False, extra_keywords=(), keep_unread=False,
):
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
            if not keep_unread:
                mark_email_as_read(gmail_service, msg_id)
            continue

        email_data = parse_email(gmail_service, msg_id)
        if is_blocked_sender(email_data["from"]) or not is_job_related(email_data, extra_keywords):
            if not keep_unread:
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
        if not keep_unread:
            mark_email_as_read(gmail_service, msg_id)


def main(
    dry_run=False, max_results=10, export_csv=None, since=None,
    extra_keywords=(), status=False, keep_unread=False,
):
    if status:
        state = load_state()
        logger.info("Local checkpoint: %d processed, %d pending reconciliation items.",
                    len(state["processed_ids"]), len(state["pending_ids"]))
        return
    if type(max_results) is not int or not 1 <= max_results <= MAX_UNREAD_MESSAGES:
        logger.error("Message limit must be between 1 and %d.", MAX_UNREAD_MESSAGES)
        return
    if export_csv and not dry_run:
        logger.error("--export-csv requires --dry-run; no Gmail or Sheets changes were made.")
        return

    if not dry_run and not SPREADSHEET_ID:
        logger.error("Set SPREADSHEET_ID before running the tracker.")
        return

    try:
        gmail_service = get_gmail_service(read_only=dry_run)
        sheets_service = None if dry_run else get_sheets_service()
    except FileNotFoundError:
        logger.error(
            "credentials/credentials.json not found. "
            "Download OAuth credentials from Google Cloud Console and place them there."
        )
        return

    if since:
        messages = get_unread_messages(gmail_service, max_results=max_results, since=since)
    else:
        messages = get_unread_messages(gmail_service, max_results=max_results)
    state = load_state()
    if not messages and not state["pending_ids"] and not (dry_run and export_csv):
        logger.info("No new unread emails found.")
        return

    if dry_run:
        try:
            matched, filtered, processed, pending, blocked, no_signal = preview_messages(
                gmail_service, messages, state, export_csv, extra_keywords
            )
        except OSError as exc:
            logger.error("Could not write CSV export: %s", exc)
            return
        logger.info(
            "Dry run: %d job-related, %d filtered (%d blocked senders, %d without job signals), %d already logged, and %d pending reconciliation items left untouched%s. No Sheets rows or Gmail labels were changed.",
            matched, filtered, blocked, no_signal, processed, pending,
            f"; matched rows exported to {export_csv}" if export_csv else "",
        )
        return

    process_messages(
        gmail_service, sheets_service, messages, state,
        SPREADSHEET_ID, SHEET_NAME, STORE_EMAIL_BODY, extra_keywords, keep_unread,
    )
    logger.info("🎉 Processing completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track job-related Gmail messages in Google Sheets.")
    parser.add_argument("--dry-run", action="store_true", help="Preview unread email matches without changing Gmail or Sheets.")
    parser.add_argument("--export-csv", metavar="PATH", help="Save matched dry-run rows to a local CSV file (requires --dry-run).")
    parser.add_argument("--since", type=parse_since_date, metavar="YYYY-MM-DD", help="Scan unread messages received after this date.")
    parser.add_argument("--job-keyword", action="append", default=[], metavar="WORD", help="Also match this job-related word or phrase; may be repeated.")
    parser.add_argument("--status", action="store_true", help="Show local checkpoint counts without signing in to Gmail.")
    parser.add_argument("--keep-unread", action="store_true", help="Log and checkpoint emails without removing their UNREAD label.")
    parser.add_argument(
        "--limit",
        type=parse_batch_size,
        default=10,
        metavar="N",
        help=f"Max unread Inbox messages to scan this run (1-{MAX_UNREAD_MESSAGES}; default: 10).",
    )
    arguments = parser.parse_args()
    main(
        dry_run=arguments.dry_run,
        max_results=arguments.limit,
        export_csv=arguments.export_csv,
        since=arguments.since,
        extra_keywords=arguments.job_keyword,
        status=arguments.status,
        keep_unread=arguments.keep_unread,
    )
