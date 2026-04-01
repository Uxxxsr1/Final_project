# db/logger/models_logs.py
from datetime import datetime

# Глобальные переменные для моделей
Action = None
GameLog = None

def init_logs_models(database):
    """Инициализация моделей логов с существующей БД"""
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
