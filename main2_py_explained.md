# main2.py explained

`main2.py` is a Library Management System that runs in the terminal. It keeps **books**, **members** and **borrowings** in an SQLite database file (`project.db`) and lets you manage them through a numbered menu.

This guide first gives the big picture, then walks through the file from top to bottom, line by line.

---

## Overview: how the whole program works

1. **Start.** The last line, `main()`, starts the program.
2. **Connect.** `main()` opens `project.db` (SQLite creates the file if it does not exist) and turns on foreign key checks.
3. **Prepare the database.** `create_tables()` makes the three tables if they are missing. `add_sample_data()` fills them with 50 books, 40 members and 30 borrowings, but only if the `books` table is empty, so the demo data is added just once.
4. **Menu loop.** `main()` prints the menu, reads a number, and calls the matching function. This repeats until you type `0`.
5. **Each function** reads input with `input()`, checks it, runs SQL with `connection.execute(...)`, saves changes with `connection.commit()`, and prints a message.
6. **Exit.** Typing `0` breaks the loop and `connection.close()` closes the database.

### The three tables

| Table | Columns | Meaning |
| --- | --- | --- |
| `books` | `book_id`, `title`, `author`, `genre`, `available` | One row per book. `available` is `1` (on the shelf) or `0` (borrowed). |
| `members` | `member_id`, `name`, `email` (unique), `program` | One row per library member. |
| `borrowings` | `borrowing_id`, `book_id`, `member_id`, `returned` | One row per loan. `returned` is `1` (returned) or `0` (still out). |

`borrowings` links the other two: `book_id` points to a book and `member_id` points to a member.

### Menu options and the function behind each

| Option | Function | What it does |
| --- | --- | --- |
| 1 | `add_book` | Insert a new book |
| 2 | `add_member` | Insert a new member (checks email) |
| 3 | `borrow_book` | Create a loan, mark book unavailable |
| 4 | `display_records` | Show books, members or borrowings |
| 5 | `search_records` | Search books by title, members by name or ID |
| 6 | `update_book` | Change a book's title and author |
| 7 | `delete_record` | Delete (cancel) a borrowing |
| 8 | `return_book` | Mark a loan returned, book available again |
| 9 | `show_statistics` | Print totals and the most borrowed book |
| 10 | `export_results` | Write a summary to `results.txt` |
| 0 | | Exit |

---

## 1. Imports and constants (lines 1–6)

```python
import random
import re
import sqlite3
```

- `random` picks a random member for each demo borrowing.
- `re` is regular expressions, used to check that an email looks valid.
- `sqlite3` is Python's built-in SQLite database library.
- All three come with Python, so nothing needs installing.

```python
DATABASE = "project.db"
RESULTS = "results.txt"
```

- File names for the database and the export file. CAPITAL names are a Python convention for constants.
- These are **relative paths**, so the files are created in the folder you run the program from (the current working directory), not necessarily next to `main2.py`.

---

## 2. The `Book` class (lines 9–21)

```python
class Book:
    def __init__(self, book_id, title, author, genre, available):
```

- `class Book:` defines a blueprint for book objects.
- `__init__` is the constructor. Python runs it when you write `Book(...)`. `self` is the new object.

```python
        self.book_id = book_id
        self.title = title
        self.author = author
        self.genre = genre
        self.available = available
```

- Each line stores one argument on the object as an attribute, e.g. `book.title`.

```python
    def show(self):
        status = "Yes" if self.available == 1 else "No"
```

- `show` is a method that prints the book as one table row.
- The one-line if/else turns `1`/`0` into `"Yes"`/`"No"`.

```python
        print("{:<4} | {:<42} | {:<34} | {:<20} | {:<9}".format(
            self.book_id, self.title, self.author, self.genre, status
        ))
```

- `"...".format(a, b, ...)` fills each `{}` with the next value.
- `:<4` means "left-align in a space 4 characters wide". The widths keep the columns lined up under the header printed by `show_book_table`.
- `|` is just a separator character between columns.

---

## 3. The `Member` class (lines 23–33)

```python
class Member:
    def __init__(self, member_id, name, email, program):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.program = program
```

- Same idea as `Book`: one object holds one member's data.

