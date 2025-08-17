import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, END, X, BOTH
import os
from PIL import Image, ImageTk
from modules.db_manager import get_connection, return_connection

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def manage_inventory(master):
    """
    Opens the Inventory Management main window.
    Displays categories as large icons. Clicking on a category opens a new window with items.
    """
    inv_win = ttk.Toplevel(master)
    inv_win.title("Inventory Management")
    inv_win.geometry("1024x768")

    categories = [
        "Juice",
        "Eggs",
        "Snacks",
        "Milk & Dairy",
        "Ice Cream",
        "Staple Food"
    ]

    category_icons = {
        "Juice": os.path.join(base_dir, "assets", "categories", "juice.png"),
        "Eggs": os.path.join(base_dir, "assets", "categories", "eggs.png"),
        "Snacks": os.path.join(base_dir, "assets", "categories", "snacks.png"),
        "Milk & Dairy": os.path.join(base_dir, "assets", "categories", "milk_dairy.png"),
        "Ice Cream": os.path.join(base_dir, "assets", "categories", "ice_cream.png"),
        "Staple Food": os.path.join(base_dir, "assets", "categories", "staplefood.png"),
    }

    # Load icons for categories
    loaded_icons = {}
    for cat, icon_path in category_icons.items():
        if os.path.exists(icon_path):
            img = Image.open(icon_path).resize((120, 120), Image.Resampling.LANCZOS)
            loaded_icons[cat] = ImageTk.PhotoImage(img)
        else:
            loaded_icons[cat] = None
            print(f"Warning: Icon not found for category {cat}: {icon_path}")

    def open_category_items(category):
        """Opens a new window displaying items for the selected category."""
        show_items_for_category(inv_win, category)

    # Header Frame
    header_frame = ttk.Frame(inv_win, padding=20)
    header_frame.pack(fill=X)
    ttk.Label(header_frame, text="Inventory Management", font=("Helvetica", 28, "bold")).pack()

    # Categories Grid Frame
    category_frame = ttk.Labelframe(inv_win, text="Categories", padding=30)
    category_frame.pack(pady=40)

    row, col = 0, 0
    for category in categories:
        icon = loaded_icons.get(category)
        if icon:
            btn = ttk.Button(category_frame, image=icon, text=category, compound=TOP,
                             bootstyle=SECONDARY, command=lambda c=category: open_category_items(c))
            btn.image = icon  # keep a reference to prevent garbage collection
        else:
            btn = ttk.Button(category_frame, text=category, bootstyle=SECONDARY,
                             command=lambda c=category: open_category_items(c))
        btn.grid(row=row, column=col, padx=30, pady=30, sticky="nsew")
        col += 1
        if col > 2:
            col = 0
            row += 1

