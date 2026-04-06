# run.py - упрощенный запуск сервера
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.main import app

if __name__ == '__main__':
    print("=" * 50)
    print("Запуск сервера ДПЖ")
    print("=" * 50)
    print("Сервер запущен на http://localhost:5000")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    app.run(debug=False, host='0.0.0.0', port=5000)