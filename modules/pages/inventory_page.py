import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import (
    BOTH, END, CENTER, W, E, X, Y, LEFT, RIGHT, TOP,
    HORIZONTAL, BOTTOM, messagebox, StringVar, BooleanVar
)
from modules.db_manager import get_connection, ConnectionContext, return_connection
from modules.data_access import get_products, invalidate_cache
from modules.utils import chunk_process, run_in_background
import random  # Added import for generating random barcode
import datetime  # Added import for datetime
import logging

# Import internationalization support
from modules.i18n import _, tr, register_refresh_callback, unregister_refresh_callback, set_widget_direction

# Configure logger
logger = logging.getLogger(__name__)

# Message-ID constants (English base text)
MSG_INVENTORY_MANAGEMENT = "Inventory Management"
MSG_BACK_HOME = "Back to Home"
MSG_INVENTORY_STATISTICS = "Inventory Statistics"
MSG_TOTAL_PRODUCTS = "Total Products"
MSG_INVENTORY_VALUE = "Inventory Value"
MSG_LOW_STOCK_ITEMS = "Low Stock Items"
MSG_CATEGORIES = "Categories"
MSG_ADD_CATEGORY = "Add Category"
MSG_SEARCH = "Search"
MSG_CLEAR = "Clear"
MSG_SHOW_OUT_OF_STOCK = "Show Out of Stock"
MSG_REFRESH_DATA = "Refresh Data"
MSG_PRODUCT_ID = "ID"
MSG_PRODUCT_NAME = "Product Name"
MSG_SELL_PRICE = "Sell Price"
MSG_BUY_PRICE = "Buy Price"
MSG_STOCK = "Stock"
MSG_CATEGORY = "Category"
MSG_ADD_PRODUCT = "Add Product"
MSG_EDIT_PRODUCT = "Edit Product"
MSG_DELETE_PRODUCT = "Delete Product"
MSG_SAVE = "Save"
MSG_CANCEL = "Cancel"

