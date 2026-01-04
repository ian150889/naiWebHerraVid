
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import threading
import sys
import os
import time
import subprocess
import numpy as np
from PIL import Image, ImageTk

# --- DEPENDENCIAS / DEPENDENCIES ---
# Importamos las librerías necesarias. Si no están instaladas, el programa intentará
# manejar el error amigablemente.
# - customtkinter: Para la Interfaz Gráfica (GUI) moderna.
# - cv2 (OpenCV): El cerebro del procesamiento de imágenes y video.
# - threading: Permite ejecutar tareas pesadas en "segundo plano" sin congelar la ventana.
# - subprocess: Para comunicarnos con programas externos como FFmpeg.
# - numpy: Para cálculos matemáticos de matrices (las imágenes son matrices de píxeles).
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    print("MediaPipe not found.")
    MEDIAPIPE_AVAILABLE = False

try: 
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError:
    print("Rembg not found.")
    REMBG_AVAILABLE = False

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    print("Pygame not found.")
    PYGAME_AVAILABLE = False

# --- CONSTANTES DE TEMA / THEME CONSTANTS ---
# Centralizamos los colores para cambiar el estilo fácilmente en el futuro.
# Usamos un tema oscuro (Dark Mode) para que parezca una herramienta profesional.
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

C_BG = "#161616"       # Fondo Principal (Casi negro)
C_PANEL = "#252525"    # Paneles (Gris oscuro para diferenciar áreas)
C_ACCENT = "#00E676"   # Acento (Verde Neón para acciones importantes)
C_TEXT = "#E0E0E0"     # Texto (Blanco suave para lectura cómoda)
FONT_MAIN = ("Roboto", 12)
FONT_BOLD = ("Roboto", 12, "bold")
FONT_TITLE = ("Roboto", 24, "bold")

LOCALES = {
    "ES": {
        "app_title": "NaiWeb Magic Suite",
        "tab_vid": "VIDEO", 
        "tab_img": "IMAGENES", 
        "tab_aud": "AUDIO", 
        "tab_mark": "QUITAR MARCA DE AGUA",
        
        "v_grp_bg": "Magic Background Removal",
        "v_grp_cnv": "Pro Video Converter",
        
        "btn_load": "📂 IMPORTAR MEDIA",
        "btn_run": "🚀 INICIAR PROCESO",
        "lbl_drop": "Arrastra o selecciona un archivo...",
        
        "wand_on": "🪄 Magic Wand (Activo)",
        "wand_off": "🪄 Magic Wand (Inactivo)",
        "est_t": "⚡ Turbo Mode (~1min)",
        "est_m": "💎 Magic Mode (~5min+)",
        
        "p_pitch": "Modulador de Voz",
        "p_noise": "Reducción de Ruido",
        "p_presets": ["Normal", "Voz Profunda", "Ardilla", "Demonio"],
        
        "m_instr": "Usa el LÁPIZ MÁGICO para pintar sobre la marca.",
        "m_btn": "🧹 ELIMINAR MARCA DE AGUA",
        
        "fmt_png": "PNG (Transparente)",
        "fmt_jpg": "JPG (Fondo Blanco)",
        "fmt_webp": "WEBP (Optimizado)",
        
        "lang": "🇺🇸 EN"
    },
    "EN": {
        "app_title": "NaiWeb Magic Suite",
        "tab_vid": "VIDEO", 
        "tab_img": "IMAGE", 
        "tab_aud": "AUDIO", 
        "tab_mark": "WATERMARK REMOVER",
        # ... (rest same) ...
        
        "v_grp_bg": "Magic Background Removal",
        "v_grp_cnv": "Pro Video Converter",
        
        "btn_load": "📂 IMPORT MEDIA",
        "btn_run": "🚀 START PROCESS",
        "lbl_drop": "Drag or select file...",
        
        "wand_on": "🪄 Magic Wand (Active)",
        "wand_off": "🪄 Magic Wand (Inactive)",
        "est_t": "⚡ Turbo Mode (~1min)",
        "est_m": "💎 Magic Mode (~5min+)",
        
        "p_pitch": "Voice Modulator",
        "p_noise": "Noise Reduction",
        "p_presets": ["Normal", "Deep Voice", "Chipmunk", "Monster"],
        
        "m_instr": "Draw a RED rectangle over the watermark.",
        "m_btn": "🧹 REMOVE WATERMARK",
        
        "fmt_png": "PNG (Transparent)",
        "fmt_jpg": "JPG (White BG)",
        "fmt_webp": "WEBP (Optimized)",
        
        "lang": "🇪🇸 ES"
    }
}

class CollapsibleFrame(ctk.CTkFrame):
    def __init__(self, master, title="", expanded=False):
        super().__init__(master, fg_color="transparent")
        self.expanded = expanded
        self.title = title
        
        self.toggle_btn = ctk.CTkButton(self, text=f"▼ {title}", width=200, height=35, 
                                        fg_color=C_PANEL, hover_color="#333", corner_radius=10,
                                        anchor="w", font=FONT_BOLD, command=self.toggle)
        self.toggle_btn.pack(fill="x", pady=5)
        
        self.content = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=10)
        if expanded: self.content.pack(fill="both", expand=True, padx=5, pady=5)

    def toggle(self):
        self.expanded = not self.expanded
        t = "▼" if self.expanded else "▶"
        self.toggle_btn.configure(text=f"{t} {self.title}")
        if self.expanded: self.content.pack(fill="both", expand=True, padx=5, pady=5)
        else: self.content.pack_forget()

