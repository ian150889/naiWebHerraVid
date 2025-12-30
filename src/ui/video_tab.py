import customtkinter as ctk
import tkinter as tk
import threading
import os
from tkinter import filedialog
from src.core.video_engine import VideoEngine
from src.ui.widgets import CanvasPlayer
from src.utils.config import C_PANEL, C_ACCENT, FONT_BOLD

class VideoTab:
    def __init__(self, parent):
        self.frame = parent
        self.in_path = ""
        self.engine = VideoEngine(self.update_progress, self.update_status)
        self.init_ui()

    def init_ui(self):
        # Layout: 3 Columns
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        # Col 1: Source
        f_src = ctk.CTkFrame(self.frame, fg_color=C_PANEL)
        f_src.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(f_src, text="1. FUENTE", font=FONT_BOLD, text_color=C_ACCENT).pack(pady=10)
        ctk.CTkButton(f_src, text="📂 IMPORTAR VIDEO", command=self.load_file).pack(pady=10)
        self.lbl_file = ctk.CTkLabel(f_src, text="...")
        self.lbl_file.pack()
        
        # Preview
        f_pv = ctk.CTkFrame(f_src, fg_color="black")
        f_pv.pack(fill="both", expand=True, padx=5, pady=5)
        self.player = CanvasPlayer(f_pv, self.frame, "wand_track") # Tracking mode

        # Col 2: Settings
        f_set = ctk.CTkFrame(self.frame, fg_color=C_PANEL)
        f_set.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(f_set, text="2. AJUSTES", font=FONT_BOLD, text_color=C_ACCENT).pack(pady=10)
        
        # Engine
        self.v_eng = ctk.StringVar(value="magic")
        ctk.CTkRadioButton(f_set, text="Magic Mode (Rembg)", variable=self.v_eng, value="magic").pack(pady=5)
        ctk.CTkRadioButton(f_set, text="Turbo Mode (MediaPipe)", variable=self.v_eng, value="turbo").pack(pady=5)
        
        self.v_model = ctk.CTkOptionMenu(f_set, values=["u2net", "isnet-anime", "u2net_human_seg"])
        self.v_model.set("isnet-anime")
        self.v_model.pack(pady=5)

        # Sliders
        ctk.CTkLabel(f_set, text="Sensibilidad").pack(pady=(10,0))
        self.sl_thresh = ctk.CTkSlider(f_set, from_=0.1, to=0.9, number_of_steps=20)
        self.sl_thresh.set(0.5)
        self.sl_thresh.pack(pady=5)
        
        ctk.CTkLabel(f_set, text="Suavizado").pack(pady=(10,0))
        self.sl_soft = ctk.CTkSlider(f_set, from_=0, to=20, number_of_steps=20)
        self.sl_soft.set(5)
        self.sl_soft.pack(pady=5)

        # Tracking Check
        self.chk_track = ctk.CTkSwitch(f_set, text="📍 Tracking (Puntos)", progress_color=C_ACCENT)
        self.chk_track.pack(pady=20)

        # Output Text
        ctk.CTkLabel(f_set, text="Formato de Salida").pack(pady=(10,0))
        self.v_fmt = ctk.StringVar(value="webm")
        ctk.CTkRadioButton(f_set, text="WebM (Transparente)", variable=self.v_fmt, value="webm").pack(anchor="w", padx=20)
        ctk.CTkRadioButton(f_set, text="MOV (PNG Codec)", variable=self.v_fmt, value="alpha").pack(anchor="w", padx=20)
        ctk.CTkRadioButton(f_set, text="Secuencia PNG", variable=self.v_fmt, value="png_seq").pack(anchor="w", padx=20)
        ctk.CTkRadioButton(f_set, text="Pantalla Verde", variable=self.v_fmt, value="green").pack(anchor="w", padx=20)

        self.btn_run = ctk.CTkButton(f_set, text="🚀 PROCESAR", fg_color=C_ACCENT, text_color="black", 
                                     height=50, font=FONT_BOLD, command=self.run)
        self.btn_run.pack(fill="x", padx=20, pady=20, side="bottom")

        # Col 3: Status
        f_stat = ctk.CTkFrame(self.frame, fg_color=C_PANEL)
        f_stat.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(f_stat, text="3. ESTADO", font=FONT_BOLD, text_color=C_ACCENT).pack(pady=10)
        
        self.lbl_stat = ctk.CTkLabel(f_stat, text="Listo.", wraplength=200)
        self.lbl_stat.pack(pady=20)
        
        self.prog = ctk.CTkProgressBar(f_stat, progress_color=C_ACCENT)
        self.prog.set(0)
        self.prog.pack(fill="x", padx=20)

    def load_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.in_path = f
            self.lbl_file.configure(text=os.path.basename(f))
            self.player.load(f)

    def update_progress(self, val, txt):
        try:
            self.prog.set(val)
            self.lbl_stat.configure(text=txt)
        except: pass

    def update_status(self, txt):
        try: self.lbl_stat.configure(text=txt)
        except: pass

    def run(self):
        if not self.in_path: return
        self.btn_run.configure(state="disabled")
        
        def _t():
            soft = int(self.sl_soft.get()); soft = soft+1 if soft%2==0 else soft
            pts = self.player.points if self.chk_track.get() else None
            
            res = self.engine.process_video(
                self.in_path, 
                engine=self.v_eng.get(),
                model=self.v_model.get(),
                out_fmt=self.v_fmt.get(),
                wand_mode=self.chk_track.get(),
                tracking_points=pts,
                thresh=self.sl_thresh.get(),
                soft=soft
            )
            
            self.btn_run.configure(state="normal")
            if res:
                self.lbl_stat.configure(text=f"¡Completado!\n{os.path.basename(res)}")
            else:
                self.lbl_stat.configure(text="Error.")
                
        threading.Thread(target=_t).start()
