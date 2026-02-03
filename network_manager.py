import socket
import json
import threading

class NetworkManager:
    def __init__(self, port=5555):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.addr = None
        self.connected = False
        
    def get_local_ip(self):
        try:
            # Conecta a un DNS público para determinar la IP local (no envía datos realmente)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def host_game(self):
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(1)
            print(f"Hosteando en {self.get_local_ip()}:{self.port}...")
            # Llamada bloqueante, debe correrse en un hilo si se usa UI
            self.conn, self.addr = self.socket.accept()
            self.connected = True
            print(f"Cliente conectado desde {self.addr}")
            return True
        except Exception as e:
            print(f"Error al hostear: {e}")
            return False

    def join_game(self, host_ip):
        try:
            print(f"Conectando a {host_ip}:{self.port}...")
            self.socket.connect((host_ip, self.port))
            self.conn = self.socket
            self.connected = True
            print("Conectado al host.")
            return True
        except Exception as e:
            print(f"Error al unirse: {e}")
            return False

    def send(self, data):
        """Envía un diccionario como string JSON."""
        if not self.conn:
            return False
            
        try:
            msg = json.dumps(data).encode('utf-8')
            self.conn.sendall(msg)
            return True
        except Exception as e:
            print(f"Error al enviar: {e}")
            self.connected = False
            return False

    def receive(self):
        """Recibe un string JSON y retorna un diccionario."""
        if not self.conn:
            return None
            
        try:
            data = self.conn.recv(1024)
            if not data:
                self.connected = False
                return None
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"Error al recibir: {e}")
            self.connected = False
            return None

    def close(self):
        if self.conn:
            self.conn.close()
        self.socket.close()
        self.connected = False
