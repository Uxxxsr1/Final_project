# launcher.py - полная исправленная версия
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import threading
import time
import socket
import webbrowser
import json
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QProgressBar, QMessageBox, QTabWidget, QFrame,
                             QCheckBox, QGroupBox, QRadioButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor


class ServerThread(QThread):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, host='127.0.0.1', port=5000):
        super().__init__()
        self.host = host
        self.port = port
        self.process = None
        self.is_running = False
    
    def run(self):
        try:
            self.process = subprocess.Popen(
                [sys.executable, 'run.py'],
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
            
            stdout_thread = threading.Thread(target=read_output, args=(self.process.stdout, 'info'))
            stderr_thread = threading.Thread(target=read_output, args=(self.process.stderr, 'error'))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            self.process.wait()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка запуска сервера: {e}", 'error')
        finally:
            self.is_running = False
    
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            time.sleep(2)
            if self.process.poll() is None:
                self.process.kill()
            self.is_running = False


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
            time.sleep(1)
            if self.process.poll() is None:
                self.process.kill()
            self.is_running = False


class SetupThread(QThread):
    log_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(bool)
    
    def run(self):
        try:
            self.log_signal.emit("Инициализация базы данных...", 'info')
            
            if os.path.exists('init_game_tables.py'):
                process = subprocess.Popen(
                    [sys.executable, 'init_game_tables.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                
                # Декодируем с правильной кодировкой
                try:
                    stdout_text = stdout.decode('cp866') if stdout else ''
                except:
                    stdout_text = stdout.decode('utf-8', errors='ignore') if stdout else ''
                
                try:
                    stderr_text = stderr.decode('cp866') if stderr else ''
                except:
                    stderr_text = stderr.decode('utf-8', errors='ignore') if stderr else ''
                
                if stdout_text:
                    for line in stdout_text.split('\n'):
                        if line.strip():
                            self.log_signal.emit(line.strip(), 'info')
                
                if stderr_text:
                    for line in stderr_text.split('\n'):
                        if line.strip():
                            self.log_signal.emit(line.strip(), 'warning')
                
                if process.returncode == 0:
                    self.log_signal.emit("База данных успешно инициализирована!", 'success')
                    self.finished_signal.emit(True)
                else:
                    self.log_signal.emit("Ошибка инициализации базы данных", 'error')
                    self.finished_signal.emit(False)
            else:
                self.log_signal.emit("Файл init_game_tables.py не найден", 'warning')
                self.finished_signal.emit(False)
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}", 'error')
            self.finished_signal.emit(False)


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.client_thread = None
        self.setup_thread = None
        self.server_started = False
        self.client_started = False
        
        self.initUI()
        self.check_dependencies()
    
    def initUI(self):
        self.setWindowTitle("ДПЖ - Лаунчер")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(self.get_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("🎮 ДПЖ - Система управления играми 🎲")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #e67e22; padding: 15px;")
        main_layout.addWidget(title_label)
        
        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background-color: #34495e; border-radius: 10px; padding: 15px; }")
        info_layout = QHBoxLayout()
        
        self.status_label = QLabel("⚙️ Статус: Ожидание запуска")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        
        self.server_status = QLabel("🔴 Сервер: Остановлен")
        self.server_status.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(self.server_status)
        
        self.client_status = QLabel("🔴 Клиент: Остановлен")
        self.client_status.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(self.client_status)
        
        info_frame.setLayout(info_layout)
        main_layout.addWidget(info_frame)
        
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { background-color: #2c3e50; border-radius: 8px; }
            QTabBar::tab { background-color: #34495e; color: #ecf0f1; padding: 8px 20px; margin-right: 2px; }
            QTabBar::tab:selected { background-color: #e67e22; }
        """)
        
        control_tab = self.create_control_tab()
        tabs.addTab(control_tab, "🎮 Управление")
        
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "📋 Логи")
        
        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)
    
    def create_control_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        startup_group = QGroupBox("Запуск системы")
        startup_group.setStyleSheet("""
            QGroupBox { font-size: 14px; font-weight: bold; border: 2px solid #3498db; border-radius: 8px; margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        startup_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        
        self.start_all_btn = QPushButton("🚀 ЗАПУСТИТЬ ВСЁ")
        self.start_all_btn.setMinimumHeight(50)
        self.start_all_btn.setStyleSheet("QPushButton { background-color: #27ae60; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #229954; }")
        self.start_all_btn.clicked.connect(self.start_all)
        btn_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QPushButton("🛑 ОСТАНОВИТЬ ВСЁ")
        self.stop_all_btn.setMinimumHeight(50)
        self.stop_all_btn.setStyleSheet("QPushButton { background-color: #e74c3c; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
        self.stop_all_btn.clicked.connect(self.stop_all)
        self.stop_all_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_all_btn)
        
        startup_layout.addLayout(btn_layout)
        
        separate_layout = QHBoxLayout()
        
        self.start_server_btn = QPushButton("▶ Запустить сервер")
        self.start_server_btn.clicked.connect(self.start_server)
        separate_layout.addWidget(self.start_server_btn)
        
        self.stop_server_btn = QPushButton("⏹ Остановить сервер")
        self.stop_server_btn.clicked.connect(self.stop_server)
        self.stop_server_btn.setEnabled(False)
        separate_layout.addWidget(self.stop_server_btn)
        
        self.start_client_btn = QPushButton("▶ Запустить клиент")
        self.start_client_btn.clicked.connect(self.start_client)
        separate_layout.addWidget(self.start_client_btn)
        
        self.stop_client_btn = QPushButton("⏹ Остановить клиент")
        self.stop_client_btn.clicked.connect(self.stop_client)
        self.stop_client_btn.setEnabled(False)
        separate_layout.addWidget(self.stop_client_btn)
        
        startup_layout.addLayout(separate_layout)
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        settings_group = QGroupBox("Настройки")
        settings_group.setStyleSheet("""
            QGroupBox { font-size: 14px; font-weight: bold; border: 2px solid #2ecc71; border-radius: 8px; margin-top: 10px; padding-top: 10px; }
        """)
        settings_layout = QVBoxLayout()
        
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("IP адрес сервера:"))
        self.ip_input = QTextEdit()
        self.ip_input.setPlainText("127.0.0.1")
        self.ip_input.setMaximumHeight(30)
        self.ip_input.setMaximumWidth(150)
        ip_layout.addWidget(self.ip_input)
        
        ip_layout.addWidget(QLabel("Порт:"))
        self.port_input = QTextEdit()
        self.port_input.setPlainText("5000")
        self.port_input.setMaximumHeight(30)
        self.port_input.setMaximumWidth(80)
        ip_layout.addWidget(self.port_input)
        
        ip_layout.addStretch()
        settings_layout.addLayout(ip_layout)
        
        self.auto_open_browser = QCheckBox("Автоматически открывать браузер при запуске")
        self.auto_open_browser.setChecked(True)
        settings_layout.addWidget(self.auto_open_browser)
        
        self.auto_start_server = QCheckBox("Автоматически запускать сервер при старте лаунчера")
        self.auto_start_server.setChecked(False)
        settings_layout.addWidget(self.auto_start_server)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        return tab
    
    def create_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр:"))
        
        self.filter_all = QRadioButton("Все")
        self.filter_all.setChecked(True)
        self.filter_info = QRadioButton("Инфо")
        self.filter_error = QRadioButton("Ошибки")
        self.filter_client = QRadioButton("Клиент")
        
        filter_layout.addWidget(self.filter_all)
        filter_layout.addWidget(self.filter_info)
        filter_layout.addWidget(self.filter_error)
        filter_layout.addWidget(self.filter_client)
        filter_layout.addStretch()
        
        self.clear_logs_btn = QPushButton("Очистить")
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        filter_layout.addWidget(self.clear_logs_btn)
        
        layout.addLayout(filter_layout)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 10))
        self.logs_text.setStyleSheet("QTextEdit { background-color: #1a1a2e; color: #ecf0f1; border-radius: 8px; padding: 15px; }")
        layout.addWidget(self.logs_text)
        
        tab.setLayout(layout)
        return tab
    
    def get_stylesheet(self):
        return """
            QMainWindow { background-color: #1a1a2e; }
            QLabel { color: #ecf0f1; }
            QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
            QTextEdit { background-color: #2c3e50; color: #ecf0f1; border: 1px solid #34495e; border-radius: 5px; }
            QCheckBox { color: #ecf0f1; }
            QRadioButton { color: #ecf0f1; }
            QProgressBar { border: 2px solid #34495e; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #27ae60; border-radius: 3px; }
        """
    
    def check_dependencies(self):
        required_files = ['run.py', 'client.py', 'db/main.py']
        missing = []
        
        for file in required_files:
            if not os.path.exists(file):
                missing.append(file)
        
        if missing:
            reply = QMessageBox.question(
                self, 
                "Отсутствуют файлы",
                f"Следующие файлы не найдены:\n{chr(10).join(missing)}\n\nЗапустить инициализацию проекта?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.run_setup()
    
    def run_setup(self):
        self.status_label.setText("⚙️ Статус: Инициализация...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.setup_thread = SetupThread()
        self.setup_thread.log_signal.connect(self.add_log)
        self.setup_thread.finished_signal.connect(self.on_setup_finished)
        self.setup_thread.start()
    
    def on_setup_finished(self, success):
        self.progress_bar.setVisible(False)
        if success:
            self.status_label.setText("✅ Статус: Готов к запуску")
            self.add_log("Система готова к запуску!", 'success')
        else:
            self.status_label.setText("⚠️ Статус: Требуется ручная настройка")
            self.add_log("Возможно, потребуется установить зависимости: pip install -r requirements.txt", 'warning')
    
    def start_all(self):
        self.start_server()
        QTimer.singleShot(2000, self.start_client)
    
    def stop_all(self):
        self.stop_client()
        self.stop_server()
    
    def start_server(self):
        if self.server_started:
            self.add_log("Сервер уже запущен", 'warning')
            return
        
        self.add_log("Запуск сервера...", 'info')
        self.status_label.setText("⚙️ Статус: Запуск сервера...")
        
        ip = self.ip_input.toPlainText().strip()
        port = self.port_input.toPlainText().strip()
        
        config = {'api_url': f"http://{ip}:{port}/api"}
        with open('client_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        self.server_thread = ServerThread(ip, int(port))
        self.server_thread.log_signal.connect(self.add_log)
        self.server_thread.start()
        
        QTimer.singleShot(2000, self.check_server_started)
    
    def check_server_started(self):
        ip = self.ip_input.toPlainText().strip()
        port = self.port_input.toPlainText().strip()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, int(port)))
            sock.close()
            
            if result == 0:
                self.server_started = True
                self.server_status.setText(f"🟢 Сервер: Запущен ({ip}:{port})")
                self.start_server_btn.setEnabled(False)
                self.stop_server_btn.setEnabled(True)
                self.status_label.setText("✅ Статус: Сервер запущен")
                self.add_log(f"✅ Сервер успешно запущен на {ip}:{port}", 'success')
                
                if self.auto_open_browser.isChecked():
                    webbrowser.open(f"http://{ip}:{port}")
            else:
                self.add_log("⚠️ Сервер запущен, но не отвечает на запросы", 'warning')
                
        except Exception as e:
            self.add_log(f"Ошибка проверки сервера: {e}", 'error')
    
    def stop_server(self):
        if not self.server_started:
            return
        
        self.add_log("Остановка сервера...", 'info')
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread = None
        
        self.server_started = False
        self.server_status.setText("🔴 Сервер: Остановлен")
        self.start_server_btn.setEnabled(True)
        self.stop_server_btn.setEnabled(False)
        self.status_label.setText("⚙️ Статус: Сервер остановлен")
        self.add_log("Сервер остановлен", 'info')
    
    def start_client(self):
        if self.client_started:
            self.add_log("Клиент уже запущен", 'warning')
            return
        
        if not self.server_started:
            reply = QMessageBox.question(
                self,
                "Сервер не запущен",
                "Сервер не запущен. Запустить сервер сначала?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.start_server()
                QTimer.singleShot(3000, self.start_client)
            return
        
        self.add_log("Запуск клиента...", 'info')
        
        self.client_thread = ClientThread()
        self.client_thread.log_signal.connect(self.add_log)
        self.client_thread.start()
        
        QTimer.singleShot(2000, self.check_client_started)
    
    def check_client_started(self):
        self.client_started = True
        self.client_status.setText("🟢 Клиент: Запущен")
        self.start_client_btn.setEnabled(False)
        self.stop_client_btn.setEnabled(True)
        self.start_all_btn.setEnabled(False)
        self.stop_all_btn.setEnabled(True)
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
        self.start_client_btn.setEnabled(True)
        self.stop_client_btn.setEnabled(False)
        self.start_all_btn.setEnabled(True)
        self.stop_all_btn.setEnabled(False)
        self.add_log("Клиент остановлен", 'info')
    
    def add_log(self, message, log_type='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {'info': '#3498db', 'error': '#e74c3c', 'warning': '#f39c12', 'success': '#2ecc71', 'client': '#9b59b6'}
        prefixes = {'info': '[INFO]', 'error': '[ERROR]', 'warning': '[WARN]', 'success': '[OK]', 'client': '[CLIENT]'}
        
        color = colors.get(log_type, '#ecf0f1')
        prefix = prefixes.get(log_type, '[LOG]')
        
        formatted_message = f'<span style="color: #7f8c8d;">[{timestamp}]</span> <span style="color: {color};">{prefix}</span> <span style="color: #ecf0f1;">{message}</span>'
        
        current_filter = self.get_current_filter()
        show = False
        
        if current_filter == 'all':
            show = True
        elif current_filter == 'info' and log_type in ['info', 'success']:
            show = True
        elif current_filter == 'error' and log_type == 'error':
            show = True
        elif current_filter == 'client' and log_type == 'client':
            show = True
        
        if show:
            self.logs_text.append(formatted_message)
            cursor = self.logs_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.logs_text.setTextCursor(cursor)
    
    def get_current_filter(self):
        if self.filter_all.isChecked():
            return 'all'
        elif self.filter_info.isChecked():
            return 'info'
        elif self.filter_error.isChecked():
            return 'error'
        elif self.filter_client.isChecked():
            return 'client'
        return 'all'
    
    def clear_logs(self):
        self.logs_text.clear()
        self.add_log("Логи очищены", 'info')
    
    def closeEvent(self, event):
        self.stop_client()
        self.stop_server()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = LauncherWindow()
    window.show()
    
    if window.auto_start_server.isChecked():
        QTimer.singleShot(1000, window.start_server)
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()