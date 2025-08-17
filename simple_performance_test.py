#!/usr/bin/env python3
"""
Enhanced Inventory Performance Quick Test
Focuses on key performance metrics with better error handling
"""

import sys
import os
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_performance():
    """Test basic performance metrics"""
    print("ENHANCED INVENTORY PERFORMANCE TEST")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        performance_results = {}
        
        # Test 1: Data Loading Performance
        print("1. Data Loading Performance...")
        start = time.time()
        products = enhanced_data.get_products()
        products_time = (time.time() - start) * 1000
        
        start = time.time()
        categories = enhanced_data.get_categories()
        categories_time = (time.time() - start) * 1000
        
        start = time.time()
        paged = enhanced_data.get_products_paged(page=1, page_size=5)
        pagination_time = (time.time() - start) * 1000
        
        print(f"   Products ({len(products)}): {products_time:.2f}ms")
        print(f"   Categories ({len(categories)}): {categories_time:.2f}ms")
        print(f"   Pagination: {pagination_time:.2f}ms")
        
        performance_results['data_loading'] = {
            'products_time': products_time,
            'products_count': len(products),
            'categories_time': categories_time,
            'pagination_time': pagination_time
        }
        
        # Test 2: Single CRUD Operation Performance
        print("\n2. CRUD Operations Performance...")
        
        # Add product
        test_product = {
            'name': f'Perf Test {int(time.time())}',
            'category': 'Performance',
            'buy_price': 15.99,
            'sell_price': 25.99,
            'stock': 10,
            'barcode': f'PERF{int(time.time())}'
        }
        
        start = time.time()
        add_result = enhanced_data.add_product(test_product)
        add_time = (time.time() - start) * 1000
        print(f"   Add Product: {add_time:.2f}ms ({'SUCCESS' if add_result else 'FAILED'})")
        
        performance_results['crud'] = {
            'add_time': add_time,
            'add_success': add_result
        }
        
        # Test 3: Search Performance
        print("\n3. Search Performance...")
        start = time.time()
        search_results = enhanced_data.search_products_fast("test", limit=5)
        search_time = (time.time() - start) * 1000
        print(f"   Search: {search_time:.2f}ms ({len(search_results)} results)")
        
        performance_results['search_time'] = search_time
        
        return performance_results
        
    except Exception as e:
        print(f"   ERROR: {e}")
        traceback.print_exc()
        return None

def analyze_performance(results):
    """Analyze performance results"""
    print("\n" + "=" * 50)
    print("PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    if not results:
        print("No performance data available")
        return False
    
    score = 100
    issues = []
    
    # Analyze data loading
    if 'data_loading' in results:
        data = results['data_loading']
        
        print(f"Data Loading Analysis:")
        print(f"  Products: {data['products_count']} items in {data['products_time']:.2f}ms")
        
        if data['products_time'] > 500:
            score -= 20
            issues.append("Slow product loading (>500ms)")
        elif data['products_time'] > 100:
            score -= 10
            issues.append("Moderate product loading delay (>100ms)")
        else:
            print(f"  Rating: EXCELLENT (< 100ms)")
        
        if data['categories_time'] > 100:
            score -= 10
            issues.append("Slow category loading")
        
        if data['pagination_time'] > 50:
            score -= 10
            issues.append("Slow pagination")
        
        # Calculate throughput
        throughput = data['products_count'] / (data['products_time'] / 1000)
        print(f"  Throughput: {throughput:.2f} products/second")
    
    # Analyze CRUD operations
    if 'crud' in results:
        crud = results['crud']
        print(f"\nCRUD Analysis:")
        print(f"  Add Product: {crud['add_time']:.2f}ms")
        
        if not crud['add_success']:
            score -= 30
            issues.append("CRUD operations failing")
        elif crud['add_time'] > 100:
            score -= 15
            issues.append("Slow CRUD operations (>100ms)")
        elif crud['add_time'] > 50:
            score -= 5
            issues.append("Moderate CRUD delay (>50ms)")
        else:
            print(f"  Rating: EXCELLENT (< 50ms)")
    
    # Analyze search
    if 'search_time' in results:
        print(f"\nSearch Analysis:")
        print(f"  Search Time: {results['search_time']:.2f}ms")
        
        if results['search_time'] > 200:
            score -= 15
            issues.append("Slow search performance")
        elif results['search_time'] > 100:
            score -= 5
            issues.append("Moderate search delay")
    
    # Overall assessment
    print(f"\n" + "=" * 50)
    print(f"PERFORMANCE SCORE: {score}/100")
    
    if score >= 90:
        rating = "EXCELLENT"
        status = "Production-ready with optimal performance"
    elif score >= 75:
        rating = "GOOD"
        status = "Production-ready with acceptable performance"
    elif score >= 60:
        rating = "FAIR"
        status = "Acceptable for small-scale use"
    else:
        rating = "POOR"
        status = "Needs optimization before production use"
    
    print(f"OVERALL RATING: {rating}")
    print(f"STATUS: {status}")
    
    if issues:
        print(f"\nISSUES IDENTIFIED:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\nNo performance issues identified!")
    
    # Specific recommendations
    print(f"\nRECOMMENDations:")
    if score >= 90:
        print("  - Performance is excellent for production use")
        print("  - Can handle multiple concurrent users efficiently")
        print("  - No immediate optimizations needed")
    elif score >= 75:
        print("  - Good performance for typical usage")
        print("  - Monitor performance under high load")
        print("  - Consider caching for frequently accessed data")
    else:
        print("  - Performance optimization recommended")
        print("  - Review database indexes and queries")
        print("  - Consider connection pooling improvements")
        print("  - Test with larger datasets")
    
    return score >= 75

def main():
    """Run performance analysis"""
    print("ENHANCED INVENTORY PAGE BACKEND PERFORMANCE TEST")
    print("=" * 60)
    
    # Run performance tests
    results = test_basic_performance()
    
    # Analyze results
    success = analyze_performance(results)
    
    print(f"\nPerformance Test: {'PASSED' if success else 'NEEDS ATTENTION'}")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
