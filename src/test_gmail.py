import unittest

from gmail_service import GMAIL_READONLY_SCOPE, READ_ONLY_SCOPES, SCOPES


class GmailScopeTests(unittest.TestCase):
    def test_requests_only_scopes_used_by_the_app(self):
        self.assertEqual(SCOPES, [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/spreadsheets",
        ])

    def test_preview_requests_read_only_gmail_scope(self):
        self.assertEqual(READ_ONLY_SCOPES, [GMAIL_READONLY_SCOPE])


if __name__ == "__main__":
    unittest.main()
