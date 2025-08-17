# modules/Login.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import Toplevel, StringVar, BOTH, messagebox, PhotoImage
import bcrypt
import os
import time
from modules.db_manager import get_connection, return_connection

# holds the active user after a successful login
current_user: dict = {}


class LoginWindow(Toplevel):
    """Modern login / account-creation window with improved UI."""
    # ------------------------------------------------------------------
    def __init__(self, master):
        super().__init__(master)
        self.title("Login - Sales Management System")
        self.geometry("800x650")  # Increased height to prevent cutoff
        self.resizable(False, False)
        self.grab_set()  # make modal
        
        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        # Set app icon if available
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            try:
                icon = PhotoImage(file=icon_path)
                self.iconphoto(True, icon)
                self.icon = icon  # Keep reference
            except Exception:
                pass
        
        # Create styles first so they're available during UI building
        self._create_styles()
        self._build_ui()
        
        # Setup key bindings
        self.bind("<Return>", lambda e: self._do_login())
        self.bind("<Escape>", lambda e: self.destroy())
        
        # Set focus to username entry after a brief delay
        self.after(100, lambda: self.username_entry.focus_set())

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Main container with two frames side by side
        container = ttk.Frame(self, style="Dark.TFrame")
        container.pack(fill=BOTH, expand=True)
        
        # Left panel - Logo/brand area
        left_panel = ttk.Frame(container, style="leftp.TFrame", width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH)
        
        # Keep left panel fixed width
        left_panel.pack_propagate(False)
        
        # Logo/Brand area in left panel
        logo_frame = ttk.Frame(left_panel, style="leftp.TFrame")
        logo_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # App title with each word on its own line
        ttk.Label(
            logo_frame, 
            text="SALES",
            font=("Arial", 28, "bold"),
            style="logo.TLabel"
        ).pack(pady=(80, 5))
        
        ttk.Label(
            logo_frame, 
            text="MANAGEMENT",
            font=("Arial", 28, "bold"),
            style="logo.TLabel"
        ).pack(pady=5)
        
        ttk.Label(
            logo_frame, 
            text="SYSTEM",
            font=("Arial", 28, "bold"),
            style="logo.TLabel"
        ).pack(pady=5)
        
        ttk.Label(
            logo_frame,
            text="Inventory • Sales • Financial",
            font=("Arial", 12),
            style="logo.TLabel"
        ).pack(pady=(20, 0))
        
        ttk.Label(
            logo_frame,
            text="v3.0",
            font=("Arial", 10),
            style="logo.TLabel"
        ).pack(pady=(80, 0))
        
        # Right panel - Login form
        right_panel = ttk.Frame(container, padding=40, style="Dark.TFrame")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Welcome message
        ttk.Label(
            right_panel, 
            text="Welcome Back",
            font=("Arial", 24, "bold"),
            style="Header.TLabel"
        ).pack(anchor=tk.W, pady=(20, 10))
        
        ttk.Label(
            right_panel,
            text="Please login to your account",
            font=("Arial", 12),
            style="Subtitle.TLabel"
        ).pack(anchor=tk.W, pady=(0, 30))
        
        # Login form
        form = ttk.Frame(right_panel, style="Dark.TFrame")
        form.pack(fill=tk.BOTH, expand=True)
        
        # Username field
        ttk.Label(
            form, 
            text="USERNAME",
            font=("Arial", 10, "bold"),
            style="FormLabel.TLabel"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.username = StringVar()
        self.username_entry = ttk.Entry(
            form, 
            textvariable=self.username,
            font=("Arial", 14),
            width=30,
            style="Glow.TEntry"
        )
        self.username_entry.pack(anchor=tk.W, pady=(0, 20), ipady=5, fill=tk.X)
        
        # Password field
        ttk.Label(
            form, 
            text="PASSWORD",
            font=("Arial", 10, "bold"),
            style="FormLabel.TLabel"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.password = StringVar()
        self.password_entry = ttk.Entry(
            form, 
            textvariable=self.password, 
            show="•",
            font=("Arial", 14),
            width=30,
            style="Glow.TEntry"
        )
        self.password_entry.pack(anchor=tk.W, pady=(0, 30), ipady=5, fill=tk.X)
        
        # Remember me and forgot password row
        options_frame = ttk.Frame(form, style="Dark.TFrame")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.remember_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Remember me",
            variable=self.remember_var,
            style="Dark.TCheckbutton"
        ).pack(side=tk.LEFT)
        
        # Login button and status indicator
        button_frame = ttk.Frame(form, style="Dark.TFrame")
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status indicator for login feedback
        self.status_var = StringVar()
        self.status_label = ttk.Label(
            button_frame,
            textvariable=self.status_var,
            foreground="#D32F2F",
            font=("Arial", 10),
            style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT, pady=(5, 0))
        
        # Login button
        self.login_button = ttk.Button(
            button_frame, 
            text="LOG IN",
            style="Glow.TButton",
            command=self._do_login,
            width=15
        )
        self.login_button.pack(side=tk.RIGHT)
        
        # Create account link at the bottom
        create_account_container = ttk.Frame(right_panel, padding=20, style="Dark.TFrame")
        create_account_container.pack(side=tk.TOP, fill=tk.X, expand=False)
        
        create_account_text = ttk.Label(
            create_account_container, 
            text="Don't have an account?", 
            style="Subtitle.TLabel"
        )
        create_account_text.pack(side=tk.LEFT, padx=(0, 5))
        
        create_account_link = ttk.Label(
            create_account_container, 
            text="Create account", 
            style="LinkButton.TLabel"
        )
        create_account_link.pack(side=tk.LEFT)
        create_account_link.bind("<Button-1>", self._open_create_account_window)
        
        # Add hover effect for create account link
        create_account_link.bind("<Enter>", lambda e: create_account_link.configure(foreground="#567BFF"))
        create_account_link.bind("<Leave>", lambda e: create_account_link.configure(foreground="#3454D1"))

    # ------------------------------------------------------------------
    def _create_styles(self):
        # Get the style object
        s = ttk.Style()
        
        # Dark theme base styles
        s.configure("Dark.TFrame", background="#1E1E1E")
        
        # Configure custom styles
        s.configure("leftp.TFrame", background="#3454D1")  # Left panel background
        s.configure("logo.TLabel", background="#3454D1", foreground="white", justify="center")
        
        s.configure("FormLabel.TLabel", background="#1E1E1E", foreground="#AAAAAA", font=("Arial", 10, "bold"))
        s.configure("Subtitle.TLabel", background="#1E1E1E", foreground="#AAAAAA", font=("Arial", 12))
        s.configure("LinkButton.TLabel", background="#1E1E1E", foreground="#3454D1", font=("Arial", 10, "bold"), cursor="hand2")
        s.configure("Header.TLabel", background="#1E1E1E", font=("Arial", 24, "bold"), foreground="#FFFFFF")
        s.configure("Status.TLabel", background="#1E1E1E", foreground="#D32F2F", font=("Arial", 10))
        
        # Custom entry field style with subtle glow outline
        s.configure("Glow.TEntry", padding=10, relief=tk.FLAT, fieldbackground="#252525", foreground="#FFFFFF", bordercolor="#333333")
        s.map("Glow.TEntry", 
              bordercolor=[("focus", "#3454D1"), ("hover", "#3454D1")],
              lightcolor=[("focus", "#3454D1"), ("hover", "#3454D1")],
              darkcolor=[("focus", "#3454D1"), ("hover", "#3454D1")])
        
        # Custom button style with subtle glow outline
        s.configure("Glow.TButton", font=("Arial", 12, "bold"), padding=10, background="#2D8C46", foreground="#FFFFFF")
        s.map("Glow.TButton", 
              background=[("active", "#2D8C46"), ("hover", "#2D8C46")],
              foreground=[("active", "#FFFFFF"), ("hover", "#FFFFFF")],
              bordercolor=[("focus", "#4CAF50"), ("hover", "#4CAF50")],
              lightcolor=[("focus", "#4CAF50"), ("hover", "#4CAF50")],
              darkcolor=[("focus", "#4CAF50"), ("hover", "#4CAF50")])
              
        # Dark checkbutton style
        s.configure("Dark.TCheckbutton", background="#1E1E1E", foreground="#AAAAAA")

    # ------------------------------------------------------------------
    def _loading_animation(self, is_loading=True):
        """Show loading state during login"""
        if is_loading:
            self.login_button.configure(text="LOGGING IN...", state="disabled")
            self.username_entry.configure(state="disabled")
            self.password_entry.configure(state="disabled")
            self.status_var.set("")
            self.update()
        else:
            self.login_button.configure(text="LOG IN", state="normal")
            self.username_entry.configure(state="normal")
            self.password_entry.configure(state="normal")
            self.update()

    # ------------------------------------------------------------------
    def _do_login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()

        if not user or not pwd:
            self.status_var.set("Please enter both username and password")
            if not user:
                self.username_entry.focus_set()
            else:
                self.password_entry.focus_set()
            return

        # Show loading animation
        self._loading_animation(True)
        
        # Small delay to show animation
        self.after(300, lambda: self._perform_login(user, pwd))

    # ------------------------------------------------------------------
    def _perform_login(self, user, pwd):
        """Actual login logic, separated to allow for animation"""
        # fetch user row
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT UserID, Password, Role "
                        "FROM Users WHERE Username = ?", (user,))
            row = cur.fetchone()
            return_connection(conn)
        except Exception as e:
            self._loading_animation(False)
            self.status_var.set(f"Database error: {e}")
            return

        if not row:
            self._loading_animation(False)
            self.status_var.set("Invalid username or password")
            return

        user_id, stored_pw, role = row
        role = (role or "").strip().lower()  # <-- fix: remove spaces then lower‑case

        # 1) bcrypt check; 2) fallback to plain text (legacy)
        ok = False
        try:
            ok = bcrypt.checkpw(pwd.encode(), stored_pw.encode())
        except Exception:
            pass
        if not ok:
            ok = pwd == stored_pw

        if not ok:
            self._loading_animation(False)
            self.status_var.set("Invalid username or password")
            return

        # ---- success ----
        current_user.clear()
        current_user.update({
            "UserID": user_id,
            "Username": user,
            "Role": role
        })
        
        # Add a small delay for animation
        self.after(300, self.destroy)

    # ------------------------------------------------------------------
    def _open_create_account_window(self, event):
        CreateAccountWindow(self)  # modal by default


