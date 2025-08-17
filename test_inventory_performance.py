#!/usr/bin/env python3
"""
Enhanced Inventory Page Performance Test
Tests performance metrics for backend operations
"""

import sys
import os
import time
import traceback
from typing import List, Dict

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_data_loading_performance():
    """Test performance of data loading operations"""
    print("PERFORMANCE TEST: DATA LOADING")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        # Test get_products performance
        print("1. Testing get_products() performance...")
        start_time = time.time()
        products = enhanced_data.get_products()
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        print(f"   Result: {len(products)} products loaded in {duration_ms:.2f}ms")
        print(f"   Performance: {len(products)/duration_ms*1000:.2f} products/second")
        
        # Test get_categories performance
        print("2. Testing get_categories() performance...")
        start_time = time.time()
        categories = enhanced_data.get_categories()
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        print(f"   Result: {len(categories)} categories loaded in {duration_ms:.2f}ms")
        
        # Test pagination performance
        print("3. Testing pagination performance...")
        start_time = time.time()
        paged = enhanced_data.get_products_paged(page=1, page_size=10)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        print(f"   Result: Page 1 ({len(paged.data)} items) loaded in {duration_ms:.2f}ms")
        print(f"   Total items: {paged.total_count}, Pages: {paged.total_pages}")
        
        return {
            'products_load_time': (end_time - start_time) * 1000,
            'products_count': len(products),
            'categories_count': len(categories),
            'pagination_time': duration_ms
        }
        
    except Exception as e:
        print(f"   ERROR: {e}")
        traceback.print_exc()
        return None

def test_crud_operations_performance():
    """Test performance of CRUD operations"""
    print("\nPERFORMANCE TEST: CRUD OPERATIONS")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        results = {}
        
        # Test add product performance
        print("1. Testing add_product() performance...")
        timestamp = int(time.time())
        test_product = {
            'name': f'Performance Test Product {timestamp}',
            'category': 'Performance Test',
            'buy_price': 19.99,
            'sell_price': 29.99,
            'stock': 50,
            'barcode': f'PERF{timestamp}'
        }
        
        start_time = time.time()
        add_result = enhanced_data.add_product(test_product)
        end_time = time.time()
        
        add_time_ms = (end_time - start_time) * 1000
        results['add_time'] = add_time_ms
        print(f"   Result: Product added in {add_time_ms:.2f}ms")
        
        if add_result:
            # Find the added product
            products = enhanced_data.get_products()
            added_product = None
            for p in products:
                if p.get('name') == test_product['name']:
                    added_product = p
                    break
            
            if added_product:
                # Test update product performance
                print("2. Testing update_product() performance...")
                update_data = {
                    'id': added_product['id'],
                    'name': added_product['name'] + ' (Updated)',
                    'category': 'Updated Performance Test',
                    'buy_price': 24.99,
                    'sell_price': 39.99,
                    'stock': 60,
                    'barcode': added_product.get('barcode', '')
                }
                
                start_time = time.time()
                update_result = enhanced_data.update_product(update_data)
                end_time = time.time()
                
                update_time_ms = (end_time - start_time) * 1000
                results['update_time'] = update_time_ms
                print(f"   Result: Product updated in {update_time_ms:.2f}ms")
                
                # Test stock update performance
                print("3. Testing update_product_stock() performance...")
                start_time = time.time()
                stock_result = enhanced_data.update_product_stock(added_product['id'], 75)
                end_time = time.time()
                
                stock_time_ms = (end_time - start_time) * 1000
                results['stock_update_time'] = stock_time_ms
                print(f"   Result: Stock updated in {stock_time_ms:.2f}ms")
        
        return results
        
    except Exception as e:
        print(f"   ERROR: {e}")
        traceback.print_exc()
        return None

