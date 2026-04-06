# db/main.py
from flask import Flask, jsonify, request, g
from db.models import db, User, Character, Session
from db.config import Config
from datetime import datetime
import logging
from werkzeug.security import generate_password_hash, check_password_hash

from db.logger.models_logs import init_logs_models
from db.logger.log_service import init_log_service, LogService
from db.logger.routes_logs import init_logs_routes, logs_bp
from db.game_routes import game_bp, init_game_routes

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db.init_app(app)

# ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ ЛОГОВ
Action, GameLog = init_logs_models(db)
init_log_service(db, Action, GameLog)
init_logs_routes(LogService, Action)

# Регистрация blueprint логов
app.register_blueprint(logs_bp)

# ИНИЦИАЛИЗАЦИЯ ИГРОВЫХ МАРШРУТОВ (исправлено!)
init_game_routes(db, LogService)

# Регистрация blueprint игры
app.register_blueprint(game_bp)

# Создание таблиц и базовых действий
with app.app_context():
    try:
        db.create_all()
        
        base_actions = [
            ('attack', 'Атака противника'),
            ('use_item', 'Использование предмета'),
            ('cast_spell', 'Применение заклинания'),
            ('trade', 'Торговля с другим игроком'),
            ('talk', 'Разговор с NPC или игроком'),
            ('move', 'Перемещение по локации'),
            ('quest_complete', 'Завершение квеста'),
            ('level_up', 'Повышение уровня'),
            ('create_character', 'Создание персонажа'),
            ('join_session', 'Присоединение к сессии'),
            ('create_session', 'Создание сессии'),
            ('gm_action', 'Действие гейммастера'),
            ('login', 'Вход в систему'),
            ('logout', 'Выход из системы'),
            ('open_gm_window', 'Открытие окна ГМ'),
            ('open_player_window', 'Открытие окна игрока'),
            ('gm_update_hp', 'Изменение HP ГМ'),
            ('gm_update_mp', 'Изменение MP ГМ'),
            ('gm_add_item', 'Добавление предмета ГМ'),
            ('player_action', 'Действие игрока'),
            ('global_event', 'Глобальное событие')
        ]
        
        for action_name, description in base_actions:
            action = Action.query.filter_by(action_name=action_name).first()
            if not action:
                db.session.add(Action(action_name=action_name, description=description))
        
        db.session.commit()
        print("Logs system initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize logs: {e}")

# Middleware
@app.before_request
def load_current_user():
    g.current_user = None
    admin = User.query.filter_by(is_admin=True).first()
    if admin:
        g.current_user = admin
    else:
        first_user = User.query.first()
        g.current_user = first_user

@app.cli.command('init-db')
def init_db():
    with app.app_context():
        db.create_all()
        log.info('db successfully created')
        
        if User.query.count() == 0:
            admin = User(
                username="admin",
                email="adminemail@example.com",
                is_admin=True
            )
            admin.set_password("admin123admin321")
            db.session.add(admin)
            db.session.commit()
            log.info('admin user created')

@app.route('/api/users/get_all', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin
    } for u in users])

@app.route('/api/users/create', methods=['POST'])
def create_user():
    data = request.json
    
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Все поля обязательны'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Логин уже занят'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email уже зарегистрирован'}), 400
    
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    log.info(f'user {user.username} created')
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin
    }), 200

@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.json
    login_or_email = data.get('login_or_email')
    password = data.get('password')
    
    if not login_or_email or not password:
        return jsonify({'error': 'Все поля обязательны'}), 400
    
    user = User.query.filter(
        (User.username == login_or_email) | (User.email == login_or_email)
    ).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Неверный логин/email или пароль'}), 401
    
    return jsonify({
        'success': True,
        'message': 'Вход выполнен успешно',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin
        }
    }), 200

@app.route('/api/characters', methods=['GET'])
def get_characters():
    characters = Character.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'data': c.data
    } for c in characters])

