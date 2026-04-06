# db/game_ui/gm_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QLabel, QPushButton, QScrollArea, QFrame,
                             QSplitter, QMessageBox, QComboBox, QTextEdit,
                             QInputDialog, QMenu, QAction, QToolButton, QTabWidget, 
                             QListWidget, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from typing import Dict, List, Optional

from db.game_ui.widgets import (PlayerStatWidget, GlobalEventsWidget, InventoryDialog)
from db.game_ui.api import GameAPI
from db.gui.logger_client import LoggerClient


class GMGameWindow(QMainWindow):
    """Основное окно Гейммастера для управления игрой"""
    
    def __init__(self, user_data: Dict, session_data: Dict, logger: LoggerClient):
        super().__init__()
        self.user_data = user_data
        self.session_data = session_data
        self.logger = logger
        self.session_id = session_data.get('id')
        self.game_api = GameAPI(user_data['id'], is_admin=True)
        
        self.player_widgets = {}  # character_id -> widget
        self.players_data = {}    # character_id -> data
        
        self.initUI()
        self.load_players()
        self.start_auto_refresh()
        
        # Логируем открытие окна ГМ
        self.logger.log_action('open_gm_window', session_id=self.session_id)
    
    def initUI(self):
        self.setWindowTitle(f"ДПЖ - Гейммастер | Сессия: {self.session_data.get('name', 'Unknown')}")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet(self.get_stylesheet())
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Верхняя панель с настройками
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Основной контент (сплиттер)
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Левая часть - игроки
        players_widget = self.create_players_panel()
        content_splitter.addWidget(players_widget)
        
        # Правая часть - логи и события
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([900, 500])
        main_layout.addWidget(content_splitter)
        
        central_widget.setLayout(main_layout)
    
    def create_top_bar(self) -> QWidget:
        """Создает верхнюю панель с настройками"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Название сессии
        session_label = QLabel(f"📌 Сессия: {self.session_data.get('name', '?')}")
        session_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e67e22;")
        layout.addWidget(session_label)
        
        layout.addStretch()
        
        # Кнопка добавления выделенного элемента
        add_element_btn = QPushButton("✨ Добавить элемент")
        add_element_btn.clicked.connect(self.add_extracted_element)
        layout.addWidget(add_element_btn)
        
        # Кнопка добавления предмета
        add_item_btn = QPushButton("➕ Добавить предмет")
        add_item_btn.clicked.connect(self.add_item_to_player)
        layout.addWidget(add_item_btn)
        
        # Кнопка глобального события
        global_event_btn = QPushButton("🌍 Глобальное событие")
        global_event_btn.clicked.connect(self.add_global_event_dialog)
        layout.addWidget(global_event_btn)
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.load_players)
        layout.addWidget(refresh_btn)
        
        # Кнопка настроек (шестеренка)
        settings_btn = QToolButton()
        settings_btn.setText("⚙️")
        settings_btn.setPopupMode(QToolButton.InstantPopup)
        
        settings_menu = QMenu()
        exit_action = QAction("🚪 Выйти из сессии", self)
        exit_action.triggered.connect(self.exit_session)
        settings_menu.addAction(exit_action)
        
        disconnect_action = QAction("🔌 Настройки подключения", self)
        disconnect_action.triggered.connect(self.open_connection_settings)
        settings_menu.addAction(disconnect_action)
        
        settings_menu.addSeparator()
        
        close_action = QAction("❌ Закрыть окно", self)
        close_action.triggered.connect(self.close)
        settings_menu.addAction(close_action)
        
        settings_btn.setMenu(settings_menu)
        layout.addWidget(settings_btn)
        
        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-bottom: 2px solid #e67e22;
            }
            QPushButton {
                background-color: #3498db;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        return widget
    
    def create_players_panel(self) -> QWidget:
        """Создает панель с игроками"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("👥 ИГРОКИ В СЕССИИ")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f39c12; padding: 5px;")
        layout.addWidget(title)
        
        # Создаем контейнер для игроков
        self.players_container = QWidget()
        self.players_layout = QVBoxLayout()  # ← ЭТО ВАЖНО!
        self.players_layout.setSpacing(10)
        self.players_container.setLayout(self.players_layout)
        
        scroll = QScrollArea()
        scroll.setWidget(self.players_container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #2c3e50; }")
        
        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget
    
    def add_extracted_element(self):
        """Добавляет новый выделенный элемент (локацию, персонажа, монстра, предмет)"""
        # Выбираем тип элемента
        element_types = ["Локация", "Персонаж", "Монстр", "Предмет", "Событие"]
        element_type, ok = QInputDialog.getItem(
            self, "Добавление элемента",
            "Выберите тип элемента:", element_types, 0, False
        )
        
        if not ok:
            return
        
        # Вводим название
        name, ok = QInputDialog.getText(self, "Добавление элемента",
                                    f"Введите название {element_type.lower()}:")
        if not ok or not name:
            return
        
        # Вводим описание/контекст
        description, ok = QInputDialog.getText(self, "Добавление элемента",
                                            f"Введите описание/контекст для {name}:",
                                            QLineEdit.MultiLine)
        if not ok:
            description = ""
        
        # Логируем добавление
        action_name = f"gm_add_{element_type.lower()}"
        self.logger.log_action(
            action_name,
            session_id=self.session_id,
            details={
                'name': name,
                'type': element_type,
                'description': description
            }
        )
        
        # Показываем в глобальных событиях
        self.game_api.add_global_event(
            self.session_id,
            f"📌 ГМ добавил {element_type.lower()}: {name}"
        )
        
        QMessageBox.information(self, "Успех", 
            f"Элемент '{name}' типа '{element_type}' добавлен и сохранен в лог!")

    def create_right_panel(self) -> QWidget:
        """Создает правую панель с логами и событиями"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Выделенные элементы из сюжета
        self.extracted_widget = ExtractedElementsWidget(self.logger)
        self.extracted_widget.element_selected.connect(self.on_element_selected)
        layout.addWidget(self.extracted_widget)
        
        # Глобальные события
        self.events_widget = GlobalEventsWidget(self.session_id, self.game_api, self)
        layout.addWidget(self.events_widget)
        
        # Логи действий
        logs_label = QLabel("📜 ЛОГИ ДЕЙСТВИЙ")
        logs_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12; margin-top: 10px;")
        layout.addWidget(logs_label)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #ecf0f1;
                font-family: monospace;
                font-size: 11px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.logs_text)
        
        widget.setLayout(layout)
        return widget

    def on_element_selected(self, element):
        """Обработка выбора элемента из сюжета"""
        QMessageBox.information(self, "Информация об элементе",
            f"Тип: {element['type']}\n"
            f"Название: {element['name']}\n"
            f"Контекст: {element.get('context', 'Нет контекста')}"
        )
    
    def load_players(self):
        """Загружает список игроков в сессии"""
        players = self.game_api.get_session_players(self.session_id)
        
        # Проверяем, что players_layout существует
        if not hasattr(self, 'players_layout') or self.players_layout is None:
            print("Error: players_layout not initialized")
            return
        
        # Очищаем контейнер
        for i in reversed(range(self.players_layout.count())):
            item = self.players_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        self.player_widgets.clear()
        self.players_data.clear()
        
        # Добавляем игроков вертикально
        for player in players:
            character = player.get('character', {})
            if character:
                character_id = character.get('id')
                self.players_data[character_id] = player
                
                gm_widget = PlayerStatWidget(player)
                gm_widget.hp_changed.connect(self.update_player_hp)
                gm_widget.mp_changed.connect(self.update_player_mp)
                gm_widget.open_inventory.connect(self.open_player_inventory)
                
                # Проверяем наличие сигнала inspect_stats
                if hasattr(gm_widget, 'inspect_stats'):
                    gm_widget.inspect_stats.connect(self.view_player_stats)
                
                self.player_widgets[character_id] = gm_widget
                self.players_layout.addWidget(gm_widget)
        
        # Загружаем логи и события
        self.load_logs()
        if hasattr(self, 'events_widget'):
            self.events_widget.load_events()
    
    def load_logs(self):
        """Загружает последние логи"""
        logs = self.game_api.get_character_logs(0, limit=50)  # 0 = все логи для ГМ
        self.logs_text.clear()
        
        for log in logs[:30]:  # Показываем последние 30
            time = log.get('timestamp', '?')[:19] if log.get('timestamp') else '?'
            action = log.get('action_name', '?')
            performer = log.get('performer_name', '?')
            details = log.get('details', {})
            
            log_line = f"[{time}] {performer}: {action}"
            if details:
                log_line += f" ({details})"
            
            self.logs_text.append(log_line)
    
    def update_player_hp(self, character_id: int, new_hp: int):
        """Обновляет HP игрока"""
        if self.game_api.update_character_stats(character_id, {'current_hp': new_hp}):
            self.logger.log_action('gm_update_hp', 
                                   character_id=character_id,
                                   details={'new_hp': new_hp})
            self.load_players()  # Обновляем отображение
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить HP")
    
    def update_player_mp(self, character_id: int, new_mp: int):
        """Обновляет MP игрока"""
        if self.game_api.update_character_stats(character_id, {'current_mp': new_mp}):
            self.logger.log_action('gm_update_mp',
                                   character_id=character_id,
                                   details={'new_mp': new_mp})
            self.load_players()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить MP")
    
    def open_player_inventory(self, character_id: int):
        """Открывает инвентарь игрока"""
        character = self.players_data.get(character_id, {}).get('character', {})
        items = self.game_api.get_character_inventory(character_id)
        
        dialog = InventoryDialog(
            character_id,
            character.get('name', 'Unknown'),
            items,
            self.game_api,
            self
        )
        dialog.exec_()
        self.load_players()  # Обновляем после закрытия
    
    def add_item_to_player(self):
        """Добавляет предмет выбранному игроку"""
        if not self.player_widgets:
            QMessageBox.warning(self, "Ошибка", "Нет игроков в сессии")
            return
        
        # Выбираем игрока
        players_list = list(self.players_data.values())
        player_names = [f"{p.get('character', {}).get('name', '?')} ({p.get('username', '?')})" 
                       for p in players_list]
        
        from PyQt5.QtWidgets import QInputDialog
        player_idx, ok = QInputDialog.getItem(self, "Выбор игрока", 
                                              "Выберите игрока:", player_names, 0, False)
        if not ok:
            return
        
        character_id = players_list[player_idx].get('character', {}).get('id')
        
        # Вводим название предмета
        item_name, ok = QInputDialog.getText(self, "Добавление предмета",
                                            "Название предмета:")
        if not ok or not item_name:
            return
        
        # Вводим количество
        quantity, ok = QInputDialog.getInt(self, "Количество", 
                                          "Количество:", 1, 1, 999)
        if not ok:
            return
        
        # Добавляем эффекты (опционально)
        add_effects = QMessageBox.question(self, "Эффекты", 
                                           "Добавить эффекты к предмету?",
                                           QMessageBox.Yes | QMessageBox.No)
        
        effects = {}
        if add_effects == QMessageBox.Yes:
            strength, ok = QInputDialog.getInt(self, "Эффекты", "Сила:", 0, -10, 10)
            if ok and strength != 0:
                effects['strength'] = strength
            
            dexterity, ok = QInputDialog.getInt(self, "Эффекты", "Ловкость:", 0, -10, 10)
            if ok and dexterity != 0:
                effects['dexterity'] = dexterity
            
            intelligence, ok = QInputDialog.getInt(self, "Эффекты", "Интеллект:", 0, -10, 10)
            if ok and intelligence != 0:
                effects['intelligence'] = intelligence
            
            charisma, ok = QInputDialog.getInt(self, "Эффекты", "Харизма:", 0, -10, 10)
            if ok and charisma != 0:
                effects['charisma'] = charisma
        
        if self.game_api.add_item_to_inventory(character_id, item_name, quantity, effects):
            QMessageBox.information(self, "Успех", f"Предмет '{item_name}' добавлен!")
            self.logger.log_action('gm_add_item',
                                   character_id=character_id,
                                   details={'item': item_name, 'quantity': quantity})
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить предмет")
    
    def add_global_event_dialog(self):
        """Диалог добавления глобального события"""
        event_text, ok = QInputDialog.getText(self, "Глобальное событие",
                                             "Введите событие:")
        if ok and event_text:
            if self.game_api.add_global_event(self.session_id, event_text):
                self.events_widget.load_events()
                self.logger.log_action('gm_global_event',
                                       session_id=self.session_id,
                                       details={'event': event_text})
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить событие")
    
    def start_auto_refresh(self):
        """Автоматическое обновление каждые 5 секунд"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(5000)
    
    def auto_refresh(self):
        """Автоматическое обновление данных"""
        self.load_players()
    
    def exit_session(self):
        """Выход из сессии и возврат к выбору роли"""
        reply = QMessageBox.question(self, "Выход", 
                                    "Вы уверены, что хотите выйти из сессии?\n\n"
                                    "Вы вернетесь в главное меню.",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logger.log_action('gm_exit_session', session_id=self.session_id)
            self.close()
            # Возвращаемся к окну выбора роли
            from db.gui.role_window import RoleWindow
            self.role_window = RoleWindow(self.user_data)
            self.role_window.show()
    
    def open_connection_settings(self):
        """Открывает настройки подключения"""
        from db.gui.config_client import client_config
        client_config.show_config_dialog(self)
    
    def get_stylesheet(self) -> str:
        return """
            QMainWindow {
                background-color: #1a1a2e;
            }
            QLabel {
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QToolButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 6px;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #3d566e;
            }
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
        """
    
    def closeEvent(self, event):
        """При закрытии окна"""
        self.refresh_timer.stop()
        self.logger.log_action('gm_close_window', session_id=self.session_id)
        event.accept()
        # Показываем окно выбора роли, если оно было скрыто
        from db.gui.role_window import RoleWindow
        if hasattr(self, 'user_data'):
            self.role_window = RoleWindow(self.user_data)
            self.role_window.show()

class ExtractedElementsWidget(QWidget):
    """Виджет для отображения выделенных элементов из сюжета"""
    
    element_selected = pyqtSignal(dict)
    
    def __init__(self, logger_client, parent=None):
        super().__init__(parent)
        self.logger = logger_client
        self.elements = {
            'locations': [],
            'characters': [],
            'monsters': [],
            'items': []
        }
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        title = QLabel("📋 ВЫДЕЛЕННЫЕ ЭЛЕМЕНТЫ ИЗ СЮЖЕТА")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #e67e22;")
        layout.addWidget(title)
        
        # Вкладки для типов элементов
        tabs = QTabWidget()
        
        # Локации
        locations_tab = QWidget()
        locations_layout = QVBoxLayout()
        self.locations_list = QListWidget()
        self.locations_list.itemClicked.connect(lambda item: self.on_element_clicked(item, 'location'))
        locations_layout.addWidget(self.locations_list)
        locations_tab.setLayout(locations_layout)
        
        # Персонажи
        characters_tab = QWidget()
        characters_layout = QVBoxLayout()
        self.characters_list = QListWidget()
        self.characters_list.itemClicked.connect(lambda item: self.on_element_clicked(item, 'character'))
        characters_layout.addWidget(self.characters_list)
        characters_tab.setLayout(characters_layout)
        
        # Монстры
        monsters_tab = QWidget()
        monsters_layout = QVBoxLayout()
        self.monsters_list = QListWidget()
        self.monsters_list.itemClicked.connect(lambda item: self.on_element_clicked(item, 'monster'))
        monsters_layout.addWidget(self.monsters_list)
        monsters_tab.setLayout(monsters_layout)
        
        # Предметы
        items_tab = QWidget()
        items_layout = QVBoxLayout()
        self.items_list = QListWidget()
        self.items_list.itemClicked.connect(lambda item: self.on_element_clicked(item, 'item'))
        items_layout.addWidget(self.items_list)
        items_tab.setLayout(items_layout)
        
        tabs.addTab(locations_tab, "📍 Локации")
        tabs.addTab(characters_tab, "👥 Персонажи")
        tabs.addTab(monsters_tab, "👾 Монстры")
        tabs.addTab(items_tab, "⚔️ Предметы")
        
        layout.addWidget(tabs)
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.clicked.connect(self.load_elements)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
    
    def load_elements(self):
        """Загружает элементы из логов"""
        if not self.logger:
            return
            
        story_actions = self.logger.get_story_actions()
        
        self.elements = {
            'locations': [],
            'characters': [],
            'monsters': [],
            'items': []
        }
        
        for action in story_actions:
            action_name = action.get('action_name', '')
            details = action.get('details', {})
            
            if action_name == 'story_location':
                self.elements['locations'].append({
                    'name': details.get('location', 'Unknown'),
                    'context': details.get('context', '')
                })
            elif action_name == 'story_character':
                self.elements['characters'].append({
                    'name': details.get('character', 'Unknown'),
                    'context': details.get('context', '')
                })
            elif action_name == 'story_monster':
                self.elements['monsters'].append({
                    'name': details.get('monster', 'Unknown'),
                    'context': details.get('context', '')
                })
            elif action_name == 'story_item':
                self.elements['items'].append({
                    'name': details.get('item', 'Unknown'),
                    'context': details.get('context', '')
                })
        
        self.update_display()
    
    def update_display(self):
        """Обновляет отображение списков"""
        self.locations_list.clear()
        for loc in self.elements['locations']:
            self.locations_list.addItem(loc['name'])
        
        self.characters_list.clear()
        for char in self.elements['characters']:
            self.characters_list.addItem(char['name'])
        
        self.monsters_list.clear()
        for monster in self.elements['monsters']:
            self.monsters_list.addItem(monster['name'])
        
        self.items_list.clear()
        for item in self.elements['items']:
            self.items_list.addItem(item['name'])
    
    def on_element_clicked(self, item, element_type):
        """Обработка клика по элементу"""
        element_name = item.text()
        elements_list = self.elements.get(f'{element_type}s', [])
        element = next((e for e in elements_list if e['name'] == element_name), None)
        
        if element:
            self.element_selected.emit({
                'type': element_type,
                'name': element_name,
                'context': element.get('context', '')
            })