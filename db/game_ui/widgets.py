# db/game_ui/widgets.py
import requests
from db.gui.config_client import API_URL
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QFrame, QListWidget, QTextEdit, 
                             QMessageBox, QDialog, QLineEdit, QComboBox, 
                             QSpinBox, QScrollArea, QTabWidget, QSplitter, 
                             QListWidget, QGroupBox)

from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, List, Optional

class PlayerStatWidget(QFrame):
    """Виджет отображения одного игрока для ГМ"""

    inspect_stats = pyqtSignal(int, str)  # character_id, character_name
    inspect_inventory = pyqtSignal(int)  # character_id
    hp_changed = pyqtSignal(int, int)  # character_id, new_hp
    mp_changed = pyqtSignal(int, int)  # character_id, new_mp
    open_inventory = pyqtSignal(int)   # character_id
    
    def __init__(self, player_data: Dict, parent=None):
        super().__init__(parent)
        self.player_data = player_data
        self.character = player_data.get('character', {})
        self.character_id = self.character.get('id')
        self.initUI()
        self.apply_styles()
    
    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Имя персонажа и игрока
        name_label = QLabel(f"{self.character.get('name', 'Unknown')}")
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e67e22;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)
        
        player_label = QLabel(f"Игрок: {self.player_data.get('username', '?')}")
        player_label.setStyleSheet("font-size: 11px; color: #bdc3c7;")
        player_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(player_label)
        
        # HP и MP
        stats_layout = QGridLayout()
        
        self.hp_label = QLabel(f"❤️ HP: {self.character.get('current_hp', 0)}/{self.character.get('max_hp', 0)}")
        self.hp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
        stats_layout.addWidget(self.hp_label, 0, 0)
        
        self.mp_label = QLabel(f"💙 MP: {self.character.get('current_mp', 0)}/{self.character.get('max_mp', 0)}")
        self.mp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db;")
        stats_layout.addWidget(self.mp_label, 0, 1)
        
        # Кнопки изменения HP/MP
        hp_adj_layout = QHBoxLayout()
        hp_minus = QPushButton("-")
        hp_minus.setFixedSize(30, 30)
        hp_minus.clicked.connect(lambda: self.adjust_hp(-1))
        hp_plus = QPushButton("+")
        hp_plus.setFixedSize(30, 30)
        hp_plus.clicked.connect(lambda: self.adjust_hp(1))
        hp_adj_layout.addWidget(hp_minus)
        hp_adj_layout.addWidget(QLabel("HP"))
        hp_adj_layout.addWidget(hp_plus)
        stats_layout.addLayout(hp_adj_layout, 1, 0)
        
        mp_adj_layout = QHBoxLayout()
        mp_minus = QPushButton("-")
        mp_minus.setFixedSize(30, 30)
        mp_minus.clicked.connect(lambda: self.adjust_mp(-1))
        mp_plus = QPushButton("+")
        mp_plus.setFixedSize(30, 30)
        mp_plus.clicked.connect(lambda: self.adjust_mp(1))
        mp_adj_layout.addWidget(mp_minus)
        mp_adj_layout.addWidget(QLabel("MP"))
        mp_adj_layout.addWidget(mp_plus)
        stats_layout.addLayout(mp_adj_layout, 1, 1)
        
        layout.addLayout(stats_layout)
        
        # Экипированные предметы
        equip_label = QLabel("⚔️ Экипировано:")
        equip_label.setStyleSheet("font-size: 12px; color: #f39c12; margin-top: 5px;")
        layout.addWidget(equip_label)
        
        self.equipment_list = QLabel(self.get_equipment_text())
        self.equipment_list.setStyleSheet("font-size: 10px; color: #ecf0f1;")
        self.equipment_list.setWordWrap(True)
        layout.addWidget(self.equipment_list)
        
        # Кнопка инвентаря
        inventory_btn = QPushButton("📦 Лут")
        inspect_btn = QPushButton("🔍 Смотреть инвентарь")
        inspect_btn.setStyleSheet("background-color: #3498db; margin-top: 5px;")
        inspect_btn.clicked.connect(lambda: self.inspect_inventory.emit(self.character_id))
        layout.addWidget(inspect_btn)
    
        stats_btn = QPushButton("📊 Смотреть статы")
        stats_btn.setStyleSheet("background-color: #9b59b6; margin-top: 5px;")
        stats_btn.clicked.connect(lambda: self.inspect_stats.emit(self.character_id, self.character.get('name', 'Unknown')))
        layout.addWidget(stats_btn)

        self.setLayout(layout)
    
    def get_equipment_text(self) -> str:
        """Получить текст с экипированными предметами"""
        equipped = self.character.get('equipped_items', [])
        if not equipped:
            return "Нет экипированных предметов"
        return "\n".join([f"• {item.get('name', '?')}" for item in equipped[:3]])
    
    def adjust_hp(self, delta: int):
        current = self.character.get('current_hp', 0)
        max_hp = self.character.get('max_hp', 100)
        new_hp = max(0, min(max_hp, current + delta))
        self.hp_changed.emit(self.character_id, new_hp)
    
    def adjust_mp(self, delta: int):
        current = self.character.get('current_mp', 0)
        max_mp = self.character.get('max_mp', 100)
        new_mp = max(0, min(max_mp, current + delta))
        self.mp_changed.emit(self.character_id, new_mp)
    
    def update_stats(self, character_data: Dict):
        """Обновить отображаемые характеристики"""
        self.character = character_data
        self.hp_label.setText(f"❤️ HP: {character_data.get('current_hp', 0)}/{character_data.get('max_hp', 0)}")
        self.mp_label.setText(f"💙 MP: {character_data.get('current_mp', 0)}/{character_data.get('max_mp', 0)}")
        self.equipment_list.setText(self.get_equipment_text())
    
    def apply_styles(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)