```python
    def show(self):
        print("{:<4} | {:<25} | {:<42} | {:<22}".format(
            self.member_id, self.name, self.email, self.program
        ))
```

- Prints the member as one aligned table row.

---

## 4. `create_tables` (lines 35–40)

```python
def create_tables(connection):
    cursor = connection.cursor()
```

- Receives the open database connection. A **cursor** is the object that runs SQL commands.

```python
    cursor.execute("CREATE TABLE IF NOT EXISTS books (book_id INTEGER PRIMARY KEY, title TEXT, author TEXT, genre TEXT, available INTEGER)")
```

- Creates the `books` table only if it does not already exist.
- `INTEGER PRIMARY KEY` makes `book_id` the unique ID. SQLite fills it in automatically (1, 2, 3, ...) when you insert without giving one.

```python
    cursor.execute("CREATE TABLE IF NOT EXISTS members (member_id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, program TEXT)")
```

- Creates `members`. `UNIQUE` on `email` means two members cannot share an email.

```python
    cursor.execute("CREATE TABLE IF NOT EXISTS borrowings (borrowing_id INTEGER PRIMARY KEY, book_id INTEGER, member_id INTEGER, returned INTEGER, FOREIGN KEY(book_id) REFERENCES books(book_id), FOREIGN KEY(member_id) REFERENCES members(member_id))")
```

- Creates `borrowings`.
- `FOREIGN KEY ... REFERENCES ...` says `book_id` must match a real book and `member_id` must match a real member. This is enforced because `main()` turns on `PRAGMA foreign_keys = ON`.

```python
    connection.commit()
```

- Saves the changes to the file.

---

## 5. `add_sample_data` (lines 43–131)

```python
def add_sample_data(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] > 0:
        return
```

- Counts the books. `fetchone()` returns one row as a tuple, e.g. `(50,)`, and `[0]` takes the number.
- If there are already books, the function stops (`return`). This stops the demo data being added again on every run.

```python
    books = [
        ("Python Crash Course", "Eric Matthes", "Programming"),
        ...
        ("Man's Search for Meaning", "Viktor E. Frankl", "Memoir"),
    ]
```

- A list of 50 tuples. Each tuple is `(title, author, genre)`. Books 1–20 are mostly programming and computer science, the rest are fiction, science, history and Kazakh literature.

```python
    names = [
        "Aibek Sarsenov", "Aida Nurgaliyeva", ...,
        "Zhibek Aman",
    ]
```

- A list of 40 member names.

```python
    programs = ["Computer Science", "Mathematics", "Engineering", "Economics", "Languages"]
```

- Five study programs that members are given in turn.

```python
    for title, author, genre in books:
        cursor.execute("INSERT INTO books (title, author, genre, available) VALUES (?, ?, ?, 1)", (title, author, genre))
```

- Loops over the 50 books. `for title, author, genre in books` unpacks each tuple into three variables.
- `?` are **placeholders**. sqlite3 fills them safely from the tuple, which prevents SQL injection. `available` is set to `1`.

```python
    for i in range(len(names)):
        email = names[i].lower().replace(" ", ".") + "@kbtu.kz"
```

- Loops `i` from 0 to 39.
- Builds an email from the name: `"Aibek Sarsenov"` → `"aibek.sarsenov"` → `"aibek.sarsenov@kbtu.kz"`.

```python
        program = programs[i % len(programs)]
```

- `%` is the remainder. `i % 5` cycles 0, 1, 2, 3, 4, 0, 1, ... so programs are handed out in rotation.

```python
        cursor.execute("INSERT INTO members (name, email, program) VALUES (?, ?, ?)", (names[i], email, program))
```

- Inserts the member.

```python
    loan_counts = [8, 5, 4, 3, 2, 2] + [1] * 6
```

- How many times each of the first 12 books has been borrowed. `[1] * 6` is `[1, 1, 1, 1, 1, 1]`, so the full list is `[8, 5, 4, 3, 2, 2, 1, 1, 1, 1, 1, 1]`. The sum is **30**, which is the 30 borrowing records.

```python
    for book_number in range(len(loan_counts)):
        book_id = book_number + 1
```