@app.route('/api/characters', methods=['POST'])
def create_character():
    data = request.json
    character = Character(
        name=data['name'],
        data=data.get('data', {}),
        user_id=data['user_id']
    )
    db.session.add(character)
    db.session.commit()
    return jsonify({'message': 'Character created', 'id': character.id}), 201

@app.route('/api/characters/my/<int:user_id>', methods=['GET'])
def get_my_characters(user_id):
    characters = Character.query.filter_by(user_id=user_id, is_active=True).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'data': c.data,
        'session_id': c.session_id
    } for c in characters])

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    sessions = Session.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'is_clean': s.is_clean,
        'master_id': s.master_id,
        'created_at': s.created_at.isoformat() if s.created_at else None,
        'vpn_address': s.vpn_address,
        'vpn_port': s.vpn_port
    } for s in sessions])

@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.json
    session = Session(
        name=data['name'],
        master_id=data['master_id'],
        is_clean=data.get('is_clean', True)
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({'message': 'Session created', 'id': session.id}), 201

@app.route('/api/sessions/<int:session_id>/join', methods=['POST'])
def join_session(session_id):
    data = request.json
    session = Session.query.get_or_404(session_id)
    user = User.query.get_or_404(data['user_id'])
    
    if user not in session.participants:
        session.participants.append(user)
        db.session.commit()
    
    return jsonify({'message': 'User joined session'})

@app.route('/api/sessions/my/<int:user_id>', methods=['GET'])
def get_my_sessions(user_id):
    user = User.query.get_or_404(user_id)
    sessions = user.sessions.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'master_id': s.master_id,
        'created_at': s.created_at.isoformat() if s.created_at else None,
        'vpn_address': s.vpn_address,
        'vpn_port': s.vpn_port
    } for s in sessions])

@app.route('/api/sessions/available/<int:user_id>', methods=['GET'])
def get_available_sessions(user_id):
    user = User.query.get_or_404(user_id)
    my_session_ids = [s.id for s in user.sessions.all()]
    sessions = Session.query.filter(~Session.id.in_(my_session_ids)).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'master_id': s.master_id,
        'created_at': s.created_at.isoformat() if s.created_at else None,
        'vpn_address': s.vpn_address,
        'vpn_port': s.vpn_port
    } for s in sessions])

@app.route('/api/sessions/<int:session_id>/vpn', methods=['GET'])
def get_session_vpn(session_id):
    session = Session.query.get_or_404(session_id)
    return jsonify({
        'vpn_address': session.vpn_address,
        'vpn_port': session.vpn_port,
        'session_name': session.name
    })

@app.route('/api/sessions/<int:session_id>/update_vpn', methods=['POST'])
def update_session_vpn(session_id):
    data = request.json
    session = Session.query.get_or_404(session_id)
    
    user = User.query.get(data.get('user_id'))
    if not user or (not user.is_admin and session.master_id != user.id):
        return jsonify({'error': 'Нет прав'}), 403
    
    if 'vpn_address' in data:
        session.vpn_address = data['vpn_address']
    if 'vpn_port' in data:
        session.vpn_port = data['vpn_port']
    
    db.session.commit()
    return jsonify({'message': 'VPN информация обновлена'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/api/characters/<int:character_id>/attach_session', methods=['PUT'])
def attach_character_to_session(character_id):
    """Привязывает персонажа к сессии"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'error': 'Персонаж не найден'}), 404
        
        # Проверяем, не привязан ли уже персонаж
        if character.session_id:
            return jsonify({'error': 'Персонаж уже привязан к другой сессии'}), 400
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Сессия не найдена'}), 404
        
        character.session_id = session_id
        db.session.commit()
        
        return jsonify({'message': 'Character attached to session'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500    

@app.route('/api/characters/<int:character_id>/detach_session', methods=['PUT'])
def detach_character_from_session(character_id):
    """Открепляет персонажа от сессии"""
    try:
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'error': 'Персонаж не найден'}), 404
        
        character.session_id = None
        db.session.commit()
        
        return jsonify({'message': 'Character detached from session'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500