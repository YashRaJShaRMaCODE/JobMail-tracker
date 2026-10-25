import unittest
from unittest.mock import Mock

from sheets_service import append_row, get_logged_message_ids


class SheetsServiceTests(unittest.TestCase):
    def test_appends_raw_row_including_message_id(self):
        service = Mock()
        row = ["from", "subject", "date", "", "message-1"]

        append_row(service, "sheet-id", "Hiring '26", row)

        service.spreadsheets.return_value.values.return_value.append.assert_called_once_with(
            spreadsheetId="sheet-id",
            range="'Hiring ''26'!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        )

    def test_reads_message_ids_for_crash_recovery(self):
        service = Mock()
        service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
            "values": [["Gmail message ID"], ["message-1"], []]
        }

        ids = get_logged_message_ids(service, "sheet-id", "Job tracker")

        self.assertEqual(ids, {"Gmail message ID", "message-1"})
        service.spreadsheets.return_value.values.return_value.get.assert_called_once_with(
            spreadsheetId="sheet-id", range="'Job tracker'!E:E"
        )


if __name__ == "__main__":
    unittest.main()
