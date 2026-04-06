# init_story_actions.py (если файл в db/Plot/)
import sys
import os

# Добавляем корневую директорию (на 2 уровня выше)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Теперь импортируем
from db.main import app
from db.models import db
from db.logger.models_logs import init_logs_models

def init_story_actions():
    """Добавляет действия для сюжета"""
    with app.app_context():
        Action, _ = init_logs_models(db)
        
        story_actions = [
            ('create_story', 'Создание сюжета'),
            ('save_story', 'Сохранение сюжета'),
            ('story_location', 'Локация из сюжета'),
            ('story_character', 'Персонаж из сюжета'),
            ('story_monster', 'Монстр из сюжета'),
            ('story_item', 'Предмет из сюжета')
        ]
        
        for action_name, description in story_actions:
            action = Action.query.filter_by(action_name=action_name).first()
            if not action:
                db.session.add(Action(action_name=action_name, description=description))
                print(f"Added story action: {action_name}")
        
        db.session.commit()
        print("Story actions initialized!")

if __name__ == '__main__':
    init_story_actions()