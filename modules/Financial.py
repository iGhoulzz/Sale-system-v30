# modules/Financial.py
# Financial dashboard – 2025‑04‑18 fixed build

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import Toplevel, BOTH, messagebox, END, StringVar, X, Y, LEFT, W, E
import time
from modules.db_manager import get_connection, ConnectionContext, return_connection
from modules.pages.invoice_viewer import show_all_invoices, show_invoices_for_user
from modules.utils import run_in_background
# Import i18n support
from modules.i18n import _, tr, set_widget_direction, register_refresh_callback, unregister_refresh_callback

# Message constants for internationalization
MSG_FINANCIAL_DASHBOARD = "Financial Dashboard"
MSG_MONTH = "Month (YYYY‑MM)"
MSG_ALL = "All"
MSG_APPLY = "Apply"
MSG_REFRESH = "Refresh"
MSG_VIEW_ALL_INVOICES = "View All Invoices"
MSG_FIX_ADMIN_RECORDS = "Fix Admin Records"
MSG_BACK_HOME = "Back to Home"
MSG_TOTAL_SALES = "Total Sales"
MSG_OUTSTANDING_DEBITS = "Outstanding Debits"
MSG_PROFIT = "Profit"
MSG_LOSSES = "Losses"
MSG_SALES_BY_USER = "Sales by User"
MSG_USER = "User"
MSG_TOTAL = "Total Sales"
MSG_COUNT = "# of Sales"
MSG_USERS_ACTIVITY = "Users & Activity"
MSG_SELECT_USER = "Select a user to view details"
MSG_VIEW_SALES = "View User Sales"
MSG_USER_ACTIVITY_LOG = "User Activity Log"
MSG_WARNING = "Warning"
MSG_PLEASE_SELECT_USER = "Please select a user first"
MSG_ACTIVITY_LOG_FOR = "Activity Log for"
MSG_CLOSE = "Close"
MSG_ACTION = "Action"
MSG_DATE_TIME = "Date / Time"
MSG_RECENT_ACTIVITY = "Recent Activity"
MSG_ERROR = "Error"
MSG_ERROR_LOADING_LOGS = "Error fetching logs"
MSG_ERROR_LOADING_DATA = "Error loading data"

# Background thread to load data without freezing
def background_load_data(where_clause, args, callback=None):
    """
    Load financial data from database and return results
    
    Args:
        where_clause: SQL WHERE clause for filtering
        args: Parameters for the query
        callback: Optional callback function (deprecated, kept for backward compatibility)
    
    Returns:
        A tuple with (total_sales, total_debits, profit, losses, sales_data)
    """
    try:
        # Use ConnectionContext for thread-safe DB access
        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            # totals
            cur.execute(f"SELECT SUM(TotalAmount) FROM Invoices {where_clause}", args)
            ts = cur.fetchone()[0] or 0.0
            cur.execute(f"SELECT SUM(Amount) FROM Debits WHERE Status='Pending' {' AND ' + where_clause if where_clause else ''}", args)
            td = cur.fetchone()[0] or 0.0

            # profit (Selling‑Buying) - Optimized query using proper JOIN on ProductID instead of Name
            cur.execute(f"""
                SELECT SUM(ii.Quantity * (ii.Price - IFNULL(p.BuyingPrice,0)))
                FROM InvoiceItems ii
                JOIN Invoices i ON i.InvoiceID = ii.InvoiceID
                LEFT JOIN Products p ON p.ProductID = ii.ProductID
                {where_clause}
            """, args)
            tp = cur.fetchone()[0] or 0.0

            # losses (stock write‑off) - Added index hint
            cur.execute(f"""
                SELECT SUM(l.Quantity * IFNULL(p.BuyingPrice, 0)) as LossValue
                FROM Losses l
                LEFT JOIN Products p ON p.ProductID = l.ProductID /* index: idx_products_productid */
                {where_clause} {'AND' if where_clause else 'WHERE'} l.DateTime IS NOT NULL
            """, args)
            tl = cur.fetchone()[0] or 0.0

            # sales by person - Added LIMIT to prevent huge result sets
            cur.execute(f"""
                SELECT 
                    ShiftEmployee, 
                    SUM(TotalAmount) as Total,
                    COUNT(*) as Count
                FROM 
                    Invoices
                {where_clause}
                GROUP BY ShiftEmployee
                ORDER BY Total DESC
                LIMIT 1000
            """, args)
            sales_data = [(row[0], row[1], row[2]) for row in cur.fetchall()]
            
            # If callback is provided (for backward compatibility), call it
            results = (ts, td, tp, tl, sales_data)
            if callback:
                callback(results)
            
            # Return results
            return results
    except Exception as e:
        raise Exception(f"Error fetching financial data: {str(e)}")

