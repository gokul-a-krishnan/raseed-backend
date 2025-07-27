# Raseed Backend - Receipt Processing System

## Project Overview
A Flask backend application for processing receipts and invoices, with features including:
- REST API for receipt management
- Intelligent invoice processing using Google's Gemini AI
- Email listener for automatic invoice processing from PDF attachments
- Firestore database integration

## Installation

### Prerequisites
- Python 3.11 or higher
- Google Cloud account (for Firestore)
- Gemini API key
- IMAP-enabled email account

### Setup Steps
1. Clone the repository:
```bash
git clone https://github.com/gokul-a-krishnan/raseed-backend.git
cd raseed-backend
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -e .
```

4. Set up service account:
- Create a service account in Google Cloud Console
- Download the JSON key file
- Save as `service-account.json` in project root

5. Create `.env` file:
```bash
touch .env
```

Add these required environment variables:
```env
GEMINI_API_KEY=your_api_key_here
MAIL_HOST=your_imap_server
MAIL_PORT=993
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
```

## Configuration

### Firestore Setup
1. Enable Firestore in Google Cloud Console
2. Create a database in Native mode
3. Create a collection named 'receipt'

### Email Configuration
- Ensure your email account allows IMAP access
- Configure the email credentials in `.env`

## Running the Application

### Main Application
```bash
python app.py
```
- Runs on http://localhost:8180

### Email Listener
```bash
python email_listener.py
```
- Runs continuously, checking for new emails every 60 seconds

## API Documentation

### Receipt Endpoints (prefix: /receipt)
- `POST /add-receipts` - Add a new receipt
- `GET /get-all` - Get all receipts
- `GET /get-by-id/<id>` - Get receipt by ID
- `PATCH /update-receipts/<id>` - Update receipt

### Intelligent Processing (prefix: /intelligent)
- `POST /categorize-receipts` - Process invoice files and categorize items

## Application Flow

1. **Receipt Processing**:
   - API receives receipt data → Stores in Firestore
   - Returns structured receipt information

2. **Email Processing**:
   - Listener checks for new emails with PDF attachments
   - Extracts invoice data using Gemini AI
   - Stores processed data in Firestore

3. **Intelligent Categorization**:
   - Accepts image/PDF files
   - Uses Gemini to extract structured data
   - Returns categorized items with prices

## Troubleshooting

### Common Issues
1. **Firestore Connection Errors**:
   - Verify service account JSON is correct
   - Check Firestore database is created

2. **Gemini API Errors**:
   - Verify API key is valid
   - Check quota limits

3. **Email Processing Failures**:
   - Verify IMAP settings
   - Check email credentials

### Logging
Application logs important events to stdout:
- Successful operations
- Error conditions
- Processing status

## License
[MIT License](LICENSE)
