# db/gui/role_window.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QListWidget,
                             QTextEdit, QInputDialog, QSplitter, QLineEdit,
                             QComboBox, QToolButton, QMenu, QAction, QGridLayout,
                             QDialog, QScrollArea)
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
        self.current_view = None
        self.vpn_manager = VPNManager()
        self.connection_thread = None
        
        # Инициализируем переменные для игрока
        self.selected_character_id = None
        self.selected_character_name = None
        self.selected_session_id = None
        self.selected_session_name = None
        
        self.logger = LoggerClient(
            user_id=user_data['id'],
            username=user_data['username'],
            is_admin=user_data.get('is_admin', False)
        )
        
        self.initUI()
        self.logger.log_action('login', details={'username': user_data['username']})
    
    def open_story_dialog(self):
        """Открывает диалог создания сюжета"""
        from db.Plot.story_dialog import StoryDialog
        dialog = StoryDialog(self.logger, parent=self)
        dialog.exec_()
    
    def open_connection_settings(self):
        """Открывает настройки подключения"""
        if client_config.show_config_dialog(self):
            from db.gui.config_client import API_URL as new_api_url
            global API_URL
            API_URL = new_api_url
            if hasattr(self, 'refresh_player_data'):
                self.refresh_player_data()
    
    def initUI(self):
        self.setWindowTitle("ДПЖ - Система управления играми")
        self.setFixedSize(1000, 750)
        self.setStyleSheet(self.get_stylesheet())
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.show_role_selection()
        self.setLayout(self.main_layout)
    
    def get_stylesheet(self):
        return """
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
            QComboBox {
                background-color: #ecf0f1;
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: #2c3e50;
            }
        """
    
    def show_role_selection(self):
        """Показывает экран выбора роли"""
        self.clear_main_layout()
        
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
        self.gm_btn.setStyleSheet("QPushButton { background-color: #e67e22; font-size: 18px; }")
        self.gm_btn.clicked.connect(lambda: self.show_role_panel("gm"))
        card_layout.addWidget(self.gm_btn)
        
        self.player_btn = QPushButton("🎲 Игрок")
        self.player_btn.setMinimumHeight(80)
        self.player_btn.setStyleSheet("QPushButton { background-color: #27ae60; font-size: 18px; }")
        self.player_btn.clicked.connect(lambda: self.show_role_panel("player"))
        card_layout.addWidget(self.player_btn)
        
        boosty = QLabel("Boosty")
        boosty.setAlignment(Qt.AlignCenter)
        boosty.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 20px;")
        card_layout.addWidget(boosty)
        
        card.setLayout(card_layout)
        layout.addWidget(card)
        widget.setLayout(layout)
        
        self.main_layout.addWidget(widget)
        self.current_view = None
    
    def show_role_panel(self, role):
        """Показывает панель выбранной роли"""
        self.current_role = role
        self.current_view = role
        self.clear_main_layout()
        
        panel_widget = QWidget()
        panel_layout = QVBoxLayout()
        
        top_layout = QHBoxLayout()
        back_btn = QPushButton("← Назад")
        back_btn.setObjectName("back_btn")
        back_btn.setMaximumWidth(100)
        back_btn.clicked.connect(self.back_to_roles)
        top_layout.addWidget(back_btn)
        
        title = QLabel("Гейм мастер" if role == "gm" else "Игрок")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(title)
        top_layout.addStretch()
        panel_layout.addLayout(top_layout)
        
        if role == "gm":
            content = self.create_gm_content()
        else:
            content = self.create_player_content()
        
        panel_layout.addWidget(content)
        panel_widget.setLayout(panel_layout)
        self.main_layout.addWidget(panel_widget)
    
    def create_gm_content(self):
        """Создает контент для ГМ (с возможностью просмотра игроков)"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel("Панель управления Гейммастера")
        title_label.setStyleSheet("font-size: 16px; color: #e67e22; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Основной сплиттер
        splitter = QSplitter(Qt.Horizontal)
        
        # ========== ЛЕВАЯ ПАНЕЛЬ - УПРАВЛЕНИЕ ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Кнопки управления
        sessions_btn = QPushButton("📋 Управление сессиями")
        sessions_btn.setMinimumHeight(50)
        sessions_btn.clicked.connect(lambda: self.show_gm_sessions())
        left_layout.addWidget(sessions_btn)
        
        characters_btn = QPushButton("👥 Все персонажи")
        characters_btn.setMinimumHeight(50)
        characters_btn.clicked.connect(lambda: self.show_gm_characters())
        left_layout.addWidget(characters_btn)
        
        connection_btn = QPushButton("🔌 VPN настройка")
        connection_btn.setMinimumHeight(50)
        connection_btn.clicked.connect(lambda: self.show_gm_vpn_config())
        left_layout.addWidget(connection_btn)
        
        story_btn = QPushButton("📖 Создать сюжет")
        story_btn.setMinimumHeight(50)
        story_btn.clicked.connect(self.open_story_dialog)
        left_layout.addWidget(story_btn)
        
        left_layout.addStretch()
        
        left_panel.setLayout(left_layout)
        
        # ========== ПРАВАЯ ПАНЕЛЬ - ИГРОКИ ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        players_title = QLabel("👥 ИГРОКИ В СИСТЕМЕ")
        players_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71; padding: 5px;")
        players_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(players_title)
        
        # Список всех игроков
        self.all_players_list = QListWidget()
        self.all_players_list.setMinimumHeight(400)
        self.all_players_list.setStyleSheet("""
            QListWidget {
                background-color: #34495e;
                border: 2px solid #2ecc71;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #3d566e;
            }
            QListWidget::item:selected {
                background-color: #2ecc71;
                color: white;
            }
        """)
        self.all_players_list.itemClicked.connect(self.on_player_selected)
        right_layout.addWidget(self.all_players_list)
        
        # Кнопки действий с игроком
        player_buttons_layout = QHBoxLayout()
        
        self.view_player_stats_btn = QPushButton("📊 Смотреть статистику")
        self.view_player_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.view_player_stats_btn.clicked.connect(self.view_selected_player_stats)
        self.view_player_stats_btn.setEnabled(False)
        player_buttons_layout.addWidget(self.view_player_stats_btn)
        
        self.view_player_inv_btn = QPushButton("📦 Смотреть инвентарь")
        self.view_player_inv_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.view_player_inv_btn.clicked.connect(self.view_selected_player_inventory)
        self.view_player_inv_btn.setEnabled(False)
        player_buttons_layout.addWidget(self.view_player_inv_btn)
        
        right_layout.addLayout(player_buttons_layout)
        
        # Кнопка обновления списка
        refresh_btn = QPushButton("🔄 Обновить список игроков")
        refresh_btn.clicked.connect(self.load_all_players)
        right_layout.addWidget(refresh_btn)
        
        right_panel.setLayout(right_layout)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Кнопка входа в игру
        start_game_btn = QPushButton("🎮 ВОЙТИ В ИГРУ КАК ГМ 🎮")
        start_game_btn.setMinimumHeight(60)
        start_game_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        start_game_btn.clicked.connect(self.start_gm_game)
        layout.addWidget(start_game_btn)
        
        # Boosty
        boosty = QLabel("Boosty")
        boosty.setAlignment(Qt.AlignCenter)
        boosty.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 10px;")
        layout.addWidget(boosty)
        
        widget.setLayout(layout)
        
        # Загружаем список игроков
        self.selected_player_id = None
        self.selected_player_name = None
        self.load_all_players()
        
        return widget

    def load_all_players(self):
        """Загружает список всех игроков в системе"""
        try:
            response = requests.get(f"{API_URL}/users/get_all")
            if response.status_code == 200:
                users = response.json()
                self.all_players_list.clear()
                for user in users:
                    if not user.get('is_admin', False):  # Показываем только обычных игроков
                        # Получаем персонажа игрока
                        char_response = requests.get(f"{API_URL}/characters/my/{user['id']}")
                        characters = char_response.json() if char_response.status_code == 200 else []
                        
                        if characters:
                            for char in characters:
                                status = "🎮 В игре" if char.get('session_id') else "📋 Свободен"
                                self.all_players_list.addItem(f"{char['name']} (игрок: {user['username']}) | {status} | ID: {char['id']}")
                        else:
                            self.all_players_list.addItem(f"👤 {user['username']} (без персонажа) | ID: {user['id']}")
        except Exception as e:
            print(f"Error loading players: {e}")

    def on_player_selected(self, item):
        """Выбор игрока из списка"""
        if item is None:
            return
        text = item.text()
        try:
            # Извлекаем ID персонажа
            if "ID: " in text:
                self.selected_player_id = int(text.split("ID: ")[-1])
            else:
                self.selected_player_id = None
            
            # Извлекаем имя
            if " (игрок:" in text:
                self.selected_player_name = text.split(" (игрок:")[0]
            else:
                self.selected_player_name = text.split(" |")[0]
            
            self.view_player_stats_btn.setEnabled(True)
            self.view_player_inv_btn.setEnabled(True)
        except Exception as e:
            print(f"Error parsing player: {e}")
            self.selected_player_id = None
            self.selected_player_name = None

    def view_selected_player_stats(self):
        """Просмотр статистики выбранного игрока"""
        if not self.selected_player_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите игрока")
            return
        self.show_player_stats(self.selected_player_id, self.selected_player_name)

    def view_selected_player_inventory(self):
        """Просмотр инвентаря выбранного игрока"""
        if not self.selected_player_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите игрока")
            return
        self.show_player_inventory(self.selected_player_id, self.selected_player_name)

    def show_player_stats(self, character_id, character_name):
        """Показывает полную статистику игрока"""
        try:
            response = requests.get(f"{API_URL}/characters/my/{self.user_data['id']}")
            if response.status_code == 200:
                characters = response.json()
                character = next((c for c in characters if c['id'] == character_id), None)
                
                if character:
                    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTabWidget, QProgressBar
                    
                    dialog = QDialog(self)
                    dialog.setWindowTitle(f"Статистика игрока - {character_name}")
                    dialog.setMinimumSize(600, 500)
                    dialog.setStyleSheet("background-color: #2c3e50;")
                    
                    layout = QVBoxLayout()
                    
                    char_data = character.get('data', {})
                    level = char_data.get('level', 1)
                    stats = char_data.get('stats', {'strength': 10, 'dexterity': 10, 'intelligence': 10, 'charisma': 10})
                    
                    # Основная информация
                    info_frame = QFrame()
                    info_frame.setStyleSheet("background-color: #34495e; border-radius: 10px; padding: 15px;")
                    info_layout = QVBoxLayout()
                    
                    name_label = QLabel(f"🎭 {character_name}")
                    name_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #e67e22;")
                    name_label.setAlignment(Qt.AlignCenter)
                    info_layout.addWidget(name_label)
                    
                    level_label = QLabel(f"⭐ Уровень: {level}")
                    level_label.setStyleSheet("font-size: 16px; color: #f39c12;")
                    level_label.setAlignment(Qt.AlignCenter)
                    info_layout.addWidget(level_label)
                    
                    # HP/MP
                    hp_mp_layout = QHBoxLayout()
                    hp_label = QLabel(f"❤️ HP: {char_data.get('current_hp', 10)}/{char_data.get('max_hp', 10)}")
                    hp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
                    mp_label = QLabel(f"💙 MP: {char_data.get('current_mp', 5)}/{char_data.get('max_mp', 5)}")
                    mp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
                    hp_mp_layout.addWidget(hp_label)
                    hp_mp_layout.addWidget(mp_label)
                    info_layout.addLayout(hp_mp_layout)
                    
                    info_frame.setLayout(info_layout)
                    layout.addWidget(info_frame)
                    
                    # Характеристики
                    stats_frame = QFrame()
                    stats_frame.setStyleSheet("background-color: #34495e; border-radius: 10px; padding: 15px; margin-top: 10px;")
                    stats_grid = QGridLayout()
                    
                    stat_names = ['💪 Сила', '🏃 Ловкость', '🧠 Интеллект', '💬 Харизма']
                    stat_keys = ['strength', 'dexterity', 'intelligence', 'charisma']
                    
                    for i, (name, key) in enumerate(zip(stat_names, stat_keys)):
                        stat_frame = QFrame()
                        stat_frame.setStyleSheet("background-color: #2c3e50; border-radius: 8px; padding: 10px;")
                        stat_frame_layout = QVBoxLayout()
                        
                        stat_name = QLabel(name)
                        stat_name.setStyleSheet("font-size: 12px; color: #bdc3c7;")
                        stat_value = QLabel(str(stats.get(key, 10)))
                        stat_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #f39c12;")
                        
                        stat_frame_layout.addWidget(stat_name)
                        stat_frame_layout.addWidget(stat_value)
                        stat_frame.setLayout(stat_frame_layout)
                        
                        stats_grid.addWidget(stat_frame, i // 2, i % 2)
                    
                    stats_frame.setLayout(stats_grid)
                    layout.addWidget(stats_frame)
                    
                    close_btn = QPushButton("Закрыть")
                    close_btn.clicked.connect(dialog.accept)
                    layout.addWidget(close_btn)
                    
                    dialog.setLayout(layout)
                    dialog.exec_()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось найти персонажа")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")

    def show_player_inventory(self, character_id, character_name):
        """Показывает инвентарь игрока"""
        try:
            response = requests.get(f"{API_URL}/game/character/{character_id}/inventory")
            if response.status_code == 200:
                data = response.json()
                inventory = data.get('inventory', [])
                equipped = data.get('equipped', [])
                
                from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame, QScrollArea, QPushButton
                
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Инвентарь - {character_name}")
                dialog.setMinimumSize(500, 400)
                dialog.setStyleSheet("background-color: #2c3e50;")
                
                layout = QVBoxLayout()
                
                # Экипировка
                if equipped:
                    equip_label = QLabel("⚔️ ЭКИПИРОВАНО:")
                    equip_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")
                    layout.addWidget(equip_label)
                    
                    for item in equipped:
                        effects = item.get('effects', {})
                        effects_text = ""
                        if effects:
                            eff_list = [f"{k}+{v}" for k, v in effects.items() if v != 0]
                            if eff_list:
                                effects_text = f" ({', '.join(eff_list)})"
                        
                        item_label = QLabel(f"  {item.get('icon', '📦')} {item.get('name', '?')}{effects_text}")
                        item_label.setStyleSheet("font-size: 12px; color: #ecf0f1; padding: 5px;")
                        layout.addWidget(item_label)
                
                # Инвентарь
                if inventory:
                    inv_label = QLabel("📦 ИНВЕНТАРЬ:")
                    inv_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db; margin-top: 10px;")
                    layout.addWidget(inv_label)
                    
                    scroll = QScrollArea()
                    scroll_widget = QWidget()
                    scroll_layout = QVBoxLayout()
                    
                    for item in inventory:
                        qty = f" x{item.get('quantity', 1)}" if item.get('quantity', 1) > 1 else ""
                        effects = item.get('effects', {})
                        effects_text = ""
                        if effects:
                            eff_list = [f"{k}+{v}" for k, v in effects.items() if v != 0]
                            if eff_list:
                                effects_text = f" ({', '.join(eff_list)})"
                        
                        item_label = QLabel(f"  {item.get('icon', '📦')} {item.get('name', '?')}{effects_text}{qty}")
                        item_label.setStyleSheet("font-size: 12px; color: #ecf0f1; padding: 3px;")
                        scroll_layout.addWidget(item_label)
                    
                    scroll_widget.setLayout(scroll_layout)
                    scroll.setWidget(scroll_widget)
                    scroll.setWidgetResizable(True)
                    scroll.setMaximumHeight(300)
                    layout.addWidget(scroll)
                
                if not equipped and not inventory:
                    empty_label = QLabel("Инвентарь пуст")
                    empty_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 20px;")
                    empty_label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(empty_label)
                
                close_btn = QPushButton("Закрыть")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.setLayout(layout)
                dialog.exec_()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить инвентарь")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")

    def start_gm_game(self):
        """Запускает игру для ГМ с выбором сессии"""
        try:
            response = requests.get(f"{API_URL}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                if not sessions:
                    QMessageBox.warning(self, "Ошибка", "Нет доступных сессий. Сначала создайте сессию.")
                    return
                
                dialog = QDialog(self)
                dialog.setWindowTitle("Выбор сессии")
                dialog.setMinimumSize(400, 500)
                dialog.setStyleSheet("background-color: #2c3e50;")
                
                layout = QVBoxLayout()
                
                label = QLabel("Выберите сессию для управления:")
                label.setStyleSheet("color: #ecf0f1; font-size: 14px; padding: 10px;")
                layout.addWidget(label)
                
                sessions_list = QListWidget()
                for session in sessions:
                    sessions_list.addItem(f"{session['name']} (ID: {session['id']})")
                layout.addWidget(sessions_list)
                
                btn_layout = QHBoxLayout()
                select_btn = QPushButton("✅ Войти в игру")
                select_btn.setStyleSheet("background-color: #27ae60;")
                cancel_btn = QPushButton("❌ Отмена")
                cancel_btn.setStyleSheet("background-color: #95a5a6;")
                
                btn_layout.addWidget(select_btn)
                btn_layout.addWidget(cancel_btn)
                layout.addLayout(btn_layout)
                
                dialog.setLayout(layout)
                
                def on_select():
                    current = sessions_list.currentItem()
                    if current:
                        session_text = current.text()
                        session_name = session_text.split(" (ID:")[0]
                        session_id = int(session_text.split("ID: ")[-1].rstrip(")"))
                        
                        session_data = {'id': session_id, 'name': session_name}
                        
                        from db.game_ui.gm_window import GMGameWindow
                        self.gm_game_window = GMGameWindow(self.user_data, session_data, self.logger)
                        self.gm_game_window.show()
                        self.hide()  # Скрываем окно выбора роли
                        dialog.accept()
                    else:
                        QMessageBox.warning(dialog, "Ошибка", "Выберите сессию")
                
                def on_cancel():
                    dialog.reject()
                
                select_btn.clicked.connect(on_select)
                cancel_btn.clicked.connect(on_cancel)
                
                dialog.exec_()
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
            
    def create_player_content(self):
        """Создает контент для игрока (слева персонажи, справа сессии)"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel("Выберите персонажа и сессию для игры")
        title_label.setStyleSheet("font-size: 16px; color: #f39c12; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Основной сплиттер (лево - персонажи, право - сессии)
        splitter = QSplitter(Qt.Horizontal)
        
        # ========== ЛЕВАЯ ПАНЕЛЬ - ПЕРСОНАЖИ ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок персонажей
        char_title = QLabel("🎭 МОИ ПЕРСОНАЖИ")
        char_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #e67e22; padding: 5px;")
        char_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(char_title)
        
        # Список персонажей
        self.player_characters_list = QListWidget()
        self.player_characters_list.setMinimumHeight(400)
        self.player_characters_list.setStyleSheet("""
            QListWidget {
                background-color: #34495e;
                border: 2px solid #e67e22;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #3d566e;
            }
            QListWidget::item:selected {
                background-color: #e67e22;
                color: white;
            }
        """)
        self.player_characters_list.itemClicked.connect(self.on_character_selected)
        left_layout.addWidget(self.player_characters_list)
        
        # Кнопка просмотра характеристик
        self.view_character_btn = QPushButton("📊 Просмотреть характеристики")
        self.view_character_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.view_character_btn.clicked.connect(self.view_selected_character)
        self.view_character_btn.setEnabled(False)
        left_layout.addWidget(self.view_character_btn)
        
        # Кнопка создания персонажа
        create_char_btn = QPushButton("➕ Создать персонажа")
        create_char_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        create_char_btn.clicked.connect(self.create_character)
        left_layout.addWidget(create_char_btn)
        
        left_panel.setLayout(left_layout)
        
        # ========== ПРАВАЯ ПАНЕЛЬ - СЕССИИ ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок сессий
        session_title = QLabel("🎮 ДОСТУПНЫЕ СЕССИИ")
        session_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71; padding: 5px;")
        session_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(session_title)
        
        # Список сессий
        self.available_sessions_list = QListWidget()
        self.available_sessions_list.setMinimumHeight(400)
        self.available_sessions_list.setStyleSheet("""
            QListWidget {
                background-color: #34495e;
                border: 2px solid #2ecc71;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #3d566e;
            }
            QListWidget::item:selected {
                background-color: #2ecc71;
                color: white;
            }
        """)
        self.available_sessions_list.itemClicked.connect(self.on_session_selected_for_player)
        right_layout.addWidget(self.available_sessions_list)
        
        # Кнопка создания сессии
        create_session_btn = QPushButton("➕ Создать сессию")
        create_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        create_session_btn.clicked.connect(lambda: self.create_session_dialog(None))
        right_layout.addWidget(create_session_btn)
        
        right_panel.setLayout(right_layout)
        
        # Добавляем панели в сплиттер
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 450])
        
        layout.addWidget(splitter)
        
        # ========== НИЖНЯЯ ПАНЕЛЬ ==========
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        # Информация о выборе
        self.selection_info = QLabel("⚡ Выберите персонажа и сессию")
        self.selection_info.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: #f39c12;
                font-size: 13px;
                padding: 10px;
                border-radius: 8px;
            }
        """)
        bottom_layout.addWidget(self.selection_info, 2)
        
        # Кнопка входа в игру
        self.start_game_btn = QPushButton("🎮 ВОЙТИ В ИГРУ 🎮")
        self.start_game_btn.setMinimumHeight(60)
        self.start_game_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.start_game_btn.clicked.connect(self.start_player_game)
        self.start_game_btn.setEnabled(False)
        bottom_layout.addWidget(self.start_game_btn, 1)
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_player_data)
        bottom_layout.addWidget(refresh_btn, 1)
        
        # Кнопка настроек
        settings_btn = QPushButton("⚙️ Настройки")
        settings_btn.setMinimumHeight(40)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        settings_btn.clicked.connect(self.open_connection_settings)
        bottom_layout.addWidget(settings_btn, 1)
        
        bottom_panel.setLayout(bottom_layout)
        layout.addWidget(bottom_panel)
        
        # Boosty
        boosty = QLabel("Boosty")
        boosty.setAlignment(Qt.AlignCenter)
        boosty.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 10px;")
        layout.addWidget(boosty)
        
        widget.setLayout(layout)
        
        # Инициализируем переменные
        self.selected_character_id = None
        self.selected_character_name = None
        self.selected_session_id = None
        self.selected_session_name = None
        
        # Загружаем данные
        self.refresh_player_data()
        
        return widget
    
    # ============ Методы для игрока ============
    
    def refresh_player_data(self):
        """Обновляет данные игрока (персонажи и сессии)"""
        self.load_my_characters()
        self.load_available_sessions()
    
    def load_my_characters(self):
        """Загружает персонажей игрока"""
        try:
            response = requests.get(f"{API_URL}/characters/my/{self.user_data['id']}")
            if response.status_code == 200:
                characters = response.json()
                self.player_characters_list.clear()
                for char in characters:
                    if char.get('session_id'):
                        # Уже в игре
                        self.player_characters_list.addItem(f"🎮 {char['name']} (ID: {char['id']})")
                    else:
                        # Свободный
                        self.player_characters_list.addItem(f"📋 {char['name']} (ID: {char['id']})")
        except Exception as e:
            print(f"Error loading characters: {e}")
    
    def load_available_sessions(self):
        """Загружает доступные сессии"""
        try:
            response = requests.get(f"{API_URL}/sessions/available/{self.user_data['id']}")
            if response.status_code == 200:
                sessions = response.json()
                self.available_sessions_list.clear()
                for session in sessions:
                    # Показываем количество участников
                    self.available_sessions_list.addItem(f"🎮 {session['name']} (ID: {session['id']})")
        except Exception as e:
            print(f"Error loading sessions: {e}")
        
    def on_character_selected(self, item):
        """Выбор персонажа"""
        if item is None:
            return
        text = item.text()
        try:
            # Извлекаем ID (учитывая возможные префиксы)
            if "ID: " in text:
                id_part = text.split("ID: ")[-1].rstrip(")")
                self.selected_character_id = int(id_part)
            else:
                self.selected_character_id = None
                return
            
            # Извлекаем имя (очищаем от префиксов)
            name_part = text.split(" (ID:")[0]
            # Убираем эмодзи если есть
            if "📋 " in name_part:
                name_part = name_part.replace("📋 ", "")
            if "🎮 " in name_part:
                name_part = name_part.replace("🎮 ", "")
            self.selected_character_name = name_part
            
            # Проверяем, не в игре ли уже персонаж
            if "[В игре]" in text:
                QMessageBox.warning(self, "Внимание", 
                    f"Персонаж '{self.selected_character_name}' уже участвует в другой сессии.\n"
                    "Выберите другого персонажа или дождитесь окончания сессии.")
                self.selected_character_id = None
                self.selected_character_name = None
                self.view_character_btn.setEnabled(False)
                self.update_selection_info()
                self.check_can_start_game()
                return
            
            self.view_character_btn.setEnabled(True)
            self.update_selection_info()
            self.check_can_start_game()
        except Exception as e:
            print(f"Error parsing character: {e}")
            self.selected_character_id = None
            self.selected_character_name = None
    
    def on_session_selected_for_player(self, item):
        """Выбор сессии для игрока"""
        if item is None:
            return
        text = item.text()
        try:
            self.selected_session_id = int(text.split("ID: ")[-1].rstrip(")"))
            self.selected_session_name = text.split(" (ID:")[0]
            self.update_selection_info()
            self.check_can_start_game()
        except Exception as e:
            print(f"Error parsing session: {e}")
            self.selected_session_id = None
            self.selected_session_name = None
    
    def update_selection_info(self):
        """Обновляет информацию о выборе"""
        char_text = self.selected_character_name if self.selected_character_name else "не выбран"
        session_text = self.selected_session_name if self.selected_session_name else "не выбрана"
        self.selection_info.setText(f"⚡ Персонаж: {char_text} | Сессия: {session_text}")
    
    def check_can_start_game(self):
        """Проверяет можно ли начать игру"""
        can_start = self.selected_character_id is not None and self.selected_session_id is not None
        self.start_game_btn.setEnabled(can_start)
    
    def view_selected_character(self):
        """Просмотр характеристик выбранного персонажа"""
        if not self.selected_character_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите персонажа")
            return
        self.show_character_stats(self.selected_character_id, self.selected_character_name)
    
    def show_character_stats(self, character_id, character_name):
        """Показывает диалог с характеристиками и инвентарем персонажа"""
        try:
            # Получаем данные персонажа
            response = requests.get(f"{API_URL}/characters/my/{self.user_data['id']}")
            if response.status_code == 200:
                characters = response.json()
                character = next((c for c in characters if c['id'] == character_id), None)
                
                if character:
                    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTabWidget, QListWidget, QPushButton
                    
                    dialog = QDialog(self)
                    dialog.setWindowTitle(f"Персонаж - {character_name}")
                    dialog.setMinimumSize(600, 500)
                    dialog.setStyleSheet("background-color: #2c3e50;")
                    
                    layout = QVBoxLayout()
                    
                    # Вкладки
                    tabs = QTabWidget()
                    tabs.setStyleSheet("""
                        QTabWidget::pane {
                            background-color: #34495e;
                            border-radius: 8px;
                        }
                        QTabBar::tab {
                            background-color: #2c3e50;
                            color: #ecf0f1;
                            padding: 8px 20px;
                            margin-right: 2px;
                        }
                        QTabBar::tab:selected {
                            background-color: #3498db;
                        }
                    """)
                    
                    # ========== Вкладка характеристик ==========
                    stats_tab = QWidget()
                    stats_layout = QVBoxLayout()
                    
                    # Основная информация
                    info_frame = QFrame()
                    info_frame.setStyleSheet("background-color: #2c3e50; border-radius: 10px; padding: 15px;")
                    info_layout = QVBoxLayout()
                    
                    name_label = QLabel(f"🎭 {character.get('name', character_name)}")
                    name_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #e67e22;")
                    name_label.setAlignment(Qt.AlignCenter)
                    info_layout.addWidget(name_label)
                    
                    # Данные из JSON
                    char_data = character.get('data', {})
                    level = char_data.get('level', 1)
                    
                    level_label = QLabel(f"Уровень: {level}")
                    level_label.setStyleSheet("font-size: 16px; color: #3498db;")
                    level_label.setAlignment(Qt.AlignCenter)
                    info_layout.addWidget(level_label)
                    
                    # HP/MP
                    hp_mp_layout = QHBoxLayout()
                    hp_label = QLabel(f"❤️ HP: {char_data.get('current_hp', 10)}/{char_data.get('max_hp', 10)}")
                    hp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
                    mp_label = QLabel(f"💙 MP: {char_data.get('current_mp', 5)}/{char_data.get('max_mp', 5)}")
                    mp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
                    hp_mp_layout.addWidget(hp_label)
                    hp_mp_layout.addWidget(mp_label)
                    info_layout.addLayout(hp_mp_layout)
                    
                    info_frame.setLayout(info_layout)
                    stats_layout.addWidget(info_frame)
                    
                    # Характеристики
                    stats_frame = QFrame()
                    stats_frame.setStyleSheet("background-color: #2c3e50; border-radius: 10px; padding: 15px; margin-top: 10px;")
                    stats_grid = QGridLayout()
                    
                    stats = char_data.get('stats', {'strength': 10, 'dexterity': 10, 'intelligence': 10, 'charisma': 10})
                    stat_names = ['💪 Сила', '🏃 Ловкость', '🧠 Интеллект', '💬 Харизма']
                    stat_keys = ['strength', 'dexterity', 'intelligence', 'charisma']
                    
                    for i, (name, key) in enumerate(zip(stat_names, stat_keys)):
                        stat_frame = QFrame()
                        stat_frame.setStyleSheet("background-color: #34495e; border-radius: 8px; padding: 10px;")
                        stat_frame_layout = QVBoxLayout()
                        
                        stat_name = QLabel(name)
                        stat_name.setStyleSheet("font-size: 12px; color: #bdc3c7;")
                        stat_value = QLabel(str(stats.get(key, 10)))
                        stat_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #f39c12;")
                        
                        stat_frame_layout.addWidget(stat_name)
                        stat_frame_layout.addWidget(stat_value)
                        stat_frame.setLayout(stat_frame_layout)
                        
                        stats_grid.addWidget(stat_frame, i // 2, i % 2)
                    
                    stats_frame.setLayout(stats_grid)
                    stats_layout.addWidget(stats_frame)
                    stats_tab.setLayout(stats_layout)
                    
                    # ========== Вкладка инвентаря ==========
                    inv_tab = QWidget()
                    inv_layout = QVBoxLayout()
                    
                    # Пытаемся получить инвентарь через API
                    try:
                        inv_response = requests.get(f"{API_URL}/game/character/{character_id}/inventory")
                        if inv_response.status_code == 200:
                            inv_data = inv_response.json()
                            inventory = inv_data.get('inventory', [])
                            equipped = inv_data.get('equipped', [])
                            
                            # Экипировка
                            if equipped:
                                equip_group = QFrame()
                                equip_group.setStyleSheet("background-color: #2c3e50; border-radius: 8px; padding: 10px;")
                                equip_layout = QVBoxLayout()
                                
                                equip_label = QLabel("⚔️ ЭКИПИРОВАНО:")
                                equip_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")
                                equip_layout.addWidget(equip_label)
                                
                                for item in equipped:
                                    effects = item.get('effects', {})
                                    effects_text = ""
                                    if effects:
                                        eff_list = [f"{k}+{v}" for k, v in effects.items() if v != 0]
                                        if eff_list:
                                            effects_text = f" ({', '.join(eff_list)})"
                                    
                                    item_label = QLabel(f"  {item.get('icon', '📦')} {item.get('name', '?')}{effects_text}")
                                    item_label.setStyleSheet("font-size: 12px; color: #ecf0f1;")
                                    equip_layout.addWidget(item_label)
                                
                                equip_group.setLayout(equip_layout)
                                inv_layout.addWidget(equip_group)
                            
                            # Остальной инвентарь
                            if inventory:
                                inv_group = QFrame()
                                inv_group.setStyleSheet("background-color: #2c3e50; border-radius: 8px; padding: 10px; margin-top: 10px;")
                                inv_group_layout = QVBoxLayout()
                                
                                inv_label = QLabel("📦 ИНВЕНТАРЬ:")
                                inv_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db;")
                                inv_group_layout.addWidget(inv_label)
                                
                                # Создаем скролл область для инвентаря
                                inv_scroll = QScrollArea()
                                inv_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
                                inv_scroll_widget = QWidget()
                                inv_scroll_layout = QVBoxLayout()
                                
                                for item in inventory:
                                    qty = f" x{item.get('quantity', 1)}" if item.get('quantity', 1) > 1 else ""
                                    effects = item.get('effects', {})
                                    effects_text = ""
                                    if effects:
                                        eff_list = [f"{k}+{v}" for k, v in effects.items() if v != 0]
                                        if eff_list:
                                            effects_text = f" ({', '.join(eff_list)})"
                                    
                                    item_label = QLabel(f"  {item.get('icon', '📦')} {item.get('name', '?')}{effects_text}{qty}")
                                    item_label.setStyleSheet("font-size: 12px; color: #ecf0f1; padding: 3px;")
                                    inv_scroll_layout.addWidget(item_label)
                                
                                inv_scroll_widget.setLayout(inv_scroll_layout)
                                inv_scroll.setWidget(inv_scroll_widget)
                                inv_scroll.setWidgetResizable(True)
                                inv_scroll.setMaximumHeight(200)
                                
                                inv_group_layout.addWidget(inv_scroll)
                                inv_group.setLayout(inv_group_layout)
                                inv_layout.addWidget(inv_group)
                            
                            if not equipped and not inventory:
                                empty_label = QLabel("Инвентарь пуст")
                                empty_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 20px;")
                                empty_label.setAlignment(Qt.AlignCenter)
                                inv_layout.addWidget(empty_label)
                        else:
                            # Если API нет, показываем базовую информацию
                            no_api_label = QLabel("Данные инвентаря временно недоступны")
                            no_api_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 20px;")
                            no_api_label.setAlignment(Qt.AlignCenter)
                            inv_layout.addWidget(no_api_label)
                            
                    except Exception as e:
                        error_label = QLabel(f"Ошибка загрузки инвентаря: {str(e)}")
                        error_label.setStyleSheet("color: #e74c3c; font-size: 12px; padding: 20px;")
                        error_label.setWordWrap(True)
                        inv_layout.addWidget(error_label)
                    
                    inv_layout.addStretch()
                    inv_tab.setLayout(inv_layout)
                    
                    tabs.addTab(stats_tab, "📊 Характеристики")
                    tabs.addTab(inv_tab, "📦 Инвентарь")
                    
                    layout.addWidget(tabs)
                    
                    close_btn = QPushButton("Закрыть")
                    close_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e74c3c;
                            margin-top: 10px;
                        }
                        QPushButton:hover {
                            background-color: #c0392b;
                        }
                    """)
                    close_btn.clicked.connect(dialog.accept)
                    layout.addWidget(close_btn)
                    
                    dialog.setLayout(layout)
                    dialog.exec_()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось найти персонажа")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить данные персонажа")
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def start_player_game(self):
        """Запускает игру для игрока с выбранным персонажем и сессией"""
        if not self.selected_character_id:
            QMessageBox.warning(self, "Ошибка", "Выберите персонажа")
            return
        
        if not self.selected_session_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сессию")
            return
        
        try:
            response = requests.put(f"{API_URL}/characters/{self.selected_character_id}/attach_session", 
                                    json={'session_id': self.selected_session_id})
            
            if response.status_code == 200:
                char_response = requests.get(f"{API_URL}/characters/my/{self.user_data['id']}")
                if char_response.status_code == 200:
                    characters = char_response.json()
                    character = next((c for c in characters if c['id'] == self.selected_character_id), None)
                    
                    if character:
                        session_data = {'id': self.selected_session_id, 'name': self.selected_session_name}
                        
                        from db.game_ui.player_window import PlayerGameWindow
                        self.player_game_window = PlayerGameWindow(self.user_data, session_data, character, self.logger)
                        self.player_game_window.show()
                        self.hide()  # Скрываем окно выбора роли
                        
                        self.logger.log_action('enter_game', 
                                            session_id=self.selected_session_id,
                                            character_id=self.selected_character_id)
                    else:
                        QMessageBox.warning(self, "Ошибка", "Не удалось найти персонажа")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось получить данные персонажа")
            else:
                error_msg = response.json().get('error', 'Неизвестная ошибка')
                QMessageBox.warning(self, "Ошибка", f"Не удалось привязать персонажа к сессии: {error_msg}")
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def create_character(self):
        """Создает нового персонажа"""
        name, ok = QInputDialog.getText(self, "Создание персонажа", "Имя персонажа:")
        if ok and name:
            try:
                response = requests.post(f"{API_URL}/characters", json={
                    'name': name,
                    'data': {'level': 1, 'stats': {'strength': 10, 'dexterity': 10, 'intelligence': 10, 'charisma': 10}},
                    'user_id': self.user_data['id']
                })
                if response.status_code == 201:
                    QMessageBox.information(self, "Успех", f"Персонаж '{name}' создан!")
                    self.logger.log_action('create_character', details={'character_name': name})
                    self.refresh_player_data()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать персонажа")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    # ============ Методы для ГМ (управление) ============
    
    def show_gm_sessions(self):
        """Показывает управление сессиями"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление сессиями")
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet("background-color: #2c3e50;")
        
        layout = QVBoxLayout()
        
        try:
            response = requests.get(f"{API_URL}/sessions")
            if response.status_code == 200:
                sessions = response.json()
                sessions_list = QListWidget()
                for session in sessions:
                    sessions_list.addItem(f"{session['name']} (ID: {session['id']})")
                layout.addWidget(sessions_list)
        except Exception as e:
            layout.addWidget(QLabel(f"Ошибка: {e}"))
        
        create_btn = QPushButton("+ Создать сессию")
        create_btn.clicked.connect(lambda: self.create_session_dialog(dialog))
        layout.addWidget(create_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def create_session_dialog(self, parent_dialog):
        """Диалог создания сессии"""
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
                    parent_dialog.accept()
                    self.refresh_player_data()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать сессию")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")
    
    def show_gm_characters(self):
        """Показывает управление персонажами"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление персонажами")
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet("background-color: #2c3e50;")
        
        layout = QVBoxLayout()
        
        try:
            response = requests.get(f"{API_URL}/characters")
            if response.status_code == 200:
                characters = response.json()
                characters_list = QListWidget()
                for char in characters:
                    characters_list.addItem(f"{char['name']} (ID: {char['id']})")
                layout.addWidget(characters_list)
        except Exception as e:
            layout.addWidget(QLabel(f"Ошибка: {e}"))

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def show_gm_vpn_config(self):
        """Показывает настройки VPN"""
        dialog = QDialog(self)
        dialog.setWindowTitle("VPN настройки")
        dialog.setMinimumSize(400, 300)
        dialog.setStyleSheet("background-color: #2c3e50;")
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Настройка VPN для сессии"))
        layout.addWidget(QLabel("IP адрес:"))
        
        ip_input = QLineEdit()
        ip_input.setPlaceholderText("Например: 192.168.1.100")
        layout.addWidget(ip_input)
        
        layout.addWidget(QLabel("Порт:"))
        port_input = QLineEdit()
        port_input.setText("25565")
        layout.addWidget(port_input)
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(lambda: self.save_vpn_settings_dialog(dialog, ip_input.text(), port_input.text()))
        layout.addWidget(save_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def save_vpn_settings_dialog(self, dialog, vpn_address, vpn_port):
        """Сохраняет VPN настройки"""
        QMessageBox.information(self, "Информация", "VPN настройки сохранены!")
        dialog.accept()
    
    # ============ Вспомогательные методы ============
    
    def clear_main_layout(self):
        """Очищает главный layout"""
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def back_to_roles(self):
        """Возврат к выбору роли"""
        self.show_role_selection()
        self.current_role = None
        self.current_view = None
        self.logger.log_action('exit_role')
    
    def closeEvent(self, event):
        """При закрытии окна"""
        self.logger.log_action('logout', details={'username': self.user_data['username']})
        event.accept()