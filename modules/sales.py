import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import END, messagebox, Toplevel, StringVar, BOTH, X, Y, W, E, CENTER, RIGHT
import cv2
from pyzbar.pyzbar import decode
import threading
from modules.db_manager import get_connection, return_connection
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import webbrowser
import os

def sales_screen(master):
    sales_win = Toplevel(master)
    sales_win.title("Sales Screen")
    sales_win.state("zoomed")  # Fullscreen

    stop_scanning = False

    container = ttk.Frame(sales_win)
    container.pack(fill=BOTH, expand=True)

    canvas = ttk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    canvas.configure(yscrollcommand=scrollbar.set)

    content_frame = ttk.Frame(canvas)
    content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=content_frame, anchor="nw")

    # ---------------------------------------------------------
    # DB Helper for scanning
    def fetch_product_by_code(code):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ProductID, Name, Price, Stock, Category, Barcode, QR_Code
            FROM Products 
            WHERE Barcode = ? OR QR_Code = ?
        """, (code, code))
        product = cursor.fetchone()
        return_connection(conn)
        return product

    # ---------------------------------------------------------
    # Cart Functions
    def add_to_cart_product(product_id, name, price):
        total_price = price * 1
        cart_table.insert("", END, values=(product_id, name, f"{price:.2f}", 1, f"{total_price:.2f}"))
        calculate_total()

    def add_to_cart():
        code = qr_entry.get().strip()
        if not code:
            messagebox.showwarning("Warning", "Please enter a Barcode or QR Code!")
            return
        product = fetch_product_by_code(code)
        if not product:
            messagebox.showwarning("Warning", "Product not found!")
            return
        product_id, name, price, stock, category, barcode, qrcode = product
        add_to_cart_product(product_id, name, price)

    def calculate_total():
        subtotal = 0.0
        for row in cart_table.get_children():
            total_val = float(cart_table.item(row, "values")[4])
            subtotal += total_val
        try:
            discount_val = float(discount_entry.get().strip())
        except ValueError:
            discount_val = 0.0
        final_total = max(subtotal - discount_val, 0.0)
        subtotal_label.config(text=f"Subtotal: ${subtotal:.2f}")
        discount_label.config(text=f"Discount: ${discount_val:.2f}")
        total_label.config(text=f"Total: ${final_total:.2f}")

    def complete_sale():
        if not cart_table.get_children():
            messagebox.showwarning("Warning", "No items in the cart!")
            return

        subtotal = 0.0
        cart_items = []
        for row in cart_table.get_children():
            vals = cart_table.item(row, "values")
            product_id, nm, price_str, qty_str, item_total_str = vals
            product_id = int(product_id)
            price = float(price_str)
            quantity = int(qty_str)
            item_total = float(item_total_str)
            subtotal += item_total
            cart_items.append((product_id, nm, price, quantity))
        try:
            discount_val = float(discount_entry.get().strip())
        except ValueError:
            discount_val = 0.0

        payment_method = payment_var.get()
        final_total = max(subtotal - discount_val, 0.0)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Invoices (DateTime, PaymentMethod, TotalAmount, Discount)
            VALUES (datetime('now'), ?, ?, ?)
        """, (payment_method, final_total, discount_val))
        invoice_id = cursor.lastrowid

        for (p_id, nm, pr, qt) in cart_items:
            cursor.execute("""
                INSERT INTO InvoiceItems (InvoiceID, ProductName, Price, Quantity)
                VALUES (?, ?, ?, ?)
            """, (invoice_id, nm, pr, qt))
            cursor.execute("""
                UPDATE Products 
                SET Stock = Stock - ? 
                WHERE ProductID = ?
            """, (qt, p_id))
        conn.commit()
        return_connection(conn)
        messagebox.showinfo("Success", "Sale completed and invoice saved!")
        reset_cart()

    def reset_cart():
        cart_table.delete(*cart_table.get_children())
        discount_entry.delete(0, END)
        discount_entry.insert(0, "0")
        payment_var.set("Cash")
        calculate_total()

    # ---------------------------------------------------------
    # Mark as Debit
    def mark_as_debit():
        if not cart_table.get_children():
            messagebox.showwarning("Warning", "No items in the cart!")
            return

        subtotal = 0.0
        cart_items = []
        for row in cart_table.get_children():
            vals = cart_table.item(row, "values")
            product_id, nm, price_str, qty_str, tot_str = vals
            product_id = int(product_id)
            price = float(price_str)
            quantity = int(qty_str)
            subtotal += float(tot_str)
            cart_items.append((product_id, nm, price, quantity))
        try:
            discount_val = float(discount_entry.get().strip())
        except ValueError:
            discount_val = 0.0
        payment_method = payment_var.get()
        final_total = max(subtotal - discount_val, 0.0)

        debit_win = Toplevel(sales_win)
        debit_win.title("Debtor Information")
        debit_win.geometry("400x250")
        frm = ttk.Frame(debit_win, padding=20)
        frm.pack(fill=BOTH, expand=True)

        ttk.Label(frm, text="Enter Debtor Name:", font=("Helvetica", 14)).grid(row=0, column=0, padx=5, pady=10, sticky=E)
        name_entry = ttk.Entry(frm, width=30, font=("Helvetica", 14))
        name_entry.grid(row=0, column=1, padx=5, pady=10, sticky=W)
        ttk.Label(frm, text="Enter Debtor Phone:", font=("Helvetica", 14)).grid(row=1, column=0, padx=5, pady=10, sticky=E)
        phone_entry = ttk.Entry(frm, width=30, font=("Helvetica", 14))
        phone_entry.grid(row=1, column=1, padx=5, pady=10, sticky=W)

        def confirm_debit():
            debtor_name = name_entry.get().strip()
            debtor_phone = phone_entry.get().strip()
            if not debtor_name:
                messagebox.showwarning("Warning", "Debtor name is required.")
                return
            if not debtor_phone:
                messagebox.showwarning("Warning", "Debtor phone is required.")
                return
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Invoices (DateTime, PaymentMethod, TotalAmount, Discount)
                VALUES (datetime('now'), ?, ?, ?)
            """, (payment_method, final_total, discount_val))
            invoice_id = cursor.lastrowid
            for (p_id, nm, pr, qt) in cart_items:
                cursor.execute("""
                    INSERT INTO InvoiceItems (InvoiceID, ProductName, Price, Quantity)
                    VALUES (?, ?, ?, ?)
                """, (invoice_id, nm, pr, qt))
                cursor.execute("""
                    UPDATE Products 
                    SET Stock = Stock - ?
                    WHERE ProductID = ?
                """, (qt, p_id))
            cursor.execute("""
                INSERT INTO Debits (Name, Phone, InvoiceID, Amount, Status, Date)
                VALUES (?, ?, ?, ?, 'Pending', datetime('now'))
            """, (debtor_name, debtor_phone, invoice_id, final_total))
            conn.commit()
            return_connection(conn)
            messagebox.showinfo("Success", "Sale marked as debit and invoice saved!")
            reset_cart()
            debit_win.destroy()
        ttk.Button(frm, text="Confirm Debit", bootstyle=SUCCESS, command=confirm_debit).grid(row=2, column=0, columnspan=2, pady=20)

    # ---------------------------------------------------------
    # Scanning (using webcam)
    def scan_code():
        nonlocal stop_scanning
        stop_scanning = False
        scan_win = Toplevel(sales_win)
        scan_win.title("Scanning...")
        ttk.Label(scan_win, text="Press 'Stop Scanning' or 'q' in the camera window to quit.", font=("Helvetica", 14)).pack(pady=20)
        stop_button = ttk.Button(scan_win, text="Stop Scanning", bootstyle=DANGER, command=lambda: stop_cam(scan_win))
        stop_button.pack(pady=10)

        def camera_loop():
            cap = cv2.VideoCapture(0)
            while True:
                if stop_scanning:
                    break
                ret, frame = cap.read()
                if not ret:
                    break
                codes = decode(frame)
                for code in codes:
                    scanned_code = code.data.decode('utf-8')
                    qr_entry.delete(0, END)
                    qr_entry.insert(0, scanned_code)
                    add_to_cart()
                    stop_cam(scan_win)
                    break
                cv2.imshow("Scanning...", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()

        def stop_cam(win):
            nonlocal stop_scanning
            stop_scanning = True
            win.destroy()
        t = threading.Thread(target=camera_loop)
        t.start()
        scan_win.protocol("WM_DELETE_WINDOW", lambda: stop_cam(scan_win))

    # ---------------------------------------------------------
    # Cart Operations
    def increment_quantity():
        selected = cart_table.selection()
        if not selected:
            messagebox.showwarning("Warning", "No item selected!")
            return
        item_id = selected[0]
        vals = cart_table.item(item_id, "values")
        quantity = int(vals[3])
        price = float(vals[2])
        quantity += 1
        new_total = quantity * price
        cart_table.item(item_id, values=(vals[0], vals[1], f"{price:.2f}", quantity, f"{new_total:.2f}"))
        calculate_total()

    def decrement_quantity():
        selected = cart_table.selection()
        if not selected:
            messagebox.showwarning("Warning", "No item selected!")
            return
        item_id = selected[0]
        vals = cart_table.item(item_id, "values")
        quantity = int(vals[3])
        price = float(vals[2])
        quantity -= 1
        if quantity <= 0:
            cart_table.delete(item_id)
        else:
            new_total = quantity * price
            cart_table.item(item_id, values=(vals[0], vals[1], f"{price:.2f}", quantity, f"{new_total:.2f}"))
        calculate_total()

    def remove_item():
        selected = cart_table.selection()
        if not selected:
            messagebox.showwarning("Warning", "No item selected!")
            return
        cart_table.delete(selected[0])
        calculate_total()

    # ---------------------------------------------------------
    # Searching for Products
    def fetch_categories():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Category FROM Products")
        cats = [row[0] for row in cursor.fetchall()]
        return_connection(conn)
        return cats

    def search_products():
        category = category_var.get()
        search_term = search_entry.get().strip()
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT ProductID, Name, Price FROM Products WHERE 1=1"
        params = []
        if category and category != "All":
            query += " AND Category = ?"
            params.append(category)
        if search_term:
            query += " AND Name LIKE ?"
            params.append(f"%{search_term}%")
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return_connection(conn)
        product_list_table.delete(*product_list_table.get_children())
        for r in rows:
            product_list_table.insert("", END, values=(r[0], r[1], f"{r[2]:.2f}"))
    
    def add_selected_product():
        selected = product_list_table.selection()
        if not selected:
            messagebox.showwarning("Warning", "No product selected!")
            return
        item_id = selected[0]
        vals = product_list_table.item(item_id, "values")
        product_id, nm, price = vals
        add_to_cart_product(product_id, nm, float(price))

    # ---------------------------------------------------------
    # View Invoices (with Print and Search)
    def view_invoices():
        inv_win = Toplevel(sales_win)
        inv_win.title("Invoices")
        inv_win.geometry("1000x600")
        current_invoice_data = {}

        search_frame_inv = ttk.Frame(inv_win, padding=10)
        search_frame_inv.pack(fill=X, pady=5)
        ttk.Label(search_frame_inv, text="Invoice ID:", font=("Helvetica", 12)).pack(side=LEFT, padx=5)
        invoice_id_entry = ttk.Entry(search_frame_inv, width=15, font=("Helvetica", 12))
        invoice_id_entry.pack(side=LEFT, padx=5)
        ttk.Label(search_frame_inv, text="Date (YYYY-MM-DD):", font=("Helvetica", 12)).pack(side=LEFT, padx=5)
        date_entry = ttk.Entry(search_frame_inv, width=15, font=("Helvetica", 12))
        date_entry.pack(side=LEFT, padx=5)
        def search_invoices():
            invoice_id_val = invoice_id_entry.get().strip()
            date_val = date_entry.get().strip()
            query = "SELECT InvoiceID, PaymentMethod, TotalAmount, Discount, DateTime FROM Invoices WHERE 1=1"
            params = []
            if invoice_id_val:
                query += " AND InvoiceID = ?"
                params.append(invoice_id_val)
            if date_val:
                query += " AND DateTime LIKE ?"
                params.append(date_val + "%")
            query += " ORDER BY InvoiceID DESC"
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return_connection(conn)
            invoice_table.delete(*invoice_table.get_children())
            for row in rows:
                invoice_table.insert("", END, values=(row[0], row[1], row[2], row[3], "", row[4]))
        ttk.Button(search_frame_inv, text="Search", bootstyle=PRIMARY, command=search_invoices).pack(side=LEFT, padx=10)

        inv_frame = ttk.Frame(inv_win, padding=20)
        inv_frame.pack(fill=BOTH, expand=True)

        invoice_table = ttk.Treeview(inv_frame, columns=("Invoice", "Payment", "Total", "Discount", "Spacer", "DateTime"),
                                      show="headings", style="Treeview")
        invoice_table.column("#0", width=0, stretch=False)
        invoice_table.heading("Invoice",  text="Invoice", anchor=CENTER)
        invoice_table.heading("Payment",  text="Payment", anchor=CENTER)
        invoice_table.heading("Total",    text="Total", anchor=E)
        invoice_table.heading("Discount", text="Discount", anchor=E)
        invoice_table.heading("Spacer",   text="", anchor=CENTER)
        invoice_table.heading("DateTime", text="DateTime", anchor=W)
        invoice_table.column("Invoice",  width=150, anchor=CENTER, stretch=False)
        invoice_table.column("Payment",  width=150, anchor=CENTER, stretch=False)
        invoice_table.column("Total",    width=150, anchor=E, stretch=False)
        invoice_table.column("Discount", width=150, anchor=E, stretch=False)
        invoice_table.column("Spacer",   width=50, anchor=CENTER, stretch=False)
        invoice_table.column("DateTime", width=400, anchor=W, stretch=True)
        invoice_table.pack(fill=X, pady=10)
        btn_frame = ttk.Frame(inv_frame)
        btn_frame.pack(pady=10)
        def show_invoice_items():
            nonlocal current_invoice_data
            selected = invoice_table.selection()
            if not selected:
                messagebox.showwarning("Warning", "No invoice selected!")
                return
            item_id = selected[0]
            inv_values = invoice_table.item(item_id, "values")
            inv_id = inv_values[0]
            inv_total = inv_values[2]
            inv_discount = inv_values[3]
            inv_datetime = inv_values[5]
            invoice_details_label.config(
                text=f"Total Amount: ${inv_total} | Discount: ${inv_discount} | Date & Time: {inv_datetime}"
            )
            item_table.delete(*item_table.get_children())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ProductName, Price, Quantity FROM InvoiceItems WHERE InvoiceID = ?", (inv_id,))
            rows = cursor.fetchall()
            return_connection(conn)
            items = []
            for row in rows:
                product_name = row[0]
                price = float(row[1])
                quantity = int(row[2])
                total_price = price * quantity
                qty_display = f"x{quantity}"
                item_table.insert("", END, values=(product_name, f"{price:.2f}", qty_display, f"{total_price:.2f}"))
                items.append((product_name, f"{price:.2f}", qty_display, f"{total_price:.2f}"))
            current_invoice_data = {
                "header": {
                    "InvoiceID": inv_id,
                    "DateTime": inv_datetime,
                    "PaymentMethod": inv_values[1],
                    "TotalAmount": inv_total,
                    "Discount": inv_discount
                },
                "items": items
            }
        ttk.Button(btn_frame, text="Show Selected Invoice Items", bootstyle=PRIMARY,
                   command=show_invoice_items).grid(row=0, column=0, padx=10)
        def print_invoice():
            nonlocal current_invoice_data
            if not current_invoice_data or "header" not in current_invoice_data:
                messagebox.showwarning("Warning", "Please select an invoice and view its products first.")
                return
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                invoice = current_invoice_data["header"]
                items = current_invoice_data["items"]
                file_name = f"invoice_{invoice['InvoiceID']}.pdf"
                c = canvas.Canvas(file_name, pagesize=letter)
                width, height = letter
                y = height - 50
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, y, "Restaurant Invoice")
                y -= 30
                c.setFont("Helvetica", 12)
                c.drawString(50, y, f"Invoice ID: {invoice['InvoiceID']}")
                y -= 20
                c.drawString(50, y, f"Date & Time: {invoice['DateTime']}")
                y -= 20
                c.drawString(50, y, f"Payment Method: {invoice['PaymentMethod']}")
                y -= 20
                c.drawString(50, y, f"Total Amount: ${invoice['TotalAmount']}")
                y -= 20
                c.drawString(50, y, f"Discount: ${invoice['Discount']}")
                y -= 40
                c.line(50, y, width - 50, y)
                y -= 30
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Product")
                c.drawString(250, y, "Price")
                c.drawString(350, y, "Qty")
                c.drawString(450, y, "Total")
                y -= 20
                c.setFont("Helvetica", 12)
                for item in items:
                    product_name, price_str, qty_display, line_total_str = item
                    if y < 100:
                        c.showPage()
                        y = height - 50
                    c.drawString(50, y, product_name)
                    c.drawString(250, y, price_str)
                    c.drawString(350, y, qty_display)
                    c.drawString(450, y, line_total_str)
                    y -= 20
                y -= 40
                c.setFont("Helvetica-Bold", 12)
                c.drawCentredString(width/2, y, "Thank you for your purchase!")
                c.save()
                try:
                    webbrowser.open_new(file_name)
                except Exception as e:
                    messagebox.showinfo("Print Invoice", f"Invoice saved as {file_name}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while printing: {str(e)}")
        ttk.Button(btn_frame, text="Print Invoice", bootstyle=INFO, command=print_invoice).grid(row=0, column=1, padx=10)

        invoice_details_label = ttk.Label(inv_frame, text="", font=("Helvetica", 14))
        invoice_details_label.pack(pady=5)

        item_table = ttk.Treeview(inv_frame, columns=("Product", "Price", "Qty", "Total"), show="headings", style="Treeview")
        item_table.column("#0", width=0, stretch=False)
        item_table.heading("Product", text="Product", anchor=W)
        item_table.heading("Price",   text="Price", anchor=E)
        item_table.heading("Qty",     text="Qty", anchor=CENTER)
        item_table.heading("Total",   text="Total", anchor=E)
        item_table.column("Product", width=240, anchor=W, stretch=True)
        item_table.column("Price",   width=100, anchor=E, stretch=False)
        item_table.column("Qty",     width=80, anchor=CENTER, stretch=False)
        item_table.column("Total",   width=100, anchor=E, stretch=False)
        item_table.pack(fill=X, pady=10)
        def load_invoices():
            invoice_table.delete(*invoice_table.get_children())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT InvoiceID, PaymentMethod, TotalAmount, Discount, DateTime
                FROM Invoices
                ORDER BY InvoiceID DESC
            """)
            rows = cursor.fetchall()
            return_connection(conn)
            for row in rows:
                invoice_table.insert("", END, values=(row[0], row[1], row[2], row[3], "", row[4]))
        load_invoices()

    # ---------------------------------------------------------
    # Title and Main Layout for Sales Screen
    ttk.Label(content_frame, text="Sales Screen", font=("Helvetica", 28, "bold")).pack(pady=20)
    top_frame = ttk.Frame(content_frame)
    top_frame.pack(fill=X, padx=20, pady=20)
    left_col = ttk.Frame(top_frame)
    left_col.pack(side=LEFT, fill=BOTH, expand=True)
    right_col = ttk.Frame(top_frame)
    right_col.pack(side=RIGHT, fill=Y, padx=20)

    qr_frame = ttk.Frame(left_col, padding=10)
    qr_frame.pack(pady=10, fill=X)
    ttk.Label(qr_frame, text="Enter Barcode/QR Code:", font=("Helvetica", 16)).grid(row=0, column=0, padx=5, pady=5)
    qr_entry = ttk.Entry(qr_frame, width=30, font=("Helvetica", 16))
    qr_entry.grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(qr_frame, text="Add to Cart", bootstyle=SUCCESS, command=add_to_cart).grid(row=0, column=2, padx=10, pady=5)
    ttk.Button(qr_frame, text="Scan Code (Camera)", bootstyle=INFO, command=scan_code).grid(row=0, column=3, padx=10, pady=5)

    search_frame = ttk.Labelframe(left_col, text="Search Products", padding=10)
    search_frame.pack(pady=20, fill=X)
    categories = fetch_categories()
    categories.insert(0, "All")
    ttk.Label(search_frame, text="Category:", font=("Helvetica", 16)).grid(row=0, column=0, padx=5, pady=5, sticky=E)
    category_var = StringVar(value="All")
    category_dropdown = ttk.Combobox(search_frame, textvariable=category_var, values=categories, state="readonly", font=("Helvetica", 16))
    category_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky=W)
    ttk.Label(search_frame, text="Search:", font=("Helvetica", 16)).grid(row=0, column=2, padx=5, pady=5, sticky=E)
    search_entry = ttk.Entry(search_frame, width=30, font=("Helvetica", 16))
    search_entry.grid(row=0, column=3, padx=5, pady=5, sticky=W)
    ttk.Button(search_frame, text="Search", bootstyle=PRIMARY, command=search_products).grid(row=0, column=4, padx=10, pady=5)
    product_list_frame = ttk.Frame(search_frame)
    product_list_frame.grid(row=1, column=0, columnspan=5, padx=5, pady=10, sticky="nsew")
    product_list_table = ttk.Treeview(product_list_frame, columns=("ID", "Name", "Price"), show="headings", style="Treeview")
    product_list_table.column("#0", width=0, stretch=False)
    product_list_table.heading("ID", text="ID", anchor=CENTER)
    product_list_table.heading("Name", text="Name", anchor=W)
    product_list_table.heading("Price", text="Price", anchor=E)
    product_list_table.column("ID", width=80, anchor=CENTER, stretch=False)
    product_list_table.column("Name", width=200, anchor=W, stretch=True)
    product_list_table.column("Price", width=100, anchor=E, stretch=False)
    product_list_table.pack(fill=BOTH, expand=True, padx=20, pady=5)
    ttk.Button(search_frame, text="Add Selected Product", bootstyle=SUCCESS, command=add_selected_product).grid(row=2, column=0, columnspan=5, pady=10)

    summary_frame = ttk.Frame(right_col, padding=20)
    summary_frame.pack(pady=10, fill=X)
    ttk.Label(summary_frame, text="Payment Method:", font=("Helvetica", 16)).grid(row=0, column=0, padx=5, pady=5, sticky=E)
    payment_var = StringVar(value="Cash")
    payment_dropdown = ttk.Combobox(summary_frame, textvariable=payment_var, values=["Cash", "Card"], state="readonly", font=("Helvetica", 16))
    payment_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky=W)
    ttk.Label(summary_frame, text="Discount:", font=("Helvetica", 16)).grid(row=1, column=0, padx=5, pady=5, sticky=E)
    discount_entry = ttk.Entry(summary_frame, width=10, font=("Helvetica", 16))
    discount_entry.grid(row=1, column=1, padx=5, pady=5, sticky=W)
    discount_entry.insert(0, "0")
    totals_frame = ttk.Frame(right_col, padding=20)
    totals_frame.pack(pady=10, fill=X)
    subtotal_label = ttk.Label(totals_frame, text="Subtotal: $0.00", font=("Helvetica", 18))
    subtotal_label.pack(anchor="w", pady=5)
    discount_label = ttk.Label(totals_frame, text="Discount: $0.00", font=("Helvetica", 18))
    discount_label.pack(anchor="w", pady=5)
    total_label = ttk.Label(totals_frame, text="Total: $0.00", font=("Helvetica", 22, "bold"))
    total_label.pack(anchor="w", pady=5)
    action_frame = ttk.Frame(right_col, padding=20)
    action_frame.pack(pady=10)
    ttk.Button(action_frame, text="Complete Sale", bootstyle=PRIMARY, command=complete_sale, width=20).grid(row=0, column=0, padx=10, pady=5)
    ttk.Button(action_frame, text="Reset Cart", bootstyle=WARNING, command=reset_cart, width=20).grid(row=1, column=0, padx=10, pady=5)
    ttk.Button(action_frame, text="View Invoices", bootstyle=INFO, command=view_invoices, width=20).grid(row=2, column=0, padx=10, pady=5)
    ttk.Button(action_frame, text="Mark As Debit", bootstyle=SECONDARY, command=mark_as_debit, width=20).grid(row=3, column=0, padx=10, pady=5)
    cart_frame = ttk.Frame(left_col)
    cart_frame.pack(pady=10, fill=BOTH, expand=True)
    cart_table = ttk.Treeview(cart_frame, columns=("ID", "Name", "Price", "Quantity", "Total"), show="headings", style="Treeview")
    cart_table.column("#0", width=0, stretch=False)
    cart_table.heading("ID", text="ID", anchor=CENTER)
    cart_table.heading("Name", text="Name", anchor=W)
    cart_table.heading("Price", text="Price", anchor=E)
    cart_table.heading("Quantity", text="Qty", anchor=CENTER)
    cart_table.heading("Total", text="Total", anchor=E)
    cart_table.column("ID", width=80, anchor=CENTER, stretch=False)
    cart_table.column("Name", width=250, anchor=W, stretch=True)
    cart_table.column("Price", width=100, anchor=E, stretch=False)
    cart_table.column("Quantity", width=100, anchor=CENTER, stretch=False)
    cart_table.column("Total", width=120, anchor=E, stretch=False)
    cart_table.pack(fill=BOTH, expand=True, padx=20, pady=10)
    cart_control_frame = ttk.Frame(left_col, padding=10)
    cart_control_frame.pack(pady=10)
    ttk.Button(cart_control_frame, text="+ Quantity", bootstyle=SUCCESS, command=increment_quantity).grid(row=0, column=0, padx=10)
    ttk.Button(cart_control_frame, text="- Quantity", bootstyle=PRIMARY, command=decrement_quantity).grid(row=0, column=1, padx=10)
    ttk.Button(cart_control_frame, text="Remove Item", bootstyle=DANGER, command=remove_item).grid(row=0, column=2, padx=10)
    
    discount_entry.bind("<KeyRelease>", lambda e: calculate_total())
    payment_dropdown.bind("<<ComboboxSelected>>", lambda e: calculate_total())

    calculate_total()

if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    root.title("Sales Screen Test")
    sales_screen(root)
    root.mainloop()

