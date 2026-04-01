# db/logger/init_logs.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.main import app
from db.models import db

def init_logs_tables():
    """Создает таблицы логов"""
    with app.app_context():
        print("Creating logs tables...")
        db.create_all()
        print("Tables created successfully!")
        
        # Проверяем создались ли таблицы
        try:
            from db.logger.models_logs import Action
            print(f"Actions table exists: {Action.query.count() if Action else 'checking...'}")
        except Exception as e:
            print(f"Error checking tables: {e}")

if __name__ == '__main__':
    init_logs_tables()
