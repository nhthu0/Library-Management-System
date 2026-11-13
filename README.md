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
- Support overdue fine calculation and simulated payment.
- Ensure system reliability through software testing.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| CustomTkinter | Graphical User Interface (GUI) |
| MySQL 8 | Database management |
| mysql-connector-python | Python–MySQL connection |
| MVC | Software architecture |
| Pytest | Unit testing |
| Git & GitHub | Version control |
| Docker | Database environment and deployment support |
| VS Code | Development environment |

## 4. System Features

### 4.1 Admin Features

- Login and logout.
- Manage reader accounts.
- Add, update, delete, and search books.
- Manage book categories and availability.
- Approve or reject borrowing requests.
- Confirm returned books.
- Manage borrowing records.
- Calculate and manage overdue fines.
- View library statistics.
- Generate reports and export data to CSV.

### 4.2 Reader Features

- Register a new account.
- Login and logout.
- Search and view available books.
- View and update personal information.
- Request to borrow books.
- Request to return books.
- Request borrowing renewal.
- View borrowing history.
- View overdue fines.
- Make simulated fine payments.

## 5. Business Rules

The system follows these business rules:

1. A reader can borrow a maximum of **3 books simultaneously**.
2. Books can only be borrowed when sufficient copies are available.
3. Borrowing requests must be approved by an Admin.
4. Returned books must be confirmed by an Admin.
5. Overdue fines are calculated at **2,000 VND per day per overdue book**.
6. Borrowing and returning transactions must update book availability correctly.
7. Only Admin users can access administrative functions.
8. Locked or inactive accounts cannot log in.
9. Fine payment is simulated within the application without real banking transactions.

## 6. Software Architecture

The system follows the **Model-View-Controller (MVC)** architecture with additional Service and Repository layers.

- **Model:** Represents system entities and business data.
- **View:** Provides graphical interfaces using CustomTkinter.
- **Controller:** Handles user interactions and coordinates application operations.
- **Service:** Implements business rules and validation.
- **Repository:** Performs database operations with MySQL.

### Main Classes

- `User`
- `Admin`
- `Reader`
- `Book`
- `BorrowingRecord`
- `BorrowingDetail`
- `Fine`

The Admin and Reader classes inherit from the User class.

## 7. Database Design

The system uses **MySQL 8** and includes seven main tables.

| Table | Description |
|---|---|
| USERS | Stores user accounts and roles |
| ADMINS | Stores administrator information |
| READERS | Stores reader information |
| BOOKS | Stores book information and inventory |
| BORROWING_RECORDS | Stores borrowing transactions |
| BORROWING_DETAILS | Stores books associated with borrowing records |
| FINES | Stores overdue fines and payment information |

### Database Relationships

- USERS has a one-to-one relationship with ADMINS or READERS depending on the user role.
- READERS has a one-to-many relationship with BORROWING_RECORDS.
- ADMINS processes borrowing transactions.
- BORROWING_RECORDS has a one-to-many relationship with BORROWING_DETAILS.
- BOOKS has a one-to-many relationship with BORROWING_DETAILS.
- BORROWING_RECORDS is associated with FINES.
- ADMINS may confirm fine payments.

### Database Notes

- `userID` is used as the primary identifier for user accounts.
- Email is used for login instead of a separate username.
- `account_status` supports Active, Locked, and Inactive accounts.
- `quantity` stores the total number of book copies.
- `renewal_count` tracks approved renewals.
- Date values are represented using `VARCHAR(10)` in the format `YYYY-MM-DD`.
- Date validation and calculations are handled by the Python application.

## 8. Proposed Project Structure

```text
Library-Management-System/
│
├── main.py
├── README.md
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
│
├── app/
│   ├── models/
│   │   ├── user.py
│   │   ├── admin.py
│   │   ├── reader.py
│   │   ├── book.py
│   │   ├── borrowing_record.py
│   │   ├── borrowing_detail.py
│   │   └── fine.py
│   │
│   ├── views/
│   ├── controllers/
│   ├── services/
│   ├── repositories/
│   │
│   └── database/
│       └── connection.py
│
├── sql/
│   ├── schema.sql
│   └── seed.sql
│
├── tests/
│   ├── test_auth.py
│   ├── test_books.py
│   ├── test_borrowing.py
│   ├── test_returning.py
│   └── test_fines.py
│
└── docs/
    ├── stage1/
    ├── testing/
    └── screenshots/
```

*This is the proposed project structure and may be updated during implementation.*

## 9. Installation and Setup

The following steps describe the planned development environment.

### Prerequisites

- Python 3
- MySQL 8
- Docker Desktop
- Git
- VS Code

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Library-Management-System
```

Replace `<repository-url>` with the actual GitHub repository URL.

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment on Windows:

```bash
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Database

Create a MySQL database and configure the connection settings using the provided environment configuration.

The database schema will be defined in `sql/schema.sql`.

### Step 5: Run the Application

```bash
python main.py
```

*Installation commands will be verified and updated after implementation.*

## 10. Software Testing

The project will include unit testing, integration testing, and functional testing.

Testing will cover:

- User authentication.
- Account registration and validation.
- Book management.
- Book searching.
- Borrowing requests and approval.
- Maximum borrowing limit.
- Returning books.
- Borrowing renewal.
- Fine calculation.
- Simulated fine payment.
- Role-based access control.
- Database operations.

### Testing Tools

- Pytest
- Manual GUI testing
- GitHub Actions (planned)

Run automated tests using:

```bash
pytest
```

Test cases, expected results, actual results, and identified defects will be documented using the required course testing template.

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

**Current Phase:** Design refinement and implementation preparation.

The requirement specification, database design, and GUI mockups provide the foundation for development.

Source code, database scripts, installation instructions, and automated tests will be updated as implementation progresses.

## 13. License

This project is developed for educational purposes as part of a university Software Engineering course.