class InventoryPage(ttk.Frame):
    """
    Inventory management – shows categories at the top and then the products in a table.
    The add/edit form now includes Selling Price, Buying Price, and a Record‑Loss section.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        self._current_category = None
        self._sort_by = "ProductID"  # Default sort column
        self._sort_reverse = False   # Default sort order (ascending)
        
        # Track active background tasks
        self._active_tasks = {
            "loading_products": False
        }
        
        # Create text variables for dynamic content
        self.title_text = StringVar()
        self.back_btn_text = StringVar()
        self.total_products_var = StringVar(value=f"{tr(MSG_TOTAL_PRODUCTS)}: 0")
        self.total_value_var = StringVar(value=f"{tr(MSG_INVENTORY_VALUE)}: $0.00")
        self.low_stock_var = StringVar(value=f"{tr(MSG_LOW_STOCK_ITEMS)}: 0")
        self.categories_text = StringVar()
        self.add_category_text = StringVar()
        self.search_text = StringVar()
        self.search_btn_text = StringVar()
        self.clear_btn_text = StringVar()
        self.show_out_of_stock_text = StringVar()
        self.refresh_btn_text = StringVar()
        self.column_headers = {
            "id": StringVar(),
            "name": StringVar(),
            "price": StringVar(),
            "buy_price": StringVar(),
            "stock": StringVar(),
            "category": StringVar()
        }
        self.add_product_text = StringVar()
        self.edit_product_text = StringVar()
        self.delete_product_text = StringVar()
        self.save_btn_text = StringVar()
        self.cancel_btn_text = StringVar()
        
        # Build the UI and register for language changes
        self._build_ui()
        self._retranslate()
        register_refresh_callback(self._retranslate)

    # ------------------------------------------------------------------
    def _make_topbar(self, title: str):
        top = ttk.Frame(self, style="TFrame", padding=10)
        top.pack(fill=X)
        
        self.title_label = ttk.Label(top, textvariable=self.title_text, style="Header.TLabel")
        self.title_label.pack(side=LEFT, padx=(10, 20))
        
        self.back_btn = ttk.Button(
            top, 
            textvariable=self.back_btn_text, 
            style="Small.TButton",
            bootstyle=SECONDARY,
            command=lambda: self.controller.show_frame("MainMenuPage")
        )
        self.back_btn.pack(side=RIGHT, padx=20)

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Set widget direction based on language
        set_widget_direction(self)
        
        self._make_topbar(tr(MSG_INVENTORY_MANAGEMENT))

        # Stats section at the top - using text instead of textvariable
        self.stats_frame = ttk.LabelFrame(self, text=tr(MSG_INVENTORY_STATISTICS), padding=10)
        self.stats_frame.pack(fill=X, padx=10, pady=10)
        
        # Create 3-column grid for stats
        ttk.Label(self.stats_frame, textvariable=self.total_products_var, font=("Helvetica", 14)).grid(row=0, column=0, padx=20, pady=5, sticky="w")
        ttk.Label(self.stats_frame, textvariable=self.total_value_var, font=("Helvetica", 14)).grid(row=0, column=1, padx=20, pady=5, sticky="w")
        ttk.Label(self.stats_frame, textvariable=self.low_stock_var, font=("Helvetica", 14)).grid(row=0, column=2, padx=20, pady=5, sticky="w")
        
        # Configure grid
        self.stats_frame.columnconfigure(0, weight=1)
        self.stats_frame.columnconfigure(1, weight=1)
        self.stats_frame.columnconfigure(2, weight=1)

        # Create main content container
        content_container = ttk.Frame(self)
        content_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Left column - Categories nav sidebar (fixed width)
        category_sidebar = ttk.Frame(content_container, width=250)
        category_sidebar.pack(side=LEFT, fill=Y, padx=(0, 10))
        category_sidebar.pack_propagate(False)  # Prevent sidebar from shrinking
        
        # Categories header and button container
        cat_header_frame = ttk.Frame(category_sidebar)
        cat_header_frame.pack(fill=X, pady=(0, 10))
        
        # Categories label
        ttk.Label(cat_header_frame, textvariable=self.categories_text, font=("Helvetica", 16, "bold")).pack(side=LEFT)
        
        # Add Category button
        add_cat_btn = ttk.Button(
            cat_header_frame, 
            textvariable=self.add_category_text, 
            style="Outline.TButton",
            command=self._add_new_category
        )
        add_cat_btn.pack(side=RIGHT)
        
        # Category buttons in scrollable frame
        categories_frame = ttk.Frame(category_sidebar)
        categories_frame.pack(fill=BOTH, expand=True)
        
        # Store the frame as an instance attribute so _retranslate can access it
        self.categories_frame = categories_frame
        
        # Add category buttons
        categories = ["Juice", "Eggs", "Snacks", "Milk & Dairy", "Ice Cream", "Staple Food"]
        for cat in categories:
            btn = ttk.Button(
                categories_frame, text=cat, style="Outline.TButton",
                command=lambda c=cat: self._filter_by_category(c)
            )
            btn.pack(fill=X, pady=2)
        
        # Right side content area
        right_area = ttk.Frame(content_container)
        right_area.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Create a PanedWindow to divide product list and forms
        paned = ttk.PanedWindow(right_area, orient="vertical")
        paned.pack(fill=BOTH, expand=True)
        
        # Top section - Product list
        product_section = ttk.Frame(paned)
        paned.add(product_section, weight=60)  # 60% of the space
        
        # Search and filter bar
        search_frame = ttk.Frame(product_section)
        search_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(search_frame, textvariable=self.search_text, font=("Helvetica", 14)).pack(side=LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30, font=("Helvetica", 14))
        self.search_entry.pack(side=LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda event: self._search_products())
        
        ttk.Button(
            search_frame, textvariable=self.search_btn_text, style="Accent.TButton",
            command=self._search_products
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            search_frame, textvariable=self.clear_btn_text, style="Secondary.TButton",
            command=self._clear_search
        ).pack(side=LEFT, padx=5)
        
        # In stock filter
        self.show_out_of_stock_var = BooleanVar(value=True)
        ttk.Checkbutton(
            search_frame, textvariable=self.show_out_of_stock_text, variable=self.show_out_of_stock_var,
            command=self._search_products
        ).pack(side=LEFT, padx=20)
        
        # Refresh button
        ttk.Button(
            search_frame, textvariable=self.refresh_btn_text, style="Accent.TButton",
            command=self._refresh_table
        ).pack(side=RIGHT, padx=5)
        
        # Product list
        list_frame = ttk.Frame(product_section)
        list_frame.pack(fill=BOTH, expand=True)
        
        # Create treeview for products
        columns = ("id", "name", "price", "buy_price", "stock", "category")
        self.product_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings",
            style="Treeview"
        )
        
        # Configure treeview header variables
        for col, var in self.column_headers.items():
            self.product_tree.heading(col, text=var.get())
        
        self.product_tree.column("id", width=50, anchor="center")
        self.product_tree.column("name", width=200, anchor="w")
        self.product_tree.column("price", width=80, anchor="e")
        self.product_tree.column("buy_price", width=80, anchor="e")
        self.product_tree.column("stock", width=60, anchor="center")
        self.product_tree.column("category", width=120, anchor="w")
        
        # Configure appearance
        self.product_tree.tag_configure("lowstock", background="#D07070", foreground="black")
        self.product_tree.tag_configure("outofstock", background="#FF8080", foreground="black")
        # Add style for "load more" indicator
        self.product_tree.tag_configure("load_more", background="#CCCCFF", foreground="#333399", font=("Helvetica", 10, "italic"))
        
        # Add scrollbar
        tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=tree_scroll.set)
        
        tree_scroll.pack(side=RIGHT, fill=Y)
        self.product_tree.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Event binding - double click to load product for editing
        self.product_tree.bind("<Double-1>", self._load_product_for_edit)
        
        # Bottom section - Forms
        form_section = ttk.Frame(paned)
        paned.add(form_section, weight=40)  # 40% of the space
        
        # Create a notebook for different forms
        form_notebook = ttk.Notebook(form_section)
        form_notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Add Product tab
        add_product_tab = ttk.Frame(form_notebook, padding=10)
        form_notebook.add(add_product_tab, text=tr(MSG_ADD_PRODUCT))
        
        # Edit Product tab
        edit_product_tab = ttk.Frame(form_notebook, padding=10)
        form_notebook.add(edit_product_tab, text=tr(MSG_EDIT_PRODUCT))
        
        # Delete Product tab
        delete_product_tab = ttk.Frame(form_notebook, padding=10)
        form_notebook.add(delete_product_tab, text=tr(MSG_DELETE_PRODUCT))
        
        # Build product form UI
        self._build_add_product_form(add_product_tab)
        self._build_edit_product_form(edit_product_tab)
        self._build_delete_product_form(delete_product_tab)
        
        # Further initialization
        self._setup_scroll_binding()
        self._load_products()
        
    def _retranslate(self):
        """Update all text elements with translated strings"""
        # Set widget direction based on language
        set_widget_direction(self)
        
        # Update all text elements with translated strings
        self.back_btn.configure(text=_("Back to Main Menu"))
        self.title_label.configure(text=_("Inventory Management"))
        
        # Update category labels - Fix: The category_frame attribute doesn't exist
        # Check if we have a categories_frame attribute from _build_ui
        if hasattr(self, 'categories_frame'):
            for btn in self.categories_frame.winfo_children():
                if isinstance(btn, ttk.Button):
                    btn.configure(text=_(btn.cget('text')))
        
        # Update column headers if treeview exists
        if hasattr(self, 'product_tree'):
            self.product_tree.heading('id', text=_("ID"))
            self.product_tree.heading('name', text=_("Product Name"))
            self.product_tree.heading('category', text=_("Category"))
            self.product_tree.heading('price', text=_("Selling Price"))
            self.product_tree.heading('buy_price', text=_("Buying Price"))
            self.product_tree.heading('stock', text=_("Stock"))
        
        # Update action buttons
        if hasattr(self, 'actions_frame'):
            for btn in self.actions_frame.winfo_children():
                if isinstance(btn, ttk.Button):
                    if 'add' in btn['text'].lower():
                        btn.configure(text=_("Add Product"))
                    elif 'edit' in btn['text'].lower():
                        btn.configure(text=_("Edit Selected"))
                    elif 'delete' in btn['text'].lower():
                        btn.configure(text=_("Delete Selected"))
                    elif 'refresh' in btn['text'].lower():
                        btn.configure(text=_("Refresh"))
        
        # Update LabelFrame text directly since it doesn't support textvariable
        if hasattr(self, 'stats_frame'):
            self.stats_frame.configure(text=tr(MSG_INVENTORY_STATISTICS))
        
        # Update statistic values while preserving the numbers
        if hasattr(self, 'total_products_var'):
            current_value = self.total_products_var.get().split(':')[-1].strip()
            self.total_products_var.set(f"{tr(MSG_TOTAL_PRODUCTS)}: {current_value}")
        
        if hasattr(self, 'total_value_var'):
            current_value = self.total_value_var.get().split(':')[-1].strip()
            self.total_value_var.set(f"{tr(MSG_INVENTORY_VALUE)}: {current_value}")
        
        if hasattr(self, 'low_stock_var'):
            current_value = self.low_stock_var.get().split(':')[-1].strip()
            self.low_stock_var.set(f"{tr(MSG_LOW_STOCK_ITEMS)}: {current_value}")
        
        # Update other text variables
        if hasattr(self, 'categories_text'):
            self.categories_text.set(tr(MSG_CATEGORIES))
        
        if hasattr(self, 'add_category_text'):
            self.add_category_text.set(tr(MSG_ADD_CATEGORY))
        
        if hasattr(self, 'search_text'):
            self.search_text.set(tr(MSG_SEARCH))
        
        if hasattr(self, 'search_btn_text'):
            self.search_btn_text.set(tr(MSG_SEARCH))
        
        if hasattr(self, 'clear_btn_text'):
            self.clear_btn_text.set(tr(MSG_CLEAR))
        
        if hasattr(self, 'show_out_of_stock_text'):
            self.show_out_of_stock_text.set(tr(MSG_SHOW_OUT_OF_STOCK))
        
        if hasattr(self, 'refresh_btn_text'):
            self.refresh_btn_text.set(tr(MSG_REFRESH_DATA))
        
        # Update column headers
        if hasattr(self, 'column_headers'):
            if 'id' in self.column_headers:
                self.column_headers["id"].set(tr(MSG_PRODUCT_ID))
            if 'name' in self.column_headers:
                self.column_headers["name"].set(tr(MSG_PRODUCT_NAME))
            if 'price' in self.column_headers:
                self.column_headers["price"].set(tr(MSG_SELL_PRICE))
            if 'buy_price' in self.column_headers:
                self.column_headers["buy_price"].set(tr(MSG_BUY_PRICE))
            if 'stock' in self.column_headers:
                self.column_headers["stock"].set(tr(MSG_STOCK))
            if 'category' in self.column_headers:
                self.column_headers["category"].set(tr(MSG_CATEGORY))
        
        # Update treeview headers
        if hasattr(self, 'product_tree') and hasattr(self, 'column_headers'):
            for col, var in self.column_headers.items():
                self.product_tree.heading(col, text=var.get())

    def __del__(self):
        """Unregister the callback when the widget is destroyed"""
        unregister_refresh_callback(self._retranslate)

    # ------------------------------------------------------------------
    def _show_items(self, category):
        self._current_category = category
        self.cat_lbl.config(text=f"Category: {category}")
        self._refresh_table()

    # ------------------------------------------------------------------
    def _sort_by_column(self, column):
        """Sort tree contents when a column header is clicked"""
        # If clicking the same column, reverse the sort order
        if self._sort_by == self._col_mapping.get(column, column):
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_reverse = False
            
        # Special case for Profit Margin which is calculated, not in DB
        if column == "Profit Margin":
            self._sort_by = "ProfitMargin"  # Custom identifier
        else:
            self._sort_by = self._col_mapping.get(column, column)
            
        # Refresh the table with the new sort order
        if self._current_category:
            self._refresh_table()
        elif self.search_var.get().strip():
            self._search_products()

    # ------------------------------------------------------------------
    def _refresh_table(self):
        # Clear existing data
        self.product_tree.delete(*self.product_tree.get_children())
        
        if not self._current_category:
            return
        
        # Add temporary loading indicator
        self.product_tree.insert("", "end", values=("Loading...", "", "", "", "", ""))
        
        # Save button states to restore later
        buttons = []
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Button) and widget.winfo_ismapped():
                buttons.append((widget, widget['state']))
                widget['state'] = 'disabled'
            
        # Track active task
        if not hasattr(self, '_active_tasks'):
            self._active_tasks = {}
        self._active_tasks["loading_products"] = True
        
        # Store all rows for lazy loading
        if not hasattr(self, '_all_product_rows'):
            self._all_product_rows = []
        self._all_product_rows = []
        self._current_page = 0
        self._rows_per_page = 100  # Number of items to load at once
        
        # Function to fetch data in background
        def fetch_products_data():
            with ConnectionContext() as conn:
                cur = conn.cursor()
                
                try:
                    # Handle special profit margin sort
                    if self._sort_by == "ProfitMargin":
                        # We can't sort by profit margin in SQL, so fetch all and sort in Python
                        cur.execute("""
                            SELECT ProductID, Name, SellingPrice, BuyingPrice, Stock, Category
                        FROM Products
                        WHERE Category = ?
                        """, (self._current_category,))
                        rows = cur.fetchall()
                        
                        # Calculate profit margins and sort
                        def calc_margin(row):
                            selling, buying = row[2], row[3]
                            if buying > 0:
                                return ((selling - buying) / buying) * 100
                            return 0
                            
                        rows = sorted(rows, key=calc_margin, reverse=self._sort_reverse)
                    else:
                        # Normal column sorting via SQL
                        order = "DESC" if self._sort_reverse else "ASC"
                        cur.execute(f"""
                            SELECT ProductID, Name, SellingPrice, BuyingPrice, Stock, Category
                            FROM Products
                            WHERE Category = ?
                            ORDER BY {self._sort_by} {order}
                        """, (self._current_category,))
                        rows = cur.fetchall()
                        
                    return rows
                except Exception as e:
                    logger.error(f"Error fetching products: {str(e)}")
                    raise
            # Connection is automatically returned to the pool by ConnectionContext
        
        # Handle the data once it's fetched
        def handle_loaded_data(rows):
            # Check if widget still exists and task is still active
            if not self.winfo_exists() or not self._active_tasks["loading_products"]:
                return
            
            # Clear the temporary loading indicator
            self.product_tree.delete(*self.product_tree.get_children())
            
            # Store all rows for lazy loading
            self._all_product_rows = rows
            
            # Set up scroll binding if not already done
            if not hasattr(self, '_scroll_binding_set'):
                self._setup_scroll_binding()
                self._scroll_binding_set = True
            
            # Load the first page
            self._load_next_page()
            
            # Update statistics
            self._update_statistics()
            
            # Re-enable buttons
            for button, state in buttons:
                try:
                    button['state'] = state
                except:
                    pass  # Button might have been destroyed
            
            # Mark task as complete
            self._active_tasks["loading_products"] = False
        
        # Process error
        def handle_error(error):
            # Check if widget still exists and task is still active
            if not self.winfo_exists() or not self._active_tasks["loading_products"]:
                return
            
            # Clear the temporary loading indicator
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)
            
            self.product_tree.insert(
                "", "end", 
                values=(f"Error loading products: {str(error)}", "", "", "", "", "")
            )
            logger.error(f"Error loading products: {str(error)}")
            
            # Re-enable buttons
            for button, state in buttons:
                try:
                    button['state'] = state
                except:
                    pass  # Button might have been destroyed
                
            # Mark task as complete
            self._active_tasks["loading_products"] = False
        
        # Load data in background
        run_in_background(
            fetch_products_data,
            on_complete=handle_loaded_data,
            on_error=handle_error
        )
    
    def _setup_scroll_binding(self):
        """Set up binding to detect when user scrolls near bottom of the Treeview"""
        self.product_tree.bind('<MouseWheel>', self._on_treeview_scroll)
        # Bind for Linux scroll events
        self.product_tree.bind('<Button-4>', self._on_treeview_scroll)
        self.product_tree.bind('<Button-5>', self._on_treeview_scroll)
        # Additional binding for scrollbar
        self.product_tree.bind('<<TreeviewSelect>>', self._on_treeview_scroll)
    
    def _on_treeview_scroll(self, event=None):
        """Check if we need to load more items as user scrolls"""
        if not hasattr(self, '_all_product_rows') or not self._all_product_rows:
            return
            
        # If we've already loaded all rows, no need to check
        if self._current_page * self._rows_per_page >= len(self._all_product_rows):
            return
            
        # Check if user is near bottom of the list
        items = self.product_tree.get_children()
        if not items:
            return
            
        # Get the last visible item
        try:
            last_visible_item = self.product_tree.identify_row(self.product_tree.winfo_height() - 10)
            if not last_visible_item:
                return
                
            # If we're within 5 items of the end, load more
            last_idx = items.index(last_visible_item)
            if last_idx >= len(items) - 5:
                self._load_next_page()
        except (ValueError, IndexError):
            # If there's an error identifying rows, just check if we're at the last item
            self._load_next_page()
    
    def _load_next_page(self):
        """Load the next page of items into the Treeview"""
        if not hasattr(self, '_all_product_rows') or not self._all_product_rows:
            return
            
        start_idx = self._current_page * self._rows_per_page
        end_idx = min(start_idx + self._rows_per_page, len(self._all_product_rows))
        
        # If we're at the end, no more to load
        if start_idx >= len(self._all_product_rows):
            return
            
        # Process this chunk of rows
        rows_to_load = self._all_product_rows[start_idx:end_idx]
        for i, row in enumerate(rows_to_load):
            pid, name, selling_price, buying_price, stock, category = row
            
            # Determine stock status
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            if stock <= 0:
                tag = "outofstock_even" if i % 2 == 0 else "outofstock_odd"
            elif stock <= 5:  # Assuming 5 is low stock threshold
                tag = "lowstock_even" if i % 2 == 0 else "lowstock_odd"
            
            self.product_tree.insert(
                "", END, 
                values=(pid, name, f"{selling_price:.2f}", buying_price, stock, category), 
                tags=(tag,)
            )
        
        # Update the current page
        self._current_page += 1
        
        # If we still have more rows, add a "Load more..." entry
        if end_idx < len(self._all_product_rows):
            remaining = len(self._all_product_rows) - end_idx
            self.product_tree.insert(
                "", END, 
                values=(f"Scroll to load {remaining} more items...", "", "", "", "", ""),
                tags=("load_more",)
            )

    # ------------------------------------------------------------------
    def _search_products(self):
        # Initialize search_var if it doesn't exist
        if not hasattr(self, 'search_var'):
            self.search_var = StringVar()
            self.search_var.set(self.search_entry.get())
        else:
            self.search_var.set(self.search_entry.get())
            
        search_term = self.search_var.get().strip().lower()
        if not search_term:
            if self._current_category:
                self._refresh_table()
            return
            
        self.product_tree.delete(*self.product_tree.get_children())
        
        # Use ConnectionContext instead of direct connection management
        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            # Handle special profit margin sort
            if self._sort_by == "ProfitMargin":
                # We can't sort by profit margin in SQL, so fetch all and sort in Python
                query = """
                    SELECT ProductID, Name, SellingPrice, BuyingPrice, Stock, Category
                    FROM Products
                    WHERE LOWER(Name) LIKE ?
                """
                cur.execute(query, (f'%{search_term}%',))
                rows = cur.fetchall()
                
                # Calculate profit margins and sort
                def calc_margin(row):
                    selling, buying = row[2], row[3]
                    if buying > 0:
                        return ((selling - buying) / buying) * 100
                    return 0
                    
                rows = sorted(rows, key=calc_margin, reverse=self._sort_reverse)
            else:
                # Normal column sorting via SQL
                order = "DESC" if self._sort_reverse else "ASC"
                query = f"""
                    SELECT ProductID, Name, SellingPrice, BuyingPrice, Stock, Category
                    FROM Products
                    WHERE LOWER(Name) LIKE ?
                    ORDER BY {self._sort_by} {order}
                """
                cur.execute(query, (f'%{search_term}%',))
                rows = cur.fetchall()
            
            # Display rows
            for i, row in enumerate(rows):
                pid, name, price = row[0], row[1], row[2]
                stock = row[3]
                category = row[4] if len(row) > 4 else ""
                
                # Determine stock status
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                if stock <= 0:
                    tag = "outofstock_even" if i % 2 == 0 else "outofstock_odd"
                elif stock <= 5:  # Use hard-coded threshold for now
                    tag = "lowstock_even" if i % 2 == 0 else "lowstock_odd"
                    
                # Create a new row with the data
                self.product_tree.insert("", END, values=(pid, name, f"{price:.2f}", stock, category), tags=(tag,))
        
        # Connection is automatically returned to the pool by ConnectionContext
        
        # Update statistics
        self._update_statistics()

    # ------------------------------------------------------------------
    def _clear_search(self):
        if hasattr(self, 'search_var'):
            self.search_var.set("")
        self.search_entry.delete(0, END)
        self.search_entry.focus_set()
        if self._current_category:
            self._refresh_table()
        else:
            self.product_tree.delete(*self.product_tree.get_children())

    # ------------------------------------------------------------------
    def _add_product(self):
        """Add a new product or update existing one"""
        # Get form values
        name = self.name_entry.get().strip()
        sell_price_str = self.selling_entry.get().strip()
        buy_price_str = self.buying_entry.get().strip()
        stock_str = self.stock_entry.get().strip()
        category = self.category_var.get()
        barcode = self.barcode_entry.get().strip()
        
        # Validate inputs
        if not name:
            messagebox.showwarning("Missing Data", "Product name is required")
            return
            
        try:
            sell_price = float(sell_price_str) if sell_price_str else 0.0
            buy_price = float(buy_price_str) if buy_price_str else 0.0
            stock = int(stock_str) if stock_str else 0
        except ValueError:
            messagebox.showwarning("Invalid Data", "Price must be a number and stock must be an integer")
            return

        # Check if updating or adding
        product_id_text = self.product_id_var.get()
        is_update = product_id_text != "Product ID: New"
        
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            if is_update:
                # Extract ID from text
                product_id = int(product_id_text.split(': ')[1])
                
                # Update existing product
                cur.execute("""
                    UPDATE Products 
                    SET Name = ?, SellingPrice = ?, BuyingPrice = ?, Stock = ?, Category = ?, Barcode = ?
                    WHERE ProductID = ?
                """, (name, sell_price, buy_price, stock, category, barcode, product_id))
                
                messagebox.showinfo("Success", f"Product '{name}' has been updated")
            else:
                # Add new product
                cur.execute("""
                    INSERT INTO Products (Name, SellingPrice, BuyingPrice, Stock, Category, Barcode)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, sell_price, buy_price, stock, category, barcode))
                
                messagebox.showinfo("Success", f"Product '{name}' has been added")
                
            conn.commit()
            
            # Import and invalidate the product cache
            invalidate_cache('products')
            
            # Clear form and refresh
            self._clear_form()
            self._load_products()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"Error saving product: {str(e)}")
        finally:
            return_connection(conn)

    # ------------------------------------------------------------------
    def _update_stock(self, direction):
        """Update stock quantity (increase or decrease)"""
        # Get product ID and quantity
        pid_str = self.manage_id_entry.get().strip()
        qty_str = self.quantity_entry.get().strip()
        
        # Validate inputs
        if not pid_str:
            messagebox.showwarning("Missing Data", "Product ID is required")
            return
            
        try:
            pid = int(pid_str)
            qty = int(qty_str) if qty_str else 1
        except ValueError:
            messagebox.showwarning("Invalid Data", "Product ID and quantity must be integers")
            return

        # Apply direction
        qty = qty * direction
        
        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            try:
                # Check if product exists and get current stock
                cur.execute("SELECT Name, Stock FROM Products WHERE ProductID = ?", (pid,))
                row = cur.fetchone()
                
                if not row:
                    messagebox.showwarning("Not Found", f"No product found with ID {pid}")
                    return
                    
                name, current_stock = row
                new_stock = current_stock + qty
                
                # Validate new stock level
                if new_stock < 0:
                    messagebox.showwarning("Invalid Stock", f"Cannot reduce stock below 0. Current stock: {current_stock}")
                    return
                    
                # Update stock
                cur.execute("UPDATE Products SET Stock = ? WHERE ProductID = ?", (new_stock, pid))
                conn.commit()
                
                action = "increased" if direction > 0 else "decreased"
                messagebox.showinfo("Success", f"Stock for '{name}' {action} by {abs(qty)}. New stock: {new_stock}")
                
                # Refresh display
                self._load_products()
                
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Database Error", f"Error updating stock: {str(e)}")

    # ------------------------------------------------------------------
    def _delete_product(self):
        """Delete a product from the database"""
        # Get product ID
        pid_str = self.manage_id_entry.get().strip()
        
        # Validate input
        if not pid_str:
            messagebox.showwarning("Missing Data", "Product ID is required")
            return
            
        try:
            pid = int(pid_str)
        except ValueError:
            messagebox.showwarning("Invalid Data", "Product ID must be an integer")
            return
            
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
            return

        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            try:
                # Check if product exists
                cur.execute("SELECT Name FROM Products WHERE ProductID = ?", (pid,))
                row = cur.fetchone()
                
                if not row:
                    messagebox.showwarning("Not Found", f"No product found with ID {pid}")
                    return
                    
                name = row[0]
                    
                # Delete product
                cur.execute("DELETE FROM Products WHERE ProductID = ?", (pid,))
                conn.commit()
                
                # Invalidate the product cache
                invalidate_cache('products')
                
                messagebox.showinfo("Success", f"Product '{name}' has been deleted")
                
                # Clear form and refresh
                self._clear_form()
                self._load_products()
                
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Database Error", f"Error deleting product: {str(e)}")

    # ------------------------------------------------------------------
    def _record_loss(self):
        """Record product loss or damage"""
        # Get form values
        pid_str = self.loss_id_entry.get().strip()
        qty_str = self.loss_qty_entry.get().strip()
        reason = self.reason_var.get()
        notes = self.notes_entry.get().strip()
        
        # Validate inputs
        if not pid_str:
            messagebox.showwarning("Missing Data", "Product ID is required")
            return
            
        try:
            pid = int(pid_str)
            qty = int(qty_str) if qty_str else 1
        except ValueError:
            messagebox.showwarning("Invalid Data", "Product ID and quantity must be integers")
            return
            
        if qty <= 0:
            messagebox.showwarning("Invalid Data", "Quantity must be greater than 0")
            return

        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            try:
                # Check if product exists and get stock
                cur.execute("SELECT Name, Stock FROM Products WHERE ProductID = ?", (pid,))
                row = cur.fetchone()
                
                if not row:
                    messagebox.showwarning("Not Found", f"No product found with ID {pid}")
                    return
                    
                name, stock = row
                
                # Validate stock
                if qty > stock:
                    messagebox.showwarning("Invalid Stock", f"Cannot record a loss of {qty} when only {stock} are in stock")
                    return
                
                # Insert loss record
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                cur.execute("""
                    INSERT INTO Losses (ProductID, Quantity, Reason, DateTime)
                    VALUES (?, ?, ?, ?)
                """, (pid, qty, f"{reason} - {notes}" if notes else reason, current_time))
                
                # Update stock
                cur.execute("UPDATE Products SET Stock = Stock - ? WHERE ProductID = ?", (qty, pid))
                
                conn.commit()
                
                # Invalidate the product cache
                invalidate_cache('products')
                
                messagebox.showinfo("Success", f"Recorded loss of {qty} '{name}' items. New stock: {stock - qty}")
                
                # Clear form and refresh
                self.loss_id_entry.delete(0, "end")
                self.loss_qty_entry.delete(0, "end")
                self.notes_entry.delete(0, "end")
                self._load_products()
                
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Database Error", f"Error recording loss: {str(e)}")

    # ------------------------------------------------------------------
    def _set_low_stock_threshold(self, value):
        try:
            threshold = int(value)
            if threshold < 1:
                threshold = 1
            self.low_stock_threshold = threshold
            
            # Refresh the display to apply the new threshold
            if self._current_category:
                self._refresh_table()
            elif self.search_var.get().strip():
                self._search_products()
                
            messagebox.showinfo("Threshold Updated", 
                               f"Low stock threshold set to {threshold} items", 
                               parent=self)
        except ValueError:
            messagebox.showwarning("Invalid Input", 
                                  "Please enter a valid number for the threshold", 
                                  parent=self)

    def _update_stock_metrics(self):
        """Update the stock status metrics"""
        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            # Count total products
            cur.execute("SELECT COUNT(*) FROM Products")
            total_products = cur.fetchone()[0]
            self.total_products_var.set(f"{tr(MSG_TOTAL_PRODUCTS)}: {total_products}")
            
            # Calculate inventory value
            cur.execute("SELECT SUM(SellingPrice * Stock) FROM Products")
            total_value = cur.fetchone()[0] or 0
            self.total_value_var.set(f"{tr(MSG_INVENTORY_VALUE)}: ${total_value:.2f}")
            
            # Count low stock items (stock <= 5)
            cur.execute("SELECT COUNT(*) FROM Products WHERE Stock > 0 AND Stock <= 5")
            low_stock = cur.fetchone()[0]
            self.low_stock_var.set(f"{tr(MSG_LOW_STOCK_ITEMS)}: {low_stock}")
            
        # Connection is automatically returned to the pool

    # ------------------------------------------------------------------
    def _build_product_section(self, parent):
        # Table on top
        table_box = ttk.Labelframe(parent, text="Products", padding=10, bootstyle=PRIMARY)
        table_box.pack(side=TOP, fill=BOTH, expand=True)

        vsb = ttk.Scrollbar(table_box, orient="vertical")
        hsb = ttk.Scrollbar(table_box, orient="horizontal")

        cols = ("ID", "Name", "Selling Price", "Buying Price", "Profit Margin", "Stock", "Status")
        
        # Create a custom style for better visibility
        style = ttk.Style()
        style.configure("Inventory.Treeview",
                      background="#3E3E3E",
                      foreground="white",
                      rowheight=30,
                      fieldbackground="#3E3E3E",
                      font=("Helvetica", 12))
        style.configure("Inventory.Treeview.Heading",
                       background="#2B2B2B",
                       foreground="white",
                       font=("Helvetica", 12, "bold"))
        style.map("Inventory.Treeview",
                 background=[("selected", "#4A6984")],
                 foreground=[("selected", "white")])
        
        self.tree = ttk.Treeview(table_box, columns=cols, show="headings",
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                 style="Inventory.Treeview")
        
        # Define column mappings for database fields
        self._col_mapping = {
            "ID": "ProductID",
            "Name": "Name",
            "Selling Price": "SellingPrice",
            "Buying Price": "BuyingPrice",
            "Stock": "Stock"
        }
        
        for col, width, anchor in [
            ("ID", 70, CENTER),
            ("Name", 250, W),
            ("Selling Price", 100, E),
            ("Buying Price", 100, E),
            ("Profit Margin", 100, E),
            ("Stock", 80, E),
            ("Status", 100, CENTER),
        ]:
            self.tree.heading(col, text=col, anchor=anchor, 
                             command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        vsb.pack(side=RIGHT, fill=Y)
        hsb.pack(side=BOTTOM, fill=X)

        # Update tag configurations for better visibility
        self.tree.tag_configure("evenrow", background="#4A4A4A", foreground="white")
        self.tree.tag_configure("oddrow",  background="#3A3A3A", foreground="white")
        
        # Add low stock indicator tags - brighter colors for better contrast
        self.tree.tag_configure("lowstock_even", background="#D07070", foreground="black")
        self.tree.tag_configure("lowstock_odd", background="#C06060", foreground="black")
        
        # Add out of stock indicator tags - brighter colors for better contrast
        self.tree.tag_configure("outofstock_even", background="#FF8080", foreground="black")
        self.tree.tag_configure("outofstock_odd", background="#FF6060", foreground="black")
        
        # Add setting for low stock threshold
        self.low_stock_threshold = 5

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling for the treeview"""
        try:
            self.tree.yview_scroll(-1 if event.delta > 0 else 1, "units")
        except:
            # Fallback for Linux
            if hasattr(event, 'num') and event.num == 4:
                self.tree.yview_scroll(-1, "units")
            elif hasattr(event, 'num') and event.num == 5:
                self.tree.yview_scroll(1, "units")

    # ------------------------------------------------------------------
    def _add_new_category(self):
        """Open dialog to add a new category to the database"""
        dialog = ttk.Toplevel(self)
        dialog.title("Add New Category")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Content frame
        content = ttk.Frame(dialog, padding=20)
        content.pack(fill=BOTH, expand=True)
        
        # Category name field
        ttk.Label(content, text="Category Name:", font=("Helvetica", 14)).grid(row=0, column=0, sticky=W, pady=10)
        category_entry = ttk.Entry(content, font=("Helvetica", 14), width=25)
        category_entry.grid(row=0, column=1, sticky=(W, E), pady=10)
        category_entry.focus_set()
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def save_category():
            category_name = category_entry.get().strip()
            if not category_name:
                messagebox.showerror("Error", "Category name cannot be empty")
                return
            
            # Check if category already exists
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT category FROM products WHERE category = ?", (category_name,))
            if cur.fetchone():
                return_connection(conn)
                messagebox.showerror("Error", f"Category '{category_name}' already exists")
                return
            
            # Insert a dummy product with the new category
            # This approach assumes categories are derived from products table
            try:
                cur.execute("""
                    INSERT INTO products (name, price, stock, category, barcode)
                    VALUES (?, ?, ?, ?, ?)
                """, (f"Sample {category_name}", 0.00, 0, category_name, f"CAT{random.randint(1000, 9999)}"))
                conn.commit()
                return_connection(conn)
                
                messagebox.showinfo("Success", f"Category '{category_name}' has been added.\nPlease add products to this category.")
                dialog.destroy()
                
                # Prompt to refresh
                self._refresh_categories()
                
            except Exception as e:
                return_connection(conn)
                messagebox.showerror("Database Error", f"Could not add category: {str(e)}")
        
        ttk.Button(
            button_frame, text="Save Category", style="Accent.TButton",
            command=save_category
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="Cancel",
            command=dialog.destroy
        ).pack(side=LEFT, padx=5)

    # ------------------------------------------------------------------
    def _refresh_categories(self):
        """Prompt user to refresh the page to see new category"""
        refresh = messagebox.askyesno(
            "Refresh Required", 
            "The category has been added to the database.\nDo you want to refresh the page to see it?"
        )
        if refresh:
            self._load_products()
            
            # Re-build the category sidebar
            # Find the category sidebar and recreate buttons
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Frame) and widget not in (self.topbar_frame, self.status_frame):
                    # This is likely our content frame
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame):
                            # This could be our page_content or content_container
                            for page_child in child.winfo_children():
                                if isinstance(page_child, ttk.Frame):
                                    # This could be our category_sidebar
                                    pass  # Would need to rebuild here, but complex to do

    def bind_mousewheel(self, widget):
        """Bind mousewheel events to the widget for scrolling"""
        widget.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        widget.bind("<Button-4>", self._on_mousewheel)    # Linux
        widget.bind("<Button-5>", self._on_mousewheel)    # Linux
        
        # Recursively bind to all children
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def _on_mousewheel(self, event):
        """Handle mousewheel events for scrolling"""
        # Different handling of event depending on platform
        if event.num == 4 or event.num == 5:  # Linux
            delta = 1 if event.num == 4 else -1
        else:  # Windows
            delta = event.delta // 120
        
        # Find the canvas being scrolled
        widget = event.widget
        while widget and not isinstance(widget, ttk.Canvas):
            if hasattr(widget, 'master'):
                widget = widget.master
            else:
                break
        
        if isinstance(widget, ttk.Canvas):
            widget.yview_scroll(-delta, "units")

    # ------------------------------------------------------------------
    def _load_products(self):
        """Load products from database with category and search filter in background thread"""
        # Clear existing items
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Mark task as active
        self._active_tasks["loading_products"] = True
        
        # Show loading indicator
        loading_item = self.product_tree.insert("", "end", values=("Loading products...", "", "", "", "", ""))
        
        # Reset lazy loading variables
        if not hasattr(self, '_all_product_rows'):
            self._all_product_rows = []
        self._all_product_rows = []
        self._current_page = 0
        self._rows_per_page = 100  # Number of items to load at once
        
        # Disable UI elements during loading to prevent multiple requests
        buttons = []
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        if child['state'] != 'disabled':  # Only track enabled buttons
                            buttons.append((child, child['state']))
                            child['state'] = 'disabled'
        
        # Define the background data loading function
        def fetch_products_data():
            try:
                # Get products from the data access layer
                return get_products(
                    category=self._current_category if self._current_category != "All Categories" else None,
                    search_term=self.search_entry.get() if hasattr(self, 'search_entry') else None,
                    show_out_of_stock=self.show_out_of_stock_var.get() if hasattr(self, 'show_out_of_stock_var') else True
                )
            except Exception as e:
                logger.error(f"Error loading products: {str(e)}")
                raise  # Re-raise to be handled by the error handler
        
        # Handle the loaded data
        def handle_loaded_data(products):
            # Check if widget still exists and task is still active
            if not self.winfo_exists() or not self._active_tasks["loading_products"]:
                return
                
            # Clear the temporary loading indicator
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)
            
            if not products:
                self.product_tree.insert("", "end", values=("No products found", "", "", "", "", ""))
                # Re-enable buttons
                for button, state in buttons:
                    try:
                        button['state'] = state
                    except:
                        pass  # Button might have been destroyed
                        
                # Mark task as complete
                self._active_tasks["loading_products"] = False
                return
            
            # Convert products to row format for lazy loading
            self._all_product_rows = [
                (product['ProductID'], 
                 product['Name'], 
                 product['SellingPrice'], 
                 product['BuyingPrice'], 
                 product['Stock'], 
                 product['Category'])
                for product in products
            ]
            
            # Set up scroll binding if not already done
            if not hasattr(self, '_scroll_binding_set'):
                self._setup_scroll_binding()
                self._scroll_binding_set = True
            
            # Load the first page
            self._load_next_page()
            
            # Update statistics
            self._update_statistics()
            
            # Re-enable buttons
            for button, state in buttons:
                try:
                    button['state'] = state
                except:
                    pass  # Button might have been destroyed
                    
            # Mark task as complete
            self._active_tasks["loading_products"] = False
        
        # Process error 
        def handle_error(error):
            # Check if widget still exists and task is still active
            if not self.winfo_exists() or not self._active_tasks["loading_products"]:
                return
                
            # Clear the temporary loading indicator
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)
            
            self.product_tree.insert(
                "", "end", 
                values=(f"Error loading products: {str(error)}", "", "", "", "", "")
            )
            logger.error(f"Error loading products: {str(error)}")
            
            # Re-enable buttons
            for button, state in buttons:
                try:
                    button['state'] = state
                except:
                    pass  # Button might have been destroyed
                    
            # Mark task as complete
            self._active_tasks["loading_products"] = False
        
        # Load data in background
        run_in_background(
            fetch_products_data,
            on_complete=handle_loaded_data,
            on_error=handle_error
        )

    # ------------------------------------------------------------------
    def _update_statistics(self):
        """Update inventory statistics"""
        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            # Count total products
            cur.execute("SELECT COUNT(*) FROM Products")
            total_products = cur.fetchone()[0]
            self.total_products_var.set(f"{tr(MSG_TOTAL_PRODUCTS)}: {total_products}")
            
            # Calculate inventory value
            cur.execute("SELECT SUM(SellingPrice * Stock) FROM Products")
            total_value = cur.fetchone()[0] or 0
            self.total_value_var.set(f"{tr(MSG_INVENTORY_VALUE)}: ${total_value:.2f}")
            
            # Count low stock items (stock <= 5)
            cur.execute("SELECT COUNT(*) FROM Products WHERE Stock > 0 AND Stock <= 5")
            low_stock = cur.fetchone()[0]
            self.low_stock_var.set(f"{tr(MSG_LOW_STOCK_ITEMS)}: {low_stock}")
            
        # Connection is automatically returned to the pool

    # ------------------------------------------------------------------
    def _filter_by_category(self, category):
        """Filter products by selected category"""
        self._current_category = category
        self._refresh_table()
        
        # Simply log the category change - removing the problematic code
        logger.info(f"Filtered inventory by category: {category}")
        
        # Note: We're removing the problematic code that tries to access topbar_frame and status_frame
        # which don't exist in this class

    # ------------------------------------------------------------------
    def _clear_form(self):
        """Clear all form fields"""
        self.name_entry.delete(0, END)
        self.selling_entry.delete(0, END)
        self.buying_entry.delete(0, END)
        self.stock_entry.delete(0, END)
        self.barcode_entry.delete(0, END)
        if self.category_combo['values']:
            self.category_combo.current(0)
        self.product_id_var.set("Product ID: New")
        self.profit_margin_var.set("Profit Margin: 0%")

    # ------------------------------------------------------------------
    def _load_product_for_edit(self, event):
        """Load selected product into the form for editing"""
        selection = self.product_tree.selection()
        if not selection:
            return
            
        # Get selected item
        item = self.product_tree.item(selection[0])
        values = item['values']
        
        if not values or len(values) < 6:
            return
            
        # Extract values
        pid, name, sell_price, buy_price, stock, category = values
        
        # Set edit form fields
        self.edit_product_id_var.set(f"Product ID: {pid}")
        self.edit_name_entry.delete(0, END)
        self.edit_name_entry.insert(0, name)
        
        self.edit_selling_entry.delete(0, END)
        self.edit_selling_entry.insert(0, sell_price)
        
        self.edit_buying_entry.delete(0, END)
        self.edit_buying_entry.insert(0, buy_price)
        
        self.edit_stock_entry.delete(0, END)
        self.edit_stock_entry.insert(0, stock)
        
        # Set category if in list
        if category in self.edit_category_combo['values']:
            self.edit_category_var.set(category)
            
        # Calculate profit margin
        try:
            sell = float(sell_price)
            buy = float(buy_price)
            if buy > 0:
                margin = ((sell - buy) / buy) * 100
                self.edit_profit_margin_var.set(f"Profit Margin: {margin:.1f}%")
            else:
                self.edit_profit_margin_var.set("Profit Margin: N/A")
        except ValueError:
            self.edit_profit_margin_var.set("Profit Margin: N/A")
            
        # Also set the delete product ID field
        self.manage_id_entry.delete(0, END)
        self.manage_id_entry.insert(0, pid)
        
        # Set loss ID field
        self.loss_id_entry.delete(0, END)
        self.loss_id_entry.insert(0, pid)
        
        # Find the form notebook and select the Edit Product tab
        for widget in self.winfo_children():
            if isinstance(widget, ttk.PanedWindow):
                for pane in widget.panes():
                    for child in pane.winfo_children():
                        if isinstance(child, ttk.Notebook):
                            # Found the notebook, select the Edit Product tab (index 1)
                            child.select(1)
                            break

    def _build_add_product_form(self, parent):
        """Build the form for adding new products"""
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=BOTH, expand=True)
        
        # Add header
        ttk.Label(form_frame, text=tr(MSG_ADD_PRODUCT), font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)
        
        # Product ID (auto-generated)
        self.product_id_var = StringVar(value="Product ID: New")
        ttk.Label(form_frame, textvariable=self.product_id_var, font=("Arial", 12, "bold")).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Product Name
        ttk.Label(form_frame, text=f"{tr(MSG_PRODUCT_NAME)}:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(form_frame, width=30, font=("Arial", 12))
        self.name_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        # Selling Price
        ttk.Label(form_frame, text=f"{tr(MSG_SELL_PRICE)}:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=5)
        self.selling_entry = ttk.Entry(form_frame, width=15, font=("Arial", 12))
        self.selling_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        
        # Buying Price
        ttk.Label(form_frame, text=f"{tr(MSG_BUY_PRICE)}:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", pady=5)
        self.buying_entry = ttk.Entry(form_frame, width=15, font=("Arial", 12))
        self.buying_entry.grid(row=4, column=1, sticky="w", pady=5, padx=5)
        
        # Profit Margin (calculated)
        self.profit_margin_var = StringVar(value="Profit Margin: 0%")
        ttk.Label(form_frame, textvariable=self.profit_margin_var, font=("Arial", 12)).grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        
        # Calculate profit margin when prices change
        def update_profit_margin(*args):
            try:
                selling = float(self.selling_entry.get()) if self.selling_entry.get() else 0
                buying = float(self.buying_entry.get()) if self.buying_entry.get() else 0
                if buying > 0:
                    margin = ((selling - buying) / buying) * 100
                    self.profit_margin_var.set(f"Profit Margin: {margin:.1f}%")
                else:
                    self.profit_margin_var.set("Profit Margin: N/A")
            except ValueError:
                self.profit_margin_var.set("Profit Margin: N/A")
                
        self.selling_entry.bind("<KeyRelease>", update_profit_margin)
        self.buying_entry.bind("<KeyRelease>", update_profit_margin)
        
        # Stock Quantity
        ttk.Label(form_frame, text=f"{tr(MSG_STOCK)}:", font=("Arial", 12)).grid(row=6, column=0, sticky="w", pady=5)
        self.stock_entry = ttk.Entry(form_frame, width=10, font=("Arial", 12))
        self.stock_entry.grid(row=6, column=1, sticky="w", pady=5, padx=5)
        
        # Category
        ttk.Label(form_frame, text=f"{tr(MSG_CATEGORY)}:", font=("Arial", 12)).grid(row=7, column=0, sticky="w", pady=5)
        
        # Get categories from database
        with ConnectionContext() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT Category FROM Products ORDER BY Category")
            categories = [row[0] for row in cur.fetchall()]
            
        self.category_var = StringVar()
        self.category_combo = ttk.Combobox(
            form_frame, textvariable=self.category_var, values=categories,
            state="readonly", width=20, font=("Arial", 12)
        )
        if categories:
            self.category_combo.current(0)
        self.category_combo.grid(row=7, column=1, sticky="w", pady=5, padx=5)
        
        # Barcode
        ttk.Label(form_frame, text="Barcode:", font=("Arial", 12)).grid(row=8, column=0, sticky="w", pady=5)
        self.barcode_entry = ttk.Entry(form_frame, width=20, font=("Arial", 12))
        self.barcode_entry.grid(row=8, column=1, sticky="w", pady=5, padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=15)
        
        add_product_btn = ttk.Button(
            button_frame, text=tr(MSG_SAVE), style="success.TButton",
            command=self._add_product, padding=10
        )
        add_product_btn.pack(side=LEFT, padx=5)
        
        clear_form_btn = ttk.Button(
            button_frame, text=tr(MSG_CLEAR), style="secondary.TButton",
            command=self._clear_form, padding=10
        )
        clear_form_btn.pack(side=LEFT, padx=5)
        
        # Configure grid columns
        form_frame.columnconfigure(1, weight=1)

    def _build_edit_product_form(self, parent):
        """Build the edit product form that's identical to the add form but will load product data"""
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=BOTH, expand=True)
        
        # Add header
        ttk.Label(form_frame, text=tr(MSG_EDIT_PRODUCT), font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)
        
        # Product ID (auto-generated)
        self.edit_product_id_var = StringVar(value="Product ID: New")
        ttk.Label(form_frame, textvariable=self.edit_product_id_var, font=("Arial", 12, "bold")).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Product Name
        ttk.Label(form_frame, text=f"{tr(MSG_PRODUCT_NAME)}:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.edit_name_entry = ttk.Entry(form_frame, width=30, font=("Arial", 12))
        self.edit_name_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        # Selling Price
        ttk.Label(form_frame, text=f"{tr(MSG_SELL_PRICE)}:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=5)
        self.edit_selling_entry = ttk.Entry(form_frame, width=15, font=("Arial", 12))
        self.edit_selling_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        
        # Buying Price
        ttk.Label(form_frame, text=f"{tr(MSG_BUY_PRICE)}:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", pady=5)
        self.edit_buying_entry = ttk.Entry(form_frame, width=15, font=("Arial", 12))
        self.edit_buying_entry.grid(row=4, column=1, sticky="w", pady=5, padx=5)
        
        # Profit Margin (calculated)
        self.edit_profit_margin_var = StringVar(value="Profit Margin: 0%")
        ttk.Label(form_frame, textvariable=self.edit_profit_margin_var, font=("Arial", 12)).grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        
        # Calculate profit margin when prices change
        def update_profit_margin(*args):
            try:
                selling = float(self.edit_selling_entry.get()) if self.edit_selling_entry.get() else 0
                buying = float(self.edit_buying_entry.get()) if self.edit_buying_entry.get() else 0
                if buying > 0:
                    margin = ((selling - buying) / buying) * 100
                    self.edit_profit_margin_var.set(f"Profit Margin: {margin:.1f}%")
                else:
                    self.edit_profit_margin_var.set("Profit Margin: N/A")
            except ValueError:
                self.edit_profit_margin_var.set("Profit Margin: N/A")
                
        self.edit_selling_entry.bind("<KeyRelease>", update_profit_margin)
        self.edit_buying_entry.bind("<KeyRelease>", update_profit_margin)
        
        # Stock Quantity
        ttk.Label(form_frame, text=f"{tr(MSG_STOCK)}:", font=("Arial", 12)).grid(row=6, column=0, sticky="w", pady=5)
        self.edit_stock_entry = ttk.Entry(form_frame, width=10, font=("Arial", 12))
        self.edit_stock_entry.grid(row=6, column=1, sticky="w", pady=5, padx=5)
        
        # Category
        ttk.Label(form_frame, text=f"{tr(MSG_CATEGORY)}:", font=("Arial", 12)).grid(row=7, column=0, sticky="w", pady=5)
        
        # Get categories from database
        with ConnectionContext() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT Category FROM Products ORDER BY Category")
            categories = [row[0] for row in cur.fetchall()]
            
        self.edit_category_var = StringVar()
        self.edit_category_combo = ttk.Combobox(
            form_frame, textvariable=self.edit_category_var, values=categories,
            state="readonly", width=20, font=("Arial", 12)
        )
        if categories:
            self.edit_category_combo.current(0)
        self.edit_category_combo.grid(row=7, column=1, sticky="w", pady=5, padx=5)
        
        # Barcode
        ttk.Label(form_frame, text="Barcode:", font=("Arial", 12)).grid(row=8, column=0, sticky="w", pady=5)
        self.edit_barcode_entry = ttk.Entry(form_frame, width=20, font=("Arial", 12))
        self.edit_barcode_entry.grid(row=8, column=1, sticky="w", pady=5, padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=15)
        
        edit_product_btn = ttk.Button(
            button_frame, text=tr(MSG_SAVE), style="success.TButton",
            command=self._update_product, padding=10
        )
        edit_product_btn.pack(side=LEFT, padx=5)
        
        clear_form_btn = ttk.Button(
            button_frame, text=tr(MSG_CLEAR), style="secondary.TButton",
            command=self._clear_edit_form, padding=10
        )
        clear_form_btn.pack(side=LEFT, padx=5)
        
        # Configure grid columns
        form_frame.columnconfigure(1, weight=1)

    def _update_product(self):
        """Update an existing product"""
        # Get form values
        product_id_text = self.edit_product_id_var.get()
        if product_id_text == "Product ID: New":
            messagebox.showwarning("Warning", "No product selected for editing", parent=self)
            return
            
        # Extract ID from text
        product_id = int(product_id_text.split(': ')[1])
        
        name = self.edit_name_entry.get().strip()
        sell_price_str = self.edit_selling_entry.get().strip()
        buy_price_str = self.edit_buying_entry.get().strip()
        stock_str = self.edit_stock_entry.get().strip()
        category = self.edit_category_var.get()
        barcode = self.edit_barcode_entry.get().strip()
        
        # Validate inputs
        if not name:
            messagebox.showwarning("Missing Data", "Product name is required", parent=self)
            return
            
        try:
            sell_price = float(sell_price_str) if sell_price_str else 0.0
            buy_price = float(buy_price_str) if buy_price_str else 0.0
            stock = int(stock_str) if stock_str else 0
        except ValueError:
            messagebox.showwarning("Invalid Data", "Price must be a number and stock must be an integer", parent=self)
            return
        
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Update existing product
            cur.execute("""
                UPDATE Products 
                SET Name = ?, SellingPrice = ?, BuyingPrice = ?, Stock = ?, Category = ?, Barcode = ?
                WHERE ProductID = ?
            """, (name, sell_price, buy_price, stock, category, barcode, product_id))
            
            conn.commit()
            
            # Import and invalidate the product cache
            invalidate_cache('products')
            
            messagebox.showinfo("Success", f"Product '{name}' has been updated", parent=self)
            
            # Clear form and refresh
            self._clear_edit_form()
            self._load_products()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"Error updating product: {str(e)}", parent=self)
        finally:
            return_connection(conn)

    def _clear_edit_form(self):
        """Clear all edit form fields"""
        self.edit_name_entry.delete(0, END)
        self.edit_selling_entry.delete(0, END)
        self.edit_buying_entry.delete(0, END)
        self.edit_stock_entry.delete(0, END)
        self.edit_barcode_entry.delete(0, END)
        if self.edit_category_combo['values']:
            self.edit_category_combo.current(0)
        self.edit_product_id_var.set("Product ID: New")
        self.edit_profit_margin_var.set("Profit Margin: 0%")

    def _build_delete_product_form(self, parent):
        """Build form for deleting products or adjusting stock"""
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(form_frame, text=tr(MSG_DELETE_PRODUCT), font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)
        
        # Product ID field 
        ttk.Label(form_frame, text="Product ID:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=5)
        self.manage_id_entry = ttk.Entry(form_frame, width=10, font=("Arial", 12))
        self.manage_id_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        # Delete button
        ttk.Button(
            form_frame, text=tr(MSG_DELETE_PRODUCT), style="danger.TButton",
            command=self._delete_product, padding=10
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        
        # Stock adjustment section
        ttk.Separator(form_frame, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=15)
        
        ttk.Label(form_frame, text="Adjust Stock", font=("Arial", 14, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", pady=10)
        
        # Quantity field
        ttk.Label(form_frame, text="Quantity:", font=("Arial", 12)).grid(row=5, column=0, sticky="w", pady=5)
        self.quantity_entry = ttk.Entry(form_frame, width=10, font=("Arial", 12))
        self.quantity_entry.insert(0, "1")
        self.quantity_entry.grid(row=5, column=1, sticky="w", pady=5, padx=5)
        
        # Adjustment buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky="w")
        
        ttk.Button(
            button_frame, text="Add Stock", style="success.TButton",
            command=lambda: self._update_stock(1), padding=10
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="Remove Stock", style="warning.TButton",
            command=lambda: self._update_stock(-1), padding=10
        ).pack(side=LEFT, padx=5)
        
        # Record Loss section
        ttk.Separator(form_frame, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=15)
        
        ttk.Label(form_frame, text="Record Loss/Damage", font=("Arial", 14, "bold")).grid(row=8, column=0, columnspan=2, sticky="w", pady=10)
        
        # Product ID for loss
        ttk.Label(form_frame, text="Product ID:", font=("Arial", 12)).grid(row=9, column=0, sticky="w", pady=5)
        self.loss_id_entry = ttk.Entry(form_frame, width=10, font=("Arial", 12))
        self.loss_id_entry.grid(row=9, column=1, sticky="w", pady=5, padx=5)
        
        # Quantity for loss
        ttk.Label(form_frame, text="Quantity:", font=("Arial", 12)).grid(row=10, column=0, sticky="w", pady=5)
        self.loss_qty_entry = ttk.Entry(form_frame, width=10, font=("Arial", 12))
        self.loss_qty_entry.insert(0, "1")
        self.loss_qty_entry.grid(row=10, column=1, sticky="w", pady=5, padx=5)
        
        # Reason dropdown
        ttk.Label(form_frame, text="Reason:", font=("Arial", 12)).grid(row=11, column=0, sticky="w", pady=5)
        self.reason_var = StringVar()
        reasons = ["Damaged", "Expired", "Lost", "Quality Issue", "Other"]
        reason_combo = ttk.Combobox(
            form_frame, textvariable=self.reason_var, values=reasons,
            state="readonly", width=15, font=("Arial", 12)
        )
        reason_combo.current(0)
        reason_combo.grid(row=11, column=1, sticky="w", pady=5, padx=5)
        
        # Notes
        ttk.Label(form_frame, text="Notes:", font=("Arial", 12)).grid(row=12, column=0, sticky="w", pady=5)
        self.notes_entry = ttk.Entry(form_frame, width=30, font=("Arial", 12))
        self.notes_entry.grid(row=12, column=1, sticky="ew", pady=5, padx=5)
        
        # Record button
        ttk.Button(
            form_frame, text="Record Loss", style="danger.TButton",
            command=self._record_loss, padding=10
        ).grid(row=13, column=0, columnspan=2, sticky="w", pady=10)
        
        # Configure grid
        form_frame.columnconfigure(1, weight=1)

# ----------------------------------------------------------------------
#  Stand‑alone test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import tkinter as tk
    root = ttk.Window(themename="darkly")
    InventoryPage(root, controller=None).pack(fill=BOTH, expand=True)
    root.mainloop()





