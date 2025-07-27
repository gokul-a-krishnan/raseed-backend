

import os
import time
import email
import fitz  # PyMuPDF
import json
import google.generativeai as genai
from imapclient import IMAPClient
from dotenv import load_dotenv
from google.cloud import firestore
from datetime import datetime
import os
from uuid import uuid4

load_dotenv(override=True)

MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_PORT = int(os.getenv("MAIL_PORT", 993))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"


def add_to_receipt_collection(invoice_dict):
    """Add parsed invoice to Firestore collection."""
    db = firestore.Client()
    collection_name = 'receipt'
    try:
        # Convert date string to Firestore Timestamp
        date = invoice_dict['billing_date']
        print(f"before: {invoice_dict['items']}")

        invoice_dict["items"] = [{'item': k, 'price': v}
                                 for k, v in invoice_dict['items'].items()]
        print(f"after: {invoice_dict['items']}")
        # Create document
        obj = {
            'id': uuid4().hex,
            'date': date,
            'items': invoice_dict['items'],
            "bill_value": invoice_dict["total"],
            "biller_name": invoice_dict["biller_name"],
        }

        doc_ref = db.collection(collection_name).add(obj)
    except Exception as e:
        print(f"Error adding document: {str(e)}")


def process_invoice_emails():
    # Setup Gemini
    genai.configure(api_key="")
    model = genai.GenerativeModel("gemini-1.5-pro")

    # Define prompt
    prompt = """You are an expert invoice analyzer.

From the invoice image, extract the following details in JSON format:

```json
{
  "biller_name": "<name of the person/shop/organization or entity billed>",
  "billing_date": "<date of the bill in YYYY-MM-DD format if available>",
  "category": "<automatically determined category, such as grocery, rent, utility, food, etc.>",
  "items": {
    "<item name>": <price>
  },
  "total": <total amount>
}
```"""

    while True:
        print("Checking for new emails...")
        try:
            with IMAPClient(MAIL_HOST, port=MAIL_PORT) as client:
                client.login(MAIL_USERNAME, MAIL_PASSWORD)
                client.select_folder('INBOX')
                messages = client.search(['UNSEEN'])

                for message_id, data in client.fetch(messages, ['RFC822']).items():
                    message = email.message_from_bytes(data[b'RFC822'])
                    from_ = message['From']
                    subject = message['Subject']
                    date = message['Date']
                    attachments_processed = []

                    if message.is_multipart():
                        for part in message.walk():
                            content_disposition = str(
                                part.get("Content-Disposition"))
                            if "attachment" in content_disposition:
                                filename = part.get_filename()
                                if filename and filename.lower().endswith(".pdf"):
                                    payload = part.get_payload(decode=True)

                                    try:
                                        with fitz.open(stream=payload, filetype="pdf") as doc:
                                            full_text = "\n".join(
                                                [page.get_text() for page in doc]).lower()
                                            if "invoice" in full_text or "bill" in full_text:
                                                # Process PDF with Gemini
                                                gemini_input = [
                                                    prompt, {"mime_type": "application/pdf", "data": payload}]
                                                response = model.generate_content(
                                                    gemini_input)
                                                json_str = response.text.strip(
                                                    "```json").strip("```").strip()
                                                invoice_dict = json.loads(
                                                    json_str)

                                                # Convert items list to dict
                                                if isinstance(invoice_dict.get("items"), list):
                                                    items_dict = {}
                                                    for entry in invoice_dict["items"]:
                                                        key = entry.get(
                                                            "item", "").strip().replace("\n", " ")
                                                        value = float(
                                                            entry.get("price", 0))
                                                        items_dict[key] = value
                                                    invoice_dict["items"] = items_dict

                                                print(
                                                    "\n🧾 Parsed Invoice Dictionary:")
                                                print(json.dumps(
                                                    invoice_dict, indent=2))
                                                attachments_processed.append(
                                                    filename)
                                                add_to_receipt_collection(
                                                    invoice_dict)

                                    except Exception as e:
                                        print(
                                            f"❌ Error processing PDF {filename}: {e}")

                    print("\n--- New Email ---")
                    print(f"From: {from_}")
                    print(f"Date: {date}")
                    print(f"Subject: {subject}")
                    if attachments_processed:
                        print("✅ Processed Attachments:")
                        for att in attachments_processed:
                            print(f"- {att}")
                    else:
                        print("📭 No invoice-related PDF attachments found.")

        except Exception as e:
            print(f"🛑 Error: {e}")
            time.sleep(10)
            continue

        time.sleep(60)


# Run the function
if __name__ == "__main__":
    process_invoice_emails()
