#!/usr/bin/env python3
"""
Connection Pool Status Checker
Checks the current status of the database connection pool to diagnose exhaustion issues.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_manager import get_connection_stats, initialize_connection_pool

def main():
    print("🔍 Connection Pool Status Check")
    print("=" * 50)
    
    try:
        # Initialize the pool first
        initialize_connection_pool()
        
        # Get current stats
        stats = get_connection_stats()
        
        print("\n📊 Current Connection Pool Statistics:")
        print(f"   Pool Size: {stats['pool_size']} connections")
        print(f"   Timeout: {stats['timeout']} seconds")
        print(f"   Created: {stats['created']} connections")
        print(f"   Returned: {stats['returned']} connections")
        print(f"   Active: {stats['active']} connections")
        print(f"   Peak: {stats['peak']} connections")
        
        # Calculate potential leaks
        leak_count = stats['created'] - stats['returned']
        
        print("\n🚨 Leak Analysis:")
        if leak_count > 0:
            print(f"   POTENTIAL LEAK DETECTED: {leak_count} connections not returned")
            print(f"   This explains pool exhaustion!")
        else:
            print(f"   No obvious leaks detected (all created connections returned)")
            
        print(f"\n📈 Pool Utilization:")
        utilization = (stats['active'] / stats['pool_size']) * 100
        print(f"   Current: {utilization:.1f}% ({stats['active']}/{stats['pool_size']})")
        
        if utilization > 80:
            print("   ⚠️  HIGH UTILIZATION - Pool stress detected")
        elif utilization > 60:
            print("   ⚡ MODERATE UTILIZATION - Normal under load")
        else:
            print("   ✅ LOW UTILIZATION - Healthy state")
            
    except Exception as e:
        print(f"❌ Error checking connection pool: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
