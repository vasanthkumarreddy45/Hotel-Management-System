#!/usr/bin/env python3
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize database
from app import app, db
with app.app_context():
    db.create_all()
    print("Database initialized successfully!")

# Start the application
if __name__ == "__main__":
    import subprocess
    import sys
    
    # Start gunicorn
    cmd = ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
    subprocess.run(cmd, sys.exit(0))
