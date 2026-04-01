# db/gui/logger_client.py
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from db.gui.config_client import API_URL

class LoggerClient:
    """Клиент для работы с системой логов из GUI"""
    
    def __init__(self, user_id: int, username: str, is_admin: bool = False):
        self.user_id = user_id
        self.username = username
        self.is_admin = is_admin
    
    def log_action(self, action_name: str, 
                   target_id: Optional[int] = None,
                   character_id: Optional[int] = None,
                   session_id: Optional[int] = None,
                   details: Optional[Dict[str, Any]] = None):
        """Записать действие в лог"""
        try:
            response = requests.post(f"{API_URL}/logs/log", json={
                'action_name': action_name,
                'performer_id': self.user_id,
                'target_id': target_id,
                'character_id': character_id,
                'session_id': session_id,
                'details': details or {}
            })
            return response.status_code == 201
        except Exception as e:
            print(f"Error logging action: {e}")
            return False
    
    def get_my_logs(self, limit: int = 50):
        """Получить свои логи"""
        try:
            response = requests.get(f"{API_URL}/logs/my-logs", 
                                   params={'limit': limit})
            if response.status_code == 200:
                return response.json().get('logs', [])
        except Exception as e:
            print(f"Error getting logs: {e}")
        return []
    
    def get_my_stats(self):
        """Получить свою статистику"""
        try:
            response = requests.get(f"{API_URL}/logs/my-stats")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting stats: {e}")
        return {}
    
    def get_session_logs(self, session_id: int):
        """Получить логи сессии"""
        try:
            response = requests.get(f"{API_URL}/logs/session/{session_id}/logs")
            if response.status_code == 200:
                return response.json().get('logs', [])
        except Exception as e:
            print(f"Error getting session logs: {e}")
        return []
    
    def get_all_logs_gm(self, limit: int = 100, player_id: Optional[int] = None):
        """ГМ: получить все логи"""
        if not self.is_admin:
            return []
        try:
            params = {'limit': limit}
            if player_id:
                params['player_id'] = player_id
            
            response = requests.get(f"{API_URL}/logs/gamemaster/all", params=params)
            if response.status_code == 200:
                return response.json().get('logs', [])
        except Exception as e:
            print(f"Error getting all logs: {e}")
        return []
    
    def get_available_actions(self):
        """Получить список доступных действий"""
        try:
            response = requests.get(f"{API_URL}/logs/actions")
            if response.status_code == 200:
                return response.json().get('actions', [])
        except Exception as e:
            print(f"Error getting actions: {e}")
        return []
    
    def log_story_element(self, element_type: str, name: str, context: str = ""):
        """Логирует элемент сюжета"""
        return self.log_action(
            f'story_{element_type}',
            details={'name': name, 'context': context}
        )
    
    def get_story_actions(self, session_id: int = None):
        """Получает все действия связанные с сюжетом"""
        actions = self.get_all_logs_gm() if self.is_admin else self.get_my_logs()
        story_actions = [a for a in actions if a.get('action_name', '').startswith('story_')]
        return story_actions
