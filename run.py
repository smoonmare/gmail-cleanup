import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_sender_info(service, user_id):
    print("Fetching messages from the inbox...")
    # Fetch messages from the user's inbox
    results = service.users().messages().list(userId=user_id, labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    senders = {}

    if messages:
        total_messages = len(messages)
        print(f"Processing {total_messages} messages...")
        for message in messages:
            msg = service.users().messages().get(userId=user_id, id=message['id'], format='metadata', metadataHeaders=['From']).execute()
            msg_headers = msg.get('payload', {}).get('headers', [])
            sender = next(header['value'] for header in msg_headers if header['name'] == 'From')
            if sender in senders:
                senders[sender] += 1
            else:
                senders[sender] = 1

    print("Finished processing messages.")
    return senders

def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    
    # Collect all sender information
    senders = get_sender_info(service, 'me')
    
    # Print sender information
    for sender, count in senders.items():
        print(f"Sender: {sender}, Messages: {count}")

if __name__ == '__main__':
    main()
