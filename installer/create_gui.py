# create_gui.py
import os

def create_gui_files():
    """Создает все GUI файлы проекта"""
    
    # Создаем папку gui
    os.makedirs("db/gui", exist_ok=True)
    
    # Файл: db/gui/__init__.py
    with open("db/gui/__init__.py", "w", encoding="utf-8") as f:
        f.write("""# db/gui/__init__.py
from db.gui.role_window import RoleWindow
from db.gui.logger_client import LoggerClient
from db.gui.vpn_manager import VPNManager, VPNConnectionThread
from db.gui.config_client import ClientConfig, client_config, API_URL
""")
    
    # Файл: db/gui/config_client.py
    with open("db/gui/config_client.py", "w", encoding="utf-8") as f:
        f.write("""# db/gui/config_client.py
import json
import os

CONFIG_FILE = "client_config.json"

class ClientConfig:
    \"\"\"Класс для управления настройками клиента\"\"\"
    
    def __init__(self):
        self.api_url = "http://localhost:5000/api"
        self.load_config()
    
    def load_config(self):
        \"\"\"Загружает конфигурацию из файла\"\"\"
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_url = config.get('api_url', self.api_url)
            except:
                pass
    
    def save_config(self):
        \"\"\"Сохраняет конфигурацию в файл\"\"\"
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'api_url': self.api_url}, f, indent=2)
    
    def set_api_url(self, url):
        \"\"\"Устанавливает новый URL API\"\"\"
        self.api_url = url
        self.save_config()
    
    def get_server_ip(self):
        \"\"\"Получает IP сервера из URL\"\"\"
        return self.api_url.replace('http://', '').replace('/api', '').split(':')[0]
    
    def show_config_dialog(self, parent=None):
        \"\"\"Показывает диалог настройки подключения\"\"\"
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        current = self.api_url.replace('http://', '').replace('/api', '')
        url, ok = QInputDialog.getText(
            parent, "Настройка подключения к серверу",
            "Введите IP адрес сервера:\\nПример: 192.168.1.100\\n\\n"
            "Текущий адрес: " + current,
            text=current
        )
        
        if ok and url:
            if ':' in url:
                ip_port = url
            else:
                ip_port = f"{url}:5000"
            
            api_url = f"http://{ip_port}/api"
            self.set_api_url(api_url)
            QMessageBox.information(parent, "Успех", f"Сервер изменен на: {api_url}")
            return True
        return False

# Глобальный экземпляр конфига
client_config = ClientConfig()
API_URL = client_config.api_url
""")
    
    # Файл: db/gui/logger_client.py
    with open("db/gui/logger_client.py", "w", encoding="utf-8") as f:
        f.write("""# db/gui/logger_client.py
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from db.gui.config_client import API_URL

class LoggerClient:
    \"\"\"Клиент для работы с системой логов из GUI\"\"\"
    
    def __init__(self, user_id: int, username: str, is_admin: bool = False):
        self.user_id = user_id
        self.username = username
        self.is_admin = is_admin
    
    def log_action(self, action_name: str, 
                   target_id: Optional[int] = None,
                   character_id: Optional[int] = None,
                   session_id: Optional[int] = None,
                   details: Optional[Dict[str, Any]] = None):
        \"\"\"Записать действие в лог\"\"\"
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
        \"\"\"Получить свои логи\"\"\"
        try:
            response = requests.get(f"{API_URL}/logs/my-logs", 
                                   params={'limit': limit})
            if response.status_code == 200:
                return response.json().get('logs', [])
        except Exception as e:
            print(f"Error getting logs: {e}")
        return []
    
    def get_my_stats(self):
        \"\"\"Получить свою статистику\"\"\"
        try:
            response = requests.get(f"{API_URL}/logs/my-stats")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting stats: {e}")
        return {}
    
    def get_session_logs(self, session_id: int):
        \"\"\"Получить логи сессии\"\"\"
        try:
            response = requests.get(f"{API_URL}/logs/session/{session_id}/logs")
            if response.status_code == 200:
                return response.json().get('logs', [])
        except Exception as e:
            print(f"Error getting session logs: {e}")
        return []
    
    def get_all_logs_gm(self, limit: int = 100, player_id: Optional[int] = None):
        \"\"\"ГМ: получить все логи\"\"\"
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
        \"\"\"Получить список доступных действий\"\"\"
        try:
            response = requests.get(f"{API_URL}/logs/actions")
            if response.status_code == 200:
                return response.json().get('actions', [])
        except Exception as e:
            print(f"Error getting actions: {e}")
        return []
    
    def log_story_element(self, element_type: str, name: str, context: str = ""):
        \"\"\"Логирует элемент сюжета\"\"\"
        return self.log_action(
            f'story_{element_type}',
            details={'name': name, 'context': context}
        )
    
    def get_story_actions(self, session_id: int = None):
        \"\"\"Получает все действия связанные с сюжетом\"\"\"
        actions = self.get_all_logs_gm() if self.is_admin else self.get_my_logs()
        story_actions = [a for a in actions if a.get('action_name', '').startswith('story_')]
        return story_actions
""")
    
    # Файл: db/gui/vpn_manager.py
    with open("db/gui/vpn_manager.py", "w", encoding="utf-8") as f:
        f.write("""# db/gui/vpn_manager.py
import subprocess
import platform
import socket
from PyQt5.QtCore import QThread, pyqtSignal

class VPNManager:
    \"\"\"Управление подключением по IP\"\"\"
    
    def __init__(self):
        self.system = platform.system()
    
    def test_connection(self, ip, port=25565):
        \"\"\"Тестирует соединение с сервером\"\"\"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_local_ip(self):
        \"\"\"Получает локальный IP адрес\"\"\"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_connection_instructions(self):
        \"\"\"Возвращает инструкцию по подключению\"\"\"
        return \"\"\"
🔧 Инструкция по подключению:

1. Убедитесь, что сервер запущен и доступен

2. Введите IP адрес сервера в настройках

3. Для подключения используйте кнопку "Подключиться"

4. Если подключение не удается:
   - Проверьте доступность сервера по ping
   - Убедитесь, что сервер запущен
   - Проверьте настройки брандмауэра
        \"\"\"

class VPNConnectionThread(QThread):
    \"\"\"Поток для проверки подключения\"\"\"
    connection_status = pyqtSignal(bool, str)
    
    def __init__(self, ip, port=25565):
        super().__init__()
        self.ip = ip
        self.port = port
        self.vpn_manager = VPNManager()
    
    def run(self):
        if not self.ip:
            self.connection_status.emit(False, "Нет IP адреса для подключения")
            return
        
        connected = self.vpn_manager.test_connection(self.ip, self.port)
        if connected:
            self.connection_status.emit(True, f"✅ Успешно подключено к {self.ip}:{self.port}")
        else:
            self.connection_status.emit(False, f"❌ Не удалось подключиться к {self.ip}:{self.port}")
""")
    
    # Файл: db/gui/role_window.py
    with open("db/gui/role_window.py", "w", encoding="utf-8") as f:
        f.write("""# db/gui/role_window.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QListWidget,
                             QTextEdit, QInputDialog, QSplitter, QLineEdit)
from PyQt5.QtCore import Qt
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db.gui.logger_client import LoggerClient
from db.gui.vpn_manager import VPNManager, VPNConnectionThread
from db.gui.config_client import client_config, API_URL

class RoleWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.current_role = None
        self.vpn_manager = VPNManager()
        self.connection_thread = None
        
        self.logger = LoggerClient(
            user_id=user_data['id'],
            username=user_data['username'],
            is_admin=user_data.get('is_admin', False)
        )
        
        self.initUI()
        self.logger.log_action('login', details={'username': user_data['username']})
    
    def open_story_dialog(self):
        \"\"\"Открывает диалог создания сюжета\"\"\"
        from db.Plot.story_dialog import StoryDialog
        dialog = StoryDialog(self.logger, parent=self)
        dialog.exec_()
    
    def open_connection_settings(self):
        \"\"\"Открывает настройки подключения\"\"\"
        if client_config.show_config_dialog(self):
            from db.gui.config_client import API_URL
            self.load_my_sessions()
            self.load_available_sessions()
    
    def initUI(self):
        self.setWindowTitle("ДПЖ - Система управления играми")
        self.setFixedSize(1000, 750)
        self.setStyleSheet(\"\"\"
            QWidget {
                background-color: #2c3e50;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#title {
                font-size: 28px;
                font-weight: bold;
                color: #ecf0f1;
                padding: 20px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#back_btn {
                background-color: #95a5a6;
            }
            QPushButton#back_btn:hover {
                background-color: #7f8c8d;
            }
            QFrame {
                background-color: #34495e;
                border-radius: 12px;
                padding: 15px;
            }
            QListWidget {
                background-color: #ecf0f1;
                border: none;
                border-radius: 8px;
                padding: 10px;
                color: #2c3e50;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #bdc3c7;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTextEdit {
                background-color: #ecf0f1;
                border: none;
                border-radius: 8px;
                padding: 10px;
                color: #2c3e50;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #ecf0f1;
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 14px;
                font-weight: bold;
            }
        \"\"\")
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.role_selection_widget = self.create_role_selection()
        self.main_layout.addWidget(self.role_selection_widget)
        
        self.setLayout(self.main_layout)
    
    def create_role_selection(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("ДПЖ")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        user_info = QLabel(f"Пользователь: {self.user_data['username']}")
        user_info.setAlignment(Qt.AlignCenter)
        user_info.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        layout.addWidget(user_info)
        
        card = QFrame()
        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)
        
        self.gm_btn = QPushButton("🎮 Гейм мастер")
        self.gm_btn.setMinimumHeight(80)
        self.gm_btn.setStyleSheet(\"\"\"QPushButton { background-color: #e67e22; font-size: 18px; }\"\"\")
        self.gm_btn.clicked.connect(lambda: self.show_role_panel("gm"))
        card_layout.addWidget(self.gm_btn)
        
        self.player_btn = QPushButton("🎲 Игрок")
        self.player_btn.setMinimumHeight(80)
        self.player_btn.setStyleSheet(\"\"\"QPushButton { background-color: #27ae60; font-size: 18px; }\"\"\")
        self.player_btn.clicked.connect(lambda: self.show_role_panel("player"))
        card_layout.addWidget(self.player_btn)
        
        boosty = QLabel("Boosty")
        boosty.setAlignment(Qt.AlignCenter)
        boosty.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 20px;")
        card_layout.addWidget(boosty)
        
        card.setLayout(card_layout)
        layout.addWidget(card)
        widget.setLayout(layout)
        return widget
    
    def show_role_panel(self, role):
        self.current_role = role
        self.clear_main_layout()
        
        if role == "gm":
            panel = self.create_gm_panel()
        else:
            panel = self.create_player_panel()
        
        self.main_layout.addWidget(panel)
    
    def create_gm_panel(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        top_layout = QHBoxLayout()
        back_btn = QPushButton("← Назад")
        back_btn.setObjectName("back_btn")
        back_btn.setMaximumWidth(100)
        back_btn.clicked.connect(self.back_to_roles)
        top_layout.addWidget(back_btn)
        
        title = QLabel("Гейм мастер")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(title)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        content = QSplitter(Qt.Horizontal)
        
        left_panel = QFrame()
        left_layout = QVBoxLayout()
        
        sessions_btn = QPushButton("📋 Сессии")
        sessions_btn.clicked.connect(lambda: self.show_gm_sessions())
        left_layout.addWidget(sessions_btn)
        
        characters_btn = QPushButton("👥 Персонажи")
        characters_btn.clicked.connect(lambda: self.show_gm_characters())
        left_layout.addWidget(characters_btn)
        
        connection_btn = QPushButton("🔌 VPN настройка")
        connection_btn.clicked.connect(lambda: self.show_gm_vpn_config())
        left_layout.addWidget(connection_btn)
        
        story_btn = QPushButton("📖 Создать сюжет")
        story_btn.clicked.connect(self.open_story_dialog)
        left_layout.addWidget(story_btn)
        
        left_layout.addStretch()
        
        boosty = QLabel("Boosty")
        boosty.setAlignment(Qt.AlignCenter)
        boosty.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 20px;")
        left_layout.addWidget(boosty)
        
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(200)
        
        self.gm_content = QFrame()
        self.gm_content_layout = QVBoxLayout()
        self.gm_content.setLayout(self.gm_content_layout)
        
        content.addWidget(left_panel)
        content.addWidget(self.gm_content)
        
        layout.addWidget(content)
        widget.setLayout(layout)
        
        self.show_gm_sessions()
        return widget
    
    def create_player_panel(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        top_layout = QHBoxLayout()
        back_btn = QPushButton("← Назад")
        back_btn.setObjectName("back_btn")
        back_btn.setMaximumWidth(100)
        back_btn.clicked.connect(self.back_to_roles)
        top_layout.addWidget(back_btn)
        
        title = QLabel("Игрок")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(title)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        content = QSplitter(Qt.Horizontal)
        
        left_panel = QFrame()
        left_layout = QVBoxLayout()
        
        my_sessions_btn = QPushButton("🎮 Мои сессии")
        my_sessions_btn.clicked.connect(lambda: self.show_player_my_sessions())
        left_layout.addWidget(my_sessions_btn)
        
        available_btn = QPushButton("✨ Доступные сессии")
        available_btn.clicked.connect(lambda: self.show_player_available_sessions())
        left_layout.addWidget(available_btn)
        
        characters_btn = QPushButton("👤 Мои персонажи")
        characters_btn.clicked.connect(lambda: self.show_player_characters())
        left_layout.addWidget(characters_btn)
        
        settings_btn = QPushButton("⚙️ Настройки сервера")
        settings_btn.clicked.connect(self.open_connection_settings)
        left_layout.addWidget(settings_btn)
        
        left_layout.addStretch()
        
        boosty = QLabel("Boosty")
        boosty.setAlignment(Qt.AlignCenter)
        boosty.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 20px;")
        left_layout.addWidget(boosty)
        
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(200)
        
        self.player_content = QFrame()
        self.player_content_layout = QVBoxLayout()
        self.player_content.setLayout(self.player_content_layout)
        
        content.addWidget(left_panel)
        content.addWidget(self.player_content)
        
        layout.addWidget(content)
        widget.setLayout(layout)
        
        self.show_player_my_sessions()
        return widget
    
    def show_gm_sessions(self):
        self.clear_content(self.gm_content_layout)
        
        header = QLabel("Управление сессиями")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.gm_content_layout.addWidget(header)
        
        self.gm_sessions_list = QListWidget()
        self.gm_sessions_list.itemDoubleClicked.connect(self.edit_session)
        self.gm_content_layout.addWidget(self.gm_sessions_list)
        
        create_btn = QPushButton("+ Создать сессию")
        create_btn.setObjectName("action_btn")
        create_btn.clicked.connect(self.create_session)
        self.gm_content_layout.addWidget(create_btn)
        
        self.load_gm_sessions()
    
    def show_gm_characters(self):
        self.clear_content(self.gm_content_layout)
        
        header = QLabel("Управление персонажами")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.gm_content_layout.addWidget(header)
        
        self.gm_characters_list = QListWidget()
        self.gm_content_layout.addWidget(self.gm_characters_list)
        
        self.load_gm_characters()
    
    def show_gm_vpn_config(self):
        self.clear_content(self.gm_content_layout)
        
        header = QLabel("Настройка VPN для сессии")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.gm_content_layout.addWidget(header)
        
        sessions_label = QLabel("Выберите сессию:")
        self.gm_content_layout.addWidget(sessions_label)
        
        self.gm_vpn_sessions_list = QListWidget()
        self.gm_vpn_sessions_list.itemClicked.connect(self.on_vpn_session_selected)
        self.gm_content_layout.addWidget(self.gm_vpn_sessions_list)
        
        self.vpn_config_frame = QFrame()
        vpn_layout = QVBoxLayout()
        
        ip_label = QLabel("VPN IP адрес:")
        vpn_layout.addWidget(ip_label)
        
        self.vpn_ip_input = QLineEdit()
        self.vpn_ip_input.setPlaceholderText("Например: 26.12.34.56")
        vpn_layout.addWidget(self.vpn_ip_input)
        
        port_label = QLabel("Порт:")
        vpn_layout.addWidget(port_label)
        
        self.vpn_port_input = QLineEdit()
        self.vpn_port_input.setText("25565")
        vpn_layout.addWidget(self.vpn_port_input)
        
        get_ip_btn = QPushButton("Получить мой IP")
        get_ip_btn.clicked.connect(self.get_my_radmin_ip)
        vpn_layout.addWidget(get_ip_btn)
        
        save_btn = QPushButton("Сохранить настройки")
        save_btn.clicked.connect(self.save_vpn_settings)
        vpn_layout.addWidget(save_btn)
        
        self.vpn_config_frame.setLayout(vpn_layout)
        self.vpn_config_frame.hide()
        self.gm_content_layout.addWidget(self.vpn_config_frame)
        
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setText(self.vpn_manager.get_connection_instructions())
        self.gm_content_layout.addWidget(instructions)
        
        self.load_gm_vpn_sessions()
    
    def show_player_my_sessions(self):
        self.clear_content(self.player_content_layout)
        
        header = QLabel("Мои сессии")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.player_content_layout.addWidget(header)
        
        self.my_sessions_list = QListWidget()
        self.my_sessions_list.itemDoubleClicked.connect(self.connect_to_session)
        self.player_content_layout.addWidget(self.my_sessions_list)
        
        self.load_my_sessions()
    
    def show_player_available_sessions(self):
        self.clear_content(self.player_content_layout)
        
        header = QLabel("Доступные сессии")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.player_content_layout.addWidget(header)
        
        info_label = QLabel("Дважды кликните по сессии, чтобы присоединиться")
        info_label.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        self.player_content_layout.addWidget(info_label)
        
        self.available_sessions_list = QListWidget()
        self.available_sessions_list.itemDoubleClicked.connect(self.join_session)
        self.player_content_layout.addWidget(self.available_sessions_list)
        
        self.load_available_sessions()
    
    def show_player_characters(self):
        self.clear_content(self.player_content_layout)
        
        header = QLabel("Мои персонажи")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.player_content_layout.addWidget(header)
        
        self.player_characters_list = QListWidget()
        self.player_characters_list.itemDoubleClicked.connect(self.select_character)
        self.player_content_layout.addWidget(self.player_characters_list)
        
        create_btn = QPushButton("+ Создать персонажа")
        create_btn.clicked.connect(self.create_character)
        self.player_content_layout.addWidget(create_btn)
        
        self.load_my_characters()
    
    def load_gm_sessions(self):
        try:
            response = requests.get(f"{API_URL}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                self.gm_sessions_list.clear()
                for session in sessions:
                    self.gm_sessions_list.addItem(f"{session['name']} (ID: {session['id']})")
        except Exception as e:
            print(f"Error: {e}")
    
    def load_gm_vpn_sessions(self):
        try:
            response = requests.get(f"{API_URL}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                self.gm_vpn_sessions_list.clear()
                for session in sessions:
                    self.gm_vpn_sessions_list.addItem(f"{session['name']} (ID: {session['id']})")
        except Exception as e:
            print(f"Error: {e}")
    
    def load_gm_characters(self):
        try:
            response = requests.get(f"{API_URL}/characters")
            if response.status_code == 200:
                characters = response.json()
                self.gm_characters_list.clear()
                for char in characters:
                    self.gm_characters_list.addItem(f"{char['name']} (ID: {char['id']})")
        except Exception as e:
            print(f"Error: {e}")
    
    def load_my_sessions(self):
        try:
            response = requests.get(f"{API_URL}/sessions/my/{self.user_data['id']}")
            if response.status_code == 200:
                sessions = response.json()
                self.my_sessions_list.clear()
                for session in sessions:
                    self.my_sessions_list.addItem(f"{session['name']}")
        except Exception as e:
            print(f"Error: {e}")
    
    def load_available_sessions(self):
        try:
            response = requests.get(f"{API_URL}/sessions/available/{self.user_data['id']}")
            if response.status_code == 200:
                sessions = response.json()
                self.available_sessions_list.clear()
                for session in sessions:
                    self.available_sessions_list.addItem(f"{session['name']}")
        except Exception as e:
            print(f"Error: {e}")
    
    def load_my_characters(self):
        try:
            response = requests.get(f"{API_URL}/characters/my/{self.user_data['id']}")
            if response.status_code == 200:
                characters = response.json()
                self.player_characters_list.clear()
                for char in characters:
                    self.player_characters_list.addItem(f"{char['name']}")
        except Exception as e:
            print(f"Error: {e}")
    
    def create_session(self):
        name, ok = QInputDialog.getText(self, "Создание сессии", "Название сессии:")
        if ok and name:
            try:
                response = requests.post(f"{API_URL}/sessions", json={
                    'name': name,
                    'master_id': self.user_data['id']
                })
                if response.status_code == 201:
                    QMessageBox.information(self, "Успех", f"Сессия '{name}' создана!")
                    self.logger.log_action('create_session', details={'session_name': name})
                    self.load_gm_sessions()
                    self.load_gm_vpn_sessions()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать сессию")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def join_session(self, item):
        session_name = item.text()
        try:
            response = requests.get(f"{API_URL}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                session = next((s for s in sessions if s['name'] == session_name), None)
                if session:
                    join_response = requests.post(f"{API_URL}/sessions/{session['id']}/join", json={
                        'user_id': self.user_data['id']
                    })
                    if join_response.status_code == 200:
                        QMessageBox.information(self, "Успех", f"Вы присоединились к сессии {session_name}")
                        self.logger.log_action('join_session', session_id=session['id'])
                        self.load_my_sessions()
                        self.load_available_sessions()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def create_character(self):
        name, ok = QInputDialog.getText(self, "Создание персонажа", "Имя персонажа:")
        if ok and name:
            try:
                response = requests.post(f"{API_URL}/characters", json={
                    'name': name,
                    'data': {},
                    'user_id': self.user_data['id']
                })
                if response.status_code == 201:
                    QMessageBox.information(self, "Успех", f"Персонаж '{name}' создан!")
                    self.logger.log_action('create_character', details={'character_name': name})
                    self.load_my_characters()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать персонажа")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def connect_to_session(self, item):
        session_name = item.text()
        try:
            response = requests.get(f"{API_URL}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                session = next((s for s in sessions if s['name'] == session_name), None)
                if session:
                    vpn_response = requests.get(f"{API_URL}/sessions/{session['id']}/vpn")
                    if vpn_response.status_code == 200:
                        vpn_data = vpn_response.json()
                        if vpn_data.get('vpn_address'):
                            reply = QMessageBox.question(
                                self, "Подключение",
                                f"Подключиться к {session_name}?\\n\\n"
                                f"Адрес: {vpn_data['vpn_address']}:{vpn_data['vpn_port']}",
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if reply == QMessageBox.Yes:
                                self.test_vpn_connection(vpn_data['vpn_address'], 
                                                        vpn_data['vpn_port'],
                                                        session_name)
                        else:
                            QMessageBox.information(self, "VPN не настроен",
                                f"Для сессии {session_name} еще не настроено VPN подключение.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def test_vpn_connection(self, ip, port, session_name):
        self.connection_thread = VPNConnectionThread(ip, port)
        self.connection_thread.connection_status.connect(
            lambda success, msg: self.on_vpn_connection_result(success, msg, session_name)
        )
        self.connection_thread.start()
        self.status_label = QLabel("Проверка подключения...")
        self.player_content_layout.addWidget(self.status_label)
    
    def on_vpn_connection_result(self, success, message, session_name):
        if hasattr(self, 'status_label'):
            self.status_label.deleteLater()
        if success:
            QMessageBox.information(self, "Успешно!", f"✅ Вы подключены к {session_name}!")
            self.logger.log_action('connect_to_session', details={'session_name': session_name})
        else:
            QMessageBox.warning(self, "Ошибка подключения", message)
    
    def on_vpn_session_selected(self, item):
        self.selected_vpn_session = item.text()
        self.vpn_config_frame.show()
        try:
            session_id = int(self.selected_vpn_session.split("ID: ")[-1].rstrip(")"))
            response = requests.get(f"{API_URL}/sessions/{session_id}/vpn")
            if response.status_code == 200:
                data = response.json()
                if data.get('vpn_address'):
                    self.vpn_ip_input.setText(data['vpn_address'])
                if data.get('vpn_port'):
                    self.vpn_port_input.setText(str(data['vpn_port']))
        except:
            pass
    
    def get_my_radmin_ip(self):
        ip = self.vpn_manager.get_local_ip()
        if ip:
            self.vpn_ip_input.setText(ip)
            QMessageBox.information(self, "IP найден", f"Ваш IP: {ip}")
        else:
            QMessageBox.warning(self, "IP не найден", "Не удалось определить IP")
    
    def save_vpn_settings(self):
        if not hasattr(self, 'selected_vpn_session'):
            QMessageBox.warning(self, "Ошибка", "Сначала выберите сессию")
            return
        try:
            session_id = int(self.selected_vpn_session.split("ID: ")[-1].rstrip(")"))
            vpn_address = self.vpn_ip_input.text()
            vpn_port = int(self.vpn_port_input.text()) if self.vpn_port_input.text() else 25565
            
            response = requests.post(
                f"{API_URL}/sessions/{session_id}/update_vpn",
                json={
                    'user_id': self.user_data['id'],
                    'vpn_address': vpn_address,
                    'vpn_port': vpn_port
                }
            )
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "VPN настройки сохранены!")
                self.logger.log_action('configure_vpn', details={'session_id': session_id})
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить настройки")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def edit_session(self, item):
        QMessageBox.information(self, "Редактирование", f"Редактирование сессии: {item.text()}")
    
    def select_character(self, item):
        char_name = item.text()
        QMessageBox.information(self, "Выбор персонажа", f"Выбран персонаж: {char_name}")
        self.logger.log_action('select_character', details={'character_name': char_name})
    
    def clear_content(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def clear_main_layout(self):
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def back_to_roles(self):
        self.clear_main_layout()
        self.main_layout.addWidget(self.create_role_selection())
        self.current_role = None
        self.logger.log_action('exit_role')
    
    def closeEvent(self, event):
        self.logger.log_action('logout', details={'username': self.user_data['username']})
        event.accept()
""")
    
    print("✅ Все GUI файлы созданы!")
    print("\nСозданные файлы:")
    print("  - db/gui/__init__.py")
    print("  - db/gui/config_client.py")
    print("  - db/gui/logger_client.py")
    print("  - db/gui/vpn_manager.py")
    print("  - db/gui/role_window.py")

if __name__ == "__main__":
    create_gui_files()