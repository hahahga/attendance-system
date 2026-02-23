# Enterprise Employee Attendance Management System

## Project Overview
A comprehensive attendance management system with face recognition, leave management, and statistical analysis capabilities.

## Features
- **Face Recognition**: Clock in/out using facial recognition
- **Attendance Tracking**: Real-time attendance monitoring
- **Leave Management**: Apply and approve leave requests
- **Statistical Reports**: Generate attendance statistics
- **User Management**: Role-based access control
- **Notifications**: Real-time notifications system

## Project Structure
```
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Core configurations
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── utils/        # Utility functions
├── static/           # CSS, JS, images
├── templates/        # HTML templates
└── config/           # Environment configurations
```

## Key Technologies
- FastAPI (Backend Framework)
- SQLAlchemy (ORM)
- Jinja2 (Templates)
- Face Recognition API
- SQLite/PostgreSQL Database
- Bootstrap (Frontend)

## API Endpoints
- `/api/v1/auth` - Authentication
- `/api/v1/attendance` - Attendance management
- `/api/v1/leave` - Leave management
- `/api/v1/users` - User management
- `/api/v1/statistics` - Statistical reports

## Requirements
- Python 3.8+
- FastAPI
- SQLAlchemy
- face-recognition
- uvicorn

## Installation
```bash
pip install -r requirements.txt
python run.py
```

## Usage
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the application at `http://localhost:8000`
