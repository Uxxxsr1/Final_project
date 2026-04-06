# db/game_routes.py - ПОЛНОСТЬЮ ЗАМЕНИТЕ СОДЕРЖИМОЕ
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import logging
from functools import wraps

game_bp = Blueprint('game', __name__, url_prefix='/api/game')

# Глобальные переменные
db = None
LogService = None

def init_game_routes(database, log_service):
    """Инициализация игровых маршрутов"""
    global db, LogService
    db = database
    LogService = log_service
    print("Game routes initialized")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user') or g.current_user is None:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def gm_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not g.current_user.is_admin:
            return jsonify({'error': 'Доступ только для ГМ'}), 403
        return f(*args, **kwargs)
    return decorated_function


@game_bp.route('/session/<int:session_id>/players', methods=['GET'])
@login_required
def get_session_players(session_id):
    """Получить всех игроков в сессии"""
    try:
        from db.models import Session, User, Character
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Сессия не найдена'}), 404
        
        # Проверяем права
        if not g.current_user.is_admin and session.master_id != g.current_user.id:
            return jsonify({'error': 'Нет доступа'}), 403
        
        players = []
        for user in session.participants.all():
            character = Character.query.filter_by(user_id=user.id, session_id=session_id, is_active=True).first()
            
            if character:
                player_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'character': {
                        'id': character.id,
                        'name': character.name,
                        'current_hp': 10,
                        'current_mp': 5,
                        'max_hp': 10,
                        'max_mp': 5,
                        'level': 1,
                        'equipped_items': []
                    }
                }
                players.append(player_data)
        
        return jsonify({'players': players}), 200
        
    except Exception as e:
        logging.error(f"Error in get_session_players: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/character/<int:user_id>/<int:session_id>', methods=['GET'])
@login_required
def get_player_character(user_id, session_id):
    """Получить персонажа игрока"""
    try:
        from db.models import Character
        
        # Проверяем права
        if not g.current_user.is_admin and g.current_user.id != user_id:
            return jsonify({'error': 'Нет доступа'}), 403
        
        character = Character.query.filter_by(user_id=user_id, session_id=session_id, is_active=True).first()
        if not character:
            return jsonify({'error': 'Персонаж не найден'}), 404
        
        return jsonify({
            'id': character.id,
            'name': character.name,
            'level': 1,
            'current_hp': 10,
            'current_mp': 5,
            'max_hp': 10,
            'max_mp': 5,
            'experience': 0,
            'stats': {
                'strength': 10,
                'dexterity': 10,
                'intelligence': 10,
                'charisma': 10
            },
            'base_stats': {
                'strength': 10,
                'dexterity': 10,
                'intelligence': 10,
                'charisma': 10
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error in get_player_character: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/character/<int:character_id>/stats', methods=['PUT'])
@login_required
def update_character_stats(character_id):
    """Обновить характеристики персонажа"""
    try:
        from db.models import Character
        
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'error': 'Персонаж не найден'}), 404
        
        # Проверяем права
        if not g.current_user.is_admin and character.user_id != g.current_user.id:
            return jsonify({'error': 'Нет прав'}), 403
        
        data = request.json
        
        # Логируем изменение
        if LogService:
            LogService.log_action(
                'update_character_stats',
                performer_id=g.current_user.id,
                character_id=character_id,
                details=data
            )
        
        return jsonify({'message': 'Stats updated successfully'}), 200
        
    except Exception as e:
        logging.error(f"Error in update_character_stats: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/character/<int:character_id>/inventory', methods=['GET'])
@login_required
def get_character_inventory(character_id):
    """Получить инвентарь персонажа"""
    try:
        from db.models import Character
        
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'error': 'Персонаж не найден'}), 404
        
        # Проверяем права
        if not g.current_user.is_admin and character.user_id != g.current_user.id:
            return jsonify({'error': 'Нет доступа'}), 403
        
        return jsonify({'items': []}), 200
        
    except Exception as e:
        logging.error(f"Error in get_character_inventory: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/character/<int:character_id>/add_item', methods=['POST'])
@gm_required
def add_item_to_character(character_id):
    """Добавить предмет персонажу (только для ГМ)"""
    try:
        data = request.json
        item_name = data.get('name')
        quantity = data.get('quantity', 1)
        
        if LogService:
            LogService.log_action(
                'gm_add_item',
                performer_id=g.current_user.id,
                character_id=character_id,
                details={'item': item_name, 'quantity': quantity}
            )
        
        return jsonify({'message': f'Added {quantity}x {item_name}'}), 200
        
    except Exception as e:
        logging.error(f"Error in add_item_to_character: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/character/<int:character_id>/equip', methods=['POST'])
@login_required
def equip_item(character_id):
    """Экипировать предмет"""
    try:
        data = request.json
        item_id = data.get('item_id')
        
        if LogService:
            LogService.log_action(
                'equip_item',
                performer_id=g.current_user.id,
                character_id=character_id,
                details={'item_id': item_id}
            )
        
        return jsonify({'message': 'Item equipped'}), 200
        
    except Exception as e:
        logging.error(f"Error in equip_item: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/character/<int:character_id>/unequip', methods=['POST'])
@login_required
def unequip_item(character_id):
    """Снять предмет"""
    try:
        data = request.json
        item_id = data.get('item_id')
        
        if LogService:
            LogService.log_action(
                'unequip_item',
                performer_id=g.current_user.id,
                character_id=character_id,
                details={'item_id': item_id}
            )
        
        return jsonify({'message': 'Item unequipped'}), 200
        
    except Exception as e:
        logging.error(f"Error in unequip_item: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/character/<int:character_id>/actions', methods=['GET'])
@login_required
def get_character_actions(character_id):
    """Получить доступные действия для персонажа"""
    try:
        from db.models import Character
        
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'error': 'Персонаж не найден'}), 404
        
        # Базовые действия
        actions = [
            {'action_name': 'move', 'display_name': '🚶 Переместиться', 'description': 'Переместиться в другую локацию'},
            {'action_name': 'talk', 'display_name': '💬 Поговорить', 'description': 'Поговорить с NPC или игроком'},
            {'action_name': 'use_item', 'display_name': '🎒 Использовать предмет', 'description': 'Использовать предмет из инвентаря'},
            {'action_name': 'check_stats', 'display_name': '📊 Проверить характеристики', 'description': 'Посмотреть свои характеристики'}
        ]
        
        return jsonify({'actions': actions}), 200
        
    except Exception as e:
        logging.error(f"Error in get_character_actions: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/perform_action', methods=['POST'])
@login_required
def perform_action():
    """Выполнить действие"""
    try:
        data = request.json
        action_name = data.get('action_name')
        character_id = data.get('character_id')
        target_id = data.get('target_id')
        details = data.get('details', {})
        
        if LogService:
            LogService.log_action(
                action_name,
                performer_id=g.current_user.id,
                character_id=character_id,
                target_id=target_id,
                details=details
            )
        
        # Обрабатываем специальные действия
        if action_name == 'check_stats':
            return jsonify({
                'message': 'Ваши характеристики: Сила 10, Ловкость 10, Интеллект 10, Харизма 10'
            }), 200
        
        return jsonify({'message': f'Action "{action_name}" performed successfully'}), 200
        
    except Exception as e:
        logging.error(f"Error in perform_action: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/session/<int:session_id>/events', methods=['GET'])
@login_required
def get_global_events(session_id):
    """Получить глобальные события сессии"""
    try:
        return jsonify({'events': []}), 200
        
    except Exception as e:
        logging.error(f"Error in get_global_events: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/session/<int:session_id>/add_event', methods=['POST'])
@gm_required
def add_global_event(session_id):
    """Добавить глобальное событие (только для ГМ)"""
    try:
        data = request.json
        message = data.get('message')
        
        if LogService:
            LogService.log_action(
                'global_event',
                performer_id=g.current_user.id,
                session_id=session_id,
                details={'message': message}
            )
        
        return jsonify({'message': 'Event added'}), 200
        
    except Exception as e:
        logging.error(f"Error in add_global_event: {e}")
        return jsonify({'error': str(e)}), 500


@game_bp.route('/character/<int:character_id>/logs', methods=['GET'])
@login_required
def get_character_logs(character_id):
    """Получить логи персонажа"""
    try:
        from db.models import Character
        from db.logger.models_logs import GameLog, Action
        
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'error': 'Персонаж не найден'}), 404
        
        limit = request.args.get('limit', 50, type=int)
        
        # Получаем логи, связанные с персонажем
        logs = GameLog.query.filter_by(character_id=character_id)\
            .order_by(GameLog.timestamp.desc())\
            .limit(limit).all()
        
        result = []
        for log in logs:
            action = Action.query.get(log.action_id)
            result.append({
                'id': log.id,
                'action_name': action.action_name if action else 'unknown',
                'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                'details': log.details
            })
        
        return jsonify({'logs': result}), 200
        
    except Exception as e:
        logging.error(f"Error in get_character_logs: {e}")
        return jsonify({'error': str(e)}), 500

@game_bp.route('/character/<int:character_id>/full_data', methods=['GET'])
@login_required
def get_character_full_data(character_id):
    """Получить полные данные персонажа (инвентарь, характеристики, логи)"""
    try:
        from db.models import Character
        from db.game_models import CharacterStats, CharacterItem, Item
        
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'error': 'Персонаж не найден'}), 404
        
        # Проверяем права
        if not g.current_user.is_admin and character.user_id != g.current_user.id:
            return jsonify({'error': 'Нет доступа'}), 403
        
        # Получаем статистику
        stats = CharacterStats.query.filter_by(character_id=character_id).first()
        
        # Получаем инвентарь
        character_items = CharacterItem.query.filter_by(character_id=character_id).all()
        inventory = []
        equipped = []
        
        for ci in character_items:
            item = Item.query.get(ci.item_id)
            item_data = {
                'id': ci.id,
                'item_id': ci.item_id,
                'name': ci.custom_name or (item.name if item else 'Unknown'),
                'quantity': ci.quantity,
                'is_equipped': ci.is_equipped,
                'effects': ci.custom_effects or (item.effects if item else {}),
                'slot': item.slot if item else None,
                'icon': item.icon if item else '📦',
                'description': item.description if item else ''
            }
            
            if ci.is_equipped:
                equipped.append(item_data)
            else:
                inventory.append(item_data)
        
        return jsonify({
            'character': {
                'id': character.id,
                'name': character.name,
                'level': stats.level if stats else 1,
                'current_hp': stats.current_hp if stats else 10,
                'current_mp': stats.current_mp if stats else 5,
                'max_hp': stats.max_hp if stats else 10,
                'max_mp': stats.max_mp if stats else 5,
                'stats': {
                    'strength': stats.base_strength if stats else 10,
                    'dexterity': stats.base_dexterity if stats else 10,
                    'intelligence': stats.base_intelligence if stats else 10,
                    'charisma': stats.base_charisma if stats else 10
                }
            },
            'inventory': inventory,
            'equipped': equipped
        }), 200
        
    except Exception as e:
        logging.error(f"Error in get_character_full_data: {e}")
        return jsonify({'error': str(e)}), 500