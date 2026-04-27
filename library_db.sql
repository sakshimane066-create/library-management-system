-- ============================================================
--  Library Management System - MySQL Database Script
--  MES Wadia COE | PCC-254-COM | Assignment 1 & 11
-- ============================================================

CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

-- ─────────────────────────────────────────────
--  TABLE DEFINITIONS (Normalized to 3NF)
-- ─────────────────────────────────────────────

CREATE TABLE Member (
    member_id   INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    phone       VARCHAR(15),
    address     TEXT,
    join_date   DATE NOT NULL DEFAULT (CURDATE())
);

CREATE TABLE Librarian (
    lib_id         INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    email          VARCHAR(100) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL
);

CREATE TABLE Author (
    author_id  INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    bio        TEXT
);

CREATE TABLE Category (
    category_id    INT AUTO_INCREMENT PRIMARY KEY,
    category_name  VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE Book (
    book_id           INT AUTO_INCREMENT PRIMARY KEY,
    title             VARCHAR(200) NOT NULL,
    ISBN              VARCHAR(20) UNIQUE NOT NULL,
    author_id         INT NOT NULL,
    category_id       INT NOT NULL,
    total_copies      INT NOT NULL DEFAULT 1,
    available_copies  INT NOT NULL DEFAULT 1,
    FOREIGN KEY (author_id)   REFERENCES Author(author_id)   ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE RESTRICT,
    CHECK (available_copies >= 0),
    CHECK (available_copies <= total_copies)
);

CREATE TABLE Issue (
    issue_id      INT AUTO_INCREMENT PRIMARY KEY,
    member_id     INT NOT NULL,
    book_id       INT NOT NULL,
    lib_id        INT NOT NULL,
    issue_date    DATE NOT NULL DEFAULT (CURDATE()),
    due_date      DATE NOT NULL,
    return_date   DATE DEFAULT NULL,
    fine_amount   DECIMAL(8,2) DEFAULT 0.00,
    FOREIGN KEY (member_id) REFERENCES Member(member_id)     ON DELETE RESTRICT,
    FOREIGN KEY (book_id)   REFERENCES Book(book_id)         ON DELETE RESTRICT,
    FOREIGN KEY (lib_id)    REFERENCES Librarian(lib_id)     ON DELETE RESTRICT
);

-- ─────────────────────────────────────────────
--  STORED PROCEDURE: Issue a book
-- ─────────────────────────────────────────────

DELIMITER $$

CREATE PROCEDURE IssueBook(
    IN p_member_id INT,
    IN p_book_id   INT,
    IN p_lib_id    INT,
    IN p_due_date  DATE
)
BEGIN
    DECLARE avail INT;
    SELECT available_copies INTO avail FROM Book WHERE book_id = p_book_id;

    IF avail <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No copies available';
    ELSE
        INSERT INTO Issue (member_id, book_id, lib_id, issue_date, due_date)
        VALUES (p_member_id, p_book_id, p_lib_id, CURDATE(), p_due_date);

        UPDATE Book SET available_copies = available_copies - 1
        WHERE book_id = p_book_id;
    END IF;
END$$

-- ─────────────────────────────────────────────
--  STORED PROCEDURE: Return a book + calc fine
-- ─────────────────────────────────────────────

CREATE PROCEDURE ReturnBook(
    IN p_issue_id INT
)
BEGIN
    DECLARE v_due_date    DATE;
    DECLARE v_book_id     INT;
    DECLARE v_fine        DECIMAL(8,2) DEFAULT 0.00;
    DECLARE days_late     INT;

    SELECT due_date, book_id INTO v_due_date, v_book_id
    FROM Issue WHERE issue_id = p_issue_id;

    SET days_late = DATEDIFF(CURDATE(), v_due_date);
    IF days_late > 0 THEN
        SET v_fine = days_late * 2.00;   -- ₹2 per day fine
    END IF;

    UPDATE Issue
    SET return_date = CURDATE(), fine_amount = v_fine
    WHERE issue_id = p_issue_id;

    UPDATE Book SET available_copies = available_copies + 1
    WHERE book_id = v_book_id;
END$$

DELIMITER ;

-- ─────────────────────────────────────────────
--  TRIGGER: Prevent over-issuing
-- ─────────────────────────────────────────────

DELIMITER $$
CREATE TRIGGER before_issue_insert
BEFORE INSERT ON Issue
FOR EACH ROW
BEGIN
    DECLARE avail INT;
    SELECT available_copies INTO avail FROM Book WHERE book_id = NEW.book_id;
    IF avail <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot issue: no copies available';
    END IF;
END$$
DELIMITER ;

-- ─────────────────────────────────────────────
--  SAMPLE DATA
-- ─────────────────────────────────────────────

INSERT INTO Librarian (name, email, password_hash) VALUES
('Admin', 'admin@library.com', 'hashed_password_here');

INSERT INTO Author (name, bio) VALUES
('Robert Sedgewick', 'Professor at Princeton, algorithms expert'),
('Abraham Silberschatz', 'Database systems researcher'),
('Andrew Tanenbaum', 'OS and networking expert'),
('E. Balagurusamy', 'Author of programming textbooks'),
('Ramez Elmasri', 'Database textbook author');

INSERT INTO Category (category_name) VALUES
('Algorithms'), ('Database'), ('Operating Systems'),
('Programming'), ('Networking');

INSERT INTO Book (title, ISBN, author_id, category_id, total_copies, available_copies) VALUES
('Algorithms, 4th Edition',             '978-0321573513', 1, 1, 3, 3),
('Database System Concepts',            '978-0073523323', 2, 2, 4, 4),
('Modern Operating Systems',            '978-0133591620', 3, 3, 2, 2),
('Programming in ANSI C',               '978-0070601598', 4, 4, 5, 5),
('Fundamentals of Database Systems',    '978-0133970777', 5, 2, 3, 3),
('Computer Networks',                   '978-0132126953', 3, 5, 2, 2);

INSERT INTO Member (name, email, phone, address, join_date) VALUES
('Aarav Shah',    'aarav@email.com',   '9876543210', 'Pune', '2024-06-01'),
('Priya Desai',   'priya@email.com',   '9812345678', 'Pune', '2024-06-15'),
('Rohan Kulkarni','rohan@email.com',   '9823456789', 'Pune', '2024-07-01'),
('Sneha Joshi',   'sneha@email.com',   '9834567890', 'Pune', '2024-07-10');

-- Sample issues
INSERT INTO Issue (member_id, book_id, lib_id, issue_date, due_date) VALUES
(1, 1, 1, '2025-04-01', '2025-04-15'),
(2, 2, 1, '2025-04-05', '2025-04-19'),
(3, 3, 1, '2025-04-10', '2025-04-24');

-- Update available copies for issued books
UPDATE Book SET available_copies = available_copies - 1 WHERE book_id IN (1, 2, 3);

-- ─────────────────────────────────────────────
--  USEFUL QUERIES FOR TESTING
-- ─────────────────────────────────────────────

-- 1. All currently issued books (not yet returned)
-- SELECT m.name AS Member, b.title AS Book, i.issue_date, i.due_date
-- FROM Issue i
-- JOIN Member m ON i.member_id = m.member_id
-- JOIN Book b ON i.book_id = b.book_id
-- WHERE i.return_date IS NULL;

-- 2. Books with low availability
-- SELECT title, available_copies FROM Book WHERE available_copies = 0;

-- 3. Members with pending fines
-- SELECT m.name, SUM(i.fine_amount) AS total_fine
-- FROM Issue i JOIN Member m ON i.member_id = m.member_id
-- WHERE i.fine_amount > 0
-- GROUP BY m.member_id;

-- 4. Search book by title
-- SELECT b.title, a.name AS Author, c.category_name, b.available_copies
-- FROM Book b
-- JOIN Author a ON b.author_id = a.author_id
-- JOIN Category c ON b.category_id = c.category_id
-- WHERE b.title LIKE '%Database%';

