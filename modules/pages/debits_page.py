# modules/pages/debits_page.py – 2025‑05‑10 update
# -----------------------------------------------------------------------------
# * Completely redesigned UI with better filters and statistics
# * Now uses the Invoices table directly instead of the Debits table
# * Added proper invoice item viewing and payment processing
# * Added statistics showing total, pending, and paid amounts
# * Improved filtering with database queries instead of UI filtering
# * Added add new debit functionality with proper customer management
# * Added payment recording with support for partial payments
# * Added invoice item display with product details
# * Added centralized data access layer for database operations
# -----------------------------------------------------------------------------

import datetime
from datetime import timedelta
import sqlite3
from typing import Tuple, Dict, List, Any

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import (
    BOTH, END, CENTER, W, E, LEFT, RIGHT, X, Y, messagebox, StringVar
)

from modules.db_manager import get_connection, return_connection
from modules.Login import current_user
from modules.data_access import (
    get_debits, get_invoice_items, record_debit_payment, add_debit
)
import logging

# Import internationalization support
from modules.i18n import _, register_refresh_callback, unregister_refresh_callback, set_widget_direction, tr

# Configure logger
logger = logging.getLogger(__name__)

# Message-ID constants (English base text)
MSG_MANAGE_DEBITS = "Manage Debits"
MSG_ADD_NEW_DEBIT = "Add New Debit"
MSG_BACK_HOME = "Back to Home"
MSG_FILTERS = "Filters"
MSG_CUSTOMER_NAME = "Customer Name:"
MSG_PHONE = "Phone:"
MSG_DATE = "Date:"
MSG_STATUS = "Status:"
MSG_APPLY_FILTERS = "Apply Filters"
MSG_RESET = "Reset"
MSG_TOTAL_AMOUNT = "Total Amount"
MSG_PENDING = "Pending"
MSG_PAID = "Paid"
MSG_INVOICE_ID = "Invoice ID"
MSG_CUSTOMER = "Customer"
MSG_PHONE_NUMBER = "Phone Number"
MSG_TOTAL = "Total"
MSG_BALANCE = "Balance"
MSG_ALL = "All"


