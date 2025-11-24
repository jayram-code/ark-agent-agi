# 📧 Gmail API Setup Guide

## Step 1: Create Google Cloud Project

1. Go to: https://console.cloud.google.com
2. **Create new project** or select existing
3. Name it: `ark-agent-agi`

## Step 2: Enable Gmail API

1. In Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click **Enable**

## Step 3: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure **OAuth consent screen**:
   - User Type: **External**
   - App name: `ARK Agent AGI`
   - User support email: your email
   - Developer contact: your email
   - Scopes: Add Gmail API scopes
   - Test users: Add your Gmail address
   - Save

4. Back to **Create OAuth client ID**:
   - Application type: **Desktop app**
   - Name: `ARK Agent Desktop`
   - Click **Create**

5. **Download** the JSON file
6. **Rename** it to `credentials.json`
7. **Move** it to: `c:\Users\jaisu\ark-agent-agi\credentials.json`

## Step 4: Install Required Packages

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Step 5: Test Authentication

```bash
cd c:\Users\jaisu\ark-agent-agi
python

>>> from src.integrations.gmail_api import get_gmail_api
>>> gmail = get_gmail_api()
```

This will:
1. Open browser for OAuth
2. Login with your Gmail
3. Grant permissions
4. Save token to `data/gmail_token.pickle`

## Step 6: Fetch Emails

```python
# Fetch latest 50 emails
emails = gmail.fetch_emails(max_results=50)

# Fetch unread emails
emails = gmail.fetch_emails(query='is:unread')

# Fetch from specific sender
emails = gmail.fetch_emails(query='from:client@example.com')
```

---

## ✅ You're Ready!

Once `credentials.json` is set up, the system will:
- Auto-authenticate
- Store token for reuse
- Fetch emails on demand

**For demo**: Use your real Gmail or create a test account with sample emails!
