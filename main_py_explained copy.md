# main.py explained

`main.py` is a Library Management System that runs in the terminal. It stores books, members, and borrowings in an SQLite database file (`project.db`) and lets you manage them through a numbered menu.

This guide covers the file from top to bottom, one part at a time.

---

## 1. Imports and constants

```python
import random
import re
import sqlite3
from pathlib import Path
```

| Module | What it is used for |
| --- | --- |
| `random` | Picks random books and members when it creates the demo borrowings |
| `re` | Regular expressions, used to check that an email looks valid |
| `sqlite3` | Python's built-in SQLite database driver |
| `pathlib.Path` | Builds file paths in a way that works on any operating system |

All four come with Python, so there is nothing to install.

```python
DATABASE = Path(__file__).with_name("project.db")
RESULTS = Path(__file__).with_name("results.txt")
EMAIL_PATTERN = r"^[\w.-]+@[\w.-]+\.\w+$"
```

- `__file__` is the path of `main.py` itself.
- `.with_name("project.db")` keeps the folder but swaps the file name. The database and the results file therefore always sit **next to main.py**, no matter which folder you run the program from.
- Names written in CAPITALS are a Python convention for constants, meaning values that never change.
- `EMAIL_PATTERN` is a regular expression. The `r"..."` prefix makes it a raw string, so the backslashes reach `re` unchanged. Here is what each piece means:
  - `^` and `$` mark the start and end of the text.
  - `[\w.-]+` means one or more letters, digits, `_`, `.` or `-`. This is the name part before the `@`.
  - `@` is a literal at sign.
  - `[\w.-]+` is the domain, for example `example`.
  - `\.` is a literal dot. A plain `.` in a regex means "any character", so it has to be escaped.
  - `\w+` is the ending, for example `com`.
  - So `name@example.com` matches, while `bad`, `a@b` and `a b@c.com` do not.

---

## 2. The `Book` class

```python
class Book:
    def __init__(self, book_id, title, author, available):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.available = available
```

- A **class** is a blueprint for objects. Each `Book` object holds the data for one book.
- `__init__` is the **constructor**. Python calls it automatically when you write `Book(1, "Title", "Author", 1)`.
- `self` is the object being created. `self.title = title` stores the argument on the object as an **attribute**.

```python
    def __str__(self):
        status = "Yes" if self.available else "No"
        return f"{self.book_id:<5} {self.title:<30} {self.author:<22} {status}"
```

- `__str__` decides what `print(book)` shows.
- `"Yes" if self.available else "No"` is a **conditional expression**, a one-line if/else. In the database `available` is `1` or `0`. In Python, `1` counts as true and `0` as false.
- The `f"..."` string is an **f-string**: anything inside `{}` is replaced by its value.
- `:<5` means "left-align in a column 5 characters wide". The ID, title, and author are padded to widths 5, 30, and 22, so the rows line up as a table. A longer value is not cut off; it just pushes the rest of the row to the right.

## 3. The `Member` class

```python
class Member:
    def __init__(self, member_id, name, email): ...
    def __str__(self):
        return f"{self.member_id:<5} {self.name:<25} {self.email}"
```

`Member` works exactly like `Book`, but it holds a member's ID, name, and email and prints them in columns 5 and 25 characters wide.

The two classes are used only for **displaying** rows. All the data itself lives in the database.

---

## 4. `connect_database()`

```python
def connect_database():
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
```

- `sqlite3.connect(...)` opens `project.db`. If the file does not exist yet, SQLite creates it.
- `PRAGMA foreign_keys = ON` turns on foreign-key checks. SQLite has them **off by default**, so they must be switched on for every new connection. Without this line, the `ON DELETE CASCADE` rules described below would do nothing.
- The function returns the connection, and every other function receives it as a parameter.

## 5. `create_tables(connection)`

```python
connection.executescript("""
    CREATE TABLE IF NOT EXISTS books (...);
    CREATE TABLE IF NOT EXISTS members (...);
    CREATE TABLE IF NOT EXISTS borrowings (...);
""")
connection.commit()
```