class InventoryDialog(QDialog):
    """Диалог просмотра полного инвентаря"""
    
    def __init__(self, character_id: int, character_name: str, 
                 items: List[Dict], game_api, parent=None):
        super().__init__(parent)
        self.character_id = character_id
        self.character_name = character_name
        self.items = items
        self.game_api = game_api
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(f"Инвентарь - {self.character_name}")
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
            }
            QListWidget {
                background-color: #34495e;
                color: #ecf0f1;
                border: none;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Разделяем на экипированные и неэкипированные
        equipped = [i for i in self.items if i.get('is_equipped', False)]
        not_equipped = [i for i in self.items if not i.get('is_equipped', False)]
        
        if equipped:
            equip_label = QLabel("⚔️ ЭКИПИРОВАНО:")
            equip_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12; margin-top: 10px;")
            layout.addWidget(equip_label)
            
            for item in equipped:
                item_widget = self.create_item_widget(item, True)
                layout.addWidget(item_widget)
        
        if not_equipped:
            inv_label = QLabel("📦 В ИНВЕНТАРЕ:")
            inv_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db; margin-top: 10px;")
            layout.addWidget(inv_label)
            
            for item in not_equipped:
                item_widget = self.create_item_widget(item, False)
                layout.addWidget(item_widget)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)
        
        self.setLayout(main_layout)
    
    def create_item_widget(self, item: Dict, is_equipped: bool) -> QWidget:
        widget = QFrame()
        layout = QHBoxLayout()
        
        name_label = QLabel(f"📦 {item.get('name', '?')}")
        name_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(name_label)
        
        if item.get('effects'):
            effects_text = ", ".join([f"{k}+{v}" for k, v in item['effects'].items() if v != 0])
            effects_label = QLabel(f"({effects_text})")
            effects_label.setStyleSheet("font-size: 10px; color: #2ecc71;")
            layout.addWidget(effects_label)
        
        layout.addStretch()
        
        if self.game_api.is_admin:
            if is_equipped:
                unequip_btn = QPushButton("Снять")
                unequip_btn.clicked.connect(lambda: self.unequip_item(item['id']))
                layout.addWidget(unequip_btn)
            else:
                equip_btn = QPushButton("Экипировать")
                equip_btn.clicked.connect(lambda: self.equip_item(item['id']))
                layout.addWidget(equip_btn)
        
        widget.setLayout(layout)
        return widget
    
    def equip_item(self, item_id: int):
        if self.game_api.equip_item(self.character_id, item_id):
            QMessageBox.information(self, "Успех", "Предмет экипирован!")
            self.accept()
    
    def unequip_item(self, item_id: int):
        if self.game_api.unequip_item(self.character_id, item_id):
            QMessageBox.information(self, "Успех", "Предмет снят!")
            self.accept()


