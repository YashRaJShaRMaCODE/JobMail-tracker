import os

from dotenv import load_dotenv

load_dotenv()

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
SHEET_NAME = os.environ.get("SHEET_NAME", "Sheet1")
STORE_EMAIL_BODY = os.environ.get("STORE_EMAIL_BODY", "false").lower() == "true"
