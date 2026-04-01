# db/gui/config_client.py
import json
import os

CONFIG_FILE = "client_config.json"

class ClientConfig:
    """Класс для управления настройками клиента"""
    
    def __init__(self):
        self.api_url = "http://localhost:5000/api"
        self.load_config()
    
    def load_config(self):
        """Загружает конфигурацию из файла"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_url = config.get('api_url', self.api_url)
            except:
                pass
    
    def save_config(self):
        """Сохраняет конфигурацию в файл"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'api_url': self.api_url}, f, indent=2)
    
    def set_api_url(self, url):
        """Устанавливает новый URL API"""
        self.api_url = url
        self.save_config()
    
    def get_server_ip(self):
        """Получает IP сервера из URL"""
        return self.api_url.replace('http://', '').replace('/api', '').split(':')[0]
    
    def show_config_dialog(self, parent=None):
        """Показывает диалог настройки подключения"""
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        current = self.api_url.replace('http://', '').replace('/api', '')
        url, ok = QInputDialog.getText(
            parent, "Настройка подключения к серверу",
            "Введите IP адрес сервера:\nПример: 192.168.1.100\n\n"
            "Текущий адрес: " + current,
            text=current
        )
        
        if ok and url:
            if ':' in url:
                ip_port = url
            else:
                ip_port = f"{url}:5000"
            
            api_url = f"http://{ip_port}/api"
            self.set_api_url(api_url)
            QMessageBox.information(parent, "Успех", f"Сервер изменен на: {api_url}")
            return True
        return False

# Глобальный экземпляр конфига
client_config = ClientConfig()
API_URL = client_config.api_url
