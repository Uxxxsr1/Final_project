# run_server.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Добавляем путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.main import app, socketio, init_db

if __name__ == '__main__':
    print("=" * 60)
    print("ДПЖ - Сервер")
    print("=" * 60)
    
    # Инициализируем БД
    init_db()
    
    print("\nСервер запущен!")
    print("Адрес: http://localhost:5000")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 60)
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)