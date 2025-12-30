import customtkinter as ctk
import os
import time
from src.utils.config import C_PANEL, C_ACCENT, FONT_BOLD, FONT_MAIN
from src.ui.widgets import CanvasPlayer

class DownloadsTab:
    def __init__(self, parent):
        self.frame = parent
        self.cwd = "Descargas"
        if not os.path.exists(self.cwd): os.makedirs(self.cwd)
        
        self.init_ui()
        self.refresh_list()

    def init_ui(self):
        # Layout: Left List | Right Preview
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=2)
        self.frame.grid_rowconfigure(0, weight=1)

        # --- LEFT: File List ---
        f_list = ctk.CTkFrame(self.frame, fg_color=C_PANEL)
        f_list.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Header
        h = ctk.CTkFrame(f_list, fg_color="transparent")
        h.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(h, text="📂 MIS DESCARGAS", font=FONT_BOLD).pack(side="left")
        ctk.CTkButton(h, text="🔄", width=30, command=self.refresh_list).pack(side="right")
        
        self.scroll = ctk.CTkScrollableFrame(f_list, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # --- RIGHT: Preview ---
        f_prev = ctk.CTkFrame(self.frame, fg_color="#000000")
        f_prev.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(f_prev, text="VISTA PREVIA", font=FONT_BOLD, text_color="gray").pack(pady=5)
        
        self.player = CanvasPlayer(f_prev, self.frame, "view") # Reusing CanvasPlayer
        
        # Actions
        f_act = ctk.CTkFrame(f_prev, fg_color="transparent")
        f_act.pack(fill="x", pady=10)
        self.btn_play = ctk.CTkButton(f_act, text="▶️ REPRODUCIR", state="disabled", fg_color=C_ACCENT, text_color="black", command=self.player.play)
        self.btn_play.pack(side="left", padx=10, expand=True)

        self.btn_stop = ctk.CTkButton(f_act, text="⏹️ STOP", fg_color="#333", command=self.player.stop)
        self.btn_stop.pack(side="left", padx=10, expand=True)
        
        self.btn_open = ctk.CTkButton(f_act, text="📂 ABRIR CARPETA", command=lambda: os.system(f"xdg-open {self.cwd}"))
        self.btn_open.pack(side="right", padx=20, expand=True)

        self.lbl_info = ctk.CTkLabel(f_prev, text="", text_color="gray")
        self.lbl_info.pack(pady=5)

    def refresh_list(self):
        for w in self.scroll.winfo_children(): w.destroy()
        
        if not os.path.exists(self.cwd): return

        # Get files sorted by modified time (newest first)
        files = [f for f in os.listdir(self.cwd) if os.path.isfile(os.path.join(self.cwd, f))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self.cwd, x)), reverse=True)
        
        pass_icon = {"mp4":"🎥", "webm":"🎥", "mov":"🎥", "png":"🖼️", "jpg":"🖼️", "webp":"🖼️", "mp3":"🎵", "wav":"🎵"}

        for f in files:
            ext = f.split(".")[-1].lower()
            icon = pass_icon.get(ext, "📄")
            
            # File Item
            item = ctk.CTkButton(self.scroll, text=f"{icon} {f}", anchor="w", fg_color="transparent",
                                 hover_color="#444", font=FONT_MAIN,
                                 command=lambda path=os.path.join(self.cwd, f): self.select_file(path))
            item.pack(fill="x", pady=1)

    def select_file(self, path):
        self.player.stop()
        self.player.load(path)
        
        # Enable Play only for video/audio
        ext = path.split(".")[-1].lower()
        if ext in ["mp4", "webm", "mov", "mp3", "wav"]:
            self.btn_play.configure(state="normal")
        else:
            self.btn_play.configure(state="disabled")
            
        size_mb = os.path.getsize(path) / (1024*1024)
        self.lbl_info.configure(text=f"{os.path.basename(path)} ({size_mb:.1f} MB)")
