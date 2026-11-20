# Library Management System

## 1. Project Overview

The **Library Management System (LMS)** is a desktop application designed to support library management activities, including book management, user management, borrowing and returning books, fine management, and report generation.

The system provides two main user roles: **Admin** and **Reader**.

The project is developed as part of the Software Engineering course, covering software analysis, design, implementation, and testing.

## 2. Project Objectives

- Develop a user-friendly library management application.
- Apply Object-Oriented Programming (OOP) principles.
- Implement the Model-View-Controller (MVC) architecture.
- Manage library data using MySQL.
- Automate book borrowing and returning processes.
- Calculate overdue fines and support test payments through MoMo Sandbox.
- Ensure system reliability through software testing.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| CustomTkinter | Graphical User Interface (GUI) |
| MySQL 8 | Database management |
| mysql-connector-python | Python–MySQL connection |
| MVC | Software architecture |
| Pytest | Unit and integration testing |
| Git & GitHub | Version control |
| Docker Compose | Isolated MySQL for integration tests |
| VS Code | Development environment |

## 4. System Features

### 4.1 Admin Features

- Sign in and sign out.
- Find, create, edit, lock, activate, and delete eligible reader accounts.
- Add, edit, delete, and search books. Assign categories and manage available stock.
- Approve or reject borrowing and renewal requests.
- Confirm returns per copy and record the actual return date and condition.
- Review borrowing records and overdue fines, and record in-person payments.
- View statistics and export reports to CSV. Borrowing and return reports also support Excel and PDF.

### 4.2 Reader Features

- Register, sign in, and request a password reset code by email.
- Browse the catalog and search by title, author, book ID, or category. View total and available copies.
- View and edit personal information.
- Request loans, returns, and renewals. Track their status in the app.
- View borrowing and return history and in-app updates.
- View overdue days and fines. Pay an eligible fine through MoMo Sandbox and check its status.

## 5. Business Rules

1. A reader may have at most **3 copies on loan at a time**. The standard loan period is **30 days**.
2. The system checks account eligibility and availability before a loan is requested and approved. An Admin approves or rejects the request.
3. The current renewal workflow allows one approved extension per active, non-overdue loan. The requested extension may be up to 30 days. An Admin reviews the request.
4. An Admin confirms returns and records each returned copy. A return can be recorded in parts.
5. A copy returned late incurs **2,000 VND per day**, based on its actual return date. The fine is finalized when the return is complete. The reader can then pay through MoMo Sandbox.
6. An online payment is recorded as paid after the app verifies it through MoMo. An Admin may record an in-person payment when there is no pending MoMo order.
7. Administrative screens require the Admin role. Locked or inactive accounts cannot sign in. Accounts with loan history can be locked to preserve their records.

## 6. Software Architecture

The system follows the **Model-View-Controller (MVC)** architecture with additional Service and Repository layers.

- **Model:** Represents system entities and business data.
- **View:** Provides graphical interfaces using CustomTkinter.
- **Controller:** Handles user interactions and coordinates application operations.
- **Service:** Implements business rules and validation.
- **Repository:** Performs database operations with MySQL.

### Main Classes

The implemented models include User, Admin, Reader, Book, and Fine. Admin and
Reader inherit from User. The borrowing repository and service handle borrowing
records and per-copy details.

## 7. Database Design

The MySQL schema contains the following core tables.

| Table | Description |
|---|---|
| users | Login identities, roles, account status, and contact information |
| admins | Administrator profiles |
| readers | Reader profiles and membership expiry |
| books | Catalog titles, categories, and inventory |
| borrowing_records | Loan dates, status, and renewal count |
| borrowing_details | Individual borrowed copies and return details |
| fines | Overdue fines and payment status |

Supporting tables are password_reset_codes, renewal_requests, and fine_momo_orders.
The first two are included in schema.sql. The MoMo order table is added by
migration 002.

An Admin or Reader profile links to one user account. A reader can have several
loans. Each loan can contain several copy records, each linked to a book title.

Users sign in with their **username and password**. Email is stored as contact
information and is used for password recovery. The legacy loan dates are stored
as ISO strings in YYYY-MM-DD format. The supporting tables also use native MySQL
date and timestamp columns.

## 8. Project Structure

~~~text
main.py                  Desktop app entry point
app/models/              Domain models
app/views/               CustomTkinter screens
app/controllers/         Application entry points for user actions
app/services/            Business rules and integrations
app/repositories/        MySQL data access
app/database/            MySQL connection
sql/schema.sql           Fresh database schema
sql/seed.sql             Optional sample book catalog
sql/migrations/          Additive database changes
tests/                   Automated tests
tests/integration/       Isolated MySQL fixtures and Compose configuration
docs/                    Project documentation and supporting material
~~~

## 9. Installation and Setup

Install Python with Tkinter, Git, and MySQL 8. Docker Desktop is needed for the
isolated integration tests in section 10.

### 9.1 Install the app on Windows

Run these commands in PowerShell.

~~~powershell
git clone https://github.com/nhthu0/Library-Management-System.git
cd Library-Management-System
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
~~~

If .env already exists, keep it and update the required variables. Set DB_HOST,
DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD to match your MySQL instance.
Keep passwords and service keys in your local .env.

### 9.2 Initialize or update MySQL

- **Fresh installation.** Run [schema.sql](sql/schema.sql) as a MySQL
  administrator. It creates and selects library_management. Optionally run
  [seed.sql](sql/seed.sql) once to add sample books. Then run
  [migration 002](sql/migrations/002_fine_momo_orders.sql) in library_management
  to enable MoMo. The fresh schema already includes the tables from migration 001.
