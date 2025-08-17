"""
Ultra-Modern 2025 Style Enhanced Inventory Page
Advanced UI with glassmorphism, animations, and modern interactions
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import (
    BOTH, END, CENTER, W, E, X, Y, LEFT, RIGHT, TOP, BOTTOM,
    HORIZONTAL, VERTICAL, messagebox, StringVar, BooleanVar, 
    IntVar, DoubleVar, Toplevel, Canvas
)
import datetime
import logging
from tkinter import font

# Import from our enhanced modules
from modules.enhanced_data_access import enhanced_data, PagedResult
from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry
from modules.db_manager import ConnectionContext
from modules.data_access import invalidate_cache

# Import internationalization support
from modules.i18n import _, tr, register_refresh_callback, unregister_refresh_callback, set_widget_direction

# Configure logger
logger = logging.getLogger(__name__)

class ModernInventoryPage2025(ttk.Frame):
    """
    Ultra-Modern 2025 Style Inventory Management Page
    Features: Glassmorphism, animations, modern cards, advanced filters
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        
        # Initialize variables
        self.current_category = "All"
        self.current_search = ""
        self.selected_product = None
        self.products_data = []
        self.categories_data = []
        self.view_mode = "grid"  # grid or list
        
        # UI Variables
        self.search_var = StringVar()
        self.category_var = StringVar(value="All")
        self.stock_filter_var = StringVar(value="all")
        self.sort_var = StringVar(value="name_asc")
        self.view_mode_var = StringVar(value="grid")
        
        # Animation variables
        self.animation_running = False
        
        # Setup the modern UI
        self._setup_modern_styles()
        self._create_modern_ui()
        self._setup_animations()
        self._load_initial_data()
        
        # Register for language changes
        register_refresh_callback(self._retranslate)
    
    def _setup_modern_styles(self):
        """Setup ultra-modern 2025 styles with glassmorphism and animations"""
        style = ttk.Style()
        
        # Modern dark theme colors (2025 style) - Fixed for tkinter compatibility
        self.colors = {
            'primary': '#667eea',          # Modern purple-blue
            'secondary': '#764ba2',        # Deep purple
            'accent': '#f093fb',           # Pink gradient
            'success': '#4facfe',          # Blue success
            'warning': '#f2994a',          # Orange warning
            'danger': '#f2709c',           # Pink danger
            'dark': '#1a1a2e',            # Deep dark blue
            'darker': '#16213e',           # Even darker
            'glass': '#3a3a3a',           # Glass effect (opaque)
            'text': '#ffffff',             # White text
            'text_muted': '#cccccc',       # Muted white (opaque)
            'card_bg': '#2d2d2d',          # Transparent card (opaque)
            'hover': '#404040',            # Hover effect (opaque)
        }
        
        # Glass card style (glassmorphism)
        style.configure("GlassCard.TFrame", 
                       background=self.colors['card_bg'],
                       relief="flat",
                       borderwidth=1)
        
        # Modern header style
        style.configure("ModernHeader.TLabel", 
                       font=("Segoe UI Variable", 28, "bold"), 
                       foreground=self.colors['text'],
                       background=self.colors['dark'])
        
        # Subtitle style
        style.configure("ModernSubtitle.TLabel", 
                       font=("Segoe UI Variable", 14), 
                       foreground=self.colors['text_muted'],
                       background=self.colors['dark'])
        
        # Card title style
        style.configure("CardTitle.TLabel", 
                       font=("Segoe UI Variable", 16, "bold"), 
                       foreground=self.colors['text'],
                       background=self.colors['card_bg'])
        
        # Metric style
        style.configure("Metric.TLabel", 
                       font=("Segoe UI Variable", 32, "bold"), 
                       foreground=self.colors['primary'],
                       background=self.colors['card_bg'])
        
        # Modern button styles
        style.configure("Primary.TButton", 
                       font=("Segoe UI Variable", 11, "bold"),
                       padding=(20, 12))
        
        style.configure("Glass.TButton", 
                       font=("Segoe UI Variable", 10),
                       padding=(15, 8))
        
        # Modern search entry
        style.configure("ModernSearch.TEntry", 
                       font=("Segoe UI Variable", 12),
                       padding=15)
        
        # Product card styles
        style.configure("ProductCard.TFrame", 
                       background=self.colors['card_bg'],
                       relief="flat",
                       borderwidth=1)
        
        # Modern treeview
        style.configure("Modern.Treeview", 
                       font=("Segoe UI Variable", 10),
                       rowheight=45,
                       borderwidth=0,
                       relief="flat")
        
        style.configure("Modern.Treeview.Heading", 
                       font=("Segoe UI Variable", 11, "bold"),
                       relief="flat",
                       borderwidth=0)
    
    def _create_modern_ui(self):
        """Create the ultra-modern 2025 UI layout"""
        # Main container with gradient background
        self.configure(style="Dark.TFrame")
        
        # Create scrollable canvas for the entire page
        self.canvas = Canvas(self, bg=self.colors['dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Main container with proper padding
        main_container = ttk.Frame(self.scrollable_frame, style="Dark.TFrame")
        main_container.pack(fill=BOTH, expand=True, padx=30, pady=30)
        
        # Create modern sections
        self._create_modern_header(main_container)
        self._create_analytics_dashboard(main_container)
        self._create_smart_filters(main_container)
        self._create_product_view(main_container)
        self._create_floating_actions(main_container)
        
        # Bind mouse wheel to canvas
        self._bind_mousewheel()
    
    def _create_modern_header(self, parent):
        """Create ultra-modern header with glassmorphism"""
        # Header container with glass effect
        header_frame = ttk.Frame(parent, style="GlassCard.TFrame")
        header_frame.pack(fill=X, pady=(0, 30))
        
        # Inner content with padding
        header_content = ttk.Frame(header_frame, style="GlassCard.TFrame")
        header_content.pack(fill=X, padx=30, pady=25)
        
        # Left side - Title and breadcrumb
        left_frame = ttk.Frame(header_content, style="GlassCard.TFrame")
        left_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Breadcrumb
        breadcrumb_frame = ttk.Frame(left_frame, style="GlassCard.TFrame")
        breadcrumb_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(breadcrumb_frame, text="🏠", 
                 font=("Segoe UI Variable", 12),
                 foreground=self.colors['text_muted'],
                 background=self.colors['card_bg']).pack(side=LEFT)
        
        ttk.Label(breadcrumb_frame, text=" / ", 
                 font=("Segoe UI Variable", 12),
                 foreground=self.colors['text_muted'],
                 background=self.colors['card_bg']).pack(side=LEFT)
        
        ttk.Label(breadcrumb_frame, text=_("Inventory"), 
                 font=("Segoe UI Variable", 12, "bold"),
                 foreground=self.colors['primary'],
                 background=self.colors['card_bg']).pack(side=LEFT)
        
        # Main title with modern typography
        title_frame = ttk.Frame(left_frame, style="GlassCard.TFrame")
        title_frame.pack(fill=X)
        
        ttk.Label(title_frame, text="📦", 
                 font=("Segoe UI Variable", 32),
                 foreground=self.colors['primary'],
                 background=self.colors['card_bg']).pack(side=LEFT, padx=(0, 15))
        
        title_text_frame = ttk.Frame(title_frame, style="GlassCard.TFrame")
        title_text_frame.pack(side=LEFT, fill=X, expand=True)
        
        ttk.Label(title_text_frame, text=_("Inventory Management"), 
                 style="ModernHeader.TLabel").pack(anchor=W)
        
        ttk.Label(title_text_frame, text=_("Manage your products, stock levels, and categories"), 
                 style="ModernSubtitle.TLabel").pack(anchor=W)
        
        # Right side - Action buttons
        right_frame = ttk.Frame(header_content, style="GlassCard.TFrame")
        right_frame.pack(side=RIGHT, padx=(30, 0))
        
        # Modern action buttons with icons
        actions_frame = ttk.Frame(right_frame, style="GlassCard.TFrame")
        actions_frame.pack()
        
        ttk.Button(actions_frame, text="🔄 " + _("Refresh"), 
                  bootstyle="info-outline",
                  command=self._refresh_with_animation).pack(pady=(0, 10), fill=X)
        
        ttk.Button(actions_frame, text="➕ " + _("Add Product"), 
                  bootstyle="success",
                  command=self._show_add_product_dialog).pack(pady=(0, 10), fill=X)
        
        ttk.Button(actions_frame, text="📤 " + _("Export"), 
                  bootstyle="warning-outline",
                  command=self._export_inventory).pack(fill=X)
    
    def _create_analytics_dashboard(self, parent):
        """Create modern analytics dashboard with animated cards"""
        # Dashboard container
        dashboard_frame = ttk.Frame(parent, style="GlassCard.TFrame")
        dashboard_frame.pack(fill=X, pady=(0, 30))
        
        # Dashboard header
        dashboard_header = ttk.Frame(dashboard_frame, style="GlassCard.TFrame")
        dashboard_header.pack(fill=X, padx=30, pady=(25, 15))
        
        ttk.Label(dashboard_header, text="📊", 
                 font=("Segoe UI Variable", 20),
                 foreground=self.colors['accent'],
                 background=self.colors['card_bg']).pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(dashboard_header, text=_("Analytics Dashboard"), 
                 style="CardTitle.TLabel").pack(side=LEFT)
        
        # Cards grid
        cards_container = ttk.Frame(dashboard_frame, style="GlassCard.TFrame")
        cards_container.pack(fill=X, padx=30, pady=(0, 25))
        
        # Row 1 - Main metrics
        row1 = ttk.Frame(cards_container, style="GlassCard.TFrame")
        row1.pack(fill=X, pady=(0, 15))
        
        # Total Products Card
        self._create_metric_card(row1, "📦", _("Total Products"), "0", self.colors['primary'], "total_products")
        
        # Total Value Card  
        self._create_metric_card(row1, "💰", _("Inventory Value"), "$0.00", self.colors['success'], "total_value")
        
        # Low Stock Card
        self._create_metric_card(row1, "⚠️", _("Low Stock"), "0", self.colors['warning'], "low_stock")
        
        # Out of Stock Card
        self._create_metric_card(row1, "🚫", _("Out of Stock"), "0", self.colors['danger'], "out_stock")
        
        # Row 2 - Additional metrics
        row2 = ttk.Frame(cards_container, style="GlassCard.TFrame")
        row2.pack(fill=X)
        
        # Categories Card
        self._create_metric_card(row2, "📁", _("Categories"), "0", self.colors['secondary'], "categories")
        
        # Average Price Card
        self._create_metric_card(row2, "💲", _("Avg Price"), "$0.00", self.colors['accent'], "avg_price")
        
        # Stock Turnover Card (placeholder for future feature)
        self._create_metric_card(row2, "🔄", _("Turnover"), "0%", self.colors['primary'], "turnover")
        
        # Performance Score (calculated metric)
        self._create_metric_card(row2, "⭐", _("Performance"), "0%", self.colors['success'], "performance")
    
    def _create_metric_card(self, parent, icon, title, value, color, metric_id):
        """Create a modern metric card with glassmorphism effect"""
        card = ttk.Frame(parent, style="ProductCard.TFrame")
        card.pack(side=LEFT, fill=BOTH, expand=True, padx=10)
        
        # Card content
        content = ttk.Frame(card, style="ProductCard.TFrame")
        content.pack(fill=BOTH, expand=True, padx=25, pady=20)
        
        # Icon
        ttk.Label(content, text=icon, 
                 font=("Segoe UI Variable", 24),
                 foreground=color,
                 background=self.colors['card_bg']).pack(pady=(0, 10))
        
        # Title
        ttk.Label(content, text=title, 
                 font=("Segoe UI Variable", 11),
                 foreground=self.colors['text_muted'],
                 background=self.colors['card_bg']).pack()
        
        # Value - store reference for updates
        value_label = ttk.Label(content, text=value, 
                               font=("Segoe UI Variable", 24, "bold"),
                               foreground=color,
                               background=self.colors['card_bg'])
        value_label.pack(pady=(5, 0))
        
        # Store reference for updates
        setattr(self, f"{metric_id}_label", value_label)
        
        # Add hover effect
        self._add_hover_effect(card, content)
    
    def _create_smart_filters(self, parent):
        """Create modern smart filters section"""
        filters_frame = ttk.Frame(parent, style="GlassCard.TFrame")
        filters_frame.pack(fill=X, pady=(0, 30))
        
        filters_content = ttk.Frame(filters_frame, style="GlassCard.TFrame")
        filters_content.pack(fill=X, padx=30, pady=25)
        
        # Filters header
        header_frame = ttk.Frame(filters_content, style="GlassCard.TFrame")
        header_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(header_frame, text="🔍", 
                 font=("Segoe UI Variable", 18),
                 foreground=self.colors['accent'],
                 background=self.colors['card_bg']).pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(header_frame, text=_("Smart Filters & Search"), 
                 style="CardTitle.TLabel").pack(side=LEFT)
        
        # View mode toggle
        view_toggle = ttk.Frame(header_frame, style="GlassCard.TFrame")
        view_toggle.pack(side=RIGHT)
        
        ttk.Button(view_toggle, text="🔲 " + _("Grid"), 
                  bootstyle="outline",
                  command=lambda: self._set_view_mode("grid")).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(view_toggle, text="📋 " + _("List"), 
                  bootstyle="outline",
                  command=lambda: self._set_view_mode("list")).pack(side=LEFT)
        
        # Main filters row
        main_filters = ttk.Frame(filters_content, style="GlassCard.TFrame")
        main_filters.pack(fill=X, pady=(0, 15))
        
        # Search with modern styling
        search_frame = ttk.Frame(main_filters, style="GlassCard.TFrame")
        search_frame.pack(side=LEFT, fill=X, expand=True, padx=(0, 15))
        
        ttk.Label(search_frame, text="🔍", 
                 font=("Segoe UI Variable", 14),
                 foreground=self.colors['text_muted'],
                 background=self.colors['card_bg']).pack(side=LEFT, padx=(0, 10))
        
        self.search_entry = ttk.Entry(search_frame, 
                                     textvariable=self.search_var,
                                     style="ModernSearch.TEntry",
                                     font=("Segoe UI Variable", 12))
        self.search_entry.pack(side=LEFT, fill=X, expand=True)
        self.search_entry.insert(0, _("Search products..."))
        self.search_entry.bind('<KeyRelease>', self._on_search)
        self.search_entry.bind('<FocusIn>', self._clear_search_placeholder)
        self.search_entry.bind('<FocusOut>', self._restore_search_placeholder)
        
        # Quick filters
        quick_filters = ttk.Frame(main_filters, style="GlassCard.TFrame")
        quick_filters.pack(side=RIGHT)
        
        # Stock status filter
        ttk.Label(quick_filters, text=_("Stock:"), 
                 font=("Segoe UI Variable", 10),
                 foreground=self.colors['text_muted'],
                 background=self.colors['card_bg']).pack(side=LEFT, padx=(0, 5))
        
        stock_combo = ttk.Combobox(quick_filters, 
                                  textvariable=self.stock_filter_var,
                                  values=[_("All"), _("In Stock"), _("Low Stock"), _("Out of Stock")],
                                  state="readonly",
                                  width=12)
        stock_combo.pack(side=LEFT, padx=(0, 15))
        stock_combo.bind('<<ComboboxSelected>>', self._on_stock_filter_change)
        
        # Sort filter
        ttk.Label(quick_filters, text=_("Sort:"), 
                 font=("Segoe UI Variable", 10),
                 foreground=self.colors['text_muted'],
                 background=self.colors['card_bg']).pack(side=LEFT, padx=(0, 5))
        
        sort_combo = ttk.Combobox(quick_filters, 
                                 textvariable=self.sort_var,
                                 values=[_("Name A-Z"), _("Name Z-A"), _("Price Low-High"), _("Price High-Low"), _("Stock Low-High"), _("Stock High-Low")],
                                 state="readonly",
                                 width=15)
        sort_combo.pack(side=LEFT)
        sort_combo.bind('<<ComboboxSelected>>', self._on_sort_change)
        
        # Categories chips
        categories_frame = ttk.Frame(filters_content, style="GlassCard.TFrame")
        categories_frame.pack(fill=X)
        
        ttk.Label(categories_frame, text=_("Categories:"), 
                 font=("Segoe UI Variable", 10),
                 foreground=self.colors['text_muted'],
                 background=self.colors['card_bg']).pack(side=LEFT, padx=(0, 15))
        
        self.categories_chips_frame = ttk.Frame(categories_frame, style="GlassCard.TFrame")
        self.categories_chips_frame.pack(side=LEFT, fill=X, expand=True)
    
    def _create_product_view(self, parent):
        """Create modern product view with both grid and list modes"""
        view_frame = ttk.Frame(parent, style="GlassCard.TFrame")
        view_frame.pack(fill=BOTH, expand=True)
        
        view_content = ttk.Frame(view_frame, style="GlassCard.TFrame")
        view_content.pack(fill=BOTH, expand=True, padx=30, pady=25)
        
        # View header
        view_header = ttk.Frame(view_content, style="GlassCard.TFrame")
        view_header.pack(fill=X, pady=(0, 20))
        
        ttk.Label(view_header, text="📦", 
                 font=("Segoe UI Variable", 18),
                 foreground=self.colors['primary'],
                 background=self.colors['card_bg']).pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(view_header, text=_("Products"), 
                 style="CardTitle.TLabel").pack(side=LEFT)
        
        # Results count
        self.results_label = ttk.Label(view_header, text="", 
                                      font=("Segoe UI Variable", 10),
                                      foreground=self.colors['text_muted'],
                                      background=self.colors['card_bg'])
        self.results_label.pack(side=RIGHT)
        
        # Products container (will switch between grid and list)
        self.products_container = ttk.Frame(view_content, style="GlassCard.TFrame")
        self.products_container.pack(fill=BOTH, expand=True)
        
        # Initialize with grid view
        self._create_grid_view()
        self._create_list_view()
        
        # Show grid by default
        self._set_view_mode("grid")
    
    def _create_grid_view(self):
        """Create modern grid view for products"""
        # Create scrollable grid
        self.grid_canvas = Canvas(self.products_container, bg=self.colors['dark'], highlightthickness=0)
        grid_scrollbar = ttk.Scrollbar(self.products_container, orient=VERTICAL, command=self.grid_canvas.yview)
        
        self.grid_frame = ttk.Frame(self.grid_canvas, style="GlassCard.TFrame")
        self.grid_frame.bind("<Configure>", lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all")))
        
        self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_canvas.configure(yscrollcommand=grid_scrollbar.set)
        
        # Don't pack yet - will be shown when grid mode is selected
        
    def _create_list_view(self):
        """Create modern list view with enhanced treeview"""
        # Create frame for list view
        self.list_frame = ttk.Frame(self.products_container, style="GlassCard.TFrame")
        
        # Modern treeview
        columns = ("id", "name", "category", "stock", "price", "buy_price", "value", "status")
        self.products_tree = ttk.Treeview(self.list_frame, 
                                         columns=columns, 
                                         show="headings",
                                         style="Modern.Treeview")
        
        # Configure columns with modern headers
        headers = {
            "id": ("ID", 60),
            "name": (_("Product Name"), 200),
            "category": (_("Category"), 120),
            "stock": (_("Stock"), 80),
            "price": (_("Sell Price"), 100),
            "buy_price": (_("Buy Price"), 100),
            "value": (_("Total Value"), 120),
            "status": (_("Status"), 100)
        }
        
        for col, (text, width) in headers.items():
            self.products_tree.heading(col, text=text, anchor=W)
            self.products_tree.column(col, width=width, anchor=W if col == "name" else CENTER)
        
        # Scrollbars for list view
        list_v_scroll = ttk.Scrollbar(self.list_frame, orient=VERTICAL, command=self.products_tree.yview)
        list_h_scroll = ttk.Scrollbar(self.list_frame, orient=HORIZONTAL, command=self.products_tree.xview)
        
        self.products_tree.configure(yscrollcommand=list_v_scroll.set, xscrollcommand=list_h_scroll.set)
        
        # Pack list view components
        self.products_tree.pack(side=LEFT, fill=BOTH, expand=True)
        list_v_scroll.pack(side=RIGHT, fill=Y)
        list_h_scroll.pack(side=BOTTOM, fill=X)
        
        # Bind events
        self.products_tree.bind('<Double-1>', self._on_product_double_click)
        self.products_tree.bind('<Button-3>', self._show_context_menu)
    
    def _create_floating_actions(self, parent):
        """Create floating action buttons (modern 2025 style)"""
        # This will be positioned as floating/sticky at the bottom right
        actions_frame = ttk.Frame(parent, style="GlassCard.TFrame")
        actions_frame.pack(side=BOTTOM, anchor=E, padx=30, pady=20)
        
        # Quick action buttons
        ttk.Button(actions_frame, text="➕", 
                  bootstyle="success",
                  command=self._show_add_product_dialog).pack(side=BOTTOM, pady=(0, 10))
        
        ttk.Button(actions_frame, text="✏️", 
                  bootstyle="warning",
                  command=self._edit_selected_product).pack(side=BOTTOM, pady=(0, 10))
        
        ttk.Button(actions_frame, text="🗑️", 
                  bootstyle="danger",
                  command=self._delete_selected_product).pack(side=BOTTOM)
    
    # Additional methods for modern functionality
    
    def _setup_animations(self):
        """Setup smooth animations for modern feel"""
        # Placeholder for animation setup
        pass
    
    def _add_hover_effect(self, widget, content_widget):
        """Add modern hover effects to cards"""
        def on_enter(e):
            widget.configure(style="GlassCard.TFrame")  # Enhanced hover style would go here
            
        def on_leave(e):
            widget.configure(style="ProductCard.TFrame")
            
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        content_widget.bind("<Enter>", on_enter)
        content_widget.bind("<Leave>", on_leave)
    
    def _refresh_with_animation(self):
        """Refresh data with smooth animation"""
        if not self.animation_running:
            self.animation_running = True
            # Add loading animation here
            self._refresh_all_data()
            # Animation complete
            self.after(1000, lambda: setattr(self, 'animation_running', False))
    
    def _set_view_mode(self, mode):
        """Switch between grid and list view modes"""
        self.view_mode = mode
        
        # Hide all views first
        for widget in self.products_container.winfo_children():
            widget.pack_forget()
        
        if mode == "grid":
            self.grid_canvas.pack(side=LEFT, fill=BOTH, expand=True)
            if hasattr(self, 'grid_scrollbar'):
                self.grid_scrollbar.pack(side=RIGHT, fill=Y)
            self._populate_grid_view()
        else:
            self.list_frame.pack(fill=BOTH, expand=True)
            self._populate_list_view()
    
    def _populate_grid_view(self):
        """Populate the grid view with product cards"""
        # Clear existing cards
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        # Create product cards in grid layout
        row = 0
        col = 0
        max_cols = 4  # Adjust based on screen width
        
        products_data = enhanced_data.get_products()
        if isinstance(products_data, list):
            products_list = products_data
        else:
            products_list = []
        
        for product in products_list:
            if self._should_show_product(product):
                card = self._create_product_card(self.grid_frame, product)
                card.grid(row=row, column=col, padx=15, pady=15, sticky="ew")
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        
        # Configure grid weights
        for i in range(max_cols):
            self.grid_frame.grid_columnconfigure(i, weight=1)
    
    def _populate_list_view(self):
        """Populate the list view with product data"""
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        products_data = enhanced_data.get_products()
        if isinstance(products_data, list):
            products_list = products_data
        else:
            products_list = []
        
        for product in products_list:
            if self._should_show_product(product):
                values = self._format_product_for_list(product)
                self.products_tree.insert('', 'end', values=values)
        
        # Update results count
        count = len(self.products_tree.get_children())
        self.results_label.config(text=f"{count} {_('products found')}")
    
    def _create_product_card(self, parent, product):
        """Create a modern product card for grid view"""
        card = ttk.Frame(parent, style="ProductCard.TFrame")
        
        # Card content
        content = ttk.Frame(card, style="ProductCard.TFrame")
        content.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Product image placeholder
        image_frame = ttk.Frame(content, style="ProductCard.TFrame", height=120)
        image_frame.pack(fill=X, pady=(0, 15))
        image_frame.pack_propagate(False)
        
        ttk.Label(image_frame, text="📦", 
                 font=("Segoe UI Variable", 48),
                 foreground=self.colors['primary'],
                 background=self.colors['card_bg']).pack(expand=True)
        
        # Product name
        ttk.Label(content, text=product.get('Name', ''), 
                 font=("Segoe UI Variable", 14, "bold"),
                 foreground=self.colors['text'],
                 background=self.colors['card_bg']).pack(pady=(0, 5))
        
        # Category
        ttk.Label(content, text=product.get('Category', ''), 
                 font=("Segoe UI Variable", 10),
                 foreground=self.colors['text_muted'],
                 background=self.colors['card_bg']).pack(pady=(0, 10))
        
        # Price and stock info
        info_frame = ttk.Frame(content, style="ProductCard.TFrame")
        info_frame.pack(fill=X, pady=(0, 15))
        
        # Price
        price = float(product.get('SellingPrice', 0))
        ttk.Label(info_frame, text=f"${price:.2f}", 
                 font=("Segoe UI Variable", 16, "bold"),
                 foreground=self.colors['success'],
                 background=self.colors['card_bg']).pack(side=LEFT)
        
        # Stock
        stock = int(product.get('Stock', 0))
        stock_color = self.colors['success'] if stock > 5 else self.colors['warning'] if stock > 0 else self.colors['danger']
        stock_text = f"Stock: {stock}"
        
        ttk.Label(info_frame, text=stock_text, 
                 font=("Segoe UI Variable", 10),
                 foreground=stock_color,
                 background=self.colors['card_bg']).pack(side=RIGHT)
        
        # Action buttons
        actions_frame = ttk.Frame(content, style="ProductCard.TFrame")
        actions_frame.pack(fill=X)
        
        ttk.Button(actions_frame, text=_("Edit"), 
                  bootstyle="outline",
                  command=lambda p=product: self._edit_product(p)).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(actions_frame, text=_("Delete"), 
                  bootstyle="danger-outline",
                  command=lambda p=product: self._delete_product(p)).pack(side=RIGHT)
        
        return card
    
    def _format_product_for_list(self, product):
        """Format product data for list view"""
        stock = int(product.get('Stock', 0))
        sell_price = float(product.get('SellingPrice', 0))
        buy_price = float(product.get('BuyingPrice', 0))
        total_value = sell_price * stock
        
        # Status based on stock level
        if stock == 0:
            status = "🚫 Out of Stock"
        elif stock <= 5:
            status = "⚠️ Low Stock"
        else:
            status = "✅ In Stock"
        
        return (
            product.get('ProductID', ''),
            product.get('Name', ''),
            product.get('Category', ''),
            stock,
            f"${sell_price:.2f}",
            f"${buy_price:.2f}",
            f"${total_value:.2f}",
            status
        )
    
    def _bind_mousewheel(self):
        """Bind mouse wheel scrolling to canvas"""
        def _on_mousewheel(event):
            if self.view_mode == "grid":
                self.grid_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.bind_all("<MouseWheel>", _on_mousewheel)
    
    # Placeholder methods for functionality (to be implemented)
    def _on_search(self, event=None):
        """Handle search input"""
        self.current_search = self.search_var.get()
        if self.current_search != _("Search products..."):
            self._refresh_products_view()
    
    def _clear_search_placeholder(self, event):
        """Clear search placeholder on focus"""
        if self.search_entry.get() == _("Search products..."):
            self.search_entry.delete(0, END)
    
    def _restore_search_placeholder(self, event):
        """Restore search placeholder on focus out"""
        if not self.search_entry.get():
            self.search_entry.insert(0, _("Search products..."))
    
    def _on_stock_filter_change(self, event=None):
        """Handle stock filter change"""
        self._refresh_products_view()
    
    def _on_sort_change(self, event=None):
        """Handle sort change"""
        self._refresh_products_view()
    
    def _refresh_products_view(self):
        """Refresh the products view based on current filters"""
        if self.view_mode == "grid":
            self._populate_grid_view()
        else:
            self._populate_list_view()
    
    def _should_show_product(self, product):
        """Check if product should be shown based on current filters"""
        # Search filter
        search_term = self.current_search.lower() if self.current_search and self.current_search != _("Search products...") else ""
        if search_term:
            if (search_term not in product.get('Name', '').lower() and
                search_term not in product.get('Category', '').lower()):
                return False
        
        # Stock filter
        stock_filter = self.stock_filter_var.get()
        stock = int(product.get('Stock', 0))
        
        if stock_filter == _("In Stock") and stock <= 0:
            return False
        elif stock_filter == _("Low Stock") and (stock > 5 or stock <= 0):
            return False
        elif stock_filter == _("Out of Stock") and stock > 0:
            return False
        
        return True
    
    # Data loading methods (using the fixed data access)
    def _load_initial_data(self):
        """Load initial data for the page"""
        self._load_statistics()
        self._load_categories()
        self._load_products()
    
    def _load_statistics(self):
        """Load and display inventory statistics"""
        try:
            products_data = enhanced_data.get_products()
            products_list = products_data if isinstance(products_data, list) else []
            
            if products_list:
                # Calculate metrics
                total_products = len(products_list)
                total_value = sum(float(p.get('SellingPrice', 0)) * int(p.get('Stock', 0)) for p in products_list)
                low_stock = sum(1 for p in products_list if 0 < int(p.get('Stock', 0)) <= 5)
                out_stock = sum(1 for p in products_list if int(p.get('Stock', 0)) == 0)
                categories = len(set(p.get('Category', '') for p in products_list))
                avg_price = sum(float(p.get('SellingPrice', 0)) for p in products_list) / total_products if total_products > 0 else 0
                
                # Performance score (example calculation)
                performance = max(0, min(100, (total_products * 10) - (out_stock * 5) - (low_stock * 2)))
                
                # Update labels
                self.total_products_label.config(text=str(total_products))
                self.total_value_label.config(text=f"${total_value:.2f}")
                self.low_stock_label.config(text=str(low_stock))
                self.out_stock_label.config(text=str(out_stock))
                self.categories_label.config(text=str(categories))
                self.avg_price_label.config(text=f"${avg_price:.2f}")
                self.turnover_label.config(text="85%")  # Placeholder
                self.performance_label.config(text=f"{performance:.0f}%")
                
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
    
    def _load_categories(self):
        """Load and display category chips"""
        # Clear existing chips
        for widget in self.categories_chips_frame.winfo_children():
            widget.destroy()
        
        try:
            products_data = enhanced_data.get_products()
            products_list = products_data if isinstance(products_data, list) else []
            
            categories = set(p.get('Category', '') for p in products_list if p.get('Category'))
            categories.add("All")  # Add "All" option
            
            for category in sorted(categories):
                chip = ttk.Button(self.categories_chips_frame, 
                                 text=category,
                                 bootstyle="outline" if category != self.current_category else "primary",
                                 command=lambda c=category: self._set_category_filter(c))
                chip.pack(side=LEFT, padx=(0, 10))
                
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
    
    def _load_products(self):
        """Load and display products"""
        self._refresh_products_view()
    
    def _set_category_filter(self, category):
        """Set category filter"""
        self.current_category = category
        self._load_categories()  # Refresh to show active state
        self._refresh_products_view()
    
    def _refresh_all_data(self):
        """Refresh all data"""
        self._load_statistics()
        self._load_categories()
        self._load_products()
        invalidate_cache()
    
    def refresh_data(self):
        """Public method to refresh data"""
        self._refresh_all_data()
    
    def load_data(self):
        """Public method to load data"""
        self._refresh_all_data()
    
    def refresh(self):
        """Called when page is shown"""
        self._refresh_all_data()
    
    def prepare_for_display(self):
        """Called before page is displayed"""
        self._refresh_all_data()
    
    # Placeholder methods for CRUD operations
    def _show_add_product_dialog(self):
        """Show add product dialog"""
        messagebox.showinfo(_("Add Product"), _("Add product dialog would open here"))
    
    def _edit_product(self, product):
        """Edit product"""
        messagebox.showinfo(_("Edit Product"), f"Edit {product.get('Name', '')} dialog would open here")
    
    def _edit_selected_product(self):
        """Edit selected product from list"""
        if self.view_mode == "list":
            selection = self.products_tree.selection()
            if selection:
                messagebox.showinfo(_("Edit Product"), _("Edit selected product dialog would open here"))
            else:
                messagebox.showwarning(_("Warning"), _("Please select a product to edit"))
    
    def _delete_product(self, product):
        """Delete product"""
        if messagebox.askyesno(_("Confirm Delete"), f"Delete {product.get('Name', '')}?"):
            messagebox.showinfo(_("Delete"), _("Product would be deleted here"))
    
    def _delete_selected_product(self):
        """Delete selected product from list"""
        if self.view_mode == "list":
            selection = self.products_tree.selection()
            if selection:
                if messagebox.askyesno(_("Confirm Delete"), _("Delete selected product?")):
                    messagebox.showinfo(_("Delete"), _("Product would be deleted here"))
            else:
                messagebox.showwarning(_("Warning"), _("Please select a product to delete"))
    
    def _export_inventory(self):
        """Export inventory data"""
        messagebox.showinfo(_("Export"), _("Export functionality would be implemented here"))
    
    def _on_product_double_click(self, event):
        """Handle double click on product"""
        selection = self.products_tree.selection()
        if selection:
            messagebox.showinfo(_("Product Details"), _("Product details dialog would open here"))
    
    def _show_context_menu(self, event):
        """Show context menu for products"""
        # Create context menu
        context_menu = ttk.Menu(self, tearoff=0)
        context_menu.add_command(label=_("View Details"), command=self._on_product_double_click)
        context_menu.add_command(label=_("Edit Product"), command=self._edit_selected_product)
        context_menu.add_separator()
        context_menu.add_command(label=_("Delete Product"), command=self._delete_selected_product)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _retranslate(self):
        """Update text for language changes"""
        # This would update all text when language changes
        pass
    
    def __del__(self):
        """Cleanup when page is destroyed"""
        try:
            unregister_refresh_callback(self._retranslate)
        except:
            pass

# For backwards compatibility, create an alias
EnhancedInventoryPage = ModernInventoryPage2025
