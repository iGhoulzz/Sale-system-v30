#!/usr/bin/env python3
from modules.db_manager import ConnectionContext

with ConnectionContext() as conn:
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(Products)')
    print('Products table schema:')
    for row in cursor.fetchall():
        print(f'  {row[1]} ({row[2]})')
