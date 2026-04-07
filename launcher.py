# launcher.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import json
from datetime import datetime

# ============ FIX QT PLUGINS FOR WINDOWS ============
# Это должно быть ДО импорта PyQt5!

def fix_qt_plugins():
    """Исправляет путь к Qt плагинам для Windows"""
    if sys.platform != 'win32':
        return
    
    # Список возможных путей к плагинам Qt
    possible_paths = [
        # Путь в виртуальном окружении
        os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins'),
        # Путь в глобальной установке
        os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins'),
        # Альтернативный путь
        os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins'),
    ]
    
    # Добавляем пути из site-packages
    try:
        import site
        for site_packages in site.getsitepackages():
            possible_paths.append(os.path.join(site_packages, 'PyQt5', 'Qt5', 'plugins'))
    except:
        pass
    
    # Ищем существующий путь
    for path in possible_paths:
        if os.path.exists(path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = path
            print(f"Qt plugins path set to: {path}")
            break
    
    # Устанавливаем платформу
    os.environ['QT_QPA_PLATFORM'] = 'windows'
    
    # Добавляем путь к библиотекам Qt в PATH
    qt_bin_path = os.path.dirname(os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH', ''))
    if qt_bin_path and os.path.exists(qt_bin_path):
        os.environ['PATH'] = qt_bin_path + os.pathsep + os.environ.get('PATH', '')

# Вызываем функцию ДО импорта PyQt5
fix_qt_plugins()

# Теперь импортируем PyQt5
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QMessageBox, QTabWidget, QFrame, QCheckBox,
                             QGroupBox, QLineEdit, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor


class ClientThread(QThread):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.is_running = False
    
    def run(self):
        try:
            self.process = subprocess.Popen(
                [sys.executable, 'client.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1
            )
            
            self.is_running = True
            
            def read_output(pipe, log_type):
                try:
                    for line in iter(pipe.readline, b''):
                        if line:
                            try:
                                decoded_line = line.decode('cp866')
                            except UnicodeDecodeError:
                                try:
                                    decoded_line = line.decode('utf-8', errors='ignore')
                                except:
                                    decoded_line = str(line)
                            if decoded_line.strip():
                                self.log_signal.emit(decoded_line.strip(), log_type)
                except Exception as e:
                    self.log_signal.emit(f"Error reading {log_type}: {e}", 'error')
            
            stdout_thread = threading.Thread(target=read_output, args=(self.process.stdout, 'client'))
            stderr_thread = threading.Thread(target=read_output, args=(self.process.stderr, 'error'))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            self.process.wait()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка запуска клиента: {e}", 'error')
        finally:
            self.is_running = False
    
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            QTimer.singleShot(2000, self.kill_process)
    
    def kill_process(self):
        if self.process and self.process.poll() is None:
            self.process.kill()
        self.is_running = False


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_thread = None
        self.client_started = False
        
        self.initUI()
        self.load_config()
    
    def initUI(self):
        self.setWindowTitle("ДПЖ - Лаунчер")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(self.get_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        title_label = QLabel("🎮 ДПЖ - Система управления играми 🎲")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #e67e22; padding: 15px;")
        main_layout.addWidget(title_label)
        
        # Информационная панель
        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background-color: #3a3a3a; border-radius: 10px; padding: 15px; }")
        info_layout = QHBoxLayout()
        
        self.status_label = QLabel("⚙️ Статус: Ожидание запуска")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        
        self.client_status = QLabel("🔴 Клиент: Остановлен")
        self.client_status.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(self.client_status)
        
        info_frame.setLayout(info_layout)
        main_layout.addWidget(info_frame)
        
        # Вкладки
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { background-color: #2e2e2e; border-radius: 8px; }
            QTabBar::tab { background-color: #3a3a3a; color: #e0e0e0; padding: 8px 20px; margin-right: 2px; }
            QTabBar::tab:selected { background-color: #e67e22; }
        """)
        
        control_tab = self.create_control_tab()
        tabs.addTab(control_tab, "🎮 Управление")
        
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "⚙️ Настройки")
        
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "📋 Логи")
        
        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)
    
    def get_stylesheet(self):
        return """
            QMainWindow { background-color: #2e2e2e; }
            QLabel { color: #e0e0e0; }
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton#start_btn {
                background-color: #2d6a4f;
            }
            QPushButton#start_btn:hover {
                background-color: #40916c;
            }
            QPushButton#stop_btn {
                background-color: #8b3a3a;
            }
            QPushButton#stop_btn:hover {
                background-color: #a04040;
            }
            QTextEdit {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 5px;
                font-family: monospace;
            }
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
            }
            QCheckBox {
                color: #e0e0e0;
            }
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QProgressBar {
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2d6a4f;
                border-radius: 3px;
            }
        """
    
    def create_control_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Группа запуска
        startup_group = QGroupBox("Запуск клиента")
        startup_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 ЗАПУСТИТЬ КЛИЕНТ")
        self.start_btn.setObjectName("start_btn")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_client)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("🛑 ОСТАНОВИТЬ КЛИЕНТ")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.stop_btn.clicked.connect(self.stop_client)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        startup_layout.addLayout(btn_layout)
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Информация
        info_group = QGroupBox("Информация")
        info_layout = QVBoxLayout()
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        self.info_text.setPlainText("""
ДПЖ - Система управления играми

Для начала игры:
1. Запустите сервер (отдельно)
2. Нажмите "Запустить клиент"
3. Войдите в аккаунт или зарегистрируйтесь
4. Выберите роль (Гейм Мастер или Игрок)
        """.strip())
        info_layout.addWidget(self.info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Настройки сервера
        server_group = QGroupBox("Настройки подключения к серверу")
        server_layout = QVBoxLayout()
        
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("IP адрес сервера:"))
        self.server_ip_input = QLineEdit()
        self.server_ip_input.setPlaceholderText("127.0.0.1")
        ip_layout.addWidget(self.server_ip_input)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Порт:"))
        self.server_port_input = QLineEdit()
        self.server_port_input.setPlaceholderText("5000")
        port_layout.addWidget(self.server_port_input)
        
        save_server_btn = QPushButton("💾 Сохранить настройки")
        save_server_btn.clicked.connect(self.save_server_settings)
        
        server_layout.addLayout(ip_layout)
        server_layout.addLayout(port_layout)
        server_layout.addWidget(save_server_btn)
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Настройки автозапуска
        auto_group = QGroupBox("Автоматический запуск")
        auto_layout = QVBoxLayout()
        
        self.auto_start_client = QCheckBox("Автоматически запускать клиент при старте лаунчера")
        self.auto_start_client.setChecked(False)
        auto_layout.addWidget(self.auto_start_client)
        
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.logs_text)
        
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self.clear_logs)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab
    
    def load_config(self):
        """Загружает конфигурацию из файла"""
        config_file = "client_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    api_url = config.get('api_url', 'http://127.0.0.1:5000/api')
                    url_part = api_url.replace('http://', '').replace('/api', '')
                    if ':' in url_part:
                        ip, port = url_part.split(':')
                        self.server_ip_input.setText(ip)
                        self.server_port_input.setText(port)
                    else:
                        self.server_ip_input.setText(url_part)
                        self.server_port_input.setText('5000')
            except:
                self.server_ip_input.setText("127.0.0.1")
                self.server_port_input.setText("5000")
        else:
            self.server_ip_input.setText("127.0.0.1")
            self.server_port_input.setText("5000")
    
    def save_server_settings(self):
        """Сохраняет настройки сервера"""
        ip = self.server_ip_input.text().strip()
        port = self.server_port_input.text().strip()
        
        if not ip:
            ip = "127.0.0.1"
        if not port:
            port = "5000"
        
        config = {'api_url': f"http://{ip}:{port}/api"}
        with open('client_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        self.add_log(f"Настройки сохранены: сервер {ip}:{port}", 'success')
        QMessageBox.information(self, "Успех", f"Настройки сохранены!\nСервер: {ip}:{port}")
    
    def start_client(self):
        if self.client_started:
            self.add_log("Клиент уже запущен", 'warning')
            return
        
        self.add_log("Запуск клиента...", 'info')
        self.status_label.setText("⚙️ Статус: Запуск клиента...")
        
        self.client_thread = ClientThread()
        self.client_thread.log_signal.connect(self.add_log)
        self.client_thread.start()
        
        QTimer.singleShot(2000, self.check_client_started)
    
    def check_client_started(self):
        if self.client_thread and self.client_thread.is_running:
            self.client_started = True
            self.client_status.setText("🟢 Клиент: Запущен")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("✅ Статус: Клиент запущен")
            self.add_log("✅ Клиент запущен", 'success')
    
    def stop_client(self):
        if not self.client_started:
            return
        
        self.add_log("Остановка клиента...", 'info')
        if self.client_thread:
            self.client_thread.stop()
            self.client_thread = None
        
        self.client_started = False
        self.client_status.setText("🔴 Клиент: Остановлен")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⚙️ Статус: Клиент остановлен")
        self.add_log("Клиент остановлен", 'info')
    
    def add_log(self, message, log_type='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {'info': '#3498db', 'error': '#e74c3c', 'warning': '#f39c12', 
                  'success': '#2ecc71', 'client': '#9b59b6'}
        prefixes = {'info': '[INFO]', 'error': '[ERROR]', 'warning': '[WARN]', 
                    'success': '[OK]', 'client': '[CLIENT]'}
        
        color = colors.get(log_type, '#e0e0e0')
        prefix = prefixes.get(log_type, '[LOG]')
        
        formatted_message = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color};">{prefix}</span> <span style="color: #e0e0e0;">{message}</span>'
        
        self.logs_text.append(formatted_message)
        cursor = self.logs_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.logs_text.setTextCursor(cursor)
    
    def clear_logs(self):
        self.logs_text.clear()
        self.add_log("Логи очищены", 'info')
    
    def closeEvent(self, event):
        self.stop_client()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = LauncherWindow()
    window.show()
    
    if window.auto_start_client.isChecked():
        QTimer.singleShot(1000, window.start_client)
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()