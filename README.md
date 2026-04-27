# LibraMS — Library Management System
## MES Wadia COE | PCC-254-COM | Assignment 1 & 11
### Stack: Python (Flask) + MySQL

---

## Setup Instructions

### Step 1 — Install MySQL & create database
```bash
mysql -u root -p < library_db.sql
```

### Step 2 — Install Python dependencies
```bash
pip install flask mysql-connector-python
```

### Step 3 — Configure DB password
Open `app.py` and set your MySQL password in DB_CONFIG:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_PASSWORD_HERE',
    'database': 'library_db'
}
```

### Step 4 — Run the app
```bash
python app.py
```
Open browser: http://127.0.0.1:5000

---

## Features
- Dashboard with live stats (books, members, issued, overdue)
- Book catalogue with search, add, delete
- Member registration with search
- Issue a book (auto 14-day due date)
- Return a book (auto fine = ₹2/day after due date)
- Reports: overdue list, top borrowed books, fine summary

## Project Structure
```
library_app/
├── app.py                  ← Flask routes & DB logic
├── requirements.txt
├── templates/
│   ├── base.html           ← Sidebar layout
│   ├── dashboard.html
│   ├── books.html
│   ├── members.html
│   ├── issues.html
│   └── reports.html
```
