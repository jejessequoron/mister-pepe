import random
import re
import sqlite3

DATABASE = "project.db"
RESULTS = "results.txt"


class Book:
    def __init__(self, book_id, title, author, genre, available):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.genre = genre
        self.available = available

    def show(self):
        status = "Yes" if self.available == 1 else "No"
        print("{:<4} | {:<42} | {:<34} | {:<20} | {:<9}".format(
            self.book_id, self.title, self.author, self.genre, status
        ))

class Member:
    def __init__(self, member_id, name, email, program):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.program = program

    def show(self):
        print("{:<4} | {:<25} | {:<42} | {:<22}".format(
            self.member_id, self.name, self.email, self.program
        ))

def create_tables(connection):
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS books (book_id INTEGER PRIMARY KEY, title TEXT, author TEXT, genre TEXT, available INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS members (member_id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, program TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS borrowings (borrowing_id INTEGER PRIMARY KEY, book_id INTEGER, member_id INTEGER, returned INTEGER, FOREIGN KEY(book_id) REFERENCES books(book_id), FOREIGN KEY(member_id) REFERENCES members(member_id))")
    connection.commit()


def add_sample_data(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] > 0:
        return

    books = [
        ("Python Crash Course", "Eric Matthes", "Programming"),
        ("Automate the Boring Stuff with Python", "Al Sweigart", "Programming"),
        ("Think Python", "Allen B. Downey", "Programming"),
        ("Fluent Python", "Luciano Ramalho", "Programming"),
        ("Effective Python", "Brett Slatkin", "Programming"),
        ("Python for Data Analysis", "Wes McKinney", "Data Science"),
        ("Learning Python", "Mark Lutz", "Programming"),
        ("Head First Python", "Paul Barry", "Programming"),
        ("Python Tricks", "Dan Bader", "Programming"),
        ("Python Cookbook", "David Beazley and Brian K. Jones", "Programming"),
        ("Clean Code", "Robert C. Martin", "Programming"),
        ("The Pragmatic Programmer", "Andrew Hunt and David Thomas", "Programming"),
        ("Code Complete", "Steve McConnell", "Programming"),
        ("Design Patterns", "Erich Gamma and others", "Programming"),
        ("Introduction to Algorithms", "Thomas H. Cormen and others", "Computer Science"),
        ("Data Structures and Algorithms in Python", "Michael T. Goodrich and others", "Computer Science"),
        ("Database System Concepts", "Abraham Silberschatz and others", "Computer Science"),
        ("Computer Networking: A Top-Down Approach", "James Kurose and Keith Ross", "Computer Science"),
        ("The Linux Command Line", "William Shotts", "Computer Science"),
        ("The C Programming Language", "Brian Kernighan and Dennis Ritchie", "Programming"),
        ("The Hobbit", "J. R. R. Tolkien", "Fantasy"),
        ("Dune", "Frank Herbert", "Science Fiction"),
        ("1984", "George Orwell", "Classic Fiction"),
        ("Pride and Prejudice", "Jane Austen", "Classic Fiction"),
        ("The Great Gatsby", "F. Scott Fitzgerald", "Classic Fiction"),
        ("To Kill a Mockingbird", "Harper Lee", "Fiction"),
        ("The Little Prince", "Antoine de Saint-Exupery", "Fiction"),
        ("Crime and Punishment", "Fyodor Dostoevsky", "Classic Fiction"),
        ("The Alchemist", "Paulo Coelho", "Fiction"),
        ("Atomic Habits", "James Clear", "Personal Development"),
        ("Sapiens", "Yuval Noah Harari", "History"),
        ("Educated", "Tara Westover", "Memoir"),
        ("And Then There Were None", "Agatha Christie", "Mystery"),
        ("The Kite Runner", "Khaled Hosseini", "Fiction"),
        ("The Book Thief", "Markus Zusak", "Historical Fiction"),
        ("The Silent Patient", "Alex Michaelides", "Mystery"),
        ("The Midnight Library", "Matt Haig", "Fiction"),
        ("A Brief History of Time", "Stephen Hawking", "Science"),
        ("Cosmos", "Carl Sagan", "Science"),
        ("The Diary of a Young Girl", "Anne Frank", "Memoir"),
        ("Words of Edification", "Abai Qunanbaiuly", "Kazakh Literature"),
        ("The Path of Abai", "Mukhtar Auezov", "Kazakh Literature"),
        ("The Nomads", "Ilyas Esenberlin", "Kazakh Literature"),
        ("One Hundred Years of Solitude", "Gabriel Garcia Marquez", "Fiction"),
        ("The Old Man and the Sea", "Ernest Hemingway", "Fiction"),
        ("The Catcher in the Rye", "J. D. Salinger", "Fiction"),
        ("The Name of the Rose", "Umberto Eco", "Mystery"),
        ("A Thousand Splendid Suns", "Khaled Hosseini", "Fiction"),
        ("The Art of War", "Sun Tzu", "History"),
        ("Man's Search for Meaning", "Viktor E. Frankl", "Memoir"),
    ]
    names = [
        "Aibek Sarsenov", "Aida Nurgaliyeva", "Alikhan Tolegen", "Amina Zhaksylyk", "Aruzhan Kassen",
        "Asel Mukan", "Askar Bekturov", "Ayan Zhumabay", "Bakyt Ermek", "Danel Akhmet",
        "Diana Abilova", "Dias Kairat", "Dinara Saparova", "Eldar Bek", "Elmira Kazybek",
        "Erasyl Tursyn", "Farida Omarova", "Gulmira Ibrayeva", "Ilyas Sadyk", "Inkar Alimova",
        "Islam Nurtay", "Kamila Balgabek", "Karina Dulat", "Madina Serik", "Miras Akhan",
        "Nurlan Aitbay", "Raushan Kenzhe", "Rustem Bayazit", "Samal Altynbek", "Sanjar Malikov",
        "Sholpan Kadir", "Sultan Zhanibek", "Tamara Ospan", "Timur Kairbek", "Tomiris Mukan",
        "Ulan Nurtay", "Yerlan Akhmet", "Zhanar Mukhtar", "Zhanibek Saken", "Zhibek Aman",
    ]
    programs = ["Computer Science", "Mathematics", "Engineering", "Economics", "Languages"]

    for title, author, genre in books:
        cursor.execute("INSERT INTO books (title, author, genre, available) VALUES (?, ?, ?, 1)", (title, author, genre))

    for i in range(len(names)):
        email = names[i].lower().replace(" ", ".") + "@kbtu.kz"
        program = programs[i % len(programs)]
        cursor.execute("INSERT INTO members (name, email, program) VALUES (?, ?, ?)", (names[i], email, program))

    loan_counts = [8, 5, 4, 3, 2, 2] + [1] * 6
    for book_number in range(len(loan_counts)):
        book_id = book_number + 1
        for copy_number in range(loan_counts[book_number]):
            member_id = random.randint(1, len(names))
            returned = 1
            if book_number < 12 and copy_number == loan_counts[book_number] - 1:
                returned = 0
                cursor.execute("UPDATE books SET available=0 WHERE book_id=?", (book_id,))
            cursor.execute("INSERT INTO borrowings (book_id, member_id, returned) VALUES (?, ?, ?)", (book_id, member_id, returned))
    connection.commit()


def add_book(connection):
    title = input("Book title: ")
    author = input("Author: ")
    genre = input("Genre: ")
    if title == "" or author == "" or genre == "":
        print("Please fill in all book details.")
        return
    connection.execute("INSERT INTO books (title, author, genre, available) VALUES (?, ?, ?, 1)", (title, author, genre))
    connection.commit()
    print("Book added.")


def add_member(connection):
    name = input("Member name: ")
    email = input("Member email: ")
    program = input("Study program: ")
    if name == "" or program == "" or re.match(r"^[\w.-]+@[\w.-]+\.\w+$", email) is None:
        print("Enter a name, study program, and valid email.")
        return
    existing = connection.execute("SELECT member_id FROM members WHERE email=?", (email,)).fetchone()
    if existing is not None:
        print("That email is already registered.")
        return
    connection.execute("INSERT INTO members (name, email, program) VALUES (?, ?, ?)", (name, email, program))
    connection.commit()
    print("Member added.")


def show_book_table(rows):
    if len(rows) == 0:
        print("No books found.")
        return
    print("{:<4} | {:<42} | {:<34} | {:<20} | {:<9}".format(
        "ID", "TITLE", "AUTHOR", "GENRE", "AVAILABLE"
    ))
    print("-" * 122)
    for row in rows:
        book = Book(row[0], row[1], row[2], row[3], row[4])
        book.show()


def show_member_table(rows):
    if len(rows) == 0:
        print("No members found.")
        return
    print("{:<4} | {:<25} | {:<42} | {:<22}".format(
        "ID", "NAME", "EMAIL", "PROGRAM"
    ))
    print("-" * 105)
    for row in rows:
        member = Member(row[0], row[1], row[2], row[3])
        member.show()


def display_books(connection):
    print("\nBOOKS")
    rows = connection.execute("SELECT book_id, title, author, genre, available FROM books").fetchall()
    show_book_table(rows)


def display_members(connection):
    print("\nMEMBERS")
    rows = connection.execute("SELECT member_id, name, email, program FROM members").fetchall()
    show_member_table(rows)


def display_borrowings(connection):
    print("\nBORROWINGS")
    print("{:<4} | {:<9} | {:<10} | {:<10}".format(
        "ID", "BOOK ID", "MEMBER ID", "STATUS"
    ))
    print("-" * 43)
    rows = connection.execute("SELECT borrowing_id, book_id, member_id, returned FROM borrowings").fetchall()
    for row in rows:
        status = "Returned" if row[3] == 1 else "Borrowed"
        print("{:<4} | {:<9} | {:<10} | {:<10}".format(row[0], row[1], row[2], status))
    if len(rows) == 0:
        print("No borrowing records found.")


def display_records(connection):
    print("1. Books")
    print("2. Members")
    print("3. Borrowings")
    choice = input("Choose records to display: ")
    if choice == "1":
        display_books(connection)
    elif choice == "2":
        display_members(connection)
    elif choice == "3":
        display_borrowings(connection)
    else:
        print("Invalid choice.")


def search_records(connection):
    print("1. Search book by title")
    print("2. Search member by name or ID")
    choice = input("Choose search: ")
    if choice == "1":
        title = input("Enter part of the title: ")
        rows = connection.execute("SELECT book_id, title, author, genre, available FROM books WHERE title LIKE ?", ("%" + title + "%",)).fetchall()
        print("\nSEARCH RESULTS: BOOKS")
        show_book_table(rows)
    elif choice == "2":
        name = input("Enter a name or member ID: ")
        rows = connection.execute("SELECT member_id, name, email, program FROM members WHERE name LIKE ? OR member_id=?", ("%" + name + "%", name)).fetchall()
        print("\nSEARCH RESULTS: MEMBERS")
        show_member_table(rows)
    else:
        print("Invalid choice.")


def borrow_book(connection):
    book_id = input("Book ID: ")
    member_id = input("Member ID: ")
    if not book_id.isdigit() or not member_id.isdigit():
        print("Please enter numbers for the IDs.")
        return
    book = connection.execute("SELECT available FROM books WHERE book_id=?", (book_id,)).fetchone()
    member = connection.execute("SELECT member_id FROM members WHERE member_id=?", (member_id,)).fetchone()
    if book is None or member is None:
        print("Book or member not found.")
    elif book[0] == 0:
        print("That book is already borrowed.")
    else:
        connection.execute("INSERT INTO borrowings (book_id, member_id, returned) VALUES (?, ?, 0)", (book_id, member_id))
        connection.execute("UPDATE books SET available=0 WHERE book_id=?", (book_id,))
        connection.commit()
        print("Borrowing saved.")


def return_book(connection):
    borrowing_id = input("Borrowing ID to return: ")
    if not borrowing_id.isdigit():
        print("Please enter a number.")
        return
    row = connection.execute("SELECT book_id, returned FROM borrowings WHERE borrowing_id=?", (borrowing_id,)).fetchone()
    if row is None:
        print("Borrowing not found.")
    elif row[1] == 1:
        print("This book was already returned.")
    else:
        connection.execute("UPDATE borrowings SET returned=1 WHERE borrowing_id=?", (borrowing_id,))
        connection.execute("UPDATE books SET available=1 WHERE book_id=?", (row[0],))
        connection.commit()
        print("Book returned.")


def update_book(connection):
    book_id = input("Book ID to update: ")
    title = input("New title: ")
    author = input("New author: ")
    if not book_id.isdigit() or title == "" or author == "":
        print("Enter a number and fill in the title and author.")
        return
    cursor = connection.execute("UPDATE books SET title=?, author=? WHERE book_id=?", (title, author, book_id))
    connection.commit()
    if cursor.rowcount == 0:
        print("Book not found.")
    else:
        print("Book updated.")


def delete_record(connection):
    borrowing_id = input("Borrowing ID to cancel: ")
    if not borrowing_id.isdigit():
        print("Please enter a number.")
        return
    row = connection.execute("SELECT book_id, returned FROM borrowings WHERE borrowing_id=?", (borrowing_id,)).fetchone()
    if row is None:
        print("Borrowing not found.")
    else:
        connection.execute("DELETE FROM borrowings WHERE borrowing_id=?", (borrowing_id,))
        if row[1] == 0:
            connection.execute("UPDATE books SET available=1 WHERE book_id=?", (row[0],))
        connection.commit()
        print("Borrowing cancelled.")


def show_statistics(connection):
    total = connection.execute("SELECT COUNT(*) FROM borrowings").fetchone()[0]
    current = connection.execute("SELECT COUNT(*) FROM borrowings WHERE returned=0").fetchone()[0]
    top_book = connection.execute("SELECT book_id, COUNT(*) FROM borrowings GROUP BY book_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
    print("Total borrowing records:", total)
    print("Books currently borrowed:", current)
    if top_book is not None:
        title = connection.execute("SELECT title FROM books WHERE book_id=?", (top_book[0],)).fetchone()
        print("Most frequently borrowed book:", title[0], "-", top_book[1], "loans")


def export_results(connection):
    with open(RESULTS, "w") as file:
        total = connection.execute("SELECT COUNT(*) FROM borrowings").fetchone()[0]
        current = connection.execute("SELECT COUNT(*) FROM borrowings WHERE returned=0").fetchone()[0]
        top_book = connection.execute("SELECT book_id, COUNT(*) FROM borrowings GROUP BY book_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        file.write("UNIVERSITY LIBRARY SUMMARY\n")
        file.write("Books: " + str(connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]) + "\n")
        file.write("Members: " + str(connection.execute("SELECT COUNT(*) FROM members").fetchone()[0]) + "\n")
        file.write("Borrowing records: " + str(total) + "\n")
        file.write("Books currently borrowed: " + str(current) + "\n")
        if top_book is not None:
            title = connection.execute("SELECT title FROM books WHERE book_id=?", (top_book[0],)).fetchone()
            file.write("Most frequently borrowed book: " + title[0] + " (" + str(top_book[1]) + " loans)\n")
        file.write("\nBORROWING RECORDS\n")
        rows = connection.execute("SELECT borrowing_id, book_id, member_id, returned FROM borrowings")
        for row in rows:
            file.write(str(row[0]) + " | Book " + str(row[1]) + " | Member " + str(row[2]) + " | Returned: " + str(row[3]) + "\n")
    print("Results saved to results.txt.")


def show_menu():
    print("""
UNIVERSITY LIBRARY SYSTEM
1. Add a book
2. Add a member
3. Borrow a book
4. Display records
5. Search books or members
6. Update a book
7. Cancel a borrowing
8. Return a book
9. Show statistics
10. Export results.txt
0. Exit
""")


def main():
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")
    create_tables(connection)
    add_sample_data(connection)
    print("Library ready: 50 books, 40 members, and 30 borrowing records.")
    while True:
        show_menu()
        choice = input("Choose an option: ")
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
            update_book(connection)
        elif choice == "7":
            delete_record(connection)
        elif choice == "8":
            return_book(connection)
        elif choice == "9":
            show_statistics(connection)
        elif choice == "10":
            export_results(connection)
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Choose a number from the menu.")
    connection.close()


main()