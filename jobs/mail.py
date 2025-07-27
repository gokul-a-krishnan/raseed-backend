from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path
from imapclient import IMAPClient
from dotenv import load_dotenv

import email

import os

load_dotenv(override=True)

MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_PORT = int(os.getenv("MAIL_PORT", 993))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")


def save_attachment(attachment, from_email, msg_id, filename):
    """Save email attachment to structured directory"""
    # Sanitize from_email for filesystem
    from_dir = "".join(c for c in from_email if c.isalnum()
                       or c in ('@', '.', '_', '-'))

    # Create directory structure
    attach_dir = Path.cwd() / "attachments" / from_dir / str(msg_id)
    attach_dir.mkdir(parents=True, exist_ok=True)

    # Save attachment
    with open(attach_dir / filename, 'wb') as f:
        f.write(attachment)


def listen_for_emails():
    while True:
        print("Checking for new emails...")
        try:
            with IMAPClient(MAIL_HOST, port=MAIL_PORT) as client:
                client.login(MAIL_USERNAME, MAIL_PASSWORD)
                client.select_folder('INBOX')
                # Search for unseen messages
                messages = client.search(['UNSEEN'])
                for message_id, data in client.fetch(messages, ['RFC822', 'BODY[TEXT]']).items():
                    # Parse email message
                    message = email.message_from_bytes(data[b'RFC822'])

                    # Get email details
                    from_ = message['From']
                    subject = message['Subject']
                    date = message['Date']

                    # Get body text and handle attachments
                    body = ""
                    attachments = []
                    if message.is_multipart():
                        for part in message.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(
                                part.get("Content-Disposition"))

                            if "attachment" in content_disposition:
                                filename = part.get_filename()
                                if filename:
                                    payload = part.get_payload(decode=True)
                                    save_attachment(
                                        payload, from_, message_id, filename)
                                    attachments.append(filename)
                            elif content_type == 'text/plain':
                                body = part.get_payload(
                                    decode=True).decode('utf-8')
                    else:
                        body = message.get_payload(decode=True).decode('utf-8')

                    # Print email details
                    print("\n--- New Email ---")
                    print(f"From: {from_}")
                    print(f"Date: {date}")
                    print(f"Subject: {subject}")
                    print(f"Body:\n{body}\n")
                    if attachments:
                        print("Attachments saved:")
                        for att in attachments:
                            print(f"- {att}")

        except Exception as e:
            print(f"Error: {e}")
            continue


sched = BackgroundScheduler()


sched.add_job(listen_for_emails, 'interval', minutes=.3,
              id='email_listener', replace_existing=True)


def start_scheduler():
    """Start the email listener scheduler"""
    sched.start()
    print("Email listener started.")
