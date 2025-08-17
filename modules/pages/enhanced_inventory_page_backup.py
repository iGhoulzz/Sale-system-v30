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
                       padding=(15, 8),
                       background="#0078D4",
                       foreground="#FFFFFF")
        
        # Statistics card styles
        style.configure("Stats.TLabel", 
                       font=("Segoe UI", 14, "bold"), 
                       foreground="#FFFFFF",
                       background="#2B2B2B")
        
        # Product list styles - dark theme
        style.configure("Product.Treeview", 
                       font=("Segoe UI", 10),
                       background="#383838",
                       foreground="#FFFFFF",
                       fieldbackground="#383838",
                       rowheight=25)
        
        style.configure("Product.Treeview.Heading", 
                       font=("Segoe UI", 10, "bold"),
                       background="#2B2B2B",
                       foreground="#FFFFFF")
        
        # Search entry dark theme
        style.configure("Search.TEntry", 
                       font=("Segoe UI", 12),
                       fieldbackground="#383838",
                       foreground="#FFFFFF",
                       borderwidth=1)
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Main container with dark background to match system theme
        main_container = ttk.Frame(self, style="Dark.TFrame")
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Header section
        self._create_header(main_container)
        
        # Statistics dashboard
        self._create_statistics(main_container)
        
        # Categories section
        self._create_categories_section(main_container)
        
        # Search and filters
        self._create_search_section(main_container)
        
        # Products list and management
        self._create_products_section(main_container)
        
        # Action buttons
        self._create_action_buttons(main_container)
    
    def _create_header(self, parent):
        """Create header with title and navigation"""
        header_frame = ttk.Frame(parent, style="Dark.TFrame")
        header_frame.pack(fill=X, pady=(0, 20))
        
        # Title with dark theme
        title_label = ttk.Label(
            header_frame,
            text=_("📦 Inventory Management"),
            style="DarkHeader.TLabel"
        )
        title_label.pack(side=LEFT)
        
        # Back button
        back_btn = ttk.Button(
            header_frame,
            text=_("🏠 Back to Home"),
            bootstyle="secondary-outline",
            command=lambda: self.controller.show_frame("MainMenuPage")
        )
        back_btn.pack(side=RIGHT)
        
        # Refresh button
        refresh_btn = ttk.Button(
            header_frame,
            text=_("🔄 Refresh"),
            bootstyle="info-outline",
            command=self._refresh_all_data
        )
        refresh_btn.pack(side=RIGHT, padx=(0, 10))
    
    def _create_statistics(self, parent):
        """Create statistics dashboard with dark theme"""
        stats_frame = ttk.Frame(parent, style="Dark.TFrame")
        stats_frame.pack(fill=X, pady=(0, 20))
        
        # Title with dark theme
        ttk.Label(
            stats_frame,
            text=_("📊 Inventory Statistics"),
            style="DarkSubheader.TLabel"
        ).pack(anchor=W, pady=(0, 10))
        
        # Stats cards container
        cards_frame = ttk.Frame(stats_frame, style="Dark.TFrame")
        cards_frame.pack(fill=X)
        
        # Total Products Card
        self.total_products_card = ttk.Frame(cards_frame, style="DarkCard.TFrame")
        self.total_products_card.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        
        ttk.Label(
            self.total_products_card,
            text="📦",
            font=("Segoe UI", 24),
            background="#383838",
            foreground="#FFFFFF"
        ).pack(pady=(10, 5))
        
        ttk.Label(
            self.total_products_card,
            text=_("Total Products"),
            font=("Segoe UI", 10, "bold"),
            foreground="#FFFFFF",
            background="#383838"
        ).pack()
        
        self.total_products_label = ttk.Label(
            self.total_products_card,
            text="0",
            font=("Segoe UI", 20, "bold"),
            foreground="#FFFFFF",
            background="#383838"
        )
        self.total_products_label.pack(pady=(5, 10))
        
        # Total Value Card with dark theme
        self.total_value_card = ttk.Frame(cards_frame, style="DarkCard.TFrame")
        self.total_value_card.pack(side=LEFT, fill=X, expand=True, padx=(5, 5))
        
        ttk.Label(
            self.total_value_card,
            text="💰",
            font=("Segoe UI", 24),
            background="#383838",
            foreground="#FFFFFF"
        ).pack(pady=(10, 5))
        
        ttk.Label(
            self.total_value_card,
            text=_("Total Value"),
            font=("Segoe UI", 10, "bold"),
            foreground="#6C757D",
            background="#F8F9FA"
        ).pack()
        
        self.total_value_label = ttk.Label(
            self.total_value_card,
            text="$0.00",
            font=("Segoe UI", 20, "bold"),
            foreground="#28A745",
            background="#F8F9FA"
        )
        self.total_value_label.pack(pady=(5, 10))
        
        # Low Stock Card
        self.low_stock_card = ttk.Frame(cards_frame, style="Card.TFrame")
        self.low_stock_card.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
        ttk.Label(
            self.low_stock_card,
            text="⚠️",
            font=("Segoe UI", 24),
            background="#F8F9FA"
        ).pack(pady=(10, 5))
        
        ttk.Label(
            self.low_stock_card,
            text=_("Low Stock Items"),
            font=("Segoe UI", 10, "bold"),
            foreground="#6C757D",
            background="#F8F9FA"
        ).pack()
        
        self.low_stock_label = ttk.Label(
            self.low_stock_card,
            text="0",
            font=("Segoe UI", 20, "bold"),
            foreground="#DC3545",
            background="#F8F9FA"
        )
        self.low_stock_label.pack(pady=(5, 10))
    
    def _create_categories_section(self, parent):
        """Create categories management section"""
        categories_frame = ttk.Frame(parent, style="Light.TFrame")
        categories_frame.pack(fill=X, pady=(0, 20))
        
        # Header
        header_frame = ttk.Frame(categories_frame, style="Light.TFrame")
        header_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text=_("📁 Categories"),
            style="Subheader.TLabel"
        ).pack(side=LEFT)
        
        # Add category button
        add_cat_btn = ttk.Button(
            header_frame,
            text=_("➕ Add Category"),
            bootstyle="success-outline",
            command=self._add_category
        )
        add_cat_btn.pack(side=RIGHT)
        
        # Categories buttons container
        self.categories_container = ttk.Frame(categories_frame, style="Light.TFrame")
        self.categories_container.pack(fill=X)
        
        # Load categories buttons
        self._load_categories()
    
    def _load_categories(self):
        """Load and display category buttons"""
        # Clear existing buttons
        for widget in self.categories_container.winfo_children():
            widget.destroy()
        
        try:
            # Load categories from database
            categories = enhanced_data.get_categories()
            
            # Add "All" category first
            all_btn = ttk.Button(
                self.categories_container,
                text=_("📋 All Categories"),
                style="ActiveCategory.TButton" if self.current_category == "All" else "Category.TButton",
                bootstyle="primary" if self.current_category == "All" else "outline-primary",
                command=lambda: self._filter_by_category("All")
            )
            all_btn.pack(side=LEFT, padx=(0, 5), pady=5)
            
            # Add category buttons
            if hasattr(categories, 'data'):
                for category in categories.data:
                    cat_name = category.get('Name', 'Unknown')
                    cat_btn = ttk.Button(
                        self.categories_container,
                        text=f"📂 {cat_name}",
                        style="ActiveCategory.TButton" if self.current_category == cat_name else "Category.TButton",
                        bootstyle="primary" if self.current_category == cat_name else "outline-primary",
                        command=lambda c=cat_name: self._filter_by_category(c)
                    )
                    cat_btn.pack(side=LEFT, padx=5, pady=5)
            
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
    
    def _create_search_section(self, parent):
        """Create search and filter section"""
        search_frame = ttk.Frame(parent, style="Light.TFrame")
        search_frame.pack(fill=X, pady=(0, 20))
        
        # Search row
        search_row = ttk.Frame(search_frame, style="Light.TFrame")
        search_row.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            search_row,
            text=_("🔍 Search:"),
            style="Body.TLabel"
        ).pack(side=LEFT, padx=(0, 10))
        
        # Search entry
        self.search_entry = ttk.Entry(
            search_row,
            textvariable=self.search_var,
            font=("Segoe UI", 12),
            width=40
        )
        self.search_entry.pack(side=LEFT, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Search button
        search_btn = ttk.Button(
            search_row,
            text=_("Search"),
            bootstyle="primary",
            command=self._perform_search
        )
        search_btn.pack(side=LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(
            search_row,
            text=_("Clear"),
            bootstyle="secondary-outline",
            command=self._clear_search
        )
        clear_btn.pack(side=LEFT)
        
        # Filter row
        filter_row = ttk.Frame(search_frame, style="Light.TFrame")
        filter_row.pack(fill=X)
        
        ttk.Label(
            filter_row,
            text=_("Filter:"),
            style="Body.TLabel"
        ).pack(side=LEFT, padx=(0, 10))
        
        # Stock status filters
        ttk.Radiobutton(
            filter_row,
            text=_("All Items"),
            variable=self.stock_filter_var,
            value="all",
            command=self._apply_filters
        ).pack(side=LEFT, padx=(0, 15))
        
        ttk.Radiobutton(
            filter_row,
            text=_("In Stock"),
            variable=self.stock_filter_var,
            value="in_stock",
            command=self._apply_filters
        ).pack(side=LEFT, padx=(0, 15))
        
        ttk.Radiobutton(
            filter_row,
            text=_("Low Stock"),
            variable=self.stock_filter_var,
            value="low_stock",
            command=self._apply_filters
        ).pack(side=LEFT, padx=(0, 15))
        
        ttk.Radiobutton(
            filter_row,
            text=_("Out of Stock"),
            variable=self.stock_filter_var,
            value="out_of_stock",
            command=self._apply_filters
        ).pack(side=LEFT)
    
    def _create_products_section(self, parent):
        """Create products list and management section"""
        products_frame = ttk.Frame(parent, style="Light.TFrame")
        products_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # Header
        header_frame = ttk.Frame(products_frame, style="Light.TFrame")
        header_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text=_("📋 Products List"),
            style="Subheader.TLabel"
        ).pack(side=LEFT)
        
        # Status label
        self.status_label = ttk.Label(
            header_frame,
            text="",
            style="Body.TLabel"
        )
        self.status_label.pack(side=RIGHT)
        
        # Products treeview with scrollbars
        tree_frame = ttk.Frame(products_frame, style="Light.TFrame")
        tree_frame.pack(fill=BOTH, expand=True)
        
        # Define columns
        columns = ("ID", "Name", "Category", "Stock", "Price", "Buy_Price", "Barcode")
        
        self.products_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Product.Treeview",
            height=15
        )
        
        # Configure columns
        self.products_tree.heading("ID", text=_("ID"))
        self.products_tree.heading("Name", text=_("Product Name"))
        self.products_tree.heading("Category", text=_("Category"))
        self.products_tree.heading("Stock", text=_("Stock"))
        self.products_tree.heading("Price", text=_("Sell Price"))
        self.products_tree.heading("Buy_Price", text=_("Buy Price"))
        self.products_tree.heading("Barcode", text=_("Barcode"))
        
        # Configure column widths
        self.products_tree.column("ID", width=50, minwidth=50)
        self.products_tree.column("Name", width=200, minwidth=150)
        self.products_tree.column("Category", width=120, minwidth=100)
        self.products_tree.column("Stock", width=80, minwidth=60)
        self.products_tree.column("Price", width=100, minwidth=80)
        self.products_tree.column("Buy_Price", width=100, minwidth=80)
        self.products_tree.column("Barcode", width=120, minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.products_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.products_tree.xview)
        
        self.products_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.products_tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Bind selection event
        self.products_tree.bind('<<TreeviewSelect>>', self._on_product_select)
        self.products_tree.bind('<Double-1>', self._edit_product)
    
    def _create_action_buttons(self, parent):
        """Create action buttons for product management"""
        actions_frame = ttk.Frame(parent, style="Light.TFrame")
        actions_frame.pack(fill=X)
        
        # Add Product button
        add_btn = ttk.Button(
            actions_frame,
            text=_("➕ Add Product"),
            bootstyle="success",
            command=self._add_product
        )
        add_btn.pack(side=LEFT, padx=(0, 10))
        
        # Edit Product button
        self.edit_btn = ttk.Button(
            actions_frame,
            text=_("✏️ Edit Product"),
            bootstyle="warning",
            command=self._edit_product,
            state="disabled"
        )
        self.edit_btn.pack(side=LEFT, padx=(0, 10))
        
        # Delete Product button
        self.delete_btn = ttk.Button(
            actions_frame,
            text=_("🗑️ Delete Product"),
            bootstyle="danger",
            command=self._delete_product,
            state="disabled"
        )
        self.delete_btn.pack(side=LEFT, padx=(0, 10))
        
        # Record Loss button
        self.loss_btn = ttk.Button(
            actions_frame,
            text=_("📉 Record Loss"),
            bootstyle="warning-outline",
            command=self._record_loss,
            state="disabled"
        )
        self.loss_btn.pack(side=LEFT, padx=(0, 10))
        
        # Export button
        export_btn = ttk.Button(
            actions_frame,
            text=_("📤 Export"),
            bootstyle="info-outline",
            command=self._export_products
        )
        export_btn.pack(side=RIGHT)
    
    def _load_initial_data(self):
        """Load initial data for the page"""
        self._load_statistics()
        self._load_products()
    
    def _load_statistics(self):
        """Load and display inventory statistics"""
        try:
            # Get products data
            products_data = enhanced_data.get_products()
            
            # Handle both list and PagedResult formats
            if hasattr(products_data, 'data'):
                # It's a PagedResult object
                products_list = products_data.data
            elif isinstance(products_data, list):
                # It's a plain list
                products_list = products_data
            else:
                products_list = []
            
            if products_list:
                total_products = len(products_list)
                total_value = sum(float(p.get('SellingPrice', p.get('Price', 0))) * int(p.get('Stock', 0)) for p in products_list)
                low_stock = sum(1 for p in products_list if int(p.get('Stock', 0)) <= 5 and int(p.get('Stock', 0)) > 0)
                
                self.total_products_label.config(text=str(total_products))
                self.total_value_label.config(text=f"${total_value:.2f}")
                self.low_stock_label.config(text=str(low_stock))
            
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
    
    def _load_products(self):
        """Load and display products"""
        try:
            # Clear existing items
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            # Load products
            products_data = enhanced_data.get_products()
            
            # Handle both list and PagedResult formats
            if hasattr(products_data, 'data'):
                # It's a PagedResult object
                products_list = products_data.data
            elif isinstance(products_data, list):
                # It's a plain list
                products_list = products_data
            else:
                products_list = []
            
            for product in products_list:
                # Apply current filters
                if not self._should_show_product(product):
                    continue
                
                values = (
                    product.get('ProductID', product.get('ID', '')),
                    product.get('Name', ''),
                    product.get('Category', ''),
                    product.get('Stock', ''),
                    f"${float(product.get('SellingPrice', product.get('Price', 0))):.2f}",
                    f"${float(product.get('BuyingPrice', product.get('BuyPrice', 0))):.2f}",
                    product.get('Barcode', '')
                )
                
                # Color coding for stock levels
                item_id = self.products_tree.insert('', 'end', values=values)
                stock = int(product.get('Stock', 0))
                if stock == 0:
                    self.products_tree.set(item_id, "Stock", "Out of Stock")
                elif stock <= 5:
                    # Low stock - could add tag here for coloring
                    pass
            
            self.status_label.config(text=f"{len(self.products_tree.get_children())} products displayed")
            
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            messagebox.showerror(_("Error"), f"{_('Error loading products')}: {e}")
    
    def _should_show_product(self, product):
        """Check if product should be shown based on current filters"""
        # Category filter
        if self.current_category != "All" and product.get('Category', '') != self.current_category:
            return False
        
        # Stock filter
        stock = int(product.get('Stock', 0))
        stock_filter = self.stock_filter_var.get()
        
        if stock_filter == "in_stock" and stock <= 0:
            return False
        elif stock_filter == "out_of_stock" and stock > 0:
            return False
        elif stock_filter == "low_stock" and (stock > 5 or stock <= 0):
            return False
        
        # Search filter
        if self.current_search:
            search_text = self.current_search.lower()
            if (search_text not in product.get('Name', '').lower() and
                search_text not in product.get('Category', '').lower() and
                search_text not in product.get('Barcode', '').lower()):
                return False
        
        return True
    
    def _filter_by_category(self, category):
        """Filter products by category"""
        self.current_category = category
        self._load_categories()  # Refresh category buttons
        self._load_products()    # Refresh products list
    
    def _on_search_change(self, event):
        """Handle search text change with debouncing"""
        # Cancel previous search
        if hasattr(self, '_search_after'):
            self.after_cancel(self._search_after)
        
        # Schedule new search
        self._search_after = self.after(500, self._perform_search)
    
    def _perform_search(self):
        """Perform the search"""
        self.current_search = self.search_var.get().strip()
        self._load_products()
    
    def _perform_product_search(self, search_term: str, limit: int = None):
        """Perform product search with limit parameter"""
        try:
            if search_term.strip():
                return enhanced_data.search_products(search_term, limit=limit)
            else:
                return enhanced_data.get_products(limit=limit)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _clear_search(self):
        """Clear search and filters"""
        self.search_var.set("")
        self.current_search = ""
        self.current_category = "All"
        self.stock_filter_var.set("all")
        self._load_categories()
        self._load_products()
    
    def _apply_filters(self):
        """Apply current filters"""
        self._load_products()
    
    def _on_product_select(self, event):
        """Handle product selection"""
        selection = self.products_tree.selection()
        if selection:
            self.selected_product = self.products_tree.item(selection[0])['values']
            self.edit_btn.config(state="normal")
            self.delete_btn.config(state="normal")
            self.loss_btn.config(state="normal")
        else:
            self.selected_product = None
            self.edit_btn.config(state="disabled")
            self.delete_btn.config(state="disabled")
            self.loss_btn.config(state="disabled")
    
    def _add_product(self):
        """Add new product"""
        self._open_product_dialog()
    
    def _edit_product(self, event=None):
        """Edit selected product"""
        if self.selected_product:
            self._open_product_dialog(edit_mode=True)
    
    def _delete_product(self):
        """Delete selected product"""
        if not self.selected_product:
            return
        
        product_name = self.selected_product[1]
        if messagebox.askyesno(
            _("Confirm Delete"),
            f"{_('Are you sure you want to delete')} '{product_name}'?\n{_('This action cannot be undone.')}"
        ):
            try:
                product_id = self.selected_product[0]
                # Delete from database
                enhanced_data.delete_product(product_id)
                
                # Refresh display
                self._refresh_all_data()
                
                messagebox.showinfo(_("Success"), _("Product deleted successfully"))
                
            except Exception as e:
                logger.error(f"Error deleting product: {e}")
                messagebox.showerror(_("Error"), f"{_('Error deleting product')}: {e}")
    
    def _record_loss(self):
        """Record product loss"""
        if not self.selected_product:
            return
        
        self._open_loss_dialog()
    
    def _add_category(self):
        """Add new category"""
        self._open_category_dialog()
    
    def _export_products(self):
        """Export products to file"""
        # Implementation for export functionality
        messagebox.showinfo(_("Export"), _("Export functionality coming soon"))
    
    def _open_product_dialog(self, edit_mode=False):
        """Open product add/edit dialog"""
        from modules.pages.product_dialog import ProductDialog
        
        initial_data = None
        if edit_mode and self.selected_product:
            initial_data = {
                'ID': self.selected_product[0],
                'Name': self.selected_product[1],
                'Category': self.selected_product[2],
                'Stock': self.selected_product[3],
                'Price': self.selected_product[4].replace('$', ''),
                'BuyPrice': self.selected_product[5].replace('$', ''),
                'Barcode': self.selected_product[6]
            }
        
        dialog = ProductDialog(self, edit_mode=edit_mode, initial_data=initial_data)
        if dialog.result:
            self._refresh_all_data()
    
    def _open_loss_dialog(self):
        """Open loss recording dialog"""
        from modules.pages.loss_dialog import LossDialog
        
        product_data = {
            'ID': self.selected_product[0],
            'Name': self.selected_product[1],
            'Current_Stock': self.selected_product[3]
        }
        
        dialog = LossDialog(self, product_data)
        if dialog.result:
            self._refresh_all_data()
    
    def _open_category_dialog(self):
        """Open category dialog"""
        from modules.pages.category_dialog import CategoryDialog
        
        dialog = CategoryDialog(self)
        if dialog.result:
            self._load_categories()
    
    def _refresh_all_data(self):
        """Refresh all data"""
        self._load_statistics()
        self._load_categories()
        self._load_products()
        invalidate_cache()  # Clear cache to ensure fresh data
    
    def refresh_data(self):
        """Public method to refresh data - called from external components"""
        self._refresh_all_data()
    
    def load_data(self):
        """Public method to load data - called from external components"""
        self._refresh_all_data()
    
    def _retranslate(self):
        """Update text for language changes"""
        # This will be called when language changes
        pass
    
    def refresh(self):
        """Called when page is shown"""
        self._refresh_all_data()
    
    def prepare_for_display(self):
        """Called before page is displayed"""
        self._refresh_all_data()
    
    def __del__(self):
        """Cleanup when page is destroyed"""
        try:
            unregister_refresh_callback(self._retranslate)
        except:
            pass
