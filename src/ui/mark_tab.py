import customtkinter as ctk
import cv2
import sys
import threading
import os
import subprocess
import gc
import time
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
        
        # 3.1 Timeline
        f_time = ctk.CTkFrame(self.frame, fg_color="transparent")
        f_time.pack(fill="x", padx=10, pady=2)
        
        self.lbl_time = ctk.CTkLabel(f_time, text="00:00 / 00:00", width=80)
        self.lbl_time.pack(side="left")
        
        self.slider = ctk.CTkSlider(f_time, from_=0, to=100, command=self.on_seek)
        self.slider.set(0)
        self.slider.pack(side="left", fill="x", expand=True, padx=10)

        # 4. Action
        self.chk_mov = ctk.CTkCheckBox(self.frame, text="Exportar como .MOV (Formato Edición)")
        self.chk_mov.pack(pady=5)

        self.btn_run = ctk.CTkButton(self.frame, text="🧹 BORRAR MARCA", fg_color="red", command=self.run)
        self.btn_run.pack(pady=10, fill="x", padx=50)
        
        self.lbl_stat = ctk.CTkLabel(self.frame, text="", text_color=C_ACCENT)
        self.lbl_stat.pack()
        self.prog = ctk.CTkProgressBar(self.frame, progress_color=C_ACCENT)
        self.prog.set(0); self.prog.pack(fill="x", padx=20, pady=5)

    def on_seek(self, val):
        if not hasattr(self.player, 'total_frames') or self.player.total_frames == 0: return
        frame = int(val)
        self.player.seek(frame)
        # Update time label
        if hasattr(self.player, 'fps') and self.player.fps > 0:
            cur_sec = int(frame / self.player.fps)
            tot_sec = int(self.player.total_frames / self.player.fps)
            self.lbl_time.configure(text=f"{cur_sec//60:02d}:{cur_sec%60:02d} / {tot_sec//60:02d}:{tot_sec%60:02d}")


    def load_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.in_path = f
            self.player.load(f)
            # Init slider
            if hasattr(self.player, 'total_frames'):
                self.slider.configure(from_=0, to=self.player.total_frames)
                self.slider.set(0)
                self.on_seek(0)


    def run(self):
        if not self.in_path: return
        self.btn_run.configure(state="disabled")
        
        def _t():
            try:
                cap = cv2.VideoCapture(self.in_path)
                w = int(cap.get(3)); h = int(cap.get(4))
                cap.release() 
                
                ext = "mov" if self.chk_mov.get() else "mp4"
                out_path = FileManager.get_unique_path(self.in_path, "Clean", ext)
                
                # Save Mask for Subprocess
                temp_mask = "temp_mask_{}.png".format(int(time.time()))
                mask = self.player.get_mask(w, h)
                cv2.imwrite(temp_mask, mask)
                del mask 

                # Call Isolated Process
                script_path = os.path.join(os.getcwd(), "src", "core", "remover_process.py")
                cmd_proc = [
                    sys.executable, script_path,
                    "--input", self.in_path,
                    "--mask", temp_mask,
                    "--output", out_path,
                ]
                if self.chk_mov.get():
                    cmd_proc.append("--mov")

                # Run Process and Monitor
                # We do NOT capture stderr here to avoid buffering issues on the UI side.
                # The worker script handles its own logging to a file.
                process = subprocess.Popen(cmd_proc, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        if line.startswith("PROGRESS:"):
                            try:
                                v = float(line.split(":")[1])
                                self.frame.after(0, lambda v=v: self.prog.set(v))
                                self.frame.after(0, lambda v=v: self.lbl_stat.configure(text=f"Procesando: {int(v*100)}%"))
                            except: pass
                
                if process.returncode != 0:
                    try:
                         # Try to read stderr if it fits in buffer, otherwise check log
                         err = process.stderr.read()
                    except: err = "Check logs"
                    print(f"Worker Error: {err}")
                    raise Exception(f"Worker process failed. {err}")
                
                # Cleanup temp mask
                if os.path.exists(temp_mask): os.remove(temp_mask)

                self.frame.after(0, lambda: self.btn_run.configure(state="normal"))
                self.frame.after(0, lambda: self.lbl_stat.configure(text=f"¡Guardado! {os.path.basename(out_path)}"))
                
            except Exception as e:
                print(f"Mark Err: {e}")
                self.frame.after(0, lambda: self.lbl_stat.configure(text="Error."))
                self.frame.after(0, lambda: self.btn_run.configure(state="normal"))
        
        threading.Thread(target=_t).start()
