import sqlite3
from modules.enhanced_data_access import EnhancedDataAccess

# Check Products table structure
conn = sqlite3.connect('sales_system.db')
cursor = conn.cursor()

print("Products table columns:")
cursor.execute('PRAGMA table_info(Products)')
for row in cursor.fetchall():
    print(f'{row[1]}: {row[2]}')

print("\nSample product data:")
cursor.execute('SELECT * FROM Products LIMIT 3')
columns = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

if rows:
    for i, row in enumerate(rows):
        print(f"Product {i+1}: {dict(zip(columns, row))}")
else:
    print("No products found")

print("\nChecking Categories table:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Categories'")
categories_exists = cursor.fetchone() is not None
print(f"Categories table exists: {categories_exists}")

if categories_exists:
    cursor.execute('SELECT * FROM Categories LIMIT 3')
    if cursor.fetchall():
        print("Categories found")
        cursor.execute('SELECT * FROM Categories')
        for row in cursor.fetchall():
            print(f"Category: {row}")

# Test enhanced data access
print("\n" + "="*50)
print("Testing EnhancedDataAccess:")
enhanced_data = EnhancedDataAccess()
products = enhanced_data.get_products(limit=3)
print(f"Products returned by get_products(): {len(products)}")
for i, product in enumerate(products):
    print(f"Product {i+1} keys: {list(product.keys())}")
    print(f"Product {i+1} data: {product}")

categories = enhanced_data.get_categories()
print(f"\nCategories returned: {len(categories)}")
for category in categories:
    print(f"Category: {category}")

conn.close()
