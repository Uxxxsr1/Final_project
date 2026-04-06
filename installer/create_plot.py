# create_plot.py
import os

def create_plot_files():
    """Создает все файлы сюжетной системы"""
    
    # Создаем папку Plot
    os.makedirs("db/Plot", exist_ok=True)
    
    # Файл: db/Plot/__init__.py
    with open("db/Plot/__init__.py", "w", encoding="utf-8") as f:
        f.write('''# db/Plot/__init__.py
from db.Plot.story_manager import StoryManager
from db.Plot.story_dialog import StoryDialog
from db.Plot.init_story_actions import init_story_actions

__all__ = [
    'StoryManager',
    'StoryDialog',
    'init_story_actions'
]
''')
    
    # Файл: db/Plot/story_manager.py
    with open("db/Plot/story_manager.py", "w", encoding="utf-8") as f:
        f.write('''# db/Plot/story_manager.py
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any

class StoryManager:
    """Менеджер для работы с сюжетом и выделением элементов"""
    
    def __init__(self, logger_client=None):
        self.logger = logger_client
        self.current_story = None
        self.extracted_items = {
            'locations': [],
            'characters': [],
            'monsters': [],
            'items': []
        }
    
    def parse_story_text(self, text: str) -> Dict[str, Any]:
        """Парсит текст и выделяет ключевые элементы"""
        
        # Словари ключевых слов для распознавания
        location_keywords = [
            'город', 'деревня', 'замок', 'пещера', 'лес', 'гора', 'долина', 
            'таверна', 'храм', 'башня', 'подземелье', 'дворец', 'площадь',
            'село', 'поселение', 'крепость', 'руины', 'болото', 'пустыня',
            'озеро', 'река', 'море', 'океан', 'остров', 'портал'
        ]
        
        character_keywords = [
            'король', 'королева', 'принц', 'принцесса', 'лорд', 'леди', 
            'рыцарь', 'маг', 'волшебник', 'жрец', 'купец', 'крестьянин',
            'воин', 'лучник', 'разбойник', 'вор', 'паладин', 'друид',
            'колдун', 'чародей', 'алхимик', 'инквизитор', 'стражник'
        ]
        
        monster_keywords = [
            'дракон', 'гоблин', 'орк', 'тролль', 'скелет', 'зомби', 'вампир',
            'оборотень', 'гигант', 'демон', 'призрак', 'гарпия', 'минотавр',
            'кобольд', 'огр', 'химера', 'грифон', 'пегас', 'единорог',
            'василиск', 'медуза', 'циклоп', 'элементаль', 'лих'
        ]
        
        item_keywords = [
            'меч', 'щит', 'кольцо', 'амулет', 'зелье', 'свиток', 'артефакт',
            'книга', 'ключ', 'сундук', 'сокровище', 'золото', 'оружие', 'броня',
            'шлем', 'перчатки', 'сапоги', 'плащ', 'посох', 'кинжал', 'лук',
            'арбалет', 'топор', 'молот', 'копье', 'алебарда'
        ]
        
        extracted = {
            'locations': [],
            'characters': [],
            'monsters': [],
            'items': []
        }
        
        # Разбиваем на предложения
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            sentence_lower = sentence.lower()
            
            # Поиск локаций
            for kw in location_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            location_name = ' '.join(words[start:end])
                            extracted['locations'].append({
                                'name': location_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw,
                                'type': 'location'
                            })
                            break
            
            # Поиск персонажей
            for kw in character_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            char_name = ' '.join(words[start:end])
                            extracted['characters'].append({
                                'name': char_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw,
                                'type': 'character'
                            })
                            break
            
            # Поиск монстров
            for kw in monster_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            monster_name = ' '.join(words[start:end])
                            extracted['monsters'].append({
                                'name': monster_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw,
                                'type': 'monster'
                            })
                            break
            
            # Поиск предметов
            for kw in item_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            item_name = ' '.join(words[start:end])
                            extracted['items'].append({
                                'name': item_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw,
                                'type': 'item'
                            })
                            break
        
        # Удаляем дубликаты
        for key in extracted:
            extracted[key] = self._remove_duplicates(extracted[key])
        
        return extracted
    
    def _remove_duplicates(self, items: List[Dict]) -> List[Dict]:
        """Удаляет дубликаты из списка"""
        seen = set()
        unique = []
        for item in items:
            name_key = item['name'].lower()
            if name_key not in seen:
                seen.add(name_key)
                unique.append(item)
        return unique
    
    def save_story_to_file(self, text: str, filename: str = None) -> str:
        """Сохраняет текст сюжета в файл"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"story_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("СЮЖЕТ\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(text)
            f.write("\n\n" + "=" * 60 + "\n")
            f.write("ВЫДЕЛЕННЫЕ ЭЛЕМЕНТЫ\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("ЛОКАЦИИ:\n")
            for loc in self.extracted_items['locations']:
                f.write(f"  • {loc['name']}\n")
                if loc.get('context'):
                    f.write(f"    Контекст: {loc['context'][:100]}...\n")
            f.write("\n")
            
            f.write("ПЕРСОНАЖИ:\n")
            for char in self.extracted_items['characters']:
                f.write(f"  • {char['name']}\n")
                if char.get('context'):
                    f.write(f"    Контекст: {char['context'][:100]}...\n")
            f.write("\n")
            
            f.write("МОНСТРЫ/ПРОТИВНИКИ:\n")
            for monster in self.extracted_items['monsters']:
                f.write(f"  • {monster['name']}\n")
                if monster.get('context'):
                    f.write(f"    Контекст: {monster['context'][:100]}...\n")
            f.write("\n")
            
            f.write("ПРЕДМЕТЫ:\n")
            for item in self.extracted_items['items']:
                f.write(f"  • {item['name']}\n")
                if item.get('context'):
                    f.write(f"    Контекст: {item['context'][:100]}...\n")
            f.write("\n")
            
            f.write("=" * 60 + "\n")
            f.write("Конец документа\n")
        
        return filename
    
    def process_and_log(self, text: str, gamemaster_id: int, session_id: int = None):
        """Обрабатывает текст и логирует выделенные элементы"""
        self.extracted_items = self.parse_story_text(text)
        
        if self.logger:
            # Логируем создание сюжета
            self.logger.log_action(
                'create_story',
                session_id=session_id,
                details={
                    'text_length': len(text),
                    'locations_count': len(self.extracted_items['locations']),
                    'characters_count': len(self.extracted_items['characters']),
                    'monsters_count': len(self.extracted_items['monsters']),
                    'items_count': len(self.extracted_items['items'])
                }
            )
            
            # Логируем локации
            for loc in self.extracted_items['locations']:
                self.logger.log_action(
                    'story_location',
                    session_id=session_id,
                    details={'location': loc['name'], 'context': loc['context'][:200]}
                )
            
            # Логируем персонажей
            for char in self.extracted_items['characters']:
                self.logger.log_action(
                    'story_character',
                    session_id=session_id,
                    details={'character': char['name'], 'context': char['context'][:200]}
                )
            
            # Логируем монстров
            for monster in self.extracted_items['monsters']:
                self.logger.log_action(
                    'story_monster',
                    session_id=session_id,
                    details={'monster': monster['name'], 'context': monster['context'][:200]}
                )
            
            # Логируем предметы
            for item in self.extracted_items['items']:
                self.logger.log_action(
                    'story_item',
                    session_id=session_id,
                    details={'item': item['name'], 'context': item['context'][:200]}
                )
        
        return self.extracted_items
    
    def get_statistics(self) -> Dict[str, int]:
        """Получить статистику выделенных элементов"""
        return {
            'total_locations': len(self.extracted_items['locations']),
            'total_characters': len(self.extracted_items['characters']),
            'total_monsters': len(self.extracted_items['monsters']),
            'total_items': len(self.extracted_items['items']),
            'total_elements': (len(self.extracted_items['locations']) + 
                              len(self.extracted_items['characters']) + 
                              len(self.extracted_items['monsters']) + 
                              len(self.extracted_items['items']))
        }
''')
    
    # Файл: db/Plot/story_dialog.py - полный код (продолжение в следующем сообщении)
    print("Создание файла story_dialog.py...")
    
    with open("db/Plot/story_dialog.py", "w", encoding="utf-8") as f:
        f.write('''# db/Plot/story_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QTabWidget, QWidget,
                             QListWidget, QMessageBox, QFileDialog, QSplitter,
                             QApplication)
from PyQt5.QtCore import Qt
from db.Plot.story_manager import StoryManager

class StoryDialog(QDialog):
    """Диалог для работы с сюжетом"""
    
    def __init__(self, logger_client, session_id=None, parent=None):
        super().__init__(parent)
        self.logger = logger_client
        self.session_id = session_id
        self.story_manager = StoryManager(logger_client)
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Редактор сюжета")
        self.setMinimumSize(1000, 750)
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 14px;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #ecf0f1;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
            QListWidget {
                background-color: #34495e;
                border: none;
                border-radius: 8px;
                padding: 8px;
                color: #ecf0f1;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #3b5998;
            }
            QListWidget::item:selected {
                background-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#save_btn {
                background-color: #27ae60;
            }
            QPushButton#save_btn:hover {
                background-color: #229954;
            }
            QPushButton#extract_btn {
                background-color: #e67e22;
            }
            QPushButton#extract_btn:hover {
                background-color: #d35400;
            }
            QPushButton#clear_btn {
                background-color: #e74c3c;
            }
            QPushButton#clear_btn:hover {
                background-color: #c0392b;
            }
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
        
        layout = QVBoxLayout()
        
        title = QLabel("Создание и редактирование сюжета")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        tabs = QTabWidget()
        
        # Вкладка редактирования
        edit_tab = QWidget()
        edit_layout = QVBoxLayout()
        
        self.story_text = QTextEdit()
        self.story_text.setPlaceholderText("""
Введите текст сюжета здесь...

Пример:
"В старом замке, на вершине горы, жил могущественный дракон. 
Рыцарь Артур отправился в опасное путешествие, чтобы победить чудовище 
и найти древний артефакт - Меч Судьбы."

Система автоматически выделит:
- Локации (замок, гора)
- Персонажей (рыцарь Артур)
- Монстров (дракон)
- Предметы (Меч Судьбы)
        """.strip())
        edit_layout.addWidget(self.story_text)
        
        btn_layout = QHBoxLayout()
        
        extract_btn = QPushButton("Выделить элементы")
        extract_btn.setObjectName("extract_btn")
        extract_btn.clicked.connect(self.extract_elements)
        btn_layout.addWidget(extract_btn)
        
        clear_btn = QPushButton("Очистить")
        clear_btn.setObjectName("clear_btn")
        clear_btn.clicked.connect(self.clear_text)
        btn_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("Сохранить сюжет")
        save_btn.setObjectName("save_btn")
        save_btn.clicked.connect(self.save_story)
        btn_layout.addWidget(save_btn)
        
        edit_layout.addLayout(btn_layout)
        edit_tab.setLayout(edit_layout)
        
        # Вкладка выделенных элементов
        elements_tab = QWidget()
        elements_layout = QVBoxLayout()
        
        stats_frame = QWidget()
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Статистика: ожидание...")
        self.stats_label.setStyleSheet("color: #f39c12; font-size: 12px;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        stats_frame.setLayout(stats_layout)
        elements_layout.addWidget(stats_frame)
        
        splitter = QSplitter(Qt.Horizontal)
        
        locations_widget = QWidget()
        locations_layout = QVBoxLayout()
        locations_label = QLabel("ЛОКАЦИИ")
        locations_label.setStyleSheet("color: #3498db;")
        locations_layout.addWidget(locations_label)
        self.locations_list = QListWidget()
        self.locations_list.itemClicked.connect(lambda item: self.show_context(item, 'location'))
        locations_layout.addWidget(self.locations_list)
        locations_widget.setLayout(locations_layout)
        
        characters_widget = QWidget()
        characters_layout = QVBoxLayout()
        characters_label = QLabel("ПЕРСОНАЖИ")
        characters_label.setStyleSheet("color: #2ecc71;")
        characters_layout.addWidget(characters_label)
        self.characters_list = QListWidget()
        self.characters_list.itemClicked.connect(lambda item: self.show_context(item, 'character'))
        characters_layout.addWidget(self.characters_list)
        characters_widget.setLayout(characters_layout)
        
        monsters_widget = QWidget()
        monsters_layout = QVBoxLayout()
        monsters_label = QLabel("МОНСТРЫ")
        monsters_label.setStyleSheet("color: #e74c3c;")
        monsters_layout.addWidget(monsters_label)
        self.monsters_list = QListWidget()
        self.monsters_list.itemClicked.connect(lambda item: self.show_context(item, 'monster'))
        monsters_layout.addWidget(self.monsters_list)
        monsters_widget.setLayout(monsters_layout)
        
        items_widget = QWidget()
        items_layout = QVBoxLayout()
        items_label = QLabel("ПРЕДМЕТЫ")
        items_label.setStyleSheet("color: #f1c40f;")
        items_layout.addWidget(items_label)
        self.items_list = QListWidget()
        self.items_list.itemClicked.connect(lambda item: self.show_context(item, 'item'))
        items_layout.addWidget(self.items_list)
        items_widget.setLayout(items_layout)
        
        splitter.addWidget(locations_widget)
        splitter.addWidget(characters_widget)
        splitter.addWidget(monsters_widget)
        splitter.addWidget(items_widget)
        elements_layout.addWidget(splitter)
        
        context_label = QLabel("Контекст:")
        context_label.setStyleSheet("margin-top: 10px;")
        elements_layout.addWidget(context_label)
        
        self.context_text = QTextEdit()
        self.context_text.setReadOnly(True)
        self.context_text.setMaximumHeight(100)
        self.context_text.setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
        elements_layout.addWidget(self.context_text)
        
        elements_tab.setLayout(elements_layout)
        
        tabs.addTab(edit_tab, "Редактор")
        tabs.addTab(elements_tab, "Выделенные элементы")
        
        layout.addWidget(tabs)
        
        dialog_btns = QHBoxLayout()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        dialog_btns.addStretch()
        dialog_btns.addWidget(close_btn)
        layout.addLayout(dialog_btns)
        
        self.setLayout(layout)
    
    def extract_elements(self):
        text = self.story_text.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Предупреждение", "Введите текст сюжета")
            return
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            elements = self.story_manager.process_and_log(
                text,
                self.logger.user_id,
                self.session_id
            )
            
            self.locations_list.clear()
            for loc in elements['locations']:
                self.locations_list.addItem(f"{loc['name']}")
            
            self.characters_list.clear()
            for char in elements['characters']:
                self.characters_list.addItem(f"{char['name']}")
            
            self.monsters_list.clear()
            for monster in elements['monsters']:
                self.monsters_list.addItem(f"{monster['name']}")
            
            self.items_list.clear()
            for item in elements['items']:
                self.items_list.addItem(f"{item['name']}")
            
            stats = self.story_manager.get_statistics()
            self.stats_label.setText(
                f"Статистика: Локации: {stats['total_locations']} | "
                f"Персонажи: {stats['total_characters']} | "
                f"Монстры: {stats['total_monsters']} | "
                f"Предметы: {stats['total_items']} | "
                f"Всего: {stats['total_elements']}"
            )
            
            QMessageBox.information(
                self, "Готово",
                f"Выделено элементов:\n\n"
                f"Локации: {len(elements['locations'])}\n"
                f"Персонажи: {len(elements['characters'])}\n"
                f"Монстры: {len(elements['monsters'])}\n"
                f"Предметы: {len(elements['items'])}\n"
                f"\nВсе элементы сохранены в лог!"
            )
            
        finally:
            QApplication.restoreOverrideCursor()
    
    def show_context(self, item, element_type):
        element_name = item.text()
        elements = self.story_manager.extracted_items
        element = None
        
        if element_type == 'location':
            element = next((e for e in elements['locations'] if e['name'] == element_name), None)
        elif element_type == 'character':
            element = next((e for e in elements['characters'] if e['name'] == element_name), None)
        elif element_type == 'monster':
            element = next((e for e in elements['monsters'] if e['name'] == element_name), None)
        elif element_type == 'item':
            element = next((e for e in elements['items'] if e['name'] == element_name), None)
        
        if element:
            context = element.get('context', 'Нет контекста')
            self.context_text.setText(f"Элемент: {element['name']}\n"
                                      f"Ключевое слово: {element.get('keyword', '?')}\n"
                                      f"Контекст: {context}")
    
    def clear_text(self):
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Очистить весь текст?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.story_text.clear()
            self.locations_list.clear()
            self.characters_list.clear()
            self.monsters_list.clear()
            self.items_list.clear()
            self.context_text.clear()
            self.stats_label.setText("Статистика: ожидание...")
    
    def save_story(self):
        text = self.story_text.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Предупреждение", "Нет текста для сохранения")
            return
        
        if not self.locations_list.count():
            reply = QMessageBox.question(
                self, "Выделение элементов",
                "Выделить элементы перед сохранением?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.extract_elements()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить сюжет", "",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        
        if filename:
            saved_file = self.story_manager.save_story_to_file(text, filename)
            QMessageBox.information(self, "Успех", f"Сюжет сохранен в:\n{saved_file}")
            self.logger.log_action('save_story', details={'filename': filename})
''')
    
    # Файл: db/Plot/init_story_actions.py
    with open("db/Plot/init_story_actions.py", "w", encoding="utf-8") as f:
        f.write('''# db/Plot/init_story_actions.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.main import app
from db.models import db
from db.logger.models_logs import init_logs_models

def init_story_actions():
    """Добавляет действия для сюжета"""
    with app.app_context():
        Action, _ = init_logs_models(db)
        
        story_actions = [
            ('create_story', 'Создание нового сюжета'),
            ('save_story', 'Сохранение сюжета в файл'),
            ('story_location', 'Локация из сюжета'),
            ('story_character', 'Персонаж из сюжета'),
            ('story_monster', 'Монстр/противник из сюжета'),
            ('story_item', 'Предмет/артефакт из сюжета'),
            ('story_published', 'Публикация сюжета для игроков')
        ]
        
        added = 0
        for action_name, description in story_actions:
            action = Action.query.filter_by(action_name=action_name).first()
            if not action:
                db.session.add(Action(action_name=action_name, description=description))
                print(f"Added story action: {action_name} - {description}")
                added += 1
        
        db.session.commit()
        print(f"\\nStory actions initialized! Added {added} new actions.")
        
        all_actions = Action.query.all()
        print(f"\\nTotal actions in system: {len(all_actions)}")

if __name__ == '__main__':
    print("Initializing story actions...")
    init_story_actions()
    print("\\nDone!")
''')
    
    print("\n✅ Все файлы сюжетной системы созданы!")
    print("\nСозданные файлы:")
    print("  - db/Plot/__init__.py")
    print("  - db/Plot/story_manager.py")
    print("  - db/Plot/story_dialog.py")
    print("  - db/Plot/init_story_actions.py")

if __name__ == "__main__":
    create_plot_files()