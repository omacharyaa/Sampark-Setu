"""
Initialize database tables and run migrations
Run this after deployment or when database schema changes
"""

from app import create_app
from app.models import db
import os

def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table (works for both SQLite and PostgreSQL)"""
    from sqlalchemy import text
    database_url = os.environ.get('DATABASE_URL', '')
    
    if 'postgresql' in database_url or 'postgres' in database_url:
        # PostgreSQL
        result = conn.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = '{column_name}'
        """))
        return result.fetchone() is not None
    else:
        # SQLite
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = result.fetchall()
        return any(col[1] == column_name for col in columns)

def table_exists(conn, table_name):
    """Check if a table exists (works for both SQLite and PostgreSQL)"""
    from sqlalchemy import text
    database_url = os.environ.get('DATABASE_URL', '')
    
    if 'postgresql' in database_url or 'postgres' in database_url:
        # PostgreSQL
        result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            )
        """))
        return result.fetchone()[0]
    else:
        # SQLite
        result = conn.execute(text(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{table_name}'
        """))
        return result.fetchone() is not None

def init_database():
    """Initialize database tables"""
    app = create_app()
    
    with app.app_context():
        print("=" * 50)
        print("Initializing database...")
        print("=" * 50)
        
        # Create all tables
        print("Creating database tables...")
        try:
            db.create_all()
            print("✓ Database tables created successfully!")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Run migrations if needed
        print("\nChecking for required columns...")
        from sqlalchemy import text
        
        try:
            with db.engine.connect() as conn:
                # Check and add file_name column to messages table
                if table_exists(conn, 'messages'):
                    if not column_exists(conn, 'messages', 'file_name'):
                        print("Adding file_name column to messages table...")
                        try:
                            conn.execute(text("ALTER TABLE messages ADD COLUMN file_name VARCHAR(255)"))
                            conn.commit()
                            print("✓ file_name column added!")
                        except Exception as e:
                            conn.rollback()
                            print(f"⚠ Could not add file_name column (may already exist): {e}")
                    else:
                        print("✓ file_name column already exists in messages table")
                else:
                    print("⚠ messages table does not exist yet")
                
                # Check and add profile_picture column to users table
                if table_exists(conn, 'users'):
                    if not column_exists(conn, 'users', 'profile_picture'):
                        print("Adding profile_picture column to users table...")
                        try:
                            conn.execute(text("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255)"))
                            conn.commit()
                            print("✓ profile_picture column added!")
                        except Exception as e:
                            conn.rollback()
                            print(f"⚠ Could not add profile_picture column (may already exist): {e}")
                    else:
                        print("✓ profile_picture column already exists in users table")
                    
                    # Check and add display_name column to users table
                    if not column_exists(conn, 'users', 'display_name'):
                        print("Adding display_name column to users table...")
                        try:
                            conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))
                            conn.commit()
                            print("✓ display_name column added!")
                        except Exception as e:
                            conn.rollback()
                            print(f"⚠ Could not add display_name column (may already exist): {e}")
                    else:
                        print("✓ display_name column already exists in users table")
                else:
                    print("⚠ users table does not exist yet")
                    
        except Exception as e:
            print(f"⚠ Migration check error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("Database initialization complete!")
        print("=" * 50)

if __name__ == '__main__':
    init_database()