########################################################################
#  Create‑account window                                               #
########################################################################
class CreateAccountWindow(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Create Account - Sales Management System")
        self.geometry("800x650")  # Match login window size
        self.resizable(False, False)
        self.grab_set()
        
        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create styles first
        self._create_styles()
        self._build_ui()
        
        # Setup key bindings
        self.bind("<Return>", lambda e: self._create())
        self.bind("<Escape>", lambda e: self.destroy())
        
        # Set focus to username entry
        self.after(100, lambda: self.new_user_entry.focus_set())

    # ------------------------------------------------------------------
    def _create_styles(self):
        """Create styles for the create account window"""
        s = ttk.Style()
        
        # Dark theme base styles
        s.configure("Dark.TFrame", background="#1E1E1E")
        
        s.configure("FormLabel.TLabel", background="#1E1E1E", foreground="#AAAAAA", font=("Arial", 10, "bold"))
        s.configure("Subtitle.TLabel", background="#1E1E1E", foreground="#AAAAAA", font=("Arial", 12))
        s.configure("Status.TLabel", background="#1E1E1E", foreground="#D32F2F", font=("Arial", 10))
        s.configure("Header.TLabel", background="#1E1E1E", font=("Arial", 24, "bold"), foreground="#FFFFFF")
        
        # Entry field with subtle glow outline
        s.configure("Glow.TEntry", padding=10, relief=tk.FLAT, fieldbackground="#252525", foreground="#FFFFFF", bordercolor="#333333")
        s.map("Glow.TEntry", 
              bordercolor=[("focus", "#3454D1"), ("hover", "#3454D1")],
              lightcolor=[("focus", "#3454D1"), ("hover", "#3454D1")],
              darkcolor=[("focus", "#3454D1"), ("hover", "#3454D1")])
        
        # Button styles with subtle glow outline
        s.configure("secondary.Outline.TButton", font=("Arial", 11), background="#333333", foreground="#FFFFFF")
        s.map("secondary.Outline.TButton",
              background=[("active", "#333333"), ("hover", "#333333")],
              foreground=[("active", "#FFFFFF"), ("hover", "#FFFFFF")],
              bordercolor=[("focus", "#555555"), ("hover", "#555555")],
              lightcolor=[("focus", "#555555"), ("hover", "#555555")],
              darkcolor=[("focus", "#555555"), ("hover", "#555555")])
              
        s.configure("Glow.TButton", font=("Arial", 12, "bold"), padding=10, background="#2D8C46", foreground="#FFFFFF")
        s.map("Glow.TButton", 
              background=[("active", "#2D8C46"), ("hover", "#2D8C46")],
              foreground=[("active", "#FFFFFF"), ("hover", "#FFFFFF")],
              bordercolor=[("focus", "#4CAF50"), ("hover", "#4CAF50")],
              lightcolor=[("focus", "#4CAF50"), ("hover", "#4CAF50")],
              darkcolor=[("focus", "#4CAF50"), ("hover", "#4CAF50")])

    # ------------------------------------------------------------------
    def _build_ui(self):
        container = ttk.Frame(self, padding=40, style="Dark.TFrame")
        container.pack(fill=BOTH, expand=True)
        
        # Header
        ttk.Label(
            container, 
            text="Create New Account",
            font=("Arial", 24, "bold"),
            style="Header.TLabel"
        ).pack(anchor=tk.W, pady=(20, 10))
        
        ttk.Label(
            container,
            text="Fill in the details to create a new user account",
            font=("Arial", 12),
            style="Subtitle.TLabel"
        ).pack(anchor=tk.W, pady=(0, 30))
        
        # Form
        form = ttk.Frame(container, style="Dark.TFrame")
        form.pack(fill=tk.BOTH, expand=True)
        
        # Username field
        ttk.Label(
            form, 
            text="NEW USERNAME",
            font=("Arial", 10, "bold"),
            style="FormLabel.TLabel"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.new_user = StringVar()
        self.new_user_entry = ttk.Entry(
            form, 
            textvariable=self.new_user,
            font=("Arial", 14),
            width=30,
            style="Glow.TEntry"
        )
        self.new_user_entry.pack(anchor=tk.W, pady=(0, 20), ipady=5, fill=tk.X)
        
        # Password field
        ttk.Label(
            form, 
            text="NEW PASSWORD",
            font=("Arial", 10, "bold"),
            style="FormLabel.TLabel"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.new_pwd = StringVar()
        self.new_pwd_entry = ttk.Entry(
            form, 
            textvariable=self.new_pwd, 
            show="•",
            font=("Arial", 14),
            width=30,
            style="Glow.TEntry"
        )
        self.new_pwd_entry.pack(anchor=tk.W, pady=(0, 20), ipady=5, fill=tk.X)
        
        # Role selection
        ttk.Label(
            form, 
            text="USER ROLE",
            font=("Arial", 10, "bold"),
            style="FormLabel.TLabel"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        role_frame = ttk.Frame(form, style="Dark.TFrame")
        role_frame.pack(anchor=tk.W, pady=(0, 30), fill=tk.X)
        
        self.role = StringVar(value="shift")
        
        ttk.Radiobutton(
            role_frame,
            text="Shift Employee",
            value="shift",
            variable=self.role,
            style="Dark.TRadiobutton"
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Radiobutton(
            role_frame,
            text="Administrator",
            value="admin",
            variable=self.role,
            style="Dark.TRadiobutton"
        ).pack(side=tk.LEFT)
        
        # Status and button
        status_frame = ttk.Frame(form, style="Dark.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_var = StringVar()
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            foreground="#D32F2F",
            font=("Arial", 10),
            style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT, pady=(5, 0))
        
        button_frame = ttk.Frame(form, style="Dark.TFrame")
        button_frame.pack(fill=tk.X, pady=(10, 20))
        
        # Back button
        ttk.Button(
            button_frame,
            text="BACK TO LOGIN",
            style="secondary.Outline.TButton",
            command=self.destroy,
            width=15
        ).pack(side=tk.LEFT)
        
        # Create button
        self.create_button = ttk.Button(
            button_frame, 
            text="CREATE ACCOUNT",
            style="Glow.TButton",
            command=self._create,
            width=20
        )
        self.create_button.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    def _loading_animation(self, is_loading=True):
        """Show loading state during account creation"""
        if is_loading:
            self.create_button.configure(text="CREATING...", state="disabled")
            self.new_user_entry.configure(state="disabled")
            self.new_pwd_entry.configure(state="disabled")
            self.status_var.set("")
            self.update()
        else:
            self.create_button.configure(text="CREATE ACCOUNT", state="normal")
            self.new_user_entry.configure(state="normal")
            self.new_pwd_entry.configure(state="normal")
            self.update()

    # ------------------------------------------------------------------
    def _create(self):
        """Create a new user account"""
        u, p, r = self.new_user.get().strip(), self.new_pwd.get().strip(), \
                  self.role.get().strip().lower()
                  
        if not u or not p:
            self.status_var.set("Please fill in all fields")
            if not u:
                self.new_user_entry.focus_set()
            else:
                self.new_pwd_entry.focus_set()
            return
            
        # Minimum password length
        if len(p) < 4:
            self.status_var.set("Password must be at least 4 characters long")
            self.new_pwd_entry.focus_set()
            return
            
        # Show loading animation
        self._loading_animation(True)
        
        # Small delay to show animation
        self.after(300, lambda: self._perform_create(u, p, r))
        
    # ------------------------------------------------------------------
    def _perform_create(self, u, p, r):
        """Actual account creation logic"""
        try:
            from modules.db_manager import ConnectionContext
            hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
            
            with ConnectionContext() as conn:
                cur = conn.cursor()
                
                # Check if username already exists
                cur.execute("SELECT 1 FROM Users WHERE Username = ?", (u,))
                if cur.fetchone():
                    self._loading_animation(False)
                    self.status_var.set(f"Username '{u}' already exists")
                    return
                
                cur.execute("INSERT INTO Users (Username, Password, Role) "
                            "VALUES (?, ?, ?)", (u, hashed, r))
                conn.commit()
            
            # Success - add a delay for animation
            self.after(300, lambda: self._show_success(u, r))
            
        except Exception as e:
            self._loading_animation(False)
            self.status_var.set(f"Error: {e}")
            
    # ------------------------------------------------------------------
    def _show_success(self, username, role):
        """Show success message and close window"""
        messagebox.showinfo("Account Created",
                            f"Account '{username}' created with role '{role}'.",
                            parent=self)
        self.destroy()











