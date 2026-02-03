import tkinter as tk
from tkinter import messagebox
import threading
import os
import random
import time
import math
from PIL import Image, ImageTk
from game_engine import RussianRoulette
from network_manager import NetworkManager

# --- Configuración ---
SHUTDOWN_ON_LOSS = True # Cambiar a False para no apagar la PC al perder.
# Paleta de Tema
COLOR_BG = "#1e1e2e"       
COLOR_PANEL = "#252538"    
COLOR_ACCENT = "#ff3c3c"   
COLOR_SAFE = "#00e5ff"     
COLOR_TEXT = "#cdd6f4"     
COLOR_MUTED = "#6c7086"    
FONT_HEADER = ("Segoe UI Black", 32)
FONT_MAIN = ("Segoe UI", 12)
FONT_ACTION = ("Segoe UI Black", 18)

class ModernButton(tk.Canvas):
    """Botón animado personalizado usando Canvas"""
    def __init__(self, parent, text, command, width=200, height=50, bg=COLOR_ACCENT, fg="white"):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        self.command = command
        self.text = text
        self.base_bg = bg
        self.hover_bg = self.adjust_brightness(bg, 1.2)
        self.fg = fg
        self.width = width
        self.height = height
        
        self.rect = self.create_rectangle(5, 5, width-5, height-5, fill=self.base_bg, outline="", width=0)
        self.text_id = self.create_text(width/2, height/2, text=text, fill=self.fg, font=FONT_ACTION)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.is_disabled = False

    def adjust_brightness(self, hex_color, factor):
        return "#ff6b6b" if self.base_bg == COLOR_ACCENT else "#33ffcc"

    def on_enter(self, e):
        if not self.is_disabled:
            self.itemconfig(self.rect, fill=self.hover_bg)
            self.config(cursor="hand2")

    def on_leave(self, e):
        if not self.is_disabled:
            self.itemconfig(self.rect, fill=self.base_bg)
            self.config(cursor="")

    def on_click(self, e):
        if not self.is_disabled and self.command:
            self.command()

    def set_state(self, state):
        if state == "disabled":
            self.is_disabled = True
            self.itemconfig(self.rect, fill=COLOR_MUTED)
            self.config(cursor="arrow")
        else:
            self.is_disabled = False
            self.itemconfig(self.rect, fill=self.base_bg)

class CylinderVisual:
    """Maneja la representación visual del cilindro del revólver"""
    def __init__(self, canvas, center_x, center_y, radius=100, assets=None):
        self.canvas = canvas
        self.cx = center_x
        self.cy = center_y
        self.radius = radius
        self.assets = assets
        self.angle_offset = 0
        self.slots = [0] * 6 # 0: Desconocido, 1: Vacío, 2: Bala
        self.item_ids = []
        self.images = [] # Mantener referencias

        self.draw()

    def draw(self, rotation_angle=0):
        self.canvas.delete("cylinder_item")
        self.images = [] # Limpiar referencias
        
        # Dibujar Eje (Centro)
        r = 40
        self.canvas.create_oval(self.cx-r, self.cy-r, self.cx+r, self.cy+r, fill="#444", outline="#222", width=2, tags="cylinder_item")
        
        # Dibujar 6 Recámaras
        for i in range(6):
            # Calcular ángulo
            angle_deg = (i * 60) + rotation_angle
            angle_rad = math.radians(angle_deg)
            
            x = self.cx + self.radius * math.cos(angle_rad)
            y = self.cy + self.radius * math.sin(angle_rad)
            
            # Determinar Imagen
            slot_type = self.slots[i]
            img_key = "unknown"
            if slot_type == 1: img_key = "empty"
            elif slot_type == 2: img_key = "bullet"
            
            base_img = self.assets.get(img_key)
            if base_img:
                # Rotar imagen para mirar al centro
                pil_img = base_img.resize((60, 60))
                
                tk_img = ImageTk.PhotoImage(pil_img)
                self.images.append(tk_img)
                self.canvas.create_image(x, y, image=tk_img, tags="cylinder_item")
            else:
                 # Placeholder de debug si falta imagen
                 self.canvas.create_oval(x-20, y-20, x+20, y+20, fill="red", outline="yellow", tags="cylinder_item")

    def update_slot(self, index, status):
        # status: 0=Desconocido, 1=Vacío, 2=Bala
        self.slots[index] = status
        self.draw(self.angle_offset)

    def spin(self, speed=20):
        # Solo actualiza el offset del ángulo
        self.angle_offset = (self.angle_offset + speed) % 360
        self.draw(self.angle_offset)

class RussianRouletteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RULETA RUSA LAN [v2.0]")
        self.geometry("900x700")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        
        try:
            self.iconbitmap("revolver.ico")
        except:
            pass

        # Assets (Usando Pillow)
        self.pil_assets = {}
        self.load_assets()

        # Estado
        self.network = NetworkManager()
        self.game = None
        self.is_my_turn = False
        self.running = True
        
        # UI
        self.main_container = tk.Frame(self, bg=COLOR_BG)
        self.main_container.pack(fill="both", expand=True)
        
        self.show_main_menu()
        
        # Hilos
        self.listen_thread = threading.Thread(target=self.network_loop, daemon=True)
        self.listen_thread.start()

    def load_assets(self):
        # Resolver rutas relativas al directorio de ejecución
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        files = {
            "unknown": "bullet_unknown.png", 
            "empty": "bullet_empty.png", 
            "bullet": "bullet.png"
        }
        for key, filename in files.items():
            abs_path = os.path.join(base_dir, filename)
            try:
                if os.path.exists(abs_path):
                    self.pil_assets[key] = Image.open(abs_path).convert("RGBA")
                else:
                    print(f"ERROR: Archivo no encontrado: {abs_path}")
            except Exception as e:
                print(f"Error cargando asset {key}: {e}")

    # --- ESCENAS UI ---
    def show_main_menu(self):
        self.clear_ui()
        
        tk.Label(self.main_container, text="R U L E T A  //  R U S A", font=("Segoe UI Black", 40), bg=COLOR_BG, fg=COLOR_ACCENT).pack(pady=(60, 10))
        tk.Label(self.main_container, text="L A N   V E R S I O N   v 2.0", font=("Segoe UI", 14, "bold"), bg=COLOR_BG, fg=COLOR_MUTED).pack(pady=(0, 40))
        
        f_actions = tk.Frame(self.main_container, bg=COLOR_BG)
        f_actions.pack()

        # Host
        ModernButton(f_actions, "HOSTEAR", self.start_hosting, width=200, height=50, bg=COLOR_SAFE).pack(pady=10)
        
        # Join
        f_join = tk.Frame(f_actions, bg=COLOR_BG)
        f_join.pack(pady=10)
        self.entry_ip = tk.Entry(f_join, font=("Consolas", 12), bg="#111", fg="white", insertbackground="white", justify="center", width=20)
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(pady=5)
        ModernButton(f_join, "CONECTAR", self.join_game, width=200, height=50, bg=COLOR_SAFE).pack(pady=5)
        
        self.lbl_status = tk.Label(self.main_container, text="Esperando...", font=("Consolas", 10), bg=COLOR_BG, fg=COLOR_MUTED)
        self.lbl_status.place(relx=0.5, rely=0.95, anchor="center")

    def show_game_ui(self):
        self.clear_ui()
        
        # Barra Superior
        top_bar = tk.Frame(self.main_container, bg=COLOR_PANEL, height=60)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="PARTIDA EN CURSO", font=("Segoe UI", 10, "bold"), bg=COLOR_PANEL, fg=COLOR_MUTED).pack(side="left", padx=20)
        
        # Arena
        arena = tk.Canvas(self.main_container, bg=COLOR_BG, highlightthickness=0)
        arena.pack(fill="both", expand=True)
        self.arena_canvas = arena
        
        self.cx, self.cy = 450, 300
        
        # Visuales
        self.cylinder_visual = CylinderVisual(arena, self.cx, self.cy, radius=120, assets=self.pil_assets)
        
        # Martillo / Indicador
        arena.create_rectangle(self.cx-5, self.cy-160, self.cx+5, self.cy-130, fill="#555", outline="#333", tags="ui_static")
        
        # Etiquetas
        self.lbl_turn_header = tk.Label(self.main_container, text="ESPERANDO...", font=("Segoe UI Black", 36), bg=COLOR_BG, fg=COLOR_MUTED)
        self.lbl_turn_header.place(relx=0.5, rely=0.15, anchor="center")
        
        # Acciones
        self.btn_trigger = ModernButton(self.main_container, "JALAR GATILLO", self.trigger_sequence, width=250, height=60, bg=COLOR_ACCENT)
        self.btn_trigger_id = arena.create_window(self.cx, self.cy + 250, window=self.btn_trigger)
        self.btn_trigger.set_state("disabled")
        
        self.update_ui_state()

    def clear_ui(self):
        for w in self.main_container.winfo_children():
            w.destroy()

    # --- ACCIONES Y ANIMACIONES ---
    def trigger_sequence(self):
        # Deshabilitar input
        self.is_my_turn = False
        self.btn_trigger.set_state("disabled")
        self.lbl_turn_header.config(text="GIRANDO...", fg=COLOR_SAFE)
        
        # Enviar señal de giro al oponente
        self.network.send({"type": "SPINNING"})
        
        # Iniciar animación local
        self.animate_spin_start()

    def animate_spin_start(self):
        # Giro más lento
        self.spin_speed = 40 # Grados por paso
        self.is_spinning = True
        self.spin_step()
        
        # Programar parada
        self.after(2000, self.resolve_shot)

    def spin_step(self):
        if self.is_spinning:
            self.cylinder_visual.spin(self.spin_speed)
            # Intervalo más lento (40ms)
            self.after(40, self.spin_step)

    def resolve_shot(self):
        self.is_spinning = False
        
        result = self.game.pull_trigger()
        
        # Obtener slot visual aleatorio
        logic_turn = self.game.current_chamber - 1
        # Proteger envoltorio
        slot_idx = self.visual_slots[logic_turn % 6]
        
        # Calcular rotación
        target_angle = -90 - (slot_idx * 60)
        self.cylinder_visual.draw(target_angle)
        
        # Networking
        self.network.send({"type": "MOVE", "result": result})
        
        # Revelar
        if result == "BANG":
            # Mostrar Bala
            self.cylinder_visual.update_slot(slot_idx, 2) # 2=Bala
            self.show_defeat()
        else:
            # Mostrar Vacío
            self.cylinder_visual.update_slot(slot_idx, 1) # 1=Vacío
            self.flash_feedback()
            self.lbl_turn_header.config(text="CLICK", fg=COLOR_SAFE)
            self.after(2000, self.update_to_opponent_wait) 

    def flash_feedback(self):
        # Flash blanco rápido en canvas
        rect_id = self.arena_canvas.create_rectangle(0, 0, 900, 700, fill="white", stipple="gray50")
        self.after(50, lambda: self.arena_canvas.delete(rect_id))

    def update_to_opponent_wait(self):
        self.update_ui_state()

    # --- Animación Oponente ---
    def on_opponent_spin(self):
        self.lbl_turn_header.config(text="OPONENTE GIRANDO...", fg=COLOR_MUTED)
        self.is_spinning = True
        self.spin_speed = 40
        self.spin_step()

    def on_opponent_move(self, result):
        self.is_spinning = False
        
        # Lógica de sincronización
        self.game.current_chamber += 1
        
        logic_turn = self.game.current_chamber - 1
        slot_idx = self.visual_slots[logic_turn % 6]
        
        # Ajustar y revelar
        target_angle = -90 - (slot_idx * 60)
        self.cylinder_visual.draw(target_angle)
        
        if result == "BANG":
            self.cylinder_visual.update_slot(slot_idx, 2)
            self.game.game_over = True
            self.show_victory()
        else:
            self.cylinder_visual.update_slot(slot_idx, 1)
            self.is_my_turn = True
            self.update_ui_state()

    # --- Networking Estándar ---
    def start_hosting(self):
        self.lbl_status.config(text="Iniciando...", fg=COLOR_SAFE)
        threading.Thread(target=self._host_thread, daemon=True).start()

    def _host_thread(self):
        if self.network.host_game():
            self.player_role = "HOST"
            self.start_game_setup()
        else:
            self.lbl_status.config(text="Error de puerto", fg=COLOR_ACCENT)

    def join_game(self):
        ip = self.entry_ip.get()
        self.lbl_status.config(text="Conectando...", fg=COLOR_SAFE)
        if self.network.join_game(ip):
            self.player_role = "CLIENT"
            self.after(0, self.show_game_ui)
        else:
            self.lbl_status.config(text="Error de conexión", fg=COLOR_ACCENT)

    def start_game_setup(self):
        bullet = random.randint(0, 5)
        starter = random.choice(["HOST", "CLIENT"])
        
        # Generar slots mezclados para sincronización
        slots_order = list(range(6))
        random.shuffle(slots_order)
        
        self.network.send({
            "type": "START", 
            "bullet": bullet, 
            "starter": starter,
            "slots": slots_order
        })
        self.initialize_game(bullet, starter, slots_order)

    def initialize_game(self, bullet, starter, slots_order=None):
        self.game = RussianRoulette(bullet)
        self.is_my_turn = (starter == self.player_role)
        
        if slots_order:
            self.visual_slots = slots_order
        else:
            # Fallback
            self.visual_slots = list(range(6)) 
            
        self.after(0, self.show_game_ui)

    def network_loop(self):
        while self.running:
            if self.network.connected:
                data = self.network.receive()
                if data:
                    self.after(0, lambda d=data: self.handle_data(d))
            time.sleep(0.1)

    def handle_data(self, data):
        t = data.get("type")
        if t == "START":
            self.initialize_game(data.get("bullet"), data.get("starter"), data.get("slots"))
        elif t == "SPINNING":
            self.on_opponent_spin()
        elif t == "MOVE":
            self.on_opponent_move(data.get("result"))

    def update_ui_state(self):
        if not self.game: return
        
        if self.is_my_turn:
            self.lbl_turn_header.config(text="TU TURNO", fg=COLOR_ACCENT)
            self.btn_trigger.set_state("normal")
        else:
            self.lbl_turn_header.config(text="TURNO OPONENTE", fg=COLOR_MUTED)
            self.btn_trigger.set_state("disabled")

    def show_defeat(self):
        self.main_container.config(bg="red")
        self.lbl_turn_header.config(text="M U E R T O", bg="red", fg="black")
        messagebox.showerror("F", "Has muerto.")
        if SHUTDOWN_ON_LOSS: os.system("shutdown /s /t 5")

    def show_victory(self):
        self.main_container.config(bg=COLOR_SAFE)
        self.lbl_turn_header.config(text="V I C T O R I A", bg=COLOR_SAFE, fg="black")
        messagebox.showinfo("GG", "Sobreviviste.")

if __name__ == "__main__":
    app = RussianRouletteApp()
    app.mainloop()
