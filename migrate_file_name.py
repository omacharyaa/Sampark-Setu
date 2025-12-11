"""
Migration script to add file_name field to messages table
"""

from app import create_app
from app.models import db
import sqlite3
import os

def migrate_file_name():
    """Add file_name column to messages table"""
    app = create_app()
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_filename = db_uri.split('///')[-1]
        
        # Get the actual root directory (project root)
        root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check instance folder first (Flask's default)
        instance_path = os.path.join(root_dir, 'instance')
        db_path = os.path.join(instance_path, db_filename)
        
        if not os.path.exists(db_path):
            # Try root directory
            root_db_path = os.path.join(root_dir, db_filename)
            if os.path.exists(root_db_path):
                db_path = root_db_path
            else:
                print(f"Database file not found. Expected at: {db_path}")
                print("Creating new database with updated schema...")
                # Create instance folder if it doesn't exist
                os.makedirs(instance_path, exist_ok=True)
                db.create_all()
                print("Database created with new schema.")
                return
        
        print(f"Found database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(messages)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            if 'file_name' not in columns:
                print("Adding file_name column to messages table...")
                cursor.execute("ALTER TABLE messages ADD COLUMN file_name VARCHAR(255)")
                print("Added file_name column.")
            else:
                print("file_name column already exists.")
                
            conn.commit()
            print("Migration completed successfully!")
            
            cursor.execute("PRAGMA table_info(messages)")
            updated_columns = [column[1] for column in cursor.fetchall()]
            print(f"Updated columns: {updated_columns}")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == '__main__':
    migrate_file_name()

