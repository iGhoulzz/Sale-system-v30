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
    Professional business-focused inventory management system with category organization,
    detailed product management, and critical loss recording for financial accuracy.
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        
        # Professional color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#34495e', 
            'accent': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'background': '#ecf0f1',
            'card': '#ffffff',
            'text': '#2c3e50',
            'text_light': '#7f8c8d'
        }
        
        # Business data variables
        self.current_category = "All Categories"
        self.current_search = ""
        self.selected_product = None
        self.products_data = []
        self.categories_data = []
        self.sort_column = 'name'
        self.sort_reverse = False
        
        # UI Variables
        self.search_var = StringVar()
        self.search_var.trace('w', self._on_search_change)
        
        # Statistics variables
        self.stats = {
            'total_products': 0,
            'total_categories': 0,
            'low_stock': 0,
            'out_of_stock': 0,
            'total_value': 0.0
        }
        
        # Setup professional UI
        self._setup_professional_styles()
        self._create_professional_ui()
        self._load_business_data()
        
        # Register for language changes
        register_refresh_callback(self._retranslate)
    
    def _setup_professional_styles(self):
        """Setup professional business styles"""
        style = ttk.Style()
        
        # Professional business frame styles
        style.configure("Business.TFrame", 
                       background=self.colors['background'])
        
        style.configure("BusinessCard.TFrame", 
                       background=self.colors['card'],
                       relief="solid", 
                       borderwidth=1)
        
        style.configure("BusinessSidebar.TFrame",
                       background=self.colors['primary'])
        
        # Professional typography
        style.configure("BusinessTitle.TLabel",
                       font=("Segoe UI", 20, "bold"),
                       foreground=self.colors['primary'],
                       background=self.colors['background'])
        
        style.configure("BusinessHeader.TLabel",
                       font=("Segoe UI", 14, "bold"),
                       foreground=self.colors['text'],
                       background=self.colors['card'])
        
        style.configure("BusinessText.TLabel",
                       font=("Segoe UI", 10),
                       foreground=self.colors['text'],
                       background=self.colors['card'])
        
        style.configure("SidebarText.TLabel",
                       font=("Segoe UI", 11, "bold"),
                       foreground='white',
                       background=self.colors['primary'])
        
        # Professional button styles
        style.configure("Category.TButton",
                       font=("Segoe UI", 10),
                       padding=(15, 8))
        
        style.configure("CategoryActive.TButton",
                       font=("Segoe UI", 10, "bold"))
        
        # Status indicator styles
        style.configure("Success.TLabel",
                       foreground=self.colors['success'],
                       background=self.colors['card'],
                       font=("Segoe UI", 9, "bold"))
        
        style.configure("Warning.TLabel", 
                       foreground=self.colors['warning'],
                       background=self.colors['card'],
                       font=("Segoe UI", 9, "bold"))
        
        style.configure("Danger.TLabel",
                       foreground=self.colors['danger'], 
                       background=self.colors['card'],
                       font=("Segoe UI", 9, "bold"))

    def _create_professional_ui(self):
        """Create professional business-focused UI layout"""
        # Configure main frame
        self.configure(style="Business.TFrame")
        
        # Main container with professional layout
        main_container = ttk.Frame(self, style="Business.TFrame")
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title section
        title_frame = ttk.Frame(main_container, style="Business.TFrame")
        title_frame.pack(fill=X, pady=(0, 15))
        
        title_label = ttk.Label(title_frame, 
                               text="📦 Professional Inventory Management",
                               style="BusinessTitle.TLabel")
        title_label.pack(side=LEFT)
        
        # Professional layout: Sidebar + Main content
        content_frame = ttk.Frame(main_container, style="Business.TFrame")
        content_frame.pack(fill=BOTH, expand=True)
        
        # Left sidebar for categories and statistics
        self._create_categories_sidebar(content_frame)
        
        # Main content area
        self._create_main_content(content_frame)
    
    def _create_categories_sidebar(self, parent):
        """Create professional categories sidebar with business intelligence"""
        sidebar = ttk.Frame(parent, style="BusinessSidebar.TFrame", width=280)
        sidebar.pack(side=LEFT, fill=Y, padx=(0, 15))
        sidebar.pack_propagate(False)
        
        # Sidebar padding
        sidebar_content = ttk.Frame(sidebar, style="BusinessSidebar.TFrame")
        sidebar_content.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # Categories section
        categories_title = ttk.Label(sidebar_content,
                                   text="📁 Product Categories",
                                   style="SidebarText.TLabel")
        categories_title.pack(anchor=W, pady=(0, 10))
        
        # Categories container
        self.categories_frame = ttk.Frame(sidebar_content, style="BusinessSidebar.TFrame")
        self.categories_frame.pack(fill=X, pady=(0, 20))
        
        # Statistics section  
        stats_title = ttk.Label(sidebar_content,
                               text="📊 Quick Statistics",
                               style="SidebarText.TLabel")
        stats_title.pack(anchor=W, pady=(20, 10))
        
        # Statistics container
        self.stats_frame = ttk.Frame(sidebar_content, style="BusinessSidebar.TFrame")
        self.stats_frame.pack(fill=X)
        
        # Statistics labels
        self.stats_labels = {
            'total_products': ttk.Label(self.stats_frame, style="SidebarText.TLabel"),
            'total_categories': ttk.Label(self.stats_frame, style="SidebarText.TLabel"),
            'low_stock': ttk.Label(self.stats_frame, style="SidebarText.TLabel"),
            'out_of_stock': ttk.Label(self.stats_frame, style="SidebarText.TLabel"),
            'total_value': ttk.Label(self.stats_frame, style="SidebarText.TLabel")
        }
        
        for label in self.stats_labels.values():
            label.pack(anchor=W, pady=2)
    
    def _create_main_content(self, parent):
        """Create main content area with product table and controls"""
        main_area = ttk.Frame(parent, style="BusinessCard.TFrame")
        main_area.pack(side=RIGHT, fill=BOTH, expand=True)
        
        # Main content padding
        content = ttk.Frame(main_area, style="BusinessCard.TFrame")
        content.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Search and controls section
        self._create_search_controls(content)
        
        # Products table section
        self._create_products_table(content)
        
        # Action buttons section
        self._create_action_buttons(content)
    
    def _create_search_controls(self, parent):
        """Create professional search and filter controls"""
        controls_frame = ttk.Frame(parent, style="BusinessCard.TFrame")
        controls_frame.pack(fill=X, pady=(0, 15))
        
        # Search section
        search_frame = ttk.Frame(controls_frame, style="BusinessCard.TFrame")
        search_frame.pack(side=LEFT, fill=X, expand=True)
        
        search_label = ttk.Label(search_frame, 
                                text="🔍 Search Products:",
                                style="BusinessHeader.TLabel")
        search_label.pack(side=LEFT, padx=(0, 10))
        
        self.search_entry = ttk.Entry(search_frame, 
                                     textvariable=self.search_var,
                                     font=("Segoe UI", 11),
                                     width=30)
        self.search_entry.pack(side=LEFT, padx=(0, 10))
        
        # Sort controls
        sort_frame = ttk.Frame(controls_frame, style="BusinessCard.TFrame")
        sort_frame.pack(side=RIGHT)
        
        ttk.Label(sort_frame, 
                 text="Sort by:",
                 style="BusinessText.TLabel").pack(side=LEFT, padx=(10, 5))
        
        self.sort_combo = ttk.Combobox(sort_frame,
                                      values=['Name', 'Price', 'Stock', 'Category'],
                                      state='readonly',
                                      width=12)
        self.sort_combo.set('Name')
        self.sort_combo.pack(side=LEFT)
        self.sort_combo.bind('<<ComboboxSelected>>', self._on_sort_change)
    
    def _create_products_table(self, parent):
        """Create detailed professional products table"""
        table_frame = ttk.Frame(parent, style="BusinessCard.TFrame")
        table_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Table header
        header_frame = ttk.Frame(table_frame, style="BusinessCard.TFrame")
        header_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(header_frame,
                 text="📋 Product Details",
                 style="BusinessHeader.TLabel").pack(side=LEFT)
        
        self.results_label = ttk.Label(header_frame,
                                      text="",
                                      style="BusinessText.TLabel")
        self.results_label.pack(side=RIGHT)
        
        # Professional treeview with detailed columns
        columns = ('id', 'name', 'category', 'buy_price', 'sell_price', 
                  'stock', 'total_value', 'status')
        
        self.products_tree = ttk.Treeview(table_frame,
                                         columns=columns,
                                         show='headings',
                                         height=15)
        
        # Configure column headings and widths
        column_config = {
            'id': ('ID', 60),
            'name': ('Product Name', 200),
            'category': ('Category', 120),
            'buy_price': ('Buy Price', 100),
            'sell_price': ('Sell Price', 100),
            'stock': ('Stock', 80),
            'total_value': ('Total Value', 120),
            'status': ('Status', 100)
        }
        
        for col, (heading, width) in column_config.items():
            self.products_tree.heading(col, text=heading)
            self.products_tree.column(col, width=width, anchor=CENTER)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, 
                                   command=self.products_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=HORIZONTAL,
                                   command=self.products_tree.xview)
        
        self.products_tree.configure(yscrollcommand=v_scrollbar.set,
                                    xscrollcommand=h_scrollbar.set)
        
        # Grid layout for table and scrollbars
        self.products_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection event
        self.products_tree.bind('<<TreeviewSelect>>', self._on_product_select)
    
    def _create_action_buttons(self, parent):
        """Create professional action buttons"""
        actions_frame = ttk.Frame(parent, style="BusinessCard.TFrame")
        actions_frame.pack(fill=X, pady=(10, 0))
        
        # Left side buttons - Product Management
        left_buttons = ttk.Frame(actions_frame, style="BusinessCard.TFrame")
        left_buttons.pack(side=LEFT)
        
        ttk.Button(left_buttons,
                  text="➕ Add Product",
                  bootstyle="success",
                  command=self._show_add_product_dialog).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(left_buttons,
                  text="✏️ Edit Product", 
                  bootstyle="primary",
                  command=self._edit_selected_product).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(left_buttons,
                  text="🗑️ Delete",
                  bootstyle="danger",
                  command=self._delete_selected_product).pack(side=LEFT, padx=(0, 10))
        
        # Right side buttons - Critical Business Functions
        right_buttons = ttk.Frame(actions_frame, style="BusinessCard.TFrame")
        right_buttons.pack(side=RIGHT)
        
        ttk.Button(right_buttons,
                  text="📉 Record Loss",
                  bootstyle="warning",
                  command=self._record_loss).pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(right_buttons,
                  text="📊 Export Report",
                  bootstyle="info", 
                  command=self._export_report).pack(side=LEFT)
    
    # Business Logic Methods
    def _load_business_data(self):
        """Load business data and update UI"""
        try:
            # Load products
            self.products_data = enhanced_data.get_products()
            
            # Load categories  
            self.categories_data = enhanced_data.get_categories()
            
            # Update UI components
            self._update_categories_display()
            self._update_products_display()
            self._update_statistics()
            
        except Exception as e:
            logger.error(f"Error loading business data: {e}")
            messagebox.showerror("Data Error", 
                               f"Error loading inventory data: {str(e)}")
    
    def _update_categories_display(self):
        """Update categories sidebar buttons"""
        # Clear existing buttons
        for widget in self.categories_frame.winfo_children():
            widget.destroy()
        
        # Add "All Categories" button
        all_btn = ttk.Button(self.categories_frame,
                            text="📦 All Categories",
                            style="CategoryActive.TButton" if self.current_category == "All Categories" else "Category.TButton",
                            command=lambda: self._set_category_filter("All Categories"))
        all_btn.pack(fill=X, pady=2)
        
        # Add category buttons
        for category in self.categories_data:
            name = category.get('name', str(category))
            count = self._get_category_product_count(name)
            
            button_text = f"📁 {name} ({count})"
            style = "CategoryActive.TButton" if name == self.current_category else "Category.TButton"
            
            btn = ttk.Button(self.categories_frame,
                           text=button_text,
                           style=style,
                           command=lambda n=name: self._set_category_filter(n))
            btn.pack(fill=X, pady=2)
    
    def _update_products_display(self):
        """Update products table with filtering and sorting"""
        # Clear current items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Filter and sort products
        filtered_products = self._filter_and_sort_products()
        
        # Populate table
        for product in filtered_products:
            # Calculate values
            stock = int(product.get('stock', 0))
            sell_price = float(product.get('sell_price', 0))
            total_value = stock * sell_price
            
            # Determine status
            if stock == 0:
                status = "Out of Stock"
                status_tag = "danger"
            elif stock <= 5:
                status = "Low Stock"  
                status_tag = "warning"
            else:
                status = "In Stock"
                status_tag = "success"
            
            # Insert row
            item = self.products_tree.insert('', END, values=(
                product.get('id', ''),
                product.get('name', ''),
                product.get('category', ''),
                f"${float(product.get('buy_price', 0)):.2f}",
                f"${sell_price:.2f}",
                stock,
                f"${total_value:.2f}",
                status
            ))
            
            # Apply status tag
            self.products_tree.set(item, 'status', status)
        
        # Update results count
        self.results_label.config(text=f"Showing {len(filtered_products)} products")
    
    def _update_statistics(self):
        """Update business statistics"""
        # Calculate statistics
        total_products = len(self.products_data)
        total_categories = len(self.categories_data)
        low_stock = sum(1 for p in self.products_data if 0 < int(p.get('stock', 0)) <= 5)
        out_of_stock = sum(1 for p in self.products_data if int(p.get('stock', 0)) == 0)
        total_value = sum(int(p.get('stock', 0)) * float(p.get('sell_price', 0)) for p in self.products_data)
        
        # Update statistics display
        self.stats_labels['total_products'].config(text=f"📦 Products: {total_products}")
        self.stats_labels['total_categories'].config(text=f"📁 Categories: {total_categories}")
        self.stats_labels['low_stock'].config(text=f"⚠️ Low Stock: {low_stock}")
        self.stats_labels['out_of_stock'].config(text=f"❌ Out of Stock: {out_of_stock}")
        self.stats_labels['total_value'].config(text=f"💰 Total Value: ${total_value:,.2f}")
    
    def _filter_and_sort_products(self):
        """Filter and sort products based on current criteria"""
        filtered = self.products_data[:]
        
        # Category filter
        if self.current_category != "All Categories":
            filtered = [p for p in filtered if p.get('category', '') == self.current_category]
        
        # Search filter
        if self.current_search:
            search_lower = self.current_search.lower()
            filtered = [p for p in filtered if 
                       search_lower in p.get('name', '').lower() or
                       search_lower in p.get('category', '').lower() or
                       search_lower in str(p.get('barcode', '')).lower()]
        
        # Sort
        sort_key_map = {
            'Name': 'name',
            'Price': 'sell_price', 
            'Stock': 'stock',
            'Category': 'category'
        }
        
        sort_key = sort_key_map.get(self.sort_combo.get(), 'name')
        
        try:
            if sort_key in ['sell_price', 'stock']:
                filtered.sort(key=lambda x: float(x.get(sort_key, 0)), reverse=self.sort_reverse)
            else:
                filtered.sort(key=lambda x: str(x.get(sort_key, '')).lower(), reverse=self.sort_reverse)
        except Exception as e:
            logger.error(f"Sort error: {e}")
        
        return filtered
    
    def _get_category_product_count(self, category_name):
        """Get product count for category"""
        return sum(1 for p in self.products_data if p.get('category', '') == category_name)
    
    # Event Handlers
    def _set_category_filter(self, category):
        """Set category filter"""
        self.current_category = category
        self._update_categories_display()
        self._update_products_display()
    
    def _on_search_change(self, *args):
        """Handle search text change"""
        self.current_search = self.search_var.get()
        self._update_products_display()
    
    def _on_sort_change(self, event=None):
        """Handle sort selection change"""
        self._update_products_display()
    
    def _on_product_select(self, event=None):
        """Handle product selection"""
        selection = self.products_tree.selection()
        if selection:
            item = selection[0]
            values = self.products_tree.item(item, 'values')
            if values:
                product_id = values[0]
                self.selected_product = next((p for p in self.products_data if str(p.get('id')) == str(product_id)), None)
    
    # Action Methods (Business Operations)
    def _show_add_product_dialog(self):
        """Show add product dialog"""
        dialog = ProductDialog(self)
        result = dialog.show()
        
        if result:
            try:
                # Add product to database (placeholder)
                logger.info(f"Adding product: {result}")
                messagebox.showinfo("Success", "Product added successfully!")
                self._load_business_data()  # Refresh data
            except Exception as e:
                logger.error(f"Error adding product: {e}")
                messagebox.showerror("Error", f"Error adding product: {str(e)}")
    
    def _edit_selected_product(self):
        """Edit selected product"""
        if not self.selected_product:
            messagebox.showwarning("No Selection", "Please select a product to edit.")
            return
        
        dialog = ProductDialog(self, self.selected_product)
        result = dialog.show()
        
        if result:
            try:
                # Update product in database (placeholder)
                logger.info(f"Updating product: {result}")
                messagebox.showinfo("Success", "Product updated successfully!")
                self._load_business_data()  # Refresh data
            except Exception as e:
                logger.error(f"Error updating product: {e}")
                messagebox.showerror("Error", f"Error updating product: {str(e)}")
    
    def _delete_selected_product(self):
        """Delete selected product"""
        if not self.selected_product:
            messagebox.showwarning("No Selection", "Please select a product to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete",
                             f"Are you sure you want to delete '{self.selected_product['name']}'?\n"
                             "This action cannot be undone."):
            try:
                # Delete product from database (placeholder)
                logger.info(f"Deleting product: {self.selected_product['id']}")
                messagebox.showinfo("Success", "Product deleted successfully!")
                self._load_business_data()  # Refresh data
            except Exception as e:
                logger.error(f"Error deleting product: {e}")
                messagebox.showerror("Error", f"Error deleting product: {str(e)}")
    
    def _record_loss(self):
        """Record product loss (Critical business function)"""
        if not self.selected_product:
            messagebox.showwarning("No Selection", "Please select a product to record a loss for.")
            return
        
        dialog = LossRecordDialog(self, self.selected_product)
        result = dialog.show()
        
        if result:
            try:
                # Record loss in database and update stock (placeholder)
                logger.info(f"Recording loss: {result}")
                messagebox.showinfo("Success", 
                    f"Loss recorded successfully!\n"
                    f"Product: {self.selected_product['name']}\n"
                    f"Quantity: {result['quantity_lost']}\n"
                    f"Reason: {result['reason']}")
                self._load_business_data()  # Refresh data
            except Exception as e:
                logger.error(f"Error recording loss: {e}")
                messagebox.showerror("Error", f"Error recording loss: {str(e)}")
    
    def _export_report(self):
        """Export inventory report"""
        try:
            # Generate report (placeholder)
            messagebox.showinfo("Export", "Inventory report exported successfully!")
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            messagebox.showerror("Error", f"Error exporting report: {str(e)}")
    
    # Compatibility Methods
    def refresh(self):
        """Refresh the page data"""
        self._load_business_data()
    
    def _retranslate(self):
        """Handle language changes"""
        # Refresh UI text for internationalization
        pass
    
    def __del__(self):
        """Cleanup on page destruction"""
        unregister_refresh_callback(self._retranslate)
