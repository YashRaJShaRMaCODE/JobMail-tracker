from datetime import datetime
import os
GMAIL_READONLY_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets'
]
READ_ONLY_SCOPES = [GMAIL_READONLY_SCOPE]
MAX_UNREAD_MESSAGES = 500


def get_gmail_service(read_only=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    scopes = READ_ONLY_SCOPES if read_only else SCOPES
    token_file = 'token-readonly.json' if read_only else 'token.json'
    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/credentials.json', scopes
            )
            creds = flow.run_local_server(port=0)

        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def get_unread_messages(service, max_results=10, since=None):
    """
    Fetch unread emails from Inbox. Gmail allows at most 500 results per request.
    """
    if type(max_results) is not int or not 1 <= max_results <= MAX_UNREAD_MESSAGES:
        raise ValueError(f"max_results must be between 1 and {MAX_UNREAD_MESSAGES}")

    query = {}
    if since is not None:
        try:
            parsed_date = datetime.strptime(since, "%Y-%m-%d")
        except (TypeError, ValueError) as exc:
            raise ValueError("since must use YYYY-MM-DD format") from exc
        query["q"] = f"after:{parsed_date:%Y/%m/%d}"

    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX', 'UNREAD'],
        maxResults=max_results,
        **query,
    ).execute()

    messages = results.get('messages', [])
    return messages
