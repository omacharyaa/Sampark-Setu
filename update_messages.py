"""
Update existing messages to have message_type = 'text'
"""
import sqlite3
import os

db_path = 'instance/sampark_setu.db'
if not os.path.exists(db_path):
    db_path = 'sampark_setu.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Update all messages without message_type to 'text'
        cursor.execute("UPDATE messages SET message_type = 'text' WHERE message_type IS NULL OR message_type = ''")
        updated = cursor.rowcount
        conn.commit()
        
        # Count total messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        total = cursor.fetchone()[0]
        
        print(f"Updated {updated} messages with message_type = 'text'")
        print(f"Total messages in database: {total}")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
else:
    print("Database not found")

