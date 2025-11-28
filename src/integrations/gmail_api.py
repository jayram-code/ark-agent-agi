"""
Gmail API Integration for ARK Agent AGI
Handles OAuth2 authentication and email fetching
"""
import os
import pickle
from typing import List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
import random
import time

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

class GmailAPI:
    def __init__(self):
        self.service = None
        self.mock_mode = False
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API or fallback to Mock Mode"""
        creds = None
        token_path = 'data/gmail_token.pickle'
        creds_path = 'credentials.json'
        
        # Check if credentials exist
        if not os.path.exists(creds_path) and not os.path.exists(token_path):
            print("⚠️ Credentials not found. Switching to MOCK MODE for Demo.")
            self.mock_mode = True
            return

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    # Fallback to mock if credentials missing during auth flow
                    print("⚠️ Credentials missing. Switching to MOCK MODE.")
                    self.mock_mode = True
                    return
                    
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            os.makedirs('data', exist_ok=True)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail API authenticated successfully!")

    def fetch_emails(self, max_results=10):
        """Fetch emails from Inbox (Real or Mock)"""
        if getattr(self, 'mock_mode', False):
            return self._fetch_mock_emails(max_results)
            
        try:
            results = self.service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            email_list = []
            print(f"📧 Fetching {len(messages)} emails...")
            
            for message in messages:
                msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
                email_data = self._parse_email(msg)
                email_list.append(email_data)
                
            return email_list
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []

    def _fetch_mock_emails(self, max_results=10):
        """Generate fake enterprise emails for demo"""
        mock_emails = []
        senders = [
            ('client@bigcorp.com', 'BigCorp'),
            ('boss@company.com', 'Internal'),
            ('invoice@vendor.com', 'Vendor'),
            ('hr@company.com', 'HR'),
            ('support@tech.com', 'IT Support')
        ]
        
        subjects = [
            "Urgent: Project Deadline",
            "Invoice #12345 for Payment",
            "Meeting Request: Q4 Planning",
            "Complaint about service downtime",
            "Employee Benefits Update",
            "Sales Inquiry - Enterprise Plan",
            "Server Access Issue",
            "Follow up on proposal"
        ]
        
        for i in range(max_results):
            sender, org = random.choice(senders)
            subject = random.choice(subjects)
            
            mock_emails.append({
                'id': f'mock_{i}',
                'threadId': f'thread_{i}',
                'snippet': f"This is a mock email content for {subject}...",
                'subject': subject,
                'from': sender,
                'to': 'me@company.com',
                'date': time.time()
            })
            
        return mock_emails

    def _parse_email(self, message):
        """Parse Gmail API message object"""
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        
        return {
            'id': message['id'],
            'threadId': message['threadId'],
            'snippet': message.get('snippet', ''),
            'subject': subject,
            'from': sender,
            'date': next((h['value'] for h in headers if h['name'] == 'Date'), '')
        }

    def send_email(self, to, subject, body):
        """Send email (Real or Mock)"""
        if getattr(self, 'mock_mode', False):
            print(f"📧 [MOCK SEND] To: {to} | Subject: {subject}")
            return {'id': 'mock_sent_id'}
            
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            message = {'raw': raw}
            return self.service.users().messages().send(userId='me', body=message).execute()
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return None

    def mark_as_read(self, email_id):
        """Mark as read (Real or Mock)"""
        if getattr(self, 'mock_mode', False):
            return
            
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            print(f"Error marking email as read: {e}")

# Singleton instance
gmail_api = None

def get_gmail_api():
    """Get or create Gmail API instance"""
    global gmail_api
    if gmail_api is None:
        gmail_api = GmailAPI()
    return gmail_api
