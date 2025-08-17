# main.py – fixed so that admin‑only buttons become active right after login
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import time
import os
from tkinter import Menu, messagebox

# ----------------------------------------------------------------------
# Embedded pages (already ported to in‑frame pages)
# ----------------------------------------------------------------------
from modules.pages.inventory_page  import InventoryPage
from modules.pages.sales_page      import SalesPage
from modules.pages.debits_page     import DebitsPage

# ----------------------------------------------------------------------
# Enhanced pages with optimized performance
# ----------------------------------------------------------------------
from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
from modules.pages.enhanced_sales_page import EnhancedSalesPage
from modules.pages.enhanced_debits_page import EnhancedDebitsPage

# Modern 2025 Style Pages (kept for reference)
from modules.pages.modern_inventory_page_2025 import ModernInventoryPage2025

# ----------------------------------------------------------------------
# New standalone Invoice Viewer (replaces inline legacy code)
# ----------------------------------------------------------------------
from modules.pages.invoice_viewer import show_all_invoices  # ✅ fixed path

# ----------------------------------------------------------------------
# Legacy pop‑up that is NOT yet ported
# ----------------------------------------------------------------------
from modules.Financial import financial_screen          # admin‑only

from modules.Login import LoginWindow, current_user
from modules.logger import logger
from modules.utils import init_background_tasks, shutdown_background_tasks, background_task_manager, run_in_background
from modules.db_manager import shutdown_pool, get_connection_stats, analyze_database_performance
from modules.data_access import stop_log_worker, clear_cache
from modules.optimize_db import run_comprehensive_optimization, optimize_database
from modules.performance_monitor import performance_monitor, shutdown_performance_monitoring

# Add internationalization support
from modules.i18n import _, switch_language, get_current_language, register_refresh_callback, unregister_refresh_callback, set_widget_direction

# Initialize database
from database.init_db import create_database

