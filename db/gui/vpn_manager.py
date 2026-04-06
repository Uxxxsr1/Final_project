# db/gui/vpn_manager.py
import subprocess
import platform
import socket
from PyQt5.QtCore import QThread, pyqtSignal

class VPNManager:
    """Управление подключением по IP"""
    def get_radmin_ip(self):
        """Получает IP адрес из Radmin VPN"""
        return self.get_local_ip()

    def open_radmin(self):
        """Открывает Radmin VPN"""
        import subprocess
        import platform
        
        system = platform.system()
        if system == "Windows":
            try:
                subprocess.Popen(["C:\\Program Files\\Radmin VPN\\RadminVPN.exe"])
            except:
                pass

    def __init__(self):
        self.system = platform.system()
    
    def test_connection(self, ip, port=25565):
        """Тестирует соединение с сервером"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_local_ip(self):
        """Получает локальный IP адрес"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_connection_instructions(self):
        """Возвращает инструкцию по подключению"""
        return """
🔧 Инструкция по подключению:

1. Убедитесь, что сервер запущен и доступен

2. Введите IP адрес сервера в настройках

3. Для подключения используйте кнопку "Подключиться"

4. Если подключение не удается:
   - Проверьте доступность сервера по ping
   - Убедитесь, что сервер запущен
   - Проверьте настройки брандмауэра
        """

class VPNConnectionThread(QThread):
    """Поток для проверки подключения"""
    connection_status = pyqtSignal(bool, str)
    
    def __init__(self, ip, port=25565):
        super().__init__()
        self.ip = ip
        self.port = port
        self.vpn_manager = VPNManager()
    
    def run(self):
        if not self.ip:
            self.connection_status.emit(False, "Нет IP адреса для подключения")
            return
        
        connected = self.vpn_manager.test_connection(self.ip, self.port)
        if connected:
            self.connection_status.emit(True, f"✅ Успешно подключено к {self.ip}:{self.port}")
        else:
            self.connection_status.emit(False, f"❌ Не удалось подключиться к {self.ip}:{self.port}")
