import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog


class CinemaDatabase:
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self.conn = sqlite3.connect(db_filename)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY,
                    nameMovie TEXT NOT NULL,
                    data TEXT NOT NULL,
                    time TEXT NOT NULL,
                    hall INTEGER NOT NULL,
                    seat INTEGER NOT NULL,
                    price REAL NOT NULL
                )
            ''')

    def add_record(self, record):
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO records (id, nameMovie, data, time, hall, seat, price) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (record['id'], record['nameMovie'], record['data'], record['time'], record['hall'], record['seat'], record['price'])
                )
        except sqlite3.IntegrityError:
            raise ValueError("ID already exists.")

    def delete_record(self, field, value):
        with self.conn:
            self.conn.execute(f"DELETE FROM records WHERE {field} = ?", (value,))

    def search_records(self, field, value):
        with self.conn:
            cursor = self.conn.execute(f"SELECT * FROM records WHERE {field} = ?", (value,))
            return cursor.fetchall()

    def update_record(self, record_id, updated_record):
        with self.conn:
            self.conn.execute(
                "UPDATE records SET id = ?, nameMovie = ?, data = ?, time = ?, hall = ?, seat = ?, price = ? WHERE id = ?",
                (updated_record['id'], updated_record['nameMovie'], updated_record['data'], updated_record['time'],
                 updated_record['hall'], updated_record['seat'], updated_record['price'], record_id)
            )

    def export_to_excel(self, export_filename):
        import xlsxwriter
        with self.conn:
            cursor = self.conn.execute("SELECT * FROM records")
            data = cursor.fetchall()

        workbook = xlsxwriter.Workbook(export_filename)
        worksheet = workbook.add_worksheet()
        headers = ['id', 'nameMovie', 'data', 'time', 'hall', 'seat', 'price']

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        for row, record in enumerate(data, start=1):
            for col, value in enumerate(record):
                worksheet.write(row, col, value)

        workbook.close()

    def clear_database(self):
        with self.conn:
            self.conn.execute("DELETE FROM records")

    def delete_database(self):
        self.conn.close()
        import os
        os.remove(self.db_filename)

    def create_backup(self, backup_filename):
        import shutil
        self.conn.close()
        shutil.copy(self.db_filename, backup_filename)
        self.conn = sqlite3.connect(self.db_filename)

    def restore_backup(self, backup_filename):
        import shutil
        self.conn.close()
        shutil.copy(backup_filename, self.db_filename)
        self.conn = sqlite3.connect(self.db_filename)


class CinemaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cinema Database")
        self.db = CinemaDatabase("cinema_db.sqlite")

        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(self.frame, columns=("id", "nameMovie", "data", "time", "hall", "seat", "price"), show="headings")
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.add_buttons()
        self.load_data()

    def add_buttons(self):
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Add Record", command=self.add_record).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Delete Record", command=self.delete_record).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Search", command=self.search_records).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Update Record", command=self.update_record).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Export to Excel", command=self.export_to_excel).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Backup", command=self.create_backup).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Restore Backup", command=self.restore_backup).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Clear Database", command=self.clear_database).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Delete Database", command=self.delete_database).pack(side=tk.LEFT)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        with self.db.conn:
            cursor = self.db.conn.execute("SELECT * FROM records")
            for record in cursor:
                self.tree.insert('', tk.END, values=record)

    def add_record(self):
        record = self.get_record_from_user()
        if record:
            try:
                self.db.add_record(record)
                self.load_data()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    def delete_record(self):
        field, value = self.get_field_value_from_user()
        if field and value:
            self.db.delete_record(field, value)
            self.load_data()

    def search_records(self):
        field, value = self.get_field_value_from_user()
        if field and value:
            results = self.db.search_records(field, value)
            for row in self.tree.get_children():
                self.tree.delete(row)
            for record in results:
                self.tree.insert('', tk.END, values=record)

    def update_record(self):
        record_id = simpledialog.askstring("Update", "Enter ID to update:")
        if record_id:
            updated_record = self.get_record_from_user()
            if updated_record:
                self.db.update_record(record_id, updated_record)
                self.load_data()

    def export_to_excel(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if filename:
            self.db.export_to_excel(filename)

    def create_backup(self):
        filename = filedialog.asksaveasfilename(defaultextension=".sqlite", filetypes=[("SQLite files", "*.sqlite")])
        if filename:
            self.db.create_backup(filename)

    def restore_backup(self):
        filename = filedialog.askopenfilename(filetypes=[("SQLite files", "*.sqlite")])
        if filename:
            self.db.restore_backup(filename)
            self.load_data()

    def clear_database(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all data?"):
            self.db.clear_database()
            self.load_data()

    def delete_database(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete the database file?"):
            self.db.delete_database()
            self.root.destroy()

    def get_record_from_user(self):
        import re
        fields = ['id', 'nameMovie', 'data', 'time', 'hall', 'seat', 'price']
        record = {}

        for field in fields:
            while True:
                value = simpledialog.askstring("Input", f"Enter {field}:")
                if not value:
                    return None

                if field == 'id' or field == 'hall' or field == 'seat':
                    if not value.isdigit():
                        messagebox.showerror("Invalid Input", f"{field} must be a positive integer.")
                        continue
                    value = int(value)
                elif field == 'price':
                    try:
                        value = float(value)
                    except ValueError:
                        messagebox.showerror("Invalid Input", f"{field} must be a number.")
                        continue
                elif field == 'data':
                    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                        messagebox.showerror("Invalid Input", "Date must be in YYYY-MM-DD format.")
                        continue
                elif field == 'time':
                    if not re.match(r"^\d{2}:\d{2}$", value):
                        messagebox.showerror("Invalid Input", "Time must be in HH:MM format.")
                        continue

                record[field] = value
                break

        return record

    def get_field_value_from_user(self):
        field = simpledialog.askstring("Input", "Enter field:")
        value = simpledialog.askstring("Input", "Enter value:")
        return field, value


if __name__ == "__main__":
    root = tk.Tk()
    app = CinemaApp(root)
    root.mainloop()
