# JobMail

**A local-first Gmail → Google Sheets tracker for job-related email.**

[Open the product site](https://yashrajsharmacode.github.io/JobMail-tracker/) · [Run the script](#run-the-script) · [Review privacy and OAuth](#oauth-flow-explanation)

---

## Project overview

JobMail is a Python automation tool that connects to the **Gmail API** and **Google Sheets API** through **OAuth 2.0**. It runs on your computer; the companion product site is static and uses fictional sample messages only.

The [JobMail product site](https://yashrajsharmacode.github.io/JobMail-tracker/) is a static overview. It does not connect to Gmail or Sheets and contains no real email data.

It reads real unread emails from a Gmail inbox, intelligently filters job-related emails, extracts structured information, and appends the data into a Google Sheet in an append-only and duplicate-safe manner.

The system is designed to be **idempotent**, meaning running the script multiple times will not create duplicate rows in the spreadsheet.

---

## 🎯 Objective

For each qualifying unread email in the Gmail inbox, the script appends a new row to Google Sheets with the following fields:

| Column | Description |
|--------|------------|
| From | Sender email address |
| Subject | Email subject |
| Date | Date & time received |
| Content | Empty by default; up to 1,000 characters only when `STORE_EMAIL_BODY=true` |
| Gmail message ID | Internal duplicate-recovery key (column E) |

Only **job-related emails** are logged to maintain signal over noise.

---

## 🎯 Smart Job Email Filtering

The system intelligently filters emails to log only job-related messages.

### 🔎 Filtering Logic:
- Keyword-based detection:
  - interview
  - application
  - internship
  - hiring
  - offer
  - shortlisted
  - opportunity
  - assessment
- Sender-based blocking:
  - noreply
  - newsletters
  - LinkedIn invites
  - promotional mailers

This transforms the system into a focused **Job Opportunity Tracker** instead of a generic email logger.

---

## 🏗️ High-Level Architecture

```
Gmail Inbox
    │
    │ (Gmail API + OAuth 2.0)
    ▼
Python Automation Script
    ├── Email Parsing
    ├── Smart Filtering
    ├── Duplicate Detection (state.json)
    ├── Mark as Read
    ▼
Google Sheets
```

---

## 🛠️ Tech Stack

- **Language:** Python 3  
- **APIs:** Gmail API, Google Sheets API  
- **Authentication:** OAuth 2.0 (Installed App Flow)  
- **Libraries:**
  - google-api-python-client
  - google-auth
  - google-auth-oauthlib
  - google-auth-httplib2
  - beautifulsoup4
  - python-dateutil

---

## 📂 Project Structure

```
gmail-to-sheets/
├── src/
│   ├── gmail_service.py
│   ├── sheets_service.py
│   ├── email_parser.py
│   ├── state_manager.py
│   └── main.py
│
├── credentials/
│   └── credentials.json (NOT committed)
│
├── proof/
│   ├── inbox.png
│   ├── sheet.png
│   └── oauth.png
│
├── config.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone <YOUR_REPOSITORY_LINK>
cd gmail-to-sheets
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Google Cloud Configuration

1. Create a Google Cloud Project  
2. Enable:
   - Gmail API  
   - Google Sheets API  
3. Configure OAuth Consent Screen (External)  
4. Add your Gmail address as a test user  
5. Create OAuth Client (Desktop App)  
6. Download `credentials.json`  

Place it inside:

```
credentials/credentials.json
```

---

### 4️⃣ Configure Google Sheet

Copy `.env.example` to `.env`, then set the spreadsheet ID and sheet name. Email bodies are not copied to Sheets by default; set `STORE_EMAIL_BODY=true` only if you want that sensitive data stored there.

The normal run uses `gmail.modify` because it marks processed messages as read. `--dry-run` uses the narrower `gmail.readonly` scope and never writes Sheets rows or changes Gmail labels. Review the OAuth consent screen and revoke the token when you no longer use the app.

---

### 5️⃣ Run the Script

<a id="run-the-script"></a>

```bash
python src/main.py --dry-run
python src/main.py
```

Use the preview first to see match counts before enabling spreadsheet writes and marking processed email as read.

---

## 🔐 OAuth Flow Explanation

The project uses the OAuth 2.0 Installed App flow.

### On First Run:
- Browser window opens
- Preview grants Gmail read-only access and creates `token-readonly.json` locally
- Normal run grants Gmail and Sheets access and creates `token.json` locally

### On Subsequent Runs:
- Stored token is reused
- Access tokens refresh automatically

This ensures secure authentication without storing user passwords.

---

## 🧠 Duplicate Prevention Logic

Each Gmail email has a unique **Message ID**. The tracker stores that ID in column E of the Google Sheet and in a local JSON checkpoint. Column E is used to recover safely if a Sheets write succeeds but the API response or process is interrupted before the local checkpoint is updated.

### Execution Flow:

1. Fetch unread emails
2. Skip IDs already in the local checkpoint
3. Save a pending checkpoint before writing a job email
4. Append the row and Message ID to columns A–E
5. Save the completed checkpoint, then mark the email read
6. On restart, check column E to recover an interrupted write without appending it twice

The local state uses sets for constant-time ID checks and is saved by atomic file replacement. Existing state files with a `processed_ids` list are migrated automatically. Add `Gmail message ID` as the header in E1 if the sheet already has a header row.

---

## 💾 State Persistence Method

Processed email IDs are stored locally:

```json
{
  "processed_ids": [
    "message_id_1",
    "message_id_2"
  ]
}
```

### Why This Approach?

- Lightweight
- Fast
- No external database required
- Survives script re-runs
- Simple and reliable for automation tasks

---

## 🛡️ Reliability Guarantees

- Duplicate recovery across interrupted Sheets writes
- Append-only Google Sheets writes
- Message ID-based duplicate detection
- Atomic local checkpoint updates
- Invalid checkpoints fail closed with a repair hint instead of silently resetting duplicate history
- Automatic token refresh handling
- Email marked as read after processing
- Smart filtering reduces noise

---

## 🚧 Challenges Faced & Solutions

### Issue: OAuth Insufficient Scope Errors

Encountered:
```
403 Insufficient Authentication Scopes
```

**Cause:** Reusing tokens created with limited permissions.

**Solution:**
- Unified Gmail and Sheets scopes
- Deleted existing `token.json`
- Forced re-authentication

---

## ⚠️ Limitations

- Email attachments are not processed
- Only unread Inbox emails are handled
- Local state file not suitable for distributed systems
- Very large inboxes may require pagination handling

---

## 🔄 Future Enhancements

- Filter emails from last 24 hours
- Categorize into multiple Sheet tabs (Interviews, Offers, Applications)
- Add structured logging
- Add pagination for large inboxes
- Replace JSON state with SQLite
- Dockerize and deploy to Cloud Run

---

## 🔐 Security Notice

This project requires Google OAuth credentials.

For security reasons:
- `credentials.json`
- `token.json`
- `state.json`

are not included in this repository.

To run locally, you must create your own Google Cloud OAuth credentials.

---

## ✅ Conclusion

This project demonstrates:

- Secure OAuth-based API integration

## 🧪 Offline tests

Run `python -m unittest discover -s src -p 'test_*.py' -v`. These tests use mocked Gmail and Sheets services and do not access a real account.
- Modular Python architecture
- Idempotent system design
- Smart filtering logic
- Reliable duplicate prevention
- Real-world Gmail → Sheets automation pipeline

It simulates a production-style backend automation workflow suitable for CRM ingestion, job tracking systems, and workflow integrations.
