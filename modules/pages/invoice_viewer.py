import tkinter as tk
from tkinter import Toplevel, messagebox, StringVar, END, W, E, CENTER, X, Y, LEFT, RIGHT, BOTH
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import webbrowser

from modules.db_manager import get_connection, return_connection, ConnectionContext
# Import i18n support
from modules.i18n import _, tr, get_current_language, set_widget_direction

# Message constants for internationalization
MSG_INVOICES = "Invoices"
MSG_SEARCH = "Search"
MSG_INVOICE_ID = "Invoice ID"
MSG_DATE = "Date"
MSG_WARNING = "Warning"
MSG_NO_INVOICE_SELECTED = "No invoice selected!"
MSG_TOTAL = "Total"
MSG_DISCOUNT = "Discount"
MSG_DATE_TIME = "Date & Time"
MSG_SELLER = "Seller"
MSG_PRODUCT = "Product"
MSG_PRICE = "Price"
MSG_QTY = "Qty"
MSG_THANKS = "Thank you for shopping with us!"
MSG_SERVED_BY = "You were served by"
MSG_SHOW_INVOICE_ITEMS = "Show Selected Invoice Items"
MSG_PRINT_INVOICE = "Print Invoice"
MSG_SELECT_INVOICE = "Select an invoice first."
MSG_INVOICE = "Invoice"
MSG_PAYMENT_METHOD = "Payment Method"
MSG_INVOICES_FOR = "Invoices for"
MSG_ERROR = "Error"
MSG_ERROR_FETCHING = "Error fetching invoices"

