"""
Initialize database tables and run migrations
Run this after deployment or when database schema changes
"""

from app import create_app, db
import os

def init_database():
    """Initialize database tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Run migrations if needed
        try:
            # Check if file_name column exists in messages table
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('messages')]
            
            if 'file_name' not in columns:
                print("Adding file_name column to messages table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE messages ADD COLUMN file_name VARCHAR(255)"))
                    conn.commit()
                print("file_name column added!")
            
            # Check if profile_picture and display_name exist in users table
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'profile_picture' not in user_columns:
                print("Adding profile_picture column to users table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255)"))
                    conn.commit()
                print("profile_picture column added!")
            
            if 'display_name' not in user_columns:
                print("Adding display_name column to users table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))
                    conn.commit()
                print("display_name column added!")
                
        except Exception as e:
            print(f"Migration check completed (some columns may already exist): {e}")
        
        print("Database initialization complete!")

if __name__ == '__main__':
    init_database()

