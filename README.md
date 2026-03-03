![Python](https://img.shields.io/badge/Python-3.10+-blue)
![OAuth](https://img.shields.io/badge/Auth-OAuth2.0-green)
![APIs](https://img.shields.io/badge/APIs-Gmail%20%7C%20Sheets-red)
![Architecture](https://img.shields.io/badge/Design-Idempotent-purple)


# 🚀 JobMail Tracker
### Gmail → Google Sheets Intelligent Automation
### 🚀 Intelligent Job Email Tracker

**Author:** Yash Raj Sharma  

---

## 📖 Project Overview

This project is a Python-based automation system that integrates the **Gmail API** and **Google Sheets API** using **OAuth 2.0 authentication**.

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
| Content | Email body (plain text) |

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

Edit `config.py`:

```python
SPREADSHEET_ID = "YOUR_GOOGLE_SHEET_ID"
SHEET_NAME = "Sheet1"
```

---

### 5️⃣ Run the Script

```bash
python src/main.py
```

---

## 🔐 OAuth Flow Explanation

The project uses the OAuth 2.0 Installed App flow.

### On First Run:
- Browser window opens
- User grants Gmail & Sheets permissions
- `token.json` is created locally

### On Subsequent Runs:
- Stored token is reused
- Access tokens refresh automatically

This ensures secure authentication without storing user passwords.

---

## 🧠 Duplicate Prevention Logic

Each Gmail email has a unique **Message ID**.

The system maintains a local JSON file (`state.json`) containing processed IDs.

### Execution Flow:

1. Fetch unread emails
2. Check Message ID in state
3. If already processed → skip
4. Else → process and append
5. Store Message ID

This guarantees append-only, duplicate-free execution.

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

- Idempotent execution (safe re-runs)
- Append-only Google Sheets writes
- Message ID-based duplicate detection
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
- Modular Python architecture
- Idempotent system design
- Smart filtering logic
- Reliable duplicate prevention
- Real-world Gmail → Sheets automation pipeline

It simulates a production-style backend automation workflow suitable for CRM ingestion, job tracking systems, and workflow integrations.
