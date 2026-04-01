# db/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

session_participants = db.Table(
    'session_participants',
    db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('session_id', db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    characters = db.relationship('Character', backref='owner', lazy=True, cascade='all, delete-orphan')
    sessions_as_master = db.relationship('Session', foreign_keys='Session.master_id', backref='master', lazy=True)
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    @property
    def sessions(self):
        return self.sessions_as_master + list(self._sessions)

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    is_clean = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    vpn_address = db.Column(db.String(100), nullable=True)
    vpn_port = db.Column(db.Integer, default=25565)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    master_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    characters = db.relationship('Character', backref='session', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('User', secondary=session_participants, backref=db.backref('_sessions', lazy='dynamic'), lazy='dynamic')

class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    data = db.Column(db.JSON, default={})
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