########################################################################
#  Main‑menu page (dashboard with four tiles)                           #
########################################################################
class MainMenuPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        
        # Create text variables for dynamic content
        self.lang_btn_text = tk.StringVar()
        self.title_text = tk.StringVar()
        self.login_text = tk.StringVar()
        self.inventory_btn_text = tk.StringVar()
        self.sales_btn_text = tk.StringVar()
        self.debits_btn_text = tk.StringVar()
        self.financial_btn_text = tk.StringVar()
        self.logout_btn_text = tk.StringVar()
        self.exit_btn_text = tk.StringVar()
        
        # Build the UI and register for language changes
        self._build_ui()
        self._retranslate()
        register_refresh_callback(self._retranslate)

    # called whenever we return to the menu so role/username are current
    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
        self._retranslate()

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Set widget direction based on language
        set_widget_direction(self)
        
        # ===== top bar =================================================
        top = ttk.Frame(self, padding=10, style="TFrame")
        top.pack(fill=tk.X)

        self.title_label = ttk.Label(top, textvariable=self.title_text,
                  style="Header.TLabel")
        self.title_label.pack(side=tk.LEFT, padx=(10, 20))

        self.time_lbl = ttk.Label(top, text="", style="SubHeader.TLabel")
        self.time_lbl.pack(side=tk.RIGHT, padx=(0, 10))
        self._tick()          # start clock

        role = current_user.get("Role", "").lower()
        user = current_user.get("Username", "")
        self.login_label = ttk.Label(top, textvariable=self.login_text,
                  style="SubHeader.TLabel")
        self.login_text.set(f"{_('Logged in as:')} {user} – {role}")
        self.login_label.pack(side=tk.LEFT, padx=(0, 20))
                  
        # Language toggle button
        self.lang_btn = ttk.Button(top, textvariable=self.lang_btn_text, 
                  bootstyle=INFO,
                  padding=(15, 5),
                  command=self._toggle_language)
        self.lang_btn.pack(side=tk.RIGHT, padx=10)

        # ===== middle grid (4 tiles) ===================================
        mid = ttk.Frame(self, padding=30, style="TFrame")
        mid.pack(expand=True, fill=tk.BOTH)
        
        # Inventory (embedded)
        self.inv_btn = ttk.Button(
            mid, 
            textvariable=self.inventory_btn_text, 
            bootstyle="primary-outline",
            padding=(40, 60),
            command=lambda: self.controller.show_frame("InventoryPage")
        )
        if role != "admin":
            self.inventory_btn_text.set(_("Manage Inventory") + "\n" + _("(Admin Only)"))
            self.inv_btn.configure(state="disabled")
        else:
            self.inventory_btn_text.set(_("Manage Inventory"))
        self.inv_btn.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")

        # Sales (embedded)
        self.sales_btn = ttk.Button(
            mid, 
            textvariable=self.sales_btn_text, 
            bootstyle="success-outline",
            padding=(40, 60),
            command=lambda: self.controller.show_frame("SalesPage")
        )
        self.sales_btn.grid(row=0, column=1, padx=30, pady=30, sticky="nsew")

        # Debits (embedded)
        self.debits_btn = ttk.Button(
            mid, 
            textvariable=self.debits_btn_text, 
            bootstyle="info-outline",
            padding=(40, 60),
            command=lambda: self.controller.show_frame("DebitsPage")
        )
        self.debits_btn.grid(row=1, column=0, padx=30, pady=30, sticky="nsew")

        # Financial (legacy pop‑up)
        self.fin_btn = ttk.Button(
            mid, 
            textvariable=self.financial_btn_text, 
            bootstyle="secondary-outline",
            padding=(40, 60),
            command=lambda: financial_screen(self.controller)
        )
        if role != "admin":
            self.financial_btn_text.set(_("Financial Dashboard") + "\n" + _("(Admin Only)"))
            self.fin_btn.configure(state="disabled")
        else:
            self.financial_btn_text.set(_("Financial Dashboard"))
        self.fin_btn.grid(row=1, column=1, padx=30, pady=30, sticky="nsew")

        # make the 2×2 grid responsive
        for r in range(2):
            mid.rowconfigure(r, weight=1)
        for c in range(2):
            mid.columnconfigure(c, weight=1)

        # ===== bottom bar ==============================================
        bottom = ttk.Frame(self, padding=10, style="TFrame")
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        self.logout_btn = ttk.Button(
            bottom, 
            textvariable=self.logout_btn_text, 
            bootstyle="warning-outline",
            padding=20,
            command=self._logout
        )
        self.logout_btn.pack(side=tk.LEFT, padx=20, pady=20)
        
        self.exit_btn = ttk.Button(
            bottom, 
            textvariable=self.exit_btn_text, 
            bootstyle="danger-outline",
            padding=20,
            command=self.controller.destroy
        )
        self.exit_btn.pack(side=tk.LEFT, padx=20, pady=20)
    
    # Update all text variables with translated strings
    def _retranslate(self):
        # Set widget direction based on language
        set_widget_direction(self)
        
        # Main title and login info
        self.title_text.set(_("Sales Management System"))
        
        # Update login text with current user info
        role = current_user.get("Role", "").lower()
        user = current_user.get("Username", "")
        self.login_text.set(f"{_('Logged in as:')} {user} – {role}")
        
        # Button texts
        current_lang = get_current_language()
        self.lang_btn_text.set(_("Switch to Arabic") if current_lang == 'en' else _("Switch to English"))
        
        # Main menu buttons
        if current_user.get("Role", "").lower() != "admin":
            self.inventory_btn_text.set(_("Manage Inventory") + "\n" + _("(Admin Only)"))
            self.financial_btn_text.set(_("Financial Dashboard") + "\n" + _("(Admin Only)"))
        else:
            self.inventory_btn_text.set(_("Manage Inventory"))
            self.financial_btn_text.set(_("Financial Dashboard"))
            
        self.sales_btn_text.set(_("Sales Screen"))
        self.debits_btn_text.set(_("Manage Debits"))
        self.logout_btn_text.set(_("Logout"))
        self.exit_btn_text.set(_("Exit"))

    # ------------------------------------------------------------------
    def _tick(self):
        # Check if widget still exists before proceeding
        if not self.winfo_exists():
            return
            
        self.time_lbl.config(text=time.strftime("%Y‑%m‑%d %H:%M:%S"))
        self.after(1000, self._tick)

    # ------------------------------------------------------------------
    def _toggle_language(self):
        """Toggle between English and Arabic languages"""
        current_lang = get_current_language()
        new_lang = 'ar' if current_lang == 'en' else 'en'
        
        # Switch the language
        switch_language(new_lang)
        
        # Update the window title
        self.controller.title(_("Sales Management System"))
        
        # Force refresh of all frames to apply language changes
        for frame_name, frame in self.controller.frames.items():
            if hasattr(frame, '_retranslate'):
                frame._retranslate()
            elif hasattr(frame, 'refresh'):
                frame.refresh()
        
        # Rebuild current page to apply language changes
        self.refresh()
        
        # Force direction update on the main container
        set_widget_direction(self.controller)
        
        # Update the current frame to reflect changes
        current_frame = self.controller.current_frame
        if current_frame:
            self.controller.show_frame(current_frame)

    # ------------------------------------------------------------------
    def _logout(self):
        current_user.clear()
        self.controller.withdraw()
        
        def try_login():
            LoginWindow(self.controller)
            # Wait for the modal window without blocking
            self.controller.wait_window(self.controller.winfo_children()[-1])
            
            # Check if login was successful
            if current_user.get("Username"):
                logger.info("User logged in: " + current_user["Username"])
                self.controller.deiconify()
                self.refresh()
            else:
                # Ask if user wants to exit
                if messagebox.askyesno(_("Exit"), _("Login cancelled or failed. Exit the program?")):
                    self.controller.destroy()
                else:
                    # Try again after a short delay
                    self.after(100, try_login)
        
        # Start the login process
        try_login()
        
    def __del__(self):
        # Unregister callback when page is destroyed
        unregister_refresh_callback(self._retranslate)

