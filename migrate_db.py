"""
Database Migration Script
Adds message_type column to messages table if it doesn't exist
Run this once to update existing databases
"""

from app import create_app
from app.models import db
import sqlite3
import os

def migrate_database():
    """Add message_type column to messages table"""
    # Check multiple possible database locations
    possible_paths = [
        'instance/sampark_setu.db',
        'sampark_setu.db',
        os.path.join(os.path.dirname(__file__), 'instance', 'sampark_setu.db'),
        os.path.join(os.path.dirname(__file__), 'sampark_setu.db')
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Database file not found. Creating new database...")
        app = create_app()
        with app.app_context():
            db.create_all()
        print("Database created with new schema.")
        return
    
    print(f"Found database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        if 'message_type' not in columns:
            print("Adding message_type column to messages table...")
            cursor.execute("ALTER TABLE messages ADD COLUMN message_type VARCHAR(20) DEFAULT 'text'")
            conn.commit()
            print("Migration completed successfully!")
            
            # Verify the column was added
            cursor.execute("PRAGMA table_info(messages)")
            new_columns = [column[1] for column in cursor.fetchall()]
            print(f"Updated columns: {new_columns}")
        else:
            print("message_type column already exists. No migration needed.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()