# Fix admin records for older data
def fix_admin_records():
    """Fix any admin records that may have incorrect data"""
    try:
        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            # Fix any invoices with missing admin records
            cur.execute("""
                UPDATE Invoices 
                SET AdminID = (SELECT UserID FROM Users WHERE Role = 'admin' LIMIT 1)
                WHERE AdminID IS NULL
            """)
            
            # Fix any activity logs with missing admin records
            cur.execute("""
                UPDATE ActivityLog 
                SET UserID = (SELECT UserID FROM Users WHERE Role = 'admin' LIMIT 1)
                WHERE UserID IS NULL
            """)
            
            conn.commit()
            messagebox.showinfo(_("Success"), _("Admin records have been fixed successfully"))
    except Exception as e:
        messagebox.showerror(_("Error"), f"Error fixing admin records: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
def financial_screen(master):
    fin = Toplevel(master)
    fin.title(tr(MSG_FINANCIAL_DASHBOARD))
    fin.geometry("1200x800")
    
    # Set widget direction based on language
    set_widget_direction(fin)
    
    # Track active tasks to prevent updates after widget destruction
    active_tasks = {"data_loading": False, "logs_loading": False}
    
    # Throttling variables to limit refresh frequency
    last_data_refresh = 0
    last_logs_refresh = 0
    refresh_interval = 3000  # 3 seconds minimum between refreshes

    # Handle window close event
    def on_close():
        # Cancel any pending background tasks
        for task in active_tasks:
            active_tasks[task] = False
        fin.destroy()
    
    fin.protocol("WM_DELETE_WINDOW", on_close)

    # Function to refresh UI when language changes
    def refresh_language():
        # Only update if window still exists
        if not fin.winfo_exists():
            return
            
        # Update window title
        fin.title(tr(MSG_FINANCIAL_DASHBOARD))
        
        # Update widget direction
        set_widget_direction(fin)
        
        # Reload data with the current language
        load_data(month_var.get())
        load_logs()
        
        # Update tab texts
        notebook.tab(0, text=tr(MSG_SALES_BY_USER))
        notebook.tab(1, text=tr(MSG_USERS_ACTIVITY))
        notebook.tab(2, text=tr(MSG_RECENT_ACTIVITY))
        
        # Update button texts
        for btn in controls.winfo_children():
            if isinstance(btn, ttk.Button):
                if btn['text'] == MSG_APPLY:
                    btn.config(text=tr(MSG_APPLY))
                elif btn['text'] == MSG_REFRESH:
                    btn.config(text=tr(MSG_REFRESH))
                elif btn['text'] == MSG_VIEW_ALL_INVOICES:
                    btn.config(text=tr(MSG_VIEW_ALL_INVOICES))
                elif btn['text'] == MSG_FIX_ADMIN_RECORDS:
                    btn.config(text=tr(MSG_FIX_ADMIN_RECORDS))
                elif btn['text'] == MSG_BACK_HOME:
                    btn.config(text=tr(MSG_BACK_HOME))
    
    # Register for language changes
    register_refresh_callback(refresh_language)

    # — helper loaders — ------------------------------------------------------
    def load_data(month):
        nonlocal last_data_refresh
        
        # Throttle refreshes to prevent UI flooding
        now = time.time() * 1000  # convert to ms
        if now - last_data_refresh < refresh_interval and active_tasks["data_loading"]:
            return  # Skip this refresh if too soon after the last one
            
        # Update last refresh time
        last_data_refresh = now
        
        # Show loading indicators
        total_lbl.config(text=tr(MSG_TOTAL_SALES) + ": " + tr("Loading..."))
        debit_lbl.config(text=tr(MSG_OUTSTANDING_DEBITS) + ": " + tr("Loading..."))
        profit_lbl.config(text=tr(MSG_PROFIT) + ": " + tr("Loading..."))
        loss_lbl.config(text=tr(MSG_LOSSES) + ": " + tr("Loading..."))
        sales_tbl.delete(*sales_tbl.get_children())
        sales_tbl.insert("", END, values=(tr("Loading data..."), "", ""))
        
        # Set active task flag
        active_tasks["data_loading"] = True
        
        # Prepare query parameters
        where = "WHERE strftime('%Y-%m', DateTime)=?" if month != tr(MSG_ALL) else ""
        args  = [month] if month != tr(MSG_ALL) else []
        
        # Callback to handle results from background thread
        def handle_data_result(results):
            # Only update UI if widget still exists and task is active
            if not fin.winfo_exists() or not active_tasks["data_loading"]:
                return
                
            try:    
                # Unpack the results tuple (should have 5 elements)
                if isinstance(results, tuple) and len(results) == 5:
                    ts, td, tp, tl, sales_data = results
                    total_lbl.config(text=f"{tr(MSG_TOTAL_SALES)}: ${ts:.2f}")
                    debit_lbl.config(text=f"{tr(MSG_OUTSTANDING_DEBITS)}: ${td:.2f}")
                    profit_lbl.config(text=f"{tr(MSG_PROFIT)}: ${tp:.2f}")
                    loss_lbl.config(text=f"{tr(MSG_LOSSES)}: ${tl:.2f}")
                    
                    # Update sales table
                    sales_tbl.delete(*sales_tbl.get_children())
                    for u, tot, count in sales_data:
                        sales_tbl.insert("", END, values=(u, f"${tot:.2f}", count))
                else:
                    messagebox.showerror(tr(MSG_ERROR), f"Unexpected data format: {results}", parent=fin)
            except Exception as e:
                messagebox.showerror(tr(MSG_ERROR), f"{tr(MSG_ERROR_LOADING_DATA)}: {str(e)}", parent=fin)
            finally:    
                # Clear active task flag
                active_tasks["data_loading"] = False
        
        def handle_data_error(error):
            # Only update UI if widget still exists and task is active
            if not fin.winfo_exists() or not active_tasks["data_loading"]:
                return
                
            messagebox.showerror(tr(MSG_ERROR), f"{tr(MSG_ERROR_LOADING_DATA)}: {str(error)}", parent=fin)
            
            # Clear active task flag
            active_tasks["data_loading"] = False
        
        # Use the central background task manager instead of raw threads
        run_in_background(
            background_load_data,
            where, args,
            on_complete=handle_data_result,
            on_error=handle_data_error
        )

    def load_logs():
        nonlocal last_logs_refresh
        
        # Throttle refreshes to prevent UI flooding
        now = time.time() * 1000  # convert to ms
        if now - last_logs_refresh < refresh_interval and active_tasks["logs_loading"]:
            return  # Skip this refresh if too soon after the last one
            
        # Update last refresh time
        last_logs_refresh = now
        
        logs_tbl.delete(*logs_tbl.get_children())
        logs_tbl.insert("", END, values=(tr("Loading logs..."), "", ""))
        
        # Set active task flag
        active_tasks["logs_loading"] = True
        
        # Callback to handle results from background thread
        def handle_logs_result(result):
            # Only update UI if widget still exists and task is active
            if not fin.winfo_exists() or not active_tasks["logs_loading"]:
                return
                
            try:
                logs_tbl.delete(*logs_tbl.get_children())
                for i, (u, act, dt) in enumerate(result):
                    tag = "evenrow" if i % 2 == 0 else "oddrow"
                    logs_tbl.insert("", END, values=(u, act, dt), tags=(tag,))
            except Exception as e:
                messagebox.showerror(tr(MSG_ERROR), f"{tr(MSG_ERROR_LOADING_LOGS)}: {str(e)}", parent=fin)
            finally:
                # Clear active task flag
                active_tasks["logs_loading"] = False
        
        def handle_logs_error(error):
            # Only update UI if widget still exists and task is active
            if not fin.winfo_exists() or not active_tasks["logs_loading"]:
                return
                
            messagebox.showerror(tr(MSG_ERROR), f"{tr(MSG_ERROR_LOADING_LOGS)}: {str(error)}", parent=fin)
            
            # Clear active task flag
            active_tasks["logs_loading"] = False
        
        def load_logs_thread():
            try:
                # Use ConnectionContext for thread safety
                with ConnectionContext() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT u.Username, a.Action, a.DateTime
                        FROM ActivityLog a
                        JOIN Users u ON a.UserID = u.UserID
                        ORDER BY a.DateTime DESC
                        LIMIT 100
                    """)
                    logs = [(row[0], row[1], row[2]) for row in cur.fetchall()]
                    return logs
            except Exception as e:
                raise Exception(f"Error loading logs: {str(e)}")
                
        # Run log loading in background thread
        run_in_background(
            load_logs_thread,
            on_complete=handle_logs_result,
            on_error=handle_logs_error
        )
    
    def selected_user():
        """Return the currently selected user or None"""
        sel = users_tbl.selection()
        if not sel:
            return None
        return users_tbl.item(sel[0], 'values')[0]  # User name is in first column

    def view_user_sales():
        """Show all sales for the selected user"""
        u = selected_user()
        if not u: 
            messagebox.showwarning(tr(MSG_WARNING), tr(MSG_PLEASE_SELECT_USER), parent=fin)
            return
        show_invoices_for_user(fin, u)

    # — top controls ----------------------------------------------------------
    top = ttk.Frame(fin, padding=15); top.pack(fill=X)
    ttk.Label(top, text=tr(MSG_FINANCIAL_DASHBOARD), 
             font=("Helvetica", 24, "bold")).pack(side=LEFT, padx=(0, 20))
    
    controls = ttk.Frame(top, padding=5); controls.pack(side=LEFT, fill=X, expand=True)
    ttk.Label(controls, text=tr(MSG_MONTH) + ":", font=("Helvetica", 16)).pack(side=LEFT)

    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT DISTINCT strftime('%Y-%m', DateTime) FROM Invoices ORDER BY 1 DESC")
        months = [r[0] for r in cur.fetchall()]; return_connection(conn)
    except: months = []
    month_var = StringVar(value=tr(MSG_ALL))
    ttk.Combobox(controls, textvariable=month_var,
                 values=[tr(MSG_ALL)] + months, state="readonly",
                 font=("Helvetica", 16), width=10).pack(side=LEFT, padx=5)
    ttk.Button(controls, text=tr(MSG_APPLY),   bootstyle=PRIMARY,
               command=lambda: (load_data(month_var.get()), load_logs()), padding=10
               ).pack(side=LEFT, padx=5)
    ttk.Button(controls, text=tr(MSG_REFRESH), bootstyle=INFO,
               command=lambda: (load_data(month_var.get()), load_logs()), padding=10
               ).pack(side=LEFT, padx=5)
    ttk.Button(controls, text=tr(MSG_VIEW_ALL_INVOICES), bootstyle=SECONDARY,
               command=lambda: show_all_invoices(fin), padding=10
               ).pack(side=LEFT, padx=5)
    
    maintenance_btn = ttk.Button(controls, text=tr(MSG_FIX_ADMIN_RECORDS), bootstyle=WARNING,
               command=fix_admin_records, padding=10)
    maintenance_btn.pack(side=LEFT, padx=5)
    ttk.Button(
        controls, text=tr(MSG_BACK_HOME), bootstyle=DANGER, padding=10,
        command=fin.destroy
    ).pack(side=RIGHT, padx=10)

    # — summary strip ---------------------------------------------------------
    sumfr = ttk.Frame(fin, padding=20); sumfr.pack(fill=X)
    
    # Create custom styled frames for metrics
    metric_style = ttk.Style()
    metric_style.configure("Metric.TFrame", background="#3E3E3E", relief="raised", borderwidth=1)
    
    metric1 = ttk.Frame(sumfr, style="Metric.TFrame", padding=15)
    metric1.pack(side=LEFT, padx=10, expand=True, fill=X)
    ttk.Label(metric1, text=tr(MSG_TOTAL_SALES), font=("Helvetica", 16)).pack(anchor="center")
    total_lbl = ttk.Label(metric1, text="$0.00", font=("Helvetica", 22, "bold"))
    total_lbl.pack(anchor="center", pady=5)
    
    metric2 = ttk.Frame(sumfr, style="Metric.TFrame", padding=15)
    metric2.pack(side=LEFT, padx=10, expand=True, fill=X)
    ttk.Label(metric2, text=tr(MSG_OUTSTANDING_DEBITS), font=("Helvetica", 16)).pack(anchor="center")
    debit_lbl = ttk.Label(metric2, text="$0.00", font=("Helvetica", 22, "bold"), bootstyle=WARNING)
    debit_lbl.pack(anchor="center", pady=5)
    
    metric3 = ttk.Frame(sumfr, style="Metric.TFrame", padding=15)
    metric3.pack(side=LEFT, padx=10, expand=True, fill=X)
    ttk.Label(metric3, text=tr(MSG_PROFIT), font=("Helvetica", 16)).pack(anchor="center")
    profit_lbl = ttk.Label(metric3, text="$0.00", font=("Helvetica", 22, "bold"), bootstyle=SUCCESS)
    profit_lbl.pack(anchor="center", pady=5)
    
    metric4 = ttk.Frame(sumfr, style="Metric.TFrame", padding=15)
    metric4.pack(side=LEFT, padx=10, expand=True, fill=X)
    ttk.Label(metric4, text=tr(MSG_LOSSES), font=("Helvetica", 16)).pack(anchor="center")
    loss_lbl = ttk.Label(metric4, text="$0.00", font=("Helvetica", 22, "bold"), bootstyle=DANGER)
    loss_lbl.pack(anchor="center", pady=5)

    # Create tabbed interface for sales, users and logs
    notebook = ttk.Notebook(fin)
    notebook.pack(fill=BOTH, expand=True, padx=20, pady=20)
    
    # Tab 1: Sales by User
    sales_tab = ttk.Frame(notebook, padding=10)
    notebook.add(sales_tab, text=tr(MSG_SALES_BY_USER))

    # — sales by user table ---------------------------------------------------
    ttk.Label(sales_tab, text=tr(MSG_SALES_BY_USER), font=("Helvetica", 20, "bold")).pack(pady=10)
    
    # Create custom style for sales table
    style = ttk.Style()
    style.configure("Financial.Treeview",
                   background="#3E3E3E",
                   foreground="white",
                   rowheight=30,
                   fieldbackground="#3E3E3E",
                   font=("Helvetica", 14))
    style.configure("Financial.Treeview.Heading",
                  background="#2B2B2B",
                  foreground="white",
                  font=("Helvetica", 16, "bold"))
    style.map("Financial.Treeview",
             background=[("selected", "#4A6984")],
             foreground=[("selected", "white")])
    
    sales_frame = ttk.Frame(sales_tab)
    sales_frame.pack(fill=BOTH, expand=True)
    sales_tbl = ttk.Treeview(
        sales_frame,
        columns=("User", "Total", "Count"),
        show="headings",
        style="Financial.Treeview"
    )
    sales_tbl.heading("User", text=tr(MSG_USER))   
    sales_tbl.heading("Total", text=tr(MSG_TOTAL))
    sales_tbl.heading("Count", text=tr(MSG_COUNT))
    
    sales_tbl.column("User", width=300, anchor=W)
    sales_tbl.column("Total", width=150, anchor=E)
    sales_tbl.column("Count", width=100, anchor=E)
    
    sales_tbl.tag_configure("evenrow", background="#4A4A4A", foreground="white")
    sales_tbl.tag_configure("oddrow", background="#3A3A3A", foreground="white")
    
    sales_tbl.pack(side=LEFT, fill=BOTH, expand=True)
    sales_scrollbar = ttk.Scrollbar(sales_frame, orient="vertical", command=sales_tbl.yview)
    sales_scrollbar.pack(side=LEFT, fill=Y)
    sales_tbl.configure(yscrollcommand=sales_scrollbar.set)
    
    # Tab 2: Users & Activity
    users_tab = ttk.Frame(notebook, padding=10)
    notebook.add(users_tab, text=tr(MSG_USERS_ACTIVITY))

    # — users list ------------------------------------------------------------
    ttk.Label(users_tab, text=tr(MSG_SELECT_USER), font=("Helvetica", 20, "bold")).pack(pady=10)
    
    users_frame = ttk.Frame(users_tab)
    users_frame.pack(fill=BOTH, expand=True)
    
    uid_map = {}  # Store user ID mapping for later use
    
    # Create treeview
    users_tbl = ttk.Treeview(
        users_frame,
        columns=("User", "Role"),
        show="headings",
        style="Financial.Treeview"
    )
    users_tbl.heading("User", text=tr(MSG_USER))
    users_tbl.heading("Role", text=tr("Role"))
    
    users_tbl.column("User", width=300, anchor=W)
    users_tbl.column("Role", width=150, anchor=W)
    
    users_tbl.tag_configure("evenrow", background="#4A4A4A", foreground="white")
    users_tbl.tag_configure("oddrow", background="#3A3A3A", foreground="white")
    
    # Fetch users
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT UserID, Username, Role FROM Users ORDER BY Role, Username")
        for i, (uid, uname, role) in enumerate(cur.fetchall()):
            uid_map[uname] = uid
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            users_tbl.insert("", END, values=(uname, role), tags=(tag,))
        return_connection(conn)
    except Exception as e:
        messagebox.showerror(tr(MSG_ERROR), f"{tr(MSG_ERROR_LOADING_DATA)}: {str(e)}", parent=fin)
    
    users_tbl.pack(side=LEFT, fill=BOTH, expand=True)
    users_scrollbar = ttk.Scrollbar(users_frame, orient="vertical", command=users_tbl.yview)
    users_scrollbar.pack(side=LEFT, fill=Y)
    users_tbl.configure(yscrollcommand=users_scrollbar.set)
    
    # Action buttons
    btns = ttk.Frame(users_tab, padding=10)
    btns.pack(pady=20)
    
    ttk.Button(btns, text=tr(MSG_VIEW_SALES), bootstyle=PRIMARY, padding=10,
               command=view_user_sales).pack(pady=10, fill=X)
               
    def view_logs():
        u = selected_user()
        if not u: 
            messagebox.showwarning(tr(MSG_WARNING), tr(MSG_PLEASE_SELECT_USER), parent=fin)
            return
        uid = uid_map[u]
        win = Toplevel(fin)
        win.title(f"{tr(MSG_ACTIVITY_LOG_FOR)} {u}")
        win.geometry("900x600")
        
        # Add header 
        header = ttk.Frame(win, padding=10)
        header.pack(fill=X)
        ttk.Label(header, text=f"{tr(MSG_ACTIVITY_LOG_FOR)} {u}", font=("Helvetica", 20, "bold")).pack(side=LEFT)
        ttk.Button(header, text=tr(MSG_CLOSE), bootstyle=SECONDARY, command=win.destroy, padding=5).pack(side=RIGHT)
        
        # Create activity log treeview with custom style
        activity_frame = ttk.Frame(win, padding=10)
        activity_frame.pack(fill=BOTH, expand=True)
        
        tv = ttk.Treeview(
            activity_frame, 
            columns=("Action", "DateTime"), 
            show="headings", 
            style="Financial.Treeview"
        )
        tv.heading("Action", text=tr(MSG_ACTION))
        tv.heading("DateTime", text=tr(MSG_DATE_TIME))
        tv.column("Action", width=600)
        tv.column("DateTime", width=200)
        tv.tag_configure("evenrow", background="#4A4A4A", foreground="white")
        tv.tag_configure("oddrow", background="#3A3A3A", foreground="white")
        
        tv.pack(side=LEFT, fill=BOTH, expand=True)
        vsb = ttk.Scrollbar(activity_frame, orient="vertical", command=tv.yview)
        vsb.pack(side=LEFT, fill=Y)
        tv.configure(yscrollcommand=vsb.set)
        
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""SELECT Action, DateTime FROM ActivityLog
                           WHERE UserID=? ORDER BY DateTime DESC""", (uid,))
            for i, (a, dt) in enumerate(cur.fetchall()):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                tv.insert("", END, values=(a, dt), tags=(tag,))
            return_connection(conn)
        except Exception as e:
            messagebox.showerror(tr(MSG_ERROR), f"{tr(MSG_ERROR_LOADING_LOGS)}: {str(e)}", parent=win)
            
    ttk.Button(btns, text=tr(MSG_USER_ACTIVITY_LOG), bootstyle=SECONDARY, padding=10,
               command=view_logs).pack(pady=10, fill=X)
    
    # Tab 3: Recent Activity Logs           
    logs_tab = ttk.Frame(notebook, padding=10)
    notebook.add(logs_tab, text=tr(MSG_RECENT_ACTIVITY))

    # — recent logs -----------------------------------------------------------
    ttk.Label(logs_tab, text=tr(MSG_RECENT_ACTIVITY), font=("Helvetica", 20, "bold")).pack(pady=10)
    logs_frame = ttk.Frame(logs_tab)
    logs_frame.pack(fill=BOTH, expand=True)
    
    logs_tbl = ttk.Treeview(
        logs_frame, 
        columns=("User", "Action", "DateTime"),
        show="headings", 
        style="Financial.Treeview"
    )
    logs_tbl.heading("User", text=tr(MSG_USER))
    logs_tbl.heading("Action", text=tr(MSG_ACTION))
    logs_tbl.heading("DateTime", text=tr(MSG_DATE_TIME))
    
    logs_tbl.column("User", width=150, anchor=W)
    logs_tbl.column("Action", width=600, anchor=W)
    logs_tbl.column("DateTime", width=150, anchor=W)
    
    logs_tbl.tag_configure("evenrow", background="#4A4A4A", foreground="white")
    logs_tbl.tag_configure("oddrow", background="#3A3A3A", foreground="white")
    
    logs_tbl.pack(side=LEFT, fill=BOTH, expand=True)
    logs_scrollbar = ttk.Scrollbar(logs_frame, orient="vertical", command=logs_tbl.yview)
    logs_scrollbar.pack(side=LEFT, fill=Y)
    logs_tbl.configure(yscrollcommand=logs_scrollbar.set)

    # initial data
    load_data(tr(MSG_ALL)); load_logs()
    
    # Clean up when window is destroyed
    fin.bind("<Destroy>", lambda e: unregister_refresh_callback(refresh_language) if e.widget == fin else None)



