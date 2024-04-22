import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import concurrent.futures

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def process_message_data(message_data):
    # Extract and process the sender information from the message payload
    msg_headers = message_data.get('payload', {}).get('headers', [])
    sender = next((header['value'] for header in msg_headers if header['name'] == 'From'), None)
    return sender

def get_sender_info(service, user_id, max_results=1000):
    print("Fetching messages from the inbox...")

    senders = {}
    page_token = None
    messages_processed = 0

    while messages_processed < max_results:
        # Adjust maxResults if we're nearing the max_results limit
        current_max_results = min(100, max_results - messages_processed)

        # Fetch messages from the user's inbox with page token
        results = service.users().messages().list(
            userId=user_id, labelIds=['INBOX'],
            pageToken=page_token, maxResults=current_max_results).execute()
        messages = results.get('messages', [])
        page_token = results.get('nextPageToken')

        if not messages:
            print("No more messages found.")
            break

        # Fetch all message details
        message_data_list = [service.users().messages().get(userId=user_id, id=message['id'], format='metadata', metadataHeaders=['From']).execute() for message in messages]

        # Use ThreadPoolExecutor to process the data concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sender in executor.map(process_message_data, message_data_list):
                if sender:
                    senders[sender] = senders.get(sender, 0) + 1

        messages_processed += len(messages)
        if not page_token or messages_processed >= max_results:
            print("No more messages to process or reached max_results limit.")
            break

    print("Finished processing messages.")
    return senders

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
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