def show_all_invoices(master=None):
    inv_win = Toplevel(master)
    inv_win.title(tr(MSG_INVOICES))
    inv_win.geometry("1000x600")
    
    # Set widget direction based on language
    set_widget_direction(inv_win)
    
    search_bar = ttk.Frame(inv_win, padding=10)
    search_bar.pack(fill=X)
    
    ttk.Label(search_bar, text=f"{tr(MSG_INVOICE_ID)}:").pack(side=LEFT, padx=5)
    inv_id_e = ttk.Entry(search_bar, width=10)
    inv_id_e.pack(side=LEFT, padx=5)
    
    ttk.Label(search_bar, text=f"{tr(MSG_DATE)}:").pack(side=LEFT, padx=5)
    date_e = ttk.Entry(search_bar, width=20)
    date_e.pack(side=LEFT, padx=5)

    columns = ("id", "payment", "total", "discount", "balance", "date")
    invoice_table = ttk.Treeview(
        inv_win, columns=columns, show="headings", style="Dark.Treeview"
    )
    invoice_table.column("#0", width=0, stretch=False)
    for col, w, anchor, hdr in [
        ("id", 80, CENTER, tr(MSG_INVOICE_ID)),
        ("payment", 150, CENTER, tr(MSG_PAYMENT_METHOD)),
        ("total", 100, E, tr(MSG_TOTAL)),
        ("discount", 100, E, tr(MSG_DISCOUNT)),
        ("balance", 100, E, tr("Balance")),
        ("date", 350, W, tr(MSG_DATE))
    ]:
        invoice_table.heading(col, text=hdr, anchor=anchor)
        invoice_table.column(col, width=w, anchor=anchor,
                        stretch=(col == "date"))
    invoice_table.pack(fill=BOTH, expand=True, padx=10, pady=10)

    item_table = ttk.Treeview(
        inv_win, columns=("Product", "Price", "Qty", "Total"),
        show="headings", style="Dark.Treeview"
    )
    item_table.column("#0", width=0, stretch=False)
    for col, w, anchor, hdr in [
        ("Product", 240, W, tr(MSG_PRODUCT)),
        ("Price", 100, E, tr(MSG_PRICE)),
        ("Qty", 80, CENTER, tr(MSG_QTY)),
        ("Total", 100, E, tr(MSG_TOTAL))
    ]:
        item_table.heading(col, text=hdr, anchor=anchor)
        item_table.column(col, width=w, anchor=anchor, stretch=(col == "Product"))
    item_table.pack(fill=X, pady=10)

    inv_details_lbl = ttk.Label(inv_win, text="", font=("Helvetica", 18))
    inv_details_lbl.pack(pady=5)

    current_invoice_data = {}

    def do_search():
        invoice_table.delete(*invoice_table.get_children())
        q = """SELECT InvoiceID, PaymentMethod, TotalAmount, Discount, DateTime
               FROM Invoices WHERE 1=1"""
        ps = []
        if inv_id_e.get().strip():
            q += " AND InvoiceID = ?"; ps.append(inv_id_e.get().strip())
        if date_e.get().strip():
            q += " AND DateTime LIKE ?"; ps.append(date_e.get().strip() + "%")
        q += " ORDER BY InvoiceID DESC"

        conn = get_connection(); cur = conn.cursor()
        cur.execute(q, ps)
        for r in cur.fetchall():
            invoice_table.insert("", END, values=(r[0], r[1], r[2], r[3], "", r[4]))
        return_connection(conn)

    ttk.Button(search_bar, text=tr(MSG_SEARCH), bootstyle=PRIMARY, command=do_search).pack(side=LEFT, padx=10)

    def show_items():
        sel = invoice_table.selection()
        if not sel:
            messagebox.showwarning(tr(MSG_WARNING), tr(MSG_NO_INVOICE_SELECTED), parent=inv_win)
            return
        inv_id, pay, tot, disc, _, dt = invoice_table.item(sel[0], "values")
        
        # Get seller information
        user_name = tr("Unknown")
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT u.Username 
                FROM Invoices i
                JOIN Users u ON i.ShiftUserID = u.UserID
                WHERE i.InvoiceID = ?
            """, (inv_id,))
            user_row = cur.fetchone()
            if user_row:
                user_name = user_row[0]
        except Exception:
            pass  # Silently ignore errors in getting username
        
        inv_details_lbl.config(
            text=f"{tr(MSG_TOTAL)}: ${tot} | {tr(MSG_DISCOUNT)}: ${disc} | {tr(MSG_DATE_TIME)}: {dt} | {tr(MSG_SELLER)}: {user_name}"
        )
        
        item_table.delete(*item_table.get_children())
        conn = get_connection(); cur = conn.cursor()
        cur.execute(
            "SELECT ProductName, Price, Quantity FROM InvoiceItems WHERE InvoiceID = ?",
            (inv_id,)
        )
        rows = cur.fetchall()
        return_connection(conn)
        items = []
        for pn, pr, qt in rows:
            lt = float(pr) * int(qt)
            item_table.insert("", END, values=(pn, f"{pr:.2f}", f"x{qt}", f"{lt:.2f}"))
            items.append((pn, f"{pr:.2f}", f"x{qt}", f"{lt:.2f}"))
        current_invoice_data.clear()
        current_invoice_data.update({
            "header": {
                "InvoiceID":   inv_id,
                "DateTime":    dt,
                "PaymentMethod": pay,
                "TotalAmount": tot,
                "Discount":    disc,
                "Seller":      user_name
            },
            "items": items
        })
        
        # Add thank you message
        thank_you_label.config(text=tr(MSG_THANKS))
        seller_label.config(text=f"{tr(MSG_SERVED_BY)}: {user_name}")

    # Thank you message and seller information (initially empty)
    thank_you_frame = ttk.Frame(inv_win, padding=5)
    thank_you_frame.pack(fill=X, pady=5)
    thank_you_label = ttk.Label(thank_you_frame, text="", font=("Helvetica", 16, "bold"), foreground="#28a745")
    thank_you_label.pack(pady=(5, 2))
    seller_label = ttk.Label(thank_you_frame, text="", font=("Helvetica", 14))
    seller_label.pack(pady=(0, 5))

    ttk.Button(inv_win, text=tr(MSG_SHOW_INVOICE_ITEMS), bootstyle=INFO, command=show_items).pack(pady=10)

    def print_invoice():
        if "header" not in current_invoice_data:
            messagebox.showwarning(tr(MSG_WARNING), tr(MSG_SELECT_INVOICE), parent=inv_win)
            return
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        # Check current language for RTL support
        is_rtl = get_current_language() == 'ar'

        inv = current_invoice_data["header"]
        items = current_invoice_data["items"]
        fname = f"invoice_{inv['InvoiceID']}.pdf"
        c = canvas.Canvas(fname, pagesize=letter)
        w, h = letter
        y = h - 50
        
        # Add support for RTL text for Arabic language
        if is_rtl:
            # Try to import Arabic support
            try:
                # Import ReportLab Arabic Support
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                
                # Check if we have a font with Arabic support
                # Arial Unicode MS font has good Arabic support
                # If font is not available, we'll use standard approach
                arabic_font_path = "C:\\Windows\\Fonts\\arial.ttf"  # Path to Windows Arial (Has some Arabic support)
                pdfmetrics.registerFont(TTFont('Arabic', arabic_font_path))
                has_arabic_font = True
            except:
                has_arabic_font = False
        else:
            has_arabic_font = False
        
        # Set starting positions based on language direction
        if is_rtl and has_arabic_font:
            c.setFont("Arabic", 16)
            title_x = w - 50  # Right side for RTL
            c.drawRightString(title_x, y, tr(MSG_INVOICE))
        else:
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y, tr(MSG_INVOICE))
        
        y -= 30
        
        # Draw invoice details based on language
        if is_rtl and has_arabic_font:
            c.setFont("Arabic", 12)
            col1_x = w - 50  # Right alignment for RTL
            col2_x = w - 250  # Start of values
            
            # Define the keys with their translated names
            fields = [
                (tr(MSG_INVOICE_ID), inv["InvoiceID"]),
                (tr(MSG_DATE_TIME), inv["DateTime"]),
                (tr(MSG_PAYMENT_METHOD), inv["PaymentMethod"]),
                (tr(MSG_TOTAL), inv["TotalAmount"]),
                (tr(MSG_DISCOUNT), inv["Discount"])
            ]
            
            for label, value in fields:
                # Draw label (right-aligned for RTL)
                c.drawRightString(col1_x, y, f"{label}: {value}")
                y -= 20
            
            # Add seller information
            if "Seller" in inv:
                c.drawRightString(col1_x, y, f"{tr(MSG_SELLER)}: {inv['Seller']}")
                y -= 20
        else:
            c.setFont("Helvetica", 12)
            # Use translated field names
            fields = [
                (tr(MSG_INVOICE_ID), inv["InvoiceID"]),
                (tr(MSG_DATE_TIME), inv["DateTime"]),
                (tr(MSG_PAYMENT_METHOD), inv["PaymentMethod"]),
                (tr(MSG_TOTAL), inv["TotalAmount"]),
                (tr(MSG_DISCOUNT), inv["Discount"])
            ]
            
            for label, value in fields:
                c.drawString(50, y, f"{label}: {value}")
                y -= 20
            
            # Add seller information
            if "Seller" in inv:
                c.drawString(50, y, f"{tr(MSG_SELLER)}: {inv['Seller']}")
                y -= 20
        
        y -= 20
        c.line(50, y, w - 50, y)
        y -= 30

        # Table headers
        if is_rtl and has_arabic_font:
            c.setFont("Arabic", 12)
            # Draw headers right-to-left
            headers_x = [
                (w - 50, tr(MSG_PRODUCT)),
                (w - 200, tr(MSG_PRICE)),
                (w - 300, tr(MSG_QTY)),
                (w - 400, tr(MSG_TOTAL))
            ]
            for x, text in headers_x:
                c.drawRightString(x, y, text)
        else:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, tr(MSG_PRODUCT))
            c.drawString(250, y, tr(MSG_PRICE))
            c.drawString(350, y, tr(MSG_QTY))
            c.drawString(450, y, tr(MSG_TOTAL))
        
        y -= 20
        
        # Draw items
        if is_rtl and has_arabic_font:
            c.setFont("Arabic", 12)
            for pn, pr, qt, lt in items:
                if y < 100:
                    c.showPage(); y = h - 50
                    # Redraw headers on new page
                    y_headers = h - 50
                    for x, text in headers_x:
                        c.drawRightString(x, y_headers, text)
                    y = h - 80
                
                # Draw right-aligned items
                c.drawRightString(w - 50, y, pn)
                c.drawRightString(w - 200, y, pr)
                c.drawRightString(w - 300, y, qt)
                c.drawRightString(w - 400, y, lt)
                y -= 20
        else:
            c.setFont("Helvetica", 12)
            for pn, pr, qt, lt in items:
                if y < 100:
                    c.showPage(); y = h - 50
                    # Redraw headers on new page
                    c.setFont("Helvetica-Bold", 12)
                    y_headers = h - 50
                    c.drawString(50, y_headers, tr(MSG_PRODUCT))
                    c.drawString(250, y_headers, tr(MSG_PRICE))
                    c.drawString(350, y_headers, tr(MSG_QTY))
                    c.drawString(450, y_headers, tr(MSG_TOTAL))
                    c.setFont("Helvetica", 12)
                    y = h - 80
                
                c.drawString(50, y, pn)
                c.drawString(250, y, pr)
                c.drawString(350, y, qt)
                c.drawString(450, y, lt)
                y -= 20
        
        # Add thank you message at the bottom
        y -= 30
        if is_rtl and has_arabic_font:
            c.setFont("Arabic", 14)
            c.drawCentredString(w/2, y, tr(MSG_THANKS))
            y -= 20
            c.setFont("Arabic", 12)
            if "Seller" in inv:
                c.drawCentredString(w/2, y, f"{tr(MSG_SERVED_BY)}: {inv['Seller']}")
        else:
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(w/2, y, tr(MSG_THANKS))
            y -= 20
            c.setFont("Helvetica", 12)
            if "Seller" in inv:
                c.drawCentredString(w/2, y, f"{tr(MSG_SERVED_BY)}: {inv['Seller']}")
        
        # Save the PDF to file - critical step, don't remove!
        c.save()
        webbrowser.open_new(fname)

    ttk.Button(inv_win, text=tr(MSG_PRINT_INVOICE), bootstyle=INFO, command=print_invoice).pack(pady=10)

    def load_invoices():
        do_search()

    load_invoices()


def show_invoices_for_user(master, username):
    """
    Opens a window displaying invoices for a given user (ShiftEmployee).
    """
    inv_win = Toplevel(master)
    inv_win.title(f"{tr(MSG_INVOICES_FOR)} {username}")
    inv_win.geometry("1000x600")
    
    # Set widget direction based on language
    set_widget_direction(inv_win)

    table = ttk.Treeview(inv_win, columns=("Invoice","Payment","Total","Discount","DateTime"), show="headings", style="Dark.Treeview")
    for col, w, anchor, hdr in [
        ("Invoice", 150, CENTER, tr(MSG_INVOICE_ID)),
        ("Payment", 150, CENTER, tr(MSG_PAYMENT_METHOD)),
        ("Total", 150, E, tr(MSG_TOTAL)),
        ("Discount", 150, E, tr(MSG_DISCOUNT)),
        ("DateTime", 400, W, tr(MSG_DATE_TIME))
    ]:
        table.heading(col, text=hdr, anchor=anchor)
        table.column(col, width=w, anchor=anchor)
    table.pack(fill=BOTH, expand=True, padx=10, pady=10)

    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("""
            SELECT InvoiceID,PaymentMethod,TotalAmount,Discount,DateTime
            FROM Invoices
            WHERE ShiftEmployee = ?
            ORDER BY InvoiceID DESC
        """, (username,))
        for row in cur.fetchall():
            table.insert("", END, values=row)
        return_connection(conn)
    except Exception as e:
        messagebox.showerror(tr(MSG_ERROR), f"{tr(MSG_ERROR_FETCHING)}: {e}")

