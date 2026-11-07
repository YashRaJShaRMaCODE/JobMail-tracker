import unittest
from unittest.mock import Mock, patch

from main import preview_messages, process_messages


class MessageProcessingTests(unittest.TestCase):
    def test_preview_counts_without_mutating_gmail_sheets_or_checkpoint(self):
        state = {
            "processed_ids": {"logged"},
            "pending_ids": {"pending"},
        }
        emails = {
            "job": {"from": "recruiter@example.com", "subject": "Interview invite", "content": "Let's talk"},
            "promo": {"from": "noreply@example.com", "subject": "Application tips", "content": "A newsletter"},
        }
        gmail = Mock()
        messages = [{"id": key} for key in ("job", "promo", "logged", "pending", "job")]

        with patch("main.parse_email", side_effect=lambda _, message_id: emails[message_id]) as parse, \
             patch("main.append_row") as append, \
             patch("main.mark_email_as_read") as mark_read, \
             patch("main.save_state") as save:
            result = preview_messages(gmail, messages, state)

        self.assertEqual(result, (1, 1, 1, 1))
        self.assertEqual(parse.call_count, 2)
        append.assert_not_called()
        mark_read.assert_not_called()
        save.assert_not_called()
        self.assertEqual(state, {"processed_ids": {"logged"}, "pending_ids": {"pending"}})

    def test_successful_append_persists_id_before_marking_read(self):
        gmail = Mock()
        state = {"processed_ids": set(), "pending_ids": set()}
        email = {
            "from": "recruiter@example.com",
            "subject": "Interview invite",
            "date": "2026-01-15 10:00:00",
            "content": "Details",
        }
        events = []

        with patch("main.parse_email", return_value=email), \
             patch("main.append_row", side_effect=lambda *args: events.append("append")), \
             patch("main.save_state", side_effect=lambda _: events.append("save")), \
             patch("main.mark_email_as_read", side_effect=lambda *args: events.append("read")):
            process_messages(gmail, Mock(), [{"id": "message-1"}], state, "sheet", "Sheet1")

        self.assertEqual(events, ["save", "append", "save", "read"])
        self.assertIn("message-1", state["processed_ids"])
        self.assertNotIn("message-1", state["pending_ids"])

    def test_recovers_a_sheet_write_that_succeeded_before_crash(self):
        state = {"processed_ids": set(), "pending_ids": {"message-1"}}

        with patch("main.get_logged_message_ids", return_value={"message-1"}), \
             patch("main.append_row") as append, \
             patch("main.parse_email") as parse, \
             patch("main.save_state"):
            process_messages(Mock(), Mock(), [], state, "sheet", "Sheet1")

        append.assert_not_called()
        parse.assert_not_called()
        self.assertIn("message-1", state["processed_ids"])
        self.assertFalse(state["pending_ids"])

    def test_retries_a_pending_write_missing_from_the_sheet(self):
        state = {"processed_ids": set(), "pending_ids": {"message-1"}}
        email = {
            "from": "recruiter@example.com",
            "subject": "Interview invite",
            "date": "2026-01-15 10:00:00",
            "content": "Details",
        }

        with patch("main.get_logged_message_ids", return_value=set()), \
             patch("main.parse_email", return_value=email), \
             patch("main.append_row") as append, \
             patch("main.save_state"), \
             patch("main.mark_email_as_read"):
            process_messages(Mock(), Mock(), [], state, "sheet", "Sheet1")

        append.assert_called_once()
        self.assertIn("message-1", state["processed_ids"])
        self.assertFalse(state["pending_ids"])

    def test_persisted_processed_message_is_never_appended_twice(self):
        state = {"processed_ids": {"message-1"}, "pending_ids": set()}

        with patch("main.append_row") as append, patch("main.mark_email_as_read"):
            process_messages(Mock(), Mock(), [{"id": "message-1"}], state, "sheet", "Sheet1")

        append.assert_not_called()


if __name__ == "__main__":
    unittest.main()
