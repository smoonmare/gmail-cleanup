import json

def filter_noreply_emails(input_filename, output_filename):
    """
    Filters out emails that contain 'norepy' variations and saves then to a new JSON file.
    """
    with open(input_filename, 'r') as file:
        data = json.load(file)

        # Prepare dictionary for noreply emails
        noreply_emails = {}

        # Check for common noreply variations
        noreply_variants = ['noreply', 'no-reply', 'no_reply']
        for email, count in data.items():
            if any(variant in email.lower() for variant in noreply_variants):
                noreply_emails[email] = count
        
        # Save the filtered data to a new JSON file
        with open(output_filename, 'w') as file:
            json.dump(noreply_emails, file, indent=2)

            print(f"Noreply emails have been saved to {output_filename}")

# Makes it executable directly in terminal for testing
if __name__ == "__main__":
    filter_noreply_emails('senders_data.json', 'noreply_senders.json')