- `executescript` runs several SQL statements at once, separated by `;`.
- `IF NOT EXISTS` means a table is created only the first time. Later runs skip it, so your data is never wiped.
- `commit()` saves the changes to the file.

The tables look like this:

**books**

| Column | Meaning |
| --- | --- |
| `book_id INTEGER PRIMARY KEY AUTOINCREMENT` | Unique ID. SQLite assigns 1, 2, 3, ... and never reuses an ID, even after a deletion |
| `title TEXT NOT NULL` | Required text |
| `author TEXT NOT NULL` | Required text |
| `available INTEGER NOT NULL DEFAULT 1` | 1 = on the shelf, 0 = borrowed. SQLite has no true/false type, so 1 and 0 are used. A new book starts at 1 |

**members**

| Column | Meaning |
| --- | --- |
| `member_id` | Unique auto ID |
| `name TEXT NOT NULL` | Required |
| `email TEXT NOT NULL UNIQUE` | Required, and no two members may share an email. A duplicate raises `sqlite3.IntegrityError` |

**borrowings** (links a book to a member)

| Column | Meaning |
| --- | --- |
| `borrowing_id` | Unique auto ID |
| `book_id ... REFERENCES books(book_id) ON DELETE CASCADE` | **Foreign key**: must be an existing book. If that book is deleted, its borrowings are deleted automatically |
| `member_id ... REFERENCES members(member_id) ON DELETE CASCADE` | Same rule, for members |
| `returned INTEGER NOT NULL DEFAULT 0` | 0 = still borrowed, 1 = returned |

This is a **one-to-many** design: one book can have many borrowings over time, and so can one member.

---

## 6. `add_sample_data(connection)` (demo data)

```python
book_count = connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]
if book_count > 0:
    return
```

- This counts the books. `fetchone()` returns one row as a tuple like `(50,)`, and `[0]` takes the number out of it.
- If any books already exist, the function stops. Demo data is added **only to an empty database**.

```python
random.seed(6)
```

- Seeding makes the "random" choices the **same on every run**, so the demo data is always identical and reproducible.

The lists `titles`, `authors`, `first_names`, and `last_names` are the raw material for the fake data.

**50 books:**
```python
for i in range(50):
    title = titles[i % len(titles)] + " " + str(i // len(titles) + 1)
    author = authors[i % len(authors)]
    connection.execute("INSERT INTO books(title, author) VALUES (?, ?)", (title, author))
```
- `i % 10` is the remainder after dividing by 10. It cycles 0 to 9, so the code walks through the 10 titles again and again.
- `i // 10 + 1` is whole-number division plus one. It gives 1 for i = 0..9, 2 for i = 10..19, and so on up to 5. The titles therefore run "Python Basics 1" ... "Number Patterns 1", then "Python Basics 2" ... up to "Number Patterns 5".
- The authors cycle through the 5 names using `i % 5`.
- The `?` placeholders are **parameterized queries**. SQLite inserts the values safely, which prevents **SQL injection**. Always prefer them over building SQL by gluing strings together.
- `book_id` and `available` are not given, so the defaults apply: an auto ID and 1.

**30 members:**
```python
name = first_names[i % len(first_names)] + " " + last_names[(i * 3) % len(last_names)]
email = "member" + str(i + 1) + "@example.com"
```
- First names cycle in order. Last names jump 3 places each time (0, 3, 6, 9, 2, 5, ...), which mixes the combinations.
- The emails are `member1@example.com` through `member30@example.com`, all unique.
- Both patterns repeat every 10 members, so the names repeat too: member 11 has the same name as member 1. Only the emails differ.

**30 borrowings:**
```python
book_ids = [row[0] for row in connection.execute("SELECT book_id FROM books")]
member_ids = [row[0] for row in connection.execute("SELECT member_id FROM members")]
borrowed_books = random.sample(book_ids, 30)
```
- These two lines are **list comprehensions**. They build plain lists of every book ID and every member ID.
- `random.sample(list, 30)` picks 30 **different** books, so no book is borrowed twice.

