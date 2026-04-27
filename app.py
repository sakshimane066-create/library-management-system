from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import date, timedelta
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or 'dev_key'

# ── DB CONFIG ─────────────────────────────
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def query(sql, params=(), fetch='all'):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)

    if fetch == 'all':
        result = cur.fetchall()
    elif fetch == 'one':
        result = cur.fetchone()
    else:
        conn.commit()
        result = cur.lastrowid

    cur.close()
    conn.close()
    return result

def execute(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    cur.close()
    conn.close()
    return last_id


# ── LOGIN REQUIRED ────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'librarian' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


# ── AUTH ──────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        lib = query("SELECT * FROM Librarian WHERE email=%s", (email,), 'one')

        if lib and check_password_hash(lib['password_hash'], password):
            session['librarian'] = lib['name']
            session['lib_id'] = lib['lib_id']
            return redirect(url_for('dashboard'))

        flash("Invalid credentials", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        lib_id = execute("""
            INSERT INTO Librarian (name, email, password_hash)
            VALUES (%s, %s, %s)
        """, (name, email, password))

        session['librarian'] = name
        session['lib_id'] = lib_id

        return redirect(url_for('dashboard'))

    return render_template('register.html')


# ── DASHBOARD ─────────────────────────────
@app.route('/')
@login_required
def dashboard():
    stats = {
        'books': query("SELECT COUNT(*) c FROM Book", fetch='one')['c'],
        'members': query("SELECT COUNT(*) c FROM Member", fetch='one')['c'],
        'issued': query("SELECT COUNT(*) c FROM Issue WHERE return_date IS NULL", fetch='one')['c'],
        'overdue': query("""
            SELECT COUNT(*) c FROM Issue
            WHERE return_date IS NULL AND due_date < CURDATE()
        """, fetch='one')['c']
    }
    return render_template('dashboard.html', stats=stats)


# ── BOOKS ────────────────────────────────
@app.route('/books')
@login_required
def books():
    data = query("""
        SELECT b.book_id, b.title, b.ISBN,
               a.name AS author,
               c.category_name,
               b.total_copies,
               b.available_copies
        FROM Book b
        JOIN Author a ON b.author_id = a.author_id
        JOIN Category c ON b.category_id = c.category_id
        ORDER BY b.book_id DESC
    """)
    return render_template('books.html', books=data)


@app.route('/books/add', methods=['POST'])
@login_required
def add_book():
    execute("""
        INSERT INTO Book (title, ISBN, author_id, category_id, total_copies, available_copies)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        request.form['title'],
        request.form['isbn'],
        request.form['author_id'],
        request.form['category_id'],
        request.form['copies'],
        request.form['copies']
    ))
    return redirect(url_for('books'))


@app.route('/books/delete/<int:book_id>')
@login_required
def delete_book(book_id):
    execute("DELETE FROM Book WHERE book_id=%s", (book_id,))
    return redirect(url_for('books'))


# ── MEMBERS ──────────────────────────────
@app.route('/members')
@login_required
def members():
    data = query("SELECT * FROM Member ORDER BY member_id DESC")
    return render_template('members.html', members=data)


# ⚠️ FIX: ADD MEMBER ROUTE (was missing)
@app.route('/members/add', methods=['POST'])
@login_required
def add_member():
    execute("""
        INSERT INTO Member (name, email, phone)
        VALUES (%s,%s,%s)
    """, (
        request.form['name'],
        request.form['email'],
        request.form['phone']
    ))
    return redirect(url_for('members'))


# ⚠️ FIX: DELETE MEMBER ROUTE (was missing)
@app.route('/members/delete/<int:member_id>')
@login_required
def delete_member(member_id):
    execute("DELETE FROM Member WHERE member_id=%s", (member_id,))
    return redirect(url_for('members'))


# ── ISSUES ───────────────────────────────
@app.route('/issues')
@login_required
def issues():
    data = query("""
        SELECT i.issue_id, m.name AS member, b.title AS book,
               i.issue_date, i.due_date, i.return_date
        FROM Issue i
        JOIN Member m ON i.member_id = m.member_id
        JOIN Book b ON i.book_id = b.book_id
        ORDER BY i.issue_id DESC
    """)
    return render_template('issues.html', issues=data)


# ⚠️ FIX: ADD ISSUE ROUTE (was missing)
@app.route('/issues/add', methods=['POST'])
@login_required
def add_issue():
    due = date.today() + timedelta(days=14)

    execute("""
        INSERT INTO Issue (member_id, book_id, lib_id, issue_date, due_date)
        VALUES (%s,%s,%s,CURDATE(),%s)
    """, (
        request.form['member_id'],
        request.form['book_id'],
        session['lib_id'],
        due
    ))

    execute("""
        UPDATE Book
        SET available_copies = available_copies - 1
        WHERE book_id=%s
    """, (request.form['book_id'],))

    return redirect(url_for('issues'))


# ── RETURN BOOK (ONLY ONE VERSION — FIXED) ──
@app.route('/return_book/<int:issue_id>')
@login_required
def return_book(issue_id):
    row = query("SELECT * FROM Issue WHERE issue_id=%s", (issue_id,), 'one')

    if row:
        late = (date.today() - row['due_date']).days
        fine = max(0, late * 2)

        execute("""
            UPDATE Issue
            SET return_date=CURDATE(), fine_amount=%s
            WHERE issue_id=%s
        """, (fine, issue_id))

        execute("""
            UPDATE Book
            SET available_copies = available_copies + 1
            WHERE book_id=%s
        """, (row['book_id'],))

    return redirect(url_for('issues'))


# ── CATALOGUE ────────────────────────────
@app.route('/catalogue')
@login_required
def catalogue():
    authors = query("""
        SELECT a.author_id, a.name, COUNT(b.book_id) AS book_count
        FROM Author a
        LEFT JOIN Book b ON a.author_id = b.author_id
        GROUP BY a.author_id
    """)

    categories = query("""
        SELECT c.category_id, c.category_name, COUNT(b.book_id) AS book_count
        FROM Category c
        LEFT JOIN Book b ON c.category_id = b.category_id
        GROUP BY c.category_id
    """)

    return render_template('catalogue.html', authors=authors, categories=categories)
# @app.route('/reports')
# @login_required
# def reports():
#     overdue = query("""
#         SELECT m.name, b.title, i.due_date,
#                DATEDIFF(CURDATE(), i.due_date) AS days_late,
#                DATEDIFF(CURDATE(), i.due_date) * 2 AS fine
#         FROM Issue i
#         JOIN Member m ON i.member_id = m.member_id
#         JOIN Book b ON i.book_id = b.book_id
#         WHERE i.return_date IS NULL AND i.due_date < CURDATE()
#     """)
@app.route('/reports')
@login_required
def reports():
    overdue = query("""
        SELECT 
            m.name AS member_name,
            b.title AS book_title,
            i.due_date,
            DATEDIFF(CURDATE(), i.due_date) AS days_late,
            DATEDIFF(CURDATE(), i.due_date) * 2 AS fine
        FROM Issue i
        JOIN Member m ON i.member_id = m.member_id
        JOIN Book b ON i.book_id = b.book_id
        WHERE i.return_date IS NULL 
        AND i.due_date < CURDATE()
    """)
    return render_template('reports.html', overdue=overdue)
    return render_template('reports.html', overdue=overdue)
@app.route('/authors/add', methods=['POST'])
@login_required
def add_author():
    name = request.form['name']

    execute("""
        INSERT INTO Author (name)
        VALUES (%s)
    """, (name,))

    return redirect(url_for('catalogue'))

@app.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    name = request.form['category_name']

    execute("""
        INSERT INTO Category (category_name)
        VALUES (%s)
    """, (name,))

    return redirect(url_for('catalogue'))

# ── RUN ──────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)