"""
Simple script to run the application locally
This script will:
1. Check if virtual environment is activated
2. Install dependencies if needed
3. Initialize database
4. Run the application
"""

import os
import sys
import subprocess

def check_virtual_env():
    """Check if virtual environment is activated"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing dependencies: {e}")
        return False

def initialize_database():
    """Initialize database tables"""
    print("Initializing database...")
    try:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            db.create_all()
            print("✓ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_application():
    """Run the Flask application"""
    print("\n" + "="*50)
    print("Starting Sampark Setu Chat Application...")
    print("="*50)
    print("\nServer will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        from app import create_app, socketio
        app = create_app()
        
        # Run the application
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\n✗ Error running application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main function"""
    print("Sampark Setu - Setup and Run Script")
    print("="*50)
    
    # Check if virtual environment is activated
    if not check_virtual_env():
        print("⚠ Warning: Virtual environment not detected.")
        print("It's recommended to use a virtual environment.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Please activate your virtual environment first:")
            print("  Windows: venv\\Scripts\\activate")
            print("  Linux/Mac: source venv/bin/activate")
            sys.exit(1)
    else:
        print("✓ Virtual environment detected")
    
    # Check if requirements.txt exists
    if not os.path.exists('requirements.txt'):
        print("✗ requirements.txt not found!")
        sys.exit(1)
    
    # Ask if user wants to install dependencies
    install_deps = input("\nInstall/update dependencies? (y/n): ")
    if install_deps.lower() == 'y':
        if not install_dependencies():
            sys.exit(1)
    
    # Initialize database
    init_db = input("\nInitialize database? (y/n): ")
    if init_db.lower() == 'y':
        if not initialize_database():
            print("⚠ Database initialization failed, but continuing...")
    
    # Run the application
    print("\n")
    run_application()

if __name__ == '__main__':
    main()