def show_items_for_category(master, category):
    """
    Display items for the selected category in a new window.
    """
    cat_win = ttk.Toplevel(master)
    cat_win.title(f"{category} Items")
    cat_win.geometry("1024x768")

    # Configure style for the Treeview
    style = ttk.Style()
    style.configure("Treeview", font=("Helvetica", 16), rowheight=35)
    style.configure("Treeview.Heading", font=("Helvetica", 16, "bold"))
    style.map("Treeview", background=[("selected", "#1E3F66")], foreground=[("selected", "white")])

    def fetch_products(category):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ProductID, Name, Price, Stock FROM Products WHERE Category = ?", (category,))
        rows = cursor.fetchall()
        return_connection(conn)
        return rows

    def refresh_table():
        stock_table.delete(*stock_table.get_children())
        products = fetch_products(category)
        for i, product in enumerate(products):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            stock_table.insert("", END, values=product, tags=(tag,))

    def add_product():
        name = name_entry.get().strip()
        price = price_entry.get().strip()
        stock = stock_entry.get().strip()

        if not name or not price or not stock:
            messagebox.showwarning("Warning", "All fields are required!", parent=cat_win)
            return

        try:
            price_val = float(price)
            stock_val = int(stock)
        except ValueError:
            messagebox.showwarning("Warning", "Price must be a number and Stock must be an integer!", parent=cat_win)
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Products (Name, Price, Stock, Category) VALUES (?, ?, ?, ?)",
                       (name, price_val, stock_val, category))
        conn.commit()
        return_connection(conn)

        messagebox.showinfo("Success", "Product added successfully!", parent=cat_win)

        # Clear fields after adding
        name_entry.delete(0, END)
        price_entry.delete(0, END)
        stock_entry.delete(0, END)
        refresh_table()

    def update_stock(item_id_str, delta):
        item_id_str = item_id_str.strip()
        if not item_id_str:
            messagebox.showwarning("Warning", "Please enter a valid Product ID!", parent=cat_win)
            return
        try:
            item_id = int(item_id_str)
        except ValueError:
            messagebox.showwarning("Warning", "Product ID must be a number!", parent=cat_win)
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Products SET Stock = Stock + ? WHERE ProductID = ?", (delta, item_id))
        conn.commit()
        return_connection(conn)
        refresh_table()

    def delete_product(item_id_str):
        item_id_str = item_id_str.strip()
        if not item_id_str:
            messagebox.showwarning("Warning", "Please enter a valid Product ID to delete!", parent=cat_win)
            return
        try:
            item_id = int(item_id_str)
        except ValueError:
            messagebox.showwarning("Warning", "Product ID must be a number!", parent=cat_win)
            return

        confirm = messagebox.askyesno("Confirm Deletion",
                                      f"Are you sure you want to delete the product with ID {item_id}?",
                                      parent=cat_win)
        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Products WHERE ProductID = ?", (item_id,))
        conn.commit()
        return_connection(conn)

        messagebox.showinfo("Success", f"Product with ID {item_id} deleted.", parent=cat_win)
        refresh_table()

    # Header Frame
    header_frame = ttk.Frame(cat_win, padding=20)
    header_frame.pack(fill=X)
    ttk.Label(header_frame, text=f"{category} Inventory", font=("Helvetica", 28, "bold")).pack()

    # Products Table Frame
    table_frame = ttk.Labelframe(cat_win, text="Products", padding=10)
    table_frame.pack(padx=20, pady=20, fill=BOTH, expand=True)

    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")

    stock_table = ttk.Treeview(table_frame, columns=("ID", "Name", "Price", "Stock"),
                               show="headings", yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    stock_table.heading("ID", text="ID", anchor=CENTER)
    stock_table.heading("Name", text="Name", anchor=W)
    stock_table.heading("Price", text="Price", anchor=E)
    stock_table.heading("Stock", text="Stock", anchor=E)
    stock_table.column("ID", width=80, anchor=CENTER)
    stock_table.column("Name", width=350, anchor=W)
    stock_table.column("Price", width=100, anchor=E)
    stock_table.column("Stock", width=150, anchor=E)
    vsb.config(command=stock_table.yview)
    hsb.config(command=stock_table.xview)
    stock_table.pack(side="left", fill=BOTH, expand=True)
    vsb.pack(side="right", fill=Y)
    hsb.pack(side="bottom", fill=X)

    stock_table.tag_configure('evenrow', background="#E1E1E1", foreground="black")
    stock_table.tag_configure('oddrow', background="#D8D8D8", foreground="black")

    ttk.Separator(cat_win, orient=HORIZONTAL).pack(fill=X, pady=10)

    bottom_frame = ttk.Frame(cat_win)
    bottom_frame.pack(padx=20, pady=20, fill=X)

    form_font = ("Helvetica", 16)
    form_frame = ttk.Labelframe(bottom_frame, text="Add New Product", padding=10)
    form_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")

    ttk.Label(form_frame, text="Name", anchor=E, font=form_font).grid(row=0, column=0, padx=5, pady=5, sticky=E)
    name_entry = ttk.Entry(form_frame, width=30, font=form_font)
    name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)

    ttk.Label(form_frame, text="Price", anchor=E, font=form_font).grid(row=1, column=0, padx=5, pady=5, sticky=E)
    price_entry = ttk.Entry(form_frame, width=30, font=form_font)
    price_entry.grid(row=1, column=1, padx=5, pady=5, sticky=W)

    ttk.Label(form_frame, text="Stock", anchor=E, font=form_font).grid(row=2, column=0, padx=5, pady=5, sticky=E)
    stock_entry = ttk.Entry(form_frame, width=30, font=form_font)
    stock_entry.grid(row=2, column=1, padx=5, pady=5, sticky=W)

    ttk.Label(form_frame, text=f"Category: {category}", anchor=E, font=("Helvetica", 16, "italic")).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    ttk.Button(form_frame, text="Add Product", bootstyle=SUCCESS, command=add_product).grid(row=4, columnspan=2, pady=20)

    adjust_frame = ttk.Labelframe(bottom_frame, text="Manage Items", padding=10)
    adjust_frame.grid(row=0, column=1, padx=20, pady=20, sticky="n")

    ttk.Label(adjust_frame, text="Product ID", anchor=E, font=form_font).grid(row=0, column=0, padx=5, pady=5, sticky=E)
    item_id_entry = ttk.Entry(adjust_frame, width=10, font=form_font)
    item_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)

    ttk.Button(adjust_frame, text="+ Increase Stock", bootstyle=SUCCESS,
               command=lambda: update_stock(item_id_entry.get(), 1)).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
    ttk.Button(adjust_frame, text="- Decrease Stock", bootstyle=PRIMARY,
               command=lambda: update_stock(item_id_entry.get(), -1)).grid(row=2, column=0, columnspan=2, padx=5, pady=5)
    ttk.Button(adjust_frame, text="Delete Product", bootstyle=DANGER,
               command=lambda: delete_product(item_id_entry.get())).grid(row=3, column=0, columnspan=2, padx=5, pady=15)

    refresh_table()

if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    root.title("Inventory Management Test")
    manage_inventory(root)
    root.mainloop()