class ActionButton(QPushButton):
    """Кнопка действия с контекстом"""
    
    def __init__(self, action_name: str, description: str, action_id: int, parent=None):
        super().__init__(action_name, parent)
        self.action_name = action_name
        self.description = description
        self.action_id = action_id
        self.setToolTip(description)
        self.setMinimumHeight(40)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                text-align: left;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)


class GlobalEventsWidget(QWidget):
    """Виджет глобальных событий"""
    
    def __init__(self, session_id: int, game_api, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.game_api = game_api
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        title = QLabel("🌍 ГЛОБАЛЬНЫЕ СОБЫТИЯ")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")
        layout.addWidget(title)
        
        self.events_list = QListWidget()
        self.events_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.events_list)
        
        if self.game_api.is_admin:
            input_layout = QHBoxLayout()
            self.event_input = QLineEdit()
            self.event_input.setPlaceholderText("Введите событие...")
            input_layout.addWidget(self.event_input)
            
            send_btn = QPushButton("Отправить")
            send_btn.clicked.connect(self.add_event)
            input_layout.addWidget(send_btn)
            
            layout.addLayout(input_layout)
        
        self.setLayout(layout)
    
    def add_event(self):
        message = self.event_input.text().strip()
        if message:
            if self.game_api.add_global_event(self.session_id, message):
                self.event_input.clear()
                self.load_events()
    
    def load_events(self):
        self.events_list.clear()
        events = self.game_api.get_global_events(self.session_id)
        for event in events:
            self.events_list.addItem(f"[{event.get('time', '?')}] {event.get('message', '')}")
    
    def refresh(self):
        self.load_events()