# ──────────────────────────────────────────────────────────────────────────────
class DebitsPage(ttk.Frame):
    """Manage Pending / Paid debits – embedded frame."""

    # ------------------------------------------------------------------
    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        
        # Create StringVars for translatable text elements
        self.title_text = StringVar()
        self.add_debit_text = StringVar()
        self.back_home_text = StringVar()
        self.total_amount_text = StringVar()
        self.pending_text = StringVar()
        self.paid_text = StringVar()
        self.customer_name_text = StringVar()
        self.phone_text = StringVar()
        self.date_text = StringVar()
        self.status_text = StringVar()
        self.apply_filters_text = StringVar()
        self.reset_text = StringVar()
        self.column_headers = {
            "id": StringVar(),
            "customer": StringVar(),
            "phone": StringVar(),
            "date": StringVar(),
            "total": StringVar(),
            "paid": StringVar(),
            "status": StringVar(),
            "balance": StringVar()
        }
        
        # Build UI and register for language changes
        self._build_ui()
        self._retranslate()
        register_refresh_callback(self._retranslate)
        
        # Optional: Bind to language changed event
        if self.winfo_toplevel():
            self.winfo_toplevel().bind('<<LanguageChanged>>', lambda e: self._retranslate())

    # ───────────────────────────────────────────────────────────────────
    #  Layout helpers
    # ------------------------------------------------------------------
    def _make_topbar(self, title: str):
        """Create a top bar with title and back button"""
        top = ttk.Frame(self, style="TFrame", padding=10)
        top.pack(fill=X)
        
        self.title_label = ttk.Label(top, textvariable=self.title_text, style="Header.TLabel")
        self.title_label.pack(side=LEFT, padx=(10, 20))
            
        # Add New Debit button
        self.add_debit_btn = ttk.Button(top, textvariable=self.add_debit_text, 
                  bootstyle="success",
                  padding=(20, 10),
                  command=self._add_debit)
        self.add_debit_btn.pack(side=LEFT, padx=20)
        
        self.back_btn = ttk.Button(top, textvariable=self.back_home_text, style="Small.TButton",
                   bootstyle=SECONDARY,
                   command=lambda: self.controller.show_frame("MainMenuPage"))
        self.back_btn.pack(side=RIGHT, padx=20)

    def _build_ui(self):
        """Build the debits UI"""
        logger.info("Building Debits UI")
        
        # Set widget direction based on language
        set_widget_direction(self)
        
        # Add top bar with title and back button
        self._make_topbar(tr(MSG_MANAGE_DEBITS))
        
        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # Statistics bar at the top
        stats_frame = ttk.Frame(main_container)
        stats_frame.pack(fill=X, pady=(0, 15))
        
        # Create statistics labels with larger fonts
        self.total_debits_var = StringVar()
        self.pending_debits_var = StringVar()
        self.paid_debits_var = StringVar()
        
        self.total_label = ttk.Label(stats_frame, textvariable=self.total_debits_var, font=("Arial", 14, "bold"))
        self.pending_label = ttk.Label(stats_frame, textvariable=self.pending_debits_var, font=("Arial", 14, "bold"), bootstyle="warning")
        self.paid_label = ttk.Label(stats_frame, textvariable=self.paid_debits_var, font=("Arial", 14, "bold"), bootstyle="success")
        
        self.total_label.grid(row=0, column=0, padx=15, sticky='w')
        self.pending_label.grid(row=0, column=1, padx=15)
        self.paid_label.grid(row=0, column=2, padx=15, sticky='e')
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        
        # Filter section
        self.filter_frame = ttk.LabelFrame(main_container, text=tr(MSG_FILTERS), padding=15)
        self.filter_frame.pack(fill=X, pady=(0, 15))
        
        # Filter components with larger fonts
        self.customer_label = ttk.Label(self.filter_frame, textvariable=self.customer_name_text, font=("Arial", 12))
        self.customer_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        
        self.name_filter = ttk.Entry(self.filter_frame, width=15, font=("Arial", 12))
        self.name_filter.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        self.phone_label = ttk.Label(self.filter_frame, textvariable=self.phone_text, font=("Arial", 12))
        self.phone_label.grid(row=0, column=2, padx=10, pady=5, sticky='w')
        
        self.phone_filter = ttk.Entry(self.filter_frame, width=15, font=("Arial", 12))
        self.phone_filter.grid(row=0, column=3, padx=10, pady=5, sticky='w')
        
        self.date_label = ttk.Label(self.filter_frame, textvariable=self.date_text, font=("Arial", 12))
        self.date_label.grid(row=0, column=4, padx=10, pady=5, sticky='w')
        
        self.date_filter = ttk.Entry(self.filter_frame, width=15, font=("Arial", 12))
        self.date_filter.grid(row=0, column=5, padx=10, pady=5, sticky='w')
        
        self.status_label = ttk.Label(self.filter_frame, textvariable=self.status_text, font=("Arial", 12))
        self.status_label.grid(row=0, column=6, padx=10, pady=5, sticky='w')
        
        self.status_var = StringVar(value=tr(MSG_ALL))
        self.status_combo = ttk.Combobox(
            self.filter_frame, 
            textvariable=self.status_var, 
            values=[tr(MSG_ALL), tr(MSG_PENDING), tr(MSG_PAID)], 
            width=10, 
            font=("Arial", 12), 
            state="readonly"
        )
        self.status_combo.grid(row=0, column=7, padx=10, pady=5, sticky='w')
        
        # Filter buttons
        button_frame = ttk.Frame(self.filter_frame)
        button_frame.grid(row=0, column=8, padx=10, pady=5, sticky='e')
        
        self.apply_btn = ttk.Button(button_frame, textvariable=self.apply_filters_text, bootstyle="primary", command=self._apply_filter, padding=(10, 5))
        self.apply_btn.pack(side=LEFT, padx=10)
        
        self.reset_btn = ttk.Button(button_frame, textvariable=self.reset_text, bootstyle="secondary", command=self._refresh, padding=(10, 5))
        self.reset_btn.pack(side=LEFT, padx=10)
        
        self.filter_frame.grid_columnconfigure(8, weight=1)
        
        # Debits table
        table_frame = ttk.Frame(main_container)
        table_frame.pack(fill=BOTH, expand=True)
        
        # Create Treeview with improved styling
        columns = ("id", "customer", "phone", "date", "total", "paid", "status", "balance")
        self.debits_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12, style="Debits.Treeview")
        
        # Apply custom style for better readability
        style = ttk.Style()
        style.configure("Debits.Treeview", 
                        rowheight=40,  # Increased row height
                        font=("Arial", 14))  # Increased font size
        style.configure("Debits.Treeview.Heading", 
                        font=("Arial", 14, "bold"))  # Increased header font size
        style.map("Debits.Treeview",
                  background=[("selected", "#4A6984")],
                  foreground=[("selected", "white")])
        
        # Configure columns with proper headers and alignment
        # These will be updated in the _retranslate method
        for col in columns:
            self.debits_tree.heading(col, text=col.capitalize(), anchor=CENTER)
        
        # Set column properties with adjusted widths
        self.debits_tree.column("id", width=120, anchor=CENTER, stretch=False)
        self.debits_tree.column("customer", width=200, anchor=W, stretch=True)
        self.debits_tree.column("phone", width=180, anchor=W, stretch=True)
        self.debits_tree.column("date", width=180, anchor=W, stretch=True)
        self.debits_tree.column("total", width=120, anchor=E, stretch=False)
        self.debits_tree.column("paid", width=120, anchor=E, stretch=False)
        self.debits_tree.column("status", width=100, anchor=CENTER, stretch=False)
        self.debits_tree.column("balance", width=120, anchor=E, stretch=False)
        
        # Configure tags for status styling with better contrast
        self.debits_tree.tag_configure('pending', background='#FFF3CD', foreground='#856404')
        self.debits_tree.tag_configure('paid', background='#D1E7DD', foreground='#0F5132')
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.debits_tree.yview, bootstyle="round")
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.debits_tree.xview, bootstyle="round")
        self.debits_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Place components
        self.debits_tree.pack(side=LEFT, fill=BOTH, expand=True)
        y_scrollbar.pack(side=RIGHT, fill=Y)
        x_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Bind selection event
        self.debits_tree.bind("<<TreeviewSelect>>", self._on_debit_select)
        
        # Initial load
        self._load()

    # ───────────────────────────────────────────────────────────────────
    #  Internationalization
    # ------------------------------------------------------------------
    def _retranslate(self):
        """Update all text elements with translated strings"""
        # Set widget direction based on language
        set_widget_direction(self)
        
        # Update the StringVars with translated text
        self.title_text.set(tr(MSG_MANAGE_DEBITS))
        self.add_debit_text.set(tr(MSG_ADD_NEW_DEBIT))
        self.back_home_text.set(tr(MSG_BACK_HOME))
        
        # Update LabelFrame text directly since it doesn't support textvariable
        if hasattr(self, 'filter_frame'):
            self.filter_frame.configure(text=tr(MSG_FILTERS))
            
        self.customer_name_text.set(tr(MSG_CUSTOMER_NAME))
        self.phone_text.set(tr(MSG_PHONE))
        self.date_text.set(tr(MSG_DATE))
        self.status_text.set(tr(MSG_STATUS))
        self.apply_filters_text.set(tr(MSG_APPLY_FILTERS))
        self.reset_text.set(tr(MSG_RESET))
        
        # Update table headers
        self.column_headers["id"].set(tr(MSG_INVOICE_ID))
        self.column_headers["customer"].set(tr(MSG_CUSTOMER))
        self.column_headers["phone"].set(tr(MSG_PHONE_NUMBER))
        self.column_headers["date"].set(tr(MSG_DATE))
        self.column_headers["total"].set(tr(MSG_TOTAL))
        self.column_headers["paid"].set(tr(MSG_PAID))
        self.column_headers["status"].set(tr(MSG_STATUS))
        self.column_headers["balance"].set(tr(MSG_BALANCE))
        
        # Update column headings - add check for debits_tree
        if hasattr(self, 'debits_tree'):
            for col, var in self.column_headers.items():
                self.debits_tree.heading(col, text=var.get())
            
        # Update combobox values and selection - add checks
        if hasattr(self, 'status_var') and hasattr(self, 'status_combo'):
            current_val = self.status_var.get()
            new_values = [tr(MSG_ALL), tr(MSG_PENDING), tr(MSG_PAID)]
            self.status_combo.configure(values=new_values)
            
            # Try to map current value to new translated value if needed
            if current_val not in new_values:
                # Find closest match
                if "All" in current_val or "all" in current_val:
                    self.status_var.set(tr(MSG_ALL))
                elif "Pending" in current_val or "pending" in current_val:
                    self.status_var.set(tr(MSG_PENDING))
                elif "Paid" in current_val or "paid" in current_val:
                    self.status_var.set(tr(MSG_PAID))
                else:
                    self.status_var.set(tr(MSG_ALL))
        
        # Update statistics
        self._update_stats_text()
        
    def _update_stats_text(self):
        """Update the statistics text with proper translations"""
        # Check if the statistics variables exist
        if not all(hasattr(self, attr) for attr in ['total_debits_var', 'pending_debits_var', 'paid_debits_var']):
            return
            
        # Get the current values
        total_val = self.total_debits_var.get().split('$')[1] if '$' in self.total_debits_var.get() else "0.00"
        pending_val = self.pending_debits_var.get().split('$')[1] if '$' in self.pending_debits_var.get() else "0.00"
        paid_val = self.paid_debits_var.get().split('$')[1] if '$' in self.paid_debits_var.get() else "0.00"
        
        # Set the translated text
        self.total_debits_var.set(f"{tr(MSG_TOTAL_AMOUNT)}: ${total_val}")
        self.pending_debits_var.set(f"{tr(MSG_PENDING)}: ${pending_val}")
        self.paid_debits_var.set(f"{tr(MSG_PAID)}: ${paid_val}")
    
    def __del__(self):
        """Unregister callbacks when the page is destroyed"""
        unregister_refresh_callback(self._retranslate)

    # ───────────────────────────────────────────────────────────────────
    #  Filter methods
    # ------------------------------------------------------------------
    def _get_db_connection(self):
        """Return a connection to the database"""
        return get_connection()

    def _apply_filter(self):
        """Apply filters to the debits view"""
        logger.info("Applying filters to debits view")
        
        # Get filter values
        name_filter = self.name_filter.get().strip().lower() or None
        phone_filter = self.phone_filter.get().strip() or None
        date_filter = self.date_filter.get().strip() or None
        status_filter = None if self.status_var.get() == "All" else self.status_var.get()
        
        # Use centralized method to refresh with filters
        self._refresh_debits(
            name_filter=name_filter,
            phone_filter=phone_filter,
            date_filter=date_filter,
            status_filter=status_filter
        )

    def _refresh(self):
        """Clear filters and reload data"""
        logger.info("Refreshing debits view")
        
        # Clear filter fields
        self.name_filter.delete(0, END)
        self.phone_filter.delete(0, END)
        self.date_filter.delete(0, END)
        self.status_var.set("All")
        
        # Remove action buttons if they exist
        if hasattr(self, 'action_frame') and self.action_frame.winfo_exists():
            self.action_frame.destroy()
        
        # Use centralized method to refresh without filters
        self._refresh_debits()

    def _load(self):
        """Load all debits from database"""
        logger.info("Loading all debits")
        
        # Use centralized method to refresh without filters
        self._refresh_debits()

    # ------------------------------------------------------------------
    def _add_debit(self):
        """Open a form to add a new debit"""
        logger.info("Opening add new debit form")
        
        dialog = ttk.Toplevel(self)
        dialog.title("Add New Debit")
        dialog.geometry("550x400")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Content frame
        content = ttk.Frame(dialog, padding=25)
        content.pack(fill=BOTH, expand=True)
        
        # Form fields
        ttk.Label(content, text="Customer Name:", font=("Arial", 14))\
            .grid(row=0, column=0, sticky=W, pady=15)
        name_entry = ttk.Entry(content, font=("Arial", 14), width=25)
        name_entry.grid(row=0, column=1, sticky=(W, E), pady=15)
        name_entry.focus_set()
        
        ttk.Label(content, text="Phone Number:", font=("Arial", 14))\
            .grid(row=1, column=0, sticky=W, pady=15)
        phone_entry = ttk.Entry(content, font=("Arial", 14), width=25)
        phone_entry.grid(row=1, column=1, sticky=(W, E), pady=15)
        
        ttk.Label(content, text="Invoice ID:", font=("Arial", 14))\
            .grid(row=2, column=0, sticky=W, pady=15)
        invoice_entry = ttk.Entry(content, font=("Arial", 14), width=25)
        invoice_entry.grid(row=2, column=1, sticky=(W, E), pady=15)
        
        ttk.Label(content, text="Amount:", font=("Arial", 14))\
            .grid(row=3, column=0, sticky=W, pady=15)
        amount_entry = ttk.Entry(content, font=("Arial", 14), width=25)
        amount_entry.grid(row=3, column=1, sticky=(W, E), pady=15)
        
        ttk.Label(content, text="Notes:", font=("Arial", 14))\
            .grid(row=4, column=0, sticky=W, pady=15)
        notes_entry = ttk.Entry(content, font=("Arial", 14), width=25)
        notes_entry.grid(row=4, column=1, sticky=(W, E), pady=15)
        
        # Buttons frame
        button_frame = ttk.Frame(content)
        button_frame.grid(row=5, column=0, columnspan=2, pady=25)
        
        def save_debit():
            # Get form values
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            invoice_id_str = invoice_entry.get().strip()
            amount_str = amount_entry.get().strip()
            notes = notes_entry.get().strip()
            
            # Process and save using the background thread to avoid UI freezes
            def process_and_save():
                try:
                    # Convert numeric inputs
                    try:
                        invoice_id = int(invoice_id_str)
                        amount = float(amount_str)
                    except ValueError:
                        return ValueError("Invalid invoice ID or amount. Please enter valid numbers.")
                    
                    # Use the data access layer to add the debit
                    debit_id = add_debit(
                        name=name, 
                        phone=phone, 
                        invoice_id=invoice_id, 
                        amount=amount, 
                        notes=notes
                    )
                    
                    return debit_id
                except Exception as e:
                    return e
            
            # Process result callback
            def on_complete(result):
                if isinstance(result, Exception):
                    # Show error
                    messagebox.showerror("Error", str(result), parent=dialog)
                else:
                    # Show success
                    messagebox.showinfo("Success", "New debit has been added successfully", parent=dialog)
                    dialog.destroy()
                    # Refresh the debits list
                    self._refresh_debits()
            
            # Execute in background thread
            from modules.utils import run_in_background
            run_in_background(
                process_and_save,
                on_complete=on_complete,
                on_error=lambda e: messagebox.showerror("Error", str(e), parent=dialog)
            )
        
        save_btn = ttk.Button(button_frame, text="Save", command=save_debit, bootstyle="success")
        save_btn.pack(side=LEFT, padx=10)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=dialog.destroy, bootstyle="secondary")
        cancel_btn.pack(side=LEFT, padx=10)

    # ───────────────────────────────────────────────────────────────────
    #  Actions
    # ------------------------------------------------------------------
    def _on_debit_select(self, event):
        """Handle selection of a debit in the treeview"""
        # Get selected item
        selection = self.debits_tree.selection()
        if not selection:
            return
            
        # Get selected item data
        selected_item = self.debits_tree.item(selection[0])
        values = selected_item['values']
        
        if not values:
            return
            
        # Extract invoice data
        invoice_id = values[0]
        customer_name = values[1]
        phone = values[2]
        date = values[3]
        total = values[4]
        paid = values[5]
        status = values[6]
        balance = values[7]
        
        logger.info(f"Selected invoice #{invoice_id} ({status})")
        
        # Remove existing action buttons if they exist
        if hasattr(self, 'action_frame') and self.action_frame.winfo_exists():
            self.action_frame.destroy()
            
        # Create frame for action buttons below the treeview with better styling
        self.action_frame = ttk.LabelFrame(self, text="Selected Debit Information", padding=20, bootstyle="secondary")
        self.action_frame.pack(fill=X, pady=15, padx=15)
        
        # Create two columns layout for better organization
        info_frame = ttk.Frame(self.action_frame)
        info_frame.pack(fill=X, expand=True, pady=10)
        
        # Left column - Customer details
        left_col = ttk.Frame(info_frame)
        left_col.pack(side=LEFT, fill=X, expand=True, padx=15)
        
        ttk.Label(left_col, text=f"Invoice #{invoice_id}", font=("Arial", 16, "bold")).pack(anchor="w", pady=3)
        ttk.Label(left_col, text=f"Customer: {customer_name}", font=("Arial", 14)).pack(anchor="w", pady=3)
        ttk.Label(left_col, text=f"Phone: {phone}", font=("Arial", 14)).pack(anchor="w", pady=3)
        ttk.Label(left_col, text=f"Date: {date}", font=("Arial", 14)).pack(anchor="w", pady=3)
        
        # Right column - Financial details
        right_col = ttk.Frame(info_frame)
        right_col.pack(side=RIGHT, fill=X, expand=True, padx=15)
        
        # Add styling based on status
        status_style = "success" if status == "Paid" else "warning"
        
        ttk.Label(right_col, text=f"Total: {total}", font=("Arial", 14)).pack(anchor="w", pady=3)
        ttk.Label(right_col, text=f"Paid: {paid}", font=("Arial", 14)).pack(anchor="w", pady=3)
        ttk.Label(right_col, text=f"Balance: {balance}", font=("Arial", 14, "bold")).pack(anchor="w", pady=3)
        ttk.Label(right_col, text=f"Status: {status}", font=("Arial", 14, "bold"), 
                 bootstyle=status_style).pack(anchor="w", pady=3)
        
        # Button frame
        btn_frame = ttk.Frame(self.action_frame)
        btn_frame.pack(fill=X, expand=True, pady=15)
        
        # View button
        view_btn = ttk.Button(
            btn_frame, 
            text="View Invoice Items", 
            bootstyle="info", 
            padding=(20, 12),
            command=lambda: self._view_invoice_items(invoice_id)
        )
        view_btn.pack(side=LEFT, padx=15)
        
        # Mark as paid button - only enabled for pending debits
        pay_btn = ttk.Button(
            btn_frame, 
            text="Make Payment", 
            bootstyle="success",
            padding=(20, 12),
            command=lambda: self._make_payment(invoice_id)
        )
        pay_btn.pack(side=LEFT, padx=15)
        
        # Only enable payment button for pending invoices
        if status == "Paid":
            pay_btn.config(state="disabled")
            
        # Print invoice button
        print_btn = ttk.Button(
            btn_frame, 
            text="Print Invoice", 
            bootstyle="secondary",
            padding=(20, 12),
            command=lambda: self._print_invoice(invoice_id)
        )
        print_btn.pack(side=LEFT, padx=15)

    def _view_invoice_items(self, invoice_id):
        """Display items from the selected invoice"""
        logger.info(f"Viewing items for invoice #{invoice_id}")
        
        try:
            # Create dialog to display invoice items
            dialog = ttk.Toplevel(self)
            dialog.title(f"Invoice #{invoice_id} Items")
            dialog.geometry("700x600")  # Increased height further to ensure footer visibility
            dialog.resizable(True, True)
            dialog.minsize(650, 550)    # Set minimum size to prevent footer from being cut off
            dialog.grab_set()
            
            # Setup processing of background tasks for this dialog
            process_results_id = None
            
            def process_bg_tasks():
                nonlocal process_results_id
                from modules.utils import background_task_manager
                
                # Process any completed background tasks
                had_results = background_task_manager.process_results(dialog)
                
                # Schedule next check
                if process_results_id:
                    dialog.after_cancel(process_results_id)
                
                # More frequent checks when active tasks are completing
                interval = 100 if had_results else 500
                process_results_id = dialog.after(interval, process_bg_tasks)
            
            # Start processing
            process_bg_tasks()
            
            # Store the process_results_id as an attribute of the dialog
            # so it can be properly cleaned up by other methods that might close this dialog
            dialog.process_results_id = process_results_id
            
            # Ensure we clean up the timer when dialog closes
            def on_dialog_close():
                nonlocal process_results_id
                if process_results_id:
                    dialog.after_cancel(process_results_id)
                dialog.destroy()
            
            dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
            
            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Main container with scrolling capability
            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # Add a canvas for scrolling if needed
            canvas = ttk.Canvas(main_frame)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            container = ttk.Frame(canvas, padding=15)
            
            # Configure the canvas
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill=BOTH, expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add the container frame to the canvas
            canvas_window = canvas.create_window((0, 0), window=container, anchor="nw")
            
            # Configure the canvas to resize with the window
            def configure_canvas(event):
                canvas.itemconfig(canvas_window, width=event.width)
            canvas.bind("<Configure>", configure_canvas)
            
            # Configure the scroll region when the content size changes
            def configure_scroll_region(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
            container.bind("<Configure>", configure_scroll_region)
            
            # Get invoice details and items using data access layer
            invoice, items = get_invoice_items(invoice_id)
            
            if not invoice:
                messagebox.showerror("Error", f"Invoice #{invoice_id} not found", parent=dialog)
                dialog.destroy()
                return
            
            # Display invoice header information
            header_frame = ttk.Frame(container)
            header_frame.pack(fill=X, pady=(0, 15))
            
            # Invoice details in header
            details_frame = ttk.LabelFrame(header_frame, text="Invoice Details", padding=10)
            details_frame.pack(fill=X, side=LEFT, expand=True)
            
            # Format the header details
            ttk.Label(details_frame, text=f"Customer: {invoice['customer_name']}", font=("Arial", 12)).grid(row=0, column=0, sticky=W, padx=5, pady=2)
            ttk.Label(details_frame, text=f"Phone: {invoice['phone']}", font=("Arial", 12)).grid(row=1, column=0, sticky=W, padx=5, pady=2)
            ttk.Label(details_frame, text=f"Date: {invoice['date']}", font=("Arial", 12)).grid(row=0, column=1, sticky=W, padx=5, pady=2)
            ttk.Label(details_frame, text=f"Status: {invoice['status']}", font=("Arial", 12)).grid(row=1, column=1, sticky=W, padx=5, pady=2)
            
            # Financial summary frame
            summary_frame = ttk.LabelFrame(header_frame, text="Payment Summary", padding=10)
            summary_frame.pack(fill=X, side=RIGHT, expand=True)
            
            # Format the financial summary
            ttk.Label(summary_frame, text=f"Total Amount: ${invoice['total']:.2f}", font=("Arial", 12)).grid(row=0, column=0, sticky=W, padx=5, pady=2)
            ttk.Label(summary_frame, text=f"Amount Paid: ${invoice['paid']:.2f}", font=("Arial", 12)).grid(row=1, column=0, sticky=W, padx=5, pady=2)
            ttk.Label(summary_frame, text=f"Balance: ${invoice['balance']:.2f}", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=W, padx=5, pady=2)
            
            # Items table
            items_frame = ttk.LabelFrame(container, text="Invoice Items", padding=10)
            items_frame.pack(fill=BOTH, expand=True)
            
            # Create treeview for items
            columns = ("product_id", "product", "price", "quantity", "total")
            items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)
            
            # Configure columns
            items_tree.heading("product_id", text="Product ID")
            items_tree.heading("product", text="Product")
            items_tree.heading("price", text="Unit Price")
            items_tree.heading("quantity", text="Quantity")
            items_tree.heading("total", text="Total")
            
            items_tree.column("product_id", width=80, anchor="center")
            items_tree.column("product", width=200)
            items_tree.column("price", width=100, anchor="e")
            items_tree.column("quantity", width=80, anchor="center")
            items_tree.column("total", width=100, anchor="e")
            
            # Add scrollbar
            y_scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=items_tree.yview)
            items_tree.configure(yscrollcommand=y_scrollbar.set)
            
            # Place components
            items_tree.pack(side=LEFT, fill=BOTH, expand=True)
            y_scrollbar.pack(side=RIGHT, fill=Y)
            
            # Add items to treeview
            if items:
                for item in items:
                    # Format values
                    price_fmt = f"${item['price']:.2f}"
                    total_fmt = f"${item['item_total']:.2f}"
                    
                    # Insert into treeview
                    items_tree.insert("", "end", values=(
                        item['product_id'], 
                        item['product_name'],
                        price_fmt, 
                        item['quantity'], 
                        total_fmt
                    ))
            else:
                # If no items found, display a message in the treeview
                items_tree.insert("", "end", values=("", "No items found for this invoice", "", "", ""))
            
            # Thank you message and seller information frame
            thank_you_frame = ttk.Frame(container, padding=10)
            thank_you_frame.pack(fill=X, pady=(15, 5))
            
            # Get user info from database
            conn = get_connection()
            cursor = conn.cursor()
            try:
                # The ShiftEmployee column in Invoices stores the username directly as TEXT
                cursor.execute("""
                    SELECT ShiftEmployee 
                    FROM Invoices
                    WHERE InvoiceID = ?
                """, (invoice_id,))
                user_row = cursor.fetchone()
                seller_name = user_row[0] if user_row and user_row[0] else "Unknown"
            except Exception as e:
                # Fallback if the query fails
                logger.error(f"Error getting seller name: {str(e)}")
                seller_name = "Unknown"
            finally:
                return_connection(conn)
            
            # Thank you message with styling
            thank_you_label = ttk.Label(
                thank_you_frame, 
                text="Thank you for shopping with us!",
                font=("Arial", 14, "bold"),
                bootstyle="success"
            )
            thank_you_label.pack(pady=(5, 10))
            
            # Add the seller info
            seller_label = ttk.Label(
                thank_you_frame, 
                text=f"You were served by: {seller_name}",
                font=("Arial", 12)
            )
            seller_label.pack(pady=(0, 5))
            
            # Button frame at bottom
            button_frame = ttk.Frame(container, padding=(10, 20, 10, 10))  # Added extra bottom padding
            button_frame.pack(fill=X, pady=(10, 0))
            
            # If balance > 0, show make payment button
            if invoice['balance'] > 0:
                pay_btn = ttk.Button(
                    button_frame, 
                    text="Make Payment", 
                    bootstyle="success",
                    command=lambda: self._make_payment_from_details(invoice_id, dialog)
                )
                pay_btn.pack(side=LEFT, padx=5)
            
            # Close button
            close_btn = ttk.Button(
                button_frame, 
                text="Close", 
                bootstyle="secondary",
                command=dialog.destroy
            )
            close_btn.pack(side=RIGHT, padx=5)
            
            # Print button
            print_btn = ttk.Button(
                button_frame, 
                text="Print Invoice", 
                bootstyle="info",
                command=lambda: self._print_invoice(invoice_id)
            )
            print_btn.pack(side=RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view invoice items: {str(e)}")
            logger.error(f"Error viewing invoice items: {str(e)}")

    def _make_payment(self, invoice_id):
        """Process payment for the selected invoice"""
        logger.info(f"Processing payment for invoice #{invoice_id}")
        
        # Get the invoice details in the background to avoid UI freezes
        def get_invoice_details():
            try:
                return get_invoice_items(invoice_id)
            except Exception as e:
                return e
        
        def on_invoice_loaded(result):
            if isinstance(result, Exception):
                messagebox.showerror("Error", f"Failed to load invoice: {str(result)}")
                return
                
            invoice, items = result
            
            if not invoice:
                messagebox.showerror("Error", f"Invoice #{invoice_id} not found")
                return
                
            if invoice['status'] == "Paid":
                messagebox.showinfo("Payment", "This invoice is already fully paid.")
                return
            
            # Create payment dialog
            dialog = ttk.Toplevel(self)
            dialog.title("Make Payment")
            dialog.geometry("600x500")  # Increased size for better visibility
            dialog.resizable(True, True)  # Allow resizing
            dialog.minsize(550, 450)    # Set minimum size
            dialog.grab_set()
            
            # Setup processing of background tasks for this dialog
            process_results_id = None
            
            def process_bg_tasks():
                nonlocal process_results_id
                from modules.utils import background_task_manager
                
                # Process any completed background tasks
                had_results = background_task_manager.process_results(dialog)
                
                # Schedule next check
                if process_results_id:
                    dialog.after_cancel(process_results_id)
                
                # More frequent checks when active tasks are completing
                interval = 100 if had_results else 500
                process_results_id = dialog.after(interval, process_bg_tasks)
            
            # Start processing
            process_bg_tasks()
            
            # Store the process_results_id as an attribute of the dialog
            # so it can be properly cleaned up by other methods that might close this dialog
            dialog.process_results_id = process_results_id
            
            # Ensure we clean up the timer when dialog closes
            def on_dialog_close():
                nonlocal process_results_id
                if process_results_id:
                    dialog.after_cancel(process_results_id)
                dialog.destroy()
            
            dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
            
            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Content frame with scrolling capability
            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
            
            # Add a canvas for scrolling if needed
            canvas = ttk.Canvas(main_frame)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            content = ttk.Frame(canvas, padding=10)
            
            # Configure the canvas
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill=BOTH, expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add the content frame to the canvas
            canvas_window = canvas.create_window((0, 0), window=content, anchor="nw", width=canvas.winfo_reqwidth())
            
            # Configure the canvas to resize with the window and update scrollregion
            def configure_canvas(event):
                canvas.itemconfig(canvas_window, width=event.width)
            canvas.bind("<Configure>", configure_canvas)
            
            def configure_scroll_region(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
            content.bind("<Configure>", configure_scroll_region)
            
            # Payment details
            ttk.Label(content, text="Payment Details", font=("Arial", 16, "bold")).pack(anchor=W, pady=(0, 15))
            
            # Display invoice info with clearer formatting
            info_frame = ttk.Frame(content)
            info_frame.pack(fill=X, pady=(0, 15))
            
            total = invoice['total']
            paid = invoice['paid'] 
            balance = invoice['balance']
            
            # Use grid with proper padding for better spacing
            ttk.Label(info_frame, text="Invoice #:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=W, pady=5, padx=(0,10))
            ttk.Label(info_frame, text=f"{invoice_id}", font=("Arial", 12)).grid(row=0, column=1, sticky=W, pady=5)
            
            ttk.Label(info_frame, text="Total Amount:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky=W, pady=5, padx=(0,10))
            ttk.Label(info_frame, text=f"${total:.2f}", font=("Arial", 12)).grid(row=1, column=1, sticky=W, pady=5)
            
            ttk.Label(info_frame, text="Previous Payment:", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=W, pady=5, padx=(0,10))
            ttk.Label(info_frame, text=f"${paid:.2f}", font=("Arial", 12)).grid(row=2, column=1, sticky=W, pady=5)
            
            ttk.Label(info_frame, text="Balance Due:", font=("Arial", 12, "bold")).grid(row=3, column=0, sticky=W, pady=5, padx=(0,10))
            ttk.Label(info_frame, text=f"${balance:.2f}", font=("Arial", 12, "bold")).grid(row=3, column=1, sticky=W, pady=5)
            
            # Payment form with improved layout
            form_frame = ttk.LabelFrame(content, text="Payment Information", padding=15)
            form_frame.pack(fill=X, pady=(0, 15))
            
            # Configure form grid columns
            form_frame.grid_columnconfigure(0, weight=0, minsize=150)  # Fixed width for labels
            form_frame.grid_columnconfigure(1, weight=1)  # Stretch the input fields
            
            ttk.Label(form_frame, text="Payment Amount:", font=("Arial", 12)).grid(row=0, column=0, sticky=W, pady=10, padx=5)
            amount_var = StringVar(value=f"{balance:.2f}")
            amount_entry = ttk.Entry(form_frame, textvariable=amount_var, font=("Arial", 12), width=20)
            amount_entry.grid(row=0, column=1, sticky=W+E, pady=10, padx=5)
            amount_entry.focus_set()  # Set focus on amount entry
            
            ttk.Label(form_frame, text="Payment Method:", font=("Arial", 12)).grid(row=1, column=0, sticky=W, pady=10, padx=5)
            method_var = StringVar(value="Cash")
            method_combo = ttk.Combobox(form_frame, textvariable=method_var, values=["Cash", "Card", "Transfer", "Check"], 
                                       font=("Arial", 12), width=20, state="readonly")
            method_combo.grid(row=1, column=1, sticky=W+E, pady=10, padx=5)
            
            # Add progress indicator with better visibility
            progress_var = StringVar(value="")
            progress_frame = ttk.Frame(content)
            progress_frame.pack(fill=X, pady=(5, 15))
            progress_label = ttk.Label(progress_frame, textvariable=progress_var, font=("Arial", 12))
            progress_label.pack(side=LEFT)
            
            # Buttons with better layout and more space
            button_frame = ttk.Frame(content)
            button_frame.pack(fill=X, pady=(10, 0))
            
            def save_payment():
                try:
                    # Validate payment amount
                    try:
                        payment_amount = float(amount_var.get())
                        if payment_amount <= 0:
                            raise ValueError("Payment amount must be greater than zero")
                        if payment_amount > balance:
                            if not messagebox.askyesno("Confirm Overpayment", 
                                "The payment amount exceeds the balance due. Do you want to continue?", 
                                parent=dialog):
                                return
                    except ValueError:
                        messagebox.showerror("Invalid Amount", "Please enter a valid payment amount", parent=dialog)
                        return
                    
                    # Get payment method and notes
                    payment_method = method_var.get()
                    
                    # Disable buttons to prevent double submission
                    save_btn.config(state="disabled")
                    cancel_btn.config(state="disabled")
                    
                    # Show progress
                    progress_var.set("Processing payment...")
                    
                    # Define what happens after payment is processed
                    def on_payment_complete(result):
                        if isinstance(result, Exception):
                            # Re-enable buttons on error
                            save_btn.config(state="normal")
                            cancel_btn.config(state="normal")
                            
                            # Clear progress
                            progress_var.set("")
                            
                            # Show error
                            messagebox.showerror("Error", 
                                               f"Failed to record payment: {str(result)}", 
                                               parent=dialog)
                        else:
                            # Payment successful
                            # Show success message
                            messagebox.showinfo("Payment Recorded", 
                                               f"Payment of ${payment_amount:.2f} has been recorded.", 
                                               parent=dialog)
                            
                            # Cancel the background task timer before destroying the dialog
                            nonlocal process_results_id
                            if process_results_id:
                                dialog.after_cancel(process_results_id)
                                process_results_id = None
                            
                            # Close dialog and refresh
                            dialog.destroy()
                            self._refresh_debits()
                    
                    # Process payment in background thread
                    # The result will be handled by the background task timer set up in this dialog
                    from modules.utils import run_in_background
                    run_in_background(
                        record_debit_payment,
                        invoice_id=invoice_id, 
                        payment_amount=payment_amount, 
                        payment_method=payment_method,
                        on_complete=on_payment_complete,
                        on_error=lambda e: on_payment_complete(e)
                    )
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to process payment: {str(e)}", parent=dialog)
            
            save_btn = ttk.Button(button_frame, text="Process Payment", bootstyle="success", padding=(15, 8), command=save_payment)
            save_btn.pack(side=LEFT, padx=5)
            
            cancel_btn = ttk.Button(button_frame, text="Cancel", bootstyle="secondary", padding=(15, 8), command=dialog.destroy)
            cancel_btn.pack(side=RIGHT, padx=5)
            
            # Bind Enter key to save_payment function
            dialog.bind("<Return>", lambda event: save_payment())
        
        # Load invoice details in background
        from modules.utils import run_in_background
        run_in_background(
            get_invoice_details,
            on_complete=on_invoice_loaded,
            on_error=lambda e: messagebox.showerror("Error", f"Failed to load invoice: {str(e)}")
        )

    def _update_financial_dashboard(self):
        """Update the financial dashboard if it's open"""
        try:
            # Check if financial dashboard is open
            for widget in self.controller.master.winfo_children():
                if widget.winfo_class() == 'Toplevel' and hasattr(widget, 'title') and 'Financial Dashboard' in widget.title():
                    # Find the month selector and refresh button
                    for child in widget.winfo_children():
                        if child.winfo_class() == 'TFrame':
                            for grandchild in child.winfo_children():
                                if grandchild.winfo_class() == 'TFrame':
                                    for button in grandchild.winfo_children():
                                        if button.winfo_class() == 'TButton' and button.cget('text') == 'Refresh':
                                            button.invoke()  # Click the refresh button
                                            return
        except Exception as e:
            logger.error(f"Error updating financial dashboard: {str(e)}")
            # Don't show error to user, just log it

    def _make_payment_from_details(self, invoice_id, parent_dialog):
        """Process payment from the invoice details dialog"""
        # Get the reference to any process_results_id in the parent dialog
        process_results_id = getattr(parent_dialog, "process_results_id", None)
        
        # Cancel any background task processing timer if it exists
        if process_results_id:
            parent_dialog.after_cancel(process_results_id)
            
        # Close the parent dialog
        parent_dialog.destroy()
        
        # Open the payment dialog
        self._make_payment(invoice_id)

    def _print_invoice(self, invoice_id):
        """Print the invoice"""
        logger.info(f"Printing invoice #{invoice_id}")
        
        # Show a message that printing is not implemented
        messagebox.showinfo("Print", f"Printing invoice #{invoice_id} (Not implemented in this version)")
        
        # In a real application, this would generate a PDF or send to a printer

    def _refresh_debits(self, **filters):
        """
        Central method to refresh debits with optional filtering.
        This replaces both _load and _apply_filter methods.
        
        Args:
            **filters: Optional filters to apply (name_filter, phone_filter, date_filter, status_filter)
        """
        try:
            # Get debits from data access layer
            debits, statistics = get_debits(**filters)
            
            # Add debits to the treeview
            self._populate_treeview(debits)
            
            # Update statistics
            self._update_stats(statistics)
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Error loading debits: {e}")
            logger.error(f"Error loading debits: {e}")
    
    def _populate_treeview(self, debits):
        """
        Populate the treeview with debits data.
        
        Args:
            debits: List of debit dictionaries from get_debits function
        """
        # Disable treeview updates while inserting - significant performance improvement
        self.debits_tree.config(displaycolumns=[])
        
        # Clear existing data first
        for item in self.debits_tree.get_children():
            self.debits_tree.delete(item)
        
        # Prepare all rows first
        for debit in debits:
            # Format amounts with dollar sign
            total_fmt = f"${debit['Amount']:.2f}"
            paid_fmt = f"${debit['AmountPaid']:.2f}"
            balance_fmt = f"${debit['Balance']:.2f}"
            
            # Insert into treeview with tag for status color
            item_id = self.debits_tree.insert(
                "", "end", 
                values=(
                    debit['InvoiceID'], 
                    debit['Name'], 
                    debit['Phone'], 
                    debit['DateTime'], 
                    total_fmt, 
                    paid_fmt, 
                    debit['Status'], 
                    balance_fmt
                ),
                tags=(debit['Status'].lower(),)
            )
        
        # Re-enable treeview updates after all insertions complete
        self.debits_tree.config(displaycolumns=self.debits_tree["columns"])
        
    def _update_stats(self, statistics):
        """Update the statistics display"""
        total_amount = statistics.get('total_amount', 0)
        pending_amount = statistics.get('pending_amount', 0)
        paid_amount = statistics.get('paid_amount', 0)
        
        # Store the values first for use by the translation method
        self.total_debits_var.set(f"Total Amount: ${total_amount:.2f}")
        self.pending_debits_var.set(f"Pending: ${pending_amount:.2f}")
        self.paid_debits_var.set(f"Paid: ${paid_amount:.2f}")
        
        # Now update with properly translated text
        self._update_stats_text()


# ──────────────────────────────────────────────────────────────────────────────
#  Stand‑alone test harness
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    class _DummyCtrl:
        def show_frame(self, name):
            print("Switch to", name)

    root = ttk.Window(themename="darkly"); root.title("Debits Page Test")
    page = DebitsPage(root, _DummyCtrl()); page.pack(fill=BOTH, expand=True)
    root.mainloop()


