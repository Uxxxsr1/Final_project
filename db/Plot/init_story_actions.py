# db/Plot/init_story_actions.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.main import app
from db.models import db
from db.logger.models_logs import init_logs_models

def init_story_actions():
    """Добавляет действия для сюжета"""
    with app.app_context():
        Action, _ = init_logs_models(db)
        
        story_actions = [
            ('create_story', 'Создание нового сюжета'),
            ('save_story', 'Сохранение сюжета в файл'),
            ('story_location', 'Локация из сюжета'),
            ('story_character', 'Персонаж из сюжета'),
            ('story_monster', 'Монстр/противник из сюжета'),
            ('story_item', 'Предмет/артефакт из сюжета'),
            ('story_published', 'Публикация сюжета для игроков')
        ]
        
        added = 0
        for action_name, description in story_actions:
            action = Action.query.filter_by(action_name=action_name).first()
            if not action:
                db.session.add(Action(action_name=action_name, description=description))
                print(f"Added story action: {action_name} - {description}")
                added += 1
        
        db.session.commit()
        print(f"\nStory actions initialized! Added {added} new actions.")
        
        all_actions = Action.query.all()
        print(f"\nTotal actions in system: {len(all_actions)}")

if __name__ == '__main__':
    print("Initializing story actions...")
    init_story_actions()
    print("\nDone!")
