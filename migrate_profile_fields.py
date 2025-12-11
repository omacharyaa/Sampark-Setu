"""
Migration script to add profile_picture and display_name fields to users table
"""

from app import create_app
from app.models import db
import sqlite3
import os

def migrate_profile_fields():
    """Add profile_picture and display_name columns to users table"""
    app = create_app()
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_filename = db_uri.split('///')[-1]
        
        # Get the actual root directory (where the script is located)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = script_dir  # Script is in root, not in a subdirectory
        
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
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            if 'profile_picture' not in columns:
                print("Adding profile_picture column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255)")
                print("Added profile_picture column.")
            else:
                print("profile_picture column already exists.")
            
            if 'display_name' not in columns:
                print("Adding display_name column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)")
                print("Added display_name column.")
            else:
                print("display_name column already exists.")
                
            conn.commit()
            print("Migration completed successfully!")
            
            cursor.execute("PRAGMA table_info(users)")
            updated_columns = [column[1] for column in cursor.fetchall()]
            print(f"Updated columns: {updated_columns}")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == '__main__':
    migrate_profile_fields()

