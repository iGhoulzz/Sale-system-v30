# modules/pages/sales_page.py – touch‑optimised Sales screen (frame version)
# --------------------------------------------------------------------------
# * Full original UI retained.
# * Fixed: NOT‑NULL DateTime/ShiftEmployee & "database is locked".
# * Added thread safety for barcode scanning.
# * Using centralized data access layer for database operations.
# --------------------------------------------------------------------------

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import (
    Toplevel, StringVar, BOTH, X, Y, W, E, CENTER, RIGHT, LEFT, END, messagebox
)
import threading
import cv2
from pyzbar.pyzbar import decode
import webbrowser
import datetime
from modules.Login import current_user
from modules.logger import logger, log_activity
from modules.data_access import (
    get_product_by_barcode, complete_sale, get_products,
    get_product_stock, get_product_categories
)

# Standalone invoice viewer
from modules.pages.invoice_viewer import show_all_invoices

# Import internationalization support
from modules.i18n import _, register_refresh_callback, unregister_refresh_callback, set_widget_direction, tr

# Message-ID constants (English base text)
MSG_SALES_SCREEN = "Sales Management Screen"
MSG_BACK_HOME = "Back to Home"
MSG_BARCODE = "Enter Barcode/QR Code:"
MSG_ADD_CART = "Add to Cart"
MSG_SCAN_CODE = "Scan Code"
MSG_SEARCH_PRODUCTS = "Search Products"
MSG_CATEGORY = "Category:"
MSG_SEARCH = "Search"
MSG_ID = "ID"
MSG_NAME = "Name"
MSG_PRICE = "Price"
MSG_ADD_SELECTED = "Add Selected Product"
MSG_SHOPPING_CART = "Shopping Cart"
MSG_PAYMENT_METHOD = "Payment Method:"
MSG_CASH = "Cash"
MSG_CARD = "Card"
MSG_DISCOUNT = "Discount:"
MSG_COMPLETE_SALE = "Complete Sale"
MSG_MARK_DEBIT = "Mark As Debit"
MSG_RESET_CART = "Reset Cart"
MSG_VIEW_INVOICES = "View Invoices"
MSG_SUBTOTAL = "Subtotal"
MSG_TOTAL = "Total"


