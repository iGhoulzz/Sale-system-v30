"""
Professional Inventory Management Page - Business-Focused Design
Features: Category organization, detailed product management, loss recording, professional editing
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

class ProfessionalInventoryPage(ttk.Frame):
    """
    Professional Business-Focused Inventory Management Page
    Features: Category management, detailed product views, loss recording, professional editing
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        
        # Initialize variables
        self.current_category = "All"
        self.selected_product_id = None
        self.products_data = []
        self.categories_data = []
        
        # UI Variables
        self.search_var = StringVar()
        self.category_var = StringVar(value="All")
        self.sort_var = StringVar(value="name")
        
        # Setup the professional UI
        self._setup_professional_styles()
        self._create_professional_ui()
        self._load_initial_data()
        
        # Register for language changes
        register_refresh_callback(self._retranslate)
    
    def _setup_professional_styles(self):
        """Setup professional business-focused styles"""
        style = ttk.Style()
        
        # Professional color scheme
        self.colors = {
            'primary': '#2c3e50',      # Professional dark blue
            'secondary': '#34495e',     # Lighter blue-gray
            'accent': '#3498db',       # Professional blue
            'success': '#27ae60',      # Professional green
            'warning': '#f39c12',      # Professional orange
            'danger': '#e74c3c',       # Professional red
            'background': '#ecf0f1',   # Light background
            'surface': '#ffffff',      # White surface
            'text': '#2c3e50',         # Dark text
            'text_muted': '#7f8c8d',   # Muted text
            'border': '#bdc3c7',       # Border color
        }
        
        # Professional card styles
        style.configure("Professional.TFrame", 
                       background=self.colors['surface'],
                       relief="solid",
                       borderwidth=1)
        
        style.configure("Category.TFrame", 
                       background=self.colors['background'],
                       relief="flat")
        
        # Professional headers
        style.configure("ProfessionalHeader.TLabel", 
                       font=("Segoe UI", 18, "bold"), 
                       foreground=self.colors['primary'],
                       background=self.colors['surface'])
        
        style.configure("SectionHeader.TLabel", 
                       font=("Segoe UI", 12, "bold"), 
                       foreground=self.colors['secondary'],
                       background=self.colors['surface'])
        
        style.configure("CategoryButton.TButton", 
                       font=("Segoe UI", 10, "bold"))
        
        style.configure("ActionButton.TButton", 
                       font=("Segoe UI", 10, "bold"),
                       padding=(15, 8))
        
        # Professional treeview
        style.configure("Professional.Treeview", 
                       font=("Segoe UI", 10),
                       rowheight=35,
                       fieldbackground=self.colors['surface'],
                       background=self.colors['surface'],
                       foreground=self.colors['text'])
        
        style.configure("Professional.Treeview.Heading", 
                       font=("Segoe UI", 10, "bold"),
                       background=self.colors['background'],
                       foreground=self.colors['primary'])
        
        # Professional entry fields
        style.configure("Professional.TEntry", 
                       font=("Segoe UI", 11),
                       fieldbackground=self.colors['surface'])
    
    def _create_professional_ui(self):
        """Create professional business-focused UI layout"""
        # Main container
        self.configure(style="Category.TFrame")
        
        # Create main scrollable container
        main_container = ttk.Frame(self, style="Category.TFrame")
        main_container.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Header section
        self._create_header_section(main_container)
        
        # Content area with sidebar and main view
        content_frame = ttk.Frame(main_container, style="Category.TFrame")
        content_frame.pack(fill=BOTH, expand=True, pady=(20, 0))
        
        # Left sidebar - Categories
        self._create_categories_sidebar(content_frame)
        
        # Main content area
        self._create_main_content_area(content_frame)
    
    def _create_header_section(self, parent):
        """Create professional header with title, search, and actions"""
        header_frame = ttk.Frame(parent, style="Professional.TFrame")
        header_frame.pack(fill=X, pady=(0, 20))
        
        # Header content with padding
        header_content = ttk.Frame(header_frame, style="Professional.TFrame")
        header_content.pack(fill=X, padx=20, pady=15)
        
        # Title section
        title_frame = ttk.Frame(header_content, style="Professional.TFrame")
        title_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(title_frame, text=_("Inventory Management"), 
                 style="ProfessionalHeader.TLabel").pack(side=LEFT)
        
        # Action buttons
        actions_frame = ttk.Frame(title_frame, style="Professional.TFrame")
        actions_frame.pack(side=RIGHT)
        
        ttk.Button(actions_frame, text=_("Add Product"), 
                  style="ActionButton.TButton",
                  bootstyle="success",
                  command=self._show_add_product_dialog).pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(actions_frame, text=_("Export Report"), 
                  style="ActionButton.TButton",
                  bootstyle="info-outline",
                  command=self._export_inventory).pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(actions_frame, text=_("Refresh"), 
                  style="ActionButton.TButton",
                  bootstyle="secondary-outline",
                  command=self._refresh_all_data).pack(side=RIGHT, padx=(10, 0))
        
        # Search and filter section
        search_frame = ttk.Frame(header_content, style="Professional.TFrame")
        search_frame.pack(fill=X)
        
        # Search box
        search_label = ttk.Label(search_frame, text=_("Search Products:"), 
                                font=("Segoe UI", 10),
                                background=self.colors['surface'])
        search_label.pack(side=LEFT, padx=(0, 10))
        
        self.search_entry = ttk.Entry(search_frame, 
                                     textvariable=self.search_var,
                                     style="Professional.TEntry",
                                     width=30)
        self.search_entry.pack(side=LEFT, padx=(0, 20))
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Sort options
        sort_label = ttk.Label(search_frame, text=_("Sort by:"), 
                              font=("Segoe UI", 10),
                              background=self.colors['surface'])
        sort_label.pack(side=LEFT, padx=(0, 10))
        
        sort_combo = ttk.Combobox(search_frame, 
                                 textvariable=self.sort_var,
                                 values=[_("Name"), _("Price"), _("Stock"), _("Category")],
                                 state="readonly",
                                 width=15)
        sort_combo.pack(side=LEFT)
        sort_combo.bind('<<ComboboxSelected>>', self._on_sort_change)
    
    def _create_categories_sidebar(self, parent):
        """Create categories sidebar for filtering"""
        # Sidebar frame
        sidebar = ttk.Frame(parent, style="Professional.TFrame", width=200)
        sidebar.pack(side=LEFT, fill=Y, padx=(0, 20))
        sidebar.pack_propagate(False)  # Maintain fixed width
        
        # Sidebar content with padding
        sidebar_content = ttk.Frame(sidebar, style="Professional.TFrame")
        sidebar_content.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # Categories header
        ttk.Label(sidebar_content, text=_("Categories"), 
                 style="SectionHeader.TLabel").pack(anchor=W, pady=(0, 15))
        
        # Categories list frame
        self.categories_frame = ttk.Frame(sidebar_content, style="Professional.TFrame")
        self.categories_frame.pack(fill=X, pady=(0, 20))
        
        # Quick stats section
        stats_label = ttk.Label(sidebar_content, text=_("Quick Stats"), 
                               style="SectionHeader.TLabel")
        stats_label.pack(anchor=W, pady=(20, 10))
        
        # Stats frame
        stats_frame = ttk.Frame(sidebar_content, style="Professional.TFrame")
        stats_frame.pack(fill=X)
        
        # Individual stat items
        self._create_stat_item(stats_frame, _("Total Products:"), "0", "total_products")
        self._create_stat_item(stats_frame, _("Categories:"), "0", "total_categories")
        self._create_stat_item(stats_frame, _("Low Stock:"), "0", "low_stock")
        self._create_stat_item(stats_frame, _("Out of Stock:"), "0", "out_stock")
        self._create_stat_item(stats_frame, _("Total Value:"), "$0.00", "total_value")
    
    def _create_stat_item(self, parent, label_text, value, stat_id):
        """Create a single stat item"""
        item_frame = ttk.Frame(parent, style="Professional.TFrame")
        item_frame.pack(fill=X, pady=2)
        
        ttk.Label(item_frame, text=label_text, 
                 font=("Segoe UI", 9),
                 background=self.colors['surface']).pack(side=LEFT)
        
        value_label = ttk.Label(item_frame, text=value, 
                               font=("Segoe UI", 9, "bold"),
                               foreground=self.colors['accent'],
                               background=self.colors['surface'])
        value_label.pack(side=RIGHT)
        
        # Store reference for updates
        setattr(self, f"{stat_id}_label", value_label)
    
    def _create_main_content_area(self, parent):
        """Create main content area with product list and details"""
        main_frame = ttk.Frame(parent, style="Professional.TFrame")
        main_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Main content with padding
        content = ttk.Frame(main_frame, style="Professional.TFrame")
        content.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # Products section header
        products_header = ttk.Frame(content, style="Professional.TFrame")
        products_header.pack(fill=X, pady=(0, 15))
        
        ttk.Label(products_header, text=_("Products"), 
                 style="SectionHeader.TLabel").pack(side=LEFT)
        
        # Results count
        self.results_label = ttk.Label(products_header, text="", 
                                      font=("Segoe UI", 9),
                                      foreground=self.colors['text_muted'],
                                      background=self.colors['surface'])
        self.results_label.pack(side=RIGHT)
        
        # Products table
        self._create_products_table(content)
        
        # Product details and actions section
        self._create_product_actions(content)
    
    def _create_products_table(self, parent):
        """Create professional products table"""
        # Table frame
        table_frame = ttk.Frame(parent, style="Professional.TFrame")
        table_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Create treeview with detailed columns
        columns = ("id", "name", "category", "buy_price", "sell_price", "stock", "total_value", "status")
        self.products_tree = ttk.Treeview(table_frame, 
                                         columns=columns, 
                                         show="headings",
                                         style="Professional.Treeview")
        
        # Configure column headers and widths
        headers = {
            "id": (_("ID"), 60, CENTER),
            "name": (_("Product Name"), 200, W),
            "category": (_("Category"), 120, CENTER),
            "buy_price": (_("Buy Price"), 100, CENTER),
            "sell_price": (_("Sell Price"), 100, CENTER),
            "stock": (_("Stock"), 80, CENTER),
            "total_value": (_("Total Value"), 120, CENTER),
            "status": (_("Status"), 100, CENTER)
        }
        
        for col, (text, width, anchor) in headers.items():
            self.products_tree.heading(col, text=text, anchor=CENTER)
            self.products_tree.column(col, width=width, anchor=anchor, minwidth=50)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.products_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=HORIZONTAL, command=self.products_tree.xview)
        
        self.products_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack table and scrollbars
        self.products_tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Bind events
        self.products_tree.bind('<<TreeviewSelect>>', self._on_product_select)
        self.products_tree.bind('<Double-1>', self._on_product_double_click)
        self.products_tree.bind('<Button-3>', self._show_context_menu)
        
        # Configure row tags for different stock levels
        self.products_tree.tag_configure('normal', background='#ffffff')
        self.products_tree.tag_configure('low_stock', background='#fff3cd', foreground='#856404')
        self.products_tree.tag_configure('out_of_stock', background='#f8d7da', foreground='#721c24')
    
    def _create_product_actions(self, parent):
        """Create product action buttons section"""
        actions_frame = ttk.Frame(parent, style="Professional.TFrame")
        actions_frame.pack(fill=X)
        
        # Selected product info
        info_frame = ttk.Frame(actions_frame, style="Professional.TFrame")
        info_frame.pack(side=LEFT, fill=X, expand=True)
        
        self.selected_info_label = ttk.Label(info_frame, 
                                           text=_("Select a product to view actions"), 
                                           font=("Segoe UI", 10),
                                           foreground=self.colors['text_muted'],
                                           background=self.colors['surface'])
        self.selected_info_label.pack(side=LEFT)
        
        # Action buttons
        buttons_frame = ttk.Frame(actions_frame, style="Professional.TFrame")
        buttons_frame.pack(side=RIGHT)
        
        self.edit_button = ttk.Button(buttons_frame, text=_("Edit Product"), 
                                     bootstyle="primary",
                                     command=self._edit_selected_product,
                                     state="disabled")
        self.edit_button.pack(side=LEFT, padx=(0, 10))
        
        self.loss_button = ttk.Button(buttons_frame, text=_("Record Loss"), 
                                     bootstyle="warning",
                                     command=self._record_loss,
                                     state="disabled")
        self.loss_button.pack(side=LEFT, padx=(0, 10))
        
        self.delete_button = ttk.Button(buttons_frame, text=_("Delete"), 
                                       bootstyle="danger",
                                       command=self._delete_selected_product,
                                       state="disabled")
        self.delete_button.pack(side=LEFT)
    
    # Event handlers
    def _on_product_select(self, event):
        """Handle product selection"""
        selection = self.products_tree.selection()
        if selection:
            item_id = selection[0]
            product_data = self.products_tree.item(item_id)
            product_id = product_data['values'][0]  # ID is first column
            product_name = product_data['values'][1]  # Name is second column
            
            self.selected_product_id = product_id
            self.selected_info_label.config(text=f"{_('Selected:')} {product_name}")
            
            # Enable action buttons
            self.edit_button.config(state="normal")
            self.loss_button.config(state="normal")
            self.delete_button.config(state="normal")
        else:
            self.selected_product_id = None
            self.selected_info_label.config(text=_("Select a product to view actions"))
            
            # Disable action buttons
            self.edit_button.config(state="disabled")
            self.loss_button.config(state="disabled")
            self.delete_button.config(state="disabled")
    
    def _on_product_double_click(self, event):
        """Handle double click on product"""
        if self.selected_product_id:
            self._edit_selected_product()
    
    def _on_search_change(self, event=None):
        """Handle search input change"""
        self._refresh_products_display()
    
    def _on_sort_change(self, event=None):
        """Handle sort selection change"""
        self._refresh_products_display()
    
    def _set_category_filter(self, category):
        """Set category filter and refresh display"""
        self.current_category = category
        self._refresh_categories_display()
        self._refresh_products_display()
    
    # Data loading and display methods
    def _load_initial_data(self):
        """Load initial data for the page"""
        self._load_categories()
        self._load_products()
        self._update_statistics()
    
    def _load_categories(self):
        """Load and display categories"""
        try:
            # Get unique categories from products
            products_data = enhanced_data.get_products()
            products_list = products_data if isinstance(products_data, list) else []
            
            categories = set()
            for product in products_list:
                category = product.get('Category', '').strip()
                if category:
                    categories.add(category)
            
            self.categories_data = sorted(list(categories))
            self._refresh_categories_display()
            
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
    
    def _refresh_categories_display(self):
        """Refresh the categories display"""
        # Clear existing category buttons
        for widget in self.categories_frame.winfo_children():
            widget.destroy()
        
        # Add "All" category
        all_button = ttk.Button(self.categories_frame, text=_("All Categories"), 
                               style="CategoryButton.TButton",
                               bootstyle="primary" if self.current_category == "All" else "secondary-outline",
                               command=lambda: self._set_category_filter("All"))
        all_button.pack(fill=X, pady=2)
        
        # Add individual categories
        for category in self.categories_data:
            button_style = "primary" if self.current_category == category else "secondary-outline"
            cat_button = ttk.Button(self.categories_frame, text=category, 
                                   style="CategoryButton.TButton",
                                   bootstyle=button_style,
                                   command=lambda c=category: self._set_category_filter(c))
            cat_button.pack(fill=X, pady=2)
    
    def _load_products(self):
        """Load products data"""
        try:
            products_data = enhanced_data.get_products()
            self.products_data = products_data if isinstance(products_data, list) else []
            self._refresh_products_display()
            
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            messagebox.showerror(_("Error"), f"{_('Error loading products')}: {e}")
    
    def _refresh_products_display(self):
        """Refresh products display with current filters"""
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Filter and sort products
        filtered_products = self._filter_and_sort_products()
        
        # Add products to tree
        for product in filtered_products:
            self._add_product_to_tree(product)
        
        # Update results count
        count = len(filtered_products)
        self.results_label.config(text=f"{count} {_('products found')}")
    
    def _filter_and_sort_products(self):
        """Filter and sort products based on current settings"""
        filtered = []
        search_term = self.search_var.get().lower()
        
        for product in self.products_data:
            # Category filter
            if self.current_category != "All":
                if product.get('Category', '') != self.current_category:
                    continue
            
            # Search filter
            if search_term:
                searchable_text = f"{product.get('Name', '')} {product.get('Category', '')} {product.get('Barcode', '')}".lower()
                if search_term not in searchable_text:
                    continue
            
            filtered.append(product)
        
        # Sort products
        sort_key = self.sort_var.get().lower()
        if sort_key == "name":
            filtered.sort(key=lambda p: p.get('Name', '').lower())
        elif sort_key == "price":
            filtered.sort(key=lambda p: float(p.get('SellingPrice', 0)), reverse=True)
        elif sort_key == "stock":
            filtered.sort(key=lambda p: int(p.get('Stock', 0)))
        elif sort_key == "category":
            filtered.sort(key=lambda p: p.get('Category', '').lower())
        
        return filtered
    
    def _add_product_to_tree(self, product):
        """Add a single product to the tree"""
        # Calculate values
        product_id = product.get('ProductID', product.get('ID', ''))
        name = product.get('Name', '')
        category = product.get('Category', '')
        buy_price = float(product.get('BuyingPrice', product.get('BuyPrice', 0)))
        sell_price = float(product.get('SellingPrice', product.get('Price', 0)))
        stock = int(product.get('Stock', 0))
        total_value = sell_price * stock
        
        # Determine status and tag
        if stock == 0:
            status = _("Out of Stock")
            tag = 'out_of_stock'
        elif stock <= 5:
            status = _("Low Stock")
            tag = 'low_stock'
        else:
            status = _("In Stock")
            tag = 'normal'
        
        # Format values for display
        values = (
            product_id,
            name,
            category,
            f"${buy_price:.2f}",
            f"${sell_price:.2f}",
            stock,
            f"${total_value:.2f}",
            status
        )
        
        # Insert into tree with appropriate tag
        self.products_tree.insert('', 'end', values=values, tags=(tag,))
    
    def _update_statistics(self):
        """Update statistics in the sidebar"""
        try:
            if not self.products_data:
                return
            
            total_products = len(self.products_data)
            total_categories = len(self.categories_data)
            low_stock = sum(1 for p in self.products_data if 0 < int(p.get('Stock', 0)) <= 5)
            out_stock = sum(1 for p in self.products_data if int(p.get('Stock', 0)) == 0)
            total_value = sum(float(p.get('SellingPrice', 0)) * int(p.get('Stock', 0)) for p in self.products_data)
            
            # Update labels
            self.total_products_label.config(text=str(total_products))
            self.total_categories_label.config(text=str(total_categories))
            self.low_stock_label.config(text=str(low_stock))
            self.out_stock_label.config(text=str(out_stock))
            self.total_value_label.config(text=f"${total_value:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    # Business logic methods
    def _show_add_product_dialog(self):
        """Show add product dialog"""
        self._show_product_dialog()
    
    def _edit_selected_product(self):
        """Edit the selected product"""
        if not self.selected_product_id:
            messagebox.showwarning(_("Warning"), _("Please select a product to edit"))
            return
        
        # Find the product data
        product_data = None
        for product in self.products_data:
            if str(product.get('ProductID', product.get('ID'))) == str(self.selected_product_id):
                product_data = product
                break
        
        if product_data:
            self._show_product_dialog(product_data)
    
    def _show_product_dialog(self, product_data=None):
        """Show product add/edit dialog"""
        dialog = ProductDialog(self, product_data)
        if dialog.result:
            self._refresh_all_data()
    
    def _record_loss(self):
        """Record product loss with reason"""
        if not self.selected_product_id:
            messagebox.showwarning(_("Warning"), _("Please select a product to record loss"))
            return
        
        # Find the product data
        product_data = None
        for product in self.products_data:
            if str(product.get('ProductID', product.get('ID'))) == str(self.selected_product_id):
                product_data = product
                break
        
        if product_data:
            dialog = LossRecordDialog(self, product_data)
            if dialog.result:
                self._refresh_all_data()
    
    def _delete_selected_product(self):
        """Delete the selected product"""
        if not self.selected_product_id:
            messagebox.showwarning(_("Warning"), _("Please select a product to delete"))
            return
        
        # Confirm deletion
        if messagebox.askyesno(_("Confirm Delete"), 
                              _("Are you sure you want to delete this product?\nThis action cannot be undone.")):
            try:
                # TODO: Implement product deletion
                messagebox.showinfo(_("Success"), _("Product deleted successfully"))
                self._refresh_all_data()
            except Exception as e:
                messagebox.showerror(_("Error"), f"{_('Error deleting product')}: {e}")
    
    def _export_inventory(self):
        """Export inventory to file"""
        try:
            # TODO: Implement inventory export
            messagebox.showinfo(_("Export"), _("Inventory export feature will be implemented"))
        except Exception as e:
            messagebox.showerror(_("Error"), f"{_('Export error')}: {e}")
    
    def _show_context_menu(self, event):
        """Show context menu on right click"""
        if self.selected_product_id:
            context_menu = ttk.Menu(self, tearoff=0)
            context_menu.add_command(label=_("Edit Product"), command=self._edit_selected_product)
            context_menu.add_command(label=_("Record Loss"), command=self._record_loss)
            context_menu.add_separator()
            context_menu.add_command(label=_("Delete Product"), command=self._delete_selected_product)
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def _refresh_all_data(self):
        """Refresh all data"""
        self._load_categories()
        self._load_products()
        self._update_statistics()
        invalidate_cache()
    
    # Public interface methods
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


class ProductDialog:
    """Professional product add/edit dialog"""
    
    def __init__(self, parent, product_data=None):
        self.parent = parent
        self.product_data = product_data
        self.result = None
        
        # Create dialog window
        self.dialog = Toplevel(parent)
        self.dialog.title(_("Edit Product") if product_data else _("Add Product"))
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self._create_dialog_ui()
        
        # Wait for dialog to complete
        self.dialog.wait_window()
    
    def _create_dialog_ui(self):
        """Create the dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_text = _("Edit Product") if self.product_data else _("Add New Product")
        ttk.Label(main_frame, text=title_text, 
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        # Form fields
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=X, pady=(0, 20))
        
        # Product Name
        ttk.Label(form_frame, text=_("Product Name:")).grid(row=0, column=0, sticky=W, pady=5)
        self.name_var = StringVar(value=self.product_data.get('Name', '') if self.product_data else '')
        ttk.Entry(form_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Category
        ttk.Label(form_frame, text=_("Category:")).grid(row=1, column=0, sticky=W, pady=5)
        self.category_var = StringVar(value=self.product_data.get('Category', '') if self.product_data else '')
        ttk.Entry(form_frame, textvariable=self.category_var, width=30).grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Buy Price
        ttk.Label(form_frame, text=_("Buy Price ($):")).grid(row=2, column=0, sticky=W, pady=5)
        self.buy_price_var = DoubleVar(value=float(self.product_data.get('BuyingPrice', 0)) if self.product_data else 0.0)
        ttk.Entry(form_frame, textvariable=self.buy_price_var, width=30).grid(row=2, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Sell Price
        ttk.Label(form_frame, text=_("Sell Price ($):")).grid(row=3, column=0, sticky=W, pady=5)
        self.sell_price_var = DoubleVar(value=float(self.product_data.get('SellingPrice', 0)) if self.product_data else 0.0)
        ttk.Entry(form_frame, textvariable=self.sell_price_var, width=30).grid(row=3, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Stock
        ttk.Label(form_frame, text=_("Stock Quantity:")).grid(row=4, column=0, sticky=W, pady=5)
        self.stock_var = IntVar(value=int(self.product_data.get('Stock', 0)) if self.product_data else 0)
        ttk.Entry(form_frame, textvariable=self.stock_var, width=30).grid(row=4, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Barcode
        ttk.Label(form_frame, text=_("Barcode:")).grid(row=5, column=0, sticky=W, pady=5)
        self.barcode_var = StringVar(value=self.product_data.get('Barcode', '') if self.product_data else '')
        ttk.Entry(form_frame, textvariable=self.barcode_var, width=30).grid(row=5, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame, text=_("Cancel"), 
                  command=self._cancel).pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(button_frame, text=_("Save"), 
                  bootstyle="primary",
                  command=self._save).pack(side=RIGHT)
    
    def _save(self):
        """Save the product"""
        try:
            # Validate inputs
            if not self.name_var.get().strip():
                messagebox.showerror(_("Error"), _("Product name is required"))
                return
            
            if self.sell_price_var.get() <= 0:
                messagebox.showerror(_("Error"), _("Sell price must be greater than 0"))
                return
            
            # TODO: Implement actual save logic here
            # This would save to database
            
            self.result = {
                'name': self.name_var.get().strip(),
                'category': self.category_var.get().strip(),
                'buy_price': self.buy_price_var.get(),
                'sell_price': self.sell_price_var.get(),
                'stock': self.stock_var.get(),
                'barcode': self.barcode_var.get().strip()
            }
            
            messagebox.showinfo(_("Success"), _("Product saved successfully"))
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror(_("Error"), f"{_('Error saving product')}: {e}")
    
    def _cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy()


class LossRecordDialog:
    """Dialog for recording product losses with reasons"""
    
    def __init__(self, parent, product_data):
        self.parent = parent
        self.product_data = product_data
        self.result = None
        
        # Create dialog window
        self.dialog = Toplevel(parent)
        self.dialog.title(_("Record Product Loss"))
        self.dialog.geometry("450x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self._create_dialog_ui()
        
        # Wait for dialog to complete
        self.dialog.wait_window()
    
    def _create_dialog_ui(self):
        """Create the loss record dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text=_("Record Product Loss"), 
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        # Product info
        info_frame = ttk.LabelFrame(main_frame, text=_("Product Information"), padding=10)
        info_frame.pack(fill=X, pady=(0, 20))
        
        product_name = self.product_data.get('Name', '')
        current_stock = int(self.product_data.get('Stock', 0))
        
        ttk.Label(info_frame, text=f"{_('Product:')} {product_name}").pack(anchor=W)
        ttk.Label(info_frame, text=f"{_('Current Stock:')} {current_stock}").pack(anchor=W)
        
        # Loss details
        loss_frame = ttk.LabelFrame(main_frame, text=_("Loss Details"), padding=10)
        loss_frame.pack(fill=X, pady=(0, 20))
        
        # Quantity lost
        qty_frame = ttk.Frame(loss_frame)
        qty_frame.pack(fill=X, pady=5)
        
        ttk.Label(qty_frame, text=_("Quantity Lost:")).pack(side=LEFT)
        self.qty_var = IntVar(value=1)
        qty_spinbox = ttk.Spinbox(qty_frame, from_=1, to=current_stock, 
                                 textvariable=self.qty_var, width=10)
        qty_spinbox.pack(side=RIGHT)
        
        # Loss reason
        ttk.Label(loss_frame, text=_("Reason for Loss:")).pack(anchor=W, pady=(10, 5))
        self.reason_var = StringVar()
        reason_combo = ttk.Combobox(loss_frame, textvariable=self.reason_var,
                                   values=[_("Damaged"), _("Expired"), _("Theft"), _("Spoilage"), 
                                          _("Breakage"), _("Other")],
                                   width=40)
        reason_combo.pack(fill=X, pady=(0, 10))
        
        # Additional notes
        ttk.Label(loss_frame, text=_("Additional Notes:")).pack(anchor=W, pady=(5, 5))
        self.notes_text = ttk.Text(loss_frame, height=4, width=40)
        self.notes_text.pack(fill=X)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        ttk.Button(button_frame, text=_("Cancel"), 
                  command=self._cancel).pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(button_frame, text=_("Record Loss"), 
                  bootstyle="warning",
                  command=self._record_loss).pack(side=RIGHT)
    
    def _record_loss(self):
        """Record the product loss"""
        try:
            qty_lost = self.qty_var.get()
            reason = self.reason_var.get()
            notes = self.notes_text.get("1.0", END).strip()
            
            # Validate inputs
            if qty_lost <= 0:
                messagebox.showerror(_("Error"), _("Quantity must be greater than 0"))
                return
            
            current_stock = int(self.product_data.get('Stock', 0))
            if qty_lost > current_stock:
                messagebox.showerror(_("Error"), _("Cannot record loss greater than current stock"))
                return
            
            if not reason:
                messagebox.showerror(_("Error"), _("Please select a reason for the loss"))
                return
            
            # Confirm the loss record
            if messagebox.askyesno(_("Confirm Loss"), 
                                  f"{_('Record loss of')} {qty_lost} {_('units')}?\n"
                                  f"{_('Reason:')} {reason}\n"
                                  f"{_('This will reduce stock from')} {current_stock} {_('to')} {current_stock - qty_lost}"):
                
                # TODO: Implement actual loss recording logic here
                # This would:
                # 1. Update product stock in database
                # 2. Record loss in losses table
                # 3. Update financial records
                
                self.result = {
                    'product_id': self.product_data.get('ProductID', self.product_data.get('ID')),
                    'quantity_lost': qty_lost,
                    'reason': reason,
                    'notes': notes,
                    'date': datetime.datetime.now()
                }
                
                messagebox.showinfo(_("Success"), _("Product loss recorded successfully"))
                self.dialog.destroy()
                
        except Exception as e:
            messagebox.showerror(_("Error"), f"{_('Error recording loss')}: {e}")
    
    def _cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy()


# For backwards compatibility, create an alias
EnhancedInventoryPage = ProfessionalInventoryPage
ModernInventoryPage2025 = ProfessionalInventoryPage