########################################################################
#  Main application window                                             #
########################################################################
class MainApp(ttk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(_("Sales Management System"))
        self.state("zoomed")  # Start maximized
        self.minsize(1024, 768)  # Set minimum size        # Dictionary to store frames
        self.frames = {}
        
        # Track current frame
        self.current_frame = None
        
        # Initialize background task processing
        init_background_tasks()
        self.after(100, self._process_background_tasks)
          # Flag to use enhanced pages for better performance
        self.use_enhanced_pages = True  # Set to False to use the original pages

        # Set up styles first
        self._setup_styles()
        
        # Start database initialization in background
        self._initialize_db()
        
        # Register for language changes to update window title and direction
        register_refresh_callback(self._on_language_change)
        
    def _initialize_db(self):
        """Initialize the database structure"""
        logger.info("Initializing database...")
        
        # Show a status dialog
        self.progress = ttk.Toplevel(self)
        self.progress.title(_("Initializing Database"))
        self.progress.geometry("400x200")
        self.progress.transient(self)
        self.progress.grab_set()
        
        # Add progress label and indicator
        ttk.Label(
            self.progress, 
            text=_("Initializing database schema..."),
            font=("Helvetica", 12)
        ).pack(pady=20)
        
        self.progress_bar = ttk.Progressbar(
            self.progress, 
            bootstyle="success-striped",
            mode="indeterminate",
            length=300
        )
        self.progress_bar.pack(pady=10, padx=20)
        self.progress_bar.start()
        
        # Status label for current operation
        self.status_label = ttk.Label(
            self.progress,
            text=_("Creating tables..."),
            font=("Helvetica", 10)
        )
        self.status_label.pack(pady=10)
        
        # Run database initialization in background
        run_in_background(
            create_database,
            on_complete=self._after_db_init,
            on_error=self._on_db_init_error
        )
        
    def _after_db_init(self, result=None):
        """Called after database initialization completes successfully"""
        # Update status
        self.status_label.config(text=_("Optimizing database..."))
        
        # Run database optimizations in background
        run_in_background(
            run_comprehensive_optimization,  # Run the comprehensive optimization
            on_complete=self._after_optimization,
            on_error=self._on_db_optimization_error
        )
    
    def _after_optimization(self, result=None):
        """Called after database optimization completes"""
        # Log optimization results
        if result and result.get("success"):
            steps = ", ".join(result.get("steps_completed", []))
            logger.info(f"Database optimization completed successfully in {result.get('duration_seconds', 0)} seconds. Steps: {steps}")
        else:
            logger.warning("Database optimization may not have been fully successful")
        
        # Close progress dialog
        self.progress_bar.stop()
        self.progress.destroy()
        
        # Continue with login process
        self._do_login()
        
    def _do_login(self):
        """Handle the login process"""
        LoginWindow(self)
        self.wait_window(self.winfo_children()[-1])  # wait for modal
        
        if current_user.get("Username"):
            logger.info("User logged in: " + current_user["Username"])
            # Initialize UI now that we have a logged-in user
            self._initialize_ui()
            self.deiconify()  # Show window after login
        else:
            if messagebox.askyesno(_("Exit"), _("Login cancelled or failed. Exit the program?")):
                self.destroy()
            else:
                # Try again
                self.after(100, self._do_login)
        
    def _on_db_optimization_error(self, error):
        """Handle errors during database optimization"""
        logger.error(f"Database optimization error: {str(error)}")
        # We'll continue anyway, just log the error
        self.progress_bar.stop()
        self.progress.destroy()
        self._initialize_ui()
        
    def _on_db_init_error(self, error):
        """Handle errors during database initialization"""
        logger.error(f"Database initialization error: {str(error)}")
        self.progress_bar.stop()
        self.progress.destroy()
        
        # Show error and exit
        messagebox.showerror(
            _("Database Error"),
            _("Failed to initialize database. The application will exit.") + f"\n\nError: {str(error)}"
        )
        self.destroy()

    def _on_language_change(self):
        """Handle language changes at the application level"""
        # Update window title
        self.title(_("Sales Management System"))
        
        # Update widget direction
        set_widget_direction(self)

    def _initialize_ui(self):
        """Initialize the UI after successful login"""
        # Set widget direction based on language
        set_widget_direction(self)
        
        # Setup visual styles
        self._setup_styles()
        
        # Create the page container
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Create a frame inside the container for the page content
        self.scroll_frame = ttk.Frame(container)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew")
        self.scroll_frame.grid_rowconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Configure protocol for window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Initialize all pages with error handling
        self.frames = {}
          # Define the page classes to load
        if self.use_enhanced_pages:
            logger.info("Using professional enhanced inventory management system")
            page_classes = [
                MainMenuPage,
                EnhancedInventoryPage,  # Professional enhanced inventory page
                EnhancedSalesPage,
                EnhancedDebitsPage
            ]
        else:
            logger.info("Using standard pages")
            page_classes = [
                MainMenuPage, 
                InventoryPage, 
                SalesPage, 
                DebitsPage
            ]
            
        for PageClass in page_classes:
            try:
                page_name = PageClass.__name__
                # For enhanced pages, register them with the standard page name for compatibility
                if page_name.startswith("Enhanced"):
                    # Remove 'Enhanced' prefix and register with the base page name
                    register_name = page_name.replace("Enhanced", "")
                elif page_name == "ModernInventoryPage2025":
                    # Register modern inventory page as standard InventoryPage
                    register_name = "InventoryPage"
                elif page_name == "ProfessionalInventoryPage":
                    # Register professional inventory page as standard InventoryPage
                    register_name = "InventoryPage"
                else:
                    register_name = page_name
                    
                logger.info(f"Initializing page: {page_name}")
                frame = PageClass(parent=self.scroll_frame, controller=self)
                self.frames[register_name] = frame
                frame.grid(row=0, column=0, sticky="nsew")
                logger.info(f"Successfully initialized page: {page_name}")
                
            except Exception as e:
                # Log the error and try fallback for enhanced pages
                logger.error(f"Error initializing page {PageClass.__name__}: {str(e)}")
                
                # If this is an enhanced page that failed, try to load the standard version as fallback
                if page_name.startswith("Enhanced") or page_name == "ModernInventoryPage2025" or page_name == "ProfessionalInventoryPage":
                    if page_name == "ModernInventoryPage2025" or page_name == "ProfessionalInventoryPage":
                        fallback_name = "InventoryPage"
                    else:
                        fallback_name = page_name.replace("Enhanced", "")
                    logger.info(f"Attempting fallback to standard {fallback_name}")
                    
                    try:
                        # Import and use the standard page instead
                        if fallback_name == "SalesPage":
                            from modules.pages.sales_page import SalesPage as FallbackPage
                        elif fallback_name == "InventoryPage":
                            from modules.pages.inventory_page import InventoryPage as FallbackPage
                        elif fallback_name == "DebitsPage":
                            from modules.pages.debits_page import DebitsPage as FallbackPage
                        else:
                            raise Exception(f"No fallback available for {fallback_name}")
                            
                        logger.info(f"Loading fallback page: {fallback_name}")
                        frame = FallbackPage(parent=self.scroll_frame, controller=self)
                        self.frames[register_name] = frame
                        frame.grid(row=0, column=0, sticky="nsew")
                        logger.info(f"Successfully loaded fallback page: {fallback_name}")
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed for {fallback_name}: {str(fallback_error)}")
                        # Show warning but continue with other pages
                        messagebox.showwarning(
                            "Page Loading Error", 
                            f"Could not load {page_name} or its fallback. Some functionality may be limited.",
                            parent=self
                        )
                else:
                    # For non-enhanced pages, just show warning
                    messagebox.showwarning(
                        "Page Initialization Error",
                        f"Could not initialize {PageClass.__name__}. Some functionality may be limited.\nError: {str(e)}",
                        parent=self
                    )
        
        # Show the main menu initially - fallback to the first available page if MainMenuPage fails
        if "MainMenuPage" in self.frames:
            self.show_frame("MainMenuPage")
        elif self.frames:
            # Get the first available page
            first_page = next(iter(self.frames.keys()))
            self.show_frame(first_page)
            logger.warning(f"MainMenuPage not available, showing {first_page} instead")
        else:
            # Critical error - no pages available
            logger.critical("No pages could be initialized!")
            messagebox.showerror(
                "Critical Error",
                "No pages could be initialized. The application will close.",
                parent=self
            )
            self.after(1000, self.destroy)
            return
        
        # Start background task processing
        self._process_background_tasks()
        
        # Start periodic maintenance tasks
        self._periodic_maintenance()

    def _setup_styles(self):
        """Set up custom TTK styles for the application."""
        s = self.style
        
        # Base frame background
        s.configure("TFrame", background="#2B2B2B")
        
        # Label styles with increased font sizes
        s.configure("TLabel", background="#2B2B2B", foreground="#FFFFFF", font=("Helvetica", 14))
        s.configure("Header.TLabel", background="#2B2B2B", foreground="#FFFFFF", font=("Helvetica", 24, "bold"))
        s.configure("SubHeader.TLabel", background="#2B2B2B", foreground="#FFFFFF", font=("Helvetica", 18))
        
        # Button styles - keep the default style but adjust padding for touch
        s.configure("TButton", padding=15)
        
        # Make sure Small.TButton works for back buttons
        s.configure("Small.TButton", padding=5)
        
        # Category button style for inventory page
        s.configure("Outline.TButton", padding=18)
        
        # Make scrollbars more touch-friendly
        s.configure("Vertical.TScrollbar", arrowsize=20)
        s.configure("Horizontal.TScrollbar", arrowsize=20)
        
        # Form controls with larger text
        s.configure("TEntry", font=("Helvetica", 14))
        s.configure("TSpinbox", font=("Helvetica", 14))
        s.configure("TCombobox", padding=5, font=("Helvetica", 14))
        
        # Configure even/odd row colors for Treeview
        # Light theme colors
        s.configure('evenrow.Treeview', background='#f0f0f0')
        s.configure('oddrow.Treeview', background='#e0e0e0')
        
        # Dark theme colors - better contrast for dark themes
        s.configure('evenrow.Dark.Treeview', background='#383838')
        s.configure('oddrow.Dark.Treeview', background='#2D2D2D')

    def show_frame(self, page_name: str):
        """Show a frame for the given page name"""
        try:
            # Start timing for performance measurement
            start_time = time.time()
            
            # Get the frame
            frame = self.frames[page_name]
            
            # Check if frame has a prepare_for_display method (enhanced pages may have this)
            if hasattr(frame, 'prepare_for_display'):
                # Enhanced pages may have async preparation steps
                logger.info(f"Preparing enhanced page {page_name} for display")
                frame.prepare_for_display()
                
            # Refresh the frame if it supports it
            if hasattr(frame, 'refresh'):
                frame.refresh()
                
            # Bring the frame to the front
            frame.tkraise()
            self.current_frame = page_name  # Track current frame
            
            # Log performance metrics
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            logger.info(f"Page transition to {page_name} completed in {duration:.2f}ms")
            
        except KeyError:
            logger.error(f"Attempted to show non-existent frame: {page_name}")
            messagebox.showwarning(
                "Navigation Error",
                f"The requested page '{page_name}' is not available.",
                parent=self
            )
        except Exception as e:
            logger.error(f"Error showing frame {page_name}: {str(e)}")
            messagebox.showwarning(
                "Navigation Error",
                f"Could not display the requested page '{page_name}'.\nError: {str(e)}",
                parent=self
            )
    
    def _process_background_tasks(self):
        """Process completed background tasks and monitor performance"""
        try:
            # Process any pending background task results
            if background_task_manager:
                start_time = time.time()
                processed = background_task_manager.process_results(self)
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Log performance metrics if tasks were processed
                if processed > 0:
                    logger.debug(f"Processed {processed} background tasks in {processing_time:.2f}ms")
                
                # Track performance metrics (every 60 seconds)
                if not hasattr(self, '_perf_counter'):
                    self._perf_counter = 0
                    self._perf_data = {
                        'task_count': 0,
                        'total_processing_time': 0,
                        'last_report': time.time()
                    }
                
                self._perf_counter += 1
                if processed > 0:
                    self._perf_data['task_count'] += processed
                    self._perf_data['total_processing_time'] += processing_time
                
                # Report performance statistics every 60 seconds if there was activity
                if time.time() - self._perf_data['last_report'] > 60 and self._perf_data['task_count'] > 0:
                    avg_time = self._perf_data['total_processing_time'] / self._perf_data['task_count'] if self._perf_data['task_count'] > 0 else 0
                    logger.info(f"Performance report: Processed {self._perf_data['task_count']} tasks in the last minute, average processing time: {avg_time:.2f}ms")
                    
                    # Reset counters
                    self._perf_data['task_count'] = 0
                    self._perf_data['total_processing_time'] = 0
                    self._perf_data['last_report'] = time.time()
            
            # Schedule this function to run again
            self.after(100, self._process_background_tasks)
        except Exception as e:
            logger.error(f"Error processing background tasks: {str(e)}")
            # Keep trying despite errors
            self.after(500, self._process_background_tasks)
    
    def _periodic_maintenance(self):
        """Run periodic maintenance tasks like cache cleanup and database optimization"""
        try:
            # Run this maintenance every 15 minutes (900000 ms)
            self.maintenance_counter = getattr(self, 'maintenance_counter', 0) + 1
            
            # Every 15 minutes, perform cleanup
            if self.maintenance_counter >= 15:
                self.maintenance_counter = 0
                
                # Clean up cache to prevent memory leaks
                run_in_background(
                    clear_cache,
                    600,  # Clear items older than 10 minutes
                    on_complete=lambda result: logger.info(f"Cache cleanup completed: {result} entries cleared"),
                    on_error=lambda e: logger.error(f"Cache cleanup error: {str(e)}")
                )
                
                # Log connection statistics
                stats = get_connection_stats()
                logger.info(f"Database connection stats: active={stats['active']}, peak={stats['peak']}, created={stats['created']}")
                
            # Schedule next maintenance check in 1 minute
            self.after(60000, self._periodic_maintenance)
        except Exception as e:
            logger.error(f"Error in periodic maintenance: {str(e)}")
            # Keep trying despite errors
            self.after(60000, self._periodic_maintenance)
            
    def _on_close(self):
        """Handle application close event"""
        logger.info("Application closing...")
        
        try:
            # Clean up resources
            if messagebox.askyesno(_("Exit"), _("Are you sure you want to exit?")):
                # Log database connection stats for monitoring performance
                try:
                    stats = get_connection_stats()
                    logger.info(f"Final database connection stats: " 
                                f"active={stats['active']}, peak={stats['peak']}, "
                                f"total created={stats['created']}, total returned={stats['returned']}")
                except:
                    pass
                  # Unregister language change callback
                unregister_refresh_callback(self._on_language_change)
                
                # Shut down threads and connections
                shutdown_background_tasks()
                stop_log_worker()
                shutdown_pool()
                shutdown_performance_monitoring()
                
                # Log final performance metrics
                logger.info("Final shutdown, application terminating")
                
                # Destroy main window
                self.destroy()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self.destroy()

########################################################################
#  Entry point                                                         #
########################################################################
def main():
    app = MainApp(themename="darkly")
    # Set window close handler BEFORE starting the main loop
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    # Start the main application loop
    app.mainloop()

if __name__ == "__main__":
    main()


