def test_bulk_operations_performance():
    """Test performance with bulk operations"""
    print("\nPERFORMANCE TEST: BULK OPERATIONS")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        # Test multiple product additions
        print("1. Testing bulk product addition (10 products)...")
        products_to_add = []
        base_time = int(time.time())
        
        for i in range(10):
            products_to_add.append({
                'name': f'Bulk Test Product {base_time + i}',
                'category': 'Bulk Test',
                'buy_price': 10.00 + i,
                'sell_price': 20.00 + i,
                'stock': 10 + i,
                'barcode': f'BULK{base_time + i}'
            })
        
        start_time = time.time()
        success_count = 0
        for product in products_to_add:
            if enhanced_data.add_product(product):
                success_count += 1
        end_time = time.time()
        
        bulk_time_ms = (end_time - start_time) * 1000
        avg_time_per_product = bulk_time_ms / 10
        print(f"   Result: {success_count}/10 products added in {bulk_time_ms:.2f}ms")
        print(f"   Average: {avg_time_per_product:.2f}ms per product")
        print(f"   Throughput: {10/bulk_time_ms*1000:.2f} products/second")
        
        # Test data refresh after bulk operations
        print("2. Testing data refresh after bulk operations...")
        start_time = time.time()
        refreshed_products = enhanced_data.get_products()
        end_time = time.time()
        
        refresh_time_ms = (end_time - start_time) * 1000
        print(f"   Result: {len(refreshed_products)} products refreshed in {refresh_time_ms:.2f}ms")
        
        return {
            'bulk_add_time': bulk_time_ms,
            'avg_add_time': avg_time_per_product,
            'throughput': 10/bulk_time_ms*1000,
            'refresh_time': refresh_time_ms,
            'total_products': len(refreshed_products)
        }
        
    except Exception as e:
        print(f"   ERROR: {e}")
        traceback.print_exc()
        return None

def test_search_performance():
    """Test search and filtering performance"""
    print("\nPERFORMANCE TEST: SEARCH OPERATIONS")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        # Get all products first
        all_products = enhanced_data.get_products()
        print(f"Testing search on {len(all_products)} total products")
        
        results = {}
        
        # Test search with different terms
        search_terms = ['Test', 'Bulk', 'Performance', '']
        
        for i, term in enumerate(search_terms, 1):
            print(f"{i}. Testing search for '{term}'...")
            start_time = time.time()
            search_results = enhanced_data.search_products_fast(term, limit=10)
            end_time = time.time()
            
            search_time_ms = (end_time - start_time) * 1000
            results[f'search_{term or "empty"}'] = search_time_ms
            print(f"   Result: {len(search_results)} results in {search_time_ms:.2f}ms")
        
        # Test pagination performance on different page sizes
        page_sizes = [5, 10, 25, 50]
        print(f"5. Testing pagination performance...")
        
        for page_size in page_sizes:
            start_time = time.time()
            paged_result = enhanced_data.get_products_paged(page=1, page_size=page_size)
            end_time = time.time()
            
            page_time_ms = (end_time - start_time) * 1000
            results[f'page_size_{page_size}'] = page_time_ms
            print(f"   Page size {page_size}: {len(paged_result.data)} items in {page_time_ms:.2f}ms")
        
        return results
        
    except Exception as e:
        print(f"   ERROR: {e}")
        traceback.print_exc()
        return None

def test_concurrent_operations():
    """Test concurrent-like operations (rapid sequential operations)"""
    print("\nPERFORMANCE TEST: RAPID SEQUENTIAL OPERATIONS")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        print("1. Testing rapid data retrievals...")
        start_time = time.time()
        
        # Simulate rapid UI refreshes
        for i in range(5):
            products = enhanced_data.get_products()
            categories = enhanced_data.get_categories()
            paged = enhanced_data.get_products_paged(page=1, page_size=10)
        
        end_time = time.time()
        rapid_time_ms = (end_time - start_time) * 1000
        print(f"   Result: 5 rapid retrievals in {rapid_time_ms:.2f}ms")
        print(f"   Average per retrieval: {rapid_time_ms/5:.2f}ms")
        
        # Test rapid stock updates
        print("2. Testing rapid stock updates...")
        products = enhanced_data.get_products()
        
        if products:
            test_product_id = products[0]['id']
            start_time = time.time()
            
            # Rapid stock updates (simulating quick adjustments)
            for i in range(5):
                enhanced_data.update_product_stock(test_product_id, 100 + i)
            
            end_time = time.time()
            stock_update_time_ms = (end_time - start_time) * 1000
            print(f"   Result: 5 rapid stock updates in {stock_update_time_ms:.2f}ms")
            print(f"   Average per update: {stock_update_time_ms/5:.2f}ms")
        
        return {
            'rapid_retrieval_time': rapid_time_ms,
            'rapid_stock_update_time': stock_update_time_ms if 'stock_update_time_ms' in locals() else 0
        }
        
    except Exception as e:
        print(f"   ERROR: {e}")
        traceback.print_exc()
        return None

