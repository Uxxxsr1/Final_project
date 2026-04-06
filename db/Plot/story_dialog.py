# db/Plot/story_dialog.py
import os
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
            QPushButton#import_btn {
                background-color: #9b59b6;
            }
            QPushButton#import_btn:hover {
                background-color: #8e44ad;
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
    
        import_btn = QPushButton("📁 Импорт из TXT")
        import_btn.setObjectName("import_btn")
        import_btn.clicked.connect(self.import_story)
        btn_layout.addWidget(import_btn)
        
        # Новая кнопка добавления элемента
        add_element_btn = QPushButton("✨ Добавить элемент")
        add_element_btn.setObjectName("add_element_btn")
        add_element_btn.setStyleSheet("background-color: #9b59b6;")
        add_element_btn.clicked.connect(self.add_custom_element)
        btn_layout.addWidget(add_element_btn)
        
        extract_btn = QPushButton("🔍 Выделить элементы")
        extract_btn.setObjectName("extract_btn")
        extract_btn.clicked.connect(self.extract_elements)
        btn_layout.addWidget(extract_btn)
        
        clear_btn = QPushButton("🗑 Очистить")
        clear_btn.setObjectName("clear_btn")
        clear_btn.clicked.connect(self.clear_text)
        btn_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("💾 Сохранить сюжет")
        save_btn.setObjectName("save_btn")
        save_btn.clicked.connect(self.save_story)
        btn_layout.addWidget(save_btn)
        
        btn_layout.addStretch()
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
    
    def add_custom_element(self):
        """Добавляет пользовательский элемент в сюжет"""
        from PyQt5.QtWidgets import QInputDialog, QComboBox, QDialog, QVBoxLayout, QHBoxLayout
        
        # Диалог добавления элемента
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление элемента")
        dialog.setMinimumSize(400, 300)
        dialog.setStyleSheet("background-color: #2c3e50;")
        
        layout = QVBoxLayout()
        
        # Тип элемента
        layout.addWidget(QLabel("Тип элемента:"))
        type_combo = QComboBox()
        type_combo.addItems(["Локация", "Персонаж", "Монстр", "Предмет", "Событие"])
        layout.addWidget(type_combo)
        
        # Название
        layout.addWidget(QLabel("Название:"))
        name_input = QLineEdit()
        name_input.setPlaceholderText("Введите название...")
        layout.addWidget(name_input)
        
        # Описание/контекст
        layout.addWidget(QLabel("Описание/контекст:"))
        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Введите описание...")
        desc_input.setMaximumHeight(100)
        layout.addWidget(desc_input)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("✅ Добавить")
        add_btn.setStyleSheet("background-color: #27ae60;")
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setStyleSheet("background-color: #95a5a6;")
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        
        def on_add():
            element_type = type_combo.currentText().lower()
            name = name_input.text().strip()
            description = desc_input.toPlainText().strip()
            
            if not name:
                QMessageBox.warning(dialog, "Ошибка", "Введите название элемента")
                return
            
            # Добавляем элемент в текст сюжета
            current_text = self.story_text.toPlainText()
            new_element = f"\n\n[{element_type.upper()}] {name}"
            if description:
                new_element += f"\nОписание: {description}"
            
            self.story_text.setPlainText(current_text + new_element)
            
            # Логируем добавление
            self.logger.log_action(f'story_{element_type}', 
                                details={'name': name, 'context': description})
            
            QMessageBox.information(dialog, "Успех", f"Элемент '{name}' добавлен в сюжет!")
            dialog.accept()
            
            # Предлагаем выделить элементы
            reply = QMessageBox.question(self, "Выделение элементов",
                                        "Выделить все элементы в сюжете?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.extract_elements()
        
        add_btn.clicked.connect(on_add)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def import_story(self):
        """Импортирует сюжет из TXT файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите файл с сюжетом", 
            "", 
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Пробуем разные кодировки
            encodings = ['utf-8', 'cp1251', 'cp866', 'latin-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                QMessageBox.warning(self, "Ошибка", "Не удалось прочитать файл. Проверьте кодировку.")
                return
            
            # Спрашиваем, заменить текущий текст или добавить
            current_text = self.story_text.toPlainText()
            
            if current_text.strip():
                reply = QMessageBox.question(
                    self, 
                    "Импорт сюжета",
                    "Заменить текущий текст или добавить в конец?\n\n"
                    "Да - заменить\n"
                    "Нет - добавить в конец\n"
                    "Отмена - отменить импорт",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Yes:
                    self.story_text.setPlainText(content)
                else:
                    self.story_text.setPlainText(current_text + "\n\n" + content)
            else:
                self.story_text.setPlainText(content)
            
            # Автоматически выделяем элементы после импорта
            reply = QMessageBox.question(
                self,
                "Выделение элементов",
                "Выделить элементы из импортированного сюжета?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.extract_elements()
            
            # Логируем импорт
            self.logger.log_action('import_story', details={'filename': os.path.basename(file_path)})
            
            QMessageBox.information(self, "Успех", f"Сюжет импортирован из:\n{file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при импорте файла:\n{str(e)}")
    
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
        """Очищает весь текст и списки"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Очистить весь текст и выделенные элементы?",
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
            self.logger.log_action('clear_story')
    
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