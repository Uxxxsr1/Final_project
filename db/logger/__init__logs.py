# init_logs.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from gui.main import app
from db.models import db

with app.app_context():
    print("Creating logs tables...")
    db.create_all()
    print("Tables created successfully!")
    
    # Проверяем создались ли таблицы
    from logger.models_logs import Action
    print(f"Actions table exists: {Action.query.count() if Action else 'checking...'}")