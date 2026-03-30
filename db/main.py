from flask import Flask, jsonify, request
from models import db, User, Character, Session
from config import Config
from datetime import datetime
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db.init_app(app)

@app.cli.command('init-db')
def init_db():
    with app.app_context():
        db.create_all()
        log.info('db successfully created')
        
        if User.query.count() == 0:
            admin = User(
                username="admin",
                email="adminemail@example.com",
                is_admin=True
            )
            admin.set_password("admin123admin321")
            db.session.add(admin)
            db.session.commit()
            log.info('admin user created')

@app.route('/api/users/get_all', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin
    } for u in users])

@app.route('/api/users/create', methods=['POST'])
def create_user():
    data = request.json
    
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Все поля обязательны'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Логин уже занят'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email уже зарегистрирован'}), 400
    
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    log.info(f'user {user.username} created')
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin
    }), 200

@app.route('/api/characters', methods=['GET'])
def get_characters():
    characters = Character.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description
    } for c in characters])

@app.route('/api/characters', methods=['POST'])
def create_character():
    data = request.json
    character = Character(
        name=data['name'],
        data=data.get('data', {}),
        user_id=data['user_id']
    )
    db.session.add(character)
    db.session.commit()
    return jsonify({'message': 'Character created', 'id': character.id}), 201

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    sessions = Session.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'is_clean': s.is_clean,
        'master_id': s.master_id,
        'created_at': s.created_at.isoformat() if s.created_at else None
    } for s in sessions])

@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.json
    session = Session(
        name=data['name'],
        master_id=data['master_id'],
        is_clean=data.get('is_clean', True)
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({'message': 'Session created', 'id': session.id}), 201

@app.route('/api/sessions/<int:session_id>/join', methods=['POST'])
def join_session(session_id):
    data = request.json
    session = Session.query.get_or_404(session_id)
    user = User.query.get_or_404(data['user_id'])
    
    if user not in session.participants:
        session.participants.append(user)
        db.session.commit()
    
    return jsonify({'message': 'User joined session'})

@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.json
    login_or_email = data.get('login_or_email')
    password = data.get('password')
    
    if not login_or_email or not password:
        return jsonify({'error': 'Все поля обязательны'}), 400
    
    user = User.query.filter(
        (User.username == login_or_email) | (User.email == login_or_email)
    ).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Неверный логин/email или пароль'}), 401
    
    return jsonify({
        'success': True,
        'message': 'Вход выполнен успешно',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin
        }
    }), 200
@app.route('/api/sessions/user/<int:user_id>', methods=['GET'])
def get_user_sessions(user_id):
    user = User.query.get_or_404(user_id)
    sessions = user.joined_sessions.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'master_id': s.master_id,
        'created_at': s.created_at.isoformat() if s.created_at else None
    } for s in sessions])
@app.route('/api/characters/user/<int:user_id>', methods=['GET'])
def get_user_characters(user_id):
    characters = Character.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'data': c.data,
        'session_id': c.session_id
    } for c in characters])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)