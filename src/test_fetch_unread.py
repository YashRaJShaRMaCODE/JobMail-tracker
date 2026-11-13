import unittest
from unittest.mock import Mock

from gmail_service import get_unread_messages


class GmailFetchTests(unittest.TestCase):
    def test_fetches_unread_inbox_messages_with_limit(self):
        service = Mock()
        request = service.users.return_value.messages.return_value.list.return_value
        request.execute.return_value = {"messages": [{"id": "message-1"}]}

        messages = get_unread_messages(service, max_results=5)

        service.users.return_value.messages.return_value.list.assert_called_once_with(
            userId="me", labelIds=["INBOX", "UNREAD"], maxResults=5
        )
        self.assertEqual(messages, [{"id": "message-1"}])

    def test_since_date_adds_gmail_query_without_changing_unread_scope(self):
        service = Mock()
        service.users.return_value.messages.return_value.list.return_value.execute.return_value = {"messages": []}

        get_unread_messages(service, max_results=25, since="2026-11-01")

        service.users.return_value.messages.return_value.list.assert_called_once_with(
            userId="me", labelIds=["INBOX", "UNREAD"], maxResults=25, q="after:2026/11/01"
        )

    def test_rejects_invalid_since_date_before_api_call(self):
        service = Mock()
        with self.assertRaises(ValueError):
            get_unread_messages(service, since="last week")
        service.users.assert_not_called()


if __name__ == "__main__":
    unittest.main()