- Loops over positions 0–11. Database IDs start at 1, so `book_id = book_number + 1`.

```python
        for copy_number in range(loan_counts[book_number]):
            member_id = random.randint(1, len(names))
            returned = 1
```

- Inner loop: one pass per loan of this book (8 for book 1, 5 for book 2, ...).
- `random.randint(1, 40)` picks a random member (both ends included).
- By default the loan is marked returned.

```python
            if book_number < 12 and copy_number == loan_counts[book_number] - 1:
                returned = 0
                cursor.execute("UPDATE books SET available=0 WHERE book_id=?", (book_id,))
```

- For the **last** loan of each book, the loan is still out (`returned = 0`) and the book is marked unavailable.
- `book_number < 12` is always true here, since there are exactly 12 entries, so all 12 books end up currently borrowed.
- `(book_id,)` with the comma is a one-item tuple, which `execute` needs.

```python
            cursor.execute("INSERT INTO borrowings (book_id, member_id, returned) VALUES (?, ?, ?)", (book_id, member_id, returned))
    connection.commit()
```

- Saves each borrowing row, then commits everything at the end.
- Result: 30 borrowings, 18 returned and 12 still borrowed. Book 1 ("Python Crash Course") is the most borrowed, with 8 loans.

---

## 6. `add_book` — option 1 (lines 134–143)

```python
def add_book(connection):
    title = input("Book title: ")
    author = input("Author: ")
    genre = input("Genre: ")
```

- `input()` shows a prompt and returns what the user typed as a string.

```python
    if title == "" or author == "" or genre == "":
        print("Please fill in all book details.")
        return
```

- Validation: if any field is empty, print a message and stop.

```python
    connection.execute("INSERT INTO books (title, author, genre, available) VALUES (?, ?, ?, 1)", (title, author, genre))
    connection.commit()
    print("Book added.")
```

- `connection.execute` is a shortcut that makes a cursor and runs the SQL in one step.
- The new book starts as available, and the change is saved.

---

## 7. `add_member` — option 2 (lines 146–159)

```python
def add_member(connection):
    name = input("Member name: ")
    email = input("Member email: ")
    program = input("Study program: ")
```

- Reads the three fields.

```python
    if name == "" or program == "" or re.match(r"^[\w.-]+@[\w.-]+\.\w+$", email) is None:
        print("Enter a name, study program, and valid email.")
        return
```

- Rejects an empty name or program.
- `re.match(pattern, email)` returns `None` if the email does not fit the pattern:
  - `^` start, `$` end of the text.
  - `[\w.-]+` one or more letters, digits, `_`, `.` or `-` (the part before `@`, then the domain).
  - `@` a literal at sign.
  - `\.` a literal dot, then `\w+` the ending like `kz` or `com`.
  - So `ali@kbtu.kz` passes, `ali@kbtu` and `ali kbtu.kz` fail.
- `r"..."` is a raw string so the backslashes are passed to `re` unchanged.

```python
    existing = connection.execute("SELECT member_id FROM members WHERE email=?", (email,)).fetchone()
    if existing is not None:
        print("That email is already registered.")
        return
```

- Looks for a member with the same email. If one is found, stop with a friendly message (instead of crashing on the `UNIQUE` rule).

```python
    connection.execute("INSERT INTO members (name, email, program) VALUES (?, ?, ?)", (name, email, program))
    connection.commit()
    print("Member added.")
```

- Inserts and saves the new member.

---

## 8. Table printing helpers (lines 162–185)

```python
def show_book_table(rows):
    if len(rows) == 0:
        print("No books found.")
        return
```

- `rows` is a list of tuples from the database. If it is empty, say so and stop.

```python
    print("{:<4} | {:<42} | {:<34} | {:<20} | {:<9}".format(
        "ID", "TITLE", "AUTHOR", "GENRE", "AVAILABLE"
    ))
    print("-" * 122)
```

- Prints the header using the same column widths as `Book.show`.
- `"-" * 122` repeats the dash 122 times to make a divider line.

```python
    for row in rows:
        book = Book(row[0], row[1], row[2], row[3], row[4])
        book.show()
```

- For each row, build a `Book` object from the tuple and print it. `row[0]` is the ID, `row[1]` the title, and so on.

