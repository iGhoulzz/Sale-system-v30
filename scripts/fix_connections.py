#!/usr/bin/env python
"""
Script to fix database connection management in Python files.
This replaces direct conn.close() calls with return_connection(conn)
and adds the necessary import if missing.
"""

import os
import re
import sys

def should_process_file(filepath):
    """Determine if we should process this file."""
    # Skip __pycache__ directories
    if '__pycache__' in filepath:
        return False
    # Only process Python files
    if not filepath.endswith('.py'):
        return False
    # Skip the current script
    if os.path.basename(filepath) == os.path.basename(__file__):
        return False
    return True

def has_return_connection_import(content):
    """Check if file already imports return_connection."""
    return re.search(r'from\s+modules\.db_manager\s+import\s+.*return_connection', content) is not None

def add_return_connection_import(content):
    """Add return_connection import to file content."""
    # Check if the file imports from db_manager
    db_manager_import = re.search(r'from\s+modules\.db_manager\s+import\s+(.*?)$', content, re.MULTILINE)
    
    if db_manager_import:
        # There's an existing import, check if we need to add return_connection
        imports = db_manager_import.group(1)
        
        if 'return_connection' not in imports:
            # Need to add return_connection to existing import
            if imports.strip().endswith(','):
                # Import already has a comma, just add return_connection
                content = content.replace(
                    db_manager_import.group(0),
                    f"{db_manager_import.group(0)} return_connection,"
                )
            elif imports.strip().endswith(')'):
                # Import is enclosed in parentheses, add within them
                content = content.replace(
                    db_manager_import.group(0),
                    f"{db_manager_import.group(0)[:-1]}, return_connection)"
                )
            else:
                # Add with comma
                content = content.replace(
                    db_manager_import.group(0),
                    f"{db_manager_import.group(0)}, return_connection"
                )
    else:
        # No existing import from db_manager, add a new one
        # Find common import locations
        import_section = re.search(r'^import\s+.*$', content, re.MULTILINE)
        if import_section:
            # Add after the last import
            last_import = list(re.finditer(r'^(import|from)\s+.*$', content, re.MULTILINE))[-1]
            content = (
                content[:last_import.end()] + 
                "\nfrom modules.db_manager import return_connection" +
                content[last_import.end():]
            )
        else:
            # No imports found, add at the beginning after any initial comments
            content = "from modules.db_manager import return_connection\n\n" + content
            
    return content

def replace_conn_close(content):
    """Replace conn.close() with return_connection(conn)."""
    # This regex looks for conn.close() but not return_connection(conn)
    return re.sub(
        r'(?<!return_)conn\.close\(\)',
        'return_connection(conn)',
        content
    )

def process_file(filepath):
    """Process a Python file to fix connection management."""
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if file has any conn.close() calls
    if 'conn.close()' not in content:
        return 0  # No changes needed
    
    # Replace conn.close() with return_connection(conn)
    modified_content = replace_conn_close(content)
    
    # If we made changes, ensure return_connection is imported
    if modified_content != content and not has_return_connection_import(modified_content):
        modified_content = add_return_connection_import(modified_content)
    
    # Write back if we made changes
    if modified_content != content:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(modified_content)
        return 1  # Changes made
    
    return 0  # No changes needed

def scan_directory(directory='.'):
    """Scan a directory for Python files and fix them."""
    changes_count = 0
    files_changed = []
    
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            
            if should_process_file(filepath):
                try:
                    file_changes = process_file(filepath)
                    if file_changes > 0:
                        files_changed.append(filepath)
                        changes_count += file_changes
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    return changes_count, files_changed

def main():
    """Main entry point."""
    directory = '.' if len(sys.argv) < 2 else sys.argv[1]
    
    print(f"Scanning directory: {directory}")
    changes_count, files_changed = scan_directory(directory)
    
    print(f"\nMade {changes_count} changes in {len(files_changed)} files:")
    for filepath in files_changed:
        print(f"  - {filepath}")

if __name__ == "__main__":
    main() 