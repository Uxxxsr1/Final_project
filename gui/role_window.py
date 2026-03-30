from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QListWidget,
                             QTextEdit, QInputDialog, QLineEdit)
from PyQt5.QtCore import Qt
import requests

API_URL = "http://localhost:5000/api"

class RoleWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data  
        self.current_role = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("ДПЖ - Выбор роли")
        self.setFixedSize(1000, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2c3e50;
            }
            
            QLabel#title {
                font-size: 36px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            QLabel#subtitle {
                font-size: 18px;
                color: #7f8c8d;
            }
            
            QPushButton {
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                opacity: 0.9;
            }
            
            QPushButton#gm_btn {
                background-color: #7f8c8d;
                font-size: 18px;
                padding: 15px;
                min-height: 80px;
            }
            
            QPushButton#player_btn {
                background-color: #7f8c8d;
                font-size: 18px;
                padding: 15px;
                min-height: 80px;
            }
                           
            QPushButton#player_btn:hover {
                background-color: #576061;               
            }
                           
            QPushButton#gm_btn:hover {
                background-color: #576061;               
            }
            
            QPushButton#back_btn {
                background-color: #95a5a6;
            }
            
            QPushButton#create_btn {
                background-color: #3498db;
            }
            
            QPushButton#join_btn {
                background-color: #9b59b6;
            }
            
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
            
            /* Исправлено: стили для QListWidget */
            QListWidget {
                border: 1px solid #dcdde1;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
                color: #2c3e50;
                outline: none;
            }
            
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                color: #2c3e50;
                background-color: white;
            }
            
            QListWidget::item:hover {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
                           

            QTextEdit {
                border: 1px solid #dcdde1;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
                font-size: 12px;
                color: #2c3e50;
            }
            
            QTextEdit:read-only {
                background-color: #f8f9fa;
                color: #2c3e50;
            }
            
            QLineEdit {
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                color: #2c3e50
            }
            
            QLineEdit:focus {
                border-color: #3498db;
            }
            
            QFrame QLabel {
                color: #2c3e50;
            }
            
            QInputDialog {
                background-color: white;
            }
            
            QMessageBox {
                background-color: white;
            }
            
            QMessageBox QLabel {
                color: #2c3e50;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #95a5a6;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 10px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:horizontal {
                background: #bdc3c7;
                border-radius: 5px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #95a5a6;
            }
        """)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        
        self.role_selection_widget = self.create_role_selection()
        self.main_layout.addWidget(self.role_selection_widget)
        
        self.setLayout(self.main_layout)
    
    def create_role_selection(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        card = QFrame()
        card_layout = QVBoxLayout()
        card_layout.setSpacing(20)
        
        subtitle = QLabel("Выбор роли")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)
        
        self.gm_btn = QPushButton("Гейм мастер")
        self.gm_btn.setObjectName("gm_btn")
        self.gm_btn.setMinimumHeight(80)
        self.gm_btn.clicked.connect(lambda: self.show_role_panel("gm"))
        card_layout.addWidget(self.gm_btn)
        
        self.player_btn = QPushButton("Игрок")
        self.player_btn.setObjectName("player_btn")
        self.player_btn.setMinimumHeight(80)
        self.player_btn.clicked.connect(lambda: self.show_role_panel("player"))
        card_layout.addWidget(self.player_btn)
        
        boosty_label = QLabel("Boosty")
        boosty_label.setAlignment(Qt.AlignCenter)
        boosty_label.setStyleSheet("color: #bdc3c7; font-size: 12px; margin-top: 30px;")
        card_layout.addWidget(boosty_label)
        
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
        
        back_btn = QPushButton("← Назад")
        back_btn.setObjectName("back_btn")
        back_btn.setMaximumWidth(100)
        back_btn.clicked.connect(self.back_to_roles)
        layout.addWidget(back_btn)
        
        title = QLabel("Гейм мастер")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        tabs = QWidget()
        tabs_layout = QHBoxLayout()
        
        left_panel = QFrame()
        left_layout = QVBoxLayout()
        
        sessions_label = QLabel("Сессии")
        sessions_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        left_layout.addWidget(sessions_label)
        
        self.sessions_list = QListWidget()
        self.sessions_list.itemClicked.connect(self.load_session_details)
        left_layout.addWidget(self.sessions_list)
        
        create_session_btn = QPushButton("+ Создать сессию")
        create_session_btn.setObjectName("create_btn")
        create_session_btn.clicked.connect(self.create_session)
        left_layout.addWidget(create_session_btn)
        
        left_panel.setLayout(left_layout)
        
        right_panel = QFrame()
        right_layout = QVBoxLayout()
        
        self.session_details = QTextEdit()
        self.session_details.setPlaceholderText("Выберите сессию для просмотра деталей")
        self.session_details.setReadOnly(True)
        right_layout.addWidget(self.session_details)
        
        right_panel.setLayout(right_layout)
        
        tabs_layout.addWidget(left_panel, 1)
        tabs_layout.addWidget(right_panel, 2)
        tabs.setLayout(tabs_layout)
        layout.addWidget(tabs)
        
        characters_label = QLabel("Персонажи")
        characters_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 20px;")
        layout.addWidget(characters_label)
        
        self.characters_list = QListWidget()
        layout.addWidget(self.characters_list)
        
        widget.setLayout(layout)
        
        self.load_sessions()
        self.load_characters()
        
        return widget
    
    def create_player_panel(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        back_btn = QPushButton("← Назад")
        back_btn.setObjectName("back_btn")
        back_btn.setMaximumWidth(100)
        back_btn.clicked.connect(self.back_to_roles)
        layout.addWidget(back_btn)
        
        title = QLabel("Игрок")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        tabs = QWidget()
        tabs_layout = QHBoxLayout()
        
        left_panel = QFrame()
        left_layout = QVBoxLayout()
        
        sessions_label = QLabel("Доступные сессии")
        sessions_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        left_layout.addWidget(sessions_label)
        
        self.player_sessions_list = QListWidget()
        self.player_sessions_list.itemClicked.connect(self.join_session)
        left_layout.addWidget(self.player_sessions_list)
        
        left_panel.setLayout(left_layout)
        
        right_panel = QFrame()
        right_layout = QVBoxLayout()
        
        self.connected_sessions = QListWidget()
        self.connected_sessions.setMaximumHeight(150)
        right_layout.addWidget(QLabel("Мои сессии:"))
        right_layout.addWidget(self.connected_sessions)
        
        right_panel.setLayout(right_layout)
        
        tabs_layout.addWidget(left_panel, 1)
        tabs_layout.addWidget(right_panel, 1)
        tabs.setLayout(tabs_layout)
        layout.addWidget(tabs)
        
        characters_label = QLabel("Мои персонажи")
        characters_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 20px;")
        layout.addWidget(characters_label)
        
        self.player_characters_list = QListWidget()
        layout.addWidget(self.player_characters_list)
        
        create_char_btn = QPushButton("+ Создать персонажа")
        create_char_btn.setObjectName("create_btn")
        create_char_btn.clicked.connect(self.create_character)
        layout.addWidget(create_char_btn)
        
        widget.setLayout(layout)
        
        self.load_available_sessions()
        self.load_player_characters()
        
        return widget
    
    def load_sessions(self):
        try:
            response = requests.get(f"{API_URL}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                self.sessions_list.clear()
                for session in sessions:
                    self.sessions_list.addItem(f"{session['name']} (ID: {session['id']})")
        except Exception as e:
            print(f"Error loading sessions: {e}")
    
    def load_session_details(self, item):
        session_id = item.text().split("ID: ")[-1].rstrip(")")
        try:
            response = requests.get(f"{API_URL}/sessions/{session_id}")
            if response.status_code == 200:
                session = response.json()
                details = f"""
Название: {session.get('name', 'Н/Д')}
Описание: {session.get('description', 'Нет описания')}
Мастер: {session.get('master_name', 'Н/Д')}
Создана: {session.get('created_at', 'Н/Д')}
                """
                self.session_details.setText(details)
        except Exception as e:
            print(f"Error loading session details: {e}")
    
    def create_session(self):
        name, ok = QInputDialog.getText(self, "Создание сессии", "Название сессии:")
        if ok and name:
            try:
                response = requests.post(f"{API_URL}/sessions", json={
                    'name': name,
                    'master_id': self.user_data['id'],
                    'description': "Новая сессия"
                })
                if response.status_code == 201:
                    QMessageBox.information(self, "Успех", f"Сессия '{name}' создана!")
                    self.load_sessions()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать сессию")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def join_session(self, item):
        session_name = item.text()
        try:
            response = requests.post(f"{API_URL}/sessions/join", json={
                'session_name': session_name,
                'user_id': self.user_data['id']
            })
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", f"Вы присоединились к сессии {session_name}")
                self.load_available_sessions()
        except Exception as e:
            print(f"Error joining session: {e}")
    
    def load_characters(self):
        try:
            response = requests.get(f"{API_URL}/characters")
            if response.status_code == 200:
                characters = response.json()
                self.characters_list.clear()
                for char in characters:
                    self.characters_list.addItem(f"{char['name']} (ID: {char['id']})")
        except Exception as e:
            print(f"Error loading characters: {e}")
    
    def load_available_sessions(self):
        try:
            response = requests.get(f"{API_URL}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                self.player_sessions_list.clear()
                for session in sessions:
                    self.player_sessions_list.addItem(session['name'])
        except Exception as e:
            print(f"Error loading sessions: {e}")
    
    def load_player_characters(self):
        try:
            response = requests.get(f"{API_URL}/characters/user/{self.user_data['id']}")
            if response.status_code == 200:
                characters = response.json()
                self.player_characters_list.clear()
                for char in characters:
                    self.player_characters_list.addItem(f"{char['name']} - {char.get('class', 'Без класса')}")
        except Exception as e:
            print(f"Error loading characters: {e}")
    
    def create_character(self):
        name, ok = QInputDialog.getText(self, "Создание персонажа", "Имя персонажа:")
        if ok and name:
            class_name, ok = QInputDialog.getText(self, "Создание персонажа", "Класс:")
            if ok:
                try:
                    response = requests.post(f"{API_URL}/characters", json={
                        'name': name,
                        'class': class_name,
                        'user_id': self.user_data['id']
                    })
                    if response.status_code == 201:
                        QMessageBox.information(self, "Успех", f"Персонаж '{name}' создан!")
                        self.load_player_characters()
                    else:
                        QMessageBox.warning(self, "Ошибка", "Не удалось создать персонажа")
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def clear_main_layout(self):
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def back_to_roles(self):
        self.clear_main_layout()
        self.main_layout.addWidget(self.create_role_selection())
        self.current_role = None