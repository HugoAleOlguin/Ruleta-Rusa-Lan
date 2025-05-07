import socket
import threading
import json
import sys
import time
import subprocess
import os

class Jugador:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.nombre = "Jugador"

def configurar_firewall():
    try:
        # Eliminar regla existente si existe
        subprocess.run(['netsh', 'advfirewall', 'firewall', 'delete', 'rule', 
                       'name=RuletaRusa'], capture_output=True)
        
        # Crear nueva regla
        subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule',
                       'name=RuletaRusa',
                       'dir=in',
                       'action=allow',
                       'protocol=TCP',
                       'localport=443'], capture_output=True)
        return True
    except:
        return False

def main():
    if configurar_firewall():
        print("Firewall configurado correctamente")
    else:
        print("Advertencia: No se pudo configurar el firewall")

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 443))
        server.listen(2)
        print("Servidor iniciado en puerto 443")
        print("IP local:", socket.gethostbyname(socket.gethostname()))
        
        jugadores = []
        
        while True:
            try:
                conn, addr = server.accept()
                if len(jugadores) < 2:
                    jugador = Jugador(conn, addr)
                    jugadores.append(jugador)
                    print(f"Jugador conectado desde {addr}")
                    
                    # Iniciar thread para este jugador
                    thread = threading.Thread(target=manejar_cliente, 
                                           args=(jugador, jugadores))
                    thread.daemon = True
                    thread.start()
            except:
                pass
                
    except Exception as e:
        print(f"Error del servidor: {e}")
        time.sleep(5)
        sys.exit(1)

def manejar_cliente(jugador, jugadores):
    try:
        data = jugador.conn.recv(1024)
        if not data:
            return
            
        datos = json.loads(data.decode())
        if datos["tipo"] == "conexion":
            jugador.nombre = datos["nombre"]
            print(f"Jugador {jugador.nombre} conectado")
            
            # Informar a los jugadores
            for otro in jugadores:
                if otro != jugador:
                    try:
                        mensaje = json.dumps({
                            "tipo": "conexion",
                            "nombre": jugador.nombre
                        }).encode()
                        otro.conn.send(mensaje)
                        
                        # También enviar los datos del otro jugador al nuevo
                        mensaje_reverso = json.dumps({
                            "tipo": "conexion",
                            "nombre": otro.nombre
                        }).encode()
                        jugador.conn.send(mensaje_reverso)
                    except:
                        continue

        while True:
            try:
                data = jugador.conn.recv(1024)
                if not data:
                    break
                
                # Validar que el mensaje sea JSON válido antes de reenviar
                datos = json.loads(data.decode())
                
                # Reenviar mensaje a todos los demás jugadores
                for otro in jugadores:
                    if otro != jugador:
                        try:
                            otro.conn.send(data)
                        except:
                            if otro in jugadores:
                                jugadores.remove(otro)
                            
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error recibiendo datos: {e}")
                break
                
    except Exception as e:
        print(f"Error en manejo de cliente: {e}")
    finally:
        if jugador in jugadores:
            jugadores.remove(jugador)
        try:
            jugador.conn.close()
        except:
            pass

if __name__ == "__main__":
    main()
