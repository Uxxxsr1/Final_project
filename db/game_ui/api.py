# db/game_ui/api.py
import requests
from typing import Dict, List, Optional, Any
from db.gui.config_client import API_URL

class GameAPI:
    """API для игровых действий"""
    
    def __init__(self, user_id: int, is_admin: bool = False):
        self.user_id = user_id
        self.is_admin = is_admin
    
    def get_session_players(self, session_id: int) -> List[Dict]:
        """Получить всех игроков в сессии с их персонажами"""
        try:
            response = requests.get(f"{API_URL}/game/session/{session_id}/players")
            if response.status_code == 200:
                return response.json().get('players', [])
        except Exception as e:
            print(f"Error getting players: {e}")
        return []
    
    def get_player_character(self, user_id: int, session_id: int) -> Optional[Dict]:
        """Получить персонажа игрока в сессии"""
        try:
            response = requests.get(f"{API_URL}/game/character/{user_id}/{session_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting character: {e}")
        return None
    
    def update_character_stats(self, character_id: int, stats: Dict) -> bool:
        """Обновить характеристики персонажа (HP, MP)"""
        try:
            response = requests.put(f"{API_URL}/game/character/{character_id}/stats", 
                                   json=stats)
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating stats: {e}")
            return False
    
    def get_available_actions(self, character_id: int, context: str = "") -> List[Dict]:
        """Получить доступные действия для персонажа"""
        try:
            params = {'context': context} if context else {}
            response = requests.get(f"{API_URL}/game/character/{character_id}/actions", 
                                   params=params)
            if response.status_code == 200:
                return response.json().get('actions', [])
        except Exception as e:
            print(f"Error getting actions: {e}")
        return []
    
    def perform_action(self, character_id: int, action_name: str, 
                       target_id: Optional[int] = None,
                       details: Optional[Dict] = None) -> bool:
        """Выполнить действие"""
        try:
            response = requests.post(f"{API_URL}/game/perform_action", json={
                'character_id': character_id,
                'action_name': action_name,
                'target_id': target_id,
                'details': details or {},
                'performer_id': self.user_id
            })
            return response.status_code == 200
        except Exception as e:
            print(f"Error performing action: {e}")
            return False
    
    def get_character_inventory(self, character_id: int) -> List[Dict]:
        """Получить инвентарь персонажа"""
        try:
            response = requests.get(f"{API_URL}/game/character/{character_id}/inventory")
            if response.status_code == 200:
                return response.json().get('items', [])
        except Exception as e:
            print(f"Error getting inventory: {e}")
        return []
    
    def equip_item(self, character_id: int, item_id: int) -> bool:
        """Экипировать предмет"""
        try:
            response = requests.post(f"{API_URL}/game/character/{character_id}/equip",
                                    json={'item_id': item_id})
            return response.status_code == 200
        except Exception as e:
            print(f"Error equipping item: {e}")
            return False
    
    def unequip_item(self, character_id: int, item_id: int) -> bool:
        """Снять предмет"""
        try:
            response = requests.post(f"{API_URL}/game/character/{character_id}/unequip",
                                    json={'item_id': item_id})
            return response.status_code == 200
        except Exception as e:
            print(f"Error unequipping item: {e}")
            return False
    
    def add_item_to_inventory(self, character_id: int, item_name: str, 
                              quantity: int = 1, effects: Optional[Dict] = None) -> bool:
        """Добавить предмет в инвентарь (для ГМ)"""
        if not self.is_admin:
            return False
        try:
            response = requests.post(f"{API_URL}/game/character/{character_id}/add_item",
                                    json={
                                        'name': item_name,
                                        'quantity': quantity,
                                        'effects': effects or {}
                                    })
            return response.status_code == 200
        except Exception as e:
            print(f"Error adding item: {e}")
            return False
    
    def get_global_events(self, session_id: int) -> List[Dict]:
        """Получить глобальные события сессии"""
        try:
            response = requests.get(f"{API_URL}/game/session/{session_id}/events")
            if response.status_code == 200:
                return response.json().get('events', [])
        except Exception as e:
            print(f"Error getting events: {e}")
        return []
    
    def add_global_event(self, session_id: int, message: str) -> bool:
        """Добавить глобальное событие (для ГМ)"""
        if not self.is_admin:
            return False
        try:
            response = requests.post(f"{API_URL}/game/session/{session_id}/add_event",
                                    json={'message': message})
            return response.status_code == 200
        except Exception as e:
            print(f"Error adding event: {e}")
            return False
    
    def get_character_logs(self, character_id: int, limit: int = 50) -> List[Dict]:
        """Получить логи персонажа"""
        try:
            response = requests.get(f"{API_URL}/game/character/{character_id}/logs",
                                   params={'limit': limit})
            if response.status_code == 200:
                return response.json().get('logs', [])
        except Exception as e:
            print(f"Error getting logs: {e}")
        return []