```python
for i in range(30):
    book_id = borrowed_books[i]
    member_id = random.choice(member_ids)
    returned = 1 if i % 3 == 0 else 0
    connection.execute("INSERT INTO borrowings(book_id, member_id, returned) VALUES (?, ?, ?)", ...)
    if returned == 0:
        connection.execute("UPDATE books SET available = 0 WHERE book_id = ?", (book_id,))
connection.commit()
```
- `random.choice` picks one random member. The same member can be picked more than once.
- `i % 3 == 0` is true for i = 0, 3, 6, ..., 27, so **10 borrowings are marked returned and 20 are still out**.
- For each borrowing that is still out, the book is marked unavailable (`available = 0`).
- `(book_id,)` has a trailing comma because a one-item tuple needs it. Without the comma, `(book_id)` is just a number in brackets.
- A single `commit()` at the end saves everything at once.

---

## 7. `get_number(message)`

```python
def get_number(message):
    try:
        return int(input(message))
    except ValueError:
        print("Please enter a number.")
        return None
```
- `input(message)` shows the prompt and returns what the user typed, as text.
- `int(...)` converts that text to a whole number. If the text is not a number (like `abc`), Python raises `ValueError`.
- `try/except` **catches** that error, so the program prints a message and returns `None` instead of crashing.
- Callers then check `if ... is None: return` to stop the current action.

---

## 8. `add_book(connection)` (menu 1)

```python
title = input("Book title: ").strip()
author = input("Author: ").strip()
if title == "" or author == "":
    print("Title and author are required.")
    return
connection.execute("INSERT INTO books(title, author) VALUES (?, ?)", (title, author))
connection.commit()
print("Book added.")
```
- `.strip()` removes spaces at the start and end, so a title made only of spaces becomes `""`.
- If either field is empty, the function prints an error and `return`s early without saving anything.
- Otherwise it inserts the book, which is available by default, and commits.

## 9. `add_member(connection)` (menu 2)

```python
if name == "" or re.fullmatch(EMAIL_PATTERN, email) is None:
    print("Enter a name and a valid email, for example name@example.com.")
    return
try:
    connection.execute("INSERT INTO members(name, email) VALUES (?, ?)", (name, email))
    connection.commit()
    print("Member added.")
except sqlite3.IntegrityError:
    print("That email is already registered.")
```
- `re.fullmatch` returns a match object if the **whole** email matches the pattern, and `None` otherwise.
- The `try/except` catches the database error raised by the `UNIQUE` rule on `email`, so a duplicate email gives a friendly message instead of a crash.

---

## 10. `show_books(connection, available_only=False)` (menus 4 and 6)

```python
if available_only:
    rows = connection.execute("SELECT ... FROM books WHERE available=1 ORDER BY title")
else:
    rows = connection.execute("SELECT ... FROM books ORDER BY title")
print("ID    TITLE                          AUTHOR                 AVAILABLE")
for row in rows:
    print(Book(row[0], row[1], row[2], row[3]))
```
- `available_only=False` is a **default argument**. A plain call `show_books(connection)` lists every book, while `show_books(connection, available_only=True)` (menu 6) lists only the books on the shelf.
- `ORDER BY title` sorts the list alphabetically.
- Each `row` is a tuple `(book_id, title, author, available)`. The code turns it into a `Book` object, and `print` calls that object's `__str__`.
- The header line is spaced by hand so it lines up with the `:<5`, `:<30`, `:<22` column widths.

## 11. `show_members(connection)`

This lists all members sorted by name, printed through `Member.__str__`.

## 12. `show_borrowings(connection)`

```sql
SELECT borrowings.borrowing_id, books.title, members.name, borrowings.returned
FROM borrowings JOIN books ON borrowings.book_id=books.book_id
JOIN members ON borrowings.member_id=members.member_id
ORDER BY borrowings.borrowing_id
```
- The `borrowings` table stores only ID numbers. A **JOIN** combines it with `books` and `members` so the output can show the actual book title and member name.
- `ON borrowings.book_id=books.book_id` tells SQLite which rows belong together.
- Then `"Returned" if row[3] else "Borrowed"` turns 1 or 0 into a word.

## 13. `display_records(connection)` (menu 4)

