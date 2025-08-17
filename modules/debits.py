import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Toplevel, BOTH, END, messagebox
from modules.db_manager import get_connection, return_connection

def debits_screen(master):
    """
    Manage pending or paid debits.
    """
    db_win = Toplevel(master)
    db_win.title("Manage Debits")
    db_win.geometry("1024x600")

    def load_debits():
        debits_table.delete(*debits_table.get_children())
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DebitID, Name, Phone, Status, Date
                FROM Debits
                ORDER BY DebitID DESC
            """)
            rows = cursor.fetchall()
            return_connection(conn)
            for row in rows:
                values = (row[0], "", row[1], row[2], row[3], "", row[4])
                debits_table.insert("", END, values=values)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading debits: {e}")

    def mark_as_paid():
        selected = debits_table.selection()
        if not selected:
            messagebox.showwarning("Warning", "No debit selected!")
            return
        item_id = selected[0]
        debit_id = debits_table.item(item_id, "values")[0]
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Debits SET Status = 'Paid' WHERE DebitID = ?", (debit_id,))
            conn.commit()
            return_connection(conn)
            messagebox.showinfo("Success", f"Debit {debit_id} marked as Paid!")
            load_debits()
        except Exception as e:
            messagebox.showerror("Error", f"Error marking debit as paid: {e}")

    def view_invoice_items():
        selected = debits_table.selection()
        if not selected:
            messagebox.showwarning("Warning", "No debit selected!")
            return
        item_id = selected[0]
        debit_values = debits_table.item(item_id, "values")
        debit_id = debit_values[0]
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT InvoiceID, Amount FROM Debits WHERE DebitID = ?", (debit_id,))
            row = cursor.fetchone()
            if not row:
                return_connection(conn)
                messagebox.showerror("Error", "Could not find Invoice/Amount for this debit.")
                return
            invoice_id, amount = row
            return_connection(conn)
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching debit details: {e}")
            return

        detail_win = Toplevel(db_win)
        detail_win.title(f"Debit {debit_id} Details")
        detail_win.geometry("600x400")

        top_info_frame = ttk.Frame(detail_win, padding=10)
        top_info_frame.pack(fill=BOTH, padx=10, pady=10)
        ttk.Label(top_info_frame, text=f"Invoice ID: {invoice_id}", font=("Helvetica", 14, "bold")).pack(side="left", padx=10)
        ttk.Label(top_info_frame, text=f"Amount: ${amount:.2f}", font=("Helvetica", 14, "bold")).pack(side="left", padx=20)

        inv_table = ttk.Treeview(detail_win, columns=("Product", "Price", "Qty"), show="headings")
        inv_table.heading("Product", text="Product", anchor="w")
        inv_table.heading("Price", text="Price", anchor="e")
        inv_table.heading("Qty", text="Qty", anchor="center")
        inv_table.column("Product", anchor="w", width=250, minwidth=250, stretch=True)
        inv_table.column("Price", anchor="e", width=100, minwidth=100, stretch=False)
        inv_table.column("Qty", anchor="center", width=80, minwidth=80, stretch=False)
        inv_table.pack(fill=BOTH, expand=True, padx=10, pady=10)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ProductName, Price, Quantity FROM InvoiceItems WHERE InvoiceID = ?", (invoice_id,))
            rows = cursor.fetchall()
            return_connection(conn)
            for item in rows:
                inv_table.insert("", END, values=(item[0], f"{item[1]:.2f}", item[2]))
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching invoice items: {e}")

    ttk.Label(db_win, text="Manage Debits", font=("Helvetica", 24, "bold")).pack(pady=10)
    table_frame = ttk.Frame(db_win)
    table_frame.pack(padx=20, pady=10, fill=BOTH, expand=True)

    debits_table = ttk.Treeview(table_frame,
                                columns=("DebitID", "Spacer1", "Name", "Phone", "Status", "Spacer2", "Date"),
                                show="headings")
    debits_table.column("#0", width=0, stretch=False)
    debits_table.heading("DebitID", text="ID", anchor="center")
    debits_table.heading("Spacer1", text="", anchor="center")
    debits_table.heading("Name", text="Name", anchor="w")
    debits_table.heading("Phone", text="Phone", anchor="w")
    debits_table.heading("Status", text="Status", anchor="center")
    debits_table.heading("Spacer2", text="", anchor="center")
    debits_table.heading("Date", text="Date", anchor="w")
    debits_table.column("DebitID", anchor="center", width=80, minwidth=80, stretch=False)
    debits_table.column("Spacer1", anchor="center", width=20, minwidth=20, stretch=False)
    debits_table.column("Name", anchor="w", width=250, minwidth=250, stretch=True)
    debits_table.column("Phone", anchor="w", width=200, minwidth=200, stretch=True)
    debits_table.column("Status", anchor="center", width=100, minwidth=100, stretch=False)
    debits_table.column("Spacer2", anchor="center", width=20, minwidth=20, stretch=False)
    debits_table.column("Date", anchor="w", width=250, minwidth=250, stretch=True)
    debits_table.pack(fill=BOTH, expand=True)

    action_frame = ttk.Frame(db_win)
    action_frame.pack(pady=10)
    ttk.Button(action_frame, text="Mark as Paid", bootstyle=SUCCESS, command=mark_as_paid).grid(row=0, column=0, padx=10)
    ttk.Button(action_frame, text="View Invoice Items", bootstyle=INFO, command=view_invoice_items).grid(row=0, column=1, padx=10)

    load_debits()

if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    root.title("Main Window")
    ttk.Button(root, text="Manage Debits", command=lambda: debits_screen(root)).pack(padx=20, pady=20)
    root.mainloop()

