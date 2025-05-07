import os
import random
import time
import ctypes
import sys
import tkinter as tk
from tkinter import messagebox, PhotoImage
import math
import socket
import json
import threading

# Verifica si el programa tiene permisos de administrador
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class RuletaRusa:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Ruleta Rusa")
        self.root.geometry("500x600")  # Hacemos la ventana un poco más alta
        self.root.configure(bg='#2C3E50')
        self.root.resizable(False, False)
        
        # Cargamos las imágenes con manejo de errores
        try:
            self.img_empty = tk.PhotoImage(file=resource_path("bullet_empty.png"))
            self.img_bullet = tk.PhotoImage(file=resource_path("bullet.png"))
            self.img_unknown = tk.PhotoImage(file=resource_path("bullet_unknown.png"))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las imágenes: {e}")
            sys.exit(1)
        
        self.modo_online = False
        self.cliente = None
        self.turno = False
        self.ip_servidor = tk.StringVar(value="26.186.82.94")
        self.puerto = tk.IntVar(value=443)  # Cambio a puerto 443
        self.nombre_jugador = tk.StringVar(value="Jugador")
        self.nombre_oponente = "Esperando..."
        
        self.mostrar_menu_inicial()

    def mostrar_menu_inicial(self):
        self.menu_frame = tk.Frame(self.root, bg='#2C3E50')
        self.menu_frame.pack(expand=True, fill='both')
        
        tk.Label(self.menu_frame, 
                text="RULETA RUSA", 
                font=("Impact", 48),
                fg='#E74C3C',
                bg='#2C3E50').pack(pady=20)
        
        # Campo de nombre
        frame_nombre = tk.Frame(self.menu_frame, bg='#2C3E50')
        frame_nombre.pack(pady=10)
        tk.Label(frame_nombre, text="Tu nombre:", bg='#2C3E50', fg='white').pack(side=tk.LEFT)
        tk.Entry(frame_nombre, textvariable=self.nombre_jugador, width=15).pack(side=tk.LEFT, padx=5)
        
        # Modo Local
        tk.Button(self.menu_frame,
                 text="Modo Local",
                 font=("Arial", 16),
                 command=self.iniciar_modo_local).pack(pady=10)
        
        # Frame para configuración online
        frame_online = tk.Frame(self.menu_frame, bg='#2C3E50')
        frame_online.pack(pady=20)
        
        tk.Label(frame_online, text="IP:", bg='#2C3E50', fg='white').pack(side=tk.LEFT)
        tk.Entry(frame_online, textvariable=self.ip_servidor, width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_online, text="Puerto:", bg='#2C3E50', fg='white').pack(side=tk.LEFT)
        tk.Entry(frame_online, textvariable=self.puerto, width=6).pack(side=tk.LEFT, padx=5)
        
        # Botones online
        frame_botones = tk.Frame(self.menu_frame, bg='#2C3E50')
        frame_botones.pack()
        
        tk.Button(frame_botones,
                 text="Crear Partida",
                 font=("Arial", 14),
                 command=self.crear_partida).pack(side=tk.LEFT, padx=5)
                 
        tk.Button(frame_botones,
                 text="Unirse",
                 font=("Arial", 14),
                 command=self.unirse_partida).pack(side=tk.LEFT, padx=5)

    def crear_partida(self):
        try:
            import subprocess
            import os
            
            # Usar resource_path para el servidor
            servidor_path = resource_path("servidor_ruleta.py")
            if getattr(sys, 'frozen', False):
                # Si es ejecutable compilado, usar python del sistema
                subprocess.Popen(['python', servidor_path])
            else:
                # Si es script, ejecutar directamente
                subprocess.Popen([sys.executable, servidor_path])
                
            self.root.after(1000, lambda: self.conectar_como_host())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el servidor: {e}")

    def conectar_como_host(self):
        self.modo_online = True
        self.turno = True
        self.conectar_a_servidor()

    def unirse_partida(self):
        self.modo_online = True
        self.turno = False
        self.conectar_a_servidor()
    
    def conectar_a_servidor(self):
        try:
            estado_temp = tk.Label(self.menu_frame,
                             text="Conectando...",
                             font=("Arial", 12),
                             fg='white',
                             bg='#2C3E50')
            estado_temp.pack(pady=10)
            self.root.update()

            self.cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.cliente.settimeout(15)  # Aumentamos el timeout a 15 segundos
        
            ip = self.ip_servidor.get()
            puerto = self.puerto.get()
        
            estado_temp.config(text=f"Conectando a {ip}:{puerto}...")
            self.root.update()
        
            try:
                self.cliente.connect((ip, puerto))
                print(f"Conectado exitosamente a {ip}:{puerto}")

            # Enviar datos iniciales
                datos_iniciales = {
                    "tipo": "conexion",
                    "nombre": self.nombre_jugador.get()
            }
                self.cliente.send(json.dumps(datos_iniciales).encode())
                print("Datos iniciales enviados")
            
            # Iniciar thread de recepción
                thread = threading.Thread(target=self.recibir_datos)
                thread.daemon = True
                thread.start()
                print("Thread de recepción iniciado")
            
            # Actualizar UI
                estado_temp.destroy()
                self.iniciar_modo_local()
                self.estado.config(text="Conectado! " + ("Tu turno" if self.turno else "Esperando..."))
            
            except socket.timeout:
                estado_temp.destroy()
                messagebox.showerror("Error", "Tiempo de espera agotado al conectar")
                if hasattr(self, 'cliente'):
                    self.cliente.close()
                    return
            
        except Exception as e:
            print(f"Error en conectar_a_servidor: {e}")
            if hasattr(self, 'menu_frame'):
                estado_temp.destroy()
                messagebox.showerror("Error", f"Error inesperado: {e}")
            if hasattr(self, 'cliente'):
                self.cliente.close()

    def iniciar_modo_local(self):
        self.menu_frame.destroy()
        self.setup_ui()
        self.nuevo_juego()
    
    def recibir_datos(self):
        while True:
            try:
                data = self.cliente.recv(1024)
                if not data:
                    break
                    
                datos = json.loads(data.decode())
                if datos["tipo"] == "disparo":
                    self.procesar_disparo_remoto(datos)
            except:
                break
        
        self.cliente.close()

    def setup_ui(self):
        # Título
        titulo = tk.Label(self.root, 
                         text="RULETA RUSA", 
                         font=("Impact", 36),
                         fg='#E74C3C',
                         bg='#2C3E50')
        titulo.pack(pady=20)
        
        # Panel de información del juego
        self.info_frame = tk.Frame(self.root, bg='#2C3E50')
        self.info_frame.pack(fill='x', padx=20)
        
        # Jugadores y turnos
        self.label_jugador = tk.Label(self.info_frame,
                                    text=f"👉 {self.nombre_jugador.get()}",
                                    font=("Arial", 12),
                                    fg='#2ECC71',
                                    bg='#2C3E50')
        self.label_jugador.pack(side=tk.LEFT, padx=10)
        
        self.label_vs = tk.Label(self.info_frame,
                                text="VS",
                                font=("Arial", 12, "bold"),
                                fg='#E74C3C',
                                bg='#2C3E50')
        self.label_vs.pack(side=tk.LEFT, padx=10)
        
        self.label_oponente = tk.Label(self.info_frame,
                                     text=self.nombre_oponente,
                                     font=("Arial", 12),
                                     fg='#95A5A6',
                                     bg='#2C3E50')
        self.label_oponente.pack(side=tk.LEFT, padx=10)
        
        # Indicador de turno
        self.turno_label = tk.Label(self.root,
                                  text="▶ Tu turno" if self.turno else "Esperando...",
                                  font=("Arial", 14, "bold"),
                                  fg='#2ECC71' if self.turno else '#95A5A6',
                                  bg='#2C3E50')
        self.turno_label.pack(pady=5)
        
        # Marco para el tambor
        self.frame_tambor = tk.Canvas(self.root, 
                                    width=300, 
                                    height=300,
                                    bg='#34495E',
                                    highlightthickness=0)
        self.frame_tambor.pack(pady=20)
        
        # Dibujar el tambor circular
        self.frame_tambor.create_oval(50, 50, 250, 250, 
                                    width=3, 
                                    outline='#95A5A6')
        
        # Posiciones de las balas en círculo
        self.balas_label = []
        center_x, center_y = 150, 150
        radius = 80
        for i in range(6):
            angle = i * (360/6) * (math.pi/180)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            bala = self.frame_tambor.create_image(x, y, 
                                                image=self.img_unknown)
            self.balas_label.append(bala)
        
        # Estado del juego
        self.estado = tk.Label(self.root,
                              text="¿Te atreves a jugar?",
                              font=("Arial", 14, "bold"),
                              fg='#ECF0F1',
                              bg='#2C3E50')
        self.estado.pack(pady=10)
        
        # Botón de disparo actualizado
        self.boton_disparar = tk.Button(self.root,
                                      text="DISPARAR",
                                      font=("Arial", 16, "bold"),
                                      fg='white',
                                      bg='#C0392B',
                                      activebackground='#E74C3C',
                                      padx=30,
                                      pady=15,
                                      relief=tk.RAISED,
                                      command=self.disparar)
        self.boton_disparar.pack()

    def animar_tambor(self):
        def rotar(angle=0, total_rotation=0):
            if total_rotation < 360:
                # Calcular nuevas posiciones
                center_x, center_y = 150, 150
                radius = 80
                
                for i, bala in enumerate(self.balas_label):
                    curr_angle = (i * 60 + total_rotation) * (math.pi/180)
                    x = center_x + radius * math.cos(curr_angle)
                    y = center_y + radius * math.sin(curr_angle)
                    self.frame_tambor.coords(bala, x, y)
                
                self.root.after(50, lambda: rotar(angle, total_rotation + 10))
        
        rotar()

    def nuevo_juego(self):
        self.tambor = [False] * 5 + [True]
        random.shuffle(self.tambor)
        self.disparos_restantes = 6
        self.estado.config(text=f"Disparos restantes: {self.disparos_restantes}")
        
        for bala in self.balas_label:
            self.frame_tambor.itemconfig(bala, image=self.img_unknown)
            
    def disparar(self):
        if self.modo_online and not self.turno:
            messagebox.showinfo("Espera", "No es tu turno")
            return
            
        self.animar_tambor()
        self.root.after(1000, self._procesar_disparo)
        
        if self.modo_online:
            self.enviar_disparo()
    
    def enviar_disparo(self):
        datos = {
            "tipo": "disparo",
            "resultado": self.tambor[-1],
            "nombre": self.nombre_jugador.get()
        }
        self.cliente.send(json.dumps(datos).encode())
        self.actualizar_turno(False)
    
    def procesar_disparo_remoto(self, datos):
        self.nombre_oponente = datos.get("nombre", "Oponente")
        self.label_oponente.config(text=self.nombre_oponente)
        self.actualizar_turno(True)
        
        disparo = datos["resultado"]
        self.disparos_restantes -= 1
        
        # Actualizar visualización
        self.frame_tambor.itemconfig(
            self.balas_label[self.disparos_restantes],
            image=self.img_bullet if disparo else self.img_empty
        )
        
        if disparo:
            self.estado.config(text="¡BANG! Cagaste wacho", fg='#E74C3C')
            self.root.after(2000, self.apagar_pc)
        else:
            self.estado.config(text=f"¡Click! Disparos restantes: {self.disparos_restantes}")
            
        if self.disparos_restantes == 0 and not disparo:
            messagebox.showinfo("¡Victoria!", "¡Has sobrevivido!")
            self.nuevo_juego()

    def _procesar_disparo(self):
        disparo = self.tambor.pop()
        self.disparos_restantes -= 1
        
        # Actualizar visualización
        self.frame_tambor.itemconfig(
            self.balas_label[self.disparos_restantes],
            image=self.img_bullet if disparo else self.img_empty
        )
        
        if disparo:
            self.estado.config(text="¡BANG! Cagaste wacho", fg='#E74C3C')
            self.root.after(2000, self.apagar_pc)
        else:
            self.estado.config(text=f"¡Click! Disparos restantes: {self.disparos_restantes}")
            
        if self.disparos_restantes == 0 and not disparo:
            messagebox.showinfo("¡Victoria!", "¡Has sobrevivido!")
            self.nuevo_juego()
            
    def actualizar_turno(self, es_mi_turno):
        self.turno = es_mi_turno
        self.turno_label.config(
            text="▶ Tu turno" if es_mi_turno else f"▶ Turno de {self.nombre_oponente}",
            fg='#2ECC71' if es_mi_turno else '#95A5A6'
        )
        
        # Actualizar indicadores de jugadores
        self.label_jugador.config(fg='#2ECC71' if es_mi_turno else '#95A5A6')
        self.label_oponente.config(fg='#2ECC71' if not es_mi_turno else '#95A5A6')
    
    def apagar_pc(self):
        os.system(r"C:\Windows\System32\shutdown.exe /s /t 5")
        self.root.destroy()
        
    def iniciar(self):
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()
    
    try:
        juego = RuletaRusa()
        juego.iniciar()
    except Exception as e:
        print(f"Error al iniciar el juego: {e}")
        sys.exit(1)
