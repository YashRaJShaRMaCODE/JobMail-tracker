import base64
import unittest
from unittest.mock import Mock

from email_parser import _decode_body, _extract_body, parse_email


class EmailParserTests(unittest.TestCase):
    def test_decodes_unpadded_base64url(self):
        self.assertEqual(_decode_body("8J-Zgw"), "🙃")

    def test_skips_attachment_parts_and_uses_the_message_body(self):
        html = base64.urlsafe_b64encode(b"<p>Interview details</p>").decode()

        content = _extract_body({"parts": [
            {"mimeType": "text/plain", "filename": "notes.txt", "body": {"attachmentId": "att-1"}},
            {"mimeType": "text/html", "body": {"data": html}},
        ]})

        self.assertEqual(content, "Interview details")

    def test_empty_or_malformed_parts_return_an_empty_body(self):
        self.assertEqual(_extract_body({"parts": [{"mimeType": "text/plain", "body": {"attachmentId": "att-1"}}]}), "")
        self.assertEqual(_extract_body({"parts": None}), "")

    def test_parses_headers_and_plain_text_body(self):
        body = base64.urlsafe_b64encode(b"  Interview details  ").decode()
        service = Mock()
        service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "payload": {
                "headers": [
                    {"name": "From", "value": "Recruiter Team <recruiter@example.com>"},
                    {"name": "Subject", "value": "Interview invite"},
                    {"name": "Date", "value": "Thu, 15 Jan 2026 10:00:00 +0000"},
                ],
                "body": {"data": body},
            }
        }

        parsed = parse_email(service, "message-1")

        self.assertEqual(parsed["from"], "recruiter@example.com")
        self.assertEqual(parsed["subject"], "Interview invite")
        self.assertEqual(parsed["date"], "2026-01-15 10:00:00")
        self.assertEqual(parsed["content"], "Interview details")


if __name__ == "__main__":
    unittest.main()
