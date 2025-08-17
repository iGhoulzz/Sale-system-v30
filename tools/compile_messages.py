#!/usr/bin/env python3
"""
tools/compile_messages.py - Compile translation message files
-------------------------------------------------------------
This script compiles the .po message files to binary .mo format
that can be used by the gettext library at runtime.

Usage:
    python tools/compile_messages.py
"""

import os
import sys
import subprocess
import platform

def main():
    # Get base directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Path to locales
    locales_dir = os.path.join(parent_dir, 'locales')
    
    # Check if locales directory exists
    if not os.path.exists(locales_dir):
        print(f"Error: Locales directory {locales_dir} does not exist.")
        sys.exit(1)
    
    # Check for msgfmt tool
    msgfmt_cmd = 'msgfmt'
    
    # On Windows, try to use the msgfmt from Python's Tools directory
    if platform.system() == 'Windows':
        python_scripts = os.path.join(sys.prefix, 'Tools', 'i18n', 'msgfmt.py')
        if os.path.exists(python_scripts):
            msgfmt_cmd = f'{sys.executable} "{python_scripts}"'
    
    # Compile .po files
    for root, dirs, files in os.walk(locales_dir):
        for file in files:
            if file.endswith('.po'):
                po_file = os.path.join(root, file)
                mo_file = os.path.join(root, file.replace('.po', '.mo'))
                
                # Skip if .mo file is newer than .po file
                if os.path.exists(mo_file) and os.path.getmtime(mo_file) > os.path.getmtime(po_file):
                    print(f"Skipping {po_file} (already up to date)")
                    continue
                
                print(f"Compiling {po_file} to {mo_file}")
                
                try:
                    # Try to compile using msgfmt command
                    if platform.system() == 'Windows' and msgfmt_cmd.startswith(sys.executable):
                        # Use Python's msgfmt.py script
                        cmd = f'{msgfmt_cmd} -o "{mo_file}" "{po_file}"'
                    else:
                        # Use system msgfmt
                        cmd = f'{msgfmt_cmd} -o "{mo_file}" "{po_file}"'
                    
                    subprocess.run(cmd, shell=True, check=True)
                except subprocess.CalledProcessError:
                    print(f"Error: Failed to compile {po_file}")
                    
                    # Fallback to Python's gettext module if msgfmt fails
                    try:
                        import gettext
                        print("Trying to compile with Python's gettext module...")
                        with open(po_file, 'rb') as f_in:
                            catalog = gettext.GNUTranslations(f_in)
                            with open(mo_file, 'wb') as f_out:
                                catalog._output_file(f_out)
                        print(f"Successfully compiled {po_file} with Python's gettext module")
                    except Exception as e:
                        print(f"Error: Failed to compile with Python's gettext module: {e}")

if __name__ == "__main__":
    main() 