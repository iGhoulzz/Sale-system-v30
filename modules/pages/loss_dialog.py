"""
Loss Dialog for recording product losses
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, IntVar, Toplevel
from modules.enhanced_data_access import enhanced_data
from modules.i18n import _

class LossDialog:
    def __init__(self, parent, product_data):
        self.parent = parent
        self.product_data = product_data
        self.result = None
        
        # Create dialog
        self.dialog = Toplevel(parent)
        self.dialog.title(_("Record Product Loss"))
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Variables
        self.loss_quantity_var = IntVar(value=1)
        self.reason_var = StringVar(value="")
        
        self._create_ui()
        
        # Handle close event
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)
    
    def _create_ui(self):
        """Create the dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text=_("Record Product Loss"), 
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))
        
        # Product info
        info_frame = ttk.LabelFrame(main_frame, text=_("Product Information"), padding=10)
        info_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(info_frame, text=f"{_('Product')}: {self.product_data['Name']}", 
                 font=("Segoe UI", 10, "bold")).pack(anchor=W)
        ttk.Label(info_frame, text=f"{_('Current Stock')}: {self.product_data['Current_Stock']}", 
                 font=("Segoe UI", 10)).pack(anchor=W, pady=(5, 0))
        
        # Loss details
        details_frame = ttk.LabelFrame(main_frame, text=_("Loss Details"), padding=10)
        details_frame.pack(fill=X, pady=(0, 20))
        
        # Loss quantity
        ttk.Label(details_frame, text=_("Loss Quantity:"), 
                 font=("Segoe UI", 10, "bold")).pack(anchor=W)
        quantity_entry = ttk.Entry(details_frame, textvariable=self.loss_quantity_var, 
                                  font=("Segoe UI", 12))
        quantity_entry.pack(fill=X, pady=(5, 15))
        quantity_entry.focus()
        
        # Reason
        ttk.Label(details_frame, text=_("Reason for Loss:"), 
                 font=("Segoe UI", 10, "bold")).pack(anchor=W)
        
        # Reason dropdown
        reason_combo = ttk.Combobox(details_frame, textvariable=self.reason_var, 
                                   values=[
                                       _("Damaged"),
                                       _("Expired"),
                                       _("Theft"),
                                       _("Lost"),
                                       _("Quality Issues"),
                                       _("Other")
                                   ], font=("Segoe UI", 12))
        reason_combo.pack(fill=X, pady=(5, 0))
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=X, pady=(20, 0))
        
        record_btn = ttk.Button(buttons_frame, text=_("📉 Record Loss"), 
                               bootstyle="warning", command=self._record_loss)
        record_btn.pack(side=RIGHT, padx=(10, 0))
        
        cancel_btn = ttk.Button(buttons_frame, text=_("❌ Cancel"), 
                               bootstyle="secondary", command=self._cancel)
        cancel_btn.pack(side=RIGHT)
        
        # Bind Enter key to record
        self.dialog.bind('<Return>', lambda e: self._record_loss())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _record_loss(self):
        """Record the loss"""
        # Validate input
        try:
            loss_qty = self.loss_quantity_var.get()
            if loss_qty <= 0:
                messagebox.showerror(_("Error"), _("Loss quantity must be greater than 0"))
                return
        except:
            messagebox.showerror(_("Error"), _("Invalid loss quantity"))
            return
        
        current_stock = int(self.product_data['Current_Stock'])
        if loss_qty > current_stock:
            messagebox.showerror(_("Error"), 
                               f"{_('Loss quantity cannot exceed current stock')} ({current_stock})")
            return
        
        if not self.reason_var.get().strip():
            messagebox.showerror(_("Error"), _("Please specify the reason for loss"))
            return
        
        # Confirm the loss
        if not messagebox.askyesno(_("Confirm Loss"), 
                                  f"{_('Are you sure you want to record a loss of')} {loss_qty} "
                                  f"{_('units for')} '{self.product_data['Name']}'?\n\n"
                                  f"{_('Reason')}: {self.reason_var.get()}\n"
                                  f"{_('New stock will be')}: {current_stock - loss_qty}"):
            return
        
        try:
            # Update stock in database
            new_stock = current_stock - loss_qty
            enhanced_data.update_product_stock(self.product_data['ID'], new_stock)
            
            # Log the loss (if loss tracking is implemented)
            # enhanced_data.log_product_loss(product_id, loss_qty, reason)
            
            messagebox.showinfo(_("Success"), 
                               f"{_('Loss recorded successfully')}\n"
                               f"{_('New stock')}: {new_stock}")
            
            self.result = {
                'product_id': self.product_data['ID'],
                'loss_quantity': loss_qty,
                'reason': self.reason_var.get(),
                'new_stock': new_stock
            }
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror(_("Error"), f"{_('Error recording loss')}: {str(e)}")
    
    def _cancel(self):
        """Cancel and close dialog"""
        self.result = None
        self.dialog.destroy()
