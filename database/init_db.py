# init_db.py
# -----------------------------------------------------------------------------
# Initialise / upgrade the SQLite schema for the Sales‑Management app.
# * NEW: InvoiceItems table now stores BOTH ProductID and ProductName.
# * Added Payments table to track payment transactions for debits.
# * If the DB already exists the script adds the missing column automatically.
# -----------------------------------------------------------------------------
import os, sys, sqlite3
from contextlib import closing

# ------------------------------------------------------------------ paths ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.db_manager import DB_PATH


def create_database() -> None:
    """Create all tables (or upgrade existing ones) so the app can run."""
    print("Starting database initialization...")
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as c:
        print("Connected to database")

        # ------------------------------ PRODUCTS -----------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS Products (
                ProductID     INTEGER PRIMARY KEY AUTOINCREMENT,
                Name          TEXT    NOT NULL,
                SellingPrice  REAL    NOT NULL,
                BuyingPrice   REAL    NOT NULL,
                Stock         INTEGER NOT NULL,
                Category      TEXT    NOT NULL,
                Barcode       TEXT,
                QR_Code       TEXT
            )
        """)

        # ------------------------------ LEGACY SALES -------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS Sales (
                SaleID      INTEGER PRIMARY KEY AUTOINCREMENT,
                Date        TEXT    NOT NULL,
                TotalAmount REAL    NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS SaleItems (
                SaleItemID INTEGER PRIMARY KEY AUTOINCREMENT,
                SaleID     INTEGER NOT NULL,
                ProductID  INTEGER NOT NULL,
                Quantity   INTEGER NOT NULL,
                Price      REAL    NOT NULL,
                FOREIGN KEY (SaleID)    REFERENCES Sales(SaleID),
                FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
            )
        """)

        # ------------------------------ INVOICES -----------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS Invoices (
                InvoiceID     INTEGER PRIMARY KEY AUTOINCREMENT,
                DateTime      TEXT    NOT NULL,
                PaymentMethod TEXT    NOT NULL,
                TotalAmount   REAL    NOT NULL,
                Discount      REAL    NOT NULL,
                ShiftEmployee TEXT
            )
        """)

        # **NEW schema ‑‑ ProductID included**
        c.execute("""
            CREATE TABLE IF NOT EXISTS InvoiceItems (
                InvoiceItemID INTEGER PRIMARY KEY AUTOINCREMENT,
                InvoiceID     INTEGER NOT NULL,
                ProductID     INTEGER,
                ProductName   TEXT    NOT NULL,
                Price         REAL    NOT NULL,
                Quantity      INTEGER NOT NULL,
                FOREIGN KEY (InvoiceID) REFERENCES Invoices(InvoiceID),
                FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
            )
        """)

        # ----- if DB pre‑exists, make sure ProductID column is present ------
        c.execute("PRAGMA table_info(InvoiceItems)")
        existing_cols = {row[1] for row in c.fetchall()}
        if "ProductID" not in existing_cols:
            # SQLite allows adding a nullable column without touching the data
            c.execute("ALTER TABLE InvoiceItems ADD COLUMN ProductID INTEGER")
            print("⟳  Added missing ProductID column to InvoiceItems")

        # ------------------------------ DEBITS -------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS Debits (
                DebitID   INTEGER PRIMARY KEY AUTOINCREMENT,
                Name      TEXT    NOT NULL,
                Phone     TEXT    NOT NULL,
                InvoiceID INTEGER NOT NULL,
                Amount    REAL    NOT NULL,
                AmountPaid REAL,
                Status    TEXT    NOT NULL,
                DateTime  TEXT    NOT NULL,
                Notes     TEXT,
                FOREIGN KEY (InvoiceID) REFERENCES Invoices(InvoiceID)
            )
        """)

        # ----- if DB pre‑exists, make sure AmountPaid column is present in Debits ------
        # First check if the Debits table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Debits'")
        if c.fetchone():
            print("Checking Debits table structure...")
            c.execute("PRAGMA table_info(Debits)")
            existing_cols = {row[1] for row in c.fetchall()}
            print(f"Existing columns in Debits: {', '.join(sorted(existing_cols))}")
            
            if "AmountPaid" not in existing_cols:
                # SQLite allows adding a nullable column without touching the data
                c.execute("ALTER TABLE Debits ADD COLUMN AmountPaid REAL")
                print("⟳  Added missing AmountPaid column to Debits")
            else:
                print("✓ AmountPaid column already exists in Debits")
            
            if "Notes" not in existing_cols:
                c.execute("ALTER TABLE Debits ADD COLUMN Notes TEXT")
                print("⟳  Added missing Notes column to Debits")
            else:
                print("✓ Notes column already exists in Debits")
        else:
            print("Debits table doesn't exist yet, will be created with proper schema")

        # ------------------------------ PAYMENTS ----------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS Payments (
                PaymentID     INTEGER PRIMARY KEY AUTOINCREMENT,
                DebitID       INTEGER NOT NULL,
                Amount        REAL    NOT NULL,
                PaymentMethod TEXT    NOT NULL,
                DateTime      TEXT    NOT NULL,
                RecordedBy    INTEGER,
                Notes         TEXT,
                FOREIGN KEY (DebitID) REFERENCES Debits(DebitID),
                FOREIGN KEY (RecordedBy) REFERENCES Users(UserID)
            )
        """)

        # ------------------------------ USERS -------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                UserID   INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT    NOT NULL UNIQUE,
                Password TEXT    NOT NULL,
                Role     TEXT    NOT NULL
            )
        """)

        # ------------------------------ LOSSES ------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS Losses (
                LossID     INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductID  INTEGER NOT NULL,
                Quantity   INTEGER NOT NULL,
                Reason     TEXT,
                DateTime   TEXT    NOT NULL,
                FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
            )
        """)

        # ------------------------------ ACTIVITY LOG ------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS ActivityLog (
                LogID     INTEGER PRIMARY KEY AUTOINCREMENT,
                UserID    INTEGER NOT NULL,
                Action    TEXT    NOT NULL,
                DateTime  TEXT    NOT NULL,
                FOREIGN KEY (UserID) REFERENCES Users(UserID)
            )
        """)

        # ------------------------------ INDEXES -------------------------------
        # Add index for faster debit queries
        print("Creating indexes...")
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_debits_status_balance
            ON Debits(Status, AmountPaid)
        """)
        print("✅ Index created on Debits(Status, AmountPaid) for better query performance")
        
        # Add indexes for Products table (previously created at runtime in get_products)
        c.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON Products(Category)")
        print("✅ Index created on Products(Category) for faster category filtering")
        
        c.execute("CREATE INDEX IF NOT EXISTS idx_products_stock ON Products(Stock)")
        print("✅ Index created on Products(Stock) for faster stock filtering")
        
        c.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON Products(Barcode)")
        print("✅ Index created on Products(Barcode) for faster barcode lookups")

    print("✅  Database is initialised / up‑to‑date.")


if __name__ == "__main__":
    create_database()



