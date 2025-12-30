import customtkinter as ctk
import cv2
import threading
import os
from tkinter import filedialog
from src.ui.widgets import CanvasPlayer
from src.utils.file_manager import FileManager
from src.utils.config import C_ACCENT, C_PANEL, FONT_BOLD

class MarkTab:
    def __init__(self, parent):
        self.frame = parent
        self.in_path = ""
        self.init_ui()

    def init_ui(self):
        # 1. Source
        ctk.CTkButton(self.frame, text="📂 ABRIR VIDEO/IMAGEN", command=self.load_file).pack(pady=10)
        
        # 2. Tools
        f_tool = ctk.CTkFrame(self.frame, fg_color="transparent")
        f_tool.pack(pady=5)
        self.v_tool = ctk.StringVar(value="pencil")
        
        ctk.CTkRadioButton(f_tool, text="✏️ Lápiz", variable=self.v_tool, value="pencil", 
                           command=lambda: self.player.set_mode("pencil")).pack(side="left", padx=10)
        ctk.CTkRadioButton(f_tool, text="🪄 Varita (Color)", variable=self.v_tool, value="flood", 
                           command=lambda: self.player.set_mode("flood")).pack(side="left", padx=10)
        
        ctk.CTkLabel(self.frame, text="Instrucción: Dibuja sobre la marca para borrarla.").pack()

        # 3. Canvas
        f_cv = ctk.CTkFrame(self.frame)
        f_cv.pack(fill="both", expand=True, padx=5, pady=5)
        self.player = CanvasPlayer(f_cv, self.frame, "pencil", height=350)

        # 4. Action
        self.btn_run = ctk.CTkButton(self.frame, text="🧹 BORRAR MARCA", fg_color="red", command=self.run)
        self.btn_run.pack(pady=10, fill="x", padx=50)
        
        self.lbl_stat = ctk.CTkLabel(self.frame, text="", text_color=C_ACCENT)
        self.lbl_stat.pack()
        self.prog = ctk.CTkProgressBar(self.frame, progress_color=C_ACCENT)
        self.prog.set(0); self.prog.pack(fill="x", padx=20, pady=5)

    def load_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.in_path = f
            self.player.load(f)

    def run(self):
        if not self.in_path: return
        self.btn_run.configure(state="disabled")
        
        def _t():
            try:
                cap = cv2.VideoCapture(self.in_path)
                w = int(cap.get(3)); h = int(cap.get(4)); fps = cap.get(5)
                tot = int(cap.get(7))
                
                out_path = FileManager.get_unique_path(self.in_path, "Clean", "mp4")
                writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w,h))
                
                # Get Combined Mask
                mask = self.player.get_mask(w, h)
                
                cnt = 0
                while True:
                    ret, frame = cap.read()
                    if not ret: break
                    cnt += 1
                    
                    # Inpaint
                    clean = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
                    writer.write(clean)
                    
                    if cnt % 10 == 0:
                        self.prog.set(cnt/tot)
                        self.lbl_stat.configure(text=f"Procesando: {int(cnt/tot*100)}%")
                
                cap.release(); writer.release()
                
                self.btn_run.configure(state="normal")
                self.lbl_stat.configure(text=f"¡Guardado! {os.path.basename(out_path)}")
            except Exception as e:
                print(f"Mark Err: {e}")
                self.lbl_stat.configure(text="Error.")
                self.btn_run.configure(state="normal")
        
        threading.Thread(target=_t).start()
