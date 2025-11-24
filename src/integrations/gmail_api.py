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

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

class GmailAPI:
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API using OAuth2"""
        creds = None
        token_path = 'data/gmail_token.pickle'
        creds_path = 'credentials.json'
        
        # Load existing token
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    raise FileNotFoundError(
                        "Please download credentials.json from Google Cloud Console"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            os.makedirs('data', exist_ok=True)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail API authenticated successfully!")
    
    def fetch_emails(self, max_results: int = 300, query: str = '') -> List[Dict[str, Any]]:
        """
        Fetch emails from Gmail inbox
        
        Args:
            max_results: Maximum number of emails to fetch (default 300)
            query: Gmail search query (e.g., 'is:unread', 'from:client@example.com')
        
        Returns:
            List of email dictionaries with metadata and content
        """
        try:
            # Get message IDs
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("No messages found.")
                return []
            
            emails = []
            total = len(messages)
            
            print(f"📧 Fetching {total} emails...")
            
            for idx, message in enumerate(messages, 1):
                email_data = self._get_email_details(message['id'])
                emails.append(email_data)
                
                if idx % 50 == 0:
                    print(f"  Processed {idx}/{total} emails...")
            
            print(f"✅ Fetched {len(emails)} emails successfully!")
            return emails
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []
    
    def _get_email_details(self, msg_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            
            # Extract headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            to = next((h['value'] for h in headers if h['name'] == 'To'), '')
            
            # Extract body
            body = self._get_email_body(message['payload'])
            
            return {
                'id': msg_id,
                'subject': subject,
                'from': sender,
                'to': to,
                'date': date,
                'body': body[:1000],  # Limit to first 1000 chars
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', [])
            }
            
        except Exception as e:
            print(f"Error getting email {msg_id}: {e}")
            return {
                'id': msg_id,
                'subject': 'Error loading email',
                'from': 'Unknown',
                'body': '',
                'snippet': ''
            }
    
    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        # Fallback to main body
        data = payload.get('body', {}).get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return ''
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email"""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            print(f"✅ Email sent to {to}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def mark_as_read(self, msg_id: str) -> bool:
        """Mark an email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error marking email as read: {e}")
            return False


# Singleton instance
gmail_api = None

def get_gmail_api():
    """Get or create Gmail API instance"""
    global gmail_api
    if gmail_api is None:
        gmail_api = GmailAPI()
    return gmail_api
