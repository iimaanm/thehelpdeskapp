# Help Desk Web Application - README

## Application Summary

### Problem Statement
Organizations require efficient ticket management systems to handle employee support requests, technical issues, and departmental queries. Traditional email-based support systems lack proper tracking, prioritization, and role-based access control.

### Application Scope
This Flask-based web application provides a comprehensive help desk solution for university environments. It enables users to submit, track, and manage support tickets while providing administrators with full oversight capabilities. The system supports role-based access control, ensuring proper security and workflow management.

### Core Features
- **User Management**: Registration, authentication, and role assignment (Admin/User)
- **Ticket Operations**: Create, read, update, and delete (CRUD) functionality with role restrictions
- **Department Integration**: User-department associations for better organization
- **Security**: Form validation, session management, and access control
- **User Interface**: Responsive Bootstrap design with intuitive navigation

### Technical Architecture
**Backend**: Python Flask framework with SQLAlchemy ORM for database operations
**Database**: SQLite with 3-table relational design (User, Ticket, Department)
**Frontend**: HTML5 templates with Jinja2, Bootstrap CSS, and JavaScript
**Authentication**: Flask-Login for session management and user authentication

### Dependencies
- **Core**: Python 3.x, Flask, Flask-Login, Flask-SQLAlchemy
- **Security**: Werkzeug for password hashing
- **UI**: Bootstrap 5 (CDN), custom CSS and JavaScript
- **Testing**: pytest for backend testing, Jest for frontend testing

### Design Documents
The application follows MVC architecture with clear separation of concerns:
- **Models** (`models.py`): Database schema and relationships
- **Views** (`views.py`, `auth.py`): Route handlers and business logic  
- **Templates**: HTML pages with Jinja2 templating
- **Static Assets**: CSS, JavaScript, and styling components

The system uses a 3-table relational database design ensuring data integrity and efficient queries. Role-based access control is implemented throughout both backend routes and frontend templates.

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

## JavaScript Testing (Frontend)

If you want to run tests for the JavaScript files (such as `index.test.js` in `helpdeskapp/static/`), follow these steps:

1. Open a terminal and navigate to the static directory:
   ```sh
   cd helpdeskapp/static
   ```
2. Install Node.js dependencies (only needed once):
   ```sh
   npm install
   ```
3. Run the tests:
   ```sh
   npm test
   ```

This uses [Jest](https://jestjs.io/) as the test runner. You can add more `.test.js` files in the same folder to expand your frontend test coverage.

## Python Testing (Backend)

To run all Python tests (for the backend Flask app), use the following instructions:

1. Open a terminal and navigate to the project root directory (where `main.py` and `helpdeskapp/` are located):
   ```sh
   cd /Users/iimaan.mohamed/New\ Software\ \&\ Agile\ project
   ```
2. Make sure your virtual environment is activated and dependencies are installed.
3. Run all tests with pytest:
   ```sh
   pytest helpdeskapp/
   ```

This will automatically discover and run all test files in the `helpdeskapp/` directory that start with `test_`.
