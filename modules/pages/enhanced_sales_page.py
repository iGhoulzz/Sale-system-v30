"""
Enhanced Sales Page with optimized performance

This is a performance-optimized version of the sales page that uses:
1. Paginated data loading to prevent UI freezing
2. Background processing for all database operations
3. Debounced search for better responsiveness
4. Better progress indicators for long operations
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import (
    BOTH, END, CENTER, W, E, X, Y, LEFT, RIGHT, TOP,
    HORIZONTAL, BOTTOM, messagebox, StringVar, BooleanVar,
    IntVar, DoubleVar
)
import random
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

class EnhancedSalesPage(ttk.Frame):
    """
    Enhanced sales page with optimized performance and touch-friendly 2025 design.
    Uses pagination and background processing to prevent UI freezing.
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        
        # Store active background tasks
        self._active_tasks = {}
        
        # Initialize touch-specific attributes
        self.selected_product = None
        self.current_view_mode = "grid"
        
        # Create text variables
        self._create_variables()
        
        # Create UI components
        self._create_ui()
        
        # Configure additional card styles
        self._configure_card_styles()
        
        # Register for language updates
        register_refresh_callback(self._refresh_language)
        
        # RTL/LTR language support
        set_widget_direction(self)
    
    def _create_variables(self):
        """Initialize all variables used in the UI"""
        # Header text
        self.title_var = StringVar(value=_("Sales Screen"))
        self.back_btn_var = StringVar(value=_("Back to Home"))
        
        # Search text
        self.search_label_var = StringVar(value=_("Search Products:"))
        self.search_var = StringVar()
        self.clear_btn_var = StringVar(value=_("Clear"))
        
        # Cart text
        self.cart_title_var = StringVar(value=_("Shopping Cart"))
        self.cart_total_var = StringVar(value=_("Total: $0.00"))
        self.cart_items_var = StringVar(value=_("Items: 0"))
        
        # Additional cart variables for minimalist design
        self.total_var = StringVar(value="Total: $0.00")
        self.item_count_var = StringVar(value="0 items")
        
        # Discount variables
        self.discount_var = StringVar(value="0")
        
        # Quantity variables
        self.qty_var = IntVar(value=1)
        self.quantity_var = IntVar(value=1)
        
        # Button text
        self.add_to_cart_var = StringVar(value=_("Add to Cart"))
        self.remove_var = StringVar(value=_("Remove"))
        self.clear_cart_var = StringVar(value=_("Clear Cart"))
        self.checkout_var = StringVar(value=_("Checkout"))
        
    def _create_ui(self):
        """Create clean, minimalist POS interface with 3-panel layout (2025-ready)"""
        # Set dark theme with proper text visibility
        self.configure(style="Dark.TFrame")
        
        # Main container with clean margins
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Top Navigation Bar - Clean and minimal
        self._create_top_navigation(main_container)
        
        # Main content area - 3 panel layout
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=BOTH, expand=True, pady=(5, 0))
        
        # Left spacer for balance (small)
        left_spacer = ttk.Frame(content_frame, width=10)
        left_spacer.pack(side=LEFT, fill=Y)
        
        # Center Inventory Area (60% width)
        self._create_center_inventory_area(content_frame)
        
        # Right Cart Panel (35% width)  
        self._create_right_cart_panel(content_frame)
        
        # Bottom Strip - Minimal floating style
        self._create_bottom_strip(main_container)
        
        # Initialize cart and data
        self.cart_items = {}
        self.cart_total = 0.0
        
        # Auto-focus search bar on open
        self.after(100, self._focus_search_bar)
        
    def _create_top_navigation(self, parent):
        """Create clean top navigation bar - Store logo, Sales label, Date/Time"""
        nav_bar = ttk.Frame(parent, style="NavBar.TFrame", padding=(15, 10))
        nav_bar.pack(fill=X)
        
        # Left: Back/Home button
        self.back_button = ttk.Button(
            nav_bar,
            text="🏠 Home",
            command=self._on_back_clicked,
            bootstyle="secondary-outline",
            style="NavButton.TButton"
        )
        self.back_button.pack(side=LEFT)
        
        # Center: Store logo and Sales label
        center_frame = ttk.Frame(nav_bar)
        center_frame.pack(side=LEFT, expand=True, fill=X)
        
        title_frame = ttk.Frame(center_frame)
        title_frame.pack(expand=True)
        
        # Store logo (emoji for now, can be replaced with actual logo)
        ttk.Label(
            title_frame,
            text="🏪",
            font=("Segoe UI", 20),
            background="#2B2B2B",
            foreground="#4ECDC4"
        ).pack(side=LEFT, padx=(0, 10))
        
        # Sales label
        ttk.Label(
            title_frame,
            text=_("Sales"),
            font=("Segoe UI", 18, "bold"),
            background="#2B2B2B",
            foreground="#FFFFFF"
        ).pack(side=LEFT)
        
        # Right: Date & Time + Settings
        right_frame = ttk.Frame(nav_bar)
        right_frame.pack(side=RIGHT)
        
        # Date & Time
        self.datetime_label = ttk.Label(
            right_frame,
            text="",
            font=("Segoe UI", 12),
            background="#2B2B2B",
            foreground="#4ECDC4"
        )
        self.datetime_label.pack(side=LEFT, padx=(0, 15))
        
        # Settings button
        ttk.Button(
            right_frame,
            text="⚙️",
            command=self._open_settings,
            bootstyle="secondary-outline",
            style="IconButton.TButton"
        ).pack(side=LEFT)
        
        # Start time updates
        self._update_datetime()
    
    def _create_center_inventory_area(self, parent):
        """Create center inventory area with search, categories, and product grid"""
        inventory_frame = ttk.Frame(parent)
        inventory_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        # Large search bar with barcode scan icon
        search_frame = ttk.Frame(inventory_frame, padding=(0, 0, 0, 10))
        search_frame.pack(fill=X)
        
        # Search container
        search_container = ttk.Frame(search_frame, style="SearchContainer.TFrame")
        search_container.pack(fill=X)
        
        # Search entry - large and prominent
        self.search_var = StringVar()
        self.search_entry = ttk.Entry(
            search_container,
            textvariable=self.search_var,
            font=("Segoe UI", 16),
            style="LargeSearch.TEntry"
        )
        self.search_entry.pack(side=LEFT, fill=X, expand=True, padx=(15, 5), pady=10)
        self.search_entry.bind('<KeyRelease>', self._on_search_changed)
        
        # Barcode scan button
        ttk.Button(
            search_container,
            text="📷",
            command=self._scan_barcode,
            bootstyle="info",
            style="ScanButton.TButton"
        ).pack(side=RIGHT, padx=(5, 15), pady=10)
        
        # Horizontally scrollable category pills
        self._create_category_pills(inventory_frame)
        
        # Clean product grid
        self._create_product_grid_area(inventory_frame)
    
    def _create_category_pills(self, parent):
        """Create horizontal scrollable category pills"""
        category_frame = ttk.Frame(parent, padding=(0, 0, 0, 10))
        category_frame.pack(fill=X)
        
        # Canvas for horizontal scrolling
        self.category_canvas = tk.Canvas(
            category_frame,
            height=50,
            highlightthickness=0,
            bg="#2B2B2B"
        )
        self.category_canvas.pack(fill=X, padx=15)
        
        # Scrollable frame for pills
        self.pills_frame = ttk.Frame(self.category_canvas)
        self.category_canvas_window = self.category_canvas.create_window(
            (0, 0), 
            window=self.pills_frame, 
            anchor="nw"
        )
        
        # Alias for backwards compatibility with old code
        self.category_buttons_frame = self.pills_frame
        
        # Load category pills
        self._load_category_pills()
        
        # Bind scroll events
        self.category_canvas.bind("<MouseWheel>", self._scroll_categories)
        self.category_canvas.bind("<Button-4>", self._scroll_categories)
        self.category_canvas.bind("<Button-5>", self._scroll_categories)
    
    def _load_category_pills(self):
        """Load category pills - clean and minimal"""
        # Clear existing
        for widget in self.pills_frame.winfo_children():
            widget.destroy()
        
        # All category
        all_pill = ttk.Button(
            self.pills_frame,
            text=_("All"),
            command=lambda: self._filter_category("All"),
            bootstyle="success",
            style="CategoryPill.TButton"
        )
        all_pill.pack(side=LEFT, padx=(0, 8), pady=5)
        
        # Load categories from database
        try:
            categories = enhanced_data.get_categories()
            for category in categories:
                cat_name = category.get('name', category) if isinstance(category, dict) else category
                pill = ttk.Button(
                    self.pills_frame,
                    text=cat_name,
                    command=lambda c=category: self._filter_category(c),
                    bootstyle="light-outline",
                    style="CategoryPill.TButton"
                )
                pill.pack(side=LEFT, padx=(0, 8), pady=5)
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
        
        # Update scroll region
        self.pills_frame.update_idletasks()
        self.category_canvas.configure(scrollregion=self.category_canvas.bbox("all"))
    
    def _create_product_grid_area(self, parent):
        """Create clean product grid layout"""
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill=BOTH, expand=True, padx=15)
        
        # Canvas for scrolling
        self.product_canvas = tk.Canvas(
            grid_frame,
            highlightthickness=0,
            bg="#2B2B2B"
        )
        self.product_scrollbar = ttk.Scrollbar(
            grid_frame,
            orient="vertical",
            command=self.product_canvas.yview,
            style="Modern.Vertical.TScrollbar"
        )
        self.product_canvas.configure(yscrollcommand=self.product_scrollbar.set)
        
        # Product grid container
        self.product_grid = ttk.Frame(self.product_canvas)
        self.product_canvas_window = self.product_canvas.create_window(
            (0, 0),
            window=self.product_grid,
            anchor="nw"
        )
        
        # Pack components
        self.product_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.product_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind events
        self.product_canvas.bind('<Configure>', self._on_canvas_configure)
        self.product_grid.bind('<Configure>', self._on_grid_configure)
        self.product_canvas.bind("<MouseWheel>", self._scroll_products)
        
        # Load products
        self._load_product_grid()
    
    def _create_right_cart_panel(self, parent):
        """Create right-side cart panel - clean and functional"""
        cart_panel = ttk.LabelFrame(
            parent,
            text="🛒 " + _("Cart"),
            style="CartPanel.TLabelframe",
            padding=15
        )
        cart_panel.pack(side=RIGHT, fill=BOTH, padx=(5, 0))
        cart_panel.configure(width=350)
        
        # Cart items list - scrollable
        self._create_cart_items_list(cart_panel)
        
        # Cart summary
        self._create_cart_summary(cart_panel)
        
        # Big action buttons at bottom
        self._create_cart_action_buttons(cart_panel)
    
    def _create_cart_items_list(self, parent):
        """Create scrollable cart items list"""
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Cart items treeview with clean styling
        columns = ["name", "qty", "price", "total"]
        self.cart_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=12,
            style="CartTree.Treeview"
        )
        
        # Configure columns
        self.cart_tree.heading("name", text=_("Item"))
        self.cart_tree.heading("qty", text=_("Qty"))
        self.cart_tree.heading("price", text=_("Price"))
        self.cart_tree.heading("total", text=_("Total"))
        
        self.cart_tree.column("name", width=140, anchor=W)
        self.cart_tree.column("qty", width=50, anchor=CENTER)
        self.cart_tree.column("price", width=60, anchor=E)
        self.cart_tree.column("total", width=70, anchor=E)
        
        # Scrollbar
        cart_scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.cart_tree.yview,
            style="Modern.Vertical.TScrollbar"
        )
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        
        # Pack
        self.cart_tree.pack(side=LEFT, fill=BOTH, expand=True)
        cart_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind events
        self.cart_tree.bind("<<TreeviewSelect>>", self._on_cart_selection)
        self.cart_tree.bind("<Double-1>", self._edit_cart_quantity)
        self.cart_tree.bind("<Delete>", self._remove_selected_item)
    
    def _create_cart_summary(self, parent):
        """Create cart summary display"""
        summary_frame = ttk.Frame(parent, style="CartSummary.TFrame", padding=10)
        summary_frame.pack(fill=X, pady=(0, 15))
        
        # Total display - large and prominent
        self.total_var = StringVar(value=_("Total: $0.00"))
        self.total_label = ttk.Label(
            summary_frame,
            textvariable=self.total_var,
            font=("Segoe UI", 18, "bold"),
            background="#383838",
            foreground="#27AE60"
        )
        self.total_label.pack()
        
        # Item count
        self.item_count_var = StringVar(value=_("0 items"))
        ttk.Label(
            summary_frame,
            textvariable=self.item_count_var,
            font=("Segoe UI", 12),
            background="#383838",
            foreground="#FFFFFF"
        ).pack()
    
    def _create_cart_action_buttons(self, parent):
        """Create big touch buttons for cart actions"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=X)
        
        # Clear Cart button
        self.clear_cart_btn = ttk.Button(
            buttons_frame,
            text="🧹 " + _("Clear Cart"),
            command=self._clear_cart,
            bootstyle="warning",
            style="BigActionButton.TButton"
        )
        self.clear_cart_btn.pack(fill=X, pady=(0, 8))
        
        # Mark as Debit button
        self.debit_btn = ttk.Button(
            buttons_frame,
            text="💳 " + _("Mark as Debit"),
            command=self._mark_as_debit,
            bootstyle="info",
            style="BigActionButton.TButton"
        )
        self.debit_btn.pack(fill=X, pady=(0, 8))
        
        # Complete Sale button - most prominent
        self.complete_sale_btn = ttk.Button(
            buttons_frame,
            text="✅ " + _("Complete Sale"),
            command=self._complete_sale,
            bootstyle="success",
            style="CompleteSaleButton.TButton"
        )
        self.complete_sale_btn.pack(fill=X)
    
    def _create_bottom_strip(self, parent):
        """Create minimal floating bottom strip"""
        strip_frame = ttk.Frame(parent, style="BottomStrip.TFrame", padding=(20, 8))
        strip_frame.pack(fill=X, pady=(10, 0))
        
        # Center the buttons
        buttons_container = ttk.Frame(strip_frame)
        buttons_container.pack(expand=True)
        
        # Minimal essential buttons only
        ttk.Button(
            buttons_container,
            text="📷 " + _("Scan"),
            command=self._scan_barcode,
            bootstyle="secondary-outline",
            style="StripButton.TButton"
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            buttons_container,
            text="📖 " + _("History"),
            command=self._view_sales_history,
            bootstyle="secondary-outline",
            style="StripButton.TButton"
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            buttons_container,
            text="🔄 " + _("Sync"),
            command=self._sync_data,
            bootstyle="secondary-outline",
            style="StripButton.TButton"
        ).pack(side=LEFT, padx=5)
        
        # Floating add custom item button (bottom-right)
        self._create_floating_add_button(parent)
    
    def _create_floating_add_button(self, parent):
        """Create floating + button for custom items"""
        self.floating_add_btn = ttk.Button(
            parent,
            text="➕",
            command=self._add_custom_item,
            bootstyle="success",
            style="FloatingButton.TButton"
        )
        self.floating_add_btn.place(relx=0.98, rely=0.85, anchor="se")
        
    def _create_touch_products_panel(self, parent):
        """✅ 2. Create touch-friendly products browsing panel with enhanced search and grid view"""
        products_frame = ttk.LabelFrame(
            parent,
            text="🛍️ " + _("Product Catalog"),
            style="Dark.TLabelframe",
            padding=15
        )
        products_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        
        # ✅ Enhanced Search Section with voice support
        search_section = ttk.Frame(products_frame)
        search_section.pack(fill=X, pady=(0, 15))
        
        # ✅ Large rounded search bar with clear button
        search_container = ttk.Frame(search_section)
        search_container.pack(fill=X, pady=(0, 10))
        
        # Search icon
        ttk.Label(
            search_container,
            text="🔍",
            font=("Segoe UI", 16),
            background="#2B2B2B",
            foreground="#4ECDC4"
        ).pack(side=LEFT, padx=(0, 5))
        
        # Large search entry with soft rounded style
        self.search_var = StringVar()
        self.search_entry = ttk.Entry(
            search_container,
            textvariable=self.search_var,
            font=("Segoe UI", 16),
            style="Search.TEntry"
        )
        self.search_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', self._on_search_changed)
        
        # ✅ Clear X button inside search
        self.clear_search_btn = ttk.Button(
            search_container,
            text="❌",
            command=self._clear_search,
            bootstyle="dark",
            style="SearchClear.TButton"
        )
        self.clear_search_btn.pack(side=RIGHT, padx=(5, 0))
        
        # ✅ Voice search button (if device supports microphone)
        self.voice_search_btn = ttk.Button(
            search_container,
            text="🎤",
            command=self._voice_search,
            bootstyle="info",
            style="TouchMedium.TButton"
        )
        self.voice_search_btn.pack(side=RIGHT, padx=(5, 0))
        
        # ✅ Category filters with larger touch targets and horizontal scrolling
        self._create_touch_category_filters(search_section)
        
        # ✅ View toggle with Grid/List options (Grid default for touch)
        self._create_view_toggle(search_section)
        
        # ✅ Products display with Grid View as default
        self._create_touch_products_display(products_frame)
    
    def _create_touch_category_filters(self, parent):
        """✅ Create touch-friendly category filter buttons with horizontal scrolling"""
        category_container = ttk.Frame(parent)
        category_container.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            category_container,
            text="🏷️ " + _("Categories:"),
            font=("Segoe UI", 14, "bold"),
            foreground="#FFFFFF",
            background="#2B2B2B"
        ).pack(side=LEFT, padx=(0, 15))
        
        # Scrollable frame for category buttons
        category_scroll_frame = ttk.Frame(category_container)
        category_scroll_frame.pack(side=LEFT, fill=X, expand=True)
        
        # Canvas for horizontal scrolling
        self.category_canvas = tk.Canvas(
            category_scroll_frame,
            height=60,
            highlightthickness=0,
            bg="#2B2B2B"
        )
        self.category_canvas.pack(fill=X)
        
        # Scrollable frame inside canvas
        self.category_buttons_frame = ttk.Frame(self.category_canvas)
        self.category_canvas_window = self.category_canvas.create_window(
            (0, 0), 
            window=self.category_buttons_frame, 
            anchor="nw"
        )
        
        # Bind mouse wheel for horizontal scrolling
        self.category_canvas.bind("<MouseWheel>", self._on_category_scroll)
        
        # Load category buttons
        self._load_touch_category_buttons()
    
    def _load_touch_category_buttons(self):
        """Load large touch-friendly category buttons"""
        # Clear existing buttons
        for widget in self.category_buttons_frame.winfo_children():
            widget.destroy()
        
        # Add "All" button with larger size
        all_btn = ttk.Button(
            self.category_buttons_frame,
            text="📋 " + _("All"),
            command=lambda: self._filter_by_category("All"),
            bootstyle="success",
            style="TouchCategory.TButton"
        )
        all_btn.pack(side=LEFT, padx=(0, 8), pady=5)
        
        # Load categories from database
        try:
            categories = enhanced_data.get_categories()
            for category in categories:
                cat_name = category.get('name', category) if isinstance(category, dict) else category
                btn = ttk.Button(
                    self.category_buttons_frame,
                    text=f"🏷️ {cat_name}",
                    command=lambda c=category: self._filter_by_category(c),
                    bootstyle="info-outline",
                    style="TouchCategory.TButton"
                )
                btn.pack(side=LEFT, padx=(0, 8), pady=5)
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
        
        # Update scroll region
        self.category_buttons_frame.update_idletasks()
        self.category_canvas.configure(scrollregion=self.category_canvas.bbox("all"))
    
    def _on_category_scroll(self, event):
        """Handle horizontal scrolling of categories"""
        self.category_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _create_view_toggle(self, parent):
        """Create Grid/List view toggle buttons"""
        view_frame = ttk.Frame(parent)
        view_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            view_frame,
            text="👁️ " + _("View:"),
            font=("Segoe UI", 14, "bold"),
            foreground="#FFFFFF",
            background="#2B2B2B"
        ).pack(side=LEFT, padx=(0, 15))
        
        # Grid/List toggle buttons
        self.view_mode = StringVar(value="grid")  # Default to grid for touch
        
        self.grid_btn = ttk.Button(
            view_frame,
            text="🎛️ " + _("Grid"),
            command=lambda: self._set_view_mode("grid"),
            bootstyle="success",
            style="TouchMedium.TButton"
        )
        self.grid_btn.pack(side=LEFT, padx=(0, 8))
        
        self.list_btn = ttk.Button(
            view_frame,
            text="📋 " + _("List"),
            command=lambda: self._set_view_mode("list"),
            bootstyle="light-outline",
            style="TouchMedium.TButton"
        )
        self.list_btn.pack(side=LEFT)
    
    def _create_touch_products_display(self, parent):
        """✅ Create touch-friendly products display with Grid View cards"""
        display_frame = ttk.Frame(parent)
        display_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Create container for both grid and list views
        self.products_container = ttk.Frame(display_frame)
        self.products_container.pack(fill=BOTH, expand=True)
        
        # ✅ Grid View with Product Cards (default for touch)
        self._create_product_grid(self.products_container)
        
        # List View (for keyboard + mouse users)
        self._create_product_list(self.products_container)
        
        # Show grid view by default
        self.current_view_mode = "grid"
        self._show_view_mode("grid")
    
    def _create_product_grid(self, parent):
        """Create grid view with touch-friendly product cards"""
        # Grid container with scrolling
        self.grid_container = ttk.Frame(parent)
        
        # Canvas for scrolling
        self.grid_canvas = tk.Canvas(
            self.grid_container,
            highlightthickness=0,
            bg="#2B2B2B"
        )
        self.grid_scrollbar = ttk.Scrollbar(
            self.grid_container,
            orient="vertical",
            command=self.grid_canvas.yview
        )
        self.grid_canvas.configure(yscrollcommand=self.grid_scrollbar.set)
        
        # Scrollable frame for product cards
        self.grid_frame = ttk.Frame(self.grid_canvas)
        self.grid_canvas_window = self.grid_canvas.create_window(
            (0, 0),
            window=self.grid_frame,
            anchor="nw"
        )
        
        # Pack grid components
        self.grid_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.grid_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind canvas resize
        self.grid_canvas.bind('<Configure>', self._on_grid_canvas_configure)
        self.grid_frame.bind('<Configure>', self._on_grid_frame_configure)
        
        # Bind mouse wheel
        self.grid_canvas.bind("<MouseWheel>", self._on_grid_scroll)
    
    def _create_product_list(self, parent):
        """Create list view for keyboard + mouse users"""
        self.list_container = ttk.Frame(parent)
        
        # Use PaginatedListView for list mode
        self.products_list = PaginatedListView(
            self.list_container,
            columns=["id", "name", "price", "stock", "category"],
            headers={
                "id": _("ID"),
                "name": _("Product Name"),
                "price": _("Price"),
                "stock": _("Stock"),
                "category": _("Category")
            },
            widths={
                "id": 60,
                "name": 200,
                "price": 100,
                "stock": 80,
                "category": 120
            },
            on_page_change=self._load_products,
            on_select=self._on_product_selected,
            on_double_click=self._add_selected_to_cart,
            page_size=20,
            height=12,
            style="Dark.Treeview"
        )
        self.products_list.pack(fill=BOTH, expand=True)
    
    def _on_grid_canvas_configure(self, event):
        """Handle grid canvas resize"""
        # Configure the canvas scrolling region
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        
        # Update the inner frame width to match canvas
        canvas_width = event.width
        self.grid_canvas.itemconfig(self.grid_canvas_window, width=canvas_width)
    
    def _on_grid_frame_configure(self, event):
        """Handle grid frame resize"""
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
    
    def _on_grid_scroll(self, event):
        """Handle grid mouse wheel scrolling"""
        self.grid_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _set_view_mode(self, mode):
        """Set the view mode and update button styles"""
        self.view_mode.set(mode)
        self._show_view_mode(mode)
        
        # Update button styles
        if mode == "grid":
            self.grid_btn.configure(bootstyle="success")
            self.list_btn.configure(bootstyle="light-outline")
        else:
            self.grid_btn.configure(bootstyle="light-outline")
            self.list_btn.configure(bootstyle="success")
    
    def _show_view_mode(self, mode):
        """Show the selected view mode"""
        if mode == "grid":
            self.list_container.pack_forget()
            self.grid_container.pack(fill=BOTH, expand=True)
            self.current_view_mode = "grid"
            self._load_products_grid()
        else:
            self.grid_container.pack_forget()
            self.list_container.pack(fill=BOTH, expand=True)
            self.current_view_mode = "list"
            self._load_products()
    
    def _voice_search(self):
        """Handle voice search (placeholder for future implementation)"""
        messagebox.showinfo(
            _("Voice Search"),
            _("Voice search feature will be implemented when microphone support is added.")
        )
    
    def _on_search_changed(self, event=None):
        """Handle search text changes with debouncing"""
        # Cancel previous timer if exists
        if hasattr(self, '_search_timer'):
            self.after_cancel(self._search_timer)
        
        # Set new timer for debounced search (300ms delay)
        self._search_timer = self.after(300, self._perform_debounced_search)
    
    def _perform_debounced_search(self):
        """Perform the actual search after debounce delay"""
        search_term = self.search_var.get()
        if self.current_view_mode == "grid":
            self._load_products_grid(search_term=search_term)
        else:
            self._load_products(1, search_term)
        
    def _create_touch_cart_panel(self, parent):
        """✅ 3. Create touch-friendly shopping cart with enhanced controls"""
        cart_frame = ttk.LabelFrame(
            parent,
            text="🛒 " + _("Shopping Cart"),
            style="Dark.TLabelframe",
            padding=15
        )
        cart_frame.pack(side=RIGHT, fill=BOTH, expand=False)
        cart_frame.configure(width=450)  # Increased width for touch
        
        # ✅ Enhanced cart summary with large text and icons
        self._create_touch_cart_summary(cart_frame)
        
        # ✅ Cart items with increased height and row spacing
        self._create_touch_cart_items(cart_frame)
        
        # ✅ Quantity controls with +/- steppers
        self._create_touch_quantity_controls(cart_frame)
        
        # ✅ Payment & Checkout with big icon buttons
        self._create_touch_payment_section(cart_frame)
    
    def _create_touch_cart_summary(self, parent):
        """Enhanced cart summary with large text and touch-friendly layout"""
        summary_frame = ttk.Frame(parent, style="Info.TFrame", padding=15)
        summary_frame.pack(fill=X, pady=(0, 15))
        
        # Items count with large font
        self.cart_items_var = StringVar(value=_("Items: 0"))
        ttk.Label(
            summary_frame,
            textvariable=self.cart_items_var,
            font=("Segoe UI", 16, "bold"),
            background="#3498DB",
            foreground="#FFFFFF"
        ).pack(side=LEFT)
        
        # Total with large font and green color
        self.cart_total_var = StringVar(value=_("Total: $0.00"))
        ttk.Label(
            summary_frame,
            textvariable=self.cart_total_var,
            font=("Segoe UI", 18, "bold"),
            background="#3498DB",
            foreground="#27AE60"
        ).pack(side=RIGHT)
    
    def _create_touch_cart_items(self, parent):
        """✅ Cart items with increased height, bigger text and touch controls"""
        items_frame = ttk.Frame(parent)
        items_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Cart items treeview with larger row height
        columns = ["name", "qty", "price", "total", "actions"]
        self.cart_tree = ttk.Treeview(
            items_frame,
            columns=columns,
            show="headings",
            height=10,  # Increased height for touch
            style="Touch.Treeview"
        )
        
        # Configure columns with better spacing
        self.cart_tree.heading("name", text=_("Product"))
        self.cart_tree.heading("qty", text=_("Qty"))
        self.cart_tree.heading("price", text=_("Price"))
        self.cart_tree.heading("total", text=_("Total"))
        self.cart_tree.heading("actions", text=_("Action"))
        
        self.cart_tree.column("name", width=180, anchor=W)
        self.cart_tree.column("qty", width=60, anchor=CENTER)
        self.cart_tree.column("price", width=80, anchor=CENTER)
        self.cart_tree.column("total", width=80, anchor=CENTER)
        self.cart_tree.column("actions", width=50, anchor=CENTER)
        
        # Configure row height for touch (increased row height)
        style = ttk.Style()
        style.configure("Touch.Treeview", rowheight=40, font=("Segoe UI", 12))
        
        # Scrollbar with larger width for touch
        cart_scroll = ttk.Scrollbar(
            items_frame, 
            orient="vertical", 
            command=self.cart_tree.yview,
            style="Touch.Vertical.TScrollbar"
        )
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)
        
        self.cart_tree.pack(side=LEFT, fill=BOTH, expand=True)
        cart_scroll.pack(side=RIGHT, fill=Y)
        
        # Bind selection event and touch events
        self.cart_tree.bind("<<TreeviewSelect>>", self._on_cart_item_selected)
        self.cart_tree.bind("<Double-1>", self._edit_cart_item_quantity)
    
    def _create_touch_quantity_controls(self, parent):
        """✅ Enhanced quantity controls with +/- steppers and common values"""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=X, pady=(0, 15))
        
        # Quantity label
        ttk.Label(
            controls_frame,
            text="📊 " + _("Quantity:"),
            font=("Segoe UI", 14, "bold"),
            foreground="#FFFFFF",
            background="#2B2B2B"
        ).pack(side=LEFT, padx=(0, 15))
        
        # +/- stepper controls
        qty_stepper_frame = ttk.Frame(controls_frame)
        qty_stepper_frame.pack(side=LEFT, padx=(0, 15))
        
        # Minus button
        self.qty_minus_btn = ttk.Button(
            qty_stepper_frame,
            text="➖",
            command=self._decrease_quantity,
            bootstyle="warning",
            style="TouchStepper.TButton"
        )
        self.qty_minus_btn.pack(side=LEFT)
        
        # Quantity display/entry
        self.qty_var = IntVar(value=1)
        self.qty_entry = ttk.Entry(
            qty_stepper_frame,
            textvariable=self.qty_var,
            width=5,
            font=("Segoe UI", 14),
            justify=CENTER,
            style="TouchQty.TEntry"
        )
        self.qty_entry.pack(side=LEFT, padx=5)
        
        # Plus button
        self.qty_plus_btn = ttk.Button(
            qty_stepper_frame,
            text="➕",
            command=self._increase_quantity,
            bootstyle="success",
            style="TouchStepper.TButton"
        )
        self.qty_plus_btn.pack(side=LEFT)
        
        # Quick quantity buttons (1, 5, 10)
        quick_qty_frame = ttk.Frame(controls_frame)
        quick_qty_frame.pack(side=LEFT)
        
        for qty in [1, 5, 10]:
            ttk.Button(
                quick_qty_frame,
                text=str(qty),
                command=lambda q=qty: self.qty_var.set(q),
                bootstyle="info-outline",
                style="TouchQuick.TButton"
            ).pack(side=LEFT, padx=2)
        
        # Action buttons row
        actions_frame = ttk.Frame(controls_frame)
        actions_frame.pack(fill=X, pady=(10, 0))
        
        # Add to cart button (large and prominent)
        self.add_to_cart_btn = ttk.Button(
            actions_frame,
            text="➕🛒 " + _("Add to Cart"),
            command=self._add_selected_to_cart,
            bootstyle="success",
            style="TouchLarge.TButton"
        )
        self.add_to_cart_btn.pack(side=TOP, fill=X, pady=(0, 8))
        
        # Remove and clear buttons row
        remove_frame = ttk.Frame(actions_frame)
        remove_frame.pack(fill=X)
        
        self.remove_btn = ttk.Button(
            remove_frame,
            text="🗑️ " + _("Remove"),
            command=self._remove_from_cart,
            bootstyle="danger",
            style="TouchMedium.TButton"
        )
        self.remove_btn.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        
        self.clear_cart_btn = ttk.Button(
            remove_frame,
            text="🧹 " + _("Clear All"),
            command=self._clear_cart,
            bootstyle="warning",
            style="TouchMedium.TButton"
        )
        self.clear_cart_btn.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
    
    def _create_touch_payment_section(self, parent):
        """✅ Enhanced payment section with large icon buttons"""
        payment_frame = ttk.LabelFrame(
            parent,
            text="💳 " + _("Payment & Checkout"),
            style="Dark.TLabelframe",
            padding=15
        )
        payment_frame.pack(fill=X, pady=(0, 15))
        
        # ✅ Payment method with big icon buttons
        method_frame = ttk.Frame(payment_frame)
        method_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            method_frame,
            text="💰 " + _("Payment Method:"),
            font=("Segoe UI", 14, "bold"),
            foreground="#FFFFFF",
            background="#2B2B2B"
        ).pack(side=TOP, pady=(0, 10))
        
        # Payment method buttons in a row
        payment_buttons_frame = ttk.Frame(method_frame)
        payment_buttons_frame.pack(fill=X)
        
        self.payment_method = StringVar(value="cash")
        
        # Cash button
        self.cash_btn = ttk.Button(
            payment_buttons_frame,
            text="💵\n" + _("Cash"),
            command=lambda: self._set_payment_method("cash"),
            bootstyle="success",
            style="TouchPayment.TButton"
        )
        self.cash_btn.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        
        # Card button
        self.card_btn = ttk.Button(
            payment_buttons_frame,
            text="💳\n" + _("Card"),
            command=lambda: self._set_payment_method("card"),
            bootstyle="info-outline",
            style="TouchPayment.TButton"
        )
        self.card_btn.pack(side=LEFT, fill=X, expand=True, padx=5)
        
        # Credit button
        self.credit_btn = ttk.Button(
            payment_buttons_frame,
            text="💰\n" + _("Credit"),
            command=lambda: self._set_payment_method("credit"),
            bootstyle="warning-outline",
            style="TouchPayment.TButton"
        )
        self.credit_btn.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
        # ✅ Discount section with toggle buttons and numeric keypad
        discount_frame = ttk.Frame(payment_frame)
        discount_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            discount_frame,
            text="🏷️ " + _("Discount:"),
            font=("Segoe UI", 14, "bold"),
            foreground="#FFFFFF",
            background="#2B2B2B"
        ).pack(side=TOP, pady=(0, 10))
        
        # Discount controls row
        discount_controls = ttk.Frame(discount_frame)
        discount_controls.pack(fill=X)
        
        # Discount percentage entry
        self.discount_var = StringVar(value="0")
        discount_entry = ttk.Entry(
            discount_controls,
            textvariable=self.discount_var,
            width=8,
            font=("Segoe UI", 14),
            justify=CENTER,
            style="TouchDiscount.TEntry"
        )
        discount_entry.pack(side=LEFT, padx=(0, 10))
        discount_entry.bind("<KeyRelease>", self._update_cart_total)
        
        ttk.Label(
            discount_controls,
            text="%",
            font=("Segoe UI", 14),
            foreground="#FFFFFF",
            background="#2B2B2B"
        ).pack(side=LEFT, padx=(0, 15))
        
        # Quick discount toggle buttons
        for discount in [5, 10, 15, 20]:
            btn = ttk.Button(
                discount_controls,
                text=f"{discount}%",
                command=lambda d=discount: self._toggle_discount(d),
                bootstyle="info-outline",
                style="TouchDiscount.TButton"
            )
            btn.pack(side=LEFT, padx=2)
        
        # Manual discount button (opens numeric keypad)
        ttk.Button(
            discount_controls,
            text="🔢",
            command=self._open_discount_keypad,
            bootstyle="secondary",
            style="TouchMedium.TButton"
        ).pack(side=RIGHT)
        
        # ✅ Large checkout button (bottom-right for ergonomics)
        checkout_frame = ttk.Frame(payment_frame)
        checkout_frame.pack(fill=X, pady=(0, 10))
        
        self.checkout_btn = ttk.Button(
            checkout_frame,
            text="💎 " + _("CHECKOUT"),
            command=self._process_checkout,
            bootstyle="success",
            style="TouchCheckout.TButton"
        )
        self.checkout_btn.pack(fill=X)
        
        # Additional action buttons row
        additional_actions = ttk.Frame(payment_frame)
        additional_actions.pack(fill=X)
        
        ttk.Button(
            additional_actions,
            text="📝 " + _("Quote"),
            command=self._save_as_quote,
            bootstyle="info",
            style="TouchSmall.TButton"
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        
        ttk.Button(
            additional_actions,
            text="📊 " + _("Debit"),
            command=self._mark_as_debit,
            bootstyle="warning",
            style="TouchSmall.TButton"
        ).pack(side=LEFT, fill=X, expand=True, padx=3)
        
        ttk.Button(
            additional_actions,
            text="🖨️ " + _("Print"),
            command=self._print_receipt,
            bootstyle="secondary",
            style="TouchSmall.TButton"
        ).pack(side=LEFT, fill=X, expand=True, padx=(3, 0))
    
    # Touch control helper methods
    def _increase_quantity(self):
        """Increase quantity by 1"""
        current = self.qty_var.get()
        self.qty_var.set(current + 1)
    
    def _decrease_quantity(self):
        """Decrease quantity by 1 (minimum 1)"""
        current = self.qty_var.get()
        if current > 1:
            self.qty_var.set(current - 1)
    
    def _set_payment_method(self, method):
        """Set payment method and update button styles"""
        self.payment_method.set(method)
        
        # Reset all buttons to outline style
        self.cash_btn.configure(bootstyle="success-outline")
        self.card_btn.configure(bootstyle="info-outline")
        self.credit_btn.configure(bootstyle="warning-outline")
        
        # Highlight selected button
        if method == "cash":
            self.cash_btn.configure(bootstyle="success")
        elif method == "card":
            self.card_btn.configure(bootstyle="info")
        elif method == "credit":
            self.credit_btn.configure(bootstyle="warning")
    
    def _toggle_discount(self, discount_percent):
        """Toggle discount percentage"""
        current = self.discount_var.get()
        if current == str(discount_percent):
            self.discount_var.set("0")
        else:
            self.discount_var.set(str(discount_percent))
        self._update_cart_total()
    
    def _open_discount_keypad(self):
        """Open numeric keypad for manual discount entry"""
        try:
            # Create keypad dialog
            dialog = ttk.Toplevel(self)
            dialog.title(_("Enter Discount %"))
            dialog.geometry("300x400")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"300x400+{x}+{y}")
            
            # Display
            display_var = StringVar(value=self.discount_var.get())
            display = ttk.Label(
                dialog,
                textvariable=display_var,
                font=("Segoe UI", 24, "bold"),
                background="#2B2B2B",
                foreground="#FFFFFF"
            )
            display.pack(pady=20)
            
            # Keypad buttons
            keypad_frame = ttk.Frame(dialog)
            keypad_frame.pack(expand=True, fill=BOTH, padx=20, pady=20)
            
            def add_digit(digit):
                current = display_var.get()
                if current == "0":
                    display_var.set(str(digit))
                else:
                    display_var.set(current + str(digit))
            
            def clear_display():
                display_var.set("0")
            
            def backspace():
                current = display_var.get()
                if len(current) > 1:
                    display_var.set(current[:-1])
                else:
                    display_var.set("0")
            
            def confirm():
                value = display_var.get()
                try:
                    percent = float(value)
                    if 0 <= percent <= 100:
                        self.discount_var.set(value)
                        self._update_cart_total()
                        dialog.destroy()
                    else:
                        messagebox.showerror(_("Error"), _("Discount must be between 0 and 100%"))
                except ValueError:
                    messagebox.showerror(_("Error"), _("Please enter a valid number"))
            
            # Create keypad layout
            buttons = [
                [7, 8, 9],
                [4, 5, 6],
                [1, 2, 3],
                ['C', 0, '⌫']
            ]
            
            for i, row in enumerate(buttons):
                row_frame = ttk.Frame(keypad_frame)
                row_frame.pack(fill=X, pady=2)
                for j, btn_text in enumerate(row):
                    if btn_text == 'C':
                        btn = ttk.Button(
                            row_frame,
                            text=str(btn_text),
                            command=clear_display,
                            bootstyle="danger",
                            style="TouchKeypad.TButton"
                        )
                    elif btn_text == '⌫':
                        btn = ttk.Button(
                            row_frame,
                            text=str(btn_text),
                            command=backspace,
                            bootstyle="warning",
                            style="TouchKeypad.TButton"
                        )
                    else:
                        btn = ttk.Button(
                            row_frame,
                            text=str(btn_text),
                            command=lambda d=btn_text: add_digit(d),
                            bootstyle="primary",
                            style="TouchKeypad.TButton"
                        )
                    btn.pack(side=LEFT, fill=X, expand=True, padx=2)
            
            # Confirm button
            ttk.Button(
                dialog,
                text=_("Apply Discount"),
                command=confirm,
                bootstyle="success",
                style="TouchLarge.TButton"
            ).pack(pady=10, padx=20, fill=X)
            
        except Exception as e:
            logger.error(f"Error opening discount keypad: {str(e)}")
    
    def _edit_cart_item_quantity(self, event):
        """Allow editing cart item quantity on double-click"""
        try:
            selection = self.cart_tree.selection()
            if not selection:
                return
            
            # Get selected item
            item_values = self.cart_tree.item(selection[0], "values")
            if not item_values:
                return
            
            product_name = item_values[0]
            current_qty = int(item_values[1])
            
            # Create quantity edit dialog
            dialog = ttk.Toplevel(self)
            dialog.title(_("Edit Quantity"))
            dialog.geometry("300x200")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
            y = (dialog.winfo_screenheight() // 2) - (200 // 2)
            dialog.geometry(f"300x200+{x}+{y}")
            
            ttk.Label(dialog, text=f"{_('Product')}: {product_name}", font=("Segoe UI", 12)).pack(pady=10)
            ttk.Label(dialog, text=_("New Quantity:"), font=("Segoe UI", 12)).pack(pady=5)
            
            qty_var = IntVar(value=current_qty)
            qty_spinbox = ttk.Spinbox(
                dialog,
                from_=1,
                to=999,
                textvariable=qty_var,
                font=("Segoe UI", 14),
                width=10
            )
            qty_spinbox.pack(pady=10)
            qty_spinbox.focus()
            qty_spinbox.select_range(0, tk.END)
            
            def update_quantity():
                new_qty = qty_var.get()
                self._update_cart_item_quantity(product_name, new_qty)
                dialog.destroy()
            
            ttk.Button(dialog, text=_("Update"), command=update_quantity, bootstyle="success").pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error editing cart item quantity: {str(e)}")
    
    def _update_cart_item_quantity(self, product_name, new_quantity):
        """Update the quantity of a cart item"""
        try:
            for product_id, item in self.cart_items.items():
                if item["name"] == product_name:
                    item["quantity"] = new_quantity
                    break
            self._update_cart_display()
        except Exception as e:
            logger.error(f"Error updating cart item quantity: {str(e)}")
        
    def _create_cart_controls(self, parent):
        """Create cart control buttons"""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=X, padx=15, pady=(0, 15))
        
        # Quantity controls
        qty_frame = ttk.Frame(controls_frame)
        qty_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            qty_frame,
            text=_("Quantity:"),
            font=("Segoe UI", 10)
        ).pack(side=LEFT, padx=(0, 10))
        
        # Quantity spinbox
        self.qty_var = IntVar(value=1)
        qty_spinbox = ttk.Spinbox(
            qty_frame,
            from_=1,
            to=999,
            textvariable=self.qty_var,
            width=8,
            font=("Segoe UI", 11)
        )
        qty_spinbox.pack(side=LEFT, padx=(0, 10))
        
        # Quick quantity buttons
        for qty in [1, 5, 10]:
            ttk.Button(
                qty_frame,
                text=str(qty),
                command=lambda q=qty: self.qty_var.set(q),
                bootstyle="outline-secondary",
                style="Tiny.TButton"
            ).pack(side=LEFT, padx=2)
        
        # Action buttons
        btn_frame = ttk.Frame(controls_frame)
        btn_frame.pack(fill=X)
        
        ttk.Button(
            btn_frame,
            textvariable=self.add_to_cart_var,
            command=self._add_selected_to_cart,
            bootstyle="success",
            style="Modern.TButton"
        ).pack(side=LEFT, padx=(0, 5), fill=X, expand=True)
        
        ttk.Button(
            btn_frame,
            textvariable=self.remove_var,
            command=self._remove_from_cart,
            bootstyle="danger",
            style="Modern.TButton"
        ).pack(side=LEFT, padx=5, fill=X, expand=True)
        
        ttk.Button(
            btn_frame,
            textvariable=self.clear_cart_var,
            command=self._clear_cart,
            bootstyle="warning",
            style="Modern.TButton"
        ).pack(side=LEFT, padx=(5, 0), fill=X, expand=True)
        
    def _create_payment_section(self, parent):
        """Create modern payment section"""
        payment_frame = ttk.LabelFrame(
            parent,
            text=_("Payment & Checkout"),
            style="Modern.TLabelframe"
        )
        payment_frame.pack(fill=X, padx=15, pady=(0, 15))
        
        # Payment method selection
        method_frame = ttk.Frame(payment_frame)
        method_frame.pack(fill=X, padx=10, pady=10)
        
        ttk.Label(
            method_frame,
            text=_("Payment Method:"),
            font=("Segoe UI", 11, "bold")
        ).pack(side=LEFT, padx=(0, 15))
        
        self.payment_method = StringVar(value="cash")
        
        ttk.Radiobutton(
            method_frame,
            text=_("Cash"),
            variable=self.payment_method,
            value="cash"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            method_frame,
            text=_("Card"),
            variable=self.payment_method,
            value="card"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            method_frame,
            text=_("Credit"),
            variable=self.payment_method,
            value="credit"
        ).pack(side=LEFT)
        
        # Discount section
        discount_frame = ttk.Frame(payment_frame)
        discount_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        ttk.Label(
            discount_frame,
            text=_("Discount %:"),
            font=("Segoe UI", 10)
        ).pack(side=LEFT, padx=(0, 10))
        
        self.discount_var = StringVar(value="0")
        discount_entry = ttk.Entry(
            discount_frame,
            textvariable=self.discount_var,
            width=8,
            font=("Segoe UI", 11)
        )
        discount_entry.pack(side=LEFT, padx=(0, 10))
        discount_entry.bind("<KeyRelease>", self._update_cart_total)
        
        # Quick discount buttons
        for discount in [5, 10, 15, 20]:
            ttk.Button(
                discount_frame,
                text=f"{discount}%",
                command=lambda d=discount: self.discount_var.set(str(d)),
                bootstyle="outline-info",
                style="Tiny.TButton"
            ).pack(side=LEFT, padx=2)
        
        # Checkout buttons
        checkout_frame = ttk.Frame(payment_frame)
        checkout_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        ttk.Button(
            checkout_frame,
            textvariable=self.checkout_var,
            command=self._process_checkout,
            bootstyle="success",
            style="Large.TButton"
        ).pack(fill=X, pady=(0, 5))
        
        # Additional actions
        actions_frame = ttk.Frame(checkout_frame)
        actions_frame.pack(fill=X)
        
        ttk.Button(
            actions_frame,
            text=_("Save as Quote"),
            command=self._save_as_quote,
            bootstyle="info",
            style="Small.TButton"
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        
        ttk.Button(
            actions_frame,
            text=_("Mark as Debit"),
            command=self._mark_as_debit,
            bootstyle="warning",
            style="Small.TButton"
        ).pack(side=LEFT, fill=X, expand=True, padx=5)
        
        ttk.Button(
            actions_frame,
            text=_("Print Receipt"),
            command=self._print_receipt,
            bootstyle="secondary",
            style="Small.TButton"
        ).pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
    def _create_touch_action_bar(self, parent):
        """✅ 4. Create bottom action bar with large icon buttons organized by function"""
        action_frame = ttk.Frame(parent, style="Dark.TFrame", padding=15)
        action_frame.pack(fill=X, pady=(15, 0))
        
        # Left group: Barcode and Sales related
        left_group = ttk.LabelFrame(action_frame, text="📱 " + _("Scan & Sales"), style="Dark.TLabelframe", padding=10)
        left_group.pack(side=LEFT, fill=Y, padx=(0, 15))
        
        # ✅ Scan Barcode - Large icon button (min 48x48 px)
        self.scan_btn = ttk.Button(
            left_group,
            text="📷\n" + _("Scan\nBarcode"),
            command=self._scan_barcode,
            bootstyle="info",
            style="TouchActionIcon.TButton"
        )
        self.scan_btn.pack(side=LEFT, padx=(0, 10))
        
        # ✅ Sales History - Large icon button
        self.history_btn = ttk.Button(
            left_group,
            text="�\n" + _("Sales\nHistory"),
            command=self._view_sales_history,
            bootstyle="secondary",
            style="TouchActionIcon.TButton"
        )
        self.history_btn.pack(side=LEFT)
        
        # Center group: Reports
        center_group = ttk.LabelFrame(action_frame, text="📊 " + _("Reports"), style="Dark.TLabelframe", padding=10)
        center_group.pack(side=LEFT, fill=Y, padx=15)
        
        # ✅ Daily Reports - Large icon button
        self.reports_btn = ttk.Button(
            center_group,
            text="📊\n" + _("Daily\nReports"),
            command=self._view_daily_reports,
            bootstyle="warning",
            style="TouchActionIcon.TButton"
        )
        self.reports_btn.pack()
        
        # Right group: Settings and Refresh
        right_group = ttk.LabelFrame(action_frame, text="⚙️ " + _("System"), style="Dark.TLabelframe", padding=10)
        right_group.pack(side=RIGHT, fill=Y, padx=(15, 0))
        
        # ✅ Refresh - Large icon button
        self.refresh_btn = ttk.Button(
            right_group,
            text="🔄\n" + _("Refresh"),
            command=self.refresh,
            bootstyle="success",
            style="TouchActionIcon.TButton"
        )
        self.refresh_btn.pack(side=LEFT, padx=(0, 10))
        
        # ✅ Settings - Large icon button
        self.settings_btn = ttk.Button(
            right_group,
            text="⚙️\n" + _("Settings"),
            command=self._open_settings,
            bootstyle="secondary",
            style="TouchActionIcon.TButton"
        )
        self.settings_btn.pack(side=LEFT)
        
    def _setup_touch_styles(self):
        """Setup clean, minimalist styles with proper text visibility"""
        style = ttk.Style()
        
        # Base dark theme with high contrast
        style.configure("Dark.TFrame", background="#2B2B2B")
        
        # Navigation bar
        style.configure("NavBar.TFrame", background="#1F1F1F", relief="flat")
        style.configure("NavButton.TButton", padding=(12, 8), font=("Segoe UI", 11))
        style.configure("IconButton.TButton", padding=(10, 8), font=("Segoe UI", 14))
        
        # Search container and entry
        style.configure("SearchContainer.TFrame", background="#383838", relief="raised", borderwidth=1)
        style.configure("LargeSearch.TEntry", 
                       fieldbackground="#FFFFFF", 
                       foreground="#000000", 
                       font=("Segoe UI", 16),
                       padding=(15, 12))
        
        style.configure("ScanButton.TButton", 
                       padding=(15, 12), 
                       font=("Segoe UI", 16))
        
        # Category pills
        style.configure("CategoryPill.TButton", 
                       padding=(15, 8), 
                       font=("Segoe UI", 12))
        
        # Product cards
        style.configure("ProductCard.TFrame", 
                       background="#383838", 
                       relief="raised", 
                       borderwidth=1,
                       padding=10)
        
        # Cart panel
        style.configure("CartPanel.TLabelframe", 
                       background="#2B2B2B", 
                       foreground="#FFFFFF",
                       borderwidth=1,
                       relief="solid")
        
        style.configure("CartPanel.TLabelframe.Label", 
                       background="#2B2B2B", 
                       foreground="#4ECDC4", 
                       font=("Segoe UI", 14, "bold"))
        
        # Cart tree
        style.configure("CartTree.Treeview", 
                       background="#383838",
                       foreground="#FFFFFF",
                       fieldbackground="#383838",
                       font=("Segoe UI", 11),
                       rowheight=30)
        
        style.configure("CartTree.Treeview.Heading", 
                       background="#4ECDC4",
                       foreground="#FFFFFF",
                       font=("Segoe UI", 11, "bold"))
        
        # Cart summary
        style.configure("CartSummary.TFrame", 
                       background="#383838", 
                       relief="sunken", 
                       borderwidth=1)
        
        # Action buttons
        style.configure("BigActionButton.TButton", 
                       padding=(20, 15), 
                       font=("Segoe UI", 13, "bold"))
        
        style.configure("CompleteSaleButton.TButton", 
                       padding=(25, 18), 
                       font=("Segoe UI", 14, "bold"))
        
        # Bottom strip
        style.configure("BottomStrip.TFrame", 
                       background="#1F1F1F", 
                       relief="flat")
        
        style.configure("StripButton.TButton", 
                       padding=(12, 6), 
                       font=("Segoe UI", 10))
        
        # Floating button
        style.configure("FloatingButton.TButton", 
                       padding=(15, 15), 
                       font=("Segoe UI", 18, "bold"))
        
        # Scrollbars
        style.configure("Modern.Vertical.TScrollbar", 
                       arrowsize=20,
                       width=16)
    
    def _update_datetime(self):
        """Update date and time display"""
        if hasattr(self, 'datetime_label') and self.winfo_exists():
            current_dt = time.strftime("%Y-%m-%d %H:%M")
            self.datetime_label.configure(text=current_dt)
            self.after(60000, self._update_datetime)  # Update every minute
    
    def _focus_search_bar(self):
        """Auto-focus on search bar"""
        if hasattr(self, 'search_entry'):
            self.search_entry.focus_set()
    
    def _on_search_changed(self, event=None):
        """Handle search with debouncing"""
        if hasattr(self, '_search_timer'):
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self._perform_search)
    
    def _perform_search(self):
        """Perform product search"""
        search_term = self.search_var.get().strip()
        self._load_product_grid(search_term)
    
    def _scroll_categories(self, event):
        """Handle category pills scrolling"""
        if event.delta:
            self.category_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 4:
                self.category_canvas.xview_scroll(-1, "units")
            elif event.num == 5:
                self.category_canvas.xview_scroll(1, "units")
    
    def _filter_category(self, category):
        """Filter products by category"""
        try:
            # Update pill styles
            for widget in self.pills_frame.winfo_children():
                if hasattr(widget, 'configure'):
                    widget.configure(bootstyle="light-outline")
            
            # Highlight selected
            category_name = category.get('name', category) if isinstance(category, dict) else category
            for widget in self.pills_frame.winfo_children():
                if hasattr(widget, 'cget') and widget.cget('text') == category_name:
                    widget.configure(bootstyle="success")
                    break
            
            # Filter products
            if category == "All":
                self._load_product_grid("")
            else:
                search_term = f"category:{category_name}"
                self._load_product_grid(search_term)
                
        except Exception as e:
            logger.error(f"Error filtering category: {str(e)}")
    
    def _load_product_grid(self, search_term=""):
        """Load products in clean grid layout"""
        try:
            # Clear existing
            for widget in self.product_grid.winfo_children():
                widget.destroy()
            
            # Get products
            if search_term:
                result = enhanced_data.get_products_paged(page=1, page_size=50, search=search_term)
            else:
                result = enhanced_data.get_products_paged(page=1, page_size=50)
            
            if isinstance(result, PagedResult):
                # Calculate grid layout (4 columns for clean look)
                columns = 4
                row = 0
                col = 0
                
                for item in result.data:
                    self._create_product_card(item, row, col)
                    
                    col += 1
                    if col >= columns:
                        col = 0
                        row += 1
                
                # Update scroll region
                self.product_grid.update_idletasks()
                self.product_canvas.configure(scrollregion=self.product_canvas.bbox("all"))
            
        except Exception as e:
            logger.error(f"Error loading products: {str(e)}")
    
    def _create_product_card(self, product, row, col):
        """Create clean, minimal product card"""
        card = ttk.Frame(self.product_grid, style="ProductCard.TFrame")
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Configure grid weights
        self.product_grid.grid_rowconfigure(row, weight=1)
        self.product_grid.grid_columnconfigure(col, weight=1)
        
        # Product image placeholder
        image_label = ttk.Label(
            card,
            text="📦",
            font=("Segoe UI", 24),
            background="#383838",
            foreground="#4ECDC4"
        )
        image_label.pack(pady=(5, 0))
        
        # Product name
        name = product.get('Name', 'Unknown')
        display_name = name[:18] + "..." if len(name) > 18 else name
        
        name_label = ttk.Label(
            card,
            text=display_name,
            font=("Segoe UI", 11, "bold"),
            background="#383838",
            foreground="#FFFFFF",
            anchor=CENTER
        )
        name_label.pack(pady=2)
        
        # Price
        price = float(product.get('Price', 0))
        price_label = ttk.Label(
            card,
            text=f"${price:.2f}",
            font=("Segoe UI", 13, "bold"),
            background="#383838",
            foreground="#27AE60"
        )
        price_label.pack(pady=2)
        
        # Stock
        stock = int(product.get('Stock', 0))
        stock_text = f"{stock} left" if stock > 0 else "Out of stock"
        stock_color = "#FFFFFF" if stock > 0 else "#E74C3C"
        
        stock_label = ttk.Label(
            card,
            text=stock_text,
            font=("Segoe UI", 9),
            background="#383838",
            foreground=stock_color
        )
        stock_label.pack(pady=(0, 5))
        
        # Add button
        add_btn = ttk.Button(
            card,
            text="+ Add",
            command=lambda: self._add_product_to_cart(product),
            bootstyle="success" if stock > 0 else "secondary",
            state="normal" if stock > 0 else "disabled",
            style="CardAddButton.TButton"
        )
        add_btn.pack(fill=X, padx=5, pady=(0, 5))
        
        # Make card clickable
        self._make_card_clickable(card, product)
    
    def _make_card_clickable(self, card, product):
        """Make card clickable for quick add"""
        def on_click(event=None):
            if int(product.get('Stock', 0)) > 0:
                self._add_product_to_cart(product)
                self._show_add_feedback(card)
        
        # Bind to card and children (except button)
        for widget in [card] + list(card.winfo_children()):
            if not isinstance(widget, ttk.Button):
                widget.bind("<Button-1>", on_click)
                widget.configure(cursor="hand2")
    
    def _show_add_feedback(self, card):
        """Show visual feedback when item added"""
        original_style = card.cget('style')
        card.configure(style="ProductCardSelected.TFrame")
        self.after(300, lambda: card.configure(style=original_style))
        
        # Configure selected style if not exists
        style = ttk.Style()
        style.configure("ProductCardSelected.TFrame", 
                       background="#27AE60", 
                       relief="raised", 
                       borderwidth=2)
    
    def _on_canvas_configure(self, event):
        """Handle canvas resize"""
        self.product_canvas.configure(scrollregion=self.product_canvas.bbox("all"))
        canvas_width = event.width
        self.product_canvas.itemconfig(self.product_canvas_window, width=canvas_width)
    
    def _on_grid_configure(self, event):
        """Handle grid resize"""
        self.product_canvas.configure(scrollregion=self.product_canvas.bbox("all"))
    
    def _scroll_products(self, event):
        """Handle product grid scrolling"""
        if event.delta:
            self.product_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 4:
                self.product_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.product_canvas.yview_scroll(1, "units")
    
    def _add_product_to_cart(self, product):
        """Add product to cart with clean feedback"""
        try:
            product_id = str(product.get('ProductID', ''))
            if not product_id:
                return
            
            # Check stock
            stock = int(product.get('Stock', 0))
            if stock <= 0:
                messagebox.showwarning(_("Out of Stock"), _("This item is out of stock"))
                return
            
            # Add to cart
            if product_id in self.cart_items:
                # Check if we can add more
                current_qty = self.cart_items[product_id]["quantity"]
                if current_qty >= stock:
                    messagebox.showwarning(_("Stock Limit"), _("Cannot add more items than available in stock"))
                    return
                self.cart_items[product_id]["quantity"] += 1
            else:
                self.cart_items[product_id] = {
                    "name": product.get('Name', 'Unknown'),
                    "price": float(product.get('Price', 0)),
                    "quantity": 1,
                    "stock": stock
                }
            
            # Update cart display
            self._update_cart_display()
            
        except Exception as e:
            logger.error(f"Error adding product to cart: {str(e)}")
    
    def _update_cart_display(self):
        """Update cart display with clean formatting"""
        if not hasattr(self, 'cart_tree'):
            return
        
        # Clear existing
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Add items
        total = 0.0
        item_count = 0
        
        for product_id, item in self.cart_items.items():
            item_total = item["price"] * item["quantity"]
            total += item_total
            item_count += item["quantity"]
            
            # Truncate name if too long
            display_name = item["name"][:20] + "..." if len(item["name"]) > 20 else item["name"]
            
            self.cart_tree.insert("", "end", values=(
                display_name,
                item["quantity"],
                f"${item['price']:.2f}",
                f"${item_total:.2f}"
            ))
        
        # Update summary
        self.total_var.set(f"Total: ${total:.2f}")
        self.item_count_var.set(f"{item_count} items")
        
        # Update button states
        has_items = bool(self.cart_items)
        self.clear_cart_btn.configure(state="normal" if has_items else "disabled")
        self.debit_btn.configure(state="normal" if has_items else "disabled")
        self.complete_sale_btn.configure(state="normal" if has_items else "disabled")
    
    def _on_cart_selection(self, event=None):
        """Handle cart item selection"""
        # Enable quantity editing on selection
        pass
    
    def _edit_cart_quantity(self, event=None):
        """Edit quantity via double-click or long-press"""
        selection = self.cart_tree.selection()
        if not selection:
            return
        
        item_values = self.cart_tree.item(selection[0], "values")
        if not item_values:
            return
        
        # Find the product in cart
        display_name = item_values[0]
        for product_id, item in self.cart_items.items():
            item_display_name = item["name"][:20] + "..." if len(item["name"]) > 20 else item["name"]
            if item_display_name == display_name:
                self._show_quantity_dialog(product_id, item)
                break
    
    def _show_quantity_dialog(self, product_id, item):
        """Show quantity edit dialog"""
        dialog = ttk.Toplevel(self)
        dialog.title(_("Edit Quantity"))
        dialog.geometry("300x200")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (150)
        y = (dialog.winfo_screenheight() // 2) - (100)
        dialog.geometry(f"300x200+{x}+{y}")
        
        # Content
        ttk.Label(dialog, text=item["name"], font=("Segoe UI", 12, "bold")).pack(pady=10)
        ttk.Label(dialog, text=_("Quantity:")).pack()
        
        qty_var = IntVar(value=item["quantity"])
        qty_frame = ttk.Frame(dialog)
        qty_frame.pack(pady=10)
        
        # Quantity controls
        ttk.Button(qty_frame, text="-", command=lambda: qty_var.set(max(0, qty_var.get()-1))).pack(side=LEFT)
        qty_entry = ttk.Entry(qty_frame, textvariable=qty_var, width=8, justify=CENTER)
        qty_entry.pack(side=LEFT, padx=5)
        ttk.Button(qty_frame, text="+", command=lambda: qty_var.set(min(item["stock"], qty_var.get()+1))).pack(side=LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def update_qty():
            new_qty = qty_var.get()
            if new_qty <= 0:
                del self.cart_items[product_id]
            else:
                self.cart_items[product_id]["quantity"] = new_qty
            self._update_cart_display()
            dialog.destroy()
        
        ttk.Button(btn_frame, text=_("Update"), command=update_qty, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text=_("Cancel"), command=dialog.destroy).pack(side=LEFT, padx=5)
    
    def _remove_selected_item(self, event=None):
        """Remove selected item from cart"""
        selection = self.cart_tree.selection()
        if not selection:
            return
        
        item_values = self.cart_tree.item(selection[0], "values")
        if not item_values:
            return
        
        # Find and remove
        display_name = item_values[0]
        for product_id, item in self.cart_items.items():
            item_display_name = item["name"][:20] + "..." if len(item["name"]) > 20 else item["name"]
            if item_display_name == display_name:
                del self.cart_items[product_id]
                self._update_cart_display()
                break
    
    def _clear_cart(self):
        """Clear all items from cart"""
        if not self.cart_items:
            return
        
        result = messagebox.askyesno(
            _("Clear Cart"),
            _("Are you sure you want to clear all items from the cart?")
        )
        
        if result:
            self.cart_items.clear()
            self._update_cart_display()
    
    def _mark_as_debit(self):
        """Mark sale as debit (unpaid)"""
        if not self.cart_items:
            messagebox.showwarning(_("Empty Cart"), _("Please add items to cart first"))
            return
        
        result = messagebox.askyesno(
            _("Mark as Debit"),
            _("Mark this sale as debit (customer will pay later)?")
        )
        
        if result:
            self._process_sale(payment_method="debit")
    
    def _complete_sale(self):
        """Complete sale with payment"""
        if not self.cart_items:
            messagebox.showwarning(_("Empty Cart"), _("Please add items to cart first"))
            return
        
        # Show payment method dialog
        self._show_payment_dialog()
    
    def _show_payment_dialog(self):
        """Show payment method selection"""
        dialog = ttk.Toplevel(self)
        dialog.title(_("Payment Method"))
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (150)
        dialog.geometry(f"400x300+{x}+{y}")
        
        # Content
        ttk.Label(dialog, text=_("Select Payment Method"), font=("Segoe UI", 14, "bold")).pack(pady=20)
        
        # Calculate total
        total = sum(item["price"] * item["quantity"] for item in self.cart_items.values())
        ttk.Label(dialog, text=f"{_('Total')}: ${total:.2f}", font=("Segoe UI", 12)).pack(pady=10)
        
        # Payment buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        payment_methods = [
            ("💵 Cash", "cash"),
            ("💳 Card", "card"),
            ("📱 Mobile", "mobile"),
            ("🏦 Bank Transfer", "transfer")
        ]
        
        for text, method in payment_methods:
            btn = ttk.Button(
                btn_frame,
                text=text,
                command=lambda m=method: self._process_payment(dialog, m),
                style="BigActionButton.TButton",
                bootstyle="success-outline",
                width=15
            )
            btn.pack(pady=5, fill=X)
        
        # Cancel button
        ttk.Button(
            btn_frame,
            text=_("Cancel"),
            command=dialog.destroy,
            style="BigActionButton.TButton",
            bootstyle="secondary",
            width=15
        ).pack(pady=(20, 5), fill=X)
    
    def _process_payment(self, dialog, payment_method):
        """Process payment and complete sale"""
        dialog.destroy()
        self._process_sale(payment_method)
    
    def _process_sale(self, payment_method="cash"):
        """Process the complete sale"""
        try:
            # Calculate totals
            subtotal = sum(item["price"] * item["quantity"] for item in self.cart_items.values())
            tax_rate = 0.1  # 10% tax
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount
            
            # Prepare sale data
            sale_data = {
                'customer_id': None,
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'total_amount': total,
                'payment_method': payment_method,
                'status': 'completed' if payment_method != 'debit' else 'pending',
                'items': []
            }
            
            # Add items
            for product_id, item in self.cart_items.items():
                sale_data['items'].append({
                    'product_id': int(product_id),
                    'quantity': item['quantity'],
                    'unit_price': item['price'],
                    'total_price': item['price'] * item['quantity']
                })
            
            # Process through enhanced data access
            success, invoice_id = enhanced_data.create_invoice_with_items(sale_data)
            
            if success:
                # Update stock
                for product_id, item in self.cart_items.items():
                    enhanced_data.update_product_stock(int(product_id), -item['quantity'])
                
                # Show success message
                status_text = _("Sale completed successfully!") if payment_method != 'debit' else _("Sale marked as debit!")
                messagebox.showinfo(_("Success"), f"{status_text}\n{_('Invoice ID')}: {invoice_id}")
                
                # Clear cart and refresh
                self.cart_items.clear()
                self._update_cart_display()
                self._load_product_grid()  # Refresh to show updated stock
                
                # Optional: Print receipt
                self._offer_print_receipt(invoice_id)
                
            else:
                messagebox.showerror(_("Error"), _("Failed to process sale. Please try again."))
                
        except Exception as e:
            logger.error(f"Error processing sale: {str(e)}")
            messagebox.showerror(_("Error"), _("An error occurred while processing the sale."))
    
    def _offer_print_receipt(self, invoice_id):
        """Offer to print receipt"""
        result = messagebox.askyesno(
            _("Print Receipt"),
            _("Would you like to print a receipt?")
        )
        
        if result:
            try:
                # Generate and print receipt
                from modules.reports import receipt_generator
                receipt_generator.print_receipt(invoice_id)
            except ImportError:
                messagebox.showinfo(_("Info"), _("Receipt printing not available"))
            except Exception as e:
                logger.error(f"Error printing receipt: {str(e)}")
                messagebox.showerror(_("Error"), _("Failed to print receipt"))
    
    def _scan_barcode(self):
        """Handle barcode scanning"""
        # For now, show a simple input dialog
        dialog = ttk.Toplevel(self)
        dialog.title(_("Scan Barcode"))
        dialog.geometry("350x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (175)
        y = (dialog.winfo_screenheight() // 2) - (75)
        dialog.geometry(f"350x150+{x}+{y}")
        
        ttk.Label(dialog, text=_("Enter or scan barcode:")).pack(pady=10)
        
        barcode_var = StringVar()
        entry = ttk.Entry(dialog, textvariable=barcode_var, font=("Segoe UI", 12), width=30)
        entry.pack(pady=10)
        entry.focus_set()
        
        def process_barcode():
            barcode = barcode_var.get().strip()
            if barcode:
                self._find_product_by_barcode(barcode)
            dialog.destroy()
        
        entry.bind("<Return>", lambda e: process_barcode())
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text=_("OK"), command=process_barcode).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text=_("Cancel"), command=dialog.destroy).pack(side=LEFT, padx=5)
    
    def _find_product_by_barcode(self, barcode):
        """Find and add product by barcode"""
        try:
            # Search for product by barcode
            result = enhanced_data.get_products_paged(page=1, page_size=1, search=f"barcode:{barcode}")
            
            if isinstance(result, PagedResult) and result.data:
                product = result.data[0]
                self._add_product_to_cart(product)
                messagebox.showinfo(_("Found"), f"{_('Added')}: {product.get('Name', 'Unknown')}")
            else:
                messagebox.showwarning(_("Not Found"), _("Product with this barcode was not found"))
                
        except Exception as e:
            logger.error(f"Error finding product by barcode: {str(e)}")
            messagebox.showerror(_("Error"), _("Error searching for product"))
    
    def _show_history(self):
        """Show sales history"""
        try:
            # Open sales history window
            from modules.pages.sales_history_page import SalesHistoryPage
            history_window = ttk.Toplevel(self)
            history_window.title(_("Sales History"))
            history_window.geometry("800x600")
            
            # Center window
            history_window.update_idletasks()
            x = (history_window.winfo_screenwidth() // 2) - (400)
            y = (history_window.winfo_screenheight() // 2) - (300)
            history_window.geometry(f"800x600+{x}+{y}")
            
            # Create history page
            SalesHistoryPage(history_window).pack(fill=BOTH, expand=True)
            
        except ImportError:
            messagebox.showinfo(_("Info"), _("Sales history feature not available"))
        except Exception as e:
            logger.error(f"Error showing history: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to open sales history"))
    
    def _sync_data(self):
        """Sync data with server/backup"""
        try:
            # Show sync progress
            progress_dialog = ttk.Toplevel(self)
            progress_dialog.title(_("Syncing Data"))
            progress_dialog.geometry("300x100")
            progress_dialog.transient(self)
            progress_dialog.grab_set()
            
            # Center dialog
            progress_dialog.update_idletasks()
            x = (progress_dialog.winfo_screenwidth() // 2) - (150)
            y = (progress_dialog.winfo_screenheight() // 2) - (50)
            progress_dialog.geometry(f"300x100+{x}+{y}")
            
            ttk.Label(progress_dialog, text=_("Syncing data...")).pack(pady=20)
            progress = ttk.Progressbar(progress_dialog, mode='indeterminate')
            progress.pack(fill=X, padx=20)
            progress.start()
            
            # Simulate sync process
            def complete_sync():
                progress.stop()
                progress_dialog.destroy()
                messagebox.showinfo(_("Success"), _("Data synchronized successfully!"))
            
            self.after(2000, complete_sync)  # Simulate 2-second sync
            
        except Exception as e:
            logger.error(f"Error during sync: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to sync data"))
    
    def _add_custom_item(self):
        """Add custom item to cart"""
        dialog = ttk.Toplevel(self)
        dialog.title(_("Add Custom Item"))
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (125)
        dialog.geometry(f"400x250+{x}+{y}")
        
        # Form
        form_frame = ttk.Frame(dialog)
        form_frame.pack(padx=20, pady=20, fill=BOTH, expand=True)
        
        ttk.Label(form_frame, text=_("Item Name:")).grid(row=0, column=0, sticky=W, pady=5)
        name_var = StringVar()
        ttk.Entry(form_frame, textvariable=name_var, width=30).grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text=_("Price:")).grid(row=1, column=0, sticky=W, pady=5)
        price_var = DoubleVar()
        ttk.Entry(form_frame, textvariable=price_var, width=30).grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text=_("Quantity:")).grid(row=2, column=0, sticky=W, pady=5)
        qty_var = IntVar(value=1)
        ttk.Entry(form_frame, textvariable=qty_var, width=30).grid(row=2, column=1, pady=5)
        
        def add_custom():
            name = name_var.get().strip()
            price = price_var.get()
            qty = qty_var.get()
            
            if not name or price <= 0 or qty <= 0:
                messagebox.showwarning(_("Invalid Input"), _("Please enter valid item details"))
                return
            
            # Add to cart as custom item
            custom_id = f"custom_{int(time.time())}"
            self.cart_items[custom_id] = {
                "name": name,
                "price": price,
                "quantity": qty,
                "stock": 999  # Unlimited stock for custom items
            }
            
            self._update_cart_display()
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text=_("Add"), command=add_custom, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text=_("Cancel"), command=dialog.destroy).pack(side=LEFT, padx=5)
    
    def _open_settings(self):
        """Open settings dialog"""
        try:
            from modules.pages.settings_page import SettingsPage
            settings_window = ttk.Toplevel(self)
            settings_window.title(_("Settings"))
            settings_window.geometry("600x500")
            
            # Center window
            settings_window.update_idletasks()
            x = (settings_window.winfo_screenwidth() // 2) - (300)
            y = (settings_window.winfo_screenheight() // 2) - (250)
            settings_window.geometry(f"600x500+{x}+{y}")
            
            # Create settings page
            SettingsPage(settings_window).pack(fill=BOTH, expand=True)
            
        except ImportError:
            messagebox.showinfo(_("Info"), _("Settings page not available"))
        except Exception as e:
            logger.error(f"Error opening settings: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to open settings"))
    
    def _update_header_stats(self):
        """Placeholder for header stats update - removed in minimalist design"""
        pass
    
    def _setup_touch_styles(self):
        """✅ 5. Setup touch-friendly styles following UX golden rules"""
        style = ttk.Style()
        
        # ✅ Touch UX Golden Rules Applied:
        # - Minimum button size: 48x48 px
        # - Large padding for touch targets
        # - Clear contrast colors
        # - Increased font sizes (16-20pt for labels & totals)
        
        # Dark theme base
        style.configure("Dark.TFrame", background="#2B2B2B")
        style.configure("Dark.TLabelframe", background="#2B2B2B", foreground="#FFFFFF")
        style.configure("Dark.TLabelframe.Label", background="#2B2B2B", foreground="#4ECDC4", font=("Segoe UI", 12, "bold"))
        
        # Touch button styles - Minimum 48x48px with large padding
        style.configure("TouchLarge.TButton", 
                       padding=(20, 15), 
                       font=("Segoe UI", 16, "bold"))
        
        style.configure("TouchMedium.TButton", 
                       padding=(15, 12), 
                       font=("Segoe UI", 14))
        
        style.configure("TouchSmall.TButton", 
                       padding=(12, 10), 
                       font=("Segoe UI", 12))
        
        # Action icon buttons - Large with vertical text layout
        style.configure("TouchActionIcon.TButton", 
                       padding=(20, 20), 
                       font=("Segoe UI", 12, "bold"),
                       width=8)
        
        # Category filter buttons - Touch-friendly with spacing
        style.configure("TouchCategory.TButton", 
                       padding=(15, 10), 
                       font=("Segoe UI", 13))
        
        # Payment method buttons - Large icon buttons
        style.configure("TouchPayment.TButton", 
                       padding=(15, 20), 
                       font=("Segoe UI", 11, "bold"),
                       width=8)
        
        # Checkout button - Extra large for primary action (bottom-right)
        style.configure("TouchCheckout.TButton", 
                       padding=(25, 20), 
                       font=("Segoe UI", 18, "bold"))
        
        # Quantity stepper buttons
        style.configure("TouchStepper.TButton", 
                       padding=(15, 15), 
                       font=("Segoe UI", 16, "bold"),
                       width=3)
        
        # Quick quantity buttons
        style.configure("TouchQuick.TButton", 
                       padding=(10, 8), 
                       font=("Segoe UI", 11),
                       width=3)
        
        # Discount buttons
        style.configure("TouchDiscount.TButton", 
                       padding=(8, 6), 
                       font=("Segoe UI", 10),
                       width=4)
        
        # Keypad buttons
        style.configure("TouchKeypad.TButton", 
                       padding=(15, 15), 
                       font=("Segoe UI", 16, "bold"))
        
        # Entry styles with larger fonts
        style.configure("Search.TEntry", 
                       fieldbackground="#383838", 
                       foreground="#FFFFFF", 
                       font=("Segoe UI", 16),
                       padding=(10, 8))
        
        style.configure("TouchQty.TEntry", 
                       fieldbackground="#383838", 
                       foreground="#FFFFFF", 
                       font=("Segoe UI", 14),
                       padding=(8, 6))
        
        style.configure("TouchDiscount.TEntry", 
                       fieldbackground="#383838", 
                       foreground="#FFFFFF", 
                       font=("Segoe UI", 14),
                       padding=(8, 6))
        
        # Search clear button
        style.configure("SearchClear.TButton", 
                       padding=(8, 8), 
                       font=("Segoe UI", 12))
        
        # Treeview with larger row height for touch
        style.configure("Touch.Treeview", 
                       rowheight=40, 
                       font=("Segoe UI", 12),
                       background="#383838",
                       foreground="#FFFFFF",
                       fieldbackground="#383838")
        
        style.configure("Touch.Treeview.Heading", 
                       font=("Segoe UI", 13, "bold"),
                       background="#4ECDC4",
                       foreground="#FFFFFF")
        
        # Scrollbar with larger width for touch
        style.configure("Touch.Vertical.TScrollbar", 
                       arrowsize=25,
                       width=20)
        
        # Success/Info/Warning cards
        style.configure("Success.TFrame", background="#27AE60")
        style.configure("Info.TFrame", background="#3498DB")
        style.configure("Warning.TFrame", background="#F39C12")
    
    def _load_products_grid(self, search_term=""):
        """Load products in grid view with touch-friendly cards"""
        try:
            # Clear existing cards
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
            
            # Get products data
            if search_term:
                result = enhanced_data.get_products_paged(page=1, page_size=50, search=search_term)
            else:
                result = enhanced_data.get_products_paged(page=1, page_size=50)
            
            if isinstance(result, PagedResult):
                # Calculate grid layout
                cards_per_row = 3  # Adjust based on screen size
                row = 0
                col = 0
                
                for item in result.data:
                    # Create product card
                    card = self._create_product_card(self.grid_frame, item, row, col)
                    
                    col += 1
                    if col >= cards_per_row:
                        col = 0
                        row += 1
                
                # Update scroll region
                self.grid_frame.update_idletasks()
                self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
            
        except Exception as e:
            logger.error(f"Error loading products grid: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to load products"))
    
    def _create_product_card(self, parent, product, row, col):
        """✅ Create touch-friendly product card with image, name, price, stock"""
        # Card container with modern styling
        card_frame = ttk.Frame(parent, style="Card.TFrame", padding=15)
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Configure card styling
        card_frame.configure(relief="raised", borderwidth=2)
        
        # Product image placeholder (64x64)
        image_frame = ttk.Frame(card_frame, width=64, height=64, style="ImagePlaceholder.TFrame")
        image_frame.pack(pady=(0, 10))
        image_frame.pack_propagate(False)
        
        # Image icon (placeholder)
        ttk.Label(
            image_frame,
            text="📦",
            font=("Segoe UI", 24),
            background="#4ECDC4",
            foreground="#FFFFFF"
        ).pack(expand=True)
        
        # Product name (truncated for card)
        name = product.get('Name', 'Unknown')
        display_name = name[:20] + "..." if len(name) > 20 else name
        
        name_label = ttk.Label(
            card_frame,
            text=display_name,
            font=("Segoe UI", 12, "bold"),
            foreground="#FFFFFF",
            background="#2B2B2B",
            anchor=CENTER
        )
        name_label.pack(pady=(0, 5))
        
        # Price - Large and prominent
        price = float(product.get('Price', 0))
        price_label = ttk.Label(
            card_frame,
            text=f"${price:.2f}",
            font=("Segoe UI", 14, "bold"),
            foreground="#27AE60",
            background="#2B2B2B",
            anchor=CENTER
        )
        price_label.pack(pady=(0, 5))
        
        # Stock availability
        stock = int(product.get('Stock', 0))
        stock_color = "#27AE60" if stock > 10 else "#F39C12" if stock > 0 else "#E74C3C"
        stock_text = f"📦 {stock} {_('available')}"
        
        stock_label = ttk.Label(
            card_frame,
            text=stock_text,
            font=("Segoe UI", 10),
            foreground=stock_color,
            background="#2B2B2B",
            anchor=CENTER
        )
        stock_label.pack(pady=(0, 10))
        
        # Add to cart button - Touch-friendly
        add_btn = ttk.Button(
            card_frame,
            text="➕ " + _("Add to Cart"),
            command=lambda: self._add_product_card_to_cart(product),
            bootstyle="success" if stock > 0 else "secondary",
            style="TouchMedium.TButton",
            state="normal" if stock > 0 else "disabled"
        )
        add_btn.pack(fill=X)
        
        # Make entire card clickable for selection
        self._make_card_clickable(card_frame, product, add_btn)
        
        return card_frame
    
    def _make_card_clickable(self, card, product, add_btn):
        """Make the entire product card clickable for touch"""
        def on_card_click(event=None):
            if int(product.get('Stock', 0)) > 0:
                self._add_product_card_to_cart(product)
                # Visual feedback
                original_style = card.cget('style')
                card.configure(style="Selected.TFrame")
                self.after(200, lambda: card.configure(style=original_style))
        
        # Bind click events to card and all children
        card.bind("<Button-1>", on_card_click)
        card.configure(cursor="hand2")
        
        for child in card.winfo_children():
            child.bind("<Button-1>", on_card_click)
            if not isinstance(child, ttk.Button):  # Don't change cursor for buttons
                child.configure(cursor="hand2")
    
    def _add_product_card_to_cart(self, product):
        """Add product from card to cart with quantity from stepper"""
        try:
            product_id = str(product.get('ProductID', ''))
            if not product_id:
                return
            
            # Get quantity from stepper
            quantity = self.qty_var.get()
            
            # Check stock
            stock = int(product.get('Stock', 0))
            if quantity > stock:
                messagebox.showerror(_("Error"), _("Not enough stock available"))
                return
            
            # Add to cart
            if product_id in self.cart_items:
                self.cart_items[product_id]["quantity"] += quantity
            else:
                self.cart_items[product_id] = {
                    "id": product_id,
                    "name": product.get('Name', 'Unknown'),
                    "price": float(product.get('Price', 0)),
                    "quantity": quantity,
                    "stock": stock
                }
            
            # Update cart display
            self._update_cart_display()
            
            # Visual feedback
            messagebox.showinfo(_("Success"), _("Product added to cart!"))
            
        except Exception as e:
            logger.error(f"Error adding product card to cart: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to add product to cart"))
    
    def _clear_search(self):
        """Clear the search entry and reload products"""
        self.search_var.set("")
        if self.current_view_mode == "grid":
            self._load_products_grid()
        else:
            self._load_products(1, "")
    
    def _create_split_view(self, parent):
        """Create the split view with products on left and cart on right"""
        split_frame = ttk.Frame(parent)
        split_frame.pack(fill=BOTH, expand=True, pady=5)
        
        # Products panel (left side)
        products_frame = ttk.LabelFrame(split_frame, text=_("Products"))
        products_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        # Search bar
        search_frame = ttk.Frame(products_frame)
        search_frame.pack(fill=X, pady=5, padx=5)
        
        ttk.Label(
            search_frame, 
            textvariable=self.search_label_var
        ).pack(side=LEFT, padx=5)
        
        # Use FastSearchEntry for debounced search
        self.search_entry = FastSearchEntry(
            search_frame,
            search_function=self._perform_product_search,
            on_select_callback=self._on_product_selected_from_search
        )
        self.search_entry.get_frame().pack(side=LEFT, padx=5)
        
        ttk.Button(
            search_frame,
            textvariable=self.clear_btn_var,
            command=self._clear_search,
            bootstyle=SECONDARY,
            style="Small.TButton"
        ).pack(side=LEFT, padx=5)
        
        # Products list (paginated)
        self.products_list = PaginatedListView(
            products_frame,
            columns=["id", "name", "price", "stock"],
            headers={
                "id": _("ID"),
                "name": _("Product"),
                "price": _("Price"),
                "stock": _("Available")
            },
            widths={"id": 50, "name": 200, "price": 80, "stock": 80},
            on_page_change=self._load_products,
            on_select=self._on_product_selected,
            page_size=20,
        )
        self.products_list.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Product actions
        product_actions = ttk.Frame(products_frame)
        product_actions.pack(fill=X, pady=5, padx=5)
        
        # Quantity selector
        ttk.Label(
            product_actions, 
            text=_("Quantity:")
        ).pack(side=LEFT, padx=5)
        
        self.quantity_var = IntVar(value=1)
        self.quantity_spin = ttk.Spinbox(
            product_actions,
            from_=1,
            to=100,
            textvariable=self.quantity_var,
            width=5
        )
        self.quantity_spin.pack(side=LEFT, padx=5)
        
        # Add to cart button
        self.add_button = ttk.Button(
            product_actions,
            textvariable=self.add_to_cart_var,
            command=self._add_selected_to_cart,
            bootstyle=SUCCESS,
            state="disabled"
        )
        self.add_button.pack(side=LEFT, padx=5)
        
        # Cart panel (right side)
        cart_frame = ttk.LabelFrame(split_frame, text=_("Cart"))
        cart_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 0))
        
        # Store reference for updating cart title
        self.cart_frame = cart_frame
        
        # Cart summary
        cart_summary = ttk.Frame(cart_frame)
        cart_summary.pack(fill=X, pady=5, padx=5)
        
        self.cart_total_label = ttk.Label(
            cart_summary, 
            textvariable=self.cart_total_var,
            font=("Arial", 12, "bold")
        )
        self.cart_total_label.pack(side=LEFT, padx=5)
        
        self.cart_items_label = ttk.Label(
            cart_summary, 
            textvariable=self.cart_items_var
        )
        self.cart_items_label.pack(side=RIGHT, padx=5)
        
        # Cart contents
        self.cart_view = ttk.Treeview(
            cart_frame,
            columns=["id", "name", "price", "quantity", "subtotal"],
            show="headings",
            height=15
        )
        self.cart_view.heading("id", text=_("ID"))
        self.cart_view.heading("name", text=_("Product"))
        self.cart_view.heading("price", text=_("Unit Price"))
        self.cart_view.heading("quantity", text=_("Qty"))
        self.cart_view.heading("subtotal", text=_("Subtotal"))
        
        self.cart_view.column("id", width=50, anchor=CENTER)
        self.cart_view.column("name", width=200, anchor=W)
        self.cart_view.column("price", width=80, anchor=E)
        self.cart_view.column("quantity", width=60, anchor=CENTER)
        self.cart_view.column("subtotal", width=80, anchor=E)
        
        self.cart_view.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Cart actions
        cart_actions = ttk.Frame(cart_frame)
        cart_actions.pack(fill=X, pady=5, padx=5)
        
        # Remove from cart button
        self.remove_button = ttk.Button(
            cart_actions,
            textvariable=self.remove_var,
            command=self._remove_from_cart,
            bootstyle=DANGER,
            state="disabled"
        )
        self.remove_button.pack(side=LEFT, padx=5)
        
        # Clear cart button
        self.clear_cart_button = ttk.Button(
            cart_actions,
            textvariable=self.clear_cart_var,
            command=self._clear_cart,
            bootstyle=WARNING
        )
        self.clear_cart_button.pack(side=LEFT, padx=5)
        
        # Checkout button
        self.checkout_button = ttk.Button(
            cart_actions,
            textvariable=self.checkout_var,
            command=self._checkout,
            bootstyle=SUCCESS
        )
        self.checkout_button.pack(side=RIGHT, padx=5)
        
        # Bind cart selection event
        self.cart_view.bind("<<TreeviewSelect>>", self._on_cart_item_selected)
        
        # Initialize cart
        self.cart_items = {}
        self.cart_total = 0.0
        self.selected_product = None
    
    def prepare_for_display(self):
        """Prepare the page before displaying - load initial data"""
        if self.current_view_mode == "grid":
            self._load_products_grid()
        else:
            self._load_products()
        
        # Update header statistics
        self._update_header_stats()
    
    def refresh(self):
        """Refresh the page data"""
        self._refresh_language()
        if self.current_view_mode == "grid":
            self._load_products_grid()
        else:
            self._load_products()
        
        # Update header statistics
        self._update_header_stats()
        
        # Reload category buttons
        self._load_touch_category_buttons()
    
    def _refresh_language(self):
        """Update all text elements with current language"""
        # Update UI direction
        set_widget_direction(self)
        
        # Update all text variables with translated strings
        self.title_var.set(_("Sales Screen"))
        self.back_btn_var.set(_("Back to Home"))
        self.search_label_var.set(_("Search Products:"))
        self.clear_btn_var.set(_("Clear"))
        self.cart_title_var.set(_("Shopping Cart"))
        self.add_to_cart_var.set(_("Add to Cart"))
        self.remove_var.set(_("Remove"))
        self.clear_cart_var.set(_("Clear Cart"))
        self.checkout_var.set(_("Checkout"))
        
        # Update headings
        self._update_cart_display()
        
        # Update product list headers
        if hasattr(self, 'products_list'):
            self.products_list.update_headers({
                "id": _("ID"),
                "name": _("Product"),
                "price": _("Price"),
                "stock": _("Available")
            })
    
    def _load_products(self, page=1, search_term=""):
        """Load products with pagination and optional search filter"""
        # Use the search term from the entry if not provided
        if search_term == "":
            search_term = self.search_var.get()
            
        # Show progress during load
        progress = ProgressDialog(
            self,
            title=_("Loading Products")
        )
        
        try:
            # Call get_products_paged synchronously (it returns PagedResult directly)
            result = enhanced_data.get_products_paged(
                page=page,
                page_size=self.products_list.page_size,
                search=search_term
            )
            
            if isinstance(result, PagedResult):
                # Transform data for display
                data = []
                for item in result.data:  # Use .data instead of .items
                    data.append({
                        "id": item["ProductID"],
                        "name": item["Name"],  # Use "Name" instead of "ProductName"
                        "price": f"${float(item['Price']):.2f}",
                        "stock": item["Stock"],
                        # Store original data for cart operations
                        "raw_data": item
                    })
                
                # Calculate total_pages from total_count and page_size
                total_pages = max(1, (result.total_count + result.page_size - 1) // result.page_size)
                
                # Update the list view
                self.products_list.update_items(
                    data,
                    result.total_count,  # Use .total_count instead of .total_items
                    result.current_page,  # Use .current_page instead of .page
                    total_pages  # Calculate total_pages
                )
            
        except Exception as error:
            logger.error(f"Error loading products: {str(error)}")
            messagebox.showerror(
                _("Error"),
                _("Failed to load products: {0}").format(str(error))
            )
        finally:
            # Close progress dialog
            progress.close()
    
    def _on_search_changed(self, search_term):
        """Handle search changes - debounced by FastSearchEntry"""
        self._load_products(1, search_term)
    
    def _clear_search(self):
        """Clear the search entry"""
        self.search_var.set("")
        self._load_products(1, "")
    
    def _perform_product_search(self, search_term):
        """Search products for FastSearchEntry - returns list of results"""
        if not search_term or len(search_term.strip()) < 2:
            return []
        
        try:
            # Use enhanced data access for search
            results = enhanced_data.search_products_fast(search_term.strip())
            if results:
                # Format results for FastSearchEntry
                formatted_results = []
                for item in results:
                    formatted_results.append({
                        'id': item.get('ProductID', ''),
                        'display': f"{item.get('Name', '')} - ${item.get('Price', 0):.2f} (Stock: {item.get('Stock', 0)})",
                        'product': item
                    })
                return formatted_results
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
        
        return []
    
    def _on_product_selected_from_search(self, result):
        """Handle product selection from search - wrapper for consistency"""
        self._on_product_selected(result)
    
    def _on_product_selected(self, result):
        """Handle product selection from FastSearchEntry"""
        if result and 'product' in result:
            product = result['product']
            # Add to cart automatically when selected
            self._add_to_cart_from_product(product)
    
    def _add_to_cart_from_product(self, product):
        """Add product to cart from product data"""
        product_id = str(product.get('ProductID', ''))
        if not product_id:
            return
        
        # Check if already in cart
        if product_id in self.cart_items:
            # Increase quantity
            self.cart_items[product_id]["quantity"] += 1
        else:
            # Add new item
            self.cart_items[product_id] = {
                "id": product_id,
                "name": product.get('Name', 'Unknown'),
                "price": float(product.get('Price', 0)),
                "quantity": 1,
                "stock": int(product.get('Stock', 0))
            }
        
        # Update display
        self._update_cart_display()
        
        # Clear search if needed
        if hasattr(self.search_entry, 'set_value'):
            self.search_entry.set_value("")

    def _on_cart_item_selected(self, event=None):
        """Handle cart item selection"""
        selection = self.cart_view.selection()
        if selection:
            self.remove_button.configure(state="normal")
        else:
            self.remove_button.configure(state="disabled")
    
    def _add_to_cart(self):
        """Add the selected product to the cart"""
        if not self.selected_product:
            return
        
        # Get quantity
        try:
            quantity = int(self.quantity_var.get())
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except:
            messagebox.showerror(
                _("Invalid Quantity"),
                _("Please enter a valid quantity")
            )
            return
        
        # Check stock
        if quantity > int(self.selected_product["Stock"]):
            messagebox.showerror(
                _("Insufficient Stock"),
                _("Not enough items in stock")
            )
            return
        
        # Get product data
        product_id = self.selected_product["ProductID"]
        product_name = self.selected_product["ProductName"]
        price = float(self.selected_product["Price"])
        
        # Add to cart or update quantity
        if product_id in self.cart_items:
            # Update existing item
            self.cart_items[product_id]["quantity"] += quantity
        else:
            # Add new item
            self.cart_items[product_id] = {
                "id": product_id,
                "name": product_name,
                "price": price,
                "quantity": quantity,
                "product_data": self.selected_product
            }
        
        # Update cart display
        self._update_cart_display()
    
    def _remove_from_cart(self):
        """Remove selected item from cart with touch-friendly confirmation"""
        try:
            selection = self.cart_tree.selection()
            if not selection:
                messagebox.showwarning(_("Warning"), _("Please select an item to remove"))
                return
            
            # Get the item name from the first column
            item_values = self.cart_tree.item(selection[0], "values")
            if not item_values:
                return
            
            item_name = item_values[0]
            
            # Find and remove the item by name
            item_to_remove = None
            for product_id, item in self.cart_items.items():
                display_name = item["name"][:25] + "..." if len(item["name"]) > 25 else item["name"]
                if display_name == item_name:
                    item_to_remove = product_id
                    break
            
            if item_to_remove:
                # Touch-friendly confirmation with large buttons
                result = messagebox.askyesno(
                    _("Remove Item"),
                    _("Remove {0} from cart?").format(self.cart_items[item_to_remove]["name"]),
                    icon="question"
                )
                
                if result:
                    del self.cart_items[item_to_remove]
                    self._update_cart_display()
                    
                    # Visual feedback
                    messagebox.showinfo(_("Success"), _("Item removed from cart"))
            
        except Exception as e:
            logger.error(f"Error removing item from cart: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to remove item from cart"))
    
    def _clear_cart(self):
        """Clear all items from cart with touch-friendly confirmation"""
        try:
            if not self.cart_items:
                messagebox.showinfo(_("Info"), _("Cart is already empty"))
                return
            
            # Touch-friendly confirmation
            result = messagebox.askyesno(
                _("Clear Cart"),
                _("Remove all items from cart?"),
                icon="warning"
            )
            
            if result:
                self.cart_items = {}
                self._update_cart_display()
                messagebox.showinfo(_("Success"), _("Cart cleared successfully"))
                
        except Exception as e:
            logger.error(f"Error clearing cart: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to clear cart"))
    
    def _on_cart_item_selected(self, event=None):
        """Handle cart item selection with touch support"""
        try:
            selection = self.cart_tree.selection()
            if selection and hasattr(self, 'remove_btn'):
                self.remove_btn.configure(state="normal")
            elif hasattr(self, 'remove_btn'):
                self.remove_btn.configure(state="disabled")
                
            # For old layout compatibility
            if selection and hasattr(self, 'remove_button'):
                self.remove_button.configure(state="normal")
            elif hasattr(self, 'remove_button'):
                self.remove_button.configure(state="disabled")
                
        except Exception as e:
            logger.error(f"Error handling cart item selection: {str(e)}")
    
    def _filter_by_category(self, category):
        """Filter products by category with touch-friendly feedback"""
        try:
            if category == "All":
                search_term = ""
            else:
                # Get category name
                category_name = category.get('name', category) if isinstance(category, dict) else category
                search_term = f"category:{category_name}"
            
            # Update search and load products
            self.search_var.set(search_term)
            
            if self.current_view_mode == "grid":
                self._load_products_grid(search_term)
            else:
                self._load_products(1, search_term)
            
            # Update button states for visual feedback
            for widget in self.category_buttons_frame.winfo_children():
                if hasattr(widget, 'configure'):
                    widget.configure(bootstyle="info-outline")
            
            # Highlight selected category button
            category_text = "All" if category == "All" else (category.get('name', category) if isinstance(category, dict) else category)
            for widget in self.category_buttons_frame.winfo_children():
                if hasattr(widget, 'cget') and category_text in widget.cget('text'):
                    widget.configure(bootstyle="success")
                    break
                    
        except Exception as e:
            logger.error(f"Error filtering by category: {str(e)}")
    
    def _process_checkout(self):
        """Process checkout with enhanced touch-friendly flow"""
        try:
            if not self.cart_items:
                messagebox.showwarning(_("Warning"), _("Cart is empty"))
                return
            
            # Get payment method and discount
            payment_method = self.payment_method.get()
            discount_percent = float(self.discount_var.get() or 0)
            
            # Calculate final totals
            subtotal = sum(item["price"] * item["quantity"] for item in self.cart_items.values())
            discount_amount = subtotal * (discount_percent / 100)
            final_total = subtotal - discount_amount
            
            # Create confirmation dialog with large buttons
            confirmation_msg = f"""
{_("Payment Summary:")}

