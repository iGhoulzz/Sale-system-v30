#!/usr/bin/env python3
"""
Fix custom style references in enhanced inventory page
"""

import re
import sys

def fix_custom_styles(file_path):
    """Fix all custom style references"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace BusinessHeader.TLabel
    content = re.sub(
        r'style="BusinessHeader\.TLabel"[^)]*\)',
        'font=("Segoe UI", 14, "bold"))',
        content
    )
    
    # Replace BusinessText.TLabel  
    content = re.sub(
        r'style="BusinessText\.TLabel"[^)]*\)',
        'font=("Segoe UI", 10))',
        content
    )
    
    # Replace SidebarText.TLabel
    content = re.sub(
        r'style="SidebarText\.TLabel"[^)]*\)', 
        'font=("Segoe UI", 11, "bold"))',
        content
    )
    
    # Remove style parameter completely for simpler labels
    content = re.sub(
        r',\s*style="Business[^"]*\.TLabel"',
        '',
        content
    )
    
    content = re.sub(
        r'style="Business[^"]*\.TLabel",?\s*',
        '',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed custom style references in enhanced inventory page")

if __name__ == "__main__":
    file_path = r"c:\Users\User\Desktop\sale-system - V30\modules\pages\enhanced_inventory_page.py"
    fix_custom_styles(file_path)
