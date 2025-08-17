"""
Category Dialog for adding/managing categories
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, Toplevel
from modules.enhanced_data_access import enhanced_data
from modules.i18n import _

class CategoryDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        
        # Create dialog
        self.dialog = Toplevel(parent)
        self.dialog.title(_("Add Category"))
        self.dialog.geometry("350x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Variables
        self.name_var = StringVar(value="")
        
        self._create_ui()
        
        # Handle close event
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)
    
    def _create_ui(self):
        """Create the dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text=_("Add New Category"), 
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))
        
        # Category name
        ttk.Label(main_frame, text=_("Category Name:"), 
                 font=("Segoe UI", 10, "bold")).pack(anchor=W)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, 
                              font=("Segoe UI", 12))
        name_entry.pack(fill=X, pady=(5, 20))
        name_entry.focus()
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=X)
        
        add_btn = ttk.Button(buttons_frame, text=_("➕ Add Category"), 
                            bootstyle="success", command=self._add_category)
        add_btn.pack(side=RIGHT, padx=(10, 0))
        
        cancel_btn = ttk.Button(buttons_frame, text=_("❌ Cancel"), 
                               bootstyle="secondary", command=self._cancel)
        cancel_btn.pack(side=RIGHT)
        
        # Bind Enter key to add
        self.dialog.bind('<Return>', lambda e: self._add_category())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _add_category(self):
        """Add the category"""
        # Validate input
        category_name = self.name_var.get().strip()
        if not category_name:
            messagebox.showerror(_("Error"), _("Category name is required"))
            return
        
        try:
            # Check if category already exists
            categories = enhanced_data.get_categories()
            if hasattr(categories, 'data'):
                existing_names = [cat.get('Name', '').lower() for cat in categories.data]
                if category_name.lower() in existing_names:
                    messagebox.showerror(_("Error"), _("Category already exists"))
                    return
            
            # Add category
            enhanced_data.add_category(category_name)
            messagebox.showinfo(_("Success"), _("Category added successfully"))
            
            self.result = category_name
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror(_("Error"), f"{_('Error adding category')}: {str(e)}")
    
    def _cancel(self):
        """Cancel and close dialog"""
        self.result = None
        self.dialog.destroy()
