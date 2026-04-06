import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my-secret-key')
    
    # Проверяем, хотим ли мы использовать SQLite
    use_sqlite = os.environ.get('USE_SQLITE', 'true').lower() == 'true'
    
    if use_sqlite:
        # Используем SQLite (просто и надежно)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
        print("Используется SQLite база данных")
    else:
        # PostgreSQL с обработкой спецсимволов
        from urllib.parse import quote_plus
        
        POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
        POSTGRES_PAS = os.environ.get('POSTGRES_PAS', '111')
        POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
        POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
        POSTGRES_DB = os.environ.get('POSTGRES_DB', 'final_projectt')
        
        encoded_password = quote_plus(POSTGRES_PAS)
        
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{POSTGRES_USER}:{encoded_password}"
            f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
        print("Используется PostgreSQL база данных")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False