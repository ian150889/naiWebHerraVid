import customtkinter as ctk
import os
import json
from src.utils.config import C_PANEL, C_ACCENT, FONT_BOLD

CLONES_FILE = "clones.json"

class ClonesTab:
    def __init__(self, parent):
        self.frame = parent
        self.clones = self.load_clones()
        self.init_ui()

    def load_clones(self):
        if os.path.exists(CLONES_FILE):
            try:
                with open(CLONES_FILE, "r") as f: return json.load(f)
            except: return []
        return []

    def save_clones(self):
        with open(CLONES_FILE, "w") as f: json.dump(self.clones, f)

    def add_clone(self, name, voice_id, desc):
        self.clones.append({"name": name, "voice_id": voice_id, "desc": desc})
        self.save_clones()
        self.refresh_list()

    def init_ui(self):
        # Header
        top = ctk.CTkFrame(self.frame, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(top, text="Mis Voces Clonadas (Simuladas)", font=FONT_BOLD).pack(side="left")
        ctk.CTkButton(top, text="🔄 Actualizar", width=80, command=self.refresh_list).pack(side="right")

        # List Area
        self.scroll = ctk.CTkScrollableFrame(self.frame, fg_color=C_PANEL)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh_list()

    def refresh_list(self):
        for w in self.scroll.winfo_children(): w.destroy()
        
        if not self.clones:
            ctk.CTkLabel(self.scroll, text="No tienes voces guardadas.\nVe a la pestaña 'CLONAR VOZ' y haz un análisis.", text_color="gray").pack(pady=20)
            return

        for idx, c in enumerate(self.clones):
            item = ctk.CTkFrame(self.scroll, fg_color="#333", corner_radius=5)
            item.pack(fill="x", pady=2, padx=5)
            
            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=5)
            
            ctk.CTkLabel(info, text=c.get("name", "Sin nombre"), font=FONT_BOLD).pack(anchor="w")
            ctk.CTkLabel(info, text=c.get("desc", ""), text_color="gray", font=("Arial", 10)).pack(anchor="w")
            
            ctk.CTkLabel(item, text=f"ID: {c.get('voice_id','?')}", text_color=C_ACCENT).pack(side="right", padx=10)