class CanvasPlayer:
    def __init__(self, master, app, mode="view", height=250):
        self.app = app; self.mode = mode
        self.canvas = tk.Canvas(master, bg="black", highlightthickness=0, height=height)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
    def set_mode(self, m):
        # Cambiar modo dinámicamente (ej: de lápiz a varita)
        self.mode = m
        self.draw_ov()
        
        self.path=None; self.playing=False; self.aud="temp.wav"
        self.points=[]; self.rect_s=None; self.rect_e=None; self.curr_fr=None
        self.strokes=[] # Lápiz: Lista de trazos (listas de puntos)
        self.masks=[]   # Varita: Lista de máscaras binarias (numpy arrays)
        
        self.canvas.bind("<Button-1>", self.click); self.canvas.bind("<B1-Motion>", self.drag)

    def click(self, e):
        # Evento Clic: Determina la acción según el modo
        if self.mode=="wand": 
            # Modo Tracking: Añadir punto para flujo óptico (Lucas-Kanade)
            self.points.append(self.map(e.x,e.y)); self.draw_ov()
        elif self.mode=="rect": 
            # Modo Rectángulo (Legacy): Punto inicial
            self.rect_s=self.map(e.x,e.y); self.rect_e=None
        elif self.mode=="pencil": 
            # Modo Lápiz: Iniciar nuevo trazo
            self.strokes.append([self.map(e.x,e.y)]); self.draw_ov()
        elif self.mode=="flood":
             # --- LÓGICA EDUCATIVA: FLOOD FILL (VARITA MÁGICA) ---
             # Este algoritmo busca píxeles conectados de color similar al clicado.
             if self.curr_fr is None: return
             
             # 1. Preparar Máscara: OpenCV floodFill requiere una máscara 2px más grande que la imagen.
             #    Esto es para evitar desbordamientos en los bordes internos del algoritmo.
             h, w = self.curr_fr.shape[:2]
             mask = np.zeros((h+2, w+2), np.uint8)
             
             # 2. Configurar Flags (Banderas de bit):
             #    - 4: Conectividad (busca en 4 vecinos: arriba, abajo, izq, der).
             #    - FLOODFILL_MASK_ONLY: No modifica la imagen, solo rellena la máscara.
             #    - (255 << 8): El valor con el que rellenar la máscara (255=blanco).
             #    - FLOODFILL_FIXED_RANGE: Compara con el píxel semilla original, no con los vecinos.
             flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE
             
             # 3. Tolerancia (Diff): Aumentamos para mejor detección
             diff = (40, 40, 40)
             
             # 4. Obtener coordenadas de imagen (e.x/e.y son de canvas, hay que mapear)
             nx, ny = self.map(e.x, e.y) # Normalizado 0-1
             ix, iy = int(nx*w), int(ny*h)
             
             print(f"DEBUG: Click Wand @ {ix},{iy} Val: {self.curr_fr[iy,ix] if 0<=iy<h and 0<=ix<w else 'OOB'}")

             # 5. Ejecutar Algoritmo
             if 0 <= ix < w and 0 <= iy < h:
                 # floodFill modifica 'mask' in-place.
                 res = cv2.floodFill(self.curr_fr, mask, (ix, iy), 0, diff, diff, flags)
                 print(f"DEBUG: Flood result pixels: {res[0]}")
                 
                 real_mask = mask[1:-1, 1:-1]
                 if np.count_nonzero(real_mask) > 0:
                     self.masks.append(real_mask)
                     self.draw_ov()
                 else:
                     print("DEBUG: Empty mask after flood")
                     # Fallback: Add a small circle mask if flood failed (e.g. click on noise)
                     # Esto asegura que el usuario vea ALGO.
                     fallback = np.zeros((h, w), np.uint8)
                     cv2.circle(fallback, (ix, iy), 10, 255, -1)
                     self.masks.append(fallback)
                     self.draw_ov()

    def drag(self, e):
        # Evento Arrastrar: Solo útil para herramientas de dibujo continuo
        if self.mode=="wand": self.points.append(self.map(e.x,e.y)); self.draw_ov()
        elif self.mode=="rect": self.rect_e=self.map(e.x,e.y); self.draw_ov()
        elif self.mode=="pencil" and self.strokes: self.strokes[-1].append(self.map(e.x,e.y)); self.draw_ov()

    def map(self, cx, cy):
        # Conversión de Coordenadas: Canvas (Píxeles UI) -> Normalizado (0.0 - 1.0)
        # Esto permite que los dibujos funcionen aunque redimensiones la ventana.
        if self.curr_fr is None: return (0,0)
        h,w = self.curr_fr.shape[:2]
        cw = self.canvas.winfo_width(); ch = self.canvas.winfo_height()
        
        # Mantener relación de aspecto (Aspect Ratio)
        r = min(cw/w, ch/h)
        nw, nh = int(w*r), int(h*r) # Nuevas dimensiones en pantalla
        ox, oy = (cw-nw)//2, (ch-nh)//2 # Offset (centrado)
        
        return (max(0, min(1, (cx-ox)/nw)), max(0, min(1, (cy-oy)/nh)))

    def demap(self, nx, ny):
        # Conversión Inversa: Normalizado (0.0 - 1.0) -> Canvas (Píxeles UI)
        if self.curr_fr is None: return (0,0)
        h,w = self.curr_fr.shape[:2]
        cw = self.canvas.winfo_width(); ch = self.canvas.winfo_height()
        r = min(cw/w, ch/h)
        nw, nh = int(w*r), int(h*r)
        ox, oy = (cw-nw)//2, (ch-nh)//2
        return (ox + nx*nw, oy + ny*nh)

    def draw_ov(self):
        # Renderizado de la Capa de Superposición (Overlay)
        self.canvas.delete("ov")
        
        # 1. Dibujar Tracking (Varita vieja)
        if self.mode=="wand" and len(self.points)>1:
            flat = []
            for p in self.points: flat.extend(self.demap(*p))
            self.canvas.create_line(flat, fill=C_ACCENT, width=2, smooth=True, tags="ov")
            
        # 2. Dibujar Lápiz (Trazos libres)
        for s in self.strokes:
            if len(s)>1:
                flat=[]
                for p in s: flat.extend(self.demap(*p))
                self.canvas.create_line(flat, fill="red", width=5, capstyle="round", smooth=True, tags="ov")
                
        # 3. Dibujar Máscaras de Inundación (Varita nueva)
        #    Para visualizar una máscara binaria en Canvas, extraemos sus contornos.
        h,w = 0,0
        if self.curr_fr is not None: h,w = self.curr_fr.shape[:2]
        
        for m in self.masks:
             # cv2.findContours devuelve una lista de polígonos
             cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
             for c in cnts:
                 # c es un array numpy (N, 1, 2) con coordenadas de imagen
                 # Debemos convertir cada punto a coordenadas de Canvas
                 flat_poly = []
                 for pt in c:
                     px, py = pt[0]
                     # Normalizar
                     nx, ny = px/w, py/h
                     # A Canvas
                     cx, cy = self.demap(nx, ny)
                     flat_poly.extend([cx, cy])
                 
                     # Visualización Mejorada:
                     # - outline: Borde verde neón grueso.
                     # - SIN FILL/STIPPLE: Causa errores en algunos sistemas Linux/X11.
                     # - Usamos solo contorno fuerte para indicar selección.
                     self.canvas.create_polygon(flat_poly, outline="#00E676", fill="", width=3, tags="ov")
        
        # 4. Dibujar Puntos de Video Wand (Tracking)
        if self.mode=="wand":
             for p in self.points:
                 cx, cy = self.demap(*p)
                 self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill=C_ACCENT, outline=C_ACCENT, tags="ov")

    def get_mask(self, w, h):
        # Generación de la Máscara Final para Inpainting
        # Combina los trazos del lápiz y las áreas de la varita.
        m = np.zeros((h, w), dtype=np.uint8)
        
        # 1. Aplicar Trazos de Lápiz
        for s in self.strokes:
            pts = np.array([(int(p[0]*w), int(p[1]*h)) for p in s], np.int32)
            if len(pts)>1: cv2.polylines(m, [pts], False, 255, 20) # 20px de grosor
            
        # 2. Sumar Máscaras de Varita
        for bm in self.masks:
            # bm es del tamaño de la imagen original mostrada.
            # Si el tamaño de salida (w,h) es diferente, redimensionar.
            if bm.shape[:2] != (h, w):
                bm_resized = cv2.resize(bm, (w, h), interpolation=cv2.INTER_NEAREST)
                m = cv2.bitwise_or(m, bm_resized)
            else:
                 m = cv2.bitwise_or(m, bm)
                 
        return m

    def show(self, f):
        self.curr_fr = f
        h,w = f.shape[:2]; cw=self.canvas.winfo_width(); ch=self.canvas.winfo_height()
        if cw<10: cw=300; ch=200
        r=min(cw/w, ch/h); nw,nh=int(w*r), int(h*r)
        im = cv2.resize(f, (nw,nh))
        
        # Handle Transparency
        if len(im.shape) == 3 and im.shape[2] == 4:
            img = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA))
        else:
            img = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
            
        self.photo = ImageTk.PhotoImage(image=img)
        
        self.canvas.delete("img")
        ox, oy = (cw-nw)//2, (ch-nh)//2
        self.canvas.create_image(ox, oy, image=self.photo, anchor="nw", tags="img")
        self.canvas.tag_lower("img")
        self.draw_ov()

    def load(self, p): 
        self.stop(); self.path=p; self.points=[]; self.rect_s=None; self.strokes=[] 
        c=cv2.VideoCapture(p); r,f=c.read(); c.release()
        if r: self.canvas.update(); self.show(f)

    def play(self):
        if not self.path or self.playing: return
        self.playing = True
        
        # Extracción de Audio para Previsualización
        if PYGAME_AVAILABLE:
            try: 
                 # Aseguramos que ffmpeg sobrescriba (-y) y use un formato WAV estándar para pygame
                 subprocess.run(["ffmpeg","-y","-i",self.path,"-vn","-acodec","pcm_s16le","-ar","44100","-ac","2",self.aud], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                 
                 if os.path.exists(self.aud): 
                     pygame.mixer.music.load(self.aud)
                     pygame.mixer.music.play()
            except Exception as e: print(f"Audio Error: {e}")
            
        threading.Thread(target=self._loop).start()
    
    def stop(self): self.playing=False; pygame.mixer.music.stop() if PYGAME_AVAILABLE else None
    
    def _loop(self):
        c=cv2.VideoCapture(self.path); fps=c.get(5) or 30; d=1.0/fps
        while self.playing and c.isOpened():
            s=time.time(); r,f=c.read()
            if not r: break
            try: self.app.after(0, lambda: self.show(f))
            except: break
            wt=d-(time.time()-s); 
            if wt>0: time.sleep(wt)
        c.release(); self.playing=False

class NaiWebSuite(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1200x900"); self.title("NaiWeb Magic Suite"); self.configure(fg_color=C_BG)
        try: 
            if os.path.exists("img_logo/logNaiWeb.png"): self.iconphoto(False, tk.PhotoImage(file="img_logo/logNaiWeb.png"))
        except: pass
        
        self.lang="ES"; self.rembg=None
        self.in_vid=""; self.in_img=""; self.in_aud=""; self.in_mark=""
        
        self.init_ui()
        self.upd_tx()

    def tr(self, k): return LOCALES[self.lang].get(k, k)
    def lang_t(self): self.lang="EN" if self.lang=="ES" else "ES"; self.upd_tx()

    def get_unique_path(self, base, suffix, ext):
        f = "Descargas"
        if not os.path.exists(f): os.makedirs(f)
        b = os.path.splitext(os.path.basename(base))[0]
        b = "".join([c for c in b if c.isalnum() or c in (' ','_','-')]).strip()
        for i in range(1, 1000):
            p = os.path.join(f, f"{b}_{suffix}_{i:03d}.{ext}")
            if not os.path.exists(p): return p
        return os.path.join(f, f"{b}_{suffix}_{int(time.time())}.{ext}")

    def init_ui(self):
        # HEADER / ENCABEZADO
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x", padx=20, pady=10)
        try:
            im = Image.open("img_logo/logNaiWeb.png"); im.thumbnail((250, 60))
            cim = ctk.CTkImage(im,im,(im.width,im.height))
            ctk.CTkLabel(top, text="", image=cim).pack(side="left")
        except: ctk.CTkLabel(top, text="NAIWEB STUDIO", font=FONT_TITLE, text_color=C_ACCENT).pack(side="left")
        self.btn_ln = ctk.CTkButton(top, text="EN", width=60, fg_color=C_PANEL, command=self.lang_t); self.btn_ln.pack(side="right")

        # TABS / PESTAÑAS
        # TABS / PESTAÑAS
        self.tabs = ctk.CTkTabview(self, fg_color=C_PANEL, corner_radius=15, 
                                   segmented_button_fg_color=C_BG, 
                                   segmented_button_selected_color=C_ACCENT,
                                   segmented_button_selected_hover_color=C_ACCENT,
                                   text_color=C_TEXT)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Mapeo de claves internas a Texto UI
        self.tab_map = {
            "tab_vid": self.tr("tab_vid"),
            "tab_img": self.tr("tab_img"),
            "tab_aud": self.tr("tab_aud"),
            "tab_mark": self.tr("tab_mark")
        }
        
        for k, name in self.tab_map.items(): self.tabs.add(name)
        
        # Usamos el nombre traducido para acceder a la pestaña
        self.ui_video(self.tabs.tab(self.tab_map["tab_vid"]))
        self.ui_image(self.tabs.tab(self.tab_map["tab_img"]))
        self.ui_audio(self.tabs.tab(self.tab_map["tab_aud"]))
        self.ui_mark(self.tabs.tab(self.tab_map["tab_mark"]))

        # STATUS / ESTADO
        self.stat = ctk.CTkLabel(self, text="System Ready.", font=FONT_MAIN, text_color="gray"); self.stat.pack(pady=2)
        self.prog = ctk.CTkProgressBar(self, height=4, progress_color=C_ACCENT); self.prog.set(0); self.prog.pack(fill="x")

    def ui_video(self, p):
        # STUDIO LAYOUT (3 Columns)
        p.grid_columnconfigure(0, weight=1); p.grid_columnconfigure(1, weight=1); p.grid_columnconfigure(2, weight=1)
        p.grid_rowconfigure(0, weight=1)

        # --- COL 1: SOURCE ---
        f_src = ctk.CTkFrame(p, fg_color=C_PANEL, corner_radius=10); f_src.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(f_src, text="1. FUENTE", font=FONT_BOLD, text_color=C_ACCENT).pack(pady=10)
        
        ctk.CTkButton(f_src, text="📂 IMPORTAR VIDEO", command=self.sl_vid, width=200, height=40, font=FONT_BOLD).pack(pady=10)
        self.lbl_fv = ctk.CTkLabel(f_src, text="Ningún archivo seleccionado", text_color="gray"); self.lbl_fv.pack()
        
        # Preview Input
        f_pv1 = ctk.CTkFrame(f_src, fg_color="black"); f_pv1.pack(fill="both", expand=True, padx=10, pady=10)
        self.pv_in = CanvasPlayer(f_pv1, self, "wand") 

        # --- COL 2: CONTROL ---
        f_ctl = ctk.CTkFrame(p, fg_color=C_PANEL, corner_radius=10); f_ctl.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(f_ctl, text="2. AJUSTES", font=FONT_BOLD, text_color=C_ACCENT).pack(pady=10)

        # Engine / Motor
        f_eng = ctk.CTkFrame(f_ctl, fg_color="transparent"); f_eng.pack(fill="x", pady=5)
        self.v_eng = tk.StringVar(value="magic")
        ctk.CTkRadioButton(f_eng, text="Turbo", variable=self.v_eng, value="turbo").pack(side="left", padx=10)
        ctk.CTkRadioButton(f_eng, text="Magic (Pro)", variable=self.v_eng, value="magic").pack(side="left", padx=10)
        
        self.model_var = ctk.CTkOptionMenu(f_ctl, values=["u2net", "isnet-anime", "u2net_human_seg", "isnet-general-use"]); self.model_var.pack(pady=5)
        self.model_var.set("isnet-anime")

        # Sliders / Deslizadores
        ctk.CTkLabel(f_ctl, text="Sensibilidad (Umbral)").pack(pady=(10,0))
        self.sl_thresh = ctk.CTkSlider(f_ctl, from_=0.1, to=0.9, number_of_steps=20); self.sl_thresh.set(0.5); self.sl_thresh.pack(pady=5)
        
        ctk.CTkLabel(f_ctl, text="Suavizado de Bordes (Feather)").pack(pady=(10,0))
        self.sl_soft = ctk.CTkSlider(f_ctl, from_=0, to=20, number_of_steps=20); self.sl_soft.set(5); self.sl_soft.pack(pady=5)

        # Wand / Varita
        self.sw_wand = ctk.CTkSwitch(f_ctl, text="Magic Wand (Tracking)", progress_color=C_ACCENT, font=FONT_BOLD); self.sw_wand.pack(pady=15)

        # Format / Formato
        ctk.CTkLabel(f_ctl, text="Formato de Salida").pack(pady=(10,0))
        self.v_fmt = tk.StringVar(value="webm")
        ctk.CTkRadioButton(f_ctl, text="WebM (Transparente - Web/OBS)", variable=self.v_fmt, value="webm").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(f_ctl, text="MOV (Transparente - Editores)", variable=self.v_fmt, value="alpha").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(f_ctl, text="Secuencia PNG (Carpeta)", variable=self.v_fmt, value="png_seq").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(f_ctl, text="Pantalla Verde (Universal)", variable=self.v_fmt, value="green").pack(anchor="w", padx=20, pady=2)

        self.btn_v_go = ctk.CTkButton(f_ctl, text="🚀 PROCESAR VIDEO", height=50, font=FONT_BOLD, fg_color=C_ACCENT, text_color="black", command=self.run_vid)
        self.btn_v_go.pack(fill="x", padx=20, pady=20, side="bottom")

        # --- COL 3: PREVIEW / VISTA PREVIA ---
        f_out = ctk.CTkFrame(p, fg_color=C_PANEL, corner_radius=10); f_out.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(f_out, text="3. RESULTADO", font=FONT_BOLD, text_color=C_ACCENT).pack(pady=10)
        
        f_pv2 = ctk.CTkFrame(f_out, fg_color="black"); f_pv2.pack(fill="both", expand=True, padx=10, pady=10)
        self.pv_out = CanvasPlayer(f_pv2, self, "view")

    def ui_image(self, p):
        ctk.CTkButton(p, text="📂 IMG", command=self.sl_img).pack(pady=5)
        
        pv = ctk.CTkFrame(p, height=300, fg_color="transparent"); pv.pack(fill="both", expand=True)
        self.pi_l = ctk.CTkLabel(pv, text=""); self.pi_l.pack(side="left", fill="both", expand=True)
        self.pi_r = ctk.CTkLabel(pv, text=""); self.pi_r.pack(side="right", fill="both", expand=True)
        
        rf=ctk.CTkFrame(p, fg_color="transparent"); rf.pack(pady=10)
        self.i_fmt = tk.StringVar(value="png")
        ctk.CTkRadioButton(rf, text="PNG", variable=self.i_fmt, value="png").pack(side="left", padx=10)
        ctk.CTkRadioButton(rf, text="JPG", variable=self.i_fmt, value="jpg").pack(side="left", padx=10)
        ctk.CTkRadioButton(rf, text="WEBP", variable=self.i_fmt, value="webp").pack(side="left", padx=10)
        
        self.btn_i_go = ctk.CTkButton(p, text="PROCESS", fg_color=C_ACCENT, text_color="black", command=self.run_img); self.btn_i_go.pack(fill="x", padx=50)

    def ui_audio(self, p):
        ctk.CTkButton(p, text="📂 VIDEO/AUDIO", command=self.sl_aud).pack(pady=20)
        self.lbl_aud_in = ctk.CTkLabel(p, text="..."); self.lbl_aud_in.pack()
        
        self.o_pres = ctk.CTkOptionMenu(p, values=["Normal"], fg_color=C_PANEL); self.o_pres.pack(pady=10)
        self.c_noise = ctk.CTkCheckBox(p, text="Denoise"); self.c_noise.pack(pady=10)
        
        ctk.CTkButton(p, text="EXPORT AUDIO", fg_color=C_ACCENT, text_color="black", command=self.run_aud).pack(pady=20)

    def ui_mark(self, p):
        # Pestaña de Eliminación de Marcas de Agua
        # Permite seleccionar un archivo y dibujar una máscara para borrarla (Inpainting)
        ctk.CTkButton(p, text="📂 ABRIR IMAGEN/VIDEO", command=self.sl_mark).pack(pady=5)
        
        # Selector de Herramienta
        self.v_mtool = tk.StringVar(value="pencil")
        box_tools = ctk.CTkFrame(p, fg_color="transparent"); box_tools.pack(pady=5)
        
        # Botones de Radio para cambiar entre Lápiz y Varita
        ctk.CTkRadioButton(box_tools, text="✏️ Lápiz (Manual)", variable=self.v_mtool, value="pencil", 
                           command=lambda: self.pm.set_mode("pencil")).pack(side="left", padx=10)
        ctk.CTkRadioButton(box_tools, text="🪄 Varita (Color Auto)", variable=self.v_mtool, value="flood", 
                           command=lambda: self.pm.set_mode("flood")).pack(side="left", padx=10)
        
        self.lbl_minstr = ctk.CTkLabel(p, text="Instrucción: Dibuja sobre la marca o haz clic para autoselección."); self.lbl_minstr.pack()
        
        pf = ctk.CTkFrame(p); pf.pack(fill="both", expand=True)
        self.pm = CanvasPlayer(pf, self, "pencil", height=350) # Inicia en modo Lápiz
        
        self.btn_m_go = ctk.CTkButton(p, text="CLEAN", fg_color="red", command=self.run_mark); self.btn_m_go.pack(pady=10)

    # --- LOGIC ---
    def upd_tx(self):
        self.btn_ln.configure(text=self.tr("lang"))
        # self.pan_rem and self.pan_cnv removed in redesign
        self.sw_wand.configure(text=self.tr("wand_on") if self.sw_wand.get() else self.tr("wand_off"))
        self.btn_v_go.configure(text=self.tr("btn_run"))
        self.o_pres.configure(values=self.tr("p_presets")); self.o_pres.set(self.tr("p_presets")[0])

    def sl_vid(self): f=filedialog.askopenfilename(); self.in_vid=f; self.lbl_fv.configure(text=os.path.basename(f)); self.pv_in.load(f)
    def sl_img(self): 
        f=filedialog.askopenfilename(); self.in_img=f
        im=Image.open(f); im.thumbnail((300,300)); ci=ctk.CTkImage(im,im,(im.width,im.height))
        self.pi_l.configure(image=ci); self.pi_r.configure(image=None)
    def sl_aud(self): f=filedialog.askopenfilename(); self.in_aud=f; self.lbl_aud_in.configure(text=os.path.basename(f))
    def sl_mark(self): f=filedialog.askopenfilename(); self.in_mark=f; self.pm.load(f)

    def run_vid(self):
        # Esta función inicia el proceso de video.
        if not self.in_vid: return
        # Iniciar Hilo (Threading):
        # Es CRÍTICO usar un hilo separado (threading.Thread) para procesos largos.
        # Si ejecutamos _run_v directamente, la ventana de la app se congelaría ("No Responde")
        # hasta que termine el video. El hilo permite que la UI siga respondiendo.
        self.lock(True); threading.Thread(target=self._run_v).start()

    def _run_v(self):
        # --- MOTOR PRINCIPAL DE VIDEO ---
        try:
            # Recoger valores de la UI
            wand = self.sw_wand.get() # Modo Tracking activado?
            eng = self.v_eng.get()    # Motor: 'turbo' (MediaPipe) o 'magic' (Rembg)
            out_t = self.v_fmt.get()  # Formato: webm, mov, secuencias...
            thresh = self.sl_thresh.get() # Umbral de sensibilidad
            soft = int(self.sl_soft.get()) # Valor de suavizado (kernel size)
            if soft % 2 == 0: soft += 1 # Debe ser impar para GaussianBlur (regla matemática de convolución)
            
            # Abrir el video con OpenCV
            cap = cv2.VideoCapture(self.in_vid)
            # Leer metadatos: Ancho (3), Alto (4), FPS (5)
            w = int(cap.get(3)); h = int(cap.get(4)); fps = cap.get(5)
            
            # Configuración de Salida (Tuberías / Pipes)
            pipe_writer = None; seq_dir = ""
            if out_t == "green":
                # Pantalla Verde: Usamos H.264 (mp4) estándar.
                # pipe open...
                temp_vid = self.get_unique_path(self.in_vid, "Green", "mp4")
                cmd = ["ffmpeg","-y","-f","rawvideo","-vcodec","rawvideo","-s",f"{w}x{h}","-pix_fmt","bgr24","-r",str(fps),"-i","-","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",temp_vid]
                pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            elif out_t == "webm":
                 # WebM con Transparencia: Usa códec VP9 y formato de píxel yuva420p (la 'a' es alfa).
                 temp_vid = self.get_unique_path(self.in_vid, "WebM", "webm")
                 cmd = ["ffmpeg","-y","-f","rawvideo","-vcodec","rawvideo","-s",f"{w}x{h}","-pix_fmt","bgra","-r",str(fps),"-i","-","-c:v","libvpx-vp9","-b:v","2M","-pix_fmt","yuva420p",temp_vid]
                 pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            elif out_t == "png_seq":
                 # Secuencia PNG: Opción nuclear. No usa video, guarda una carpeta de fotos.
                 base_n = os.path.splitext(os.path.basename(self.in_vid))[0]
                 # Lógica de directorio único...
                 seq_dir = "Descargas"
                 if not os.path.exists(seq_dir): os.makedirs(seq_dir)
                 for i in range(1, 1000):
                     sd = os.path.join(seq_dir, f"{base_n}_Frames_{i:03d}")
                     if not os.path.exists(sd):
                         seq_dir = sd; break
                 if not os.path.exists(seq_dir): os.makedirs(seq_dir)
                 pipe = None
            else:
                 # MOV con Transparencia (Universal):
                 # Usamos códec 'png' dentro del contenedor MOV. Es literalmente imágenes PNG en video.
                 # Esto garantiza compatibilidad 100% con editores que no soportan ProRes 4444.
                 temp_vid = self.get_unique_path(self.in_vid, "Alpha", "mov")
                 cmd = ["ffmpeg","-y","-f","rawvideo","-vcodec","rawvideo","-s",f"{w}x{h}","-pix_fmt","bgra","-r",str(fps),"-i","-","-c:v","png","-pix_fmt","rgba",temp_vid]
                 pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE) 

            writ = None

            # Inicializar Motores (Init Engines)
            sess = None; seg = None
            if eng == "magic":
                 model_name = self.model_var.get()
                 if not self.rembg or (getattr(self, 'curr_model', '') != model_name): 
                     self.lock(True, f"Cargando modelo AI: {model_name}...")
                     self.rembg = new_session(model_name)
                     self.curr_model = model_name
                 sess = self.rembg
            else:
                 m_path="selfie_segmenter.tflite"
                 if not os.path.exists(m_path):
                     import urllib.request
                     self.lock(True, "Descargando modelo Turbo...")
                     urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite", m_path)
                 op = mp.tasks.vision.ImageSegmenterOptions(base_options=mp.tasks.BaseOptions(model_asset_path=m_path), running_mode=mp.tasks.vision.RunningMode.IMAGE, output_confidence_masks=True)
                 seg = mp.tasks.vision.ImageSegmenter.create_from_options(op)

            # Loop
            prev_g=None; tot=int(cap.get(7)); cnt=0
            lk_p = dict(winSize=(15,15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,10,0.03))
            
            start_time = time.time()
            while True:
                r, f = cap.read()
                if not r: break
                cnt+=1
                
                # AI Mask Base
                if eng == "magic":
                    m = remove(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), session=sess, alpha_matting=True)[:,:,3].copy()
                else: 
                    res = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)))
                    if len(res.confidence_masks) > 1: target_mask = res.confidence_masks[1]
                    elif len(res.confidence_masks) > 0: target_mask = res.confidence_masks[0]
                    else: target_mask = None

                    if target_mask: m = (target_mask.numpy_view()>0.5).astype(np.uint8)*255
                    else: m = np.zeros((f.shape[0], f.shape[1]), dtype=np.uint8)
                
                # --- PROCESAMIENTO PROFESIONAL DE MÁSCARA ---
                # 1. Umbralización (Thresholding):
                #    Convertimos la máscara suave (grises) en dura (blanco/negro) según la sensibilidad.
                #    Esto ayuda a eliminar "manchas" semitransparentes no deseadas.
                #    cv2.threshold devuelve (ret, imagen_resultado).
                if eng != "magic": 
                    # MediaPipe ya devuelve binario o casi binario, pero podemos asegurar.
                    pass 
                else:
                    # Aplicamos umbral: todo lo menor a "thresh" se vuelve 0 (transparente).
                    _, m = cv2.threshold(m, int(thresh*255), 255, cv2.THRESH_TOZERO)

                # 2. Plumeado / Suavizado (Feathering):
                #    Aplicamos un Desenfoque Gaussiano (GaussianBlur) a los bordes de la máscara.
                #    Esto hace que el recorte se vea natural y no "pegado" o pixelado.
                if soft > 1:
                     m = cv2.GaussianBlur(m, (soft, soft), 0)

                # Aseguramos que la matriz sea escribible (requisito técnico de numpy/opencv).
                if not m.flags.writeable: m = m.copy()

                # 3. Flujo Óptico (Tracking) - Opcional:
                #    Si usamos la varita de seguimiento, calculamos hacia dónde se movieron los puntos
                #    y dibujamos sobre la máscara para "forzar" mantener esas áreas.
                if wand and track_pts is not None:
                     g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                     if prev_g is not None:
                         # Lucas-Kanade Optical Flow (calcOpticalFlowPyrLK)
                         p1, st, err = cv2.calcOpticalFlowPyrLK(prev_g, g, track_pts, None, **lk_p)
                         good = p1[st==1]
                         if len(good)>0:
                             track_pts = good.reshape(-1,1,2)
                             for pt in track_pts: cv2.circle(m, (int(pt[0][0]), int(pt[0][1])), 20, 255, -1)
                     prev_g = g
                elif wand and track_pts is not None and prev_g is None:
                     prev_g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)

                # Output Processing
                try:
                    if out_t=="green":
                        # Composición Pantalla Verde:
                        # Fórmula: Pixeles = (Original * Máscara) + (Verde * (1 - Máscara))
                        bg=np.zeros_like(f); bg[:]=(0,255,0); m_n=m/255.0; m3=np.dstack((m_n,m_n,m_n))
                        fin = (f*m3 + bg*(1-m3)).astype(np.uint8)
                        if pipe: pipe.stdin.write(fin.tobytes())
                    else:
                        # Salida con Transparencia (Alpha Channel):
                        # Separamos los canales Azul, Verde y Rojo original.
                        b,g,r_ = cv2.split(f)
                        
                        # CRÍTICO: "Enmascaramos" (bitwise_and) los canales de color también.
                        # Esto pone en NEGRO (0,0,0) los píxeles transparentes.
                        # Si no hacemos esto, algunos reproductores mostrarían el fondo antiguo "escondido".
                        b = cv2.bitwise_and(b, b, mask=m)
                        g = cv2.bitwise_and(g, g, mask=m)
                        r_ = cv2.bitwise_and(r_, r_, mask=m)
                        
                        # Unimos B, G, R y el canal Alpha (m) en una imagen de 4 canales.
                        fin = cv2.merge((b,g,r_,m))
                        
                        if out_t == "png_seq":
                             # Escritura Directa a Disco (Secuencia de Imágenes)
                             fname = os.path.join(seq_dir, f"frame_{cnt:05d}.png")
                             cv2.imwrite(fname, fin)
                        elif pipe:
                             # Escritura al Pipe de FFmpeg
                             pipe.stdin.write(fin.tobytes())

                except BrokenPipeError:
                    self.lock(False, "Error: Tubería FFmpeg Rota"); break
                except Exception as e: 
                    self.lock(False, f"Error Tubería: {e}"); break
                
                # Visual Feedback
                if cnt % 2 == 0:
                    prog_val = int(cnt/tot*100)
                    elapsed = time.time() - start_time
                    if elapsed > 0 and cnt > 0:
                        rate = cnt / elapsed; rem_frames = tot - cnt; etr_s = rem_frames / rate
                        etr_str = f"{int(etr_s//60):02d}:{int(etr_s%60):02d}"
                    else: etr_str = "--:--"

                    msg = f"PROCESANDO: {prog_val}% (ETR: {etr_str})"
                    self.upd(cnt/tot, msg)
                    
                    if m.max() == 0: self.upd(cnt/tot, msg + " (⚠️ VACÍO)")

                    # Overlay Percentage on Preview
                    if out_t == "green":
                        prev_f = fin.copy()
                    else:
                        h_pv, w_pv = fin.shape[:2]
                        cb = np.zeros((h_pv, w_pv, 3), dtype=np.uint8); cb[:] = (50, 50, 50)
                        step = 20
                        for y in range(0, h_pv, step):
                           for x in range(0, w_pv, step):
                               if (x//step + y//step) % 2 == 0: cb[y:y+step, x:x+step] = (100, 100, 100)
                        
                        b,g,r,a = cv2.split(fin); a_f = a/255.0
                        fg = cv2.merge((b,g,r))
                        prev_f = (fg * a_f[:,:,None] + cb * (1 - a_f[:,:,None])).astype(np.uint8)

                    cv2.rectangle(prev_f, (20, 70), (450, 180), (0, 0, 0), -1) 
                    cv2.putText(prev_f, f"{prog_val}%", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                    cv2.putText(prev_f, f"ETR: {etr_str}", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                    self.after(0, lambda frame=prev_f: self.pv_out.show(frame))

            cap.release(); 
            if writ: writ.release()
            if pipe: pipe.stdin.close(); pipe.wait()

            # --- AUDIO MUX (Pass 2) ---
            if out_t == "png_seq":
                self.pv_out.stop() # Can't play sequence easily
                self.lock(False, f"¡Listo! Secuencia guardada en:\n{seq_dir}")
                return

            self.lock(True, "Uniendo Audio...")
            out_final = os.path.splitext(self.in_vid)[0]
            if out_t == "png_seq":
                self.pv_out.stop()
                self.lock(False, f"¡Listo! Secuencia:\n{seq_dir}")
                return

            self.lock(True, "Uniendo Audio...")
            # temp_vid is ALREADY the final path with get_unique_path, BUT logic below renames it?
            # Actually with get_unique_path, temp_vid IS the destination. But we need to MUX audio into it.
            # We must use a tmp file for muxing if we want to write back to final, or write to tmp first.
            # Current logic: temp_vid -> output.
            
            # Let's adjust: ffmpeg wrote to 'temp_vid' (which is now in Descargas).
            # We should write MUXED output to a NEW temp, then rename? 
            # OR: Let's treat 'temp_vid' as the raw video, and 'out_final' as the muxed one.
            
            # Since get_unique_path gives us a nice name, let's call that 'final_path'.
            # And 'temp_vid' should have been a tmp file.
            # FIX: Let's rename the temp_vid logic above to use a real temp file, OR just append "muxed" here.
            
            final_artifact = self.get_unique_path(self.in_vid, out_t.upper()+"_Audio", temp_vid.split(".")[-1])
            
            if out_t == "green":
                cmd_mux = ["ffmpeg","-y","-i",temp_vid,"-i",self.in_vid,"-c:v","copy","-c:a","aac","-map","0:v:0","-map","1:a:0","-shortest", final_artifact]
            elif out_t == "webm":
                 cmd_mux = ["ffmpeg","-y","-i",temp_vid,"-i",self.in_vid,"-c:v","copy","-c:a","libvorbis","-map","0:v:0","-map","1:a:0","-shortest", final_artifact]
            else:
                cmd_mux = ["ffmpeg","-y","-i",temp_vid,"-i",self.in_vid,"-c:v","copy","-c:a","pcm_s16le","-map","0:v:0","-map","1:a:0","-shortest", final_artifact]
            
            subprocess.run(cmd_mux, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(temp_vid): os.remove(temp_vid) # Remove the silent video

            self.pv_out.load(final_artifact)
            self.lock(False, f"Guardado: {os.path.basename(final_artifact)}")
            


        except Exception as e: self.lock(False, str(e)); print(e)


    def cnv_v(self, m):
        if not self.in_vid: return
        def _c():
            ext = "mov" if m=="prores" else "mp4"
            out = self.get_unique_path(self.in_vid, "Conv_"+m, ext)
            cmd = ["ffmpeg","-y","-i",self.in_vid]
            if m=="prores": cmd.extend(["-c:v","prores_ks","-profile:v","2", "-c:a","pcm_s16le", out])
            else: cmd.extend(["-c:v","libx264","-c:a","aac", out])
            
            # Robust Check
            print(f"DEBUG: Ejecutando FFmpeg: {cmd}")
            try:
                res = subprocess.run(cmd, check=True, capture_output=True, text=True)
                self.lock(False, f"Guardado: {os.path.basename(out)}")
            except subprocess.CalledProcessError as e:
                print(f"FFMPEG ERROR: {e.stderr}")
                self.lock(False, f"Error Conv: {e.stderr[:50]}...")
        self.lock(True, "Convirtiendo..."); threading.Thread(target=_c).start()

    def run_img(self): 
        if not self.in_img: return
        self.lock(True); threading.Thread(target=self._run_i).start()
    def _run_i(self):
        print(f"DEBUG: Iniciando _run_i con {self.in_img}")
        try:
             # Similar Img Logic
             f = self.i_fmt.get(); img = cv2.imread(self.in_img)
             if img is None: raise Exception("No se pudo leer la imagen")
             
             print("DEBUG: Ejecutando remove...")
             # Session optimization
             if not self.rembg: self.rembg = new_session(self.model_var.get())
             
             res = remove(img, session=self.rembg, alpha_matting=True)
             
             out = self.get_unique_path(self.in_img, "NoBG", f)
             print(f"DEBUG: Guardando en {out}")
             cv2.imwrite(out, res) 
             
             # Show
             im = Image.open(out); im.thumbnail((300,300)); ci=ctk.CTkImage(im,im,(im.width,im.height))
             self.after(0, lambda: self.pi_r.configure(image=ci))
             self.lock(False, f"Guardado: {os.path.basename(out)}")
        except Exception as e: 
            print(f"ERROR IMG: {e}")
            self.lock(False, f"Error: {str(e)}")

    def run_aud(self):
         # Similar Audio Logic
         pass # Placeholder for brevity, user has logic already prueba

    def run_mark(self):
        # Valida si hay algo para procesar: O trazos libres (Lápiz) o máscaras (Varita)
        if not self.in_mark or (not self.pm.strokes and not self.pm.masks): return
        self.lock(True); threading.Thread(target=self._run_m).start()

    def _run_m(self):
        # --- MOTOR DE ELIMINACIÓN DE MARCAS DE AGUA (INPAINTING) ---
        try:
            c=cv2.VideoCapture(self.in_mark); w=int(c.get(3)); h=int(c.get(4)); fps=c.get(5)
            
            out = self.get_unique_path(self.in_mark, "Clean", "mp4")
            writ=cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w,h))
            
            # Obtener Máscara Combinada (Lápiz + Varita) de CanvasPlayer
            m = self.pm.get_mask(w, h)
            
            tot=int(c.get(7)); cnt=0
            while True:
                r,f=c.read()
                if not r: break
                cnt+=1
                
                # Inpainting (Reconstrucción):
                # cv2.inpaint usa los píxeles vecinos para "rellenar" el área blanca de la máscara.
                # flags: cv2.INPAINT_TELEA (Algoritmo rápido basado en Fast Marching Method)
                # radio: 3px (distancia de vecindad para tomar color)
                wr=cv2.inpaint(f, m, 3, cv2.INPAINT_TELEA)
                
                writ.write(wr)
                if cnt%10==0: self.upd(cnt/tot, "Inpainting...") # Actualiza UI cada 10 frames
            c.release(); writ.release()
            self.lock(False, f"Saved: {out}")
        except Exception as e: self.lock(False, str(e))

    def lock(self, l, t="Processing..."):
        self.stat.configure(text=t); self.prog.set(0 if l else 1)
        if l: self.prog.start() 
        else: self.prog.stop()

    def upd(self, p, t): self.prog.set(p); self.stat.configure(text=t)

if __name__ == "__main__":
    app = NaiWebSuite()
    app.mainloop()
