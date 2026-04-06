# create_logger.py
import os

def create_logger_files():
    """Создает все файлы системы логов"""
    
    # Создаем папку logger
    os.makedirs("db/logger", exist_ok=True)
    
    # Файл: db/logger/__init__.py
    with open("db/logger/__init__.py", "w", encoding="utf-8") as f:
        f.write("""# db/logger/__init__.py
from db.logger.models_logs import init_logs_models, Action, GameLog
from db.logger.log_service import init_log_service, LogService
from db.logger.routes_logs import init_logs_routes, logs_bp

__all__ = [
    'init_logs_models',
    'Action',
    'GameLog',
    'init_log_service',
    'LogService',
    'init_logs_routes',
    'logs_bp'
]
""")
    
    # Файл: db/logger/models_logs.py
    with open("db/logger/models_logs.py", "w", encoding="utf-8") as f:
        f.write("""# db/logger/models_logs.py
from datetime import datetime

# Глобальные переменные для моделей
Action = None
GameLog = None

def init_logs_models(database):
    \"\"\"Инициализация моделей логов с существующей БД\"\"\"
    global Action, GameLog
    
    class ActionModel(database.Model):
        __tablename__ = 'actions'
        
        id = database.Column(database.Integer, primary_key=True)
        action_name = database.Column(database.String(100), nullable=False, unique=True)
        description = database.Column(database.Text)
        is_active = database.Column(database.Boolean, default=True)
        created_at = database.Column(database.DateTime, default=datetime.utcnow)
        
        def __repr__(self):
            return f'<Action {self.action_name}>'
    
    class GameLogModel(database.Model):
        __tablename__ = 'game_logs'
        
        id = database.Column(database.Integer, primary_key=True)
        action_id = database.Column(database.Integer, database.ForeignKey('actions.id'), nullable=False)
        performer_id = database.Column(database.Integer, database.ForeignKey('users.id'), nullable=False)
        target_id = database.Column(database.Integer, database.ForeignKey('users.id'), nullable=True)
        character_id = database.Column(database.Integer, database.ForeignKey('characters.id'), nullable=True)
        session_id = database.Column(database.Integer, database.ForeignKey('sessions.id'), nullable=True)
        details = database.Column(database.JSON, default={})
        timestamp = database.Column(database.DateTime, default=datetime.utcnow, index=True)
        
        def __repr__(self):
            return f'<GameLog {self.id}>'
        
        def to_dict(self):
            from db.models import User, Character, Session
            
            action_name = None
            if self.action_id:
                action = Action.query.get(self.action_id)
                action_name = action.action_name if action else None
            
            performer_name = None
            if self.performer_id:
                performer = User.query.get(self.performer_id)
                performer_name = performer.username if performer else None
            
            target_name = None
            if self.target_id:
                target = User.query.get(self.target_id)
                target_name = target.username if target else None
            
            character_name = None
            if self.character_id:
                character = Character.query.get(self.character_id)
                character_name = character.name if character else None
            
            session_name = None
            if self.session_id:
                session = Session.query.get(self.session_id)
                session_name = session.name if session else None
            
            return {
                'id': self.id,
                'action_id': self.action_id,
                'action_name': action_name,
                'performer_id': self.performer_id,
                'performer_name': performer_name,
                'target_id': self.target_id,
                'target_name': target_name,
                'character_id': self.character_id,
                'character_name': character_name,
                'session_id': self.session_id,
                'session_name': session_name,
                'details': self.details,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None
            }
    
    Action = ActionModel
    GameLog = GameLogModel
    
    return Action, GameLog
""")
    
    # Файл: db/logger/log_service.py
    with open("db/logger/log_service.py", "w", encoding="utf-8") as f:
        f.write("""# db/logger/log_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import or_, and_

# Глобальные переменные
Action = None
GameLog = None
db = None

def init_log_service(database, action_model, gamelog_model):
    \"\"\"Инициализация сервиса логов\"\"\"
    global db, Action, GameLog
    db = database
    Action = action_model
    GameLog = gamelog_model

class LogService:
    \"\"\"Сервис для управления логами действий\"\"\"
    
    @staticmethod
    def get_or_create_action(action_name: str, description: str = None):
        \"\"\"Получить существующее действие или создать новое\"\"\"
        action = Action.query.filter_by(action_name=action_name).first()
        if not action:
            action = Action(action_name=action_name, description=description)
            db.session.add(action)
            db.session.commit()
        elif description and not action.description:
            action.description = description
            db.session.commit()
        return action
    
    @staticmethod
    def log_action(
        action_name: str,
        performer_id: int,
        target_id: Optional[int] = None,
        character_id: Optional[int] = None,
        session_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        \"\"\"Записать действие в лог\"\"\"
        action = LogService.get_or_create_action(action_name)
        
        game_log = GameLog(
            action_id=action.id,
            performer_id=performer_id,
            target_id=target_id,
            character_id=character_id,
            session_id=session_id,
            details=details or {}
        )
        
        db.session.add(game_log)
        db.session.commit()
        
        return game_log
    
    @staticmethod
    def get_logs_for_gamemaster(
        limit: int = 100,
        offset: int = 0,
        action_name: Optional[str] = None,
        player_id: Optional[int] = None,
        session_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        \"\"\"Получить логи для гейммастера\"\"\"
        query = GameLog.query
        
        if action_name:
            action = Action.query.filter_by(action_name=action_name).first()
            if action:
                query = query.filter(GameLog.action_id == action.id)
        
        if player_id:
            query = query.filter(
                or_(
                    GameLog.performer_id == player_id,
                    GameLog.target_id == player_id
                )
            )
        
        if session_id:
            query = query.filter(GameLog.session_id == session_id)
        
        if start_date:
            query = query.filter(GameLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(GameLog.timestamp <= end_date)
        
        return query.order_by(GameLog.timestamp.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_logs_for_player(
        player_id: int,
        limit: int = 100,
        offset: int = 0,
        only_own_actions: bool = True
    ):
        \"\"\"Получить логи для конкретного игрока\"\"\"
        if only_own_actions:
            query = GameLog.query.filter(
                or_(
                    GameLog.performer_id == player_id,
                    GameLog.target_id == player_id
                )
            )
        else:
            query = GameLog.query
        
        return query.order_by(GameLog.timestamp.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_player_stats(player_id: int) -> Dict[str, Any]:
        \"\"\"Получить статистику действий для игрока\"\"\"
        player_actions = GameLog.query.filter(
            or_(
                GameLog.performer_id == player_id,
                GameLog.target_id == player_id
            )
        ).all()
        
        stats = {
            'total_actions': len(player_actions),
            'actions_performed': 0,
            'actions_received': 0,
            'by_action_type': {}
        }
        
        for log in player_actions:
            if log.performer_id == player_id:
                stats['actions_performed'] += 1
            if log.target_id == player_id:
                stats['actions_received'] += 1
            
            action = Action.query.get(log.action_id)
            action_name = action.action_name if action else 'unknown'
            
            if action_name not in stats['by_action_type']:
                stats['by_action_type'][action_name] = 0
            stats['by_action_type'][action_name] += 1
        
        return stats
    
    @staticmethod
    def get_session_logs(session_id: int, limit: int = 100):
        \"\"\"Получить логи по сессии\"\"\"
        return GameLog.query.filter_by(session_id=session_id)\\
            .order_by(GameLog.timestamp.desc())\\
            .limit(limit).all()
    
    @staticmethod
    def get_character_logs(character_id: int, limit: int = 100):
        \"\"\"Получить логи по персонажу\"\"\"
        return GameLog.query.filter_by(character_id=character_id)\\
            .order_by(GameLog.timestamp.desc())\\
            .limit(limit).all()
""")
    
    # Файл: db/logger/routes_logs.py
    with open("db/logger/routes_logs.py", "w", encoding="utf-8") as f:
        f.write("""# db/logger/routes_logs.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request, jsonify, g
from datetime import datetime
import logging
from functools import wraps
from db.logger.models_logs import Action, GameLog

# Будет инициализировано позже
log_service = None

def init_logs_routes(service, action_model):
    \"\"\"Инициализация маршрутов логов\"\"\"
    global log_service, Action
    log_service = service
    Action = action_model

logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

# ============ ДЕКОРАТОРЫ ============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user') or g.current_user is None:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def gamemaster_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not g.current_user.is_admin:
            return jsonify({'error': 'Доступ только для гейммастера'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============ МАРШРУТЫ ============

@logs_bp.route('/log', methods=['POST'])
@login_required
def create_log():
    \"\"\"Создать запись в логе\"\"\"
    try:
        data = request.get_json()
        
        if not data or 'action_name' not in data:
            return jsonify({'error': 'action_name is required'}), 400
        
        performer_id = data.get('performer_id', g.current_user.id)
        
        if performer_id != g.current_user.id and not g.current_user.is_admin:
            return jsonify({'error': 'Можно создавать логи только от своего имени'}), 403
        
        if data.get('target_id'):
            from db.models import User
            target = User.query.get(data['target_id'])
            if not target:
                return jsonify({'error': 'Цель не найдена'}), 404
        
        if data.get('character_id'):
            from db.models import Character
            character = Character.query.get(data['character_id'])
            if not character:
                return jsonify({'error': 'Персонаж не найден'}), 404
            if character.user_id != g.current_user.id and not g.current_user.is_admin:
                return jsonify({'error': 'Нет прав на этого персонажа'}), 403
        
        log_entry = log_service.log_action(
            action_name=data['action_name'],
            performer_id=performer_id,
            target_id=data.get('target_id'),
            character_id=data.get('character_id'),
            session_id=data.get('session_id'),
            details=data.get('details', {})
        )
        
        return jsonify({
            'message': 'Действие записано',
            'log_id': log_entry.id,
            'log': log_entry.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Error in create_log: {e}")
        return jsonify({'error': str(e)}), 500

@logs_bp.route('/my-logs', methods=['GET'])
@login_required
def get_my_logs():
    \"\"\"Получить свои логи\"\"\"
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        logs = log_service.get_logs_for_player(
            player_id=g.current_user.id,
            limit=limit,
            offset=offset,
            only_own_actions=True
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in logs],
            'count': len(logs)
        }), 200
        
    except Exception as e:
        logging.error(f"Error in get_my_logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@logs_bp.route('/my-stats', methods=['GET'])
@login_required
def get_my_stats():
    \"\"\"Получить статистику\"\"\"
    try:
        stats = log_service.get_player_stats(g.current_user.id)
        stats['player_name'] = g.current_user.username
        return jsonify(stats), 200
        
    except Exception as e:
        logging.error(f"Error in get_my_stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@logs_bp.route('/gamemaster/all', methods=['GET'])
@gamemaster_required
def gm_get_all_logs():
    \"\"\"Гейммастер: все логи\"\"\"
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        action_name = request.args.get('action_name')
        player_id = request.args.get('player_id', type=int)
        session_id = request.args.get('session_id', type=int)
        
        logs = log_service.get_logs_for_gamemaster(
            limit=limit,
            offset=offset,
            action_name=action_name,
            player_id=player_id,
            session_id=session_id
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in logs],
            'count': len(logs)
        }), 200
        
    except Exception as e:
        logging.error(f"Error in gm_get_all_logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@logs_bp.route('/gamemaster/player/<int:player_id>', methods=['GET'])
@gamemaster_required
def gm_get_player_logs(player_id):
    \"\"\"Гейммастер: логи игрока\"\"\"
    try:
        from db.models import User
        player = User.query.get(player_id)
        if not player:
            return jsonify({'error': 'Игрок не найден'}), 404
        
        logs = log_service.get_logs_for_player(
            player_id=player_id,
            only_own_actions=False
        )
        
        return jsonify({
            'player_id': player_id,
            'player_name': player.username,
            'logs': [log.to_dict() for log in logs],
            'count': len(logs)
        }), 200
        
    except Exception as e:
        logging.error(f"Error in gm_get_player_logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@logs_bp.route('/session/<int:session_id>/logs', methods=['GET'])
@login_required
def get_session_logs(session_id):
    \"\"\"Получить логи сессии\"\"\"
    try:
        from db.models import Session
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Сессия не найдена'}), 404
        
        if not g.current_user.is_admin:
            is_master = session.master_id == g.current_user.id
            is_participant = session.participants.filter_by(id=g.current_user.id).first() is not None
            
            if not (is_master or is_participant):
                return jsonify({'error': 'Нет доступа к этой сессии'}), 403
            
            logs = log_service.get_logs_for_player(
                player_id=g.current_user.id,
                only_own_actions=True
            )
            logs = [log for log in logs if log.session_id == session_id]
        else:
            logs = log_service.get_session_logs(session_id)
        
        return jsonify({
            'session_id': session_id,
            'session_name': session.name,
            'logs': [log.to_dict() for log in logs],
            'count': len(logs)
        }), 200
        
    except Exception as e:
        logging.error(f"Error in get_session_logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@logs_bp.route('/actions', methods=['GET'])
def get_available_actions():
    \"\"\"Получить список действий\"\"\"
    try:
        actions = Action.query.filter_by(is_active=True).all()
        return jsonify({
            'actions': [
                {
                    'id': a.id,
                    'action_name': a.action_name,
                    'description': a.description
                }
                for a in actions
            ]
        }), 200
        
    except Exception as e:
        logging.error(f"Error in get_available_actions: {e}")
        return jsonify({'error': 'Internal server error'}), 500
""")
    
    # Файл: db/logger/init_logs.py
    with open("db/logger/init_logs.py", "w", encoding="utf-8") as f:
        f.write("""# db/logger/init_logs.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.main import app
from db.models import db

def init_logs_tables():
    \"\"\"Создает таблицы логов\"\"\"
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
""")
    
    print("✅ Все файлы системы логов созданы!")
    print("\nСозданные файлы:")
    print("  - db/logger/__init__.py")
    print("  - db/logger/models_logs.py")
    print("  - db/logger/log_service.py")
    print("  - db/logger/routes_logs.py")
    print("  - db/logger/init_logs.py")

if __name__ == "__main__":
    create_logger_files()