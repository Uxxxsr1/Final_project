# db/logger/routes_logs.py
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
    """Инициализация маршрутов логов"""
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
    """Создать запись в логе"""
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
    """Получить свои логи"""
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
    """Получить статистику"""
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
    """Гейммастер: все логи"""
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
    """Гейммастер: логи игрока"""
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
    """Получить логи сессии"""
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
    """Получить список действий"""
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
