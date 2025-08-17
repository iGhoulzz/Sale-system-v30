from modules.enhanced_data_access import enhanced_data

products = enhanced_data.get_products()
print('Current products:')
for i, p in enumerate(products[:5]):
    print(f'  {i+1}. ID: {p["id"]}, Name: "{p["name"]}"')
    print(f'     BuyPrice: {p["buy_price"]} ({type(p["buy_price"])})')
    print(f'     SellPrice: {p["sell_price"]} ({type(p["sell_price"])})')
    print(f'     Stock: {p["stock"]}')
    print()
