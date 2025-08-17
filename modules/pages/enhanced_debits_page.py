"""
Enhanced Debits Page with optimized performance

This is a performance-optimized version of the debits page that uses:
1. Paginated data loading to prevent UI freezing
2. Background processing for all database operations
3. Debounced search for better responsiveness
4. Better progress indicators for long operations
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import (
    BOTH, END, CENTER, W, E, X, Y, LEFT, RIGHT, TOP,
    HORIZONTAL, BOTTOM, messagebox, StringVar, BooleanVar,
    IntVar, DoubleVar
)
import datetime
import logging
from decimal import Decimal
import time

# Import from our enhanced modules
from modules.enhanced_data_access import enhanced_data, PagedResult
from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry
from modules.db_manager import ConnectionContext
from modules.data_access import invalidate_cache

# Import internationalization support
from modules.i18n import _, register_refresh_callback, unregister_refresh_callback, set_widget_direction

# Configure logger
logger = logging.getLogger(__name__)

class EnhancedDebitsPage(ttk.Frame):
    """
    Enhanced debits page with optimized performance.
    Uses pagination and background processing to prevent UI freezing.
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        
        # Store active background tasks
        self._active_tasks = {}
        
        # Create text variables
        self._create_variables()
          # Create UI components
        self._create_ui()
        
        # Register for language updates
        register_refresh_callback(self._refresh_language)
        
        # RTL/LTR language support
        set_widget_direction(self)
    
    def _create_variables(self):
        """Initialize all variables used in the UI"""
        # Header text
        self.title_var = StringVar(value=_("Manage Debits"))
        self.back_btn_var = StringVar(value=_("Back to Home"))
        
        # Search text
        self.search_label_var = StringVar(value=_("Search Debits:"))
        self.search_var = StringVar()
        self.clear_btn_var = StringVar(value=_("Clear"))
        
        # Filter text
        self.filter_label_var = StringVar(value=_("Filter:"))
        self.filter_all_var = StringVar(value=_("All"))
        self.filter_unpaid_var = StringVar(value=_("Unpaid"))
        self.filter_paid_var = StringVar(value=_("Paid"))
        
        # Stats text
        self.total_debits_var = StringVar(value=_("Total Debits: $0.00"))
        self.unpaid_debits_var = StringVar(value=_("Unpaid: $0.00"))
        
        # Initialize statistics attributes
        self.total_debits = 0
        self.unpaid_debits = 0
        
        # Button text
        self.add_debit_var = StringVar(value=_("Add Debit"))
        self.mark_paid_var = StringVar(value=_("Mark as Paid"))
        self.edit_debit_var = StringVar(value=_("Edit"))
        self.delete_debit_var = StringVar(value=_("Delete"))
        self.refresh_var = StringVar(value=_("Refresh"))
        
    def _create_ui(self):
        """Create the main UI components with modern 2025 design"""
        # Main container with modern styling
        main_container = ttk.Frame(self, style="Card.TFrame")
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # Modern header with gradient-like appearance
        self._create_modern_header(main_container)
        
        # Dashboard statistics panel
        self._create_dashboard_stats(main_container)
        
        # Search and filter section with modern design
        self._create_search_filters(main_container)
        
        # Main content area with debits management
        self._create_debits_management(main_container)
        
        # Bottom action bar
        self._create_action_bar(main_container)
        
    def _create_modern_header(self, parent):
        """Create modern header with title and navigation"""
        header_frame = ttk.Frame(parent, style="Primary.TFrame")
        header_frame.pack(fill=X, pady=(0, 20))
        
        # Title with modern styling
        title_container = ttk.Frame(header_frame)
        title_container.pack(fill=X, padx=20, pady=15)
        
        # Main title with icon
        title_section = ttk.Frame(title_container)
        title_section.pack(side=LEFT)
        
        ttk.Label(
            title_section,
            text="💳",
            font=("Segoe UI", 24)
        ).pack(side=LEFT, padx=(0, 10))
        
        self.title_label = ttk.Label(
            title_section,
            textvariable=self.title_var,
            font=("Segoe UI", 24, "bold"),
            foreground="#2C3E50"
        )
        self.title_label.pack(side=LEFT)
        
        # Navigation and actions
        nav_frame = ttk.Frame(title_container)
        nav_frame.pack(side=RIGHT)
        
        # Quick action buttons
        ttk.Button(
            nav_frame,
            text=_("📊 Reports"),
            command=self._view_reports,
            bootstyle="outline-info",
            style="Modern.TButton"
        ).pack(side=RIGHT, padx=(10, 0))
        
        self.back_button = ttk.Button(
            nav_frame,
            textvariable=self.back_btn_var,
            command=self._on_back_clicked,
            bootstyle="outline-primary",
            style="Modern.TButton"
        )
        self.back_button.pack(side=RIGHT, padx=(10, 0))
        
    def _create_dashboard_stats(self, parent):
        """Create modern dashboard with key statistics"""
        dashboard_frame = ttk.Frame(parent, style="Secondary.TFrame")
        dashboard_frame.pack(fill=X, padx=10, pady=(0, 20))
        
        # Stats cards container
        cards_container = ttk.Frame(dashboard_frame)
        cards_container.pack(fill=X, padx=20, pady=15)
        
        # Total Debits Card
        total_card = ttk.Frame(cards_container, style="Info.TFrame")
        total_card.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        
        ttk.Label(
            total_card,
            text="💰",
            font=("Segoe UI", 20)
        ).pack(pady=(10, 5))
        
        ttk.Label(
            total_card,
            text=_("Total Debits"),
            font=("Segoe UI", 10, "bold"),
            foreground="#34495E"
        ).pack()
        
        self.total_debits_label = ttk.Label(
            total_card,
            textvariable=self.total_debits_var,
            font=("Segoe UI", 16, "bold"),
            foreground="#27AE60"
        )
        self.total_debits_label.pack(pady=(0, 10))
        
        # Unpaid Debits Card
        unpaid_card = ttk.Frame(cards_container, style="Warning.TFrame")
        unpaid_card.pack(side=LEFT, fill=X, expand=True, padx=(5, 5))
        
        ttk.Label(
            unpaid_card,
            text="⚠️",
            font=("Segoe UI", 20)
        ).pack(pady=(10, 5))
        
        ttk.Label(
            unpaid_card,
            text=_("Unpaid Amount"),
            font=("Segoe UI", 10, "bold"),
            foreground="#34495E"
        ).pack()
        
        self.unpaid_debits_label = ttk.Label(
            unpaid_card,
            textvariable=self.unpaid_debits_var,
            font=("Segoe UI", 16, "bold"),
            foreground="#E74C3C"
        )
        self.unpaid_debits_label.pack(pady=(0, 10))
        
        # Customer Count Card
        customers_card = ttk.Frame(cards_container, style="Success.TFrame")
        customers_card.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
        ttk.Label(
            customers_card,
            text="👥",
            font=("Segoe UI", 20)
        ).pack(pady=(10, 5))
        
        ttk.Label(
            customers_card,
            text=_("Active Customers"),
            font=("Segoe UI", 10, "bold"),
            foreground="#34495E"
        ).pack()
        
        self.customers_count_var = StringVar(value="0")
        ttk.Label(
            customers_card,
            textvariable=self.customers_count_var,
            font=("Segoe UI", 16, "bold"),
            foreground="#3498DB"
        ).pack(pady=(0, 10))
        
    def _create_search_filters(self, parent):
        """Create modern search and filter section"""
        search_frame = ttk.LabelFrame(
            parent,
            text=_("🔍 Search & Filter"),
            style="Modern.TLabelframe"
        )
        search_frame.pack(fill=X, padx=10, pady=(0, 15))
        
        content_frame = ttk.Frame(search_frame)
        content_frame.pack(fill=X, padx=15, pady=15)
        
        # Top row - Search bar
        search_row = ttk.Frame(content_frame)
        search_row.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            search_row,
            textvariable=self.search_label_var,
            font=("Segoe UI", 11, "bold")
        ).pack(side=LEFT, padx=(0, 10))
        
        # Enhanced search with autocomplete
        self.search_entry = FastSearchEntry(
            search_row,
            search_function=self._perform_debit_search,
            on_select_callback=self._on_debit_selected,
            placeholder=_("Search by customer name, amount, or date...")
        )
        self.search_entry.get_frame().pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        
        ttk.Button(
            search_row,
            textvariable=self.clear_btn_var,
            command=self._clear_search,
            bootstyle="outline-secondary",
            style="Small.TButton"
        ).pack(side=RIGHT)
        
        # Bottom row - Filter options
        filter_row = ttk.Frame(content_frame)
        filter_row.pack(fill=X)
        
        ttk.Label(
            filter_row,
            textvariable=self.filter_label_var,
            font=("Segoe UI", 11, "bold")
        ).pack(side=LEFT, padx=(0, 15))
        
        # Modern filter buttons
        self.filter_var = StringVar(value="all")
        
        filter_buttons = ttk.Frame(filter_row)
        filter_buttons.pack(side=LEFT)
        
        ttk.Radiobutton(
            filter_buttons,
            text=_("All"),
            variable=self.filter_var,
            value="all",
            command=self._apply_filter
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            filter_buttons,
            text=_("Unpaid"),
            variable=self.filter_var,
            value="unpaid",
            command=self._apply_filter
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            filter_buttons,
            text=_("Paid"),
            variable=self.filter_var,
            value="paid",
            command=self._apply_filter
        ).pack(side=LEFT)
        
        # Date range filter
        date_filter = ttk.Frame(filter_row)
        date_filter.pack(side=RIGHT)
        
        ttk.Label(
            date_filter,
            text=_("Date Range:"),
            font=("Segoe UI", 10)
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            date_filter,
            text=_("Last 30 Days"),
            command=lambda: self._filter_by_date(30),
            bootstyle="outline-info",
            style="Small.TButton"
        ).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(
            date_filter,
            text=_("This Month"),
            command=self._filter_current_month,
            bootstyle="outline-info",
            style="Small.TButton"
        ).pack(side=LEFT)
        
    def _create_debits_management(self, parent):
        """Create modern debits list with management features"""
        management_frame = ttk.LabelFrame(
            parent,
            text=_("💳 Debits Management"),
            style="Modern.TLabelframe"
        )
        management_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 15))
        
        # Toolbar
        toolbar = ttk.Frame(management_frame)
        toolbar.pack(fill=X, padx=15, pady=(15, 0))
        
        # Left toolbar - View options
        view_options = ttk.Frame(toolbar)
        view_options.pack(side=LEFT)
        
        ttk.Label(
            view_options,
            text=_("View:"),
            font=("Segoe UI", 10)
        ).pack(side=LEFT, padx=(0, 10))
        
        self.view_mode = StringVar(value="detailed")
        
        ttk.Radiobutton(
            view_options,
            text=_("Detailed"),
            variable=self.view_mode,
            value="detailed",
            command=self._change_view_mode
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            view_options,
            text=_("Summary"),
            variable=self.view_mode,
            value="summary",
            command=self._change_view_mode
        ).pack(side=LEFT)
        
        # Right toolbar - Quick actions
        quick_actions = ttk.Frame(toolbar)
        quick_actions.pack(side=RIGHT)
        
        ttk.Button(
            quick_actions,
            text=_("📊 Export"),
            command=self._export_debits,
            bootstyle="outline-info",
            style="Small.TButton"
        ).pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(
            quick_actions,
            text=_("🔄 Refresh"),
            command=self.refresh,
            bootstyle="outline-secondary",
            style="Small.TButton"
        ).pack(side=RIGHT)
        
        # Debits list with pagination
        list_container = ttk.Frame(management_frame)
        list_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        self.debits_list = PaginatedListView(
            list_container,
            columns=["id", "customer", "amount", "date", "due_date", "status", "notes"],
            headers={
                "id": _("ID"),
                "customer": _("Customer"),
                "amount": _("Amount"),
                "date": _("Date"),
                "due_date": _("Due Date"),
                "status": _("Status"),
                "notes": _("Notes")
            },
            widths={
                "id": 60,
                "customer": 150,
                "amount": 100,
                "date": 100,
                "due_date": 100,
                "status": 80,
                "notes": 200
            },
            on_page_change=self._load_debits,
            on_select=self._on_debit_selected,
            on_double_click=self._edit_selected_debit,
            page_size=15,
            height=12,
            style="Modern.Treeview"
        )
        self.debits_list.pack(fill=BOTH, expand=True)
        
    def _create_action_bar(self, parent):
        """Create modern action bar with primary actions"""
        action_frame = ttk.Frame(parent, style="Primary.TFrame")
        action_frame.pack(fill=X, pady=(10, 0))
        
        # Left side - Primary actions
        primary_actions = ttk.Frame(action_frame)
        primary_actions.pack(side=LEFT, padx=15, pady=10)
        
        ttk.Button(
            primary_actions,
            textvariable=self.add_debit_var,
            command=self._add_new_debit,
            bootstyle="success",
            style="Action.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            primary_actions,
            textvariable=self.mark_paid_var,
            command=self._mark_as_paid,
            bootstyle="warning",
            style="Action.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        # Center - Selection actions
        selection_actions = ttk.Frame(action_frame)
        selection_actions.pack(side=LEFT, expand=True)
        
        ttk.Button(
            selection_actions,
            textvariable=self.edit_debit_var,
            command=self._edit_selected_debit,
            bootstyle="primary",
            style="Modern.TButton"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(
            selection_actions,
            textvariable=self.delete_debit_var,
            command=self._delete_selected_debit,
            bootstyle="danger",
            style="Modern.TButton"
        ).pack(side=LEFT)
        
        # Right side - Utility actions
        utility_actions = ttk.Frame(action_frame)
        utility_actions.pack(side=RIGHT, padx=15, pady=10)
        
        ttk.Button(
            utility_actions,
            text=_("📧 Send Reminders"),
            command=self._send_reminders,
            bootstyle="info",
            style="Modern.TButton"
        ).pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(
            utility_actions,
            text=_("📋 Payment Plans"),
            command=self._manage_payment_plans,
            bootstyle="secondary",
            style="Modern.TButton"        ).pack(side=RIGHT)
    
    # ===== HELPER METHODS =====
    
    # ===== HELPER METHODS =====
    
    def prepare_for_display(self):
        """Prepare the page before displaying - load initial data"""
        self._load_debits()
        self._load_statistics()
    
    def refresh(self):
        """Refresh the page data"""
        self._refresh_language()
        self._load_debits()
        self._load_statistics()
    
    def _refresh_language(self):
        """Update all text elements with current language"""
        # Update UI direction
        set_widget_direction(self)
        
        # Update all text variables with translated strings
        self.title_var.set(_("Manage Debits"))
        self.back_btn_var.set(_("Back to Home"))
        self.search_label_var.set(_("Search Debits:"))
        self.clear_btn_var.set(_("Clear"))
        self.filter_label_var.set(_("Filter:"))
        self.filter_all_var.set(_("All"))
        self.filter_unpaid_var.set(_("Unpaid"))
        self.filter_paid_var.set(_("Paid"))
        self.add_debit_var.set(_("Add Debit"))
        self.mark_paid_var.set(_("Mark as Paid"))
        self.edit_debit_var.set(_("Edit"))
        self.delete_debit_var.set(_("Delete"))
        self.refresh_var.set(_("Refresh"))
        
        # Update list headers
        self.debits_list.update_headers({
            "id": _("ID"),
            "customer": _("Customer"),
            "amount": _("Amount"),
            "date": _("Date"),
            "paid": _("Status"),
            "notes": _("Notes")
        })
        
        # Update statistics
        self._update_statistics_display()
    
    def _load_debits(self, page=1, search_term=""):
        """Load debits with pagination and filters"""
        # Use the search term from the entry if not provided
        if search_term == "":
            search_term = self.search_var.get()
        
        # Get current filter
        filter_value = self.filter_var.get()        # Show progress during load
        progress = ProgressDialog(
            self,
            title=_("Loading Debits")
        )
        
        # Callback for when data is loaded
        def on_debits_loaded(result):
            if isinstance(result, PagedResult):
                # Transform data for display
                data = []
                for item in result.data:  # Use .data instead of .items
                    # Format the paid status
                    paid_status = _("Paid") if item.get("Paid") else _("Unpaid")
                    
                    data.append({
                        "id": item["DebitID"],
                        "customer": item["CustomerName"],
                        "amount": f"${float(item['Amount']):.2f}",
                        "date": item["Date"],
                        "paid": paid_status,
                        "notes": item.get("Notes", ""),
                        # Store original data
                        "raw_data": item
                    })
                
                # Calculate total_pages from total_count and page_size
                total_pages = max(1, (result.total_count + result.page_size - 1) // result.page_size)
                
                # Update the list view
                self.debits_list.update_items(
                    data,
                    result.total_count,  # Use .total_count instead of .total_items
                    result.current_page,  # Use .current_page instead of .page
                    total_pages  # Calculate total_pages
                )
            
            # Close progress dialog
            progress.close()
        
        # Error callback
        def on_error(error):
            logger.error(f"Error loading debits: {str(error)}")
            messagebox.showerror(
                _("Error"),
                _("Failed to load debits: {0}").format(str(error))
            )
            progress.close()
        
        # Load data in background
        enhanced_data.run_in_background(
            "load_debits",
            enhanced_data.get_debits_paged,
            on_success=on_debits_loaded,
            on_error=on_error,
            page=page,
            page_size=self.debits_list.page_size,
            search_term=search_term,
            filter_paid=(
                None if filter_value == "all" 
                else (filter_value == "paid")
            )
        )
    
    def _load_statistics(self):
        """Load debit statistics (totals, unpaid amounts)"""
        # Get statistics in background
        enhanced_data.get_debit_statistics(
            on_success=self._update_statistics,
            on_error=lambda err: logger.error(f"Error loading statistics: {str(err)}")
        )
    
    def _update_statistics(self, stats):
        """Update statistics from loaded data"""
        if stats:
            self.total_debits = stats.get("total_debits", 0)
            self.unpaid_debits = stats.get("unpaid_debits", 0)
            self._update_statistics_display()
    
    def _update_statistics_display(self):
        """Update the statistics display with current values"""
        self.total_debits_var.set(
            _("Total Debits: ${0:.2f}").format(self.total_debits or 0)        )
        self.unpaid_debits_var.set(
            _("Unpaid: ${0:.2f}").format(self.unpaid_debits or 0)
        )
    
    def _on_search_changed(self, search_term):
        """Handle search changes - debounced by FastSearchEntry"""
        self._load_debits(1, search_term)
    
    def _clear_search(self):
        """Clear the search entry"""
        self.search_var.set("")
        self._load_debits(1, "")
    
    def _apply_filter(self):
        """Apply the selected filter"""
        self._load_debits()
    
    def _perform_debit_search(self, search_term):
        """Search debits for FastSearchEntry - returns list of results"""
        if not search_term or len(search_term.strip()) < 2:
            return []
        
        try:
            # Use enhanced data access for search
            result = enhanced_data.search_debits(search_term.strip())
            if hasattr(result, 'data'):
                # Format results for FastSearchEntry
                formatted_results = []
                for item in result.data:
                    status = _("Paid") if item.get('paid', False) else _("Unpaid")
                    formatted_results.append({
                        'id': item.get('id', ''),
                        'display': f"{item.get('customer_name', '')} - ${item.get('amount', 0):.2f} ({status})",
                        'debit': item
                    })
                return formatted_results
        except Exception as e:
            logger.error(f"Error searching debits: {str(e)}")
        
        return []
    
    def _on_debit_selected(self, result):
        """Handle debit selection from FastSearchEntry"""
        if result and 'debit' in result:
            debit = result['debit']
            # Auto-select in the list if possible
            # For now, just refresh the list to show the search results
            self._refresh_data()
    
    def _on_debit_selected(self, item_data):
        """Handle debit selection"""
        if item_data and "raw_data" in item_data:
            debit_data = item_data["raw_data"]
            self.selected_debit = debit_data
            
            # Enable action buttons
            self.edit_button.configure(state="normal")
            self.delete_button.configure(state="normal")
            
            # Only enable mark paid button if debit is unpaid
            if not debit_data.get("Paid"):
                self.mark_paid_button.configure(state="normal")
            else:
                self.mark_paid_button.configure(state="disabled")
        else:
            self.selected_debit = None
            self.edit_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            self.mark_paid_button.configure(state="disabled")
    
    def _add_debit(self):
        """Show dialog to add a new debit"""
        self._show_debit_dialog()
    
    def _edit_debit(self):
        """Show dialog to edit the selected debit"""
        if not hasattr(self, "selected_debit") or not self.selected_debit:
            return
        
        self._show_debit_dialog(self.selected_debit)
    
    def _mark_as_paid(self):
        """Mark the selected debit as paid"""
        if not hasattr(self, "selected_debit") or not self.selected_debit:
            return
        
        if messagebox.askyesno(
            _("Confirm"),
            _("Mark this debit as paid?")
        ):            # Show progress dialog
            progress = ProgressDialog(
                self,
                title=_("Processing")
            )
            
            # Update in background
            debit_id = self.selected_debit["DebitID"]
            
            def on_complete(result):
                progress.close()
                if result and result.get("success"):
                    messagebox.showinfo(
                        _("Success"),
                        _("Debit marked as paid")
                    )
                    # Refresh data
                    self.refresh()
                else:
                    messagebox.showerror(
                        _("Error"),
                        _("Failed to update debit: {0}").format(
                            result.get("error", _("Unknown error"))
                        )
                    )
            
            def on_error(error):
                progress.close()
                messagebox.showerror(
                    _("Error"),
                    _("Failed to update debit: {0}").format(str(error))
                )
            
            # Call update function
            enhanced_data.mark_debit_as_paid(
                debit_id,
                on_success=on_complete,
                on_error=on_error
            )
    
    def _delete_debit(self):
        """Delete the selected debit"""
        if not hasattr(self, "selected_debit") or not self.selected_debit:
            return
        
        if messagebox.askyesno(
            _("Confirm Delete"),
            _("Are you sure you want to delete this debit?"),
            icon="warning"
        ):            # Show progress dialog
            progress = ProgressDialog(
                self,
                title=_("Processing")
            )
            
            # Delete in background
            debit_id = self.selected_debit["DebitID"]
            
            def on_complete(result):
                progress.close()
                if result and result.get("success"):
                    messagebox.showinfo(
                        _("Success"),
                        _("Debit deleted successfully")
                    )
                    # Refresh data
                    self.refresh()
                else:
                    messagebox.showerror(
                        _("Error"),
                        _("Failed to delete debit: {0}").format(
                            result.get("error", _("Unknown error"))
                        )
                    )
            
            def on_error(error):
                progress.close()
                messagebox.showerror(
                    _("Error"),
                    _("Failed to delete debit: {0}").format(str(error))
                )
            
            # Call delete function
            enhanced_data.delete_debit(
                debit_id,
                on_success=on_complete,
                on_error=on_error
            )
    
    def _show_debit_dialog(self, debit_data=None):
        """Show dialog to add or edit a debit"""
        # Create dialog window
        dialog = ttk.Toplevel(self)
        dialog.title(_("Add Debit") if not debit_data else _("Edit Debit"))
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Form frame
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=BOTH, expand=True)
        
        # Customer name
        ttk.Label(
            form_frame,
            text=_("Customer Name:"),
            font=("Arial", 12)
        ).grid(row=0, column=0, sticky=W, pady=5)
        
        customer_var = StringVar()
        if debit_data:
            customer_var.set(debit_data.get("CustomerName", ""))
        
        customer_entry = ttk.Entry(
            form_frame,
            textvariable=customer_var,
            width=30,
            font=("Arial", 12)
        )
        customer_entry.grid(row=0, column=1, sticky=W, pady=5)
        
        # Amount
        ttk.Label(
            form_frame,
            text=_("Amount:"),
            font=("Arial", 12)
        ).grid(row=1, column=0, sticky=W, pady=5)
        
        amount_var = StringVar()
        if debit_data:
            amount_var.set(str(debit_data.get("Amount", "")))
        
        amount_entry = ttk.Entry(
            form_frame,
            textvariable=amount_var,
            width=15,
            font=("Arial", 12)
        )
        amount_entry.grid(row=1, column=1, sticky=W, pady=5)
        
        # Date
        ttk.Label(
            form_frame,
            text=_("Date:"),
            font=("Arial", 12)
        ).grid(row=2, column=0, sticky=W, pady=5)
        
        date_var = StringVar()
        if debit_data and debit_data.get("Date"):
            date_var.set(debit_data.get("Date"))
        else:
            # Set current date as default
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            date_var.set(current_date)
        
        date_entry = ttk.Entry(
            form_frame,
            textvariable=date_var,
            width=15,
            font=("Arial", 12)
        )
        date_entry.grid(row=2, column=1, sticky=W, pady=5)
        
        # Paid status
        paid_var = BooleanVar()
        if debit_data:
            paid_var.set(debit_data.get("Paid", False))
        else:
            paid_var.set(False)
        
        paid_check = ttk.Checkbutton(
            form_frame,
            text=_("Paid"),
            variable=paid_var,
            bootstyle="round-toggle"
        )
        paid_check.grid(row=3, column=0, columnspan=2, sticky=W, pady=5)
        
        # Notes
        ttk.Label(
            form_frame,
            text=_("Notes:"),
            font=("Arial", 12)
        ).grid(row=4, column=0, sticky=W, pady=5)
        
        notes_var = StringVar()
        if debit_data:
            notes_var.set(debit_data.get("Notes", ""))
        
        notes_entry = ttk.Text(
            form_frame,
            width=40,
            height=5,
            font=("Arial", 12)
        )
        if debit_data and debit_data.get("Notes"):
            notes_entry.insert("1.0", debit_data.get("Notes"))
        notes_entry.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=5)
        
        # Button frame
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)
        
        # Save button
        save_button = ttk.Button(
            button_frame,
            text=_("Save"),
            command=lambda: self._save_debit(
                dialog,
                debit_data.get("DebitID") if debit_data else None,
                customer_var.get(),
                amount_var.get(),
                date_var.get(),
                paid_var.get(),
                notes_entry.get("1.0", "end-1c")
            ),
            bootstyle=SUCCESS,
            width=15
        )
        save_button.pack(side=LEFT, padx=5)
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text=_("Cancel"),
            command=dialog.destroy,
            bootstyle=SECONDARY,
            width=15
        )
        cancel_button.pack(side=LEFT, padx=5)
        
        # Make form expandable
        form_frame.columnconfigure(1, weight=1)
        form_frame.rowconfigure(5, weight=1)
          # Focus on first field
        customer_entry.focus_set()
    
    def _save_debit(self, dialog, debit_id, customer_name, amount_str, date_str, paid, notes):
        """Save the debit data"""
        # Validate input
        if not customer_name:
            messagebox.showerror(
                _("Error"),
                _("Please enter a customer name")
            )
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError()
        except:
            messagebox.showerror(
                _("Error"),
                _("Please enter a valid amount")
            )
            return
        
        # Show progress dialog
        progress = ProgressDialog(
            dialog,
            title=_("Processing")
        )
        
        # Prepare data
        debit_data = {
            "CustomerName": customer_name,
            "Amount": amount,
            "Date": date_str,
            "Paid": paid,
            "Notes": notes
        }
        
        if debit_id:
            debit_data["DebitID"] = debit_id
        
        def on_complete(result):
            progress.close()
            if result and result.get("success"):
                dialog.destroy()
                messagebox.showinfo(
                    _("Success"),
                    _("Debit saved successfully")
                )
                # Refresh data
                self.refresh()
            else:
                messagebox.showerror(
                    _("Error"),
                    _("Failed to save debit: {0}").format(
                        result.get("error", _("Unknown error"))
                    )
                )
        
        def on_error(error):
            progress.close()
            messagebox.showerror(
                _("Error"),
                _("Failed to save debit: {0}").format(str(error))
            )
        
        # Save data in background
        if debit_id:
            # Update existing debit
            enhanced_data.update_debit(
                debit_data,
                on_success=on_complete,
                on_error=on_error
            )
        else:
            # Add new debit
            enhanced_data.add_debit(
                debit_data,
                on_success=on_complete,
                on_error=on_error
            )
    
    # ===== MODERN ACTION METHODS =====
    
    def _view_reports(self):
        """View debits reports"""
        # TODO: Implement debits reporting
        messagebox.showinfo(_("Reports"), _("Debits reporting feature coming soon!"))
    
    def _filter_by_date(self, days):
        """Filter debits by date range"""
        # TODO: Implement date filtering
        messagebox.showinfo(_("Date Filter"), _(f"Filtering by last {days} days"))
    
    def _filter_current_month(self):
        """Filter debits for current month"""
        # TODO: Implement current month filtering
        messagebox.showinfo(_("Date Filter"), _("Filtering by current month"))
    
    def _change_view_mode(self):
        """Change between detailed and summary view"""
        mode = self.view_mode.get()
        if mode == "summary":
            # TODO: Implement summary view
            messagebox.showinfo(_("View Mode"), _("Summary view coming soon!"))
        else:
            # Already in detailed view
            pass
    
    def _export_debits(self):
        """Export debits to file"""
        # TODO: Implement export functionality
        messagebox.showinfo(_("Export"), _("Export feature coming soon!"))
    
    def _add_new_debit(self):
        """Add a new debit entry"""
        from modules.debits import DebitDialog
        
        dialog = DebitDialog(self, title=_("Add New Debit"))
        if dialog.result:
            # Refresh the list after adding
            self.refresh()
    
    def _edit_selected_debit(self):
        """Edit the selected debit"""
        if not hasattr(self, 'selected_debit') or not self.selected_debit:
            messagebox.showwarning(_("Warning"), _("Please select a debit to edit."))
            return
        
        from modules.debits import DebitDialog
        
        dialog = DebitDialog(
            self, 
            title=_("Edit Debit"),
            debit_data=self.selected_debit
        )
        if dialog.result:
            # Refresh the list after editing
            self.refresh()
    
    def _delete_selected_debit(self):
        """Delete the selected debit"""
        if not hasattr(self, 'selected_debit') or not self.selected_debit:
            messagebox.showwarning(_("Warning"), _("Please select a debit to delete."))
            return
        
        if messagebox.askyesno(
            _("Confirm Delete"),
            _("Are you sure you want to delete this debit?\nThis action cannot be undone.")
        ):
            try:
                # Delete the debit
                enhanced_data.delete_debit(self.selected_debit["DebitID"])
                messagebox.showinfo(_("Success"), _("Debit deleted successfully."))
                self.refresh()
            except Exception as e:
                logger.error(f"Error deleting debit: {str(e)}")
                messagebox.showerror(_("Error"), _("Failed to delete debit: {0}").format(str(e)))
    
    def _mark_as_paid(self):
        """Mark selected debit as paid"""
        if not hasattr(self, 'selected_debit') or not self.selected_debit:
            messagebox.showwarning(_("Warning"), _("Please select a debit to mark as paid."))
            return
        
        if self.selected_debit.get("Paid"):
            messagebox.showinfo(_("Info"), _("This debit is already marked as paid."))
            return
        
        if messagebox.askyesno(
            _("Mark as Paid"),
            _("Mark this debit as paid?\nAmount: ${0:.2f}").format(
                float(self.selected_debit.get("Amount", 0))
            )
        ):
            try:
                # Mark as paid
                enhanced_data.mark_debit_paid(self.selected_debit["DebitID"])
                messagebox.showinfo(_("Success"), _("Debit marked as paid successfully."))
                self.refresh()
            except Exception as e:
                logger.error(f"Error marking debit as paid: {str(e)}")
                messagebox.showerror(_("Error"), _("Failed to mark debit as paid: {0}").format(str(e)))
    
    def _send_reminders(self):
        """Send payment reminders to customers"""
        # TODO: Implement reminder system
        messagebox.showinfo(_("Reminders"), _("Payment reminder system coming soon!"))
    
    def _manage_payment_plans(self):
        """Manage payment plans for customers"""
        # TODO: Implement payment plans
        messagebox.showinfo(_("Payment Plans"), _("Payment plans feature coming soon!"))
    
    # ===== EVENT HANDLERS =====
    
    def _on_back_clicked(self):
        """Handle back button click"""
        self.controller.show_frame("StartPage")
