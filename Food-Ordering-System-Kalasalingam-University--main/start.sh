#!/bin/bash

# Initialize database
python -c "from app import app, db; with app.app_context(): db.create_all(); print('Database initialized successfully!')"

# Start the application
exec gunicorn -c gunicorn_config.py app:app
