import os.path
import time
import random
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import concurrent.futures
import data_processor

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def exponential_backoff(n):
    """Calculate sleep time in seconds for exponential backoff."""
    return (2 ** n) + random.uniform(0, 1)

def process_message_data(message_data):
    # Extract and process the sender information from the message payload
    msg_headers = message_data.get('payload', {}).get('headers', [])
    sender = next((header['value'] for header in msg_headers if header['name'] == 'From'), None)
    return sender

def get_sender_info(service, user_id):
    print("Fetching messages from the inbox...")
    senders = {}
    page_token = None
    attempt = 0

    while True:
        try:
            results = service.users().messages().list(userId=user_id, labelIds=['INBOX'],
                                                      pageToken=page_token, maxResults=500).execute()
            messages = results.get('messages', [])
            page_token = results.get('nextPageToken')

            if not messages:
                print("\nNo more messages found.")
                break

            print(f"\nProcessing batch of {len(messages)} messages...")

            for i, message in enumerate(messages):
                print(f"\rCurrent message: {i + 1}/{len(messages)}", end='', flush=True)
                full_message = service.users().messages().get(userId=user_id, id=message['id'], format='metadata', metadataHeaders=['From']).execute()
                payload = full_message.get('payload')
                if payload:
                    headers = payload.get('headers', [])
                    sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), None)
                    if sender:
                        senders[sender] = senders.get(sender, 0) + 1
                else:
                    print("No payload available for message ID:", message['id'])

            # Reset attempt counter after a successful batch
            attempt = 0

        except Exception as error:
            print(f"An error occurred: {error}")
            attempt += 1
            sleep_time = exponential_backoff(attempt)
            print(f"\nRetrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            if attempt > 5:  # Limit the number of retries to prevent infinite loops
                print("\nMaximum retry attempts reached, stopping...")
                break

        if not page_token:
            print("\nNo more messages to process.")
            break

        # Save intermediate results after processing each batch
        with open('senders_data_partial.json', 'w') as f:
            json.dump(senders, f, indent=2)

    print("\nFinished processing messages.")
    return senders

def main():
    if os.path.exists('senders_data.json'):
        with open('senders_data.json', 'r') as file:
            data = json.load(file)
            if data:  # Check if the data is not empty
                print("Local data found. Processing...")
                data_processor.filter_noreply_emails('senders_data.json', 'noreply_senders.json')
                return

    print("No local data found or file is empty. Fetching data...")
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
    senders = get_sender_info(service, 'me')

    # Save sender information to a JSON file
    with open('senders_data.json', 'w') as f:
        json.dump(senders, f, indent=2)

    print("\nSender information has been saved to senders_data.json")
    data_processor.filter_noreply_emails('senders_data.json', 'noreply_senders.json')

if __name__ == '__main__':
    main()