```python
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
```

- The same thing for members.
- These helpers are shared by both "display" and "search", so the table code is written once.

---

## 9. Display functions — option 4 (lines 188–226)

```python
def display_books(connection):
    print("\nBOOKS")
    rows = connection.execute("SELECT book_id, title, author, genre, available FROM books").fetchall()
    show_book_table(rows)
```

- `\n` prints a blank line first.
- `fetchall()` returns all rows as a list of tuples, which is passed to the table helper.

```python
def display_members(connection):
    print("\nMEMBERS")
    rows = connection.execute("SELECT member_id, name, email, program FROM members").fetchall()
    show_member_table(rows)
```

- Same for members.

```python
def display_borrowings(connection):
    print("\nBORROWINGS")
    print("{:<4} | {:<9} | {:<10} | {:<10}".format(
        "ID", "BOOK ID", "MEMBER ID", "STATUS"
    ))
    print("-" * 43)
```

- Prints the borrowings title, header and divider. There is no class for borrowings, so it prints rows directly.

```python
    rows = connection.execute("SELECT borrowing_id, book_id, member_id, returned FROM borrowings").fetchall()
    for row in rows:
        status = "Returned" if row[3] == 1 else "Borrowed"
        print("{:<4} | {:<9} | {:<10} | {:<10}".format(row[0], row[1], row[2], status))
```

- Turns `returned` (`1`/`0`) into a readable word and prints each loan.

```python
    if len(rows) == 0:
        print("No borrowing records found.")
```

- If there are no loans, a message is printed under the (empty) header.

```python
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
```

- A small sub-menu. `input()` returns text, so it compares with `"1"`, not `1`.
- `if / elif / else` picks exactly one branch.

---

## 10. `search_records` — option 5 (lines 229–244)

```python
def search_records(connection):
    print("1. Search book by title")
    print("2. Search member by name or ID")
    choice = input("Choose search: ")
```

- Sub-menu for the type of search.

```python
    if choice == "1":
        title = input("Enter part of the title: ")
        rows = connection.execute("SELECT book_id, title, author, genre, available FROM books WHERE title LIKE ?", ("%" + title + "%",)).fetchall()
        print("\nSEARCH RESULTS: BOOKS")
        show_book_table(rows)
```

- `LIKE` with `%` on both sides means "title contains this text anywhere". `%` matches any characters.
- In SQLite, `LIKE` ignores upper/lower case for English letters, so `python` finds `Python Crash Course`.

```python
    elif choice == "2":
        name = input("Enter a name or member ID: ")
        rows = connection.execute("SELECT member_id, name, email, program FROM members WHERE name LIKE ? OR member_id=?", ("%" + name + "%", name)).fetchall()
        print("\nSEARCH RESULTS: MEMBERS")
        show_member_table(rows)
```

- One input works two ways: it matches members whose name contains the text, **or** whose ID equals it. Typing `5` finds member 5; typing `Aida` finds Aida.

```python
    else:
        print("Invalid choice.")
```

---

## 11. `borrow_book` — option 3 (lines 247–263)

```python
def borrow_book(connection):
    book_id = input("Book ID: ")
    member_id = input("Member ID: ")
    if not book_id.isdigit() or not member_id.isdigit():
        print("Please enter numbers for the IDs.")
        return
```

- `.isdigit()` is `True` only if the text is all digits. This rejects things like `abc` or `-1`.

```python
    book = connection.execute("SELECT available FROM books WHERE book_id=?", (book_id,)).fetchone()
    member = connection.execute("SELECT member_id FROM members WHERE member_id=?", (member_id,)).fetchone()
```

- Looks up the book and the member. `fetchone()` returns `None` if nothing matches.

```python
    if book is None or member is None:
        print("Book or member not found.")
    elif book[0] == 0:
        print("That book is already borrowed.")
```

- Stops if either one does not exist, or if the book is already out (`available` is `0`).

```python
    else:
        connection.execute("INSERT INTO borrowings (book_id, member_id, returned) VALUES (?, ?, 0)", (book_id, member_id))
        connection.execute("UPDATE books SET available=0 WHERE book_id=?", (book_id,))
        connection.commit()
        print("Borrowing saved.")
```

