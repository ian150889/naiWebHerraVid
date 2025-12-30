import customtkinter as ctk
import threading
import os
from tkinter import filedialog
from PIL import Image
from src.core.image_engine import ImageEngine
from src.utils.config import C_ACCENT

class ImageTab:
    def __init__(self, parent):
        self.frame = parent
        self.engine = ImageEngine()
        self.in_path = ""
        self.init_ui()

    def init_ui(self):
        # 1. Source
        ctk.CTkButton(self.frame, text="📂 ABRIR IMAGEN", command=self.load_file).pack(pady=10)
        
        # 2. Preview
        pv = ctk.CTkFrame(self.frame, height=300, fg_color="transparent")
        pv.pack(fill="both", expand=True)
        
        self.lbl_l = ctk.CTkLabel(pv, text="Original")
        self.lbl_l.pack(side="left", fill="both", expand=True)
        
        self.lbl_r = ctk.CTkLabel(pv, text="Resultado")
        self.lbl_r.pack(side="right", fill="both", expand=True)

        # 3. Format
        self.v_fmt = ctk.StringVar(value="png")
        f_fmt = ctk.CTkFrame(self.frame, fg_color="transparent")
        f_fmt.pack(pady=10)
        
        ctk.CTkRadioButton(f_fmt, text="PNG (Transparente)", variable=self.v_fmt, value="png").pack(side="left", padx=10)
        ctk.CTkRadioButton(f_fmt, text="JPG (Fondo Blanco)", variable=self.v_fmt, value="jpg").pack(side="left", padx=10)
        ctk.CTkRadioButton(f_fmt, text="WEBP (Optimizado)", variable=self.v_fmt, value="webp").pack(side="left", padx=10)

        # 4. Action
        self.btn_run = ctk.CTkButton(self.frame, text="🚀 PROCESAR IMAGEN", fg_color=C_ACCENT, text_color="black", command=self.run)
        self.btn_run.pack(pady=10, fill="x", padx=50)
        self.lbl_stat = ctk.CTkLabel(self.frame, text="", text_color=C_ACCENT)
        self.lbl_stat.pack()

    def load_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.in_path = f
            im = Image.open(f)
            im.thumbnail((300,300))
            ci = ctk.CTkImage(im, im, (im.width, im.height))
            self.lbl_l.configure(image=ci, text="")
            self.lbl_r.configure(image=None, text="Resultado")

    def run(self):
        if not self.in_path: return
        self.btn_run.configure(state="disabled", text="Procesando...")
        self.lbl_stat.configure(text="Eliminando fondo...")
        
        def _t():
            out = self.engine.process(self.in_path, fmt=self.v_fmt.get())
            self.btn_run.configure(state="normal", text="🚀 PROCESAR IMAGEN")
            
            if out:
                im = Image.open(out)
                im.thumbnail((300,300))
                ci = ctk.CTkImage(im, im, (im.width, im.height))
                self.lbl_r.configure(image=ci, text="")
                self.lbl_stat.configure(text=f"¡Guardado! {os.path.basename(out)}")
            else:
                self.lbl_stat.configure(text="Error al procesar.")
        
        threading.Thread(target=_t).start()
