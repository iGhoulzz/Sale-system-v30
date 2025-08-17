"""
UI Components for performance-optimized interfaces.
This module provides reusable UI components that help prevent UI freezing
and provide better user feedback during long operations.

Updated: July 17, 2025
- Enhanced error handling
- Better responsiveness
- Modern design elements
- Improved accessibility
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import logging
from typing import Optional, Callable, Dict, Any, List

# Configure logger
logger = logging.getLogger(__name__)

class ProgressDialog:
    """Non-blocking progress dialog with status updates and modern design"""
    
    def __init__(self, parent, title="Processing...", cancelable=False, theme_style="modern"):
        self.parent = parent
        self.cancelled = False
        self.theme_style = theme_style
        
        try:
            # Create dialog with error handling
            self.dialog = tk.Toplevel(parent)
            self.dialog.title(title)
            self.dialog.geometry("400x150")
            self.dialog.transient(parent)
            self.dialog.grab_set()
            
            # Prevent dialog from being closed prematurely
            self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
            
            # Apply modern styling
            self._setup_modern_styling()
            
            # Center the dialog
            self._center_dialog()
            
            # Create components
            self._create_components(cancelable)
            
        except Exception as e:
            logger.error(f"Error creating progress dialog: {e}")
            raise
    
    def _setup_modern_styling(self):
        """Apply modern styling to the dialog"""
        if self.theme_style == "modern":
            self.dialog.configure(bg="#f0f0f0")
    
    def _center_dialog(self):
        """Center the dialog relative to parent"""
        try:
            # Update to get accurate geometry
            self.dialog.update_idletasks()
            
            # Get parent geometry
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            # Calculate center position
            dialog_width = 400
            dialog_height = 150
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2
            
            self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        except Exception as e:
            logger.warning(f"Could not center dialog: {e}")
            # Fallback to simple positioning
            self.dialog.geometry("+50+50")
    
    def _create_components(self, cancelable):
        """Create dialog components"""
        # Main frame
        main_frame = tk.Frame(self.dialog, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Progress bar with modern styling
        self.progress = ttk.Progressbar(
            main_frame, 
            mode='indeterminate',
            length=350,
            style="Modern.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=(0, 15))
        self.progress.start()
        
        # Status label with modern font
        self.status_label = tk.Label(
            main_frame, 
            text="Please wait...",
            font=('Segoe UI', 10),
            bg="#f0f0f0",
            fg="#333333"
        )
        self.status_label.pack(pady=(0, 10))
        
        # Cancel button (optional) with modern styling
        if cancelable:
            self.cancel_button = tk.Button(
                main_frame,
                text="Cancel",
                command=self._cancel,
                font=('Segoe UI', 9),
                bg="#e74c3c",
                fg="white",
                relief=tk.FLAT,
                padx=20,
                pady=5
            )
            self.cancel_button.pack()
    
    def _on_close(self):
        """Handle dialog close event"""
        self._cancel()
    
    def _cancel(self):
        """Cancel the operation"""
        self.cancelled = True
        self.close()
    
    def update_status(self, message: str):
        """Update the status message"""
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.config(text=message)
                self.dialog.update_idletasks()
        except Exception as e:
            logger.warning(f"Could not update status: {e}")
    
    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        try:
            if hasattr(self, 'progress') and self.progress:
                self.progress.config(mode='determinate', value=value)
                self.dialog.update_idletasks()
        except Exception as e:
            logger.warning(f"Could not set progress: {e}")
    
    def close(self):
        """Close the dialog"""
        try:
            if hasattr(self, 'progress') and self.progress:
                self.progress.stop()
            if hasattr(self, 'dialog') and self.dialog:
                self.dialog.destroy()
        except Exception as e:
            logger.warning(f"Error closing dialog: {e}")
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        return self.cancelled

class PaginatedListView:
    """Enhanced paginated list view component with modern features"""
    
    def __init__(self, parent, columns, data_loader=None, page_size=50, 
                 headers=None, widths=None, on_page_change=None, on_select=None, 
                 on_double_click=None, height=None, style="Modern"):
        self.parent = parent
        self.columns = columns
        self.data_loader = data_loader or on_page_change  # Support both parameter names
        self.page_size = page_size
        self.current_page = 1
        self.total_pages = 1
        self.total_items = 0
        self.loading = False
        self.search_var = None
        
        # Enhanced features
        self.headers = headers or {}
        self.widths = widths or {}
        self.height = height or 15
        self.style = style
        self.on_select_callback = on_select
        self.on_double_click_callback = on_double_click
        
        # Data storage
        self.current_data = []
        self.selected_item = None
        
        # Performance tracking
        self.last_load_time = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the modern paginated UI"""
        try:
            # Main frame with modern styling
            self.main_frame = tk.Frame(self.parent, bg="#f8f9fa")
            self.main_frame.pack(fill='both', expand=True)
            
            # Header frame
            self._create_header_frame()
            
            # List frame
            self._create_list_frame()
            
            # Pagination frame
            self._create_pagination_frame()
            
            # Status frame
            self._create_status_frame()
            
        except Exception as e:
            logger.error(f"Error setting up PaginatedListView: {e}")
            raise
    
    def _create_header_frame(self):
        """Create header with search and filters"""
        self.header_frame = tk.Frame(self.main_frame, bg="#f8f9fa")
        self.header_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        # Search functionality
        search_label = tk.Label(
            self.header_frame,
            text="🔍 Search:",
            font=('Segoe UI', 10),
            bg="#f8f9fa",
            fg="#333333"
        )
        search_label.pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            self.header_frame,
            textvariable=self.search_var,
            font=('Segoe UI', 10),
            width=30
        )
        self.search_entry.pack(side='left', padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Refresh button
        self.refresh_btn = tk.Button(
            self.header_frame,
            text="🔄 Refresh",
            command=self.refresh,
            font=('Segoe UI', 9),
            bg="#007bff",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        self.refresh_btn.pack(side='right', padx=(10, 0))
    
    def _create_list_frame(self):
        """Create the main list view"""
        list_frame = tk.Frame(self.main_frame, bg="#ffffff")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview with modern styling
        self.tree = ttk.Treeview(
            list_frame,
            columns=self.columns,
            show='headings',
            height=self.height,
            style=f"{self.style}.Treeview"
        )
        
        # Configure columns
        for col in self.columns:
            header_text = self.headers.get(col, col.title())
            self.tree.heading(col, text=header_text)
            
            # Set column width
            if col in self.widths:
                self.tree.column(col, width=self.widths[col])
            else:
                self.tree.column(col, width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal', command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Event bindings
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        if self.on_double_click_callback:
            self.tree.bind('<Double-1>', self._on_double_click)
        
        # Pack components
        self.tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
    
    def _create_pagination_frame(self):
        """Create modern pagination controls"""
        self.pagination_frame = tk.Frame(self.main_frame, bg="#f8f9fa")
        self.pagination_frame.pack(fill='x', padx=10, pady=5)
        
        # Page navigation
        self.first_btn = tk.Button(
            self.pagination_frame,
            text="⏮️",
            command=self.first_page,
            font=('Segoe UI', 9),
            bg="#6c757d",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3
        )
        self.first_btn.pack(side='left', padx=(0, 2))
        
        self.prev_btn = tk.Button(
            self.pagination_frame,
            text="⏪",
            command=self.previous_page,
            font=('Segoe UI', 9),
            bg="#6c757d",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3
        )
        self.prev_btn.pack(side='left', padx=2)
        
        # Page info
        self.page_info = tk.Label(
            self.pagination_frame,
            text="Page 1 of 1",
            font=('Segoe UI', 10),
            bg="#f8f9fa",
            fg="#333333"
        )
        self.page_info.pack(side='left', padx=10)
        
        self.next_btn = tk.Button(
            self.pagination_frame,
            text="⏩",
            command=self.next_page,
            font=('Segoe UI', 9),
            bg="#6c757d",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3
        )
        self.next_btn.pack(side='left', padx=2)
        
        self.last_btn = tk.Button(
            self.pagination_frame,
            text="⏭️",
            command=self.last_page,
            font=('Segoe UI', 9),
            bg="#6c757d",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3
        )
        self.last_btn.pack(side='left', padx=(2, 0))
    
    def _create_status_frame(self):
        """Create status information frame"""
        self.status_frame = tk.Frame(self.main_frame, bg="#f8f9fa")
        self.status_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Items count
        self.items_label = tk.Label(
            self.status_frame,
            text="No items",
            font=('Segoe UI', 9),
            bg="#f8f9fa",
            fg="#666666"
        )
        self.items_label.pack(side='left')
        
        # Performance info
        self.perf_label = tk.Label(
            self.status_frame,
            text="",
            font=('Segoe UI', 9),
            bg="#f8f9fa",
            fg="#666666"
        )
        self.perf_label.pack(side='right')
    
    def load_data(self, page=None, search_term=None):
        """Load data for a specific page"""
        if self.loading:
            return
        
        if page is not None:
            self.current_page = page
        
        if search_term is None:
            search_term = self.search_var.get() if self.search_var else ""
        
        self.loading = True
        
        def load_worker():
            try:
                if self.data_loader:
                    # Call the data loader with proper parameters
                    if hasattr(self.data_loader, '__call__'):
                        result = self.data_loader(
                            page=self.current_page,
                            page_size=self.page_size,
                            search=search_term
                        )
                        
                        # Update UI on main thread
                        self.parent.after(0, lambda: self.on_data_loaded(result))
                    else:
                        raise Exception("Data loader is not callable")
                else:
                    raise Exception("No data loader configured")
                    
            except Exception as e:
                error_msg = str(e)
                self.parent.after(0, lambda: self.on_data_error(error_msg))
        
        threading.Thread(target=load_worker, daemon=True).start()
    
    def on_data_loaded(self, result):
        """Handle loaded data"""
        self.loading = False
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Handle different result formats
        if hasattr(result, 'data'):
            # Object with data attribute
            data = result.data
            total_count = getattr(result, 'total_count', len(data))
        elif isinstance(result, dict):
            # Dictionary format
            data = result.get('data', result.get('items', []))
            total_count = result.get('total_count', result.get('total', len(data)))
        else:
            # Direct list format
            data = result if isinstance(result, list) else []
            total_count = len(data)
        
        # Add new items
        for row in data:
            if isinstance(row, dict):
                values = [row.get(col, '') for col in self.columns]
            else:
                values = [str(row)]
            self.tree.insert('', 'end', values=values)
        
        # Update pagination
        self.total_items = total_count
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        self._update_pagination()
        self._update_status()
    
    def on_data_error(self, error):
        """Handle data loading error"""
        self.loading = False
        logger.error(f"Data loading error: {error}")
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Update status to show error
        self.items_label.config(text=f"Error: {error}")
        self.perf_label.config(text="")
        
        # Reset pagination
        self.total_pages = 1
        self.total_items = 0
        self._update_pagination()
    
    def first_page(self):
        """Go to first page"""
        if self.current_page > 1:
            self.current_page = 1
            self.load_data(self.search_var.get() or None)
    
    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data(self.search_var.get() or None)
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data(self.search_var.get() or None)
    
    def last_page(self):
        """Go to last page"""
        if self.current_page < self.total_pages:
            self.current_page = self.total_pages
            self.load_data(self.search_var.get() or None)
    
    def refresh(self):
        """Refresh current data"""
        search_term = self.search_var.get() if self.search_var else ""
        self.load_data(search_term=search_term if search_term else None)
    
    def on_search_change(self, event):
        """Handle search input change with debounce"""
        # Debounce search
        if hasattr(self, '_search_after'):
            self.parent.after_cancel(self._search_after)
        
        self._search_after = self.parent.after(500, self.perform_search)
    
    def perform_search(self):
        """Execute search after debounce"""
        self.current_page = 1
        search_term = self.search_var.get().strip()
        self.load_data(search_term=search_term if search_term else None)
    
    def _on_search_change(self, event):
        """Handle search text change"""
        try:
            # Debounced search
            if hasattr(self, '_search_after'):
                self.parent.after_cancel(self._search_after)
            
            self._search_after = self.parent.after(300, self._perform_search)
            
        except Exception as e:
            logger.warning(f"Search change error: {e}")
    
    def _perform_search(self):
        """Perform the actual search"""
        try:
            self.current_page = 1
            search_term = self.search_var.get().strip()
            self.load_data(search_term=search_term if search_term else None)
        except Exception as e:
            logger.error(f"Search error: {e}")
    
    def _on_select(self, event):
        """Handle item selection"""
        try:
            selection = self.tree.selection()
            if selection and self.on_select_callback:
                item = self.tree.item(selection[0])
                self.selected_item = item['values']
                self.on_select_callback(event)
        except Exception as e:
            logger.warning(f"Selection error: {e}")
    
    def _on_double_click(self, event):
        """Handle double-click"""
        try:
            selection = self.tree.selection()
            if selection and self.on_double_click_callback:
                item = self.tree.item(selection[0])
                self.selected_item = item['values']
                self.on_double_click_callback(event)
        except Exception as e:
            logger.warning(f"Double-click error: {e}")
    
    def get_frame(self):
        """Get the main frame"""
        return self.main_frame
    
    def load_page(self, page: int):
        """Load a specific page"""
        try:
            if self.data_loader and not self.loading:
                search_term = self.search_var.get() if self.search_var else ""
                self.load_data(page=page, search_term=search_term)
        except Exception as e:
            logger.error(f"Error loading page {page}: {e}")
            self.loading = False
    
    def update_headers(self, headers: Dict[str, str]):
        """Update column headers"""
        try:
            self.headers.update(headers)
            for col in self.columns:
                if col in self.headers:
                    self.tree.heading(col, text=self.headers[col])
        except Exception as e:
            logger.warning(f"Could not update headers: {e}")
    
    def update_items(self, items: List[Any], total_count: int, current_page: int, total_pages: int):
        """Update the list with new items"""
        try:
            start_time = time.time()
            
            # Clear existing items
            self.tree.delete(*self.tree.get_children())
            
            # Store data
            self.current_data = items
            self.total_items = total_count
            self.current_page = current_page
            self.total_pages = total_pages
            
            # Insert new items
            for item in items:
                if isinstance(item, dict):
                    values = [item.get(col, '') for col in self.columns]
                elif isinstance(item, (list, tuple)):
                    values = item
                else:
                    values = [str(item)]
                
                self.tree.insert('', 'end', values=values)
            
            # Update pagination
            self._update_pagination()
            
            # Update status
            self._update_status()
            
            # Track performance
            load_time = (time.time() - start_time) * 1000
            self.last_load_time = load_time
            self.perf_label.config(text=f"Loaded in {load_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error updating items: {e}")
    
    def _update_pagination(self):
        """Update pagination controls"""
        try:
            # Update page info
            self.page_info.config(text=f"Page {self.current_page} of {self.total_pages}")
            
            # Update button states
            self.first_btn.config(state='normal' if self.current_page > 1 else 'disabled')
            self.prev_btn.config(state='normal' if self.current_page > 1 else 'disabled')
            self.next_btn.config(state='normal' if self.current_page < self.total_pages else 'disabled')
            self.last_btn.config(state='normal' if self.current_page < self.total_pages else 'disabled')
            
        except Exception as e:
            logger.warning(f"Could not update pagination: {e}")
    
    def _update_status(self):
        """Update status information"""
        try:
            start_item = ((self.current_page - 1) * self.page_size) + 1
            end_item = min(self.current_page * self.page_size, self.total_items)
            
            if self.total_items == 0:
                status_text = "No items"
            else:
                status_text = f"Showing {start_item}-{end_item} of {self.total_items} items"
            
            self.items_label.config(text=status_text)
            
        except Exception as e:
            logger.warning(f"Could not update status: {e}")
    
    def refresh(self):
        """Refresh current page"""
        search_term = self.search_var.get() if self.search_var else ""
        self.load_data(search_term=search_term if search_term else None)
    
    def get_selected_item(self):
        """Get the currently selected item"""
        return self.selected_item
    
    def pack(self, **kwargs):
        """Pack the main frame"""
        self.main_frame.pack(**kwargs)

class FastSearchEntry:
    """Fast autocomplete search entry"""
    
    def __init__(self, parent, search_function, on_select_callback=None, placeholder=None):
        self.parent = parent
        self.search_function = search_function
        self.on_select_callback = on_select_callback
        self.placeholder = placeholder
        self.search_results = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup search UI"""
        self.frame = tk.Frame(self.parent)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            self.frame,
            textvariable=self.search_var,
            font=('Arial', 12),
            width=30
        )
        
        # Set placeholder if provided
        if self.placeholder:
            self.search_entry.insert(0, self.placeholder)
            self.search_entry.bind('<FocusIn>', self._on_entry_focus_in)
            self.search_entry.bind('<FocusOut>', self._on_entry_focus_out)
            self.search_entry.config(fg='gray')
            self._placeholder_active = True
        else:
            self._placeholder_active = False
            
        self.search_entry.pack(fill='x')
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        self.search_entry.bind('<Down>', self.focus_results)
        
        # Results listbox
        self.results_frame = tk.Frame(self.frame)
        
        self.results_listbox = tk.Listbox(
            self.results_frame,
            height=6,
            font=('Arial', 10)
        )
        
        scrollbar = ttk.Scrollbar(
            self.results_frame,
            orient='vertical',
            command=self.results_listbox.yview
        )
        
        self.results_listbox.configure(yscrollcommand=scrollbar.set)
        self.results_listbox.bind('<Double-Button-1>', self.on_result_select)
        self.results_listbox.bind('<Return>', self.on_result_select)
        self.results_listbox.bind('<Up>', self.on_listbox_up)
        
        self.results_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Initially hidden
        self.hide_results()
    
    def on_search_change(self, event):
        """Handle search text change"""
        # Skip if placeholder is active
        if self._placeholder_active:
            return
            
        search_term = self.search_var.get().strip()
        
        if len(search_term) < 2:
            self.hide_results()
            return
        
        # Cancel previous search
        if hasattr(self, '_search_after'):
            self.parent.after_cancel(self._search_after)
        
        # Debounced search
        self._search_after = self.parent.after(300, lambda: self.perform_search(search_term))
    
    def perform_search(self, search_term):
        """Perform fast search"""
        def search_worker():
            try:
                results = self.search_function(search_term, limit=10)
                self.parent.after(0, lambda: self.display_results(results))
            except Exception as e:
                print(f"Search error: {e}")
        
        threading.Thread(target=search_worker, daemon=True).start()
    
    def display_results(self, results):
        """Display search results"""
        self.search_results = results
        self.results_listbox.delete(0, tk.END)
        
        if results:
            for item in results:
                # Handle different result formats
                if 'display' in item:
                    # Enhanced page format - use the pre-formatted display text
                    display_text = item['display']
                elif 'Name' in item:
                    # Original format for products
                    display_text = f"{item['Name']} - {item.get('Barcode', '')} (Stock: {item.get('Stock', '')})"
                else:
                    # Fallback format
                    display_text = str(item.get('id', item))
                    
                self.results_listbox.insert(tk.END, display_text)
            
            self.show_results()
        else:
            self.hide_results()
    
    def show_results(self):
        """Show results dropdown"""
        self.results_frame.pack(fill='both', expand=True, pady=(2, 0))
    
    def hide_results(self):
        """Hide results dropdown"""
        self.results_frame.pack_forget()
    
    def focus_results(self, event):
        """Focus on results listbox"""
        if self.results_listbox.size() > 0:
            self.results_listbox.focus_set()
            self.results_listbox.selection_set(0)
    
    def on_listbox_up(self, event):
        """Handle up arrow in listbox"""
        if self.results_listbox.curselection() and self.results_listbox.curselection()[0] == 0:
            self.search_entry.focus_set()
    
    def on_result_select(self, event):
        """Handle result selection"""
        selection = self.results_listbox.curselection()
        if selection and self.on_select_callback:
            selected_product = self.search_results[selection[0]]
            self.on_select_callback(selected_product)
            self.hide_results()
    
    def get_frame(self):
        """Get the main frame"""
        return self.frame
    
    def get_value(self):
        """Get current search text"""
        return self.search_var.get()
    
    def set_value(self, value):
        """Set search text"""
        if self._placeholder_active:
            self._clear_placeholder()
        self.search_var.set(value)
    
    def _on_entry_focus_in(self, event):
        """Handle entry focus in - clear placeholder"""
        if self._placeholder_active and self.search_entry.get() == self.placeholder:
            self._clear_placeholder()
    
    def _on_entry_focus_out(self, event):
        """Handle entry focus out - restore placeholder if empty"""
        if not self.search_entry.get().strip():
            self._set_placeholder()
    
    def _clear_placeholder(self):
        """Clear placeholder text"""
        if self._placeholder_active:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg='black')
            self._placeholder_active = False
    
    def _set_placeholder(self):
        """Set placeholder text"""
        if self.placeholder and not self._placeholder_active:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, self.placeholder)
            self.search_entry.config(fg='gray')
            self._placeholder_active = True