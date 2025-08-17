from modules.enhanced_data_access import EnhancedDataAccess

print("Testing enhanced data access with fixes...")
enhanced_data = EnhancedDataAccess()

print("\n1. Testing get_products():")
products = enhanced_data.get_products(limit=5)
print(f"   Found {len(products)} products")
for i, product in enumerate(products):
    print(f"   Product {i+1}: {product}")

print("\n2. Testing get_categories():")
categories = enhanced_data.get_categories()
print(f"   Found {len(categories)} categories")
for category in categories:
    print(f"   Category: {category}")

print("\n3. Testing data structure compatibility:")
if products:
    product = products[0]
    required_keys = ['id', 'name', 'sell_price', 'buy_price', 'stock', 'category', 'barcode']
    missing_keys = [key for key in required_keys if key not in product]
    if missing_keys:
        print(f"   Missing keys: {missing_keys}")
    else:
        print("   ✓ All required keys present")
        
        # Test the values that were showing as empty
        print(f"   Product name: '{product['name']}'")
        print(f"   Product category: '{product['category']}'")
        print(f"   Product stock: {product['stock']}")
        print(f"   Product prices: buy=${product['buy_price']}, sell=${product['sell_price']}")
