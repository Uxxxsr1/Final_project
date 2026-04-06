# init_logs_actions.py
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gui.main import app
from db.models import db
from logger.models_logs import init_logs_models

def init_actions():
    """Инициализация базовых действий в БД"""
    with app.app_context():
        Action, _ = init_logs_models(db)
        
        base_actions = [
            ('login', 'Вход в систему'),
            ('logout', 'Выход из системы'),
            ('create_character', 'Создание персонажа'),
            ('select_character', 'Выбор персонажа'),
            ('delete_character', 'Удаление персонажа'),
            ('create_session', 'Создание игровой сессии'),
            ('join_session', 'Присоединение к сессии'),
            ('leave_session', 'Выход из сессии'),
            ('view_session', 'Просмотр сессии'),
            ('exit_role', 'Выход из роли'),
            ('attack', 'Атака противника'),
            ('use_item', 'Использование предмета'),
            ('cast_spell', 'Применение заклинания'),
            ('trade', 'Торговля с другим игроком'),
            ('talk', 'Разговор с NPC или игроком'),
            ('move', 'Перемещение по локации'),
            ('quest_complete', 'Завершение квеста'),
            ('level_up', 'Повышение уровня'),
            ('gm_action', 'Действие гейммастера')
        ]
        
        for action_name, description in base_actions:
            action = Action.query.filter_by(action_name=action_name).first()
            if not action:
                db.session.add(Action(action_name=action_name, description=description))
                print(f"Added action: {action_name}")
        
        db.session.commit()
        print("All base actions initialized!")

if __name__ == '__main__':
    init_actions()