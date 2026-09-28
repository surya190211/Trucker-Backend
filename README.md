# 🚚 Trucker Logbook - Backend

The core API and database logic for the digital Trucker Logbook application. It provides robust Django REST Framework endpoints to capture, validate, and securely store driver daily logs adhering to FMCSA rules.

## ✨ Features
- **FMCSA Compliance Validation:** Automatically blocks overlapping time entries and enforces precisely 24 hours of total log coverage.
- **Custom Nested Serializers:** Employs advanced Django bulk creation to atomically save a `DailyLog` along with multiple `StatusEntry` blocks in a single, high-efficiency database transaction.
- **Relational Integrity:** Enforces strong constraints suitable for auditing compliance data.
- **CORS Configured:** Setup to securely communicate with the remote React frontend.

## 🚀 Tech Stack
- Python
- Django
- Django REST Framework (DRF)
- SQLite (Development & PythonAnywhere Production)
- django-cors-headers

## 🛠️ Local Development
1. Clone the repository: `git clone https://github.com/surya190211/Trucker-Backend.git`
2. Create and activate a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install django djangorestframework django-cors-headers`
4. Run migrations: `python manage.py migrate`
5. Start the server: `python manage.py runserver`

## 🌍 Production
This backend is currently optimized to be hosted on [PythonAnywhere](https://www.pythonanywhere.com/). 
When pushing to enterprise production, remember to swap SQLite with PostgreSQL and add your specific frontend domain to `CORS_ALLOWED_ORIGINS` to maintain strict origin security.
