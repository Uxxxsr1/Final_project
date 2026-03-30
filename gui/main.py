# client.py
import sys
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox, QDialog)
from PyQt5.QtCore import Qt
from role_window import RoleWindow

API_URL = "http://localhost:5000/api"

class RegisterDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Регистрация")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QPushButton {
                background-color: #646b67;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Регистрация")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин")
        self.username_input.setMinimumHeight(40)
        layout.addWidget(self.username_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setMinimumHeight(40)
        layout.addWidget(self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(40)
        layout.addWidget(self.confirm_input)
        
        self.register_btn = QPushButton("Зарегистрироваться")
        self.register_btn.setMinimumHeight(45)
        self.register_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_btn)
        
        self.setLayout(layout)
    
    def handle_register(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if not all([username, email, password, confirm]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        
        try:
            response = requests.post(f"{API_URL}/users/create", json={
                'username': username,
                'email': email,
                'password': password
            })
            
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "Регистрация успешна!")
                self.accept()
            else:
                error = response.json().get('error', 'Неизвестная ошибка')
                QMessageBox.warning(self, "Ошибка", error)
                
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к серверу")

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.user_data = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("ДПК")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#title {
                color: #2c3e50;
                font-size: 32px;
                font-weight: bold;
                padding: 20px;
            }
            QLabel {
                color: #34495e;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QPushButton {
                background-color: #5c5e5d;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d2e2d;
            }
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("QFrame#card { background-color: white; border-radius: 16px; padding: 20px; }")
        
        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)
        
        login_label = QLabel("Логин / Email")
        login_label.setStyleSheet("color: #7f8c8d;")
        card_layout.addWidget(login_label)
        
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите ваш email или логин")
        self.login_input.setMinimumHeight(40)
        card_layout.addWidget(self.login_input)
        
        password_label = QLabel("Пароль")
        password_label.setStyleSheet("color: #7f8c8d; margin-top: 10px;")
        card_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        card_layout.addWidget(self.password_input)
        
        self.login_button = QPushButton("Вход")
        self.login_button.setMinimumHeight(45)
        self.login_button.clicked.connect(self.handle_login)
        card_layout.addWidget(self.login_button)
        
        self.register_button = QPushButton("Регистрация")
        self.register_button.setMinimumHeight(45)
        self.register_button.setStyleSheet("QPushButton { background-color: #95a5a6; } QPushButton:hover { background-color: #7f8c8d; }")
        self.register_button.clicked.connect(self.handle_register)
        card_layout.addWidget(self.register_button)
        
        base_label = QLabel("Базовый")
        base_label.setAlignment(Qt.AlignCenter)
        base_label.setStyleSheet("color: #bdc3c7; font-size: 12px; margin-top: 20px;")
        card_layout.addWidget(base_label)
        
        card.setLayout(card_layout)
        main_layout.addWidget(card)
        self.setLayout(main_layout)
    
    def handle_login(self):
        login_or_email = self.login_input.text()
        password = self.password_input.text()
        
        if not login_or_email or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        try:
            response = requests.post(f"{API_URL}/users/login", json={
                'login_or_email': login_or_email,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.user_data = data.get('user')
                QMessageBox.information(self, "Успех", f"Успешный вход, {self.user_data['username']}!")
                self.after_login()
            else:
                error = response.json().get('error', 'Неверный логин или пароль')
                QMessageBox.warning(self, "Ошибка", error)
                
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к серверу")
    
    def handle_register(self):
        dialog = RegisterDialog()
        if dialog.exec_():
            self.login_input.setText("")
            self.password_input.setText("")
    
    def after_login(self):
        self.role_window = RoleWindow(self.user_data)
        self.role_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())