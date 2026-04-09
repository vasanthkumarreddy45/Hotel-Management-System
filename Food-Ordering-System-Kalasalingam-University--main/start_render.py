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

# Replace current process with gunicorn
os.execlp("gunicorn", "gunicorn", "-c", "gunicorn_config.py", "app:app")