def test_memory_usage():
    """Test memory usage patterns"""
    print("\nPERFORMANCE TEST: MEMORY USAGE")
    print("=" * 50)
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"1. Initial memory usage: {initial_memory:.2f} MB")
        
        from modules.enhanced_data_access import enhanced_data
        
        # Load data and measure memory
        products = enhanced_data.get_products()
        categories = enhanced_data.get_categories()
        
        after_load_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"2. Memory after data load: {after_load_memory:.2f} MB")
        print(f"   Memory increase: {after_load_memory - initial_memory:.2f} MB")
        
        # Perform several operations and measure memory
        for i in range(10):
            paged = enhanced_data.get_products_paged(page=1, page_size=20)
            search = enhanced_data.search_products_fast("test", limit=10)
        
        after_operations_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"3. Memory after operations: {after_operations_memory:.2f} MB")
        print(f"   Total memory increase: {after_operations_memory - initial_memory:.2f} MB")
        
        return {
            'initial_memory': initial_memory,
            'after_load_memory': after_load_memory,
            'after_operations_memory': after_operations_memory,
            'memory_increase': after_operations_memory - initial_memory
        }
        
    except ImportError:
        print("   psutil not available - skipping memory test")
        return None
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

def generate_performance_report(results: Dict):
    """Generate a comprehensive performance report"""
    print("\n" + "=" * 70)
    print("ENHANCED INVENTORY PAGE PERFORMANCE REPORT")
    print("=" * 70)
    
    # Data Loading Performance
    if 'data_loading' in results and results['data_loading']:
        data = results['data_loading']
        print(f"\nDATA LOADING PERFORMANCE:")
        print(f"  Products Load Time: {data['products_load_time']:.2f}ms")
        print(f"  Products Count: {data['products_count']}")
        print(f"  Categories Count: {data['categories_count']}")
        print(f"  Pagination Time: {data['pagination_time']:.2f}ms")
        
        # Performance rating
        if data['products_load_time'] < 100:
            print(f"  Rating: EXCELLENT (< 100ms)")
        elif data['products_load_time'] < 500:
            print(f"  Rating: GOOD (< 500ms)")
        else:
            print(f"  Rating: NEEDS OPTIMIZATION (> 500ms)")
    
    # CRUD Performance
    if 'crud_ops' in results and results['crud_ops']:
        crud = results['crud_ops']
        print(f"\nCRUD OPERATIONS PERFORMANCE:")
        if 'add_time' in crud:
            print(f"  Add Product: {crud['add_time']:.2f}ms")
        if 'update_time' in crud:
            print(f"  Update Product: {crud['update_time']:.2f}ms")
        if 'stock_update_time' in crud:
            print(f"  Stock Update: {crud['stock_update_time']:.2f}ms")
        
        avg_crud_time = sum(crud.values()) / len(crud)
        if avg_crud_time < 50:
            print(f"  Rating: EXCELLENT (avg {avg_crud_time:.2f}ms)")
        elif avg_crud_time < 200:
            print(f"  Rating: GOOD (avg {avg_crud_time:.2f}ms)")
        else:
            print(f"  Rating: NEEDS OPTIMIZATION (avg {avg_crud_time:.2f}ms)")
    
    # Bulk Operations Performance
    if 'bulk_ops' in results and results['bulk_ops']:
        bulk = results['bulk_ops']
        print(f"\nBULK OPERATIONS PERFORMANCE:")
        print(f"  Bulk Add (10 products): {bulk['bulk_add_time']:.2f}ms")
        print(f"  Average per Product: {bulk['avg_add_time']:.2f}ms")
        print(f"  Throughput: {bulk['throughput']:.2f} products/second")
        print(f"  Data Refresh: {bulk['refresh_time']:.2f}ms")
        print(f"  Total Products: {bulk['total_products']}")
        
        if bulk['throughput'] > 20:
            print(f"  Rating: EXCELLENT (> 20 products/sec)")
        elif bulk['throughput'] > 10:
            print(f"  Rating: GOOD (> 10 products/sec)")
        else:
            print(f"  Rating: NEEDS OPTIMIZATION (< 10 products/sec)")
    
    # Search Performance
    if 'search' in results and results['search']:
        search = results['search']
        print(f"\nSEARCH OPERATIONS PERFORMANCE:")
        for key, value in search.items():
            if 'search_' in key:
                term = key.replace('search_', '')
                print(f"  Search '{term}': {value:.2f}ms")
            elif 'page_size_' in key:
                size = key.replace('page_size_', '')
                print(f"  Page size {size}: {value:.2f}ms")
    
    # Memory Usage
    if 'memory' in results and results['memory']:
        mem = results['memory']
        print(f"\nMEMORY USAGE:")
        print(f"  Initial: {mem['initial_memory']:.2f} MB")
        print(f"  After Load: {mem['after_load_memory']:.2f} MB")
        print(f"  After Operations: {mem['after_operations_memory']:.2f} MB")
        print(f"  Total Increase: {mem['memory_increase']:.2f} MB")
        
        if mem['memory_increase'] < 10:
            print(f"  Rating: EXCELLENT (< 10 MB increase)")
        elif mem['memory_increase'] < 50:
            print(f"  Rating: GOOD (< 50 MB increase)")
        else:
            print(f"  Rating: HIGH USAGE (> 50 MB increase)")
    
    print(f"\n" + "=" * 70)
    print("OVERALL PERFORMANCE ASSESSMENT")
    print("=" * 70)
    
    # Calculate overall score
    performance_issues = 0
    total_tests = 0
    
    if 'data_loading' in results and results['data_loading']:
        total_tests += 1
        if results['data_loading']['products_load_time'] > 500:
            performance_issues += 1
    
    if 'crud_ops' in results and results['crud_ops']:
        total_tests += 1
        avg_crud = sum(results['crud_ops'].values()) / len(results['crud_ops'])
        if avg_crud > 200:
            performance_issues += 1
    
    if 'bulk_ops' in results and results['bulk_ops']:
        total_tests += 1
        if results['bulk_ops']['throughput'] < 10:
            performance_issues += 1
    
    performance_score = ((total_tests - performance_issues) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Performance Score: {performance_score:.1f}%")
    
    if performance_score >= 90:
        print("Overall Rating: EXCELLENT - Production ready with optimal performance")
    elif performance_score >= 75:
        print("Overall Rating: GOOD - Production ready with acceptable performance")
    elif performance_score >= 60:
        print("Overall Rating: FAIR - May need optimization for high-load scenarios")
    else:
        print("Overall Rating: NEEDS IMPROVEMENT - Performance optimization required")
    
    return performance_score

def main():
    """Run all performance tests"""
    print("ENHANCED INVENTORY PAGE PERFORMANCE TESTING")
    print("=" * 70)
    print("Testing backend performance for production readiness...")
    print("=" * 70)
    
    results = {}
    
    # Run all performance tests
    results['data_loading'] = test_data_loading_performance()
    results['crud_ops'] = test_crud_operations_performance()
    results['bulk_ops'] = test_bulk_operations_performance()
    results['search'] = test_search_performance()
    results['concurrent'] = test_concurrent_operations()
    results['memory'] = test_memory_usage()
    
    # Generate comprehensive report
    performance_score = generate_performance_report(results)
    
    return performance_score >= 75  # Consider 75% as passing

if __name__ == "__main__":
    success = main()
    print(f"\nPerformance Test: {'PASSED' if success else 'NEEDS ATTENTION'}")
    sys.exit(0 if success else 1)
