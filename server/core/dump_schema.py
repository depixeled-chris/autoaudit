"""Dump complete database schema to JSON."""
import sqlite3
import json

conn = sqlite3.connect('/app/data/compliance.db')
cursor = conn.cursor()

schema = {}

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = []
    for row in cursor.fetchall():
        columns.append({
            'name': row[1],
            'type': row[2],
            'notnull': bool(row[3]),
            'default': row[4],
            'pk': bool(row[5])
        })

    # Get indexes
    cursor.execute(f"PRAGMA index_list({table})")
    indexes = [{'name': row[1], 'unique': bool(row[2])} for row in cursor.fetchall()]

    schema[table] = {
        'columns': columns,
        'indexes': indexes
    }

print(json.dumps(schema, indent=2))