```python
choice = input("Display (b)ooks, (m)embers, or bo(r)rowings? ").strip().lower()
```
`.lower()` makes `B` and `b` both work. The function then calls `show_books`, `show_members`, or `show_borrowings`, or prints "Choose b, m, or r." for anything else.

---

## 14. `borrow_book(connection)` (menu 3)

```python
book_id = get_number("Book ID: ")
member_id = get_number("Member ID: ")
if book_id is None or member_id is None:
    return
book = connection.execute("SELECT available FROM books WHERE book_id=?", (book_id,)).fetchone()
member = connection.execute("SELECT member_id FROM members WHERE member_id=?", (member_id,)).fetchone()
```
- It reads both IDs, and stops if either one was not a number.
- `fetchone()` returns `None` if no row matched, which means the book or member does not exist.

```python
if book is None or member is None:
    print("Book or member was not found.")
elif book[0] == 0:
    print("That book is already borrowed.")
else:
    connection.execute("INSERT INTO borrowings(book_id, member_id) VALUES (?, ?)", ...)
    connection.execute("UPDATE books SET available=0 WHERE book_id=?", (book_id,))
    connection.commit()
    print("Borrowing saved.")
```
- There are three outcomes: not found, already borrowed (`available` is 0), or success.
- On success it does **two** things: it adds a borrowing row (with `returned` defaulting to 0) and marks the book unavailable. One `commit()` saves both together.

---

## 15. `search_records(connection)` (menu 5)

**Books by title:**
```python
rows = connection.execute(
    "SELECT ... FROM books WHERE title LIKE ? ORDER BY title",
    ("%" + title + "%",),
)
```
- `LIKE` does pattern matching. `%` means "any characters", so `%Python%` finds every title that **contains** "Python". In SQLite, `LIKE` ignores upper and lower case for English letters.
- `found = False` is a **flag**. It becomes `True` as soon as one row prints. If it is still `False` after the loop, the function prints "No books found."

**Members by name or ID:**
```sql
WHERE name LIKE ? OR CAST(member_id AS TEXT)=?
```
- The same text is checked two ways. Either the name contains it, or the ID equals it exactly. `CAST(member_id AS TEXT)` turns the number into text so it can be compared with what the user typed.
- Typing `5` therefore finds member 5, plus anyone whose name contains a "5".

---

## 16. `update_book(connection)` (menu 7)

```python
cursor = connection.execute("UPDATE books SET title=?, author=? WHERE book_id=?", (title, author, book_id))
connection.commit()
print("Book updated." if cursor.rowcount else "Book not found.")
```
- It asks for the ID, a new title, and a new author (both required).
- `cursor.rowcount` is the number of rows the UPDATE changed. A count of 0 means no book had that ID, so it prints "Book not found."

## 17. `delete_record(connection)` (menu 8)

```python
choice = input("Delete a (b)ook or cancel a borrowing (r)? ").strip().lower()
record_id = get_number("ID: ")
```
- It asks for the ID straight away, before checking whether the choice was `b` or `r`. An invalid choice is only reported after the ID is typed.

**Deleting a book (`b`):**
```python
cursor = connection.execute("DELETE FROM books WHERE book_id=?", (record_id,))
```
- Because of `ON DELETE CASCADE` and the `PRAGMA` from step 4, every borrowing of that book is deleted automatically.
- `rowcount` again tells the program whether a book was actually found.

**Cancelling a borrowing (`r`):**
```python
row = connection.execute("SELECT book_id, returned FROM borrowings WHERE borrowing_id=?", ...).fetchone()
...
connection.execute("DELETE FROM borrowings WHERE borrowing_id=?", (record_id,))
if row[1] == 0:
    connection.execute("UPDATE books SET available=1 WHERE book_id=?", (row[0],))
```
- First it reads the borrowing to learn which book it was for and whether it was already returned.
- Then it deletes the borrowing.
- If the book was still out (`returned == 0`), the book goes back on the shelf (`available = 1`). If it had already been returned, the book is already available, so nothing else changes.

---

## 18. `show_statistics(connection)` (menu 9)