class SalesPage(ttk.Frame):
    """Touch‑optimised Sales screen with improved layout and cart scrollbar."""

    # ------------------------------------------------------------------
    #  Construction / layout helpers
    # ------------------------------------------------------------------
    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller

        # state ---------------------------------------------------------
        self.stop_scanning: bool = False
        self.qr_entry          = None
        self.cart_table        = None
        self.discount_entry    = None
        self.payment_var       = None
        self.subtotal_label    = None
        self.discount_label    = None
        self.total_label       = None      # optional (used by pop‑up debit window)
        self.footer_total_lbl  = None
        
        # Text variables for internationalization
        self.title_text = StringVar()
        self.back_btn_text = StringVar()
        self.barcode_label_text = StringVar()
        self.add_cart_btn_text = StringVar()
        self.scan_btn_text = StringVar()
        self.category_label_text = StringVar()
        self.search_label_text = StringVar()
        self.search_btn_text = StringVar()
        self.id_col_text = StringVar()
        self.name_col_text = StringVar()
        self.price_col_text = StringVar()
        self.add_selected_btn_text = StringVar()
        self.cart_frame_text = StringVar()
        self.payment_label_text = StringVar()
        self.cash_text = StringVar()
        self.card_text = StringVar()
        self.discount_text = StringVar()
        self.complete_sale_btn_text = StringVar()
        self.mark_debit_btn_text = StringVar()
        self.reset_cart_btn_text = StringVar()
        self.view_invoices_btn_text = StringVar()

        # --- Style tweaks ---------------------------------------------
        s = ttk.Style()
        s.configure("Touch.TButton", font=("Helvetica", 18, "bold"), padding=15)
        # Dark Treeview style
        s.configure(
            "Dark.Treeview",
            font=("Helvetica", 14),
            rowheight=28,
            background="#2D2D2D",
            fieldbackground="#2D2D2D",
            foreground="white",
        )
        s.configure(
            "Dark.Treeview.Heading",
            font=("Helvetica", 16, "bold"),
            background="#1F1F1F",
            foreground="white",
        )
        s.map(
            "Dark.Treeview",
            background=[("selected", "#3F51B5")],
            foreground=[("selected", "white")],
        )

        self._build_ui()
        self._retranslate()
        
        # Register for language changes
        register_refresh_callback(self._retranslate)
        
        # Optional: Bind to language changed event
        if self.winfo_toplevel():
            self.winfo_toplevel().bind('<<LanguageChanged>>', lambda e: self._retranslate())

    # ------------------------------------------------------------------
    #  Top bar
    # ------------------------------------------------------------------
    def _make_topbar(self, title: str):
        top = ttk.Frame(self, style="TFrame", padding=10)
        top.pack(fill="x")
        self.title_label = ttk.Label(
            top, textvariable=self.title_text, style="Header.TLabel", font=("Helvetica", 24, "bold")
        )
        self.title_label.pack(side=LEFT, padx=(10, 20))
        self.back_btn = ttk.Button(
            top,
            textvariable=self.back_btn_text,
            style="Small.TButton",
            bootstyle=SECONDARY,
            command=lambda: self.controller.show_frame("MainMenuPage"),
        )
        self.back_btn.pack(side=RIGHT, padx=20)

    # ------------------------------------------------------------------
    #  Main UI builder
    # ------------------------------------------------------------------
    def _build_ui(self):
        # 1) Title bar ---------------------------------------------------
        self._make_topbar(tr(MSG_SALES_SCREEN))
        
        # Set widget direction based on language
        set_widget_direction(self)
        
        # 2) Main Content Area
        self.pack_propagate(False)  # Prevent the frame from shrinking
        
        # Main content container
        content_container = ttk.Frame(self)
        content_container.pack(fill=BOTH, expand=True, padx=10, pady=(10, 80))  # Add bottom padding for footer

        # 3) PanedWindow for left/right columns -------------------------
        # Use a fixed ratio where the cart gets at least 45% of the space
        pane = ttk.PanedWindow(content_container, orient=HORIZONTAL)
        pane.pack(fill=BOTH, expand=True)

        left_col = ttk.Frame(pane)
        right_col = ttk.Frame(pane)
        pane.add(left_col, weight=55)  # 55% of space
        pane.add(right_col, weight=45) # 45% of space

        # -- LEFT COL ----------------------------------------------------
        # Barcode / QR entry -------------------------------------------
        qr_frame = ttk.Frame(left_col, padding=10)
        qr_frame.pack(fill=X, pady=10)
        self.barcode_label = ttk.Label(qr_frame, textvariable=self.barcode_label_text, font=("Helvetica", 18))
        self.barcode_label.grid(row=0, column=0, padx=5, pady=5, sticky=E)

        self.qr_entry = ttk.Entry(qr_frame, width=20, font=("Helvetica", 18))
        self.qr_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)

        self.add_cart_btn = ttk.Button(
            qr_frame, textvariable=self.add_cart_btn_text,
            bootstyle=SUCCESS, style="Touch.TButton", command=self._add_to_cart
        )
        self.add_cart_btn.grid(row=0, column=2, padx=10)

        self.scan_btn = ttk.Button(
            qr_frame, textvariable=self.scan_btn_text,
            bootstyle=INFO, style="Touch.TButton", command=self._scan_code
        )
        self.scan_btn.grid(row=0, column=3, padx=10)

        # Product search ------------------------------------------------
        self.search_frame = ttk.Labelframe(left_col, text=tr(MSG_SEARCH_PRODUCTS), padding=10)
        self.search_frame.pack(fill=BOTH, expand=True, pady=10)

        cats = self._fetch_categories()
        cats.insert(0, "All")

        self.category_label = ttk.Label(self.search_frame, textvariable=self.category_label_text, font=("Helvetica", 18))
        self.category_label.grid(row=0, column=0, sticky=E, padx=5, pady=5)
        
        category_var = ttk.StringVar(value="All")
        cat_combo = ttk.Combobox(
            self.search_frame, textvariable=category_var, values=cats, state="readonly",
            font=("Helvetica", 18), width=12
        )
        cat_combo.grid(row=0, column=1, sticky=W, padx=5, pady=5)

        self.search_label = ttk.Label(self.search_frame, textvariable=self.search_label_text, font=("Helvetica", 18))
        self.search_label.grid(row=0, column=2, sticky=E, padx=5, pady=5)
        
        search_entry = ttk.Entry(self.search_frame, width=18, font=("Helvetica", 18))
        search_entry.grid(row=0, column=3, sticky=W, padx=5, pady=5)

        self.search_btn = ttk.Button(
            self.search_frame, textvariable=self.search_btn_text,
            bootstyle=PRIMARY, style="Touch.TButton",
            command=lambda: self._search_products(category_var.get(), search_entry.get())
        )
        self.search_btn.grid(row=0, column=4, padx=10, pady=5)

        prod_list_fr = ttk.Frame(self.search_frame)
        prod_list_fr.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
        self.search_frame.rowconfigure(1, weight=1)
        self.search_frame.columnconfigure(3, weight=1)
        
        # Create custom style for product list
        style = ttk.Style()
        style.configure("ProductList.Treeview",
                       background="#3E3E3E",
                       foreground="white",
                       rowheight=30,
                       fieldbackground="#3E3E3E",
                       font=("Helvetica", 14))
        style.configure("ProductList.Treeview.Heading",
                      background="#2B2B2B",
                      foreground="white",
                      font=("Helvetica", 14, "bold"))
        style.map("ProductList.Treeview",
                 background=[("selected", "#4A6984")],
                 foreground=[("selected", "white")])

        self.product_list_table = ttk.Treeview(
            prod_list_fr, columns=("ID", "Name", "Price"), show="headings",
            style="ProductList.Treeview"
        )
        self.product_list_table.column("#0", width=0, stretch=False)
        for col, w, anchor in [
            ("ID", 60, CENTER), ("Name", 280, W), ("Price", 80, E)
        ]:
            self.product_list_table.heading(col, text=col, anchor=anchor)
            self.product_list_table.column(col, width=w, anchor=anchor,
                                           stretch=(col == "Name"))
                                           
        # Add scrollbar to product list
        prod_scroll = ttk.Scrollbar(prod_list_fr, orient="vertical", command=self.product_list_table.yview)
        self.product_list_table.configure(yscrollcommand=prod_scroll.set)
        
        prod_scroll.pack(side=RIGHT, fill=Y)
        self.product_list_table.pack(side=LEFT, fill=BOTH, expand=True)

        ttk.Button(
            self.search_frame, textvariable=self.add_selected_btn_text,
            bootstyle=SUCCESS, style="Touch.TButton",
            command=self._add_selected_product
        ).grid(row=2, column=0, columnspan=5, pady=10)

        # -- RIGHT COL ---------------------------------------------------
        # Shopping Cart
        cart_frame = ttk.Frame(right_col, padding=10)
        cart_frame.pack(fill=BOTH, expand=True)

        # Cart label
        ttk.Label(cart_frame, textvariable=self.cart_frame_text, font=("Helvetica", 18, "bold"))\
            .pack(side=TOP, anchor="w", pady=(0, 10))

        cart_table_frame = ttk.Frame(cart_frame)
        cart_table_frame.pack(fill=BOTH, expand=True)

        vsb_cart = ttk.Scrollbar(cart_table_frame, orient="vertical")
        
        # Create cart table style
        style.configure("Cart.Treeview",
                       background="#3E3E3E",
                       foreground="white",
                       rowheight=30,
                       fieldbackground="#3E3E3E",
                       font=("Helvetica", 14))
        style.configure("Cart.Treeview.Heading",
                      background="#2B2B2B",
                      foreground="white",
                      font=("Helvetica", 14, "bold"))
        style.map("Cart.Treeview",
                 background=[("selected", "#4A6984")],
                 foreground=[("selected", "white")])
                 
        self.cart_table = ttk.Treeview(
            cart_table_frame,
            columns=("ID", "Name", "Price", "Quantity", "Total"),
            show="headings", style="Cart.Treeview",
            yscrollcommand=vsb_cart.set,
        )
        self.cart_table.column("#0", width=0, stretch=False)
        for col, w, anchor in [
            ("ID", 50, CENTER),
            ("Name", 180, W),
            ("Price", 80,  E),
            ("Quantity", 80, CENTER),
            ("Total", 100, E),
        ]:
            self.cart_table.heading(col, text=col, anchor=anchor)
            self.cart_table.column(col, width=w, anchor=anchor, stretch=(col == "Name"))
        self.cart_table.tag_configure("even", background="#4A4A4A", foreground="white")
        self.cart_table.tag_configure("odd",  background="#3A3A3A", foreground="white")

        self.cart_table.pack(side=LEFT, fill=BOTH, expand=True)
        vsb_cart.config(command=self.cart_table.yview)
        vsb_cart.pack(side=RIGHT, fill=Y)

        cart_ctrl = ttk.Frame(right_col, padding=10)
        cart_ctrl.pack(fill=X)
        ttk.Button(
            cart_ctrl, text="+ Qty", bootstyle=SUCCESS, style="Touch.TButton",
            command=self._increment_quantity
        ).pack(side=LEFT, padx=10)
        ttk.Button(
            cart_ctrl, text="- Qty", bootstyle=PRIMARY, style="Touch.TButton",
            command=self._decrement_quantity
        ).pack(side=LEFT, padx=10)
        ttk.Button(
            cart_ctrl, text="Remove", bootstyle=DANGER, style="Touch.TButton",
            command=self._remove_item
        ).pack(side=LEFT, padx=10)

        summary_fr = ttk.Frame(right_col, padding=20)
        summary_fr.pack(fill=X)
        ttk.Label(summary_fr, textvariable=self.payment_label_text, font=("Helvetica", 18))\
            .grid(row=0, column=0, sticky=E, padx=5, pady=5)
        self.payment_var = StringVar(value=tr(MSG_CASH))
        self.pay_combo = ttk.Combobox(
            summary_fr, textvariable=self.payment_var,
            values=[tr(MSG_CASH), tr(MSG_CARD)], state="readonly",
            font=("Helvetica", 18), width=8
        )
        self.pay_combo.grid(row=0, column=1, sticky=W, padx=5, pady=5)

        ttk.Label(summary_fr, textvariable=self.discount_text, font=("Helvetica", 18))\
            .grid(row=1, column=0, sticky=E, padx=5, pady=5)
        self.discount_entry = ttk.Entry(summary_fr, width=8, font=("Helvetica", 18))
        self.discount_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        self.discount_entry.insert(0, "0")

        self.subtotal_label = ttk.Label(summary_fr, text="Subtotal: $0.00",
                                        font=("Helvetica", 18))
        self.subtotal_label.grid(row=2, column=0, columnspan=2, sticky=W, pady=5)
        self.discount_label = ttk.Label(summary_fr, text="Discount: $0.00",
                                        font=("Helvetica", 18))
        self.discount_label.grid(row=3, column=0, columnspan=2, sticky=W, pady=5)

        # 4) Footer ------------------------------------------------------
        footer = ttk.Frame(self, padding=10, style="TFrame")
        footer.pack(side=BOTTOM, fill=X)

        # Footer sizing and positioning
        footer.config(height=70)  # Fixed height for footer
        footer.pack_propagate(False)  # Don't shrink

        self.footer_total_lbl = ttk.Label(
            footer, text="Total: $0.00", font=("Helvetica", 26, "bold")
        )
        self.footer_total_lbl.pack(side=LEFT, padx=20)

        ttk.Button(
            footer, textvariable=self.complete_sale_btn_text,
            bootstyle=SUCCESS, style="Touch.TButton", command=self._complete_sale
        ).pack(side=LEFT, padx=10)
        ttk.Button(
            footer, textvariable=self.mark_debit_btn_text,
            bootstyle=WARNING, style="Touch.TButton", command=self._mark_as_debit
        ).pack(side=LEFT, padx=10)
        ttk.Button(
            footer, textvariable=self.reset_cart_btn_text,
            bootstyle=DANGER, style="Touch.TButton", command=self._reset_cart
        ).pack(side=LEFT, padx=10)
        ttk.Button(
            footer, textvariable=self.view_invoices_btn_text,
            bootstyle=INFO, style="Touch.TButton", command=self._view_invoices
        ).pack(side=LEFT, padx=10)

        # dynamic recalc bindings --------------------------------------
        self.discount_entry.bind("<KeyRelease>", lambda _: self._calculate_total())
        self.pay_combo.bind("<<ComboboxSelected>>", lambda _: self._calculate_total())
        self._calculate_total()

    # Add a method to bind the mousewheel event to any widget
    def bind_mousewheel(self, widget):
        """Bind mousewheel events to the widget for scrolling"""
        widget.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        widget.bind("<Button-4>", self._on_mousewheel)    # Linux
        widget.bind("<Button-5>", self._on_mousewheel)    # Linux
        
        # Recursively bind to all children
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling for the treeviews"""
        try:
            # Attempt to scroll whichever treeview has focus or mouse over
            if self.cart_table.identify_region(event.x_root, event.y_root):
                self.cart_table.yview_scroll(-1 if event.delta > 0 else 1, "units")
            elif self.product_list_table.identify_region(event.x_root, event.y_root):
                self.product_list_table.yview_scroll(-1 if event.delta > 0 else 1, "units")
        except:
            # Fallback for Linux
            if hasattr(event, 'num') and event.num == 4:
                try:
                    self.cart_table.yview_scroll(-1, "units")
                except:
                    self.product_list_table.yview_scroll(-1, "units")
            elif hasattr(event, 'num') and event.num == 5:
                try:
                    self.cart_table.yview_scroll(1, "units")
                except:
                    self.product_list_table.yview_scroll(1, "units")

    # ------------------------------------------------------------------
    #  Database & cart helpers (unchanged)
    # ------------------------------------------------------------------
    @staticmethod
    def _fetch_categories():
        """Get all product categories using the data access layer"""
        try:
            return get_product_categories()
        except Exception:
            # If there's an error, return an empty list
            return []

    def _search_products(self, category: str, term: str):
        """Search for products using the data access layer"""
        # Clear existing items
        for item in self.product_list_table.get_children():
            self.product_list_table.delete(item)
            
        show_out_of_stock = True  # In sales page, we typically want to see all products
        
        try:
            # Use data access layer to get filtered products
            products = get_products(
                category=None if category == "All" else category,
                search_term=term if term else None,
                show_out_of_stock=show_out_of_stock
            )
            
            # Add products to the list
            for product in products:
                price = product['SellingPrice']
                stock = product['Stock']
                
                # Determine stock status
                stock_tag = 'instock' if stock > 0 else 'outofstock'
                
                self.product_list_table.insert(
                    "", "end",
                    values=(
                        product['ProductID'],
                        product['Name'],
                        f"${price:.2f}"
                    ),
                    tags=(stock_tag,)
                )
                
            # Log the search
            log_activity(f"Searched products: {category} / '{term}' - Found {len(products)} results")
            
        except Exception as e:
            messagebox.showerror("Search Error", f"Failed to search products: {str(e)}")
            log_activity(f"Error searching products: {str(e)}")

    def _add_selected_product(self):
        sel = self.product_list_table.selection()
        if not sel:
            messagebox.showwarning("Warning", "No product selected!", parent=self)
            return
        values = self.product_list_table.item(sel[0], "values")
        pid = int(values[0])
        name = values[1]
        price_str = values[2].replace('$', '')  # Remove the $ sign
        price = float(price_str)
        self._add_to_cart_product(pid, name, price)

    def _add_to_cart(self):
        code = self.qr_entry.get().strip()
        if not code:
            messagebox.showwarning("Warning", "Please enter a code!", parent=self)
            return
        product = self._fetch_product_by_code(code)
        if not product:
            messagebox.showwarning("Warning", "Product not found!", parent=self)
            return
        pid, name, price, *_ = product
        self._add_to_cart_product(pid, name, price)

    def _add_to_cart_product(self, pid: int, name: str, price: float):
        # Check current stock before adding to cart using the data access layer
        try:
            # Get the stock information for this product
            product_info = get_product_stock(pid)
            
            if not product_info:
                messagebox.showwarning("Product Not Found", "This product ID doesn't exist in the database.", parent=self)
                return
            
            available_stock = product_info['stock']
            
            # If product already in cart → check if we can increment qty -------------------
            for rowid in self.cart_table.get_children():
                vals = self.cart_table.item(rowid, "values")
                if int(vals[0]) == pid:
                    current_qty = int(vals[3])
                    new_qty = current_qty + 1
                    
                    # Check if we have enough stock
                    if new_qty > available_stock:
                        messagebox.showwarning(
                            "Low Stock", 
                            f"Not enough stock available for {name}.\nRequested: {new_qty}, Available: {available_stock}",
                            parent=self
                        )
                        # Log the failed attempt
                        log_activity(f"Failed to add item {name} (ID: {pid}) to cart - insufficient stock")
                        return
                        
                    # Enough stock available, update cart
                    self.cart_table.item(
                        rowid, values=(vals[0], vals[1], f"{price:.2f}", new_qty,
                                      f"{price * new_qty:.2f}")
                    )
                    # Log the product quantity increase
                    log_activity(f"Increased quantity of {name} (ID: {pid}) to {new_qty} in cart")
                    self._calculate_total()
                    return
                    
            # Item not in cart, check if we have at least 1 in stock
            if available_stock <= 0:
                messagebox.showwarning(
                    "Out of Stock", 
                    f"The product '{name}' is out of stock.",
                    parent=self
                )
                # Log the failed attempt
                log_activity(f"Failed to add item {name} (ID: {pid}) to cart - out of stock")
                return
            
            # Otherwise add new row -------------------------------------------
            idx = len(self.cart_table.get_children())
            tag = "even" if idx % 2 == 0 else "odd"
            self.cart_table.insert(
                "", END,
                values=(pid, name, f"{price:.2f}", 1, f"{price:.2f}"),
                tags=(tag,)
            )
            # Log the new product addition
            log_activity(f"Added {name} (ID: {pid}) to cart")
            self._calculate_total()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check product stock: {str(e)}", parent=self)
            log_activity(f"Error checking stock for product {pid}: {str(e)}")

    def _increment_quantity(self):
        sel = self.cart_table.selection()
        if not sel:
            messagebox.showwarning("Warning", "No item selected!", parent=self)
            return
        rowid = sel[0]; vals = self.cart_table.item(rowid, "values")
        pid = int(vals[0])
        current_qty = int(vals[3])
        new_qty = current_qty + 1
        price = float(vals[2])
        
        try:
            # Get the stock information for this product using the data access layer
            product_info = get_product_stock(pid)
            
            if not product_info:
                messagebox.showwarning("Product Not Found", "This product ID doesn't exist in the database.", parent=self)
                return
            
            available_stock = product_info['stock']
            
            if new_qty > available_stock:
                messagebox.showwarning(
                    "Low Stock", 
                    f"Not enough stock available for {vals[1]}.\nRequested: {new_qty}, Available: {available_stock}",
                    parent=self
                )
                # Log the failed attempt
                log_activity(f"Failed to increase quantity of {vals[1]} (ID: {pid}) - insufficient stock")
                return
            
            # Update the quantity
            self.cart_table.item(
                rowid, values=(vals[0], vals[1], vals[2], new_qty, f"{price * new_qty:.2f}")
            )
            # Log the quantity increase
            log_activity(f"Increased quantity of {vals[1]} (ID: {pid}) to {new_qty} in cart")
            self._calculate_total()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check product stock: {str(e)}", parent=self)
            log_activity(f"Error checking stock for product {pid}: {str(e)}")

    def _decrement_quantity(self):
        sel = self.cart_table.selection()
        if not sel:
            messagebox.showwarning("Warning", "No item selected!", parent=self)
            return
        rowid = sel[0]; vals = self.cart_table.item(rowid, "values")
        qty = int(vals[3]) - 1; price = float(vals[2])
        if qty <= 0:
            self.cart_table.delete(rowid)
            # Log item removal
            log_activity(f"Removed {vals[1]} (ID: {vals[0]}) from cart")
        else:
            self.cart_table.item(
                rowid, values=(vals[0], vals[1], vals[2], qty, f"{price * qty:.2f}")
            )
            # Log quantity decrease
            log_activity(f"Decreased quantity of {vals[1]} (ID: {vals[0]}) to {qty} in cart")
        self._calculate_total()

    def _remove_item(self):
        sel = self.cart_table.selection()
        if not sel:
            messagebox.showwarning("Warning", "No item selected!", parent=self)
            return
        # Get item details before deletion for logging
        vals = self.cart_table.item(sel[0], "values")
        item_name = vals[1]
        item_id = vals[0]
        
        self.cart_table.delete(sel[0])
        # Log the removal
        log_activity(f"Removed {item_name} (ID: {item_id}) from cart")
        self._calculate_total()

    # ------------------------------------------------------------------
    #  Barcode / QR scanner
    # ------------------------------------------------------------------
    def _scan_code(self):
        self.stop_scanning = False
        scan_win = Toplevel(self); scan_win.title("Scanning…")
        ttk.Label(
            scan_win, text="Press 'Stop Scanning' or 'q' in the camera window to quit.",
            font=("Helvetica", 16)
        ).pack(pady=20)
        ttk.Button(
            scan_win, text="Stop Scanning",
            bootstyle=DANGER, style="Touch.TButton",
            command=lambda: self._stop_cam(scan_win)
        ).pack(pady=10)

        def camera_loop():
            cap = cv2.VideoCapture(0)
            try:
                while not self.stop_scanning:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    for code in decode(frame):
                        data = code.data.decode("utf‑8")
                        # Schedule UI updates on the main thread
                        self.after_idle(lambda d=data: self._process_scanned_code(d, scan_win))
                        # Exit the loop after detecting a code
                        return
                    cv2.imshow("Scanning…", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            finally:
                # Always release camera resources
                cap.release()
                cv2.destroyAllWindows()

        threading.Thread(target=camera_loop, daemon=True).start()
        scan_win.protocol("WM_DELETE_WINDOW", lambda: self._stop_cam(scan_win))
    
    def _process_scanned_code(self, data, scan_win):
        """Process the scanned barcode data on the main thread"""
        # Update the entry field
        self.qr_entry.delete(0, END)
        self.qr_entry.insert(0, data)
        # Add to cart
        self._add_to_cart()
        # Close the scanning window
        self._stop_cam(scan_win)

    def _stop_cam(self, win):
        self.stop_scanning = True
        win.destroy()

    # ------------------------------------------------------------------
    #  DB helpers / totals
    # ------------------------------------------------------------------
    def _fetch_product_by_code(self, code: str):
        """Fetch product by barcode using the data access layer"""
        try:
            product = get_product_by_barcode(code)
            if not product:
                return None
                
            # Return only the essential fields needed
            return (
                product['ProductID'],
                product['Name'],
                product['SellingPrice']
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch product: {str(e)}", parent=self)
            log_activity(f"Error fetching product by code: {str(e)}")
            return None

    def _calculate_total(self):
        """Calculate and update the cart totals"""
        subtotal = sum(
            float(self.cart_table.item(i, "values")[4])
            for i in self.cart_table.get_children()
        )
        try:
            discount_val = float(self.discount_entry.get().strip())
        except ValueError:
            discount_val = 0.0
        final_total = max(subtotal - discount_val, 0.0)

        self.subtotal_label.config(text=f"{tr(MSG_SUBTOTAL)}: ${subtotal:.2f}")
        self.discount_label.config(text=f"{tr(MSG_DISCOUNT)}: ${discount_val:.2f}")
        self.footer_total_lbl.config(text=f"{tr(MSG_TOTAL)}: ${final_total:.2f}")
        if self.total_label:
            self.total_label.config(text=f"{tr(MSG_TOTAL)}: ${final_total:.2f}")

    # ------------------------------------------------------------------
    #  Invoice viewer wrapper (new)
    # ------------------------------------------------------------------
    def _view_invoices(self):
        # Opens the new standalone viewer in a child window
        show_all_invoices(master=self.winfo_toplevel())

    # ------------------------------------------------------------------
    #  Cart / sale lifecycle helpers
    # ------------------------------------------------------------------
    def _reset_cart(self):
        if self.cart_table.get_children():
            # Only log if there were items in the cart
            log_activity("Cleared shopping cart")
        self.cart_table.delete(*self.cart_table.get_children())
        self.discount_entry.delete(0, END)
        self.discount_entry.insert(0, "0")
        self._calculate_total()

    def _complete_sale(self):
        if not self.cart_table.get_children():
            messagebox.showwarning("Warning", "Cart is empty!", parent=self)
            return

        # Prepare cart items
        cart_items = []
        
        for item_id in self.cart_table.get_children():
            pid, name, price_str, qty_str, total_str = self.cart_table.item(item_id, "values")
            cart_items.append({
                'product_id': int(pid),
                'name': name,
                'price': float(price_str),
                'quantity': int(qty_str),
                'total': float(total_str)
            })

        # Get payment info
        payment_method = self.payment_var.get()
        discount = float(self.discount_entry.get().strip() or 0.0)

        try:
            # Use data access layer to complete the sale
            # The complete_sale function now uses batch stock checks and proper transaction management
            invoice_id = complete_sale(
                cart_items=cart_items,
                payment_method=payment_method,
                discount=discount,
                as_debit=False
            )
            
            messagebox.showinfo(
                "Success", f"Sale completed! Invoice #{invoice_id} created.",
                parent=self
            )
            self._reset_cart()

        except Exception as e:
            error_msg = f"Could not complete sale: {str(e)}"
            messagebox.showerror("Error", error_msg, parent=self)
            log_activity(f"Error during sale: {error_msg}")

    def _mark_as_debit(self):
        if not self.cart_table.get_children():
            messagebox.showwarning("Warning", "Cart is empty!", parent=self)
            return

        # Create customer info dialog
        debit_win = Toplevel(self)
        debit_win.title("Add Debit Information")
        debit_win.geometry("600x550")  # Increased size for better visibility
        debit_win.resizable(True, True)  # Allow resizing
        debit_win.minsize(550, 450)    # Set minimum size
        debit_win.transient(self)
        debit_win.grab_set()
        
        # Center the window
        debit_win.update_idletasks()
        width = debit_win.winfo_width()
        height = debit_win.winfo_height()
        x = (debit_win.winfo_screenwidth() // 2) - (width // 2)
        y = (debit_win.winfo_screenheight() // 2) - (height // 2)
        debit_win.geometry(f"{width}x{height}+{x}+{y}")
        
        # Main container with scrolling capability
        main_container = ttk.Frame(debit_win)
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Add a canvas for scrolling if needed
        canvas = ttk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        # Content frame that will be placed inside the canvas
        content = ttk.Frame(canvas, padding=20)
        
        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Add the content frame to the canvas
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
        
        # Configure the canvas to resize with the window and update scrollregion
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", configure_canvas)
        
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content.bind("<Configure>", configure_scroll_region)
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Unbind mousewheel when dialog is destroyed
        def _on_destroy(event):
            canvas.unbind_all("<MouseWheel>")
        debit_win.bind("<Destroy>", _on_destroy)
        
        # Title with better formatting
        ttk.Label(
            content, text="Customer Information", 
            font=("Helvetica", 24, "bold")
        ).pack(pady=(0, 20))
        
        # Cart summary with improved layout
        cart_frame = ttk.LabelFrame(content, text="Cart Summary", padding=15)
        cart_frame.pack(fill=X, pady=10)
        
        # Calculate totals with proper formatting
        subtotal = sum(float(self.cart_table.item(i, "values")[4]) 
                     for i in self.cart_table.get_children())
        discount = float(self.discount_entry.get().strip() or 0)
        total = max(subtotal - discount, 0)
        
        # Use grid for better layout
        ttk.Label(cart_frame, text="Items:", font=("Helvetica", 14, "bold")).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        ttk.Label(cart_frame, text=f"{len(self.cart_table.get_children())}", font=("Helvetica", 14)).grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        ttk.Label(cart_frame, text="Subtotal:", font=("Helvetica", 14, "bold")).grid(row=1, column=0, sticky=W, padx=5, pady=5)
        ttk.Label(cart_frame, text=f"${subtotal:.2f}", font=("Helvetica", 14)).grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        ttk.Label(cart_frame, text="Discount:", font=("Helvetica", 14, "bold")).grid(row=2, column=0, sticky=W, padx=5, pady=5)
        ttk.Label(cart_frame, text=f"${discount:.2f}", font=("Helvetica", 14)).grid(row=2, column=1, sticky=W, padx=5, pady=5)
        
        ttk.Label(cart_frame, text="Total:", font=("Helvetica", 16, "bold")).grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.total_label = ttk.Label(cart_frame, text=f"${total:.2f}", font=("Helvetica", 16, "bold"))
        self.total_label.grid(row=3, column=1, sticky=W, padx=5, pady=5)
        
        # Configure grid columns to expand properly
        cart_frame.columnconfigure(1, weight=1)
        
        # Customer form with improved layout
        form_frame = ttk.LabelFrame(content, text="Customer Details", padding=15)
        form_frame.pack(fill=X, pady=15)
        
        # Configure form grid columns for better layout
        form_frame.columnconfigure(0, weight=0, minsize=150)  # Fixed width for labels
        form_frame.columnconfigure(1, weight=1)  # Stretch the input fields
        
        ttk.Label(form_frame, text="Customer Name:", font=("Helvetica", 14)).grid(row=0, column=0, sticky=W, pady=10, padx=5)
        name_var = StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=name_var, font=("Helvetica", 14), width=25)
        name_entry.grid(row=0, column=1, sticky=(W, E), pady=10, padx=5)
        name_entry.focus_set()
        
        ttk.Label(form_frame, text="Phone Number:", font=("Helvetica", 14)).grid(row=1, column=0, sticky=W, pady=10, padx=5)
        phone_var = StringVar()
        phone_entry = ttk.Entry(form_frame, textvariable=phone_var, font=("Helvetica", 14), width=25)
        phone_entry.grid(row=1, column=1, sticky=(W, E), pady=10, padx=5)
        
        # Buttons with better layout
        btn_frame = ttk.Frame(content)
        btn_frame.pack(fill=X, pady=20)
        
        def save_debtor_info():
            # Validate inputs
            customer_name = name_var.get().strip()
            customer_phone = phone_var.get().strip()
            
            if not customer_name:
                messagebox.showwarning("Missing Information", 
                                       "Please enter customer name",
                                       parent=debit_win)
                return
                
            if not customer_phone:
                messagebox.showwarning("Missing Information", 
                                       "Please enter customer phone",
                                       parent=debit_win)
                return
            
            # Prepare cart items
            cart_items = []
            
            for item_id in self.cart_table.get_children():
                pid, name, price_str, qty_str, total_str = self.cart_table.item(item_id, "values")
                cart_items.append({
                    'product_id': int(pid),
                    'name': name,
                    'price': float(price_str),
                    'quantity': int(qty_str),
                    'total': float(total_str)
                })

            # Get payment info
            payment_method = "Debit"
            discount = float(self.discount_entry.get().strip() or 0.0)
            
            try:
                # Use data access layer to complete the sale as debit
                invoice_id = complete_sale(
                    cart_items=cart_items,
                    payment_method=payment_method,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    discount=discount,
                    as_debit=True
                )
                
                debit_win.destroy()
                
                messagebox.showinfo(
                    "Success", 
                    f"Debit recorded! Invoice #{invoice_id} created for {customer_name}.",
                    parent=self
                )
                self._reset_cart()

            except Exception as e:
                error_msg = f"Could not create debit: {str(e)}"
                messagebox.showerror("Error", error_msg, parent=debit_win)
                log_activity(f"Error creating debit: {error_msg}")
        
        ttk.Button(btn_frame, text="Save Debit", 
                  bootstyle=SUCCESS, style="Touch.TButton",
                  command=save_debtor_info).pack(side=LEFT, padx=5)
        
        def cancel_debit():
            debit_win.destroy()
            
        ttk.Button(btn_frame, text="Cancel", 
                  bootstyle=SECONDARY, style="Touch.TButton",
                  command=cancel_debit).pack(side=RIGHT, padx=5)

    def _retranslate(self):
        """Update all text elements with translated strings"""
        # Set widget direction based on language
        set_widget_direction(self)
        
        # Update all text variables
        self.title_text.set(tr(MSG_SALES_SCREEN))
        self.back_btn_text.set(tr(MSG_BACK_HOME))
        self.barcode_label_text.set(tr(MSG_BARCODE))
        self.add_cart_btn_text.set(tr(MSG_ADD_CART))
        self.scan_btn_text.set(tr(MSG_SCAN_CODE))
        
        # Update the Labelframe text directly since it doesn't support textvariable
        if hasattr(self, 'search_frame'):
            self.search_frame.configure(text=tr(MSG_SEARCH_PRODUCTS))
            
        self.category_label_text.set(tr(MSG_CATEGORY))
        self.search_label_text.set(tr(MSG_SEARCH))
        self.search_btn_text.set(tr(MSG_SEARCH))
        
        # Update table headers
        self.id_col_text.set(tr(MSG_ID))
        self.name_col_text.set(tr(MSG_NAME))
        self.price_col_text.set(tr(MSG_PRICE))
        
        # Update other buttons and labels
        self.add_selected_btn_text.set(tr(MSG_ADD_SELECTED))
        self.cart_frame_text.set(tr(MSG_SHOPPING_CART))
        self.payment_label_text.set(tr(MSG_PAYMENT_METHOD))
        self.cash_text.set(tr(MSG_CASH))
        self.card_text.set(tr(MSG_CARD))
        self.discount_text.set(tr(MSG_DISCOUNT))
        self.complete_sale_btn_text.set(tr(MSG_COMPLETE_SALE))
        self.mark_debit_btn_text.set(tr(MSG_MARK_DEBIT))
        self.reset_cart_btn_text.set(tr(MSG_RESET_CART))
        self.view_invoices_btn_text.set(tr(MSG_VIEW_INVOICES))
        
        # Update combobox values
        if hasattr(self, 'pay_combo') and self.pay_combo is not None:
            self.pay_combo.configure(values=[tr(MSG_CASH), tr(MSG_CARD)])
        
        # Recalculate totals to update labels with translated text
        if hasattr(self, '_calculate_total') and hasattr(self, 'cart_table') and self.cart_table is not None:
            self._calculate_total()
            
    def __del__(self):
        """Unregister the callback when the widget is destroyed"""
        unregister_refresh_callback(self._retranslate)

    def refresh(self):
        """
        Complete refresh of the page - rebuilds all UI elements
        and updates translations. Called when page is shown or 
        when language changes.
        """
        # Clear all existing widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        # Reset state variables
        self.stop_scanning = False
        self.qr_entry = None
        self.cart_table = None
        self.discount_entry = None
        self.payment_var = None
        self.subtotal_label = None
        self.discount_label = None
        self.total_label = None
        self.footer_total_lbl = None
        
        # Rebuild UI with current language
        self._build_ui()
        self._retranslate()
        
        # Focus on the barcode entry if it exists
        if self.qr_entry:
            self.qr_entry.focus_set()












