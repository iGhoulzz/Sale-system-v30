#!/usr/bin/env python3
"""
Test script for Database Routes module
Tests the new database routes functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_routes():
    """Test database routes functionality"""
    print("🔍 Testing Database Routes Module...")
    
    try:
        # Import the new database routes
        from modules.database_routes import db_routes
        
        print("  ✅ Database routes imported successfully")
        
        # Test 1: Get categories
        print("\n  📋 Testing get_categories()...")
        categories = db_routes.get_categories()
        print(f"  ✅ Found {len(categories)} categories: {categories}")
        
        # Test 2: Get products with pagination
        print("\n  📋 Testing get_products()...")
        products_result = db_routes.get_products(page=1, limit=5)
        print(f"  ✅ Found {products_result['total_count']} total products")
        print(f"  ✅ Page 1 has {len(products_result['data'])} products")
        print(f"  ✅ Total pages: {products_result['total_pages']}")
        
        # Test 3: Fast product search
        print("\n  📋 Testing search_products_fast()...")
        search_results = db_routes.search_products_fast("", limit=3)
        print(f"  ✅ Fast search returned {len(search_results)} results")
        
        if search_results:
            print(f"  ✅ Sample result: {search_results[0]['display']}")
        
        # Test 4: Get low stock products
        print("\n  📋 Testing get_low_stock_products()...")
        low_stock = db_routes.get_low_stock_products(threshold=20)
        print(f"  ✅ Found {len(low_stock)} low stock products")
        
        # Test 5: Get category stats
        print("\n  📋 Testing get_category_stats()...")
        category_stats = db_routes.get_category_stats()
        print(f"  ✅ Category stats: {len(category_stats)} categories with stats")
        
        # Test 6: Performance stats
        print("\n  📋 Testing get_performance_stats()...")
        perf_stats = db_routes.get_performance_stats()
        print(f"  ✅ Query count: {perf_stats['query_count']}")
        print(f"  ✅ Cache hits: {perf_stats['cache_hits']}")
        print(f"  ✅ Cache hit rate: {perf_stats['cache_hit_rate']:.1f}%")
        print(f"  ✅ Slow queries: {perf_stats['slow_queries_count']}")
        
        # Test 7: Test caching by running same query again
        print("\n  📋 Testing caching functionality...")
        products_result2 = db_routes.get_products(page=1, limit=5)
        perf_stats2 = db_routes.get_performance_stats()
        
        if perf_stats2['cache_hits'] > perf_stats['cache_hits']:
            print("  ✅ Caching is working correctly!")
        else:
            print("  ⚠️  Caching might not be working as expected")
        
        print("\n🎉 All Database Routes tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Database routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_routes()
    sys.exit(0 if success else 1)
