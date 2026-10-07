import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

DB_NAME = "library.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            available INTEGER DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS issued_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY(book_id) REFERENCES books(id)
        )
    """)
    conn.commit()
    conn.close()

def refresh_books():
    for item in book_tree.get_children():
        book_tree.delete(item)
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute(
        "SELECT id, title, author, isbn, available FROM books ORDER BY id DESC"
    ).fetchall()
    conn.close()
    for row in rows:
        status = "Available" if row[4] else "Issued"
        book_tree.insert("", "end", values=(row[0], row[1], row[2], row[3] or "-", status))

def add_book():
    title = title_var.get().strip()
    author = author_var.get().strip()
    isbn = isbn_var.get().strip()

    if not title or not author:
        messagebox.showwarning("Missing data", "Enter book title and author.")
        return

    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            "INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)",
            (title, author, isbn or None)
        )
        conn.commit()
        messagebox.showinfo("Success", "Book added successfully.")
        title_var.set("")
        author_var.set("")
        isbn_var.set("")
        refresh_books()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "This ISBN already exists.")
    finally:
        conn.close()

def issue_book():
    selected = book_tree.selection()
    student = student_var.get().strip()

    if not selected:
        messagebox.showwarning("Select book", "Select an available book first.")
        return
    if not student:
        messagebox.showwarning("Missing data", "Enter student name.")
        return

    book_id = book_tree.item(selected[0])["values"][0]
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT available FROM books WHERE id = ?", (book_id,))
    row = cur.fetchone()

    if not row or not row[0]:
        messagebox.showerror("Unavailable", "This book is already issued.")
        conn.close()
        return

    cur.execute(
        "INSERT INTO issued_books (book_id, student_name, issue_date) VALUES (?, ?, ?)",
        (book_id, student, date.today().isoformat())
    )
    cur.execute("UPDATE books SET available = 0 WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    student_var.set("")
    refresh_books()
    messagebox.showinfo("Success", "Book issued successfully.")

def return_book():
    selected = book_tree.selection()
    if not selected:
        messagebox.showwarning("Select book", "Select an issued book first.")
        return

    book_id = book_tree.item(selected[0])["values"][0]
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM issued_books WHERE book_id = ? AND return_date IS NULL",
        (book_id,)
    )
    row = cur.fetchone()

    if not row:
        messagebox.showinfo("Info", "This book is not currently issued.")
        conn.close()
        return

    cur.execute(
        "UPDATE issued_books SET return_date = ? WHERE id = ?",
        (date.today().isoformat(), row[0])
    )
    cur.execute("UPDATE books SET available = 1 WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    refresh_books()
    messagebox.showinfo("Success", "Book returned successfully.")

def search_books():
    keyword = search_var.get().strip()
    for item in book_tree.get_children():
        book_tree.delete(item)

    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT id, title, author, isbn, available
        FROM books
        WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
        ORDER BY id DESC
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")).fetchall()
    conn.close()

    for row in rows:
        status = "Available" if row[4] else "Issued"
        book_tree.insert("", "end", values=(row[0], row[1], row[2], row[3] or "-", status))

init_db()

root = tk.Tk()
root.title("Library Management System")
root.geometry("900x600")
root.minsize(800, 520)

title_var = tk.StringVar()
author_var = tk.StringVar()
isbn_var = tk.StringVar()
student_var = tk.StringVar()
search_var = tk.StringVar()

header = ttk.Frame(root, padding=15)
header.pack(fill="x")
ttk.Label(header, text="Library Management System",
          font=("Arial", 22, "bold")).pack(anchor="w")
ttk.Label(header, text="Python + Tkinter + SQLite",
          font=("Arial", 10)).pack(anchor="w")

form = ttk.LabelFrame(root, text="Add New Book", padding=12)
form.pack(fill="x", padx=15, pady=5)

ttk.Label(form, text="Title").grid(row=0, column=0, sticky="w", padx=5, pady=5)
ttk.Entry(form, textvariable=title_var, width=28).grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form, text="Author").grid(row=0, column=2, sticky="w", padx=5, pady=5)
ttk.Entry(form, textvariable=author_var, width=25).grid(row=0, column=3, padx=5, pady=5)

ttk.Label(form, text="ISBN").grid(row=0, column=4, sticky="w", padx=5, pady=5)
ttk.Entry(form, textvariable=isbn_var, width=20).grid(row=0, column=5, padx=5, pady=5)

ttk.Button(form, text="Add Book", command=add_book).grid(
    row=0, column=6, padx=8, pady=5
)

actions = ttk.Frame(root, padding=(15, 5))
actions.pack(fill="x")

ttk.Label(actions, text="Student Name").pack(side="left", padx=5)
ttk.Entry(actions, textvariable=student_var, width=25).pack(side="left", padx=5)
ttk.Button(actions, text="Issue Selected", command=issue_book).pack(side="left", padx=5)
ttk.Button(actions, text="Return Selected", command=return_book).pack(side="left", padx=5)

search_frame = ttk.Frame(root, padding=(15, 5))
search_frame.pack(fill="x")
ttk.Label(search_frame, text="Search").pack(side="left", padx=5)
search_entry = ttk.Entry(search_frame, textvariable=search_var, width=35)
search_entry.pack(side="left", padx=5)
ttk.Button(search_frame, text="Search", command=search_books).pack(side="left", padx=5)
ttk.Button(search_frame, text="Show All", command=refresh_books).pack(side="left", padx=5)

table_frame = ttk.Frame(root, padding=15)
table_frame.pack(fill="both", expand=True)

columns = ("ID", "Title", "Author", "ISBN", "Status")
book_tree = ttk.Treeview(table_frame, columns=columns, show="headings")

for col in columns:
    book_tree.heading(col, text=col)

book_tree.column("ID", width=50, anchor="center")
book_tree.column("Title", width=250)
book_tree.column("Author", width=180)
book_tree.column("ISBN", width=150)
book_tree.column("Status", width=100, anchor="center")

scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=book_tree.yview)
book_tree.configure(yscrollcommand=scrollbar.set)

book_tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

refresh_books()
root.mainloop()
