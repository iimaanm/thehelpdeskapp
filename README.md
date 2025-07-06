# Help Desk Web Application - README

## Overview
This is a Flask-based web application for managing help desk tickets in an organization. It supports two user roles: Admin (full CRUD on all tickets) and User (CRU on their own tickets). The app uses SQLite for data storage and Bootstrap for a modern UI.

## Features
- User registration and login
- Role-based access (Admin/User)
- Ticket creation, viewing, editing, and (admin-only) deletion
- Department assignment for users
- Flash messages and form validation
- Responsive, user-friendly interface

## Dependencies
- Python 3.x
- Flask
- Flask-Login
- Flask-SQLAlchemy
- Werkzeug
- Bootstrap (via CDN)

## Setup Instructions
1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Initialize the database:**
   ```sh
   python main.py
   ```
   (This will create the database if it doesn't exist.)
5. **Seed the database with test data:**
   ```sh
   python seed_db.py
   ```
6. **Run the application:**
   ```sh
   python main.py
   ```
7. **Access the app:**
   Open your browser and go to [http://localhost:5000](http://localhost:5000)

## Entity Relationship Diagram (ERD)
- **User** (id, username, first_name, password, role, department_id)
- **Ticket** (id, title, description, date, status, user_id, priority)
- **Department** (id, name)

Relationships:
- User → Department (many-to-one)
- Ticket → User (many-to-one)

(See included ERD image or generate with draw.io)

## User Manual
### Login/Signup
- Register as a new user or log in with your credentials.
- Choose your role (Admin/User) and department during signup.

### Dashboard
- **Admin:** View all tickets, edit or delete any ticket, see user info.
- **User:** View only your tickets, edit your tickets.

### Create Ticket
- Click "Create Ticket" on the home page or dashboard.
- Fill in the title and description, then submit.

### Edit Ticket
- Click "Edit" next to a ticket in the dashboard.
- Update the fields and save changes.

### Delete Ticket
- (Admin only) Click "Delete" next to a ticket in the dashboard. Confirm deletion.

### Logout
- Click the "Logout" link in the navigation bar.

## Screenshots
(See the screenshots folder for annotated images of the running application.)

---
For more details, see the report and ERD included in the project files.

## Setup

1. Create a virtual environment:
   python -m venv .venv

2. Activate the environment:
   - On Windows: .venv\Scripts\activate
   - On macOS/Linux: source .venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt
