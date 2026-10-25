import unittest

from gmail_service import SCOPES


class GmailScopeTests(unittest.TestCase):
    def test_requests_only_scopes_used_by_the_app(self):
        self.assertEqual(SCOPES, [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/spreadsheets",
        ])


if __name__ == "__main__":
    unittest.main()