```python
total = connection.execute("SELECT COUNT(*) FROM borrowings").fetchone()[0]
active = connection.execute("SELECT COUNT(*) FROM borrowings WHERE returned=0").fetchone()[0]
most_borrowed = connection.execute("""
    SELECT books.title, COUNT(*) AS total
    FROM borrowings JOIN books ON borrowings.book_id = books.book_id
    GROUP BY books.book_id ORDER BY total DESC, books.title LIMIT 1
""").fetchone()
```
- `COUNT(*)` counts rows. That gives all borrowings, and then only the active ones.
- The "most borrowed" query works in steps:
  1. JOIN borrowings with books to get each title.
  2. `GROUP BY books.book_id` puts all borrowings of the same book into one group.
  3. `COUNT(*) AS total` counts each group and names the result `total`.
  4. `ORDER BY total DESC, books.title` puts the highest count first, and breaks ties alphabetically.
  5. `LIMIT 1` keeps only the top row.
- With the demo data every book was borrowed at most once, so all of them tie at 1, and the alphabetically first title, "A Long Journey 1", wins.
- `if most_borrowed:` protects against an empty table. With no borrowings the query returns `None`, and nothing is printed for that line.

## 19. `export_results(connection)` (menu 10)

```python
with open(RESULTS, "w", encoding="utf-8") as file:
    file.write(...)
```
- It runs the same statistics queries as menu 9, plus a count of books and members.
- `open(..., "w")` opens `results.txt` for writing and **replaces** the file each time. `encoding="utf-8"` makes any characters save correctly.
- `with ... as file:` closes the file automatically, even if an error happens.
- `str(...)` converts numbers to text, because `write` accepts only strings.
- It then writes every borrowing as `ID | title | member | status`, using the same JOIN as `show_borrowings`.

---

## 20. `show_menu()`

This prints the menu text. The triple quotes `"""..."""` allow a string that spans several lines.

## 21. `main()`, the program loop

```python
def main():
    connection = connect_database()
    create_tables(connection)
    add_sample_data(connection)
    print("Demo data ready: 50 books, 30 members, and 30 borrowings.")
```
1. Open the database.
2. Make sure the tables exist.
3. Add demo data if the database is empty.
4. Print a welcome line. The message is fixed text, so it says "50 books" even after you add or delete some.

```python
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_book(connection)
        elif choice == "2":
            ...
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Please choose one of the menu numbers.")
    connection.close()
```
- `while True` is an **infinite loop**: it repeats until something stops it.
- The choice is compared as **text** (`"1"`, not `1`), so no number conversion is needed and typing letters cannot crash it.
- The `if/elif` chain sends each choice to its function, and the same `connection` is passed to every function.
- `break` (option 0) leaves the loop, and then `connection.close()` closes the database cleanly.
- Anything else prints an error, and the loop shows the menu again.

## 22. Entry point

```python
if __name__ == "__main__":
    main()
```
- Python sets `__name__` to `"__main__"` only when you run the file directly (`python3 main.py`).
- If another file does `import main`, this check is false, so the menu does **not** start, and the functions can be reused or tested on their own.

---

## Key ideas summary

| Concept | Where it appears |
| --- | --- |
| Classes, `__init__`, `__str__` | `Book`, `Member` |
| SQLite tables, primary keys, foreign keys, cascade | `create_tables` |
| Parameterized queries (`?`) against SQL injection | every query with user input |
| `commit()` to save changes | after every INSERT, UPDATE, DELETE |
| JOIN, GROUP BY, COUNT, ORDER BY, LIMIT, LIKE | display, search, statistics |
| Input validation (`strip`, empty check, regex, `try/except`) | `get_number`, `add_book`, `add_member` |
| Error handling for database rules | `IntegrityError` in `add_member` |
| File writing with `with open` | `export_results` |
| Menu loop with `while True` and `break` | `main` |

## Things worth knowing (no changes made)

- There is no "return a book" option. Nothing in the menu sets `returned` to 1; only the demo data uses it. "Cancel a borrowing" deletes the record instead.
- Members can be added but not updated or deleted from the menu.
- Pressing Ctrl+C or Ctrl+D at a prompt stops the program with an error message (`KeyboardInterrupt` or `EOFError`). Nothing is lost, because every change is committed right away.
