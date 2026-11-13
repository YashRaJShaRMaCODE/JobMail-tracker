import base64
from bs4 import BeautifulSoup
from email.utils import parseaddr, parsedate_to_datetime


def _get_header(headers, name):
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ""


def _decode_body(data):
    decoded_bytes = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    return decoded_bytes.decode("utf-8", errors="ignore")


def _extract_body(payload):
    """
    Recursively extract email body
    """
    if not isinstance(payload, dict):
        return ""

    parts = payload.get('parts')
    if isinstance(parts, list):
        for part in parts:
            if not isinstance(part, dict) or part.get('filename'):
                continue
            mime_type = part.get('mimeType')
            body = part.get('body') or {}
            data = body.get('data') if isinstance(body, dict) else None
            if mime_type == 'text/plain' and data:
                return _decode_body(data)
            elif mime_type == 'text/html' and data:
                html = _decode_body(data)
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text()
            else:
                result = _extract_body(part)
                if result:
                    return result
    else:
        body = payload.get('body') or {}
        data = body.get('data') if isinstance(body, dict) else None
        if data:
            return _decode_body(data)

    return ""


def parse_email(service, message_id):
    """
    Fetch and parse a Gmail message by ID
    """
    msg = service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'
    ).execute()

    headers = msg['payload']['headers']

    sender_header = _get_header(headers, 'From')
    sender = parseaddr(sender_header)[1] or sender_header
    subject = _get_header(headers, 'Subject')
    date_raw = _get_header(headers, 'Date')

    try:
        date = parsedate_to_datetime(date_raw)
        date = date.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        date = date_raw

    body = _extract_body(msg['payload'])

    return {
        "from": sender,
        "subject": subject,
        "date": date,
        "content": body.strip()
    }
