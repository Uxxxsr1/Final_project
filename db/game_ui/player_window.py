# db/game_ui/player_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QPushButton, QScrollArea, QFrame,
                             QSplitter, QMessageBox, QTextEdit, QListWidget,
                             QToolButton, QMenu, QAction, QInputDialog, QLineEdit,
                             QTabWidget, QDialog, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from typing import Dict, List, Optional

from db.game_ui.widgets import CharacterStatsWidget, ActionButton, InventoryDialog
from db.game_ui.api import GameAPI
from db.gui.logger_client import LoggerClient


class PlayerGameWindow(QMainWindow):
    """Основное окно Игрока для участия в сессии"""
    
    def __init__(self, user_data: Dict, session_data: Dict, 
                 character_data: Dict, logger: LoggerClient):
        super().__init__()
        self.user_data = user_data
        self.session_data = session_data
        self.character_data = character_data
        self.logger = logger
        self.session_id = session_data.get('id')
        self.character_id = character_data.get('id')
        
        self.game_api = GameAPI(user_data['id'], is_admin=user_data.get('is_admin', False))
        self.current_context = ""  # Текущий контекст для действий
        
        self.initUI()
        self.load_data()
        self.start_auto_refresh()
        
        # Логируем открытие окна игрока
        self.logger.log_action('open_player_window', 
                               session_id=self.session_id,
                               character_id=self.character_id)
    
    def initUI(self):
        self.setWindowTitle(f"ДПЖ - Игрок | {self.character_data.get('name', 'Unknown')}")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet(self.get_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Верхняя панель
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Основной контент
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Левая часть - персонаж и инвентарь
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Правая часть - действия и события
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([400, 800])
        main_layout.addWidget(content_splitter)
        
        central_widget.setLayout(main_layout)
    
    def create_top_bar(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        session_label = QLabel(f"📌 Сессия: {self.session_data.get('name', '?')}")
        session_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e67e22;")
        layout.addWidget(session_label)
        
        character_label = QLabel(f"🎭 Персонаж: {self.character_data.get('name', '?')}")
        character_label.setStyleSheet("font-size: 14px; color: #3498db;")
        level_label = QLabel(f"⭐ Уровень: {self.character_data.get('level', 1)}")
        level_label.setStyleSheet("font-size: 14px; color: #f39c12;")
        layout.addWidget(level_label)

        # Добавьте разделитель
        separator = QLabel("|")
        separator.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(separator)

        # Добавьте HP и MP
        hp_label = QLabel(f"❤️ {self.character_data.get('current_hp', 0)}/{self.character_data.get('max_hp', 0)}")
        hp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(hp_label)

        mp_label = QLabel(f"💙 {self.character_data.get('current_mp', 0)}/{self.character_data.get('max_mp', 0)}")
        mp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db;")
        layout.addWidget(mp_label)
        layout.addWidget(character_label)
        
        layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)

        # Кнопка выхода из игры
        exit_game_btn = QPushButton("🚪 Выйти из игры")
        exit_game_btn.clicked.connect(self.exit_session)
        exit_game_btn.setStyleSheet("background-color: #e74c3c;")
        layout.addWidget(exit_game_btn)

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
                border-bottom: 2px solid #3498db;
            }
            QPushButton {
                background-color: #27ae60;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        return widget
    
    def create_left_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Характеристики персонажа (увеличьте размер)
        self.stats_widget = CharacterStatsWidget(self.character_data)
        self.stats_widget.setMinimumHeight(250)
        layout.addWidget(self.stats_widget)
        
        # Группа опыта
        exp_group = QGroupBox("🎯 Прогресс")
        exp_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        exp_layout = QVBoxLayout()
        
        exp_label = QLabel(f"Опыт: {self.character_data.get('experience', 0)} / {self.character_data.get('next_level_exp', 100)}")
        exp_layout.addWidget(exp_label)
        
        exp_bar = QProgressBar()
        exp_bar.setRange(0, self.character_data.get('next_level_exp', 100))
        exp_bar.setValue(self.character_data.get('experience', 0))
        exp_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #34495e;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #f39c12;
                border-radius: 3px;
            }
        """)
        exp_layout.addWidget(exp_bar)
        
        exp_group.setLayout(exp_layout)
        layout.addWidget(exp_group)
        
        # Инвентарь (увеличьте)
        self.inventory_widget = PlayerInventoryWidget(self.character_id, self.game_api)
        self.inventory_widget.setMinimumHeight(300)
        layout.addWidget(self.inventory_widget)
        
        # Кнопки управления инвентарем
        btn_layout = QHBoxLayout()
        
        refresh_inv_btn = QPushButton("🔄 Обновить")
        refresh_inv_btn.clicked.connect(self.refresh_inventory)
        btn_layout.addWidget(refresh_inv_btn)
        
        use_item_btn = QPushButton("🎒 Использовать предмет")
        use_item_btn.clicked.connect(self.use_item)
        btn_layout.addWidget(use_item_btn)
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        return widget
    def refresh_inventory(self):
        """Обновляет инвентарь"""
        if hasattr(self, 'inventory_widget'):
            self.inventory_widget.refresh()
    
    def use_item(self):
        """Использовать предмет из инвентаря"""
        # Получаем выбранный предмет из списка инвентаря
        if hasattr(self, 'inventory_widget'):
            current_item = self.inventory_widget.inventory_list.currentItem()
            if current_item:
                item_name = current_item.text()
                # Здесь логика использования предмета
                QMessageBox.information(self, "Использование предмета", f"Вы использовали: {item_name}")
            else:
                QMessageBox.warning(self, "Ошибка", "Выберите предмет из инвентаря")

    def filter_logs(self, filter_type):
        """Фильтрует логи по типу"""
        # Обновляем стили кнопок
        for btn in [self.filter_all, self.filter_actions, self.filter_system]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    padding: 5px 10px;
                }
                QPushButton:checked {
                    background-color: #3498db;
                }
            """)
        
        # Здесь логика фильтрации логов
        self.load_logs()

    def exit_session(self):
        """Выход из сессии и освобождение персонажа"""
        reply = QMessageBox.question(self, "Выход",
                                    "Вы уверены, что хотите выйти из сессии?\n"
                                    "Персонаж снова станет доступен для выбора.",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Освобождаем персонажа
            try:
                requests.put(f"{API_URL}/characters/{self.character_id}/detach_session")
            except:
                pass
            
            self.logger.log_action('player_exit_session',
                                session_id=self.session_id,
                                character_id=self.character_id)
            self.close()


    def create_right_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Создаем вкладки
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #2c3e50;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
            }
        """)
        
        # Вкладка действий
        actions_tab = self.create_actions_tab()
        tabs.addTab(actions_tab, "🎮 Действия")
        
        # Вкладка событий
        events_tab = self.create_events_tab()
        tabs.addTab(events_tab, "🌍 События")
        
        # Вкладка логов
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "📜 Логи")
        
        layout.addWidget(tabs)
        widget.setLayout(layout)
        
        return widget

    def create_actions_tab(self) -> QWidget:
        """Создает вкладку с действиями"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Контекст
        context_group = QGroupBox("📍 Текущая локация")
        context_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #e67e22;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        context_layout = QVBoxLayout()
        
        self.context_text = QLabel("Городская площадь")
        self.context_text.setStyleSheet("font-size: 16px; color: #f39c12; padding: 10px;")
        self.context_text.setWordWrap(True)
        context_layout.addWidget(self.context_text)
        
        context_group.setLayout(context_layout)
        layout.addWidget(context_group)
        
        # Доступные действия
        actions_group = QGroupBox("⚡ Доступные действия")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #2ecc71;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        self.actions_container = QWidget()
        self.actions_layout = QVBoxLayout()
        self.actions_layout.setSpacing(8)
        self.actions_container.setLayout(self.actions_layout)
        
        actions_scroll = QScrollArea()
        actions_scroll.setWidget(self.actions_container)
        actions_scroll.setWidgetResizable(True)
        actions_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        actions_group_layout = QVBoxLayout()
        actions_group_layout.addWidget(actions_scroll)
        actions_group.setLayout(actions_group_layout)
        
        layout.addWidget(actions_group)
        
        tab.setLayout(layout)
        return tab

    def create_events_tab(self) -> QWidget:
        """Создает вкладку с событиями"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Глобальные события
        events_group = QGroupBox("🌍 Глобальные события")
        events_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        events_layout = QVBoxLayout()
        
        self.events_list = QListWidget()
        self.events_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
            }
        """)
        events_layout.addWidget(self.events_list)
        
        events_group.setLayout(events_layout)
        layout.addWidget(events_group)
        
        # Игровые новости
        news_group = QGroupBox("📰 Новости")
        news_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        news_layout = QVBoxLayout()
        
        self.news_list = QListWidget()
        self.news_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                color: #3498db;
                border: 1px solid #34495e;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        news_layout.addWidget(self.news_list)
        
        news_group.setLayout(news_layout)
        layout.addWidget(news_group)
        
        tab.setLayout(layout)
        return tab

    def create_logs_tab(self) -> QWidget:
        """Создает вкладку с логами"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Фильтры логов
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр:"))
        
        self.filter_all = QPushButton("Все")
        self.filter_all.setCheckable(True)
        self.filter_all.setChecked(True)
        self.filter_all.clicked.connect(lambda: self.filter_logs('all'))
        
        self.filter_actions = QPushButton("Действия")
        self.filter_actions.setCheckable(True)
        self.filter_actions.clicked.connect(lambda: self.filter_logs('actions'))
        
        self.filter_system = QPushButton("Система")
        self.filter_system.setCheckable(True)
        self.filter_system.clicked.connect(lambda: self.filter_logs('system'))
        
        filter_layout.addWidget(self.filter_all)
        filter_layout.addWidget(self.filter_actions)
        filter_layout.addWidget(self.filter_system)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Текстовое поле для логов
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #ecf0f1;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.logs_text)
        
        # Статистика
        stats_label = QLabel("📊 Статистика действий")
        stats_label.setStyleSheet("font-size: 12px; color: #2ecc71; margin-top: 5px;")
        layout.addWidget(stats_label)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(100)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #bdc3c7;
                font-size: 11px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.stats_text)
        
        tab.setLayout(layout)
        return tab
    
    def load_data(self):
        """Загружает все данные персонажа"""
        updated_char = self.game_api.get_player_character(self.user_data['id'], self.session_id)
        if updated_char:
            self.character_data = updated_char
            self.stats_widget.character = updated_char
            self.stats_widget.initUI()
        
        # Обновляем инвентарь
        if hasattr(self, 'inventory_widget'):
            self.inventory_widget.refresh()
        
        # Загружаем действия
        self.load_actions()
        
        # Загружаем события
        self.load_events()
        
        # Загружаем логи
        self.load_logs()
        
        # Загружаем статистику
        self.load_stats()
        
        # Обновляем верхнюю панель
        self.update_top_bar()

    def update_top_bar(self):
        """Обновляет информацию в верхней панели"""
        # Находим и обновляем виджеты в top_bar
        for child in self.centralWidget().children():
            if isinstance(child, QWidget):
                for subchild in child.children():
                    if isinstance(subchild, QLabel):
                        text = subchild.text()
                        if '❤️' in text:
                            subchild.setText(f"❤️ {self.character_data.get('current_hp', 0)}/{self.character_data.get('max_hp', 0)}")
                        elif '💙' in text:
                            subchild.setText(f"💙 {self.character_data.get('current_mp', 0)}/{self.character_data.get('max_mp', 0)}")
                        elif '⭐' in text:
                            subchild.setText(f"⭐ Уровень: {self.character_data.get('level', 1)}")

    def load_stats(self):
        """Загружает статистику действий"""
        if hasattr(self, 'stats_text'):
            stats = self.logger.get_my_stats()
            stats_text = f"""
            📊 ВАША СТАТИСТИКА:
            • Всего действий: {stats.get('total_actions', 0)}
            • Совершено действий: {stats.get('actions_performed', 0)}
            • Получено действий: {stats.get('actions_received', 0)}
            
            📋 ПО ТИПАМ:
            """
            for action, count in stats.get('by_action_type', {}).items():
                stats_text += f"\n  • {action}: {count}"
            
            self.stats_text.setText(stats_text)
    
    def load_actions(self):
        """Загружает доступные действия"""
        # Очищаем старые действия
        for i in reversed(range(self.actions_layout.count())):
            self.actions_layout.itemAt(i).widget().deleteLater()
        
        actions = self.game_api.get_available_actions(self.character_id, self.current_context)
        
        for action in actions:
            btn = ActionButton(
                action.get('display_name', action.get('action_name', '?')),
                action.get('description', ''),
                action.get('id', 0)
            )
            btn.clicked.connect(lambda checked, a=action: self.perform_action(a))
            self.actions_layout.addWidget(btn)
        
        if not actions:
            no_actions = QLabel("Нет доступных действий")
            no_actions.setStyleSheet("color: #7f8c8d; padding: 10px;")
            no_actions.setAlignment(Qt.AlignCenter)
            self.actions_layout.addWidget(no_actions)
    
    def load_events(self):
        """Загружает глобальные события"""
        events = self.game_api.get_global_events(self.session_id)
        self.events_list.clear()
        
        for event in events[-10:]:  # Последние 10 событий
            time = event.get('time', '?')[:16] if event.get('time') else '?'
            self.events_list.addItem(f"[{time}] {event.get('message', '')}")
    
    def load_logs(self):
        """Загружает логи персонажа"""
        logs = self.game_api.get_character_logs(self.character_id, limit=30)
        self.logs_text.clear()
        
        for log in logs:
            time = log.get('timestamp', '?')[:16] if log.get('timestamp') else '?'
            action = log.get('action_name', '?')
            details = log.get('details', {})
            
            log_line = f"[{time}] {action}"
            if details:
                log_line += f" - {details}"
            
            self.logs_text.append(log_line)
    
    def perform_action(self, action: Dict):
        """Выполняет выбранное действие"""
        action_name = action.get('action_name')
        
        # Спрашиваем подтверждение
        reply = QMessageBox.question(self, "Подтверждение",
                                    f"Выполнить действие: {action.get('display_name', action_name)}?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.game_api.perform_action(self.character_id, action_name):
                QMessageBox.information(self, "Успех", f"Действие '{action.get('display_name', action_name)}' выполнено!")
                self.logger.log_action('player_action',
                                       character_id=self.character_id,
                                       session_id=self.session_id,
                                       details={'action': action_name})
                self.load_data()  # Обновляем все данные
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось выполнить действие")
    
    def open_full_inventory(self):
        """Открывает полный инвентарь"""
        items = self.game_api.get_character_inventory(self.character_id)
        dialog = InventoryDialog(
            self.character_id,
            self.character_data.get('name', 'Unknown'),
            items,
            self.game_api,
            self
        )
        dialog.exec_()
        self.load_data()  # Обновляем после закрытия
    
    def start_auto_refresh(self):
        """Автоматическое обновление каждые 5 секунд"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(5000)
    
    def auto_refresh(self):
        """Автоматическое обновление"""
        self.load_events()
        self.load_logs()
        # Обновляем характеристики только если они изменились
        updated_char = self.game_api.get_player_character(self.user_data['id'], self.session_id)
        if updated_char and updated_char.get('current_hp') != self.character_data.get('current_hp'):
            self.load_data()
    
    def exit_session(self):
        """Выход из сессии"""
        reply = QMessageBox.question(self, "Выход",
                                    "Вы уверены, что хотите выйти из сессии?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logger.log_action('player_exit_session',
                                   session_id=self.session_id,
                                   character_id=self.character_id)
            self.close()
    
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
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
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
                background-color: #27ae60;
            }
            QListWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
        """
    
    def closeEvent(self, event):
        self.refresh_timer.stop()
        self.logger.log_action('player_close_window',
                               session_id=self.session_id,
                               character_id=self.character_id)
        event.accept()

    def select_character_dialog(self):
        """Диалог выбора персонажа"""
        try:
            response = requests.get(f"{API_URL}/characters/my/{self.user_data['id']}")
            if response.status_code == 200:
                characters = response.json()
                if not characters:
                    QMessageBox.warning(self, "Ошибка", "У вас нет персонажей. Создайте персонажа в главном меню.")
                    return
                
                from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
                
                dialog = QDialog(self)
                dialog.setWindowTitle("Выбор персонажа")
                dialog.setMinimumSize(400, 500)
                dialog.setStyleSheet("background-color: #2c3e50;")
                
                layout = QVBoxLayout()
                
                label = QLabel("Выберите персонажа:")
                label.setStyleSheet("color: #ecf0f1; font-size: 14px; padding: 10px;")
                layout.addWidget(label)
                
                characters_list = QListWidget()
                for char in characters:
                    characters_list.addItem(f"{char['name']} (ID: {char['id']})")
                layout.addWidget(characters_list)
                
                btn_layout = QHBoxLayout()
                select_btn = QPushButton("✅ Выбрать")
                select_btn.setStyleSheet("background-color: #27ae60;")
                cancel_btn = QPushButton("❌ Отмена")
                cancel_btn.setStyleSheet("background-color: #95a5a6;")
                
                btn_layout.addWidget(select_btn)
                btn_layout.addWidget(cancel_btn)
                layout.addLayout(btn_layout)
                
                dialog.setLayout(layout)
                
                def on_select():
                    current = characters_list.currentItem()
                    if current:
                        char_text = current.text()
                        char_name = char_text.split(" (ID:")[0]
                        char_id = int(char_text.split("ID: ")[-1].rstrip(")"))
                        
                        # Обновляем данные персонажа
                        for char in characters:
                            if char['id'] == char_id:
                                self.character_data = char
                                self.character_id = char_id
                                self.character_label.setText(f"🎭 Персонаж: {char_name}")
                                
                                # Обновляем виджеты
                                self.stats_widget.character = char
                                self.stats_widget.initUI()
                                if hasattr(self, 'inventory_widget'):
                                    self.inventory_widget.character_id = char_id
                                    self.inventory_widget.refresh()
                                
                                self.logger.log_action('select_character', 
                                                    character_id=char_id,
                                                    details={'character_name': char_name})
                                
                                QMessageBox.information(dialog, "Успех", f"Выбран персонаж: {char_name}")
                                dialog.accept()
                                break
                    else:
                        QMessageBox.warning(dialog, "Ошибка", "Выберите персонажа")
                
                select_btn.clicked.connect(on_select)
                cancel_btn.clicked.connect(dialog.reject)
                
                dialog.exec_()
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")

    def show_character_stats_dialog(self):
        """Показывает диалог с полными характеристиками персонажа"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Характеристики - {self.character_data.get('name', 'Unknown')}")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet("background-color: #2c3e50;")
        
        layout = QVBoxLayout()
        
        # Основная информация
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #34495e; border-radius: 10px; padding: 15px;")
        info_layout = QVBoxLayout()
        
        name_label = QLabel(f"🎭 {self.character_data.get('name', 'Unknown')}")
        name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #e67e22;")
        name_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(name_label)
        
        level_label = QLabel(f"Уровень: {self.character_data.get('level', 1)}")
        level_label.setStyleSheet("font-size: 14px;")
        level_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(level_label)
        
        # HP/MP
        hp_mp_layout = QHBoxLayout()
        hp_label = QLabel(f"❤️ HP: {self.character_data.get('current_hp', 0)}/{self.character_data.get('max_hp', 0)}")
        hp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        mp_label = QLabel(f"💙 MP: {self.character_data.get('current_mp', 0)}/{self.character_data.get('max_mp', 0)}")
        mp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        hp_mp_layout.addWidget(hp_label)
        hp_mp_layout.addWidget(mp_label)
        info_layout.addLayout(hp_mp_layout)
        
        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        
        # Характеристики
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #34495e; border-radius: 10px; padding: 15px; margin-top: 10px;")
        stats_layout = QGridLayout()
        
        stats = self.character_data.get('stats', {})
        base_stats = self.character_data.get('base_stats', {})
        
        stats_data = [
            ('💪 Сила', stats.get('strength', 10), base_stats.get('strength', 10)),
            ('🏃 Ловкость', stats.get('dexterity', 10), base_stats.get('dexterity', 10)),
            ('🧠 Интеллект', stats.get('intelligence', 10), base_stats.get('intelligence', 10)),
            ('💬 Харизма', stats.get('charisma', 10), base_stats.get('charisma', 10))
        ]
        
        for i, (name, current, base) in enumerate(stats_data):
            row = i // 2
            col = i % 2
            
            stat_widget = QFrame()
            stat_widget.setStyleSheet("background-color: #2c3e50; border-radius: 8px; padding: 10px;")
            stat_layout = QVBoxLayout()
            
            stat_name = QLabel(name)
            stat_name.setStyleSheet("font-size: 12px; color: #bdc3c7;")
            stat_layout.addWidget(stat_name)
            
            stat_value = QLabel(str(current))
            stat_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #f39c12;")
            stat_layout.addWidget(stat_value)
            
            if current != base:
                diff = current - base
                diff_text = f"(база: {base}, {diff:+d})"
                diff_label = QLabel(diff_text)
                diff_label.setStyleSheet("font-size: 10px; color: #2ecc71;" if diff > 0 else "font-size: 10px; color: #e74c3c;")
                stat_layout.addWidget(diff_label)
            
            stat_widget.setLayout(stat_layout)
            stats_layout.addWidget(stat_widget, row, col)
        
        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()