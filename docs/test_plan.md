# Test plan

## Test data

Use a test database with an admin and a reader. For TC4 to TC9, use the same book and finish the borrow and return steps on the same day.

## Test cases

| Test Case ID | Function | Test Steps | Input Data | Expected Result |
| --- | --- | --- | --- | --- |
| TC1 | Login | Open Sign in. Enter the username and password. Click Sign in. | Active reader `reader01`, password `Reader@123`. | The reader dashboard opens. |
| TC2 | Login | Open Sign in. Enter the right username and a wrong password. Click Sign in. | Active reader `student01`, password `wrongpass`. | The app shows “Tên đăng nhập hoặc mật khẩu không chính xác.” The reader stays on Sign in. |
| TC3 | Register Account | Open the register form. Fill in the fields, accept the terms and submit. | John, `john@gmail.com`, `0900000000`, unused username `student01`, password and confirmation `123456`. | A success message appears and the app goes back to Sign in. |
| TC4 | Book Management | Sign in as Admin. Add a book and reload the book list. | A new title, author, category and quantity of 2. | The new book is in the list with 2 available copies. |
| TC5 | Search Books | Sign in as Reader. Search for the book from TC4 and open the result. | Part of the book title from TC4. | The right book shows up and its details open. |
| TC6 | Borrow Books | Reader requests 1 copy. Admin approves it. Check the loan and the book details. | Book from TC4 with 2 available copies. Reader has no active loans. | The request is `Pending` before approval. After approval it has a due date and shows `Approved` in Borrowing History. Quantity is still 2 and Available copies is 1. |
| TC7 | Return Books | Reader requests a return. Admin selects the copy, enters the return date and condition, then confirms. | Loan from TC6. Return before the due date. Condition: `Good`. | The loan shows `Returned`. Quantity is 2 and Available copies is back to 2. |
| TC8 | Borrowing History | Open Borrowing History as the same reader and find the loan from TC7. | The loan just returned in TC7. | The book title, return date and `Returned` status are correct. |
| TC9 | Reports / Statistics | Open Reports as Admin. Select Borrowing and returns and preview the report. | Set From and To to the date used in TC6 and TC7. | The report counts the loan and the return. If they are the only activity that day, each total is 1. |
| TC10 | My Profile | Open My Profile as Reader. Change the phone number, save and reopen the profile. | A new valid phone number. | The new phone number is shown. |

## Results

| Cases | How we tested | Result |
| --- | --- | --- |
| TC1–TC3 | Pytest | PASS |
| TC4–TC10 | Tested on the app | PASS (reported by the team) |

Pytest shows TC1 and TC2 as `test_sign_in[TC01]` and `test_sign_in[TC02]`. TC3 is `test_register_reader_tc03`.

## Commands

Run the login and registration tests.

```powershell
python -B -m pytest -p no:cacheprovider -q tests/test_auth_scenarios.py
```

Run all tests that do not need MySQL.

```powershell
python -B -m pytest -p no:cacheprovider -q --ignore=tests/integration --ignore=tests/test_auth_mysql_integration.py --ignore=tests/test_books.py
```

Result on 2026-11-21: **203 passed**.
