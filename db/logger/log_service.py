# db/logger/log_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import or_, and_

# Глобальные переменные
Action = None
GameLog = None
db = None

def init_log_service(database, action_model, gamelog_model):
    """Инициализация сервиса логов"""
    global db, Action, GameLog
    db = database
    Action = action_model
    GameLog = gamelog_model

class LogService:
    """Сервис для управления логами действий"""
    
    @staticmethod
    def get_or_create_action(action_name: str, description: str = None):
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
        return GameLog.query.filter_by(session_id=session_id)\
            .order_by(GameLog.timestamp.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_character_logs(character_id: int, limit: int = 100):
        return GameLog.query.filter_by(character_id=character_id)\
            .order_by(GameLog.timestamp.desc())\
            .limit(limit).all()