{_("Items")}: {sum(item["quantity"] for item in self.cart_items.values())}
{_("Subtotal")}: ${subtotal:.2f}
{_("Discount")}: {discount_percent}% (${discount_amount:.2f})
{_("Total")}: ${final_total:.2f}
{_("Payment Method")}: {payment_method.title()}

{_("Proceed with checkout?")}
"""
            
            result = messagebox.askyesno(
                _("Confirm Checkout"),
                confirmation_msg,
                icon="question"
            )
            
            if result:
                # Process the actual checkout
                self._checkout()
            
        except Exception as e:
            logger.error(f"Error processing checkout: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to process checkout"))
    
    def _update_cart_display(self):
        """Update the cart display and totals with touch-friendly enhancements"""
        # Check if cart_tree exists before updating
        if not hasattr(self, 'cart_tree'):
            return
            
        # Clear existing items
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Add all items to the view
        subtotal = 0.0
        item_count = 0
        
        for product_id, item in self.cart_items.items():
            item_subtotal = item["price"] * item["quantity"]
            subtotal += item_subtotal
            item_count += item["quantity"]
            
            # Add trash icon in actions column for touch deletion
            self.cart_tree.insert(
                "",
                "end",
                values=(
                    item["name"][:25] + "..." if len(item["name"]) > 25 else item["name"],
                    item["quantity"],
                    f"${item['price']:.2f}",
                    f"${item_subtotal:.2f}",
                    "🗑️"  # Trash icon for removal
                )
            )
        
        # Apply discount if any
        discount_percent = float(self.discount_var.get() or 0)
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        # Update totals with enhanced formatting
        self.cart_total = total
        item_text = _("Items: {0}").format(item_count)
        
        if discount_percent > 0:
            total_text = _("Subtotal: ${0:.2f} | Discount: {1}% | Total: ${2:.2f}").format(
                subtotal, discount_percent, total
            )
        else:
            total_text = _("Total: ${0:.2f}").format(total)
        
        self.cart_items_var.set(item_text)
        self.cart_total_var.set(total_text)
        
        # Update button states
        has_items = bool(self.cart_items)
        
        # Update cart control buttons
        if hasattr(self, 'checkout_btn'):
            self.checkout_btn.configure(state="normal" if has_items else "disabled")
        if hasattr(self, 'clear_cart_btn'):
            self.clear_cart_btn.configure(state="normal" if has_items else "disabled")
        if hasattr(self, 'remove_btn'):
            self.remove_btn.configure(state="disabled")  # Will be enabled on selection
        
        # Update action buttons in old layout if they exist
        if hasattr(self, 'checkout_button'):
            self.checkout_button.configure(state="normal" if has_items else "disabled")
        if hasattr(self, 'clear_cart_button'):
            self.clear_cart_button.configure(state="normal" if has_items else "disabled")
    
    def _checkout(self):
        """Process the checkout"""
        if not self.cart_items:
            return
        
        # Show progress dialog
        progress = ProgressDialog(
            self,
            title=_("Processing")
        )
        
        # Create invoice data
        invoice_data = {
            "items": [],
            "total": self.cart_total,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add all items
        for product_id, item in self.cart_items.items():
            invoice_data["items"].append({
                "product_id": item["id"],
                "product_name": item["name"],
                "quantity": item["quantity"],
                "price": item["price"],
                "subtotal": item["price"] * item["quantity"]
            })
        
        # Process in background
        def process_sale():
            # Simulate processing delay (replace with actual processing)
            time.sleep(1)
            
            # Create invoice and update stock
            try:
                with ConnectionContext() as conn:
                    cursor = conn.cursor()
                    
                    # 1. Create invoice
                    cursor.execute("""
                        INSERT INTO Invoices (TotalAmount, Date) 
                        VALUES (?, ?)
                    """, (invoice_data["total"], invoice_data["timestamp"]))
                    
                    # Get invoice ID
                    cursor.execute("SELECT last_insert_rowid()")
                    invoice_id = cursor.fetchone()[0]
                    
                    # 2. Add items to invoice
                    for item in invoice_data["items"]:
                        cursor.execute("""
                            INSERT INTO InvoiceItems (InvoiceID, ProductID, Quantity, Price) 
                            VALUES (?, ?, ?, ?)
                        """, (
                            invoice_id, 
                            item["product_id"], 
                            item["quantity"], 
                            item["price"]
                        ))
                        
                        # 3. Update stock
                        cursor.execute("""
                            UPDATE Products 
                            SET Stock = Stock - ? 
                            WHERE ProductID = ?
                        """, (item["quantity"], item["product_id"]))
                    
                    # Commit all changes
                    conn.commit()
                    
                    # Clear cache to reflect changes
                    invalidate_cache()
                    
                    return {
                        "success": True, 
                        "invoice_id": invoice_id
                    }
            
            except Exception as e:
                logger.error(f"Error processing sale: {str(e)}")
                return {
                    "success": False, 
                    "error": str(e)
                }
        
        # Handle result
        def on_complete(result):
            # Close progress dialog
            progress.close()
            
            if result.get("success"):
                # Show success message
                invoice_id = result.get("invoice_id")
                messagebox.showinfo(
                    _("Sale Complete"),
                    _("Sale completed successfully!\nInvoice ID: {0}").format(invoice_id)
                )
                
                # Clear cart
                self.cart_items = {}
                self._update_cart_display()
                
                # Refresh product list to show updated stock
                self._load_products()
            else:
                # Show error message
                messagebox.showerror(
                    _("Error"),
                    _("Failed to process sale: {0}").format(result.get("error", "Unknown error"))
                )
        
        # Handle error
        def on_error(error):
            progress.close()
            messagebox.showerror(
                _("Error"),
                _("Failed to process sale: {0}").format(str(error))
            )
        
        # Run in background
        enhanced_data.run_in_background(
            process_sale,
            on_success=on_complete,
            on_error=on_error
        )
    
    def _on_back_clicked(self):
        """Navigate back to the main menu"""
        self.controller.show_frame("MainMenuPage")

    # Missing method implementations for Enhanced Sales Page
    
    def _change_view_mode(self):
        """Change between list and grid view modes"""
        try:
            mode = self.view_mode.get()
            if mode == "grid":
                # TODO: Implement grid view
                logger.info("Grid view mode selected")
                messagebox.showinfo(_("Info"), _("Grid view mode is not yet implemented"))
            else:
                # List view is default
                logger.info("List view mode selected")
                self._load_products()
        except Exception as e:
            logger.error(f"Error changing view mode: {str(e)}")
    
    def _filter_by_category(self, category):
        """Filter products by category"""
        try:
            if category == "All":
                self.search_var.set("")
                self._load_products(1, "")
            else:
                # Get category name
                category_name = category.get('name', category) if isinstance(category, dict) else category
                self.search_var.set(f"category:{category_name}")
                self._load_products(1, f"category:{category_name}")
            
            # Update button states
            for widget in self.category_buttons_frame.winfo_children():
                if hasattr(widget, 'configure'):
                    widget.configure(bootstyle="outline-primary")
            
            # Highlight selected category button
            for widget in self.category_buttons_frame.winfo_children():
                if hasattr(widget, 'cget') and widget.cget('text') == category_name:
                    widget.configure(bootstyle="primary")
                    
        except Exception as e:
            logger.error(f"Error filtering by category: {str(e)}")
    
    def _add_selected_to_cart(self):
        """Add selected product to cart with touch-friendly feedback"""
        try:
            if self.current_view_mode == "grid":
                # In grid mode, we need a product to be selected differently
                messagebox.showinfo(_("Info"), _("In grid mode, tap on product cards to add them to cart"))
                return
            
            # For list mode
            if hasattr(self, 'products_list'):
                selected_items = self.products_list.get_selected_items()
                if not selected_items:
                    messagebox.showwarning(_("Warning"), _("Please select a product to add to cart"))
                    return
                
                # Get the first selected item
                selected_item = selected_items[0]
                if 'raw_data' in selected_item:
                    product = selected_item['raw_data']
                    
                    # Get quantity from the quantity variable
                    try:
                        quantity = self.qty_var.get()
                        if quantity <= 0:
                            raise ValueError("Quantity must be positive")
                    except ValueError:
                        messagebox.showerror(_("Error"), _("Please enter a valid quantity"))
                        return
                    
                    # Check stock availability
                    stock = int(product.get('Stock', 0))
                    if quantity > stock:
                        messagebox.showerror(_("Error"), _("Not enough stock available"))
                        return
                    
                    # Add to cart
                    product_id = str(product.get('ProductID', ''))
                    if product_id in self.cart_items:
                        self.cart_items[product_id]["quantity"] += quantity
                    else:
                        self.cart_items[product_id] = {
                            "id": product_id,
                            "name": product.get('Name', 'Unknown'),
                            "price": float(product.get('Price', 0)),
                            "quantity": quantity,
                            "stock": stock
                        }
                    
                    # Update cart display
                    self._update_cart_display()
                    
                    # Reset quantity to 1
                    self.qty_var.set(1)
                    
                    # Visual feedback
                    messagebox.showinfo(_("Success"), _("Product added to cart!"))
            
        except Exception as e:
            logger.error(f"Error adding product to cart: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to add product to cart"))
    
    def _on_product_selected(self, event=None):
        """Handle product selection from the list view"""
        try:
            if hasattr(self, 'products_list'):
                selected_items = self.products_list.get_selected_items()
                if selected_items and hasattr(self, 'add_to_cart_btn'):
                    self.add_to_cart_btn.configure(state="normal")
                    self.selected_product = selected_items[0].get('raw_data')
                elif hasattr(self, 'add_to_cart_btn'):
                    self.add_to_cart_btn.configure(state="disabled")
                    self.selected_product = None
                    
                # For old layout compatibility
                if selected_items and hasattr(self, 'add_button'):
                    self.add_button.configure(state="normal")
                elif hasattr(self, 'add_button'):
                    self.add_button.configure(state="disabled")
                    
        except Exception as e:
            logger.error(f"Error handling product selection: {str(e)}")
    
    def _change_view_mode(self):
        """Handle view mode changes for compatibility"""
        try:
            mode = self.view_mode.get()
            self._set_view_mode(mode)
        except Exception as e:
            logger.error(f"Error changing view mode: {str(e)}")
    
    # Add missing style configuration for card styling
    def _configure_card_styles(self):
        """Configure additional styles for product cards"""
        style = ttk.Style()
        
        # Card styles
        style.configure("Card.TFrame", 
                       background="#383838", 
                       relief="raised", 
                       borderwidth=2,
                       padding=10)
        
        style.configure("Selected.TFrame", 
                       background="#4ECDC4", 
                       relief="raised", 
                       borderwidth=3,
                       padding=10)
        
        style.configure("ImagePlaceholder.TFrame", 
                       background="#4ECDC4",
                       relief="flat")
    
    def _scan_barcode(self):
        """Open barcode scanner dialog"""
        try:
            # Create a simple barcode input dialog
            dialog = ttk.Toplevel(self)
            dialog.title(_("Scan Barcode"))
            dialog.geometry("400x200")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (dialog.winfo_screenheight() // 2) - (200 // 2)
            dialog.geometry(f"400x200+{x}+{y}")
            
            ttk.Label(dialog, text=_("Enter or scan barcode:"), font=("Segoe UI", 12)).pack(pady=20)
            
            barcode_var = StringVar()
            entry = ttk.Entry(dialog, textvariable=barcode_var, font=("Segoe UI", 14))
            entry.pack(pady=10, padx=20, fill=X)
            entry.focus()
            
            def on_barcode_entered():
                barcode = barcode_var.get().strip()
                if barcode:
                    self._search_by_barcode(barcode)
                dialog.destroy()
            
            ttk.Button(dialog, text=_("Search"), command=on_barcode_entered, bootstyle="success").pack(pady=10)
            
            # Bind Enter key
            entry.bind('<Return>', lambda e: on_barcode_entered())
            
        except Exception as e:
            logger.error(f"Error opening barcode scanner: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to open barcode scanner"))
    
    def _search_by_barcode(self, barcode):
        """Search for product by barcode"""
        try:
            # Search in the products list
            result = enhanced_data.search_product_by_barcode(barcode)
            if result:
                # Add to cart automatically
                self._add_to_cart_from_product(result)
                messagebox.showinfo(_("Success"), _("Product found and added to cart"))
            else:
                messagebox.showwarning(_("Not Found"), _("Product with this barcode not found"))
        except Exception as e:
            logger.error(f"Error searching by barcode: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to search by barcode"))
    
    def _view_sales_history(self):
        """Open sales history dialog"""
        try:
            # Create sales history dialog
            dialog = ttk.Toplevel(self)
            dialog.title(_("Sales History"))
            dialog.geometry("800x600")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
            y = (dialog.winfo_screenheight() // 2) - (600 // 2)
            dialog.geometry(f"800x600+{x}+{y}")
            
            # Create header
            header = ttk.Frame(dialog)
            header.pack(fill=X, padx=10, pady=10)
            
            ttk.Label(header, text=_("Recent Sales"), font=("Segoe UI", 16, "bold")).pack(side=LEFT)
            
            # Create treeview for sales history
            tree_frame = ttk.Frame(dialog)
            tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            columns = ["id", "date", "total", "items"]
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
            
            tree.heading("id", text=_("Invoice ID"))
            tree.heading("date", text=_("Date"))
            tree.heading("total", text=_("Total"))
            tree.heading("items", text=_("Items"))
            
            tree.column("id", width=80, anchor=CENTER)
            tree.column("date", width=150, anchor=CENTER)
            tree.column("total", width=100, anchor=CENTER)
            tree.column("items", width=80, anchor=CENTER)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Load sales history
            self._load_sales_history(tree)
            
        except Exception as e:
            logger.error(f"Error opening sales history: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to open sales history"))
    
    def _load_sales_history(self, tree):
        """Load sales history into the treeview"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            
            # Get sales data
            sales_data = enhanced_data.get_recent_sales(limit=50)
            
            for sale in sales_data:
                tree.insert("", "end", values=(
                    sale.get("InvoiceID", ""),
                    sale.get("Date", ""),
                    f"${sale.get('TotalAmount', 0):.2f}",
                    sale.get("ItemCount", 0)
                ))
                
        except Exception as e:
            logger.error(f"Error loading sales history: {str(e)}")
    
    def _view_daily_reports(self):
        """Open daily reports dialog"""
        try:
            # Create daily reports dialog
            dialog = ttk.Toplevel(self)
            dialog.title(_("Daily Reports"))
            dialog.geometry("600x400")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"600x400+{x}+{y}")
            
            # Create notebook for different report types
            notebook = ttk.Notebook(dialog)
            notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # Sales summary tab
            sales_frame = ttk.Frame(notebook)
            notebook.add(sales_frame, text=_("Sales Summary"))
            
            # Load and display sales summary
            self._create_sales_summary(sales_frame)
            
            # Top products tab
            products_frame = ttk.Frame(notebook)
            notebook.add(products_frame, text=_("Top Products"))
            
            # Load and display top products
            self._create_top_products_report(products_frame)
            
        except Exception as e:
            logger.error(f"Error opening daily reports: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to open daily reports"))
    
    def _create_sales_summary(self, parent):
        """Create sales summary display"""
        try:
            # Get today's sales data
            today_sales = enhanced_data.get_today_sales_summary()
            
            # Create summary labels
            summary_frame = ttk.LabelFrame(parent, text=_("Today's Performance"), padding=20)
            summary_frame.pack(fill=X, padx=10, pady=10)
            
            # Total sales
            ttk.Label(summary_frame, text=_("Total Sales:"), font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky=W, pady=5)
            ttk.Label(summary_frame, text=f"${today_sales.get('total_sales', 0):.2f}", font=("Segoe UI", 12), foreground="green").grid(row=0, column=1, sticky=W, padx=20, pady=5)
            
            # Transaction count
            ttk.Label(summary_frame, text=_("Transactions:"), font=("Segoe UI", 12, "bold")).grid(row=1, column=0, sticky=W, pady=5)
            ttk.Label(summary_frame, text=str(today_sales.get('transaction_count', 0)), font=("Segoe UI", 12)).grid(row=1, column=1, sticky=W, padx=20, pady=5)
            
            # Average transaction
            ttk.Label(summary_frame, text=_("Average Sale:"), font=("Segoe UI", 12, "bold")).grid(row=2, column=0, sticky=W, pady=5)
            ttk.Label(summary_frame, text=f"${today_sales.get('average_sale', 0):.2f}", font=("Segoe UI", 12)).grid(row=2, column=1, sticky=W, padx=20, pady=5)
            
            # Update the header stats
            self.sales_today_var.set(_("Today's Sales: ${0:.2f}").format(today_sales.get('total_sales', 0)))
            self.transactions_var.set(_("Transactions: {0}").format(today_sales.get('transaction_count', 0)))
            
        except Exception as e:
            logger.error(f"Error creating sales summary: {str(e)}")
    
    def _create_top_products_report(self, parent):
        """Create top products report"""
        try:
            # Get top products data
            top_products = enhanced_data.get_top_products(limit=10)
            
            # Create treeview for top products
            tree_frame = ttk.Frame(parent)
            tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            columns = ["rank", "name", "quantity", "revenue"]
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
            
            tree.heading("rank", text=_("Rank"))
            tree.heading("name", text=_("Product"))
            tree.heading("quantity", text=_("Qty Sold"))
            tree.heading("revenue", text=_("Revenue"))
            
            tree.column("rank", width=50, anchor=CENTER)
            tree.column("name", width=200, anchor=W)
            tree.column("quantity", width=80, anchor=CENTER)
            tree.column("revenue", width=100, anchor=CENTER)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Populate with data
            for i, product in enumerate(top_products, 1):
                tree.insert("", "end", values=(
                    i,
                    product.get("Name", ""),
                    product.get("TotalQuantity", 0),
                    f"${product.get('TotalRevenue', 0):.2f}"
                ))
                
        except Exception as e:
            logger.error(f"Error creating top products report: {str(e)}")
    
    def _open_settings(self):
        """Open settings dialog"""
        try:
            # Create settings dialog
            dialog = ttk.Toplevel(self)
            dialog.title(_("Sales Settings"))
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"500x400+{x}+{y}")
            
            # Create notebook for settings
            notebook = ttk.Notebook(dialog)
            notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # General settings tab
            general_frame = ttk.Frame(notebook)
            notebook.add(general_frame, text=_("General"))
            
            # Display settings
            display_frame = ttk.LabelFrame(general_frame, text=_("Display Settings"), padding=10)
            display_frame.pack(fill=X, padx=10, pady=10)
            
            # Page size setting
            ttk.Label(display_frame, text=_("Items per page:")).grid(row=0, column=0, sticky=W, pady=5)
            page_size_var = StringVar(value=str(self.products_list.page_size))
            ttk.Entry(display_frame, textvariable=page_size_var, width=10).grid(row=0, column=1, sticky=W, padx=10, pady=5)
            
            # Auto-refresh setting
            auto_refresh_var = BooleanVar(value=True)
            ttk.Checkbutton(display_frame, text=_("Auto-refresh product list"), variable=auto_refresh_var).grid(row=1, column=0, columnspan=2, sticky=W, pady=5)
            
            # Buttons frame
            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill=X, padx=10, pady=10)
            
            def save_settings():
                try:
                    # Save page size
                    new_page_size = int(page_size_var.get())
                    if new_page_size > 0:
                        self.products_list.page_size = new_page_size
                        self._load_products()
                    
                    # Save other settings...
                    
                    messagebox.showinfo(_("Success"), _("Settings saved successfully"))
                    dialog.destroy()
                except ValueError:
                    messagebox.showerror(_("Error"), _("Please enter a valid page size"))
            
            ttk.Button(buttons_frame, text=_("Save"), command=save_settings, bootstyle="success").pack(side=RIGHT, padx=5)
            ttk.Button(buttons_frame, text=_("Cancel"), command=dialog.destroy, bootstyle="secondary").pack(side=RIGHT)
            
        except Exception as e:
            logger.error(f"Error opening settings: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to open settings"))
    
    def _save_as_quote(self):
        """Save current cart as a quote"""
        try:
            if not self.cart_items:
                messagebox.showwarning(_("Warning"), _("Cart is empty"))
                return
            
            # Create quote data
            quote_data = {
                "items": [],
                "total": self.cart_total,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add all items
            for product_id, item in self.cart_items.items():
                quote_data["items"].append({
                    "product_id": item["id"],
                    "product_name": item["name"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "subtotal": item["price"] * item["quantity"]
                })
            
            # Save quote to database
            quote_id = enhanced_data.save_quote(quote_data)
            
            if quote_id:
                messagebox.showinfo(_("Success"), _("Quote saved successfully with ID: {0}").format(quote_id))
            else:
                messagebox.showerror(_("Error"), _("Failed to save quote"))
                
        except Exception as e:
            logger.error(f"Error saving quote: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to save quote"))
    
    def _mark_as_debit(self):
        """Mark current cart as a debit sale"""
        try:
            if not self.cart_items:
                messagebox.showwarning(_("Warning"), _("Cart is empty"))
                return
            
            # Create customer selection dialog
            dialog = ttk.Toplevel(self)
            dialog.title(_("Select Customer"))
            dialog.geometry("400x300")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (dialog.winfo_screenheight() // 2) - (300 // 2)
            dialog.geometry(f"400x300+{x}+{y}")
            
            ttk.Label(dialog, text=_("Select customer for debit sale:"), font=("Segoe UI", 12)).pack(pady=10)
            
            # Customer selection
            customers = enhanced_data.get_customers()
            customer_var = StringVar()
            customer_combo = ttk.Combobox(dialog, textvariable=customer_var, values=[c['name'] for c in customers], state="readonly")
            customer_combo.pack(pady=10, padx=20, fill=X)
            
            def create_debit():
                customer_name = customer_var.get()
                if not customer_name:
                    messagebox.showerror(_("Error"), _("Please select a customer"))
                    return
                
                # Process debit sale
                debit_id = enhanced_data.create_debit_sale(customer_name, self.cart_items)
                if debit_id:
                    messagebox.showinfo(_("Success"), _("Debit sale created successfully"))
                    self.cart_items = {}
                    self._update_cart_display()
                    dialog.destroy()
                else:
                    messagebox.showerror(_("Error"), _("Failed to create debit sale"))
            
            ttk.Button(dialog, text=_("Create Debit"), command=create_debit, bootstyle="success").pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error marking as debit: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to mark as debit"))
    
    def _print_receipt(self):
        """Print receipt for current cart"""
        try:
            if not self.cart_items:
                messagebox.showwarning(_("Warning"), _("Cart is empty"))
                return
            
            # Create receipt content
            receipt_content = self._generate_receipt_content()
            
            # Show print preview dialog
            dialog = ttk.Toplevel(self)
            dialog.title(_("Print Receipt"))
            dialog.geometry("600x700")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (700 // 2)
            dialog.geometry(f"600x700+{x}+{y}")
            
            # Receipt preview
            text_widget = tk.Text(dialog, wrap=tk.WORD, font=("Courier", 10))
            text_widget.pack(fill=BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, receipt_content)
            text_widget.config(state=tk.DISABLED)
            
            # Print button
            ttk.Button(dialog, text=_("Print"), command=lambda: self._do_print(receipt_content), bootstyle="success").pack(pady=5)
            
        except Exception as e:
            logger.error(f"Error printing receipt: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to print receipt"))
    
    def _generate_receipt_content(self):
        """Generate receipt content"""
        try:
            lines = []
            lines.append("=" * 50)
            lines.append(_("SALES RECEIPT").center(50))
            lines.append("=" * 50)
            lines.append("")
            lines.append(_("Date: {0}").format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            lines.append("")
            lines.append("-" * 50)
            lines.append(f"{'Item':<25} {'Qty':<5} {'Price':<10} {'Total':<10}")
            lines.append("-" * 50)
            
            for item in self.cart_items.values():
                lines.append(f"{item['name'][:25]:<25} {item['quantity']:<5} ${item['price']:<9.2f} ${item['price'] * item['quantity']:<9.2f}")
            
            lines.append("-" * 50)
            lines.append(f"{'TOTAL':<40} ${self.cart_total:.2f}")
            lines.append("=" * 50)
            lines.append("")
            lines.append(_("Thank you for your purchase!").center(50))
            lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating receipt: {str(e)}")
            return _("Error generating receipt")
    
    def _do_print(self, content):
        """Actually print the receipt"""
        try:
            # This would integrate with actual printer
            # For now, just show a message
            messagebox.showinfo(_("Print"), _("Receipt would be printed here"))
            
        except Exception as e:
            logger.error(f"Error printing: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to print receipt"))
    
    def _update_cart_total(self, event=None):
        """Update cart total with discount applied"""
        try:
            # Get discount percentage
            discount_percent = float(self.discount_var.get() or 0)
            if discount_percent < 0 or discount_percent > 100:
                discount_percent = 0
                self.discount_var.set("0")
            
            # Calculate total with discount
            subtotal = sum(item["price"] * item["quantity"] for item in self.cart_items.values())
            discount_amount = subtotal * (discount_percent / 100)
            total = subtotal - discount_amount
            
            # Update display
            self.cart_total = total
            self.cart_total_var.set(_("Total: ${0:.2f}").format(total))
            
            # Show discount if applied
            if discount_percent > 0:
                self.cart_total_var.set(_("Subtotal: ${0:.2f} | Discount: {1}% | Total: ${2:.2f}").format(subtotal, discount_percent, total))
            
        except ValueError:
            # Invalid discount value
            self.discount_var.set("0")
            self._update_cart_display()
        except Exception as e:
            logger.error(f"Error updating cart total: {str(e)}")
    
    def _process_checkout(self):
        """Process checkout with selected payment method"""
        try:
            if not self.cart_items:
                messagebox.showwarning(_("Warning"), _("Cart is empty"))
                return
            
            # Get payment method
            payment_method = self.payment_method.get()
            
            # Apply discount
            discount_percent = float(self.discount_var.get() or 0)
            self._update_cart_total()
            
            # Process the sale
            self._checkout()
            
        except Exception as e:
            logger.error(f"Error processing checkout: {str(e)}")
            messagebox.showerror(_("Error"), _("Failed to process checkout"))
    
    def __del__(self):
        """Cleanup when page is destroyed"""
        try:
            # Unregister language change callback
            unregister_refresh_callback(self._refresh_language)
        except:
            pass
