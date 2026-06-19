InvoSmart

AI-powered invoice automation system built with Django and Google Cloud Document AI.


Developed as a Capstone Project (IS498/IS499) — Information Systems Department, King Saud University.




Overview

InvoSmart is a system designed to automate invoice processing for organizations with multiple branches. Manually reviewing and entering invoice data is slow and error-prone, especially at scale. InvoSmart solves this by using Google Document AI to automatically extract invoice data (invoice number, supplier, amount, date), matching it against Purchase Orders, and routing it through a structured review and approval workflow.


Key Features


AI-Powered Data Extraction — Upload an invoice (PDF/JPG/PNG) and the system extracts all key fields automatically, each with a confidence score
Role-Based Access Control (RBAC) — Three roles: System Admin, Branch Manager, and Accounting Staff, each with scoped permissions
Smart Purchase Order Matching — Invoices are automatically linked to matching POs; remaining balances update automatically, and POs close when fully used
Notification System — Instant alerts on processing failures, and automatic warnings to branch managers when the error rate exceeds 20% in the last 24 hours
Role-Specific Dashboards — Each role sees relevant stats: total invoices, pending, reviewed, and errors
Multi-Branch Support — Each branch has isolated data, users, and purchase orders



Tech Stack

CategoryTechnologyBackendPython 3.12, Django 5.1DatabaseSQLite (development)AI/OCRGoogle Cloud Document AIFrontendDjango Templates, Bootstrap 5File ProcessingPillow, pdf2image


Installation

Prerequisites


Python 3.10+
A Google Cloud account with Document AI API enabled
Git


Steps

bash# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/invosmart.git
cd invosmart

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.example .env
# then edit .env with your own values

# 6. Apply migrations
python manage.py migrate

# 7. Create an admin user
python manage.py createsuperuser

# 8. Run the development server
python manage.py runserver

Open your browser at: http://127.0.0.1:8000/


Environment Variables (.env)

Create a .env file in the project root:

envSECRET_KEY=your-secret-key-here
DEBUG=True

DOCUMENT_AI_PROJECT_ID=your-project-id
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
DOCUMENT_AI_LOCATION=us
GOOGLE_APPLICATION_CREDENTIALS=google-credentials.json

Note: Never commit .env or google-credentials.json to GitHub. Make sure both are listed in .gitignore.


Roles and Permissions

RolePermissionsSystem AdminFull system access: manage users, branches, and all dataBranch ManagerReview branch invoices, manage branch staff, generate reportsAccounting StaffUpload invoices and review extracted data before approval


How It Works


Upload — Accounting staff uploads an invoice file (PDF/image)
AI Processing — Google Document AI extracts the data; the system attempts to auto-match it with an existing Purchase Order
Review — Staff reviews extracted fields (with confidence scores), corrects any errors, and checks the PO match
Approval — Once reviewed, the invoice status updates and the matched PO's remaining balance is adjusted (auto-closing if fully used)
Error Handling — If extraction fails, the invoice is flagged as error and a notification is sent; if the branch's error rate exceeds 20% in 24 hours, the Branch Manager is alerted



Project Structure

invosmart/
├── core/                  # Project settings & root URL config
├── users/                 # Authentication, roles, profiles
├── invoices/              # Invoices & Purchase Orders
├── branches/              # Branch management & dashboards
├── notifications/         # Notification system
├── media/                 # Uploaded invoices (not committed)
├── requirements.txt
└── manage.py


Security


Passwords hashed with PBKDF2 + SHA256 (never stored in plain text)
CSRF protection on all forms
Role-based data isolation (users only access their own branch's data)
Secrets (API keys, credentials) kept out of version control via .env



Future Enhancements


REST API for mobile app integration
Batch invoice processing
Export reports to Excel/PDF
Integration with accounting platforms (e.g., QuickBooks)
Two-factor authentication (2FA)



Project Info


Student: Mohammed Alharbi
Supervisor: Dr. Ahmed Al-Hamid
Department: Information Systems, King Saud University
Course: IS498/IS499 — Capstone Project



License

This project was developed for academic purposes as part of a university graduation requirement.
