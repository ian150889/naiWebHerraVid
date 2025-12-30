import customtkinter as ctk
from tkinter import filedialog
import os
import threading
from src.core.audio_engine import AudioEngine
from src.utils.config import C_PANEL, C_ACCENT, FONT_BOLD

class AudioTab:
    def __init__(self, parent):
        self.frame = parent
        self.in_path = ""
        self.init_ui()

    def init_ui(self):
        # 1. Source
        f_src = ctk.CTkFrame(self.frame, fg_color=C_PANEL)
        f_src.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(f_src, text="📂 ABRIR AUDIO/VIDEO", command=self.load_file).pack(side="left", padx=10, pady=10)
        self.lbl_file = ctk.CTkLabel(f_src, text="Sin archivo...")
        self.lbl_file.pack(side="left", padx=10)

        # 2. Controls (Grid)
        f_ctl = ctk.CTkFrame(self.frame, fg_color="transparent")
        f_ctl.pack(fill="both", expand=True, padx=10)

        # Pitch Control
        ctk.CTkLabel(f_ctl, text="Tonalidad (Semitonos)", font=FONT_BOLD).pack(pady=(20,5))
        self.sl_pitch = ctk.CTkSlider(f_ctl, from_=-12, to=12, number_of_steps=24)
        self.sl_pitch.set(0)
        self.sl_pitch.pack(pady=5)
        self.lbl_pitch = ctk.CTkLabel(f_ctl, text="0 st")
        self.lbl_pitch.pack()
        self.sl_pitch.configure(command=lambda v: self.lbl_pitch.configure(text=f"{int(v)} st"))

        # Presets
        ctk.CTkLabel(f_ctl, text="Efectos de Voz", font=FONT_BOLD).pack(pady=(20,5))
        self.v_preset = ctk.CTkOptionMenu(f_ctl, values=["Normal", "Ardilla", "Goku / Villano", "Demonio"])
        self.v_preset.pack(pady=5)

        # Action
        self.btn_run = ctk.CTkButton(f_ctl, text="🎹 PROCESAR AUDIO", fg_color=C_ACCENT, text_color="black", 
                                     height=50, font=FONT_BOLD, command=self.run_process)
        self.btn_run.pack(pady=30, fill="x", padx=50)
        
        self.lbl_status = ctk.CTkLabel(f_ctl, text="", text_color=C_ACCENT)
        self.lbl_status.pack()

    def load_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.in_path = f
            self.lbl_file.configure(text=os.path.basename(f))

    def run_process(self):
        if not self.in_path: return
        
        self.btn_run.configure(state="disabled", text="Procesando...")
        self.lbl_status.configure(text="Generando audio mágico...")
        
        def _t():
            semi = self.sl_pitch.get()
            preset = self.v_preset.get()
            
            # If manual pitch is used, ignore preset "Normal" logic or combine?
            # Let's say preset overrides if not Normal, else pitch.
            if preset == "Normal": 
                out = AudioEngine.apply_effects(self.in_path, "Normal", semi)
            else:
                out = AudioEngine.apply_effects(self.in_path, preset, 0) # Presets usually have fixed pitch
                
            self.btn_run.configure(state="normal", text="🎹 PROCESAR AUDIO")
            if out:
                self.lbl_status.configure(text=f"¡Guardado! {os.path.basename(out)}")
            else:
                self.lbl_status.configure(text="Error en el procesamiento.")
                
        threading.Thread(target=_t).start()
