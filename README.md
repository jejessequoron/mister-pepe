# Library Management System

A command-line library management system written in Python with an SQLite database. It keeps track of books, members, and borrowings through a simple numbered menu.

## Requirements

- Python 3.8 or newer
- No third-party packages; it only uses the standard library (`sqlite3`, `re`, `random`, `pathlib`)

## How to run

```bash
python3 main.py
```

On first start the program creates the tables in `project.db` (next to `main.py`) and fills them with demo data if the database is empty: 50 books, 30 members, and 30 borrowings. The included `project.db` already contains this data.

## Menu

| Option | Action |
| --- | --- |
| 1 | Add a book |
| 2 | Add a member (email is validated and must be unique) |
| 3 | Borrow a book (checks that the book and member exist and the book is available) |
| 4 | Display books, members, or borrowings |
| 5 | Search books by title, or members by name or ID |
| 6 | Show available books |
| 7 | Update a book's title and author |
| 8 | Delete a book, or cancel a borrowing (the book becomes available again) |
| 9 | Show statistics: total borrowings, books currently borrowed, most borrowed book |
| 10 | Export a summary and all borrowings to `results.txt` |
| 0 | Exit |

## Database

`project.db` has three tables:

- `books` (`book_id`, `title`, `author`, `available`)
- `members` (`member_id`, `name`, `email` unique)
- `borrowings` (`borrowing_id`, `book_id`, `member_id`, `returned`), with foreign keys to `books` and `members` that cascade on delete

## Project structure

```
main.py      # the program: Book and Member classes, database functions, menu loop
project.db   # SQLite database with demo data
```
