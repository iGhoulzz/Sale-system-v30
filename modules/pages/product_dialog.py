"""
Product Dialog for adding/editing products
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, IntVar, DoubleVar, Toplevel
from modules.enhanced_data_access import enhanced_data
from modules.i18n import _

class ProductDialog:
    def __init__(self, parent, edit_mode=False, initial_data=None):
        self.parent = parent
        self.edit_mode = edit_mode
        self.initial_data = initial_data or {}
        self.result = None
        
        # Create dialog
        self.dialog = Toplevel(parent)
        self.dialog.title(_("Edit Product") if edit_mode else _("Add Product"))
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Variables
        self.name_var = StringVar(value=self.initial_data.get('Name', ''))
        self.category_var = StringVar(value=self.initial_data.get('Category', ''))
        self.stock_var = IntVar(value=int(self.initial_data.get('Stock', 0)))
        self.price_var = DoubleVar(value=float(self.initial_data.get('Price', 0)))
        self.buy_price_var = DoubleVar(value=float(self.initial_data.get('BuyPrice', 0)))
        self.barcode_var = StringVar(value=self.initial_data.get('Barcode', ''))
        self.description_var = StringVar(value=self.initial_data.get('Description', ''))
        
        self._create_ui()
        
        # Handle close event
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)
    
    def _create_ui(self):
        """Create the dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title = _("Edit Product") if self.edit_mode else _("Add New Product")
        ttk.Label(main_frame, text=title, font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))
        
        # Form fields
        # Product Name
        ttk.Label(main_frame, text=_("Product Name:"), font=("Segoe UI", 10, "bold")).pack(anchor=W)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, font=("Segoe UI", 12))
        name_entry.pack(fill=X, pady=(5, 15))
        name_entry.focus()
        
        # Category
        ttk.Label(main_frame, text=_("Category:"), font=("Segoe UI", 10, "bold")).pack(anchor=W)
        
        # Load categories for combobox
        try:
            categories = enhanced_data.get_categories()
            category_values = []
            if hasattr(categories, 'data'):
                category_values = [cat.get('Name', '') for cat in categories.data]
        except:
            category_values = []
        
        category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, 
                                     values=category_values, font=("Segoe UI", 12))
        category_combo.pack(fill=X, pady=(5, 15))
        
        # Stock
        ttk.Label(main_frame, text=_("Stock Quantity:"), font=("Segoe UI", 10, "bold")).pack(anchor=W)
        stock_entry = ttk.Entry(main_frame, textvariable=self.stock_var, font=("Segoe UI", 12))
        stock_entry.pack(fill=X, pady=(5, 15))
        
        # Selling Price
        ttk.Label(main_frame, text=_("Selling Price ($):"), font=("Segoe UI", 10, "bold")).pack(anchor=W)
        price_entry = ttk.Entry(main_frame, textvariable=self.price_var, font=("Segoe UI", 12))
        price_entry.pack(fill=X, pady=(5, 15))
        
        # Buying Price
        ttk.Label(main_frame, text=_("Buying Price ($):"), font=("Segoe UI", 10, "bold")).pack(anchor=W)
        buy_price_entry = ttk.Entry(main_frame, textvariable=self.buy_price_var, font=("Segoe UI", 12))
        buy_price_entry.pack(fill=X, pady=(5, 15))
        
        # Barcode
        ttk.Label(main_frame, text=_("Barcode:"), font=("Segoe UI", 10, "bold")).pack(anchor=W)
        barcode_entry = ttk.Entry(main_frame, textvariable=self.barcode_var, font=("Segoe UI", 12))
        barcode_entry.pack(fill=X, pady=(5, 15))
        
        # Description
        ttk.Label(main_frame, text=_("Description:"), font=("Segoe UI", 10, "bold")).pack(anchor=W)
        desc_entry = ttk.Entry(main_frame, textvariable=self.description_var, font=("Segoe UI", 12))
        desc_entry.pack(fill=X, pady=(5, 20))
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=X)
        
        save_btn = ttk.Button(buttons_frame, text=_("💾 Save"), bootstyle="success", command=self._save)
        save_btn.pack(side=RIGHT, padx=(10, 0))
        
        cancel_btn = ttk.Button(buttons_frame, text=_("❌ Cancel"), bootstyle="secondary", command=self._cancel)
        cancel_btn.pack(side=RIGHT)
        
        # Bind Enter key to save
        self.dialog.bind('<Return>', lambda e: self._save())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _save(self):
        """Save the product"""
        # Validate input
        if not self.name_var.get().strip():
            messagebox.showerror(_("Error"), _("Product name is required"))
            return
        
        if not self.category_var.get().strip():
            messagebox.showerror(_("Error"), _("Category is required"))
            return
        
        try:
            stock = self.stock_var.get()
            if stock < 0:
                messagebox.showerror(_("Error"), _("Stock cannot be negative"))
                return
        except:
            messagebox.showerror(_("Error"), _("Invalid stock quantity"))
            return
        
        try:
            price = self.price_var.get()
            if price < 0:
                messagebox.showerror(_("Error"), _("Price cannot be negative"))
                return
        except:
            messagebox.showerror(_("Error"), _("Invalid selling price"))
            return
        
        try:
            buy_price = self.buy_price_var.get()
            if buy_price < 0:
                messagebox.showerror(_("Error"), _("Buy price cannot be negative"))
                return
        except:
            messagebox.showerror(_("Error"), _("Invalid buying price"))
            return
        
        # Prepare data
        product_data = {
            'Name': self.name_var.get().strip(),
            'Category': self.category_var.get().strip(),
            'Stock': self.stock_var.get(),
            'Price': self.price_var.get(),
            'BuyPrice': self.buy_price_var.get(),
            'Barcode': self.barcode_var.get().strip(),
            'Description': self.description_var.get().strip()
        }
        
        try:
            if self.edit_mode:
                # Update existing product
                product_data['ID'] = self.initial_data.get('ID')
                enhanced_data.update_product(product_data)
                messagebox.showinfo(_("Success"), _("Product updated successfully"))
            else:
                # Add new product
                enhanced_data.add_product(product_data)
                messagebox.showinfo(_("Success"), _("Product added successfully"))
            
            self.result = product_data
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror(_("Error"), f"{_('Error saving product')}: {str(e)}")
    
    def _cancel(self):
        """Cancel and close dialog"""
        self.result = None
        self.dialog.destroy()
