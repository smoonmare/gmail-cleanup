import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_sender_info(service, user_id, max_results=1000):
    print("Fetching messages from the inbox...")

    senders = {}
    page_token = None
    message_count = 0

    while message_count < max_results:
        # Fetch messages from the user's inbox with page token
        results = service.users().messages().list(userId=user_id, labelIds=['INBOX'], pageToken=page_token, maxResults=100).execute()
        messages = results.get('messages', [])
        page_token = results.get('nextPageToken')

        if not messages:
            print("No more messages found.")
            break

        print(f"Processing batch of {len(messages)} messages... might take a while")
        for message in messages:
            msg = service.users().messages().get(userId=user_id, id=message['id'], format='metadata', metadataHeaders=['From']).execute()
            msg_headers = msg.get('payload', {}).get('headers', [])
            sender = next(header['value'] for header in msg_headers if header['name'] == 'From')
            senders[sender] = senders.get(sender, 0) + 1
            message_count += 1

            if message_count >= max_results:
                break

        if not page_token:
            print("No more messages to process.")
            break

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
    senders = get_sender_info(service, 'me', max_results=1000)
    
    # Print sender information
    for sender, count in senders.items():
        print(f"Sender: {sender}, Messages: {count}")

if __name__ == '__main__':
    main()
