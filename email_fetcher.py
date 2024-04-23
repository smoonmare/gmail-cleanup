import os
import json
from googleapiclient.discovery import build

def exponential_backoff(n):
    import random
    """Calculate sleep time in seconds for exponential backoff."""
    return (2 ** n) + random.uniform(0, 1)

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
            if attempt > 5:
                print("\nMaximum retry attempts reached, stopping...")
                break

        if not page_token:
            print("\nNo more messages to process.")
            break

        # Save intermediate results after processing each batch
        partial_data_path = os.path.join('data', 'senders_data_partial.json')
        with open(partial_data_path, 'w') as f:
            json.dump(senders, f, indent=2)

    print("\nFinished processing messages.")
    return senders
