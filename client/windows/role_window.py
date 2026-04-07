# client/windows/role_window.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QDialog, QListWidget)
from PyQt5.QtCore import Qt
from client.api_client import api_client
from client.windows.gm_window import GMWindow
from client.windows.player_window import PlayerWindow


class RoleWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("ДПЖ - Выбор роли")
        self.setFixedSize(350, 250)
        self.setStyleSheet("""
            QWidget {
                background-color: #3a3a3a;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #5a5a5a;
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6a6a6a;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Выберите роль")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e67e22;")
        layout.addWidget(title)
        
        user_label = QLabel(f"Пользователь: {self.user_data['username']}")
        user_label.setAlignment(Qt.AlignCenter)
        user_label.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(user_label)
        
        layout.addSpacing(10)
        
        self.gm_btn = QPushButton("🎮 Гейм Мастер")
        self.gm_btn.clicked.connect(self.select_gm)
        layout.addWidget(self.gm_btn)
        
        self.player_btn = QPushButton("🎲 Игрок")
        self.player_btn.clicked.connect(self.select_player)
        layout.addWidget(self.player_btn)
        
        self.setLayout(layout)
    
    def select_gm(self):
        # Проверяем есть ли у ГМ сессии
        sessions = api_client.get_my_sessions(self.user_data['id'])
        
        if not sessions:
            # Предлагаем создать сессию
            reply = QMessageBox.question(self, "Нет сессий", 
                                         "У вас нет созданных сессий. Создать новую?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.create_session_and_continue()
            return
        
        # Показываем выбор сессии
        self.show_session_selection(sessions, is_gm=True)
    
    def select_player(self):
        # Проверяем есть ли персонажи
        characters = api_client.get_my_characters(self.user_data['id'])
        
        if not characters:
            reply = QMessageBox.question(self, "Нет персонажей", 
                                         "У вас нет персонажей. Создать нового?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.create_character_and_continue()
            return
        
        # Показываем выбор персонажа и сессии
        self.show_character_and_session_selection(characters)
    
    def create_session_and_continue(self):
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Создание сессии", "Название сессии:")
        if ok and name:
            session = api_client.create_session(name, self.user_data['id'])
            if session:
                QMessageBox.information(self, "Успех", f"Сессия '{name}' создана!")
                self.gm_window = GMWindow(self.user_data, session)
                self.gm_window.show()
                self.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать сессию")
    
    def create_character_and_continue(self):
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Создание персонажа", "Имя персонажа:")
        if ok and name:
            character = api_client.create_character(self.user_data['id'], name)
            if character:
                QMessageBox.information(self, "Успех", f"Персонаж '{name}' создан!")
                self.select_player()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать персонажа")
    
    def show_session_selection(self, sessions, is_gm=False):
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор сессии")
        dialog.setFixedSize(350, 400)
        dialog.setStyleSheet("""
            QDialog { background-color: #3a3a3a; }
            QLabel { color: #e0e0e0; }
            QListWidget { background-color: #4a4a4a; color: #e0e0e0; border: none; border-radius: 6px; }
            QPushButton { background-color: #5a5a5a; border: none; border-radius: 6px; padding: 8px; color: white; }
            QPushButton:hover { background-color: #6a6a6a; }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("Выберите сессию:")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        list_widget = QListWidget()
        for session in sessions:
            list_widget.addItem(f"{session['name']} (ID: {session['id']})")
        layout.addWidget(list_widget)
        
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Выбрать")
        cancel_btn = QPushButton("Отмена")
        
        def on_select():
            current = list_widget.currentItem()
            if current:
                text = current.text()
                session_id = int(text.split("ID: ")[-1].rstrip(")"))
                session = next((s for s in sessions if s['id'] == session_id), None)
                if session:
                    dialog.accept()
                    if is_gm:
                        self.gm_window = GMWindow(self.user_data, session)
                        self.gm_window.show()
                    else:
                        self.player_window = PlayerWindow(self.user_data, session)
                        self.player_window.show()
                    self.close()
        
        select_btn.clicked.connect(on_select)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def show_character_and_session_selection(self, characters):
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор персонажа и сессии")
        dialog.setFixedSize(400, 500)
        dialog.setStyleSheet("""
            QDialog { background-color: #3a3a3a; }
            QLabel { color: #e0e0e0; }
            QListWidget { background-color: #4a4a4a; color: #e0e0e0; border: none; border-radius: 6px; }
            QPushButton { background-color: #5a5a5a; border: none; border-radius: 6px; padding: 8px; color: white; }
            QPushButton:hover { background-color: #6a6a6a; }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Список персонажей
        char_label = QLabel("Выберите персонажа:")
        layout.addWidget(char_label)
        
        char_list = QListWidget()
        for char in characters:
            session_info = f" [Сессия: {char['session_name']}]" if char.get('session_name') else ""
            char_list.addItem(f"{char['name']} (Ур. {char['level']}){session_info}")
        layout.addWidget(char_list)
        
        # Список доступных сессий
        session_label = QLabel("Выберите сессию:")
        layout.addWidget(session_label)
        
        session_list = QListWidget()
        available_sessions = api_client.get_available_sessions(self.user_data['id'])
        for session in available_sessions:
            session_list.addItem(f"{session['name']} (ID: {session['id']})")
        layout.addWidget(session_list)
        
        # Кнопка создания персонажа
        create_char_btn = QPushButton("➕ Создать персонажа")
        create_char_btn.clicked.connect(lambda: self.create_character_and_close(dialog))
        layout.addWidget(create_char_btn)
        
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Играть")
        cancel_btn = QPushButton("Отмена")
        
        def on_select():
            char_item = char_list.currentItem()
            session_item = session_list.currentItem()
            
            if not char_item:
                QMessageBox.warning(dialog, "Ошибка", "Выберите персонажа")
                return
            if not session_item:
                QMessageBox.warning(dialog, "Ошибка", "Выберите сессию")
                return
            
            char_text = char_item.text()
            char_name = char_text.split(" (Ур.")[0]
            character = next((c for c in characters if c['name'] == char_name), None)
            
            if not character:
                return
            
            if character.get('session_name'):
                QMessageBox.warning(dialog, "Ошибata", 
                                   f"Персонаж '{char_name}' уже привязан к сессии '{character['session_name']}'")
                return
            
            session_text = session_item.text()
            session_id = int(session_text.split("ID: ")[-1].rstrip(")"))
            session = next((s for s in available_sessions if s['id'] == session_id), None)
            
            if session:
                # Привязываем персонажа к сессии
                if api_client.attach_character_to_session(character['id'], session_id):
                    # Присоединяемся к сессии
                    api_client.join_session(session_id, self.user_data['id'])
                    dialog.accept()
                    self.player_window = PlayerWindow(self.user_data, session, character)
                    self.player_window.show()
                    self.close()
                else:
                    QMessageBox.warning(dialog, "Ошибка", "Не удалось привязать персонажа")
        
        select_btn.clicked.connect(on_select)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def create_character_and_close(self, dialog):
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Создание персонажа", "Имя персонажа:")
        if ok and name:
            character = api_client.create_character(self.user_data['id'], name)
            if character:
                QMessageBox.information(self, "Успех", f"Персонаж '{name}' создан!")
                dialog.accept()
                self.select_player()