# server/socket_routes.py
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import json

# Хранилище активных соединений
# Структура: session_id -> {
#     'gm_sid': str,
#     'gm_username': str,
#     'players': {
#         user_id: {
#             'sid': str,
#             'username': str,
#             'character_id': int,
#             'character_name': str,
#             'ping': int,
#             'joined_at': str
#         }
#     }
# }
active_connections = {}


def register_socket_handlers(socketio, db, LogService):
    """Регистрирует все обработчики WebSocket событий"""
    
    @socketio.on('connect')
    def handle_connect():
        """Обработчик подключения клиента"""
        print(f'🔌 Client connected: {request.sid}')
        emit('connected', {'status': 'ok', 'sid': request.sid})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Обработчик отключения клиента"""
        print(f'🔌 Client disconnected: {request.sid}')
        
        # Удаляем из всех комнат
        for session_id, room in list(active_connections.items()):
            # Проверяем ГМ
            if room.get('gm_sid') == request.sid:
                del active_connections[session_id]
                emit('gm_disconnected', {
                    'message': 'Гейм мастер покинул сессию'
                }, room=f'session_{session_id}')
                print(f'👋 GM left session {session_id}')
            
            # Проверяем игроков
            for user_id, player_data in list(room.get('players', {}).items()):
                if player_data.get('sid') == request.sid:
                    del active_connections[session_id]['players'][user_id]
                    emit('player_disconnected', {
                        'user_id': user_id,
                        'username': player_data['username'],
                        'character_name': player_data['character_name'],
                        'message': f"{player_data['character_name']} покинул сессию"
                    }, room=f'session_{session_id}')
                    print(f'👋 Player {player_data["username"]} left session {session_id}')
                    break
    
    @socketio.on('register_gm')
    def handle_register_gm(data):
        """Регистрация Гейм Мастера в сессии"""
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        username = data.get('username')
        
        if not session_id or not user_id:
            emit('error', {'message': 'Missing session_id or user_id'})
            return
        
        # Создаем комнату для сессии если её нет
        if session_id not in active_connections:
            active_connections[session_id] = {
                'gm_sid': None,
                'gm_username': None,
                'players': {},
                'created_at': datetime.now().isoformat()
            }
        
        # Проверяем, не занято ли место ГМ
        if active_connections[session_id]['gm_sid'] is not None:
            emit('error', {'message': 'GM already exists in this session'})
            return
        
        # Регистрируем ГМ
        active_connections[session_id]['gm_sid'] = request.sid
        active_connections[session_id]['gm_username'] = username
        
        # Присоединяемся к комнате сессии
        join_room(f'session_{session_id}')
        
        # Логируем
        LogService.log_action(
            'gm_joined',
            performer_id=user_id,
            session_id=session_id,
            details={'username': username}
        )
        
        # Отправляем подтверждение
        emit('gm_registered', {
            'status': 'ok',
            'session_id': session_id,
            'message': f'Вы вошли как ГМ в сессию {session_id}'
        })
        
        # Отправляем текущий список игроков
        players_list = get_players_list(session_id)
        emit('players_list', players_list)
        
        print(f'🎮 GM {username} registered for session {session_id}')
    
    @socketio.on('register_player')
    def handle_register_player(data):
        """Регистрация игрока в сессии"""
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        username = data.get('username')
        character_id = data.get('character_id')
        character_name = data.get('character_name')
        
        if not all([session_id, user_id, username, character_id, character_name]):
            emit('error', {'message': 'Missing required fields'})
            return
        
        # Создаем комнату для сессии если её нет
        if session_id not in active_connections:
            active_connections[session_id] = {
                'gm_sid': None,
                'gm_username': None,
                'players': {},
                'created_at': datetime.now().isoformat()
            }
        
        # Проверяем, не зарегистрирован ли уже игрок
        if user_id in active_connections[session_id]['players']:
            emit('error', {'message': 'Player already registered in this session'})
            return
        
        # Регистрируем игрока
        active_connections[session_id]['players'][user_id] = {
            'sid': request.sid,
            'username': username,
            'character_id': character_id,
            'character_name': character_name,
            'ping': 0,
            'joined_at': datetime.now().isoformat()
        }
        
        # Присоединяемся к комнате сессии
        join_room(f'session_{session_id}')
        
        # Логируем
        LogService.log_action(
            'player_joined',
            performer_id=user_id,
            session_id=session_id,
            character_id=character_id,
            details={'character_name': character_name, 'username': username}
        )
        
        # Отправляем подтверждение игроку
        emit('player_registered', {
            'status': 'ok',
            'session_id': session_id,
            'character_id': character_id,
            'character_name': character_name,
            'message': f'Вы вошли как {character_name} в сессию {session_id}'
        })
        
        # Уведомляем всех в комнате о новом игроке
        emit('player_joined', {
            'user_id': user_id,
            'username': username,
            'character_id': character_id,
            'character_name': character_name,
            'message': f'{character_name} присоединился к сессии!'
        }, room=f'session_{session_id}')
        
        # Отправляем обновленный список игроков ГМ
        if active_connections[session_id]['gm_sid']:
            players_list = get_players_list(session_id)
            emit('players_list', players_list, room=active_connections[session_id]['gm_sid'])
        
        print(f'🎮 Player {username} ({character_name}) joined session {session_id}')
    
    @socketio.on('ping')
    def handle_ping(data):
        """Обработчик пинга для измерения задержки"""
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        client_time = data.get('timestamp')
        
        if session_id and session_id in active_connections:
            # Обновляем пинг для игрока
            if user_id in active_connections[session_id]['players']:
                # Отправляем ответ с временем сервера
                emit('pong', {
                    'client_time': client_time,
                    'server_time': datetime.now().timestamp()
                }, room=request.sid)
    
    @socketio.on('update_ping')
    def handle_update_ping(data):
        """Обновление значения пинга"""
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        ping = data.get('ping', 0)
        
        if session_id in active_connections:
            if user_id in active_connections[session_id]['players']:
                active_connections[session_id]['players'][user_id]['ping'] = ping
                
                # Отправляем обновленный список ГМ
                if active_connections[session_id]['gm_sid']:
                    players_list = get_players_list(session_id)
                    emit('players_list', players_list, room=active_connections[session_id]['gm_sid'])
    
    @socketio.on('send_chat')
    def handle_send_chat(data):
        """Обработчик отправки сообщения в чат"""
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        username = data.get('username')
        character_name = data.get('character_name')
        message = data.get('message', '').strip()
        action_type = data.get('action_type', 'chat')
        
        if not message:
            return
        
        if not session_id or session_id not in active_connections:
            emit('error', {'message': 'Invalid session'})
            return
        
        # Определяем отправителя
        is_gm = (active_connections[session_id].get('gm_sid') == request.sid)
        
        # Если отправитель не ГМ, проверяем что он зарегистрирован
        if not is_gm:
            player_found = False
            for uid, player in active_connections[session_id]['players'].items():
                if player['sid'] == request.sid:
                    user_id = uid
                    username = player['username']
                    character_name = player['character_name']
                    player_found = True
                    break
            if not player_found:
                emit('error', {'message': 'Not registered in this session'})
                return
        
        # Обрабатываем специальные действия
        if action_type == 'dice':
            # Бросок кубика
            import re, random
            match = re.match(r'(\d+)d(\d+)(?:[+-](\d+))?', message)
            if match:
                num = int(match.group(1))
                sides = int(match.group(2))
                modifier = int(match.group(3)) if match.group(3) else 0
                
                rolls = [random.randint(1, sides) for _ in range(min(num, 10))]  # Ограничиваем 10 кубиками
                total = sum(rolls) + modifier
                
                message = f"🎲 Бросок {num}d{sides}" + (f"+{modifier}" if modifier else "") + f": {rolls} = {total}"
        
        # Логируем сообщение
        LogService.log_action(
            'chat_message',
            performer_id=user_id,
            session_id=session_id,
            details={
                'message': message,
                'action_type': action_type,
                'is_gm': is_gm
            }
        )
        
        # Отправляем сообщение всем в комнате
        emit('chat_message', {
            'user_id': user_id,
            'username': username,
            'character_name': character_name,
            'message': message,
            'action_type': action_type,
            'is_gm': is_gm,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=f'session_{session_id}')
        
        print(f'💬 Chat in session {session_id}: {character_name or username}: {message[:50]}')
    
    @socketio.on('gm_update_character')
    def handle_gm_update_character(data):
        """ГМ обновляет характеристики персонажа"""
        session_id = data.get('session_id')
        character_id = data.get('character_id')
        updates = data.get('updates', {})
        
        # Проверяем, что отправитель - ГМ этой сессии
        if session_id not in active_connections:
            emit('error', {'message': 'Session not found'})
            return
        
        if active_connections[session_id].get('gm_sid') != request.sid:
            emit('error', {'message': 'Only GM can update characters'})
            return
        
        # Обновляем в БД
        from server.models import Character
        character = Character.query.get(character_id)
        if not character:
            emit('error', {'message': 'Character not found'})
            return
        
        # Проверяем, что персонаж принадлежит этой сессии
        if character.session_id != session_id:
            emit('error', {'message': 'Character not in this session'})
            return
        
        # Применяем обновления
        for key, value in updates.items():
            if hasattr(character, key):
                setattr(character, key, value)
        
        db.session.commit()
        
        # Логируем
        LogService.log_action(
            'gm_update_character',
            performer_id=character.user_id,
            session_id=session_id,
            character_id=character_id,
            details={'updates': updates}
        )
        
        # Отправляем обновление всем в комнате
        emit('character_updated', {
            'character_id': character_id,
            'character_name': character.name,
            'updates': updates,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=f'session_{session_id}')
        
        print(f'📊 GM updated character {character.name}: {updates}')
    
    @socketio.on('gm_add_item')
    def handle_gm_add_item(data):
        """ГМ добавляет предмет персонажу"""
        session_id = data.get('session_id')
        character_id = data.get('character_id')
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        # Проверяем права
        if session_id not in active_connections:
            emit('error', {'message': 'Session not found'})
            return
        
        if active_connections[session_id].get('gm_sid') != request.sid:
            emit('error', {'message': 'Only GM can add items'})
            return
        
        from server.models import CharacterItem
        existing = CharacterItem.query.filter_by(character_id=character_id, item_id=item_id).first()
        
        if existing:
            existing.quantity += quantity
        else:
            existing = CharacterItem(character_id=character_id, item_id=item_id, quantity=quantity)
            db.session.add(existing)
        
        db.session.commit()
        
        # Логируем
        LogService.log_action(
            'gm_add_item',
            performer_id=None,  # ГМ
            session_id=session_id,
            character_id=character_id,
            details={'item_id': item_id, 'quantity': quantity}
        )
        
        # Уведомляем всех
        emit('item_added', {
            'character_id': character_id,
            'item_id': item_id,
            'quantity': quantity,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=f'session_{session_id}')
        
        print(f'📦 GM added item {item_id} x{quantity} to character {character_id}')
    
    @socketio.on('gm_remove_item')
    def handle_gm_remove_item(data):
        """ГМ удаляет предмет у персонажа"""
        session_id = data.get('session_id')
        character_id = data.get('character_id')
        item_id = data.get('item_id')
        
        # Проверяем права
        if session_id not in active_connections:
            emit('error', {'message': 'Session not found'})
            return
        
        if active_connections[session_id].get('gm_sid') != request.sid:
            emit('error', {'message': 'Only GM can remove items'})
            return
        
        from server.models import CharacterItem
        item = CharacterItem.query.filter_by(character_id=character_id, item_id=item_id).first()
        
        if item:
            if item.quantity > 1:
                item.quantity -= 1
            else:
                db.session.delete(item)
            db.session.commit()
        
        # Логируем
        LogService.log_action(
            'gm_remove_item',
            performer_id=None,
            session_id=session_id,
            character_id=character_id,
            details={'item_id': item_id}
        )
        
        # Уведомляем всех
        emit('item_removed', {
            'character_id': character_id,
            'item_id': item_id,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=f'session_{session_id}')
        
        print(f'🗑 GM removed item {item_id} from character {character_id}')
    
    @socketio.on('add_game_object')
    def handle_add_game_object(data):
        """Добавление игрового объекта (локация, NPC, монстр)"""
        session_id = data.get('session_id')
        obj_type = data.get('type')  # location, npc, monster
        name = data.get('name')
        description = data.get('description', '')
        obj_data = data.get('data', {})
        
        # Проверяем права
        if session_id not in active_connections:
            emit('error', {'message': 'Session not found'})
            return
        
        if active_connections[session_id].get('gm_sid') != request.sid:
            emit('error', {'message': 'Only GM can add game objects'})
            return
        
        from server.models import GameContext
        context = GameContext(
            session_id=session_id,
            context_type=obj_type,
            name=name,
            description=description,
            data=obj_data
        )
        db.session.add(context)
        db.session.commit()
        
        # Логируем
        LogService.log_action(
            'add_game_object',
            performer_id=None,
            session_id=session_id,
            details={'type': obj_type, 'name': name}
        )
        
        # Уведомляем всех
        emit('game_object_added', {
            'type': obj_type,
            'name': name,
            'description': description,
            'data': context.to_dict(),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=f'session_{session_id}')
        
        print(f'📍 GM added {obj_type}: {name}')
    
    @socketio.on('get_players')
    def handle_get_players(data):
        """Запрос списка игроков"""
        session_id = data.get('session_id')
        
        if session_id in active_connections:
            players_list = get_players_list(session_id)
            emit('players_list', players_list, room=request.sid)
    
    @socketio.on('get_game_objects')
    def handle_get_game_objects(data):
        """Запрос списка игровых объектов"""
        session_id = data.get('session_id')
        
        if session_id:
            from server.models import GameContext
            contexts = GameContext.query.filter_by(session_id=session_id).all()
            objects = {
                'locations': [],
                'npcs': [],
                'monsters': []
            }
            
            for ctx in contexts:
                if ctx.context_type == 'location':
                    objects['locations'].append(ctx.to_dict())
                elif ctx.context_type == 'npc':
                    objects['npcs'].append(ctx.to_dict())
                elif ctx.context_type == 'monster':
                    objects['monsters'].append(ctx.to_dict())
            
            emit('game_objects_list', objects, room=request.sid)
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        """Выход из сессии"""
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        
        if session_id not in active_connections:
            emit('error', {'message': 'Session not found'})
            return
        
        # Проверяем, ГМ или игрок
        if active_connections[session_id].get('gm_sid') == request.sid:
            # ГМ выходит
            del active_connections[session_id]
            emit('gm_left', {'message': 'GM left the session'}, room=f'session_{session_id}')
            leave_room(f'session_{session_id}')
        else:
            # Игрок выходит
            for uid, player in active_connections[session_id]['players'].items():
                if player['sid'] == request.sid:
                    del active_connections[session_id]['players'][uid]
                    emit('player_left', {
                        'user_id': uid,
                        'character_name': player['character_name']
                    }, room=f'session_{session_id}')
                    leave_room(f'session_{session_id}')
                    break
        
        emit('left_session', {'status': 'ok'}, room=request.sid)
        print(f'👋 User left session {session_id}')


def get_players_list(session_id):
    """Возвращает список игроков в сессии"""
    if session_id not in active_connections:
        return {'players': [], 'gm_username': None}
    
    players = []
    for user_id, data in active_connections[session_id]['players'].items():
        players.append({
            'user_id': user_id,
            'username': data['username'],
            'character_id': data['character_id'],
            'character_name': data['character_name'],
            'ping': data.get('ping', 0),
            'joined_at': data.get('joined_at')
        })
    
    return {
        'players': players,
        'gm_username': active_connections[session_id].get('gm_username'),
        'count': len(players)
    }