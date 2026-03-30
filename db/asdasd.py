import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import db
from main import app

with app.app_context():
    print("Creating all tables...")
    db.create_all()
    print("Tables created successfully!")
    
    from models import User
    if User.query.count() == 0:
        admin = User(
            username="admin",
            email="admin@example.com",
            is_admin=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created!")
        print("Login: admin or admin@example.com")
        print("Password: admin123")