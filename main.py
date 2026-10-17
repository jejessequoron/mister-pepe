import random
import re
import sqlite3
from pathlib import Path

DATABASE = Path(__file__).with_name("project.db")
RESULTS = Path(__file__).with_name("results.txt")
EMAIL_PATTERN = r"^[\w.-]+@[\w.-]+\.\w+$"

class Book:
    def __init__(self, book_id, title, author, available):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.available = available

    def __str__(self):
        status = "Yes" if self.available else "No"
        return f"{self.book_id:<5} {self.title:<30} {self.author:<22} {status}"

class Member:
    def __init__(self, member_id, name, email):
        self.member_id = member_id
        self.name = name
        self.email = email

    def __str__(self):
        return f"{self.member_id:<5} {self.name:<25} {self.email}"

def connect_database():
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def create_tables(connection):
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            available INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS borrowings (
            borrowing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
            member_id INTEGER NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
            returned INTEGER NOT NULL DEFAULT 0
        );
    """)
    connection.commit()

def add_sample_data(connection):
    book_count = connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if book_count > 0:
        return
    random.seed(6)
    titles = ["Python Basics", "A World of Stories", "The Green Garden", "Space and Stars", "The Lost Key",
              "Simple Machines", "A Long Journey", "Ocean Life", "The Old House", "Number Patterns"]
    authors = ["A. Brown", "M. Ali", "S. Kim", "D. Smith", "L. Chen"]
    first_names = ["Amina", "Daniel", "Sara", "Arman", "Maya", "Timur", "Leila", "Noah", "Dina", "Ethan"]
    last_names = ["Brown", "Kim", "Sato", "Patel", "Garcia", "Ali", "Chen", "Smith", "Ivanov", "Jones"]
    for i in range(50):
        title = titles[i % len(titles)] + " " + str(i // len(titles) + 1)
        author = authors[i % len(authors)]
        connection.execute("INSERT INTO books(title, author) VALUES (?, ?)", (title, author))
    for i in range(30):
        name = first_names[i % len(first_names)] + " " + last_names[(i * 3) % len(last_names)]
        email = "member" + str(i + 1) + "@example.com"
        connection.execute("INSERT INTO members(name, email) VALUES (?, ?)", (name, email))
    book_ids = [row[0] for row in connection.execute("SELECT book_id FROM books")]
    member_ids = [row[0] for row in connection.execute("SELECT member_id FROM members")]
    borrowed_books = random.sample(book_ids, 30)
    for i in range(30):
        book_id = borrowed_books[i]
        member_id = random.choice(member_ids)
        returned = 1 if i % 3 == 0 else 0
        connection.execute(
            "INSERT INTO borrowings(book_id, member_id, returned) VALUES (?, ?, ?)",
            (book_id, member_id, returned),
        )
        if returned == 0:
            connection.execute("UPDATE books SET available = 0 WHERE book_id = ?", (book_id,))
    connection.commit()

def get_number(message):
    try:
        return int(input(message))
    except ValueError:
        print("Please enter a number.")
        return None

def add_book(connection):
    title = input("Book title: ").strip()
    author = input("Author: ").strip()
    if title == "" or author == "":
        print("Title and author are required.")
        return
    connection.execute("INSERT INTO books(title, author) VALUES (?, ?)", (title, author))
    connection.commit()
    print("Book added.")

def add_member(connection):
    name = input("Member name: ").strip()
    email = input("Member email: ").strip()
    if name == "" or re.fullmatch(EMAIL_PATTERN, email) is None:
        print("Enter a name and a valid email, for example name@example.com.")
        return
    try:
        connection.execute("INSERT INTO members(name, email) VALUES (?, ?)", (name, email))
        connection.commit()
        print("Member added.")
    except sqlite3.IntegrityError:
        print("That email is already registered.")

def show_books(connection, available_only=False):
    if available_only:
        rows = connection.execute("SELECT book_id, title, author, available FROM books WHERE available=1 ORDER BY title")
    else:
        rows = connection.execute("SELECT book_id, title, author, available FROM books ORDER BY title")
    print("ID    TITLE                          AUTHOR                 AVAILABLE")
    for row in rows:
        print(Book(row[0], row[1], row[2], row[3]))

def show_members(connection):
    rows = connection.execute("SELECT member_id, name, email FROM members ORDER BY name")
    print("ID    NAME                      EMAIL")
    for row in rows:
        print(Member(row[0], row[1], row[2]))

def show_borrowings(connection):
    rows = connection.execute("""
        SELECT borrowings.borrowing_id, books.title, members.name, borrowings.returned
        FROM borrowings JOIN books ON borrowings.book_id=books.book_id
        JOIN members ON borrowings.member_id=members.member_id
        ORDER BY borrowings.borrowing_id
    """)
    print("ID    BOOK                           MEMBER                    STATUS")
    for row in rows:
        status = "Returned" if row[3] else "Borrowed"
        print(f"{row[0]:<5} {row[1]:<30} {row[2]:<25} {status}")

def display_records(connection):
    choice = input("Display (b)ooks, (m)embers, or bo(r)rowings? ").strip().lower()
    if choice == "b":
        show_books(connection)
    elif choice == "m":
        show_members(connection)
    elif choice == "r":
        show_borrowings(connection)
    else:
        print("Choose b, m, or r.")

def borrow_book(connection):
    book_id = get_number("Book ID: ")
    member_id = get_number("Member ID: ")
    if book_id is None or member_id is None:
        return
    book = connection.execute("SELECT available FROM books WHERE book_id=?", (book_id,)).fetchone()
    member = connection.execute("SELECT member_id FROM members WHERE member_id=?", (member_id,)).fetchone()
    if book is None or member is None:
        print("Book or member was not found.")
    elif book[0] == 0:
        print("That book is already borrowed.")
    else:
        connection.execute("INSERT INTO borrowings(book_id, member_id) VALUES (?, ?)", (book_id, member_id))
        connection.execute("UPDATE books SET available=0 WHERE book_id=?", (book_id,))
        connection.commit()
        print("Borrowing saved.")

def search_records(connection):
    choice = input("Search (b)ooks or (m)embers? ").strip().lower()
    if choice == "b":
        title = input("Book title contains: ").strip()
        rows = connection.execute(
            "SELECT book_id, title, author, available FROM books WHERE title LIKE ? ORDER BY title",
            ("%" + title + "%",),
        )
        print("ID    TITLE                          AUTHOR                 AVAILABLE")
        found = False
        for row in rows:
            print(Book(row[0], row[1], row[2], row[3]))
            found = True
        if not found:
            print("No books found.")
    elif choice == "m":
        name = input("Member name or ID: ").strip()
        rows = connection.execute(
            "SELECT member_id, name, email FROM members WHERE name LIKE ? OR CAST(member_id AS TEXT)=?",
            ("%" + name + "%", name),
        )
        print("ID    NAME                      EMAIL")
        found = False
        for row in rows:
            print(Member(row[0], row[1], row[2]))
            found = True
        if not found:
            print("No members found.")
    else:
        print("Choose b or m.")

def update_book(connection):
    book_id = get_number("Book ID to update: ")
    if book_id is None:
        return
    title = input("New title: ").strip()
    author = input("New author: ").strip()
    if title == "" or author == "":
        print("Title and author are required.")
        return
    cursor = connection.execute("UPDATE books SET title=?, author=? WHERE book_id=?", (title, author, book_id))
    connection.commit()
    print("Book updated." if cursor.rowcount else "Book not found.")

def delete_record(connection):
    choice = input("Delete a (b)ook or cancel a borrowing (r)? ").strip().lower()
    record_id = get_number("ID: ")
    if record_id is None:
        return
    if choice == "b":
        cursor = connection.execute("DELETE FROM books WHERE book_id=?", (record_id,))
        connection.commit()
        print("Book deleted." if cursor.rowcount else "Book not found.")
    elif choice == "r":
        row = connection.execute("SELECT book_id, returned FROM borrowings WHERE borrowing_id=?", (record_id,)).fetchone()
        if row is None:
            print("Borrowing not found.")
        else:
            connection.execute("DELETE FROM borrowings WHERE borrowing_id=?", (record_id,))
            if row[1] == 0:
                connection.execute("UPDATE books SET available=1 WHERE book_id=?", (row[0],))
            connection.commit()
            print("Borrowing cancelled.")
    else:
        print("Choose b or r.")

def show_statistics(connection):
    total = connection.execute("SELECT COUNT(*) FROM borrowings").fetchone()[0]
    active = connection.execute("SELECT COUNT(*) FROM borrowings WHERE returned=0").fetchone()[0]
    most_borrowed = connection.execute("""
        SELECT books.title, COUNT(*) AS total
        FROM borrowings JOIN books ON borrowings.book_id = books.book_id
        GROUP BY books.book_id ORDER BY total DESC, books.title LIMIT 1
    """).fetchone()
    print("Total borrowing records:", total)
    print("Books currently borrowed:", active)
    if most_borrowed:
        print("Most borrowed book:", most_borrowed[0], "-", most_borrowed[1], "time(s)")

def export_results(connection):
    total = connection.execute("SELECT COUNT(*) FROM borrowings").fetchone()[0]
    active = connection.execute("SELECT COUNT(*) FROM borrowings WHERE returned=0").fetchone()[0]
    most_borrowed = connection.execute("""
        SELECT books.title, COUNT(*) AS total
        FROM borrowings JOIN books ON borrowings.book_id = books.book_id
        GROUP BY books.book_id ORDER BY total DESC, books.title LIMIT 1
    """).fetchone()
    with open(RESULTS, "w", encoding="utf-8") as file:
        file.write("LIBRARY MANAGEMENT SYSTEM\n")
        file.write("Books: " + str(connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]) + "\n")
        file.write("Members: " + str(connection.execute("SELECT COUNT(*) FROM members").fetchone()[0]) + "\n")
        file.write("Borrowing records: " + str(total) + "\n")
        file.write("Books currently borrowed: " + str(active) + "\n")
        if most_borrowed:
            file.write("Most borrowed book: " + most_borrowed[0] + " (" + str(most_borrowed[1]) + ")\n")
        file.write("\nBORROWINGS\n")
        rows = connection.execute("""
            SELECT borrowings.borrowing_id, books.title, members.name, borrowings.returned
            FROM borrowings JOIN books ON borrowings.book_id=books.book_id
            JOIN members ON borrowings.member_id=members.member_id
            ORDER BY borrowings.borrowing_id
        """)
        for row in rows:
            status = "Returned" if row[3] else "Borrowed"
            file.write(str(row[0]) + " | " + row[1] + " | " + row[2] + " | " + status + "\n")
    print("Results saved to results.txt.")

def show_menu():
    print("""
LIBRARY MANAGEMENT SYSTEM
1. Add a book
2. Add a member
3. Borrow a book
4. Display books, members, or borrowings
5. Search books or members
6. Show available books
7. Update a book
8. Delete a book or cancel a borrowing
9. Show statistics
10. Export results.txt
0. Exit
""")

def main():
    connection = connect_database()
    create_tables(connection)
    add_sample_data(connection)
    print("Demo data ready: 50 books, 30 members, and 30 borrowings.")
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_book(connection)
        elif choice == "2":
            add_member(connection)
        elif choice == "3":
            borrow_book(connection)
        elif choice == "4":
            display_records(connection)
        elif choice == "5":
            search_records(connection)
        elif choice == "6":
            show_books(connection, available_only=True)
        elif choice == "7":
            update_book(connection)
        elif choice == "8":
            delete_record(connection)
        elif choice == "9":
            show_statistics(connection)
        elif choice == "10":
            export_results(connection)
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Please choose one of the menu numbers.")
    connection.close()

if __name__ == "__main__":
    main()