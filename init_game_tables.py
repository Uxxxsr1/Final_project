# init_game_tables.py
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.main import app
from db.models import db
from db.logger.models_logs import init_logs_models

def init_tables():
    with app.app_context():
        print("=" * 50)
        print("Инициализация игровых таблиц")
        print("=" * 50)
        
        # Инициализируем модели логов
        Action, GameLog = init_logs_models(db)
        
        # Создаем все таблицы (включая новые)
        print("Создание таблиц...")
        db.create_all()
        print("✓ Таблицы созданы")
        
        # Проверяем создание таблиц
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        game_tables = ['character_stats', 'items', 'character_items', 'global_events', 'game_contexts']
        existing_game_tables = [t for t in game_tables if t in tables]
        
        print(f"\nИгровые таблицы: {existing_game_tables}")
        
        # Добавляем базовые предметы
        from db.models import Item
        if Item.query.count() == 0:
            print("\nДобавление базовых предметов...")
            
            starter_items = [
                Item(name='Рваная рубашка', description='Простая рубашка', slot='body', 
                     effects={'strength': 0, 'dexterity': 0, 'intelligence': 0, 'charisma': 0},
                     item_type='armor', icon='👕'),
                
                Item(name='Деревянный меч', description='Тренировочный меч', slot='weapon', 
                     effects={'strength': 1}, item_type='weapon', icon='⚔️'),
                
                Item(name='Кожаные сапоги', description='Обычные сапоги', slot='feet', 
                     effects={'dexterity': 1}, item_type='armor', icon='👢'),
                
                Item(name='Пояс великана', description='Магический пояс, дающий силу великана', slot='waist', 
                     effects={'strength': 3, 'dexterity': -1}, item_type='accessory', icon='🔗'),
                
                Item(name='Сапоги эльфа', description='Эльфийские сапоги, увеличивающие ловкость', slot='feet', 
                     effects={'dexterity': 2}, item_type='armor', icon='👢'),
                
                Item(name='Мантия мага', description='Мантия, увеличивающая интеллект', slot='body', 
                     effects={'intelligence': 5}, item_type='armor', icon='🧥'),
                
                Item(name='Кольцо силы', description='Кольцо дающее силу', slot='finger', 
                     effects={'strength': 2}, item_type='accessory', icon='💍'),
                
                Item(name='Амулет мудрости', description='Амулет дающий мудрость', slot='neck', 
                     effects={'intelligence': 2, 'charisma': 1}, item_type='accessory', icon='📿'),
                
                Item(name='Целительное зелье', description='Восстанавливает 10 HP', 
                     effects={'heal_hp': 10}, item_type='consumable', is_equippable=False, icon='🧪'),
                
                Item(name='Магическое зелье', description='Восстанавливает 5 MP', 
                     effects={'heal_mp': 5}, item_type='consumable', is_equippable=False, icon='🧪'),
            ]
            
            for item in starter_items:
                db.session.add(item)
            
            db.session.commit()
            print(f"✓ Добавлено {len(starter_items)} предметов")
        
        print("\n" + "=" * 50)
        print("Инициализация завершена!")
        print("=" * 50)

if __name__ == '__main__':
    init_tables()