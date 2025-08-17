#!/usr/bin/env python3
"""
tools/extract_messages.py - Extract translatable strings from source code
------------------------------------------------------------------------
This script extracts translatable strings from the source code and creates
the message template (.pot) file that can be used for translations.

Usage:
    python tools/extract_messages.py
"""

import os
import re
import sys

def main():
    # Add parent directory to path so we can import application modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    # Create locales directory if it doesn't exist
    locales_dir = os.path.join(parent_dir, 'locales')
    if not os.path.exists(locales_dir):
        os.makedirs(locales_dir)
    
    # Create messages directory for each language
    for lang in ['ar']:  # Add more languages as needed
        lang_dir = os.path.join(locales_dir, lang, 'LC_MESSAGES')
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir, exist_ok=True)
    
    # Paths to search for translatable strings
    search_paths = [
        os.path.join(parent_dir, 'modules'),
        os.path.join(parent_dir, 'main.py'),
    ]
    
    # Create a .pot template file
    pot_file = os.path.join(locales_dir, 'messages.pot')
    
    with open(pot_file, 'w', encoding='utf-8') as f:
        f.write('''msgid ""
msgstr ""
"Project-Id-Version: Sales Management System\\n"
"POT-Creation-Date: 2023-08-17 12:00+0000\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Generated-By: extract_messages.py\\n"

''')
        
        # Regular expression to find translatable strings
        # Look for _("...") or _('...')
        pattern = re.compile(r'_\([\'"](.+?)[\'"]\)')
        
        # Dictionary to store unique strings
        strings = {}
        
        # Walk through each file in search paths
        for path in search_paths:
            if os.path.isfile(path):
                extract_strings_from_file(path, pattern, strings)
            else:
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            extract_strings_from_file(file_path, pattern, strings)
        
        # Write strings to the template file
        for text in sorted(strings.keys()):
            # Escape quotes
            text_escaped = text.replace('"', '\\"')
            f.write(f'msgid "{text_escaped}"\nmsgstr ""\n\n')
    
    print(f"Extracted {len(strings)} translatable strings to {pot_file}")
    print("Now you can use this template to create translations.")
    print("For Arabic (ar), create locales/ar/LC_MESSAGES/messages.po")

def extract_strings_from_file(file_path, pattern, strings):
    """Extract translatable strings from a file using the given pattern."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for match in pattern.finditer(content):
                text = match.group(1)
                strings[text] = True
    except UnicodeDecodeError:
        print(f"Warning: Could not read {file_path} as UTF-8, skipping")

if __name__ == "__main__":
    main() 