# client/socket_client.py
import socketio
from typing import Optional, Dict, Any, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

SOCKET_URL = "http://localhost:5000"


class SocketClient(QObject):
    # Сигналы для обновления UI
    connected_signal = pyqtSignal()
    disconnected_signal = pyqtSignal()
    chat_signal = pyqtSignal(dict)
    players_list_signal = pyqtSignal(dict)
    character_updated_signal = pyqtSignal(dict)
    item_added_signal = pyqtSignal(dict)
    item_removed_signal = pyqtSignal(dict)
    game_object_added_signal = pyqtSignal(dict)
    player_joined_signal = pyqtSignal(dict)
    player_disconnected_signal = pyqtSignal(dict)
    gm_disconnected_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.sio = socketio.Client()
        self.is_connected = False
        self.current_session_id = None
        self.current_user_id = None
        self.current_character_id = None
        self.is_gm = False
        
        # Таймер для пинга
        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self.send_ping)
        self.ping_timer.setInterval(5000)  # Каждые 5 секунд
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.sio.event
        def connect():
            self.is_connected = True
            self.connected_signal.emit()
            print("Connected to server")
        
        @self.sio.event
        def disconnect():
            self.is_connected = False
            self.ping_timer.stop()
            self.disconnected_signal.emit()
            print("Disconnected from server")
        
        @self.sio.on('chat_message')
        def on_chat_message(data):
            self.chat_signal.emit(data)
        
        @self.sio.on('players_list')
        def on_players_list(data):
            self.players_list_signal.emit(data)
        
        @self.sio.on('character_updated')
        def on_character_updated(data):
            self.character_updated_signal.emit(data)
        
        @self.sio.on('item_added')
        def on_item_added(data):
            self.item_added_signal.emit(data)
        
        @self.sio.on('item_removed')
        def on_item_removed(data):
            self.item_removed_signal.emit(data)
        
        @self.sio.on('game_object_added')
        def on_game_object_added(data):
            self.game_object_added_signal.emit(data)
        
        @self.sio.on('player_joined')
        def on_player_joined(data):
            self.player_joined_signal.emit(data)
        
        @self.sio.on('player_disconnected')
        def on_player_disconnected(data):
            self.player_disconnected_signal.emit(data)
        
        @self.sio.on('gm_disconnected')
        def on_gm_disconnected(data):
            self.gm_disconnected_signal.emit()
    
    def connect_to_server(self, server_ip: str, port: int = 5000):
        try:
            url = f"http://{server_ip}:{port}"
            self.sio.connect(url, transports=['websocket'])
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        if self.is_connected:
            self.sio.disconnect()
    
    def register_gm(self, session_id: int, user_id: int, username: str):
        self.current_session_id = session_id
        self.current_user_id = user_id
        self.is_gm = True
        self.sio.emit('register_gm', {
            'session_id': session_id,
            'user_id': user_id,
            'username': username
        })
        self.ping_timer.start()
    
    def register_player(self, session_id: int, user_id: int, username: str, 
                        character_id: int, character_name: str):
        self.current_session_id = session_id
        self.current_user_id = user_id
        self.current_character_id = character_id
        self.is_gm = False
        self.sio.emit('register_player', {
            'session_id': session_id,
            'user_id': user_id,
            'username': username,
            'character_id': character_id,
            'character_name': character_name
        })
        self.ping_timer.start()
    
    def send_ping(self):
        if self.is_connected and self.current_session_id and self.current_user_id:
            self.sio.emit('ping', {
                'session_id': self.current_session_id,
                'user_id': self.current_user_id,
                'ping': 0  # Можно рассчитать реальный пинг
            })
    
    def send_chat(self, message: str, action_type: str = 'chat'):
        if self.is_connected:
            self.sio.emit('send_chat', {
                'session_id': self.current_session_id,
                'user_id': self.current_user_id,
                'username': None,  # Будет заменено на сервере
                'character_name': None,
                'message': message,
                'action_type': action_type
            })
    
    def gm_update_character(self, character_id: int, updates: Dict):
        if self.is_connected and self.is_gm:
            self.sio.emit('gm_update_character', {
                'session_id': self.current_session_id,
                'character_id': character_id,
                'updates': updates
            })
    
    def gm_add_item(self, character_id: int, item_id: int, quantity: int = 1):
        if self.is_connected and self.is_gm:
            self.sio.emit('gm_add_item', {
                'session_id': self.current_session_id,
                'character_id': character_id,
                'item_id': item_id,
                'quantity': quantity
            })
    
    def gm_remove_item(self, character_id: int, item_id: int):
        if self.is_connected and self.is_gm:
            self.sio.emit('gm_remove_item', {
                'session_id': self.current_session_id,
                'character_id': character_id,
                'item_id': item_id
            })
    
    def add_game_object(self, obj_type: str, name: str, description: str = "", data: Dict = None):
        if self.is_connected and self.is_gm:
            self.sio.emit('add_game_object', {
                'session_id': self.current_session_id,
                'type': obj_type,
                'name': name,
                'description': description,
                'data': data or {}
            })
    
    def get_players(self):
        if self.is_connected and self.is_gm:
            self.sio.emit('get_players', {'session_id': self.current_session_id})


socket_client = SocketClient()