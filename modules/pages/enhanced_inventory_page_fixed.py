"""
Fixed Enhanced Inventory Page with proper UI, categories, and CRUD operations

This is a comprehensive inventory management page with:
1. Proper category management with visual buttons
2. Full CRUD operations (Add, Edit, Delete products)
3. Good visibility with proper colors and fonts
4. Search and filtering functionality
5. Product management with losses tracking
6. Professional UI design
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import (
    BOTH, END, CENTER, W, E, X, Y, LEFT, RIGHT, TOP, BOTTOM,
    HORIZONTAL, VERTICAL, messagebox, StringVar, BooleanVar, 
    IntVar, DoubleVar, Toplevel
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
    Enhanced inventory management page with full functionality.
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
        
        # UI Variables
        self.search_var = StringVar()
        self.category_var = StringVar(value="All")
        self.stock_filter_var = StringVar(value="all")
        
        # Setup the UI
        self._setup_styles()
        self._create_ui()
        self._load_initial_data()
        
        # Register for language changes
        register_refresh_callback(self._retranslate)
    
    def _setup_styles(self):
        """Setup custom styles for better visibility"""
        style = ttk.Style()
        
        # Light background for main content
        style.configure("Light.TFrame", background="#FFFFFF")
        style.configure("Card.TFrame", background="#F8F9FA", relief="solid", borderwidth=1)
        
        # Dark text for visibility
        style.configure("Header.TLabel", 
                       font=("Segoe UI", 16, "bold"), 
                       foreground="#2C3E50", 
                       background="#FFFFFF")
        
        style.configure("Subheader.TLabel", 
                       font=("Segoe UI", 12, "bold"), 
                       foreground="#34495E", 
                       background="#FFFFFF")
        
        style.configure("Body.TLabel", 
                       font=("Segoe UI", 10), 
                       foreground="#2C3E50", 
                       background="#FFFFFF")
        
        # Category button styles
        style.configure("Category.TButton", 
                       font=("Segoe UI", 10, "bold"),
                       padding=(15, 8))
        
        # Active category button
        style.configure("ActiveCategory.TButton", 
                       font=("Segoe UI", 10, "bold"),
                       padding=(15, 8))
        
        # Statistics card styles
        style.configure("Stats.TLabel", 
                       font=("Segoe UI", 14, "bold"), 
                       foreground="#FFFFFF")
        
        # Product list styles
        style.configure("Product.Treeview", 
                       font=("Segoe UI", 10),
                       rowheight=25)
        
        style.configure("Product.Treeview.Heading", 
                       font=("Segoe UI", 10, "bold"))
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Main container with white background
        main_container = ttk.Frame(self, style="Light.TFrame")
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
        header_frame = ttk.Frame(parent, style="Light.TFrame")
        header_frame.pack(fill=X, pady=(0, 20))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text=_("📦 Inventory Management"),
            style="Header.TLabel"
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
        """Create statistics dashboard"""
        stats_frame = ttk.Frame(parent, style="Light.TFrame")
        stats_frame.pack(fill=X, pady=(0, 20))
        
        # Title
        ttk.Label(
            stats_frame,
            text=_("📊 Inventory Statistics"),
            style="Subheader.TLabel"
        ).pack(anchor=W, pady=(0, 10))
        
        # Stats cards container
        cards_frame = ttk.Frame(stats_frame, style="Light.TFrame")
        cards_frame.pack(fill=X)
        
        # Total Products Card
        self.total_products_card = ttk.Frame(cards_frame, style="Card.TFrame")
        self.total_products_card.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        
        ttk.Label(
            self.total_products_card,
            text="📦",
            font=("Segoe UI", 24),
            background="#F8F9FA"
        ).pack(pady=(10, 5))
        
        ttk.Label(
            self.total_products_card,
            text=_("Total Products"),
            font=("Segoe UI", 10, "bold"),
            foreground="#6C757D",
            background="#F8F9FA"
        ).pack()
        
        self.total_products_label = ttk.Label(
            self.total_products_card,
            text="0",
            font=("Segoe UI", 20, "bold"),
            foreground="#007BFF",
            background="#F8F9FA"
        )
        self.total_products_label.pack(pady=(5, 10))
        
        # Total Value Card
        self.total_value_card = ttk.Frame(cards_frame, style="Card.TFrame")
        self.total_value_card.pack(side=LEFT, fill=X, expand=True, padx=(5, 5))
        
        ttk.Label(
            self.total_value_card,
            text="💰",
            font=("Segoe UI", 24),
            background="#F8F9FA"
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
            products = enhanced_data.get_products()
            
            if hasattr(products, 'data'):
                total_products = len(products.data)
                total_value = sum(float(p.get('Price', 0)) * int(p.get('Stock', 0)) for p in products.data)
                low_stock = sum(1 for p in products.data if int(p.get('Stock', 0)) <= 5 and int(p.get('Stock', 0)) > 0)
                
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
            products = enhanced_data.get_products()
            
            if hasattr(products, 'data'):
                for product in products.data:
                    # Apply current filters
                    if not self._should_show_product(product):
                        continue
                    
                    values = (
                        product.get('ID', ''),
                        product.get('Name', ''),
                        product.get('Category', ''),
                        product.get('Stock', ''),
                        f"${float(product.get('Price', 0)):.2f}",
                        f"${float(product.get('BuyPrice', 0)):.2f}",
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
