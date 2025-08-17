#!/usr/bin/env python3
"""
CRITICAL FIX: Connection Pool Leak Repair
This script fixes the connection leaks causing pool exhaustion
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_connection_leaks():
    """Fix all connection leaks in enhanced_data_access.py and database_routes.py"""
    
    print("🔧 FIXING CONNECTION LEAKS - CRITICAL REPAIR")
    print("=" * 60)
    
    # Files to fix
    files_to_fix = [
        "modules/enhanced_data_access.py",
        "modules/database_routes.py"
    ]
    
    fixes_applied = 0
    
    for file_path in files_to_fix:
        print(f"\n📁 Fixing file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count instances before fix
            leak_count = content.count('with get_connection() as conn:')
            
            if leak_count > 0:
                print(f"   Found {leak_count} connection leaks")
                
                # Fix: Replace get_connection() with ConnectionContext()
                fixed_content = content.replace(
                    'with get_connection() as conn:',
                    'with ConnectionContext() as conn:'
                )
                
                # Write back the fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                print(f"   ✅ Fixed {leak_count} connection leaks")
                fixes_applied += leak_count
            else:
                print("   ✅ No leaks found in this file")
                
        except Exception as e:
            print(f"   ❌ Error fixing {file_path}: {str(e)}")
    
    print(f"\n🎯 REPAIR SUMMARY:")
    print(f"   Total connection leaks fixed: {fixes_applied}")
    
    if fixes_applied > 0:
        print("   🚨 CRITICAL: Connection pool exhaustion should now be resolved!")
        print("   🔄 Restart the application to apply fixes")
    else:
        print("   ℹ️  No leaks found to fix")
    
    return fixes_applied > 0

if __name__ == "__main__":
    success = fix_connection_leaks()
    if success:
        print("\n" + "="*60)
        print("✅ CONNECTION LEAK FIX COMPLETE")
        print("💡 The pool exhaustion issue should now be resolved")
        print("🔄 Please restart your application")
        print("="*60)
    
    sys.exit(0 if success else 1)
