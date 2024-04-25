import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import data_processor
import email_fetcher

# Update scopes to include both read and modify permissions
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # To read and delete emails
    'https://www.googleapis.com/auth/gmail.readonly'  # Redundant in this context, but included for clarity
]

def main():
    base_dir = os.path.abspath('.')
    auth_dir = os.path.join(base_dir, 'auth')
    data_dir = os.path.join(base_dir, 'data')

    senders_data_path = os.path.join(data_dir, 'senders_data.json')
    noreply_senders_path = os.path.join(data_dir, 'noreply_senders.json')  # Ensure the correct file extension is used

    creds = None
    token_path = os.path.join(auth_dir, 'token.json')
    # Check if the existing token covers the new scopes
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds_path = os.path.join(auth_dir, 'credentials.json')
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the new token with broader scopes
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    
    if os.path.exists(senders_data_path):
        with open(senders_data_path, 'r') as file:
            data = json.load(file)
            if data:
                print("Local data found. Processing...")
                data_processor.filter_noreply_emails(senders_data_path, noreply_senders_path)
                email_fetcher.delete_emails_from_senders(service, 'me', noreply_senders_path)
                return

    print("No local data found or file is empty. Fetching data...")
    
    senders = email_fetcher.get_sender_info(service, 'me')  # Use the function from the new module
    with open(senders_data_path, 'w') as f:
        json.dump(senders, f, indent=2)

    print("\nSender information has been saved to senders_data.json")
    data_processor.filter_noreply_emails(senders_data_path, noreply_senders_path)
    email_fetcher.delete_emails_from_senders(service, 'me', noreply_senders_path)

if __name__ == '__main__':
    main()
