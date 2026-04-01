# db/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my-secret-key')
    
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
    POSTGRES_PAS = os.environ.get('POSTGRES_PAS', '111')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'final_projectt')
    
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{(POSTGRES_PAS)}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
