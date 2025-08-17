"""
Professional Business-Focused Inventory Management System

Complete professional inventory page with:
1. Category-based organization with sidebar navigation
2. Detailed product table with comprehensive information
3. Professional product editing and management
4. Critical loss recording system for financial tracking
5. Professional business design without space-wasting icons
6. Advanced search and filtering capabilities
7. Real-time statistics and business intelligence
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import (
    BOTH, END, CENTER, W, E, X, Y, LEFT, RIGHT, TOP, BOTTOM,
    HORIZONTAL, VERTICAL, messagebox, StringVar, BooleanVar, 
    IntVar, DoubleVar, Toplevel, Frame as TkFrame
)
import datetime
import logging

# Import from our enhanced modules
from modules.enhanced_data_access import enhanced_data, PagedResult
from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry
from modules.db_manager import ConnectionContext
from modules.data_access import invalidate_cache

# Import internationalization support
from modules.i18n import _, tr, register_refresh_callback, unregister_refresh_callback, set_widget_direction

# Configure logger
logger = logging.getLogger(__name__)

class ProductDialog:
    """Professional product add/edit dialog"""
    
    def __init__(self, parent, product_data=None):
        self.parent = parent
        self.product_data = product_data
        self.result = None
        self.dialog = None
        
    def show(self):
        """Show the professional product dialog"""
        self.dialog = Toplevel(self.parent)
        self.dialog.title("Add Product" if not self.product_data else "Edit Product")
        self.dialog.geometry("500x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Professional styling
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = "Add New Product" if not self.product_data else "Edit Product Details"
        ttk.Label(main_frame, text=title, font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))
        
        # Form fields
        self._create_form_fields(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
        
        # Populate fields if editing
        if self.product_data:
            self._populate_fields()
        
        # Focus on first field
        self.name_entry.focus()
        
        # Wait for dialog result
        self.dialog.wait_window()
        return self.result
    
    def _create_form_fields(self, parent):
        """Create professional form fields"""
        # Form frame with professional styling
        form_frame = ttk.LabelFrame(parent, text="Product Information", padding=20)
        form_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # Product Name
        ttk.Label(form_frame, text="Product Name *", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.name_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=40)
        self.name_entry.pack(fill=X, pady=(0, 15))
        
        # Category
        ttk.Label(form_frame, text="Category", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.category_combo = ttk.Combobox(form_frame, font=("Segoe UI", 11), width=37, state="normal")
        self._load_categories()
        self.category_combo.pack(fill=X, pady=(0, 15))
        
        # Price fields in a row
        price_frame = ttk.Frame(form_frame)
        price_frame.pack(fill=X, pady=(0, 15))
        
        # Buy Price
        buy_frame = ttk.Frame(price_frame)
        buy_frame.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        ttk.Label(buy_frame, text="Buy Price", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.buy_price_entry = ttk.Entry(buy_frame, font=("Segoe UI", 11))
        self.buy_price_entry.pack(fill=X)
        
        # Sell Price
        sell_frame = ttk.Frame(price_frame)
        sell_frame.pack(side=RIGHT, fill=X, expand=True)
        ttk.Label(sell_frame, text="Sell Price", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.sell_price_entry = ttk.Entry(sell_frame, font=("Segoe UI", 11))
        self.sell_price_entry.pack(fill=X)
        
        # Stock and Barcode in a row
        stock_frame = ttk.Frame(form_frame)
        stock_frame.pack(fill=X, pady=(0, 15))
        
        # Stock
        stock_left = ttk.Frame(stock_frame)
        stock_left.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        ttk.Label(stock_left, text="Stock Quantity", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.stock_entry = ttk.Entry(stock_left, font=("Segoe UI", 11))
        self.stock_entry.pack(fill=X)
        
        # Barcode
        barcode_right = ttk.Frame(stock_frame)
        barcode_right.pack(side=RIGHT, fill=X, expand=True)
        ttk.Label(barcode_right, text="Barcode (Optional)", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.barcode_entry = ttk.Entry(barcode_right, font=("Segoe UI", 11))
        self.barcode_entry.pack(fill=X)
        
    def _create_buttons(self, parent):
        """Create professional dialog buttons"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=X, pady=(10, 0))
        
        # Cancel button
        ttk.Button(buttons_frame, text="Cancel", bootstyle="secondary", 
                  command=self._cancel).pack(side=RIGHT, padx=(10, 0))
        
        # Save button
        save_text = "Add Product" if not self.product_data else "Save Changes"
        ttk.Button(buttons_frame, text=save_text, bootstyle="primary",
                  command=self._save).pack(side=RIGHT)
    
    def _load_categories(self):
        """Load categories for dropdown"""
        try:
            categories = enhanced_data.get_categories()
            category_names = [cat.get('name', str(cat)) for cat in categories]
            self.category_combo['values'] = category_names
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            self.category_combo['values'] = ['General', 'Electronics', 'Clothing', 'Food']
    
    def _populate_fields(self):
        """Populate fields when editing"""
        if not self.product_data:
            return
            
        self.name_entry.insert(0, str(self.product_data.get('name', '')))
        self.category_combo.set(str(self.product_data.get('category', '')))
        self.buy_price_entry.insert(0, str(self.product_data.get('buy_price', '0.00')))
        self.sell_price_entry.insert(0, str(self.product_data.get('sell_price', '0.00')))
        self.stock_entry.insert(0, str(self.product_data.get('stock', '0')))
        self.barcode_entry.insert(0, str(self.product_data.get('barcode', '')))
    
    def _save(self):
        """Save product data with validation"""
        # Validate required fields
        if not self.name_entry.get().strip():
            messagebox.showerror("Error", "Product name is required!")
            self.name_entry.focus()
            return
        
        try:
            buy_price = float(self.buy_price_entry.get() or 0)
            sell_price = float(self.sell_price_entry.get() or 0)
            stock = int(self.stock_entry.get() or 0)
            
            if buy_price < 0 or sell_price < 0:
                messagebox.showerror("Error", "Prices cannot be negative!")
                return
                
            if stock < 0:
                messagebox.showerror("Error", "Stock cannot be negative!")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for prices and stock!")
            return
        
        # Prepare result
        self.result = {
            'name': self.name_entry.get().strip(),
            'category': self.category_combo.get().strip(),
            'buy_price': buy_price,
            'sell_price': sell_price,
            'stock': stock,
            'barcode': self.barcode_entry.get().strip()
        }
        
        if self.product_data:
            self.result['id'] = self.product_data['id']
        
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel dialog"""
        self.dialog.destroy()

class LossRecordDialog:
    """Professional loss recording dialog for financial tracking"""
    
    def __init__(self, parent, product_data):
        self.parent = parent
        self.product_data = product_data
        self.result = None
        self.dialog = None
    
    def show(self):
        """Show the professional loss recording dialog"""
        self.dialog = Toplevel(self.parent)
        self.dialog.title("Record Product Loss")
        self.dialog.geometry("500x550")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Title with warning
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(title_frame, text="⚠️ Record Product Loss", 
                 font=("Segoe UI", 16, "bold"), foreground="#e74c3c").pack()
        
        # Product info
        self._create_product_info(main_frame)
        
        # Loss details
        self._create_loss_form(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
        
        # Focus on quantity
        self.quantity_entry.focus()
        
        # Wait for result
        self.dialog.wait_window()
        return self.result
    
    def _create_product_info(self, parent):
        """Display current product information"""
        info_frame = ttk.LabelFrame(parent, text="Product Information", padding=15)
        info_frame.pack(fill=X, pady=(0, 20))
        
        # Product details
        ttk.Label(info_frame, text=f"Product: {self.product_data['name']}", 
                 font=("Segoe UI", 12, "bold")).pack(anchor=W, pady=2)
        ttk.Label(info_frame, text=f"Category: {self.product_data.get('category', 'N/A')}", 
                 font=("Segoe UI", 11)).pack(anchor=W, pady=2)
        ttk.Label(info_frame, text=f"Current Stock: {self.product_data.get('stock', 0)} units", 
                 font=("Segoe UI", 11)).pack(anchor=W, pady=2)
        ttk.Label(info_frame, text=f"Unit Value: ${self.product_data.get('sell_price', 0):.2f}", 
                 font=("Segoe UI", 11)).pack(anchor=W, pady=2)
    
    def _create_loss_form(self, parent):
        """Create loss recording form"""
        form_frame = ttk.LabelFrame(parent, text="Loss Details", padding=15)
        form_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # Quantity lost
        ttk.Label(form_frame, text="Quantity Lost *", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.quantity_entry = ttk.Entry(form_frame, font=("Segoe UI", 11))
        self.quantity_entry.pack(fill=X, pady=(0, 15))
        
        # Loss reason
        ttk.Label(form_frame, text="Reason for Loss *", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.reason_combo = ttk.Combobox(form_frame, font=("Segoe UI", 11), state="readonly")
        self.reason_combo['values'] = [
            "💔 Damaged", "⏰ Expired", "🚨 Theft", 
            "🥀 Spoilage", "💥 Breakage", "❓ Other"
        ]
        self.reason_combo.pack(fill=X, pady=(0, 15))
        
        # Additional notes
        ttk.Label(form_frame, text="Additional Notes", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(0, 5))
        self.notes_text = ttk.Text(form_frame, height=4, font=("Segoe UI", 10))
        self.notes_text.pack(fill=X, pady=(0, 15))
        
        # Impact preview
        self.impact_label = ttk.Label(form_frame, text="", font=("Segoe UI", 10, "italic"))
        self.impact_label.pack(anchor=W)
        
        # Bind quantity change to update impact
        self.quantity_entry.bind('<KeyRelease>', self._update_impact_preview)
    
    def _create_buttons(self, parent):
        """Create dialog buttons"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=X)
        
        ttk.Button(buttons_frame, text="Cancel", bootstyle="secondary",
                  command=self._cancel).pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(buttons_frame, text="Record Loss", bootstyle="danger",
                  command=self._record_loss).pack(side=RIGHT)
    
    def _update_impact_preview(self, event=None):
        """Update impact preview as user types"""
        try:
            quantity = int(self.quantity_entry.get() or 0)
            current_stock = int(self.product_data.get('stock', 0))
            unit_value = float(self.product_data.get('sell_price', 0))
            
            if quantity > 0:
                new_stock = max(0, current_stock - quantity)
                total_loss_value = quantity * unit_value
                
                self.impact_label.config(
                    text=f"Impact: Stock will change from {current_stock} to {new_stock} units. "
                         f"Financial loss: ${total_loss_value:.2f}",
                    foreground="#e74c3c"
                )
            else:
                self.impact_label.config(text="")
        except ValueError:
            self.impact_label.config(text="")
    
    def _record_loss(self):
        """Record the loss with validation"""
        # Validation
        try:
            quantity = int(self.quantity_entry.get() or 0)
            if quantity <= 0:
                messagebox.showerror("Error", "Quantity lost must be greater than 0!")
                return
            
            current_stock = int(self.product_data.get('stock', 0))
            if quantity > current_stock:
                if not messagebox.askyesno("Confirm", 
                    f"Loss quantity ({quantity}) exceeds current stock ({current_stock}). "
                    "This will set stock to 0. Continue?"):
                    return
                    
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity!")
            return
        
        if not self.reason_combo.get():
            messagebox.showerror("Error", "Please select a reason for the loss!")
            return
        
        # Final confirmation
        if not messagebox.askyesno("Confirm Loss Recording",
            f"Are you sure you want to record a loss of {quantity} units?\n"
            "This action affects financial reporting and cannot be undone."):
            return
        
        # Prepare result
        self.result = {
            'product_id': self.product_data['id'],
            'quantity_lost': quantity,
            'reason': self.reason_combo.get(),
            'notes': self.notes_text.get('1.0', END).strip(),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel dialog"""
        self.dialog.destroy()

class EnhancedInventoryPage(ttk.Frame):
    """
    Modern Professional Inventory Management System - 2025 Style
    Implements all UI/UX suggestions for enhanced user experience
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        
        # Enhanced data access
        from modules.enhanced_data_access import EnhancedDataAccess
        global enhanced_data
        enhanced_data = EnhancedDataAccess()
        
        # Modern UI variables
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="All Categories")
        self.sort_var = tk.StringVar(value="Name ↑")
        self.theme_var = tk.StringVar(value="🌙 Dark")
        self.current_filter = "all"
        self.current_sort = "name"
        self.current_category_filter = "all"
        self.is_dark_theme = True
        
        # Data storage
        self.products_data = []
        self.categories_data = []
        self.filtered_products = []
        self.selected_product = None
        
        # Dashboard stats
        self.stats = {
            'total_products': 0,
            'low_stock_count': 0,
            'out_of_stock_count': 0,
            'total_value': 0.0,
            'avg_price': 0.0,
            'top_category': 'Unknown',
            'categories_count': 0
        }
        
        # Modern 2025 color scheme
        self.colors = {
            'background': '#2B2B2B',
            'card': '#383838',
            'sidebar': '#1F1F1F',
            'header': '#2D2D2D',
            'text': '#FFFFFF',
            'secondary_text': '#CCCCCC',
            'accent': '#888888',
            'primary': '#4285F4',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'danger': '#F44336',
            'info': '#2196F3',
            'border': '#555555',
            'hover': '#4A4A4A'
        }
        
        # Setup enhanced UI
        self._setup_modern_styles()
        self._create_modern_ui()
        self._load_data()
        
        # Register for internationalization
        register_refresh_callback(self._retranslate)
    def _setup_modern_styles(self):
        """Setup modern 2025 styles with rounded corners and shadows"""
        style = ttk.Style()
        
        # Modern frame styles
        style.configure("Modern.TFrame", background=self.colors['background'], relief="flat")
        style.configure("Card.TFrame", background=self.colors['card'], relief="solid", borderwidth=1)
        style.configure("Header.TFrame", background=self.colors['header'], relief="flat")
        style.configure("Sidebar.TFrame", background=self.colors['sidebar'], relief="flat")
        
        # Modern button styles with hover effects
        style.configure("ModernPrimary.TButton", background=self.colors['primary'], foreground="white", borderwidth=0, focuscolor='none')
        style.configure("ModernSuccess.TButton", background=self.colors['success'], foreground="white", borderwidth=0, focuscolor='none')
        style.configure("ModernWarning.TButton", background=self.colors['warning'], foreground="white", borderwidth=0, focuscolor='none')
        style.configure("ModernDanger.TButton", background=self.colors['danger'], foreground="white", borderwidth=0, focuscolor='none')
        style.configure("ModernInfo.TButton", background=self.colors['info'], foreground="white", borderwidth=0, focuscolor='none')
        
        # Modern entry and combobox styles
        style.configure("Modern.TEntry", fieldbackground=self.colors['card'], borderwidth=1, relief="solid", insertcolor=self.colors['text'])
        style.configure("Modern.TCombobox", fieldbackground=self.colors['card'], borderwidth=1, relief="solid")
        
        # Modern treeview with enhanced styling
        style.configure("Modern.Treeview", 
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['card'],
                       borderwidth=1,
                       relief="solid")
        
        style.configure("Modern.Treeview.Heading",
                       background=self.colors['header'],
                       foreground=self.colors['text'],
                       relief="solid",
                       borderwidth=1)
        
        # Configure treeview selection and hover colors
        style.map("Modern.Treeview", 
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', 'white')])
        
        # Modern scrollbar styles
        style.configure("Modern.Vertical.TScrollbar", 
                       background=self.colors['card'],
                       troughcolor=self.colors['background'],
                       borderwidth=0,
                       arrowcolor=self.colors['text'])
        
        style.configure("Modern.Horizontal.TScrollbar",
                       background=self.colors['card'],
                       troughcolor=self.colors['background'], 
                       borderwidth=0,
                       arrowcolor=self.colors['text'])
        
        # Modern label frame styles
        style.configure("ActionGroup.TLabelframe",
                       background=self.colors['background'],
                       foreground=self.colors['secondary_text'],
                       borderwidth=1,
                       relief="solid")
        
        style.configure("ActionGroup.TLabelframe.Label",
                       background=self.colors['background'],
                       foreground=self.colors['secondary_text'])

    def _create_modern_ui(self):
        """Create the complete modern 2025 UI based on all suggestions"""
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # === 1. TOP HEADER BAR (Search, Filters, Actions) ===
        self._create_top_header()
        
        # === 2. DASHBOARD CARDS (Business Intelligence) ===
        self._create_dashboard_cards()
        
        # === 3. MAIN CONTENT AREA ===
        main_container = ttk.Frame(self, style="Modern.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # === 4. CONTENT WITH COLLAPSIBLE SIDEBAR AND TABLE ===
        content_frame = ttk.Frame(main_container, style="Modern.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # === 5. COLLAPSIBLE SIDEBAR ===
        self._create_collapsible_sidebar(content_frame)
        
        # === 6. ENHANCED MAIN TABLE AREA ===
        self._create_enhanced_table_area(content_frame)
        
        # === 7. GROUPED ACTION BUTTONS ===
        self._create_grouped_actions()

    def _create_top_header(self):
        """Create modern top header with back button, search, and theme toggle"""
        header_frame = ttk.Frame(self, style="Header.TFrame", padding=15)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Left section: Back button and title
        left_section = ttk.Frame(header_frame, style="Header.TFrame")
        left_section.pack(side=tk.LEFT, fill=tk.Y)
        
        # Modern back button with icon
        back_btn = ttk.Button(
            left_section,
            text="← Back to Menu",
            bootstyle="info-outline",
            padding=(15, 10),
            command=self._go_back_to_menu
        )
        back_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # Modern title with icon
        title_container = ttk.Frame(left_section, style="Header.TFrame")
        title_container.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = tk.Label(
            title_container,
            text="📦 Professional Inventory Management",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['header'],
            fg=self.colors['text']
        )
        title_label.pack(side=tk.LEFT, pady=5)
        
        # Status indicator with modern styling
        self.status_indicator = tk.Label(
            title_container,
            text="● Ready",
            font=("Segoe UI", 12),
            bg=self.colors['header'],
            fg=self.colors['success']
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(20, 0), pady=5)
        
        # Right section: Search and filters
        right_section = ttk.Frame(header_frame, style="Header.TFrame")
        right_section.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create modern search container
        search_container = ttk.Frame(right_section, style="Card.TFrame", padding=5)
        search_container.pack(side=tk.RIGHT, padx=(0, 15))
        
        # Search icon and entry with modern styling
        search_icon = tk.Label(
            search_container,
            text="🔍",
            font=("Segoe UI", 14),
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        search_icon.pack(side=tk.LEFT, padx=(5, 5))
        
        self.search_entry = ttk.Entry(
            search_container,
            textvariable=self.search_var,
            font=("Segoe UI", 12),
            width=25,
            style="Modern.TEntry"
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Modern filter controls
        filters_frame = ttk.Frame(right_section, style="Header.TFrame")
        filters_frame.pack(side=tk.RIGHT, padx=(0, 15))
        
        # Category filter with label
        category_label = tk.Label(
            filters_frame,
            text="Category:",
            font=("Segoe UI", 10),
            bg=self.colors['header'],
            fg=self.colors['secondary_text']
        )
        category_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.category_combo = ttk.Combobox(
            filters_frame,
            textvariable=self.category_var,
            font=("Segoe UI", 10),
            width=15,
            state="readonly",
            style="Modern.TCombobox"
        )
        self.category_combo.grid(row=0, column=1, padx=(0, 15))
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_change)
        
        # Sort filter with label
        sort_label = tk.Label(
            filters_frame,
            text="Sort:",
            font=("Segoe UI", 10),
            bg=self.colors['header'],
            fg=self.colors['secondary_text']
        )
        sort_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        
        self.sort_combo = ttk.Combobox(
            filters_frame,
            textvariable=self.sort_var,
            values=["Name ↑", "Name ↓", "Stock ↑", "Stock ↓", "Price ↑", "Price ↓", "Category ↑"],
            font=("Segoe UI", 10),
            width=12,
            state="readonly",
            style="Modern.TCombobox"
        )
        self.sort_combo.grid(row=0, column=3)
        self.sort_combo.bind('<<ComboboxSelected>>', self._on_sort_change)

    def _create_dashboard_cards(self):
        """Create modern dashboard cards with business intelligence"""
        cards_frame = ttk.Frame(self, style="Modern.TFrame", padding=15)
        cards_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Cards container with responsive grid
        cards_container = ttk.Frame(cards_frame, style="Modern.TFrame")
        cards_container.pack(fill=tk.X)
        
        # Configure responsive columns
        for i in range(4):
            cards_container.columnconfigure(i, weight=1, uniform="card")
        
        # Modern dashboard cards with icons and colors
        self.card_widgets = {}
        card_data = [
            ("📦", "Total Products", "total_products", self.colors['primary'], self._show_all_products),
            ("⚠️", "Low Stock", "low_stock_count", self.colors['warning'], self._show_low_stock),
            ("📉", "Out of Stock", "out_of_stock_count", self.colors['danger'], self._show_out_of_stock),
            ("💰", "Total Value", "total_value", self.colors['success'], self._show_high_value),
        ]
        
        for i, (icon, title, stat_key, color, command) in enumerate(card_data):
            card = self._create_dashboard_card(cards_container, icon, title, stat_key, color, command)
            card.grid(row=0, column=i, padx=8, pady=5, sticky="ew")
            self.card_widgets[stat_key] = card

    def _create_dashboard_card(self, parent, icon, title, stat_key, color, command):
        """Create a single modern dashboard card with hover effects"""
        # Create card frame with modern styling
        card_frame = tk.Frame(parent, bg=self.colors['card'], relief="solid", bd=1, cursor="hand2")
        
        # Add hover effects
        def on_enter(e):
            card_frame.config(bg=self.colors['hover'])
        def on_leave(e):
            card_frame.config(bg=self.colors['card'])
        def on_click(e):
            command()
            
        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
        card_frame.bind("<Button-1>", on_click)
        
        # Card content with proper padding
        content_frame = tk.Frame(card_frame, bg=self.colors['card'], padx=20, pady=15)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top row: Icon and value
        top_frame = tk.Frame(content_frame, bg=self.colors['card'])
        top_frame.pack(fill=tk.X)
        
        # Icon
        icon_label = tk.Label(
            top_frame,
            text=icon,
            font=("Segoe UI", 24),
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        icon_label.pack(side=tk.LEFT)
        
        # Value (will be updated dynamically)
        value_label = tk.Label(
            top_frame,
            text="0",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['card'],
            fg=color
        )
        value_label.pack(side=tk.RIGHT)
        
        # Title
        title_label = tk.Label(
            content_frame,
            text=title,
            font=("Segoe UI", 11),
            bg=self.colors['card'],
            fg=self.colors['secondary_text']
        )
        title_label.pack(pady=(10, 0))
        
        # Store references for updates
        card_frame.value_label = value_label
        card_frame.title_label = title_label
        card_frame.stat_key = stat_key
        card_frame.content_frame = content_frame
        
        # Bind click event to all child widgets too
        for widget in [content_frame, top_frame, icon_label, value_label, title_label]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        return card_frame

    def _create_collapsible_sidebar(self, parent):
        """Create modern collapsible sidebar with icons and enhanced organization"""
        # Sidebar container with collapse functionality
        self.sidebar_frame = ttk.Frame(parent, style="Sidebar.TFrame")
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        # Sidebar header 
        sidebar_header = tk.Frame(self.sidebar_frame, bg=self.colors['sidebar'], height=50)
        sidebar_header.pack(fill=tk.X, pady=(0, 10))
        sidebar_header.pack_propagate(False)
        
        # Sidebar title
        sidebar_title = tk.Label(
            sidebar_header,
            text="Navigation",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['sidebar'],
            fg=self.colors['text']
        )
        sidebar_title.pack(side=tk.LEFT, padx=(10, 0), pady=10)
        
        # Sidebar content container
        self.sidebar_content = tk.Frame(self.sidebar_frame, bg=self.colors['sidebar'])
        self.sidebar_content.pack(fill=tk.BOTH, expand=True)
        
        # Categories section
        self._create_categories_section()
        
        # Quick actions section  
        self._create_quick_actions_section()

    def _create_categories_section(self):
        """Create modern categories section with icons and badges"""
        # Categories header
        categories_header = tk.Frame(self.sidebar_content, bg=self.colors['sidebar'], height=40)
        categories_header.pack(fill=tk.X, pady=(10, 5))
        categories_header.pack_propagate(False)
        
        tk.Label(
            categories_header,
            text="📂 Categories",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['sidebar'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT, padx=15, pady=10)
        
        # Categories container
        self.categories_container = tk.Frame(self.sidebar_content, bg=self.colors['sidebar'])
        self.categories_container.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        # All Categories button
        all_btn = self._create_sidebar_button("📋 All Categories", lambda: self._filter_by_category("all"), True)
        all_btn.pack(fill=tk.X, pady=2)
        
        # Dynamic category buttons (will be populated in _update_categories)
        self.category_buttons = []

    def _create_quick_actions_section(self):
        """Create modern quick actions section"""
        # Quick actions header
        actions_header = tk.Frame(self.sidebar_content, bg=self.colors['sidebar'], height=40)
        actions_header.pack(fill=tk.X, pady=(20, 5))
        actions_header.pack_propagate(False)
        
        tk.Label(
            actions_header,
            text="⚡ Quick Actions",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['sidebar'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT, padx=15, pady=10)
        
        # Actions container
        actions_container = tk.Frame(self.sidebar_content, bg=self.colors['sidebar'])
        actions_container.pack(fill=tk.X, padx=10)
        
        # Quick action buttons with modern styling
        quick_actions = [
            ("➕ Add Product", self._add_product, self.colors['success']),
            ("📁 Add Category", self._add_category, self.colors['primary']),  # New Add Category button
            ("📦 Import Data", self._import_products, self.colors['info']),
            ("📊 Analytics", self._show_analytics, self.colors['warning']),
            ("🔄 Refresh", self._refresh_data, self.colors['accent'])
        ]
        
        for text, command, color in quick_actions:
            btn = self._create_action_button(actions_container, text, command, color)
            btn.pack(fill=tk.X, pady=3)

    def _create_sidebar_button(self, text, command, is_active=False):
        """Create a modern sidebar button with hover effects"""
        bg_color = self.colors['primary'] if is_active else self.colors['sidebar']
        
        btn = tk.Button(
            self.categories_container,
            text=text,
            font=("Segoe UI", 10),
            bg=bg_color,
            fg=self.colors['text'],
            bd=0,
            cursor="hand2",
            command=command,
            anchor="w",
            padx=15,
            pady=8
        )
        
        # Hover effects
        def on_enter(e):
            if not is_active:
                btn.config(bg=self.colors['hover'])
        def on_leave(e):
            if not is_active:
                btn.config(bg=self.colors['sidebar'])
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def _create_action_button(self, parent, text, command, color):
        """Create a modern action button with color coding"""
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10),
            bg=color,
            fg="white",
            bd=0,
            cursor="hand2",
            command=command,
            pady=8
        )
        
        # Hover effects
        def on_enter(e):
            btn.config(bg=self._lighten_color(color))
        def on_leave(e):
            btn.config(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def _create_enhanced_table_area(self, parent):
        """Create the enhanced main table area with modern styling and features"""
        table_container = ttk.Frame(parent, style="Modern.TFrame")
        table_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Table header with modern styling
        table_header = tk.Frame(table_container, bg=self.colors['header'], height=60)
        table_header.pack(fill=tk.X, padx=10, pady=(0, 10))
        table_header.pack_propagate(False)
        
        # Left: Table title and info
        left_header = tk.Frame(table_header, bg=self.colors['header'])
        left_header.pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        tk.Label(
            left_header,
            text="📋 Product Inventory Details",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['header'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT, pady=15)
        
        # Right: Table info and controls
        right_header = tk.Frame(table_header, bg=self.colors['header'])
        right_header.pack(side=tk.RIGHT, fill=tk.Y, padx=15)
        
        # Product count and selection info
        info_container = tk.Frame(right_header, bg=self.colors['header'])
        info_container.pack(side=tk.RIGHT, pady=15)
        
        self.selection_info = tk.Label(
            info_container,
            text="No selection",
            font=("Segoe UI", 10),
            bg=self.colors['header'],
            fg=self.colors['secondary_text']
        )
        self.selection_info.pack(side=tk.RIGHT, padx=(15, 0))
        
        self.count_info = tk.Label(
            info_container,
            text="Showing 0 of 0 products",
            font=("Segoe UI", 10),
            bg=self.colors['header'],
            fg=self.colors['secondary_text']
        )
        self.count_info.pack(side=tk.RIGHT)
        
        # Enhanced table with improved row height and styling
        table_frame = ttk.Frame(table_container, style="Modern.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Configure modern treeview with all suggested improvements
        columns = ("ID", "Product Name", "Category", "Buy Price", "Sell Price", 
                  "Stock", "Total Value", "Status", "Margin %", "Barcode")
        
        self.products_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Modern.Treeview",
            height=15
        )
        
        # Configure columns with improved width and alignment
        column_config = {
            "ID": {"width": 60, "anchor": tk.CENTER},
            "Product Name": {"width": 200, "anchor": tk.W},  # Left aligned for readability
            "Category": {"width": 120, "anchor": tk.CENTER},
            "Buy Price": {"width": 100, "anchor": tk.E},     # Right aligned for money
            "Sell Price": {"width": 100, "anchor": tk.E},    # Right aligned for money
            "Stock": {"width": 80, "anchor": tk.CENTER},
            "Total Value": {"width": 120, "anchor": tk.E},   # Right aligned for money
            "Status": {"width": 120, "anchor": tk.CENTER},
            "Margin %": {"width": 90, "anchor": tk.CENTER},
            "Barcode": {"width": 120, "anchor": tk.CENTER}
        }
        
        # Configure each column with modern styling
        for col, config in column_config.items():
            self.products_tree.heading(col, text=col, anchor=tk.CENTER)
            self.products_tree.column(col, 
                                    width=config["width"], 
                                    minwidth=60, 
                                    anchor=config["anchor"])
        
        # Enhanced scrollbars with modern styling
        v_scrollbar = ttk.Scrollbar(
            table_frame, 
            orient=tk.VERTICAL, 
            command=self.products_tree.yview, 
            style="Modern.Vertical.TScrollbar"
        )
        h_scrollbar = ttk.Scrollbar(
            table_frame, 
            orient=tk.HORIZONTAL, 
            command=self.products_tree.xview, 
            style="Modern.Horizontal.TScrollbar"
        )
        
        self.products_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout with proper expansion
        self.products_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights for responsiveness
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Enhanced event bindings
        self.products_tree.bind('<<TreeviewSelect>>', self._on_product_select)
        self.products_tree.bind('<Double-1>', self._on_product_double_click)
        self.products_tree.bind('<Button-3>', self._show_context_menu)  # Right-click menu
        
        # Configure modern row styling with color coding
        self._configure_tree_styling()

    def _configure_tree_styling(self):
        """Configure modern tree styling with color coding"""
        # Configure alternating row colors for better readability
        self.products_tree.tag_configure('evenrow', background=self.colors['card'])
        self.products_tree.tag_configure('oddrow', background=self.colors['background'])
        
        # Status-based color coding with modern colors
        self.products_tree.tag_configure('out_of_stock', 
                                        background='#ffebee', 
                                        foreground='#c62828')
        self.products_tree.tag_configure('low_stock', 
                                        background='#fff8e1', 
                                        foreground='#f57f17')
        self.products_tree.tag_configure('in_stock', 
                                        background=self.colors['card'], 
                                        foreground=self.colors['text'])
        self.products_tree.tag_configure('high_value', 
                                        background='#e8f5e8', 
                                        foreground='#2e7d32')

    def _create_grouped_actions(self):
        """Create modern grouped action buttons with improved organization"""
        actions_container = tk.Frame(self, bg=self.colors['background'], height=120)
        actions_container.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        actions_container.pack_propagate(False)
        
        # Create three modern action groups as suggested
        self._create_action_group(actions_container, "Product Actions", 
                                [("➕ Add Product", self._add_product, self.colors['success']),
                                 ("✏️ Edit Product", self._edit_product, self.colors['primary']),
                                 ("📄 Duplicate", self._duplicate_product, self.colors['info']),
                                 ("🗑️ Delete", self._delete_product, self.colors['danger'])], 
                                tk.LEFT)
        
        self._create_action_group(actions_container, "Inventory Management",
                                [("📉 Record Loss", self._record_loss, self.colors['warning']),
                                 ("📦 Adjust Stock", self._adjust_stock, self.colors['info']),
                                 ("💵 Update Prices", self._bulk_price_update, self.colors['accent'])],
                                tk.LEFT)
        
        self._create_action_group(actions_container, "Data & Analytics",
                                [("📈 Analytics", self._show_analytics, self.colors['info']),
                                 ("⬆️ Export Data", self._export_data, self.colors['accent']),
                                 ("🔄 Refresh Data", self._refresh_data, self.colors['accent'])],
                                tk.RIGHT)
        
        # Modern status bar
        self._create_status_bar(actions_container)

    def _create_action_group(self, parent, title, actions, side):
        """Create a modern action group with labeled frame"""
        group_frame = tk.Frame(parent, bg=self.colors['card'], relief="solid", bd=1)
        group_frame.pack(side=side, fill=tk.Y, padx=10, pady=10)
        
        # Group title
        title_frame = tk.Frame(group_frame, bg=self.colors['card'], height=25)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text=title,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['card'],
            fg=self.colors['secondary_text']
        ).pack(pady=5)
        
        # Action buttons container
        buttons_frame = tk.Frame(group_frame, bg=self.colors['card'])
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        # Create action buttons with modern styling
        for i, (text, command, color) in enumerate(actions):
            btn = tk.Button(
                buttons_frame,
                text=text,
                font=("Segoe UI", 9),
                bg=color,
                fg="white",
                bd=0,
                cursor="hand2",
                command=command,
                pady=6,
                padx=12
            )
            btn.grid(row=0, column=i, padx=3, pady=2, sticky="ew")
            
            # Modern hover effects
            def make_hover(button, original_color):
                def on_enter(e):
                    button.config(bg=self._lighten_color(original_color))
                def on_leave(e):
                    button.config(bg=original_color)
                return on_enter, on_leave
            
            enter_func, leave_func = make_hover(btn, color)
            btn.bind("<Enter>", enter_func)
            btn.bind("<Leave>", leave_func)
        
        # Configure button column weights
        for i in range(len(actions)):
            buttons_frame.columnconfigure(i, weight=1)

    def _create_status_bar(self, parent):
        """Create modern status bar with real-time information"""
        status_frame = tk.Frame(parent, bg=self.colors['background'], height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # Left: Selection and operation status
        self.status_text = tk.Label(
            status_frame,
            text="Select a product for details",
            font=("Segoe UI", 10),
            bg=self.colors['background'],
            fg=self.colors['secondary_text']
        )
        self.status_text.pack(side=tk.LEFT, padx=15, pady=5)
        
        # Right: Last updated timestamp
        self.timestamp_label = tk.Label(
            status_frame,
            text="",
            font=("Segoe UI", 10),
            bg=self.colors['background'],
            fg=self.colors['accent']
        )
        self.timestamp_label.pack(side=tk.RIGHT, padx=15, pady=5)

    # === MODERN UI UTILITY METHODS ===
    
    def _lighten_color(self, color):
        """Lighten a color for hover effects"""
        # Simple color lightening for hover effects
        color_map = {
            self.colors['primary']: '#5A9BF5',
            self.colors['success']: '#6CBF60',
            self.colors['warning']: '#FFB64D',
            self.colors['danger']: '#F66B6B',
            self.colors['info']: '#4FC3F7',
            self.colors['accent']: '#A8A8A8'
        }
        return color_map.get(color, '#6A6A6A')
    
    def _go_back_to_menu(self):
        """Navigate back to main menu"""
        self.controller.show_frame("MainMenuPage")

    # === DATA LOADING AND MANAGEMENT ===
    
    def _load_data(self):
        """Load products data with modern error handling and status updates"""
        try:
            self.status_indicator.config(text="● Loading...", fg=self.colors['warning'])
            self.update_idletasks()
            
            # Load products using the fixed enhanced data access
            self.products_data = enhanced_data.get_products()
            self.categories_data = enhanced_data.get_categories()
            
            # Update all UI components
            self._update_dashboard_stats()
            self._update_categories_dropdown()
            self._update_categories_sidebar()
            self._update_products_display()
            
            self.status_indicator.config(text="● Ready", fg=self.colors['success'])
            self.timestamp_label.config(text=f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error loading inventory data: {e}")
            self.status_indicator.config(text="● Error", fg=self.colors['danger'])
            self.status_text.config(text=f"Error loading data: {str(e)}")

    def _update_dashboard_stats(self):
        """Update modern dashboard cards with current statistics"""
        if not self.products_data:
            return
        
        # Calculate comprehensive statistics
        total_products = len(self.products_data)
        low_stock = sum(1 for p in self.products_data 
                       if 0 < int(p.get('stock', 0)) <= 5)
        out_of_stock = sum(1 for p in self.products_data 
                          if int(p.get('stock', 0)) == 0)
        
        total_value = sum(
            float(p.get('sell_price', 0)) * int(p.get('stock', 0)) 
            for p in self.products_data
        )
        
        # Update card values with proper formatting
        stats_mapping = {
            'total_products': str(total_products),
            'low_stock_count': str(low_stock),
            'out_of_stock_count': str(out_of_stock),
            'total_value': f"${total_value:,.2f}"
        }
        
        for stat_key, value in stats_mapping.items():
            if stat_key in self.card_widgets:
                card = self.card_widgets[stat_key]
                card.value_label.config(text=value)

    def _update_categories_dropdown(self):
        """Update category dropdown with current categories"""
        category_names = ["All Categories"] + [cat.get('name', str(cat)) for cat in self.categories_data]
        self.category_combo['values'] = category_names
        if not self.category_var.get() or self.category_var.get() not in category_names:
            self.category_var.set("All Categories")

    def _update_categories_sidebar(self):
        """Update sidebar categories with modern styling and badges"""
        # Clear existing category buttons
        for btn in getattr(self, 'category_buttons', []):
            btn.destroy()
        self.category_buttons = []
        
        # Add category buttons with product counts
        for category in self.categories_data:
            name = category.get('name', str(category))
            count = sum(1 for p in self.products_data if p.get('category') == name)
            
            btn_text = f"🧃 {name} ({count})" if name == "Juice" else f"📁 {name} ({count})"
            btn = self._create_sidebar_button(btn_text, lambda n=name: self._filter_by_category(n))
            btn.pack(fill=tk.X, pady=2)
            self.category_buttons.append(btn)

    def _update_products_display(self):
        """Update products table with enhanced styling and modern features"""
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Apply current filters
        self._apply_current_filters()
        
        # Populate table with enhanced styling
        for i, product in enumerate(self.filtered_products):
            # Calculate enhanced values
            buy_price = float(product.get('buy_price', 0))
            sell_price = float(product.get('sell_price', 0))
            stock = int(product.get('stock', 0))
            total_value = sell_price * stock
            
            # Calculate margin percentage
            margin_text = f"{((sell_price - buy_price) / buy_price) * 100:.1f}%" if buy_price > 0 else "N/A"
            
            # Enhanced status with modern indicators
            if stock == 0:
                status = "❌ Out of Stock"
                tag = 'out_of_stock'
            elif stock <= 5:
                status = "⚠️ Low Stock"  
                tag = 'low_stock'
            else:
                status = "✅ In Stock"
                tag = 'in_stock'
            
            # Prepare enhanced row values
            values = (
                product.get('id', ''),
                product.get('name', ''),
                product.get('category', ''),
                f"${buy_price:.2f}",
                f"${sell_price:.2f}",
                f"{stock:,}",
                f"${total_value:,.2f}",
                status,
                margin_text,
                product.get('barcode', 'N/A') or 'N/A'
            )
            
            # Insert with alternating row colors and status tags
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            tags = (row_tag, tag)
            self.products_tree.insert('', 'end', values=values, tags=tags)
        
        # Update count information
        total_count = len(self.products_data)
        filtered_count = len(self.filtered_products)
        self.count_info.config(text=f"Showing {filtered_count} of {total_count} products")

    def _apply_current_filters(self):
        """Apply current search, category, and sort filters"""
        # Start with all products
        filtered = list(self.products_data)
        
        # Apply search filter
        search_term = self.search_var.get().lower().strip()
        if search_term:
            filtered = [p for p in filtered 
                       if search_term in p.get('name', '').lower() or 
                          search_term in p.get('category', '').lower() or
                          search_term in str(p.get('barcode', '')).lower()]
        
        # Apply category filter
        if self.current_category_filter != "all":
            filtered = [p for p in filtered if p.get('category') == self.current_category_filter]
        
        # Apply status filter
        if self.current_filter == "low_stock":
            filtered = [p for p in filtered if 0 < int(p.get('stock', 0)) <= 5]
        elif self.current_filter == "out_of_stock":
            filtered = [p for p in filtered if int(p.get('stock', 0)) == 0]
        elif self.current_filter == "high_value":
            if filtered:
                avg_value = sum(float(p.get('sell_price', 0)) for p in filtered) / len(filtered)
                filtered = [p for p in filtered if float(p.get('sell_price', 0)) > avg_value]
        
        # Apply sorting
        sort_option = self.sort_var.get()
        if sort_option == "Name ↑":
            filtered.sort(key=lambda p: p.get('name', '').lower())
        elif sort_option == "Name ↓":
            filtered.sort(key=lambda p: p.get('name', '').lower(), reverse=True)
        elif sort_option == "Stock ↑":
            filtered.sort(key=lambda p: int(p.get('stock', 0)))
        elif sort_option == "Stock ↓":
            filtered.sort(key=lambda p: int(p.get('stock', 0)), reverse=True)
        elif sort_option == "Price ↑":
            filtered.sort(key=lambda p: float(p.get('sell_price', 0)))
        elif sort_option == "Price ↓":
            filtered.sort(key=lambda p: float(p.get('sell_price', 0)), reverse=True)
        elif sort_option == "Category ↑":
            filtered.sort(key=lambda p: p.get('category', ''))
        
        self.filtered_products = filtered

    # === EVENT HANDLERS ===
    
    def _on_search_change(self, *args):
        """Handle search input changes"""
        self._update_products_display()
    
    def _on_category_change(self, event=None):
        """Handle category filter changes"""
        selected = self.category_var.get()
        self.current_category_filter = "all" if selected == "All Categories" else selected
        self._update_products_display()
    
    def _on_sort_change(self, event=None):
        """Handle sort option changes"""
        self._update_products_display()
    
    def _on_product_select(self, event):
        """Handle product selection in table"""
        selection = self.products_tree.selection()
        if selection:
            item = self.products_tree.item(selection[0])
            product_name = item['values'][1] if len(item['values']) > 1 else "Unknown"
            self.selection_info.config(text=f"Selected: {product_name}")
            self.status_text.config(text=f"Selected product: {product_name}")
        else:
            self.selection_info.config(text="No selection")
            self.status_text.config(text="Select a product for details")
    
    def _on_product_double_click(self, event):
        """Handle double-click on product (edit)"""
        self._edit_product()
    
    def _show_context_menu(self, event):
        """Show right-click context menu"""
        # This could be implemented for advanced users
        pass
    
    # === FILTER ACTIONS (Dashboard Cards) ===
    
    def _show_all_products(self):
        """Show all products (reset filters)"""
        self.current_filter = "all"
        self.current_category_filter = "all"
        self.category_var.set("All Categories")
        self.search_var.set("")
        self._update_products_display()
    
    def _show_low_stock(self):
        """Filter to show only low stock products"""
        self.current_filter = "low_stock"
        self._update_products_display()
    
    def _show_out_of_stock(self):
        """Filter to show only out of stock products"""
        self.current_filter = "out_of_stock" 
        self._update_products_display()
    
    def _show_high_value(self):
        """Filter to show high value products"""
        self.current_filter = "high_value"
        self._update_products_display()
    
    def _filter_by_category(self, category_name):
        """Filter products by category"""
        self.current_category_filter = category_name
        if category_name == "all":
            self.category_var.set("All Categories")
        else:
            self.category_var.set(category_name)
        self._update_products_display()

    # === ACTION METHODS ===
    
    def _add_product(self):
        """Add new product with modern dialog"""
        try:
            dialog = ProductDialog(self)
            result = dialog.show()
            if result:
                # Add product to database
                enhanced_data.add_product(result)
                self._load_data()  # Refresh data
                self.status_text.config(text="Product added successfully")
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            messagebox.showerror("Error", f"Failed to add product: {str(e)}")
    
    def _add_category(self):
        """Add new category with modern dialog"""
        try:
            from tkinter.simpledialog import askstring
            
            # Simple dialog to get category name
            category_name = askstring(
                "Add New Category", 
                "Enter category name:",
                parent=self
            )
            
            if category_name and category_name.strip():
                category_name = category_name.strip()
                
                # Check if category already exists
                existing_categories = [cat.get('name', '') for cat in self.categories_data]
                if category_name in existing_categories:
                    messagebox.showwarning(
                        "Category Exists", 
                        f"Category '{category_name}' already exists.",
                        parent=self
                    )
                    return
                
                # Add category to database (pass just the name string)
                success = enhanced_data.add_category(category_name)
                
                if success:
                    # Refresh data to show new category
                    self._load_data()
                    
                    # Show success message
                    messagebox.showinfo(
                        "Success", 
                        f"Category '{category_name}' added successfully!",
                        parent=self
                    )
                    
                    self.status_indicator.config(text="● Category added", fg=self.colors['success'])
                else:
                    messagebox.showerror(
                        "Error", 
                        "Failed to add category to database.",
                        parent=self
                    )
                
        except Exception as e:
            logger.error(f"Error adding category: {e}")
            messagebox.showerror("Error", f"Failed to add category: {str(e)}", parent=self)
    
    def _edit_product(self):
        """Edit selected product"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a product to edit")
            return
        
        try:
            item = self.products_tree.item(selection[0])
            product_id = item['values'][0]
            
            # Find product data
            product_data = next((p for p in self.products_data if str(p.get('id')) == str(product_id)), None)
            if not product_data:
                messagebox.showerror("Error", "Product not found")
                return
            
            dialog = ProductDialog(self, product_data)
            result = dialog.show()
            if result:
                # Update product in database
                enhanced_data.update_product(product_id, result)
                self._load_data()  # Refresh data
                self.status_text.config(text="Product updated successfully")
        except Exception as e:
            logger.error(f"Error editing product: {e}")
            messagebox.showerror("Error", f"Failed to edit product: {str(e)}")
    
    def _duplicate_product(self):
        """Duplicate selected product"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a product to duplicate")
            return
        
        try:
            item = self.products_tree.item(selection[0])
            product_id = item['values'][0]
            
            # Find product data
            product_data = next((p for p in self.products_data if str(p.get('id')) == str(product_id)), None)
            if not product_data:
                messagebox.showerror("Error", "Product not found")
                return
            
            # Create copy with modified name
            duplicate_data = product_data.copy()
            duplicate_data['name'] = f"{duplicate_data['name']} (Copy)"
            duplicate_data.pop('id', None)  # Remove ID for new product
            
            dialog = ProductDialog(self, duplicate_data)
            result = dialog.show()
            if result:
                # Add duplicated product to database
                enhanced_data.add_product(result)
                self._load_data()  # Refresh data
                self.status_text.config(text="Product duplicated successfully")
        except Exception as e:
            logger.error(f"Error duplicating product: {e}")
            messagebox.showerror("Error", f"Failed to duplicate product: {str(e)}")
    
    def _delete_product(self):
        """Delete selected product with confirmation"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a product to delete")
            return
        
        try:
            item = self.products_tree.item(selection[0])
            product_name = item['values'][1]
            product_id = item['values'][0]
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Deletion", 
                                 f"Are you sure you want to delete '{product_name}'?\n\nThis action cannot be undone."):
                # Delete product from database
                enhanced_data.delete_product(product_id)
                self._load_data()  # Refresh data
                self.status_text.config(text=f"Product '{product_name}' deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            messagebox.showerror("Error", f"Failed to delete product: {str(e)}")
    
    def _record_loss(self):
        """Record product loss with modern dialog"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a product to record loss")
            return
        
        try:
            item = self.products_tree.item(selection[0])
            product_data = {
                'id': item['values'][0],
                'name': item['values'][1],
                'current_stock': int(item['values'][5].replace(',', ''))
            }
            
            dialog = LossRecordDialog(self, product_data)
            result = dialog.show()
            if result:
                # Record loss in database
                enhanced_data.record_loss(result)
                self._load_data()  # Refresh data
                self.status_text.config(text="Loss recorded successfully")
        except Exception as e:
            logger.error(f"Error recording loss: {e}")
            messagebox.showerror("Error", f"Failed to record loss: {str(e)}")
    
    def _adjust_stock(self):
        """Adjust stock for selected product"""
        messagebox.showinfo("Stock Adjustment", "Stock adjustment feature coming soon!")
    
    def _bulk_price_update(self):
        """Update prices for multiple products"""
        messagebox.showinfo("Bulk Update", "Bulk price update feature coming soon!")
    
    def _show_analytics(self):
        """Show detailed analytics"""
        messagebox.showinfo("Analytics", "Advanced analytics feature coming soon!")
    
    def _import_products(self):
        """Import products from file"""
        messagebox.showinfo("Import", "Product import feature coming soon!")
    
    def _export_data(self):
        """Export inventory data"""
        messagebox.showinfo("Export", "Data export feature coming soon!")
    
    def _refresh_data(self):
        """Refresh all data"""
        self.status_text.config(text="Refreshing data...")
        self._load_data()

    def _retranslate(self):
        """Handle language changes"""
        # Placeholder for internationalization
        pass

    def refresh(self):
        """Refresh the entire page"""
        self._load_data()

# End of EnhancedInventoryPage class
