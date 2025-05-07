import subprocess
import sys
import os
import random
import time
import ctypes
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
            # Launch server process
            servidor_path = resource_path("servidor_ruleta.py")
            if getattr(sys, 'frozen', False):
                # If running as executable
                subprocess.Popen(['python', servidor_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # If running from source
                python_exe = sys.executable
                subprocess.Popen([python_exe, servidor_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Show waiting message
            messagebox.showinfo("Servidor", "Iniciando servidor...")
                    
            # Connect after delay
            self.root.after(2000, lambda: self.conectar_como_host())
            
            # Initialize game UI
            self.menu_frame.destroy()
            self.setup_ui()
            self.nuevo_juego()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el servidor: {str(e)}")

    def conectar_como_host(self):
        self.modo_online = True
        self.turno = random.choice([True, False])  # Turno aleatorio inicial
        self.conectar_a_servidor()

    def unirse_partida(self):
        self.modo_online = True
        self.turno = random.choice([True, False])  # Turno aleatorio inicial
        if self.conectar_a_servidor():
            self.menu_frame.destroy()
            self.setup_ui()
            self.nuevo_juego()
    
    def conectar_a_servidor(self):
        try:
            self.cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.cliente.settimeout(15)
            
            ip = self.ip_servidor.get()
            puerto = self.puerto.get()
            
            self.cliente.connect((ip, puerto))
            
            datos_iniciales = {
                "tipo": "conexion",
                "nombre": self.nombre_jugador.get()
            }
            mensaje = json.dumps(datos_iniciales).encode()
            self.cliente.send(mensaje)
            
            thread = threading.Thread(target=self.recibir_datos)
            thread.daemon = True
            thread.start()
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Error de conexión: {e}")
            if hasattr(self, 'cliente'):
                self.cliente.close()
            return False

    def iniciar_modo_local(self):
        self.menu_frame.destroy()
        self.setup_ui()
        self.nuevo_juego()
        
    def recibir_datos(self):
        while True:
            try:
                data = self.cliente.recv(1024)
                if not data:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Conexión perdida"))
                    break
                
                datos = json.loads(data.decode())
                print(f"Datos recibidos: {datos}")
                
                if datos["tipo"] == "conexion":
                    self.nombre_oponente = datos["nombre"]
                    self.root.after(0, lambda: self.label_oponente.config(text=self.nombre_oponente))
                    
                elif datos["tipo"] == "disparo":
                    # Procesamos el disparo en el hilo principal
                    self.root.after(0, lambda d=datos: self.procesar_disparo_remoto(d))
                    
            except socket.timeout:
                # Ignoramos los timeouts
                continue
            except Exception as e:
                print(f"Error en recibir_datos: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error de conexión: {e}"))
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
            
        if self.modo_online:
            # Primero enviamos el disparo
            if not self.enviar_disparo():
                return
        
        # Luego animamos y procesamos
        self.animar_tambor()
        self.root.after(1000, self._procesar_disparo)
    
    def enviar_disparo(self):
        try:
            if not self.cliente:
                print("No hay conexión con el servidor")
                return False
                
            datos = {
                "tipo": "disparo",
                "resultado": self.tambor[-1],
                "nombre": self.nombre_jugador.get()
            }
            
            # Enviamos directamente sin prueba de conexión
            mensaje = json.dumps(datos).encode()
            self.cliente.send(mensaje)
            print(f"Disparo enviado: {datos}")
            self.actualizar_turno(False)
            return True
            
        except Exception as e:
            print(f"Error al enviar disparo: {e}")
            messagebox.showerror("Error", "Se perdió la conexión con el servidor")
            self.cliente.close()
            return False

    def procesar_disparo_remoto(self, datos):
        try:
            print(f"Procesando disparo remoto: {datos}")  # Debug
            
            self.nombre_oponente = datos.get("nombre", "Oponente")
            self.label_oponente.config(text=self.nombre_oponente)
            
            disparo = datos["resultado"]
            self.disparos_restantes -= 1
            
            # Animar el tambor
            self.animar_tambor()
            
            def actualizar_ui():
                # Actualizar visualización
                self.frame_tambor.itemconfig(
                    self.balas_label[self.disparos_restantes],
                    image=self.img_bullet if disparo else self.img_empty
                )
                
                if disparo:
                    self.estado.config(text=f"¡BANG! Has muerto!", fg='#E74C3C')
                    messagebox.showinfo("¡Cagaste wacho!", "¡te moriste!")
                    self.root.after(2000, self.apagar_pc)  # Solo apaga la PC del que recibe el disparo
                else:
                    self.estado.config(text=f"¡Click! Disparos restantes: {self.disparos_restantes}")
                    self.actualizar_turno(True)
                    
            # Ejecutar actualización UI después de la animación
            self.root.after(1000, actualizar_ui)
            
        except Exception as e:
            print(f"Error procesando disparo remoto: {e}")

    def _procesar_disparo(self):
        disparo = self.tambor.pop()
        self.disparos_restantes -= 1
        
        # Actualizar visualización
        self.frame_tambor.itemconfig(
            self.balas_label[self.disparos_restantes],
            image=self.img_bullet if disparo else self.img_empty
        )
        
        if disparo:
            self.estado.config(text=f"¡BANG! {self.nombre_oponente} a muerto!", fg='#E74C3C')
            # No apagamos la PC aquí, solo mostramos el mensaje
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
            if not os.path.exists(resource_path("bullet_empty.png")) or \
               not os.path.exists(resource_path("bullet.png")) or \
               not os.path.exists(resource_path("bullet_unknown.png")):
                messagebox.showerror("Error", "No se encontraron las imágenes necesarias")
                return
            self.root.mainloop()
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            messagebox.showerror("Error", f"Error inesperado: {e}")
            self.root.destroy()

if __name__ == "__main__":
    try:
        app = RuletaRusa()
        app.iniciar()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        messagebox.showerror("Error Fatal", f"No se pudo iniciar la aplicación: {e}")