- Adds a new loan (`returned = 0`) and marks the book unavailable. Both changes are saved together by one `commit()`.

---

## 12. `return_book` — option 8 (lines 266–280)

```python
def return_book(connection):
    borrowing_id = input("Borrowing ID to return: ")
    if not borrowing_id.isdigit():
        print("Please enter a number.")
        return
```

- Reads and checks the loan ID.

```python
    row = connection.execute("SELECT book_id, returned FROM borrowings WHERE borrowing_id=?", (borrowing_id,)).fetchone()
    if row is None:
        print("Borrowing not found.")
    elif row[1] == 1:
        print("This book was already returned.")
```

- Finds the loan. `row[0]` is the book ID and `row[1]` is the returned flag. It stops if the loan does not exist or was already returned.

```python
    else:
        connection.execute("UPDATE borrowings SET returned=1 WHERE borrowing_id=?", (borrowing_id,))
        connection.execute("UPDATE books SET available=1 WHERE book_id=?", (row[0],))
        connection.commit()
        print("Book returned.")
```

- Marks the loan returned and puts the book back on the shelf. The loan row is kept as history.

---

## 13. `update_book` — option 6 (lines 283–295)

```python
def update_book(connection):
    book_id = input("Book ID to update: ")
    title = input("New title: ")
    author = input("New author: ")
    if not book_id.isdigit() or title == "" or author == "":
        print("Enter a number and fill in the title and author.")
        return
```

- Reads the ID and the new values, then checks them.

```python
    cursor = connection.execute("UPDATE books SET title=?, author=? WHERE book_id=?", (title, author, book_id))
    connection.commit()
```

- Changes the title and author of that book. The genre and availability are not touched.

```python
    if cursor.rowcount == 0:
        print("Book not found.")
    else:
        print("Book updated.")
```

- `rowcount` is how many rows the `UPDATE` changed. `0` means no book has that ID.

---

## 14. `delete_record` — option 7, cancel a borrowing (lines 298–311)

```python
def delete_record(connection):
    borrowing_id = input("Borrowing ID to cancel: ")
    if not borrowing_id.isdigit():
        print("Please enter a number.")
        return
    row = connection.execute("SELECT book_id, returned FROM borrowings WHERE borrowing_id=?", (borrowing_id,)).fetchone()
    if row is None:
        print("Borrowing not found.")
```

- Same checks as `return_book`.

```python
    else:
        connection.execute("DELETE FROM borrowings WHERE borrowing_id=?", (borrowing_id,))
```

- Removes the loan row completely (unlike returning, which keeps it).

```python
        if row[1] == 0:
            connection.execute("UPDATE books SET available=1 WHERE book_id=?", (row[0],))
        connection.commit()
        print("Borrowing cancelled.")
```

- If the loan was still active, the book is made available again, so the book is never left stuck as "borrowed".

---

## 15. `show_statistics` — option 9 (lines 314–322)

```python
def show_statistics(connection):
    total = connection.execute("SELECT COUNT(*) FROM borrowings").fetchone()[0]
    current = connection.execute("SELECT COUNT(*) FROM borrowings WHERE returned=0").fetchone()[0]
```

- `total` is the number of loans ever. `current` is how many are still out.

```python
    top_book = connection.execute("SELECT book_id, COUNT(*) FROM borrowings GROUP BY book_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
```

- `GROUP BY book_id` makes one group per book, and `COUNT(*)` counts loans in each group.
- `ORDER BY COUNT(*) DESC` puts the biggest count first, and `LIMIT 1` keeps only that row.
- The result is a tuple like `(1, 8)`, or `None` if there are no loans.

```python
    print("Total borrowing records:", total)
    print("Books currently borrowed:", current)
    if top_book is not None:
        title = connection.execute("SELECT title FROM books WHERE book_id=?", (top_book[0],)).fetchone()
        print("Most frequently borrowed book:", title[0], "-", top_book[1], "loans")
```

- Prints the numbers. If there is a top book, it looks up its title and prints it with its loan count.
- With the sample data this shows 30 records, 12 borrowed, and "Python Crash Course - 8 loans".

---

## 16. `export_results` — option 10 (lines 325–342)