class CharacterStatsWidget(QWidget):
    """Виджет характеристик персонажа для игрока"""
    
    def __init__(self, character_data: Dict, parent=None):
        super().__init__(parent)
        self.character = character_data
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Имя и уровень
        name_label = QLabel(self.character.get('name', 'Unknown'))
        name_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #e67e22;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)
        
        level_label = QLabel(f"Уровень: {self.character.get('level', 1)}")
        level_label.setStyleSheet("font-size: 14px; color: #bdc3c7;")
        level_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(level_label)
        
        # HP/MP
        stats_layout = QGridLayout()
        
        hp_label = QLabel(f"❤️ Здоровье: {self.character.get('current_hp', 0)}/{self.character.get('max_hp', 0)}")
        hp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        stats_layout.addWidget(hp_label, 0, 0)
        
        mp_label = QLabel(f"💙 Мана: {self.character.get('current_mp', 0)}/{self.character.get('max_mp', 0)}")
        mp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        stats_layout.addWidget(mp_label, 0, 1)
        
        layout.addLayout(stats_layout)
        
        # Характеристики
        attrs_layout = QGridLayout()
        attrs_layout.setSpacing(10)
        
        attrs = ['strength', 'dexterity', 'intelligence', 'charisma']
        attr_names = ['💪 Сила', '🏃 Ловкость', '🧠 Интеллект', '💬 Харизма']
        
        for i, (attr, name) in enumerate(zip(attrs, attr_names)):
            value = self.character.get('stats', {}).get(attr, 10)
            label = QLabel(f"{name}: {value}")
            label.setStyleSheet("font-size: 14px;")
            attrs_layout.addWidget(label, i // 2, i % 2)
        
        layout.addLayout(attrs_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #34495e;
                border-radius: 10px;
                padding: 15px;
            }
        """)
class PlayerInventoryWidget(QWidget):
    """Виджет инвентаря для игрока"""
    
    def __init__(self, character_id: int, game_api, parent=None):
        super().__init__(parent)
        self.character_id = character_id
        self.game_api = game_api
        self.inventory = []
        self.equipped = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Экипировка
        equipped_label = QLabel("⚔️ ЭКИПИРОВАНО:")
        equipped_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")
        layout.addWidget(equipped_label)
        
        self.equipped_list = QListWidget()
        self.equipped_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #f39c12;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
        """)
        layout.addWidget(self.equipped_list)
        
        # Инвентарь
        inventory_label = QLabel("📦 ИНВЕНТАРЬ:")
        inventory_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db; margin-top: 10px;")
        layout.addWidget(inventory_label)
        
        self.inventory_list = QListWidget()
        self.inventory_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #3498db;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
        """)
        self.inventory_list.itemDoubleClicked.connect(self.on_item_double_click)
        layout.addWidget(self.inventory_list)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Загружает данные инвентаря"""
        try:
            response = requests.get(f"{API_URL}/game/character/{self.character_id}/full_data")
            if response.status_code == 200:
                data = response.json()
                self.equipped = data.get('equipped', [])
                self.inventory = data.get('inventory', [])
                self.update_display()
        except Exception as e:
            print(f"Error loading inventory: {e}")
    
    def update_display(self):
        """Обновляет отображение"""
        self.equipped_list.clear()
        for item in self.equipped:
            effects_text = self.get_effects_text(item.get('effects', {}))
            self.equipped_list.addItem(f"{item.get('icon', '📦')} {item.get('name', '?')}{effects_text}")
        
        self.inventory_list.clear()
        for item in self.inventory:
            effects_text = self.get_effects_text(item.get('effects', {}))
            quantity_text = f" x{item.get('quantity', 1)}" if item.get('quantity', 1) > 1 else ""
            self.inventory_list.addItem(f"{item.get('icon', '📦')} {item.get('name', '?')}{effects_text}{quantity_text}")
    
    def get_effects_text(self, effects):
        """Форматирует текст эффектов"""
        if not effects:
            return ""
        effects_list = []
        for stat, value in effects.items():
            if value != 0 and stat not in ['heal_hp', 'heal_mp']:
                sign = "+" if value > 0 else ""
                effects_list.append(f"{stat}: {sign}{value}")
        if effects_list:
            return f" ({', '.join(effects_list)})"
        return ""
    
    def on_item_double_click(self, item):
        """Обработка двойного клика по предмету"""
        # Показываем информацию о предмете
        item_text = item.text()
        for inv_item in self.inventory:
            if inv_item.get('name') in item_text:
                QMessageBox.information(self, "Информация о предмете",
                    f"Название: {inv_item.get('name')}\n"
                    f"Тип: {inv_item.get('slot', 'обычный')}\n"
                    f"Описание: {inv_item.get('description', 'Нет описания')}\n"
                    f"Эффекты: {self.get_effects_text(inv_item.get('effects', {}))}"
                )
                break
    
    def refresh(self):
        """Обновляет данные"""
        self.load_data()

class ExtractedElementsWidget(QWidget):
    """Виджет для отображения выделенных элементов из сюжета"""
    
    element_selected = pyqtSignal(dict)  # сигнал при выборе элемента
    
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
        # Получаем все story_ действия из логов
        story_actions = self.logger.get_story_actions()
        
        # Очищаем списки
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
        
        # Обновляем отображение
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
        
        # Находим элемент
        elements_list = self.elements.get(f'{element_type}s', [])
        element = next((e for e in elements_list if e['name'] == element_name), None)
        
        if element:
            self.element_selected.emit({
                'type': element_type,
                'name': element_name,
                'context': element.get('context', '')
            })