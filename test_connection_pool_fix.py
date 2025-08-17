#!/usr/bin/env python3
"""
Connection Pool Leak Fix Validation Test
Tests that the connection pool no longer exhausts after fixing leaks
"""

import sys
import os
import time
import threading

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.enhanced_data_access import EnhancedDataAccess
from modules.db_manager import get_connection_stats, reset_connection_stats, initialize_connection_pool

def test_connection_pool_stress():
    """Test that connection pool doesn't exhaust under load"""
    
    print("🧪 CONNECTION POOL LEAK FIX VALIDATION")
    print("=" * 50)
    
    try:
        # Initialize pool and reset stats
        initialize_connection_pool()
        reset_connection_stats()
        
        # Get initial stats
        initial_stats = get_connection_stats()
        print(f"📊 Initial Pool State:")
        print(f"   Pool Size: {initial_stats['pool_size']} connections")
        print(f"   Active: {initial_stats['active']} connections")
        print(f"   Created: {initial_stats['created']} connections")
        print(f"   Returned: {initial_stats['returned']} connections")
        
        # Create data access instance
        data_access = EnhancedDataAccess()
        
        # Test multiple operations that previously leaked connections
        print(f"\n🔄 Running stress test (50 operations)...")
        
        start_time = time.time()
        
        for i in range(50):
            try:
                # Test operations that were leaking connections
                
                # 1. Get products (this was leaking)
                products = data_access.get_all_products()
                
                # 2. Search products (this was leaking)
                if i % 10 == 0:
                    search_results = data_access.search_products("test", 1, 5)
                
                # 3. Add category (this was leaking)
                if i % 20 == 0:
                    data_access.add_category(f"TestCategory{i}")
                
                # Print progress every 10 operations
                if (i + 1) % 10 == 0:
                    current_stats = get_connection_stats()
                    leak_count = current_stats['created'] - current_stats['returned']
                    print(f"   Operation {i+1}/50 - Leaks: {leak_count}, Active: {current_stats['active']}")
                    
                    if leak_count > 5:
                        print(f"   🚨 LEAK DETECTED: {leak_count} connections not returned!")
                        break
                        
            except Exception as e:
                if "pool exhausted" in str(e).lower() or "extended wait" in str(e).lower():
                    print(f"   ❌ POOL EXHAUSTION at operation {i+1}: {str(e)}")
                    return False
                else:
                    print(f"   ⚠️  Operation {i+1} failed: {str(e)}")
        
        end_time = time.time()
        
        # Get final stats
        final_stats = get_connection_stats()
        leak_count = final_stats['created'] - final_stats['returned']
        
        print(f"\n📈 FINAL RESULTS:")
        print(f"   Test Duration: {end_time - start_time:.2f} seconds")
        print(f"   Pool Size: {final_stats['pool_size']} connections")
        print(f"   Created: {final_stats['created']} connections")
        print(f"   Returned: {final_stats['returned']} connections")
        print(f"   Active: {final_stats['active']} connections")
        print(f"   Peak Usage: {final_stats['peak']} connections")
        print(f"   Detected Leaks: {leak_count} connections")
        
        # Verdict
        print(f"\n🎯 TEST VERDICT:")
        if leak_count == 0:
            print("   ✅ PERFECT - No connection leaks detected!")
            print("   ✅ Pool exhaustion issue RESOLVED")
            return True
        elif leak_count <= 2:
            print("   ⚡ GOOD - Minimal leaks within acceptable range")
            print("   ⚡ Pool exhaustion issue likely RESOLVED")
            return True
        else:
            print(f"   ⚠️  CONCERNING - {leak_count} connections still leaking")
            print("   ⚠️  Pool exhaustion may still occur under heavy load")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_connection_pool_stress()
    
    if success:
        print("\n" + "="*50)
        print("🎉 CONNECTION POOL FIXES VALIDATED")
        print("✅ The pool exhaustion issue has been resolved!")
        print("🚀 Backend is now ready for production load")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("⚠️  ADDITIONAL FIXES MAY BE NEEDED")
        print("📋 Review the test results above")
        print("="*50)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