```python
def export_results(connection):
    with open(RESULTS, "w") as file:
```

- Opens `results.txt` for writing (`"w"` replaces any old content).
- `with` closes the file automatically when the block ends, even after an error.

```python
        total = connection.execute("SELECT COUNT(*) FROM borrowings").fetchone()[0]
        current = connection.execute("SELECT COUNT(*) FROM borrowings WHERE returned=0").fetchone()[0]
        top_book = connection.execute("SELECT book_id, COUNT(*) FROM borrowings GROUP BY book_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
```

- The same three queries as `show_statistics`.

```python
        file.write("UNIVERSITY LIBRARY SUMMARY\n")
        file.write("Books: " + str(connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]) + "\n")
        file.write("Members: " + str(connection.execute("SELECT COUNT(*) FROM members").fetchone()[0]) + "\n")
        file.write("Borrowing records: " + str(total) + "\n")
        file.write("Books currently borrowed: " + str(current) + "\n")
```

- `file.write` adds text to the file. Unlike `print`, it does not add a new line, so each line ends with `"\n"`.
- `str(...)` turns numbers into text so they can be joined with `+`.

```python
        if top_book is not None:
            title = connection.execute("SELECT title FROM books WHERE book_id=?", (top_book[0],)).fetchone()
            file.write("Most frequently borrowed book: " + title[0] + " (" + str(top_book[1]) + " loans)\n")
```

- Writes the most borrowed book, if any.

```python
        file.write("\nBORROWING RECORDS\n")
        rows = connection.execute("SELECT borrowing_id, book_id, member_id, returned FROM borrowings")
        for row in rows:
            file.write(str(row[0]) + " | Book " + str(row[1]) + " | Member " + str(row[2]) + " | Returned: " + str(row[3]) + "\n")
```

- Writes every loan, one per line. A cursor can be looped over directly without `fetchall()`.

```python
    print("Results saved to results.txt.")
```

- This line is outside the `with` block, so it runs after the file is closed.

---

## 17. `show_menu` (lines 345–359)

```python
def show_menu():
    print("""
UNIVERSITY LIBRARY SYSTEM
1. Add a book
...
0. Exit
""")
```

- Triple quotes `"""..."""` make a string that spans several lines, so the whole menu prints with one `print`.

---

## 18. `main` (lines 362–396)

```python
def main():
    connection = sqlite3.connect(DATABASE)
```

- Opens (or creates) `project.db` and returns a connection used by every function.

```python
    connection.execute("PRAGMA foreign_keys = ON")
```

- SQLite does not check foreign keys by default. This turns the check on, so a borrowing cannot point to a missing book or member.

```python
    create_tables(connection)
    add_sample_data(connection)
    print("Library ready: 50 books, 40 members, and 30 borrowing records.")
```

- Prepares the tables and demo data, then prints a ready message. The numbers in this message are fixed text, so they do not change after you add or delete records.

```python
    while True:
        show_menu()
        choice = input("Choose an option: ")
```

- `while True` repeats forever until `break`. Each pass shows the menu and reads a choice.

```python
        if choice == "1":
            add_book(connection)
        elif choice == "2":
            add_member(connection)
        ...
        elif choice == "10":
            export_results(connection)
```

- Calls the function for the chosen option, passing the shared connection.

```python
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Choose a number from the menu.")
```

- `0` ends the loop. Anything else shows a hint and the menu appears again.

```python
    connection.close()
```

- Closes the database after the loop ends.

---

## 19. Starting the program (line 399)

```python
main()
```

- Calls `main()` when the file is run with `python3 main2.py`. Without this line, the file would only define functions and do nothing.

---

## Key ideas to remember

- **SQLite + `?` placeholders**: all user input goes into SQL through `?`, which is safe against SQL injection.
- **`commit()`** is needed after every change, or the change is lost.
- **`available`** in `books` and **`returned`** in `borrowings` always change together: borrowing sets them to `0`/`0`, returning sets them to `1`/`1`.
- **Classes** `Book` and `Member` are used to print rows neatly; the data itself lives in the database.
- **Validation** (`isdigit`, empty checks, email regex, duplicate email check) stops bad input before it reaches the database.
