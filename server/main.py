# server/main.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from server.config import Config
from server.models import db, User, Item

# Создаем приложение
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=["http://localhost:5001", "http://127.0.0.1:5001"])

# Инициализация БД
db.init_app(app)

# WebSocket
socketio = SocketIO(app, cors_allowed_origins="*")

# Импортируем API Blueprints
from server.api.auth import auth_bp
from server.api.characters import characters_bp
from server.api.sessions import sessions_bp
from server.api.items import items_bp
from server.api.game_contexts import contexts_bp
from server.api.logs import logs_bp

# Регистрируем Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(characters_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(items_bp)
app.register_blueprint(contexts_bp)
app.register_blueprint(logs_bp)

# Регистрируем WebSocket обработчики
from server.socket_routes import register_socket_handlers
register_socket_handlers(socketio, db, logs_bp)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


def init_db():
    """Инициализация базы данных и базовых предметов"""
    with app.app_context():
        db.create_all()
        
        # Добавляем базовые предметы
        if Item.query.count() == 0:
            starter_items = [
                Item(name='Рваная рубашка', description='Простая рубашка', 
                     item_type='armor', slot='body', icon='👕'),
                Item(name='Деревянный меч', description='Тренировочный меч', 
                     item_type='weapon', slot='weapon', effects={'strength': 1}, icon='⚔️'),
                Item(name='Кожаные сапоги', description='Обычные сапоги', 
                     item_type='armor', slot='feet', effects={'dexterity': 1}, icon='👢'),
                Item(name='Целительное зелье', description='Восстанавливает 10 HP', 
                     item_type='consumable', is_equippable=False, effects={'heal_hp': 10}, icon='🧪'),
                Item(name='Магическое зелье', description='Восстанавливает 5 MP', 
                     item_type='consumable', is_equippable=False, effects={'heal_mp': 5}, icon='🧪'),
            ]
            
            for item in starter_items:
                db.session.add(item)
            
            db.session.commit()
            print("Базовые предметы добавлены")
        
        # Создаем админа если нет пользователей
        if User.query.count() == 0:
            admin = User(
                username="admin",
                email="admin@example.com",
                is_admin=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Администратор создан: admin / admin123")
        
        print("База данных инициализирована")


if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("Сервер ДПЖ запущен")
    print("Адрес: http://localhost:5000")
    print("=" * 50)
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)