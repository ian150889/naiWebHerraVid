import customtkinter as ctk
import threading
import os
from src.core.tts_engine import TTSEngine
from src.core.audio_engine import AudioEngine
from src.utils.config import C_PANEL, C_ACCENT, FONT_BOLD
import os
import json
import customtkinter as ctk

CUSTOM_VOICES_FILE = "src/data/custom_voices.json"
import subprocess
import time

class VoiceTab:
    def __init__(self, parent):
        self.frame = parent
        self.tts = TTSEngine()
        self.samples = []
        self.rec_proc = None
        self.is_processing = False
        self.init_ui()

    def init_ui(self):
        # 1. Voice Clone Upload (ElevenLabs Style)
        # 1. Voice Clone Section (Upload OR Record)
        f_clone = ctk.CTkFrame(self.frame, fg_color=C_PANEL, corner_radius=10, border_width=2, border_color="#333")
        f_clone.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(f_clone, text="Clonar Voz (Analizador IA)", font=FONT_BOLD).pack(pady=5)
        
        # Tabs for Upload vs Record
        tab_cl = ctk.CTkTabview(f_clone, height=150, fg_color="transparent")
        tab_cl.pack(fill="x", padx=10, pady=5)
        tab_cl.add("🎤 GRABAR"); tab_cl.add("📂 SUBIR ARCHIVO")
        
        # --- TAB RECORD ---
        f_rec = tab_cl.tab("🎤 GRABAR")
        self.lbl_rec_count = ctk.CTkLabel(f_rec, text="Grabaciones: 0 (Mín 3) | Lista: []", text_color="orange")
        self.lbl_rec_count.pack(pady=5)
        
        f_btns = ctk.CTkFrame(f_rec, fg_color="transparent")
        f_btns.pack(pady=5)
        
        self.btn_rec = ctk.CTkButton(f_btns, text="🔴 GRABAR (Máx 60s)", fg_color="red", hover_color="darkred",
                                     command=self.record_sample)
        self.btn_rec.pack(side="left", padx=5)

        self.btn_stop_rec = ctk.CTkButton(f_btns, text="⏹️ CORTAR", state="disabled", fg_color="#333", width=80,
                                          command=self.stop_recording)
        self.btn_stop_rec.pack(side="left", padx=5)
        
        self.btn_analyze_rec = ctk.CTkButton(f_rec, text="🧠 ANALIZAR GRABACIONES", state="disabled", fg_color=C_ACCENT, text_color="black",
                                             command=self.analyze_recordings)
        self.btn_analyze_rec.pack(pady=5)

        # --- TAB UPLOAD ---
        f_up = tab_cl.tab("📂 SUBIR ARCHIVO")
        ctk.CTkButton(f_up, text="📂 SUBIR AUDIO DE REFERENCIA", fg_color="#333", hover_color="#444", 
                      command=self.upload_clone, height=40).pack(pady=20, padx=20, fill="x")

        self.lbl_clone_res = ctk.CTkLabel(f_clone, text="Esperando entrada de voz...", text_color="gray")
        self.lbl_clone_res.pack(pady=5)

        # 2. Text Input
        ctk.CTkLabel(self.frame, text="Texto a Voz (TTS)", font=FONT_BOLD).pack(pady=(10,5))
        self.txt_in = ctk.CTkTextbox(self.frame, height=120)
        self.txt_in.pack(fill="x", padx=10, pady=5)
        self.txt_in.insert("0.0", "Hola, soy NaiWeb. Mi voz ha sido ajustada a tu referencia.")

        # 3. Voice Settings
        f_set = ctk.CTkFrame(self.frame, fg_color="transparent")
        f_set.pack(fill="x", padx=10, pady=10)
        
        # Voice Selection
        voices = self.tts.get_voices()
        v_stock = [v['name'] for v in voices]
        self.voice_map_stock = {v['name']: v['id'] for v in voices}
        
        # Load Custom
        self.custom_map = self.load_custom_voices()
        v_custom = list(self.custom_map.keys())
        
        # Dropdown 1: Base Voices
        ctk.CTkLabel(f_set, text="Voz Neural (Base)").pack(side="left", padx=5)
        self.opt_base = ctk.CTkOptionMenu(f_set, values=["Seleccionar..."] + v_stock, command=self.on_base_select)
        self.opt_base.set("Seleccionar...")
        self.opt_base.pack(side="left", padx=5)
        
        # Dropdown 2: Cloned Voices
        ctk.CTkLabel(f_set, text="Mis Clones (Máx 5)").pack(side="left", padx=5)
        self.opt_clone = ctk.CTkOptionMenu(f_set, values=["Ninguno"] + v_custom, command=self.on_clone_select, fg_color="#444")
        self.opt_clone.set("Ninguno")
        self.opt_clone.pack(side="left", padx=5)
        
        self.selected_voice_id = None

        # 3. Post-Process FX (Cloning Sim)
        f_fx = ctk.CTkFrame(self.frame, fg_color="transparent")
        f_fx.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(f_fx, text="Modulador (Clonador)", font=FONT_BOLD).pack(anchor="w")
        self.v_fx = ctk.CTkOptionMenu(f_fx, values=["Sin Efecto (Voz Pura)", "Ardilla", "Goku / Villano", "Demonio"])
        self.v_fx.pack(pady=5, fill="x")

        # 4. Generate & Preview
        f_act = ctk.CTkFrame(self.frame, fg_color="transparent")
        f_act.pack(pady=20, fill="x", padx=50)
        
        self.btn_prev = ctk.CTkButton(f_act, text="▶️ PREVIEW", fg_color=C_PANEL, hover_color="#333", width=100,
                                      height=50, font=FONT_BOLD, command=self.preview)
        self.btn_prev.pack(side="left", padx=(0, 10))
        
        self.btn_gen = ctk.CTkButton(f_act, text="🗣️ GENERAR & GUARDAR", fg_color=C_ACCENT, text_color="black", 
                                     height=50, font=FONT_BOLD, command=self.generate)
        self.btn_gen.pack(side="left", fill="x", expand=True)
        
        
        self.lbl_stat = ctk.CTkLabel(self.frame, text="", text_color=C_ACCENT)
        self.lbl_stat.pack()
        
        # Progress Bar
        self.prog = ctk.CTkProgressBar(self.frame, width=400, mode="determinate")
        self.prog.set(0)
        self.prog.pack(pady=(5,0))
        
        self.lbl_prog = ctk.CTkLabel(self.frame, text="0%", font=("Arial", 10))
        self.lbl_prog.pack()

    def simulate_progress(self):
        if not self.is_processing: return
        # Simulate loading up to 95%
        cur = self.prog.get()
        if cur < 0.95:
             new_val = cur + 0.05
             self.prog.set(new_val)
             pct = int(new_val*100)
             self.lbl_prog.configure(text=f"{pct}%")
             
             # Update Contextual Labels
             if self.prog_mode == "analysis":
                 self.lbl_clone_res.configure(text=f"Analizando biometría... {pct}%", text_color=C_ACCENT)
             elif self.prog_mode == "gen":
                 self.lbl_stat.configure(text=f"Sintetizando... {pct}%", text_color=C_ACCENT)
                 
             self.frame.after(100, self.simulate_progress)

    def start_progress(self, mode="gen"):
        self.is_processing = True
        self.prog_mode = mode
        self.prog.set(0)
        self.simulate_progress()

    def stop_progress(self):
        self.is_processing = False
        self.prog.set(1.0)
        self.lbl_prog.configure(text="100%")
        
        # Reset labels final text is handled by caller


    def generate(self):
        text = self.txt_in.get("0.0", "end").strip()
        if not text: return
        
        self.btn_gen.configure(state="disabled", text="Generando (Internet)...")
        self.lbl_stat.configure(text="Sintetizando voz Neural...")
        
        def _t():
            # 1. Config TTS
            if self.selected_voice_id:
                self.tts.set_voice(self.selected_voice_id)
                # Pitch se pasa en save_to_file
            else:
                 # Check if we have a default default
                 # Fallback to first voice
                 pass 

            if not self.selected_voice_id:
                self.lbl_stat.configure(text="⚠️ Selecciona una voz.")
                self.btn_gen.configure(state="normal", text="🗣️ GENERAR & GUARDAR")
                return

            self.frame.after(0, lambda: self.start_progress("gen"))
            
            # Usar pitch seleccionado o default +0Hz
            pitch = getattr(self, "selected_pitch", "+0Hz")

            # 2. Gen Raw
            raw_path = self.tts.save_to_file(text, "VoiceClone_Raw", pitch=pitch)
            
            self.frame.after(0, self.stop_progress)
            
            if raw_path:
                fx = self.v_fx.get()
                if fx != "Sin Efecto (Voz Pura)":
                    self.lbl_stat.configure(text=f"Aplicando efecto {fx}...")
                    final_path = AudioEngine.apply_effects(raw_path, fx, 0)
                else:
                    final_path = raw_path
                
                self.btn_gen.configure(state="normal", text="🗣️ GENERAR & GUARDAR")
                if final_path:
                    self.lbl_stat.configure(text=f"¡Generado! {os.path.basename(final_path)}")
                else:
                    self.lbl_stat.configure(text="Error aplicando efectos.")
            else:
                self.btn_gen.configure(state="normal", text="🗣️ GENERAR & GUARDAR")
                self.lbl_stat.configure(text="Error TTS (Motor no disponible).")
        
        threading.Thread(target=_t).start()

    def preview(self):
        """
        [ES] Genera y reproduce el audio sin guardarlo permanentemente.
        [EN] Generates and plays audio without permanent saving.
        """
        text = self.txt_in.get("0.0", "end").strip()
        if not text: return
        
        self.btn_prev.configure(state="disabled", text="⏳")
        
        def _t():
            # 1. Config TTS
            if self.selected_voice_id:
                self.tts.set_voice(self.selected_voice_id)
            else:
                self.btn_prev.configure(state="normal", text="▶️ PREVIEW")
                return

            self.frame.after(0, lambda: self.start_progress("gen"))
            
            pitch = getattr(self, "selected_pitch", "+0Hz")

            # 2. Gen Temp
            # [ES] Usamos un archivo temporal oculto
            # [EN] Use a hidden temp file
            raw_path = self.tts.save_to_file(text, ".temp_preview", pitch=pitch)
            
            self.frame.after(0, self.stop_progress)
            
            if raw_path:
                fx = self.v_fx.get()
                if fx != "Sin Efecto (Voz Pura)":
                    final_path = AudioEngine.apply_effects(raw_path, fx, 0)
                else:
                    final_path = raw_path
                
                # Playback
                if final_path and os.path.exists(final_path):
                    try:
                        import pygame
                        pygame.mixer.music.load(final_path)
                        pygame.mixer.music.play()
                        # [ES] Esperar a que termine (Opcional, pero bloquea el hilo)
                        # [EN] Wait for finish (Optional, but blocks thread)
                        while pygame.mixer.music.get_busy():
                            pygame.time.Clock().tick(10)
                    except: pass
                    
                    # Cleanup
                    try: os.remove(final_path)
                    except: pass
            
            self.btn_prev.configure(state="normal", text="▶️ PREVIEW")
        
        threading.Thread(target=_t).start()


    def upload_clone(self):
        f = ctk.filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.ogg *.m4a")])
        if not f: return
        self.process_analysis(f)

    def record_sample(self):
        if self.rec_proc: return
        
        self.btn_rec.configure(state="disabled", text="🎙️ Grabando... (60s)")
        self.btn_stop_rec.configure(state="normal", fg_color="red")
        self.frame.update()
        
        # Asegurar directorio temp
        if not os.path.exists("temp"): os.makedirs("temp")
        
        fname = f"temp/sample_{len(self.samples)+1}.wav"
        
        # Grabación Asíncrona (Límite 60s)
        # usando -y para sobrescribir, -t 60 para duración máxima
        cmd = ["ffmpeg", "-y", "-f", "alsa", "-i", "default", "-t", "60", fname]
        try:
             self.rec_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             
             # Watcher thread to reset UI when done
             def _watch():
                 self.rec_proc.wait()
                 self.rec_proc = None
                 self.frame.after(0, lambda: self.finish_recording(fname))
                 
             threading.Thread(target=_watch).start()
             
        except Exception as e:
            print(f"Rec Error: {e}")
            self.stop_recording()

    def stop_recording(self):
        if self.rec_proc:
            self.rec_proc.terminate() # Send SIGTERM
            # UI reset handled by _watch -> finish_recording

    def finish_recording(self, fname):
        if os.path.exists(fname):
             # Check minimal size (avoid empty files)
             if os.path.getsize(fname) > 1000:
                 self.samples.append(fname)
        
        self.update_rec_ui()

    def update_rec_ui(self):
        c = len(self.samples)
        s_list = [os.path.basename(s) for s in self.samples]
        self.lbl_rec_count.configure(text=f"Grabaciones: {c} (Mín 3) | {s_list}", text_color=C_ACCENT if c>=3 else "orange")
        
        self.btn_rec.configure(state="normal", text="🔴 GRABAR (Máx 60s)")
        self.btn_stop_rec.configure(state="disabled", fg_color="#333")
        
        if c >= 3:
            self.btn_analyze_rec.configure(state="normal")

    def analyze_recordings(self):
        if not self.samples: return
        
        # Unir muestras
        merged = "temp/merged_samples.wav"
        list_file = "temp/flist.txt"
        
        # Crear archivo de lista
        with open(list_file, "w") as f:
            for s in self.samples: 
                # FFmpeg necesita rutas absolutas o relativas seguras
                # Como estamos en temp/, pero ejecutamos desde root, la ruta relativa temp/sample... está bien
                f.write(f"file '{os.path.abspath(s)}'\n")
            
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", merged],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                       
        if os.path.exists(merged):
             self.process_analysis(merged)


    def process_analysis(self, f_path):
        self.lbl_clone_res.configure(text="Analizando biometría de voz...", text_color=C_ACCENT)
        self.frame.after(0, lambda: self.start_progress("analysis"))
        
        def _t():
            try:
                # Ahora acepta 4 valores de retorno
                res = self.tts.analyze_and_match(f_path)
                if res[0] is None:
                     # Error msg is in res[3]
                     msg = res[3]
                     self.lbl_clone_res.configure(text=f"❌ {msg}", text_color="red")
                     self.frame.after(0, self.stop_progress)
                     return

                vid, vname, pitch, msg = res
                
                self.frame.after(0, lambda: self.save_custom_voice_dialog(os.path.basename(f_path), vid, pitch))
                self.lbl_clone_res.configure(text=f"✅ {msg}", text_color=C_ACCENT)
            
            except Exception as e:
                print(f"ANALYZE ERROR: {e}")
                self.lbl_clone_res.configure(text=f"❌ Error interno: {str(e)[:40]}...", text_color="red")
            
            finally:
                 self.frame.after(0, self.stop_progress)
        
        threading.Thread(target=_t).start()

    
    # ... Rest of methods ...
    
    
    def load_custom_voices(self):
        if os.path.exists(CUSTOM_VOICES_FILE):
            try:
                with open(CUSTOM_VOICES_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

    def on_base_select(self, val):
        if val in self.voice_map_stock:
            self.selected_voice_id = self.voice_map_stock[val]
            self.opt_clone.set("Ninguno") # Clear other

    def on_clone_select(self, val):
        # Refresh map to be safe
        # self.custom_map = self.load_custom_voices() (Too slow for select)
        if val in self.custom_map:
            self.selected_voice_id = self.custom_map[val]
            self.opt_base.set("Seleccionar...") # Clear other

    def save_custom_voice_dialog(self, default_name, vid, pitch=None):
        # Limit Check
        keys = list(self.custom_map.keys())
        if len(keys) >= 5:
             del self.custom_map[keys[0]]

        dialog = ctk.CTkInputDialog(text="Nombre para este Clon de Voz:", title="Guardar Clon")
        name = dialog.get_input()
        if name:
            full_name = f"👤 {name}"
            self.custom_map[full_name] = vid
            
            try:
                with open(CUSTOM_VOICES_FILE, "w") as f: json.dump(self.custom_map, f)
            except: pass
            
            # Explicit Update
            new_values = ["Ninguno"] + list(self.custom_map.keys())
            self.opt_clone.configure(values=new_values)
            self.opt_clone.set(full_name)
            self.selected_voice_id = vid
            self.opt_base.set("Seleccionar...") # Clear base
