InvoSmart

AI-powered invoice automation system built with Django and Google Cloud Document AI. Developed as a Capstone Project (IS498/IS499) — Information Systems Department, King Saud University.

Overview

InvoSmart automates invoice processing for organizations with multiple branches. Users upload an invoice (PDF/image), and the system extracts key fields automatically — invoice number, supplier, amount, date — matches it against Purchase Orders, and routes it through a review workflow.

Features


AI Data Extraction — Google Document AI extracts invoice fields with per-field confidence scores
Role-Based Access — System Admin, Branch Manager, and Accounting Staff roles with scoped permissions
Purchase Order Matching — Automatic linking and remaining-balance tracking
Notifications — Alerts on processing failures and high error rates (>20% in 24h)
Branch Dashboards — Real-time stats per branch (pending, reviewed, errors)


Tech Stack


Backend: Python 3.12, Django 5.1
Database: SQLite (dev)
AI/OCR: Google Cloud Document AI
Frontend: Django Templates, Bootstrap 5


Setup

bashgit clone https://github.com/YOUR_USERNAME/invosmart.git
cd invosmart
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

Environment Variables

Create a .env file in the project root:

envSECRET_KEY=your-secret-key
DEBUG=True
DOCUMENT_AI_PROJECT_ID=your-project-id
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
DOCUMENT_AI_LOCATION=us
GOOGLE_APPLICATION_CREDENTIALS=google-credentials.json


.env and google-credentials.json are gitignored and must never be committed.



Project Structure

invosmart/
├── core/             # Project settings & root URLs
├── users/            # Authentication & roles
├── invoices/         # Invoices & Purchase Orders
├── branches/         # Branch management & dashboards
├── notifications/    # Notification system
└── manage.py

Author

Mohammed Alharbi — Information Systems, King Saud University
Supervised by Dr. Ahmed Al-Hamid