- **Existing installation.** Select the database configured in your app and
  apply [migration 001](sql/migrations/001_password_reset_and_renewal.sql) and
  [migration 002](sql/migrations/002_fine_momo_orders.sql) with a MySQL
  administrator. Use these additive migrations to keep existing data.
  **Do not import schema.sql over an existing installation.** It contains
  DROP TABLE statements and explicitly selects library_management.

The app account needs SELECT, INSERT, UPDATE, and DELETE on the database. When
creating a local app account, replace the example password in the SQL below with
the password you put in .env. Run this as a MySQL administrator.

~~~sql
CREATE USER IF NOT EXISTS 'library_user'@'localhost' IDENTIFIED BY '<local-app-password>';
GRANT SELECT, INSERT, UPDATE, DELETE ON library_management.* TO 'library_user'@'localhost';
~~~

### 9.3 Create the first Admin

The seed file only adds sample books. Save the following script as
create_admin.local.py in the project directory. It reads the app's connection
settings and prompts for a password without echoing it. The user account and
Admin profile are created in one transaction.

~~~python
from getpass import getpass
import bcrypt
from app.database.connection import get_connection

username = input("Admin username: ").strip()
name = input("Full name: ").strip()
email = input("Email: ").strip()
password = getpass("Admin password: ")
if not username or not name or "@" not in email or not 8 <= len(password.encode("utf-8")) <= 72:
    raise SystemExit("Enter a username, full name, valid email and an 8-72 byte password.")
if password != getpass("Confirm password: "):
    raise SystemExit("Passwords do not match.")
password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
with get_connection() as db:
    db.start_transaction()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (username, full_name, email, password, role, account_status) "
            "VALUES (%s, %s, %s, %s, 'Admin', 'Active')",
            (username, name, email, password_hash),
        )
        cursor.execute("INSERT INTO admins (userID) VALUES (%s)", (cursor.lastrowid,))
    db.commit()
print("Admin account created.")
~~~

Run it once against the intended database, then remove the temporary script.
Reader accounts can be registered from the app.

~~~powershell
.\.venv\Scripts\python.exe .\create_admin.local.py
~~~

### 9.4 Configure email and Sandbox payments

- **Password reset.** Set SMTP_HOST, SMTP_PORT, and SMTP_FROM in .env.
  Set SMTP_USERNAME and SMTP_PASSWORD when the SMTP server requires login.
  The app connects with STARTTLS.
- **MoMo Sandbox.** Set MOMO_PARTNER_CODE, MOMO_ACCESS_KEY, MOMO_SECRET_KEY,
  MOMO_REDIRECT_URL, and MOMO_IPN_URL in .env. The Reader opens **My Fines**,
  chooses **Pay with MoMo Sandbox**, and uses **Check MoMo status** after checkout.
  The desktop app verifies payment with the MoMo query API. It does not host an IPN server.

### 9.5 Start the app

~~~powershell
.\.venv\Scripts\python.exe main.py
~~~

Sign in with your **username** and password.

## 10. Software Testing

### Tests without a MySQL test database

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/integration --ignore=tests/test_auth_mysql_integration.py --ignore=tests/test_books.py
~~~

The separate book CRUD test uses the configured MySQL database and writes a
temporary book. Use a disposable database for it. The authentication integration
test requires DB_NAME=library_management_test, set in the environment, and a
separately initialized test schema.

### Isolated MySQL integration tests

Start Docker Desktop and use the dedicated Compose file on port 3308.

~~~powershell
.\.venv\Scripts\python.exe tests/integration/prepare_mysql.py
docker compose -f tests/integration/compose.mysql.yml up -d --wait
$env:TV4_MYSQL_TESTS = '1'
.\.venv\Scripts\python.exe -m pytest -q tests/integration
Remove-Item Env:TV4_MYSQL_TESTS
docker compose -f tests/integration/compose.mysql.yml stop
~~~

The partial-return test named test_partial_returns_keep_their_dates_and_paid_charges
currently tries to insert two fines for one loan. The schema's unique constraint
rejects that fixture. Report it as a known test failure when recording results.

For UI verification, test both roles and walk through borrowing approval,
return confirmation, fines, renewal, and report export. Use isolated records for
cases that change data. Verify email and Sandbox checkout separately with local
service settings.

## 11. Development Stages

### Stage 1 – Analysis and Requirements Specification

- Define functional and non-functional requirements.
- Create Use Case Diagram.
- Create Data Flow Diagram (DFD).
- Create Class Diagram.
- Design database and graphical interfaces.

### Stage 2 – Design

- Finalize the MVC architecture.
- Finalize database tables and relationships.
- Prepare GUI designs.
- Define application components.

### Stage 3 – Implementation

- Implement Python classes and business logic.
- Develop graphical interfaces.
- Connect the application to MySQL.
- Implement Admin and Reader functionalities.
- Manage source code using GitHub.

### Stage 4 – Testing

- Prepare test cases.
- Execute functional and unit tests.
- Identify and fix defects.
- Verify system requirements.
- Prepare testing documentation.

## 12. Project Status

The desktop app and its core Admin and Reader workflows are implemented.
Database migrations, SMTP configuration, and MoMo Sandbox settings are required
for the corresponding features on a fresh test machine.

The root Dockerfile and docker-compose.yml are placeholders. The current Compose
configuration runs the isolated test database only. Packaging the desktop app
and database together remains open under the course deployment requirement.

The specification targets startup within **60 seconds** and login, book search,
and borrowing history within **2 seconds** per operation. These are acceptance
criteria to measure under the course testing conditions.

## 13. License

This project is developed for educational purposes as part of a university Software Engineering course.
