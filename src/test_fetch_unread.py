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


if __name__ == "__main__":
    unittest.main()
