import tkinter as tk
import customtkinter as ctk
import cv2
import numpy as np
import threading
import subprocess
import os
import time
from PIL import Image, ImageTk
from src.utils.config import C_PANEL, C_ACCENT, FONT_BOLD

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False

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
        
        self.path=None; self.playing=False; self.aud="temp.wav"
        self.points=[] # Video Wand Tracking points
        self.strokes=[] # Pencil strokes
        self.masks=[]   # Magic Wand flood masks
        self.curr_fr=None
        
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.drag)

    def set_mode(self, m):
        self.mode = m
        self.draw_ov()

    def click(self, e):
        if self.mode=="wand_track": 
            self.points.append(self.map(e.x,e.y)); self.draw_ov()
        elif self.mode=="pencil": 
            self.strokes.append([self.map(e.x,e.y)]); self.draw_ov()
        elif self.mode=="flood":
             if self.curr_fr is None: return
             h, w = self.curr_fr.shape[:2]
             
             # Flood Fill Logic
             mask = np.zeros((h+2, w+2), np.uint8)
             flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE
             diff = (45, 45, 45) # Tolerance adjusted
             
             nx, ny = self.map(e.x, e.y)
             ix, iy = int(nx*w), int(ny*h)
             
             if 0 <= ix < w and 0 <= iy < h:
                 cv2.floodFill(self.curr_fr, mask, (ix, iy), 0, diff, diff, flags)
                 real_mask = mask[1:-1, 1:-1]
                 
                 if np.count_nonzero(real_mask) > 0:
                     self.masks.append(real_mask)
                 else:
                     # Fallback Dot
                     fb = np.zeros((h, w), np.uint8)
                     cv2.circle(fb, (ix, iy), 15, 255, -1)
                     self.masks.append(fb)
                 self.draw_ov()

    def drag(self, e):
        if self.mode=="wand_track": self.points.append(self.map(e.x,e.y)); self.draw_ov()
        elif self.mode=="pencil" and self.strokes: self.strokes[-1].append(self.map(e.x,e.y)); self.draw_ov()

    def map(self, cx, cy):
        if self.curr_fr is None: return (0,0)
        h,w = self.curr_fr.shape[:2]
        cw = self.canvas.winfo_width(); ch = self.canvas.winfo_height()
        r = min(cw/w, ch/h)
        nw, nh = int(w*r), int(h*r)
        ox, oy = (cw-nw)//2, (ch-nh)//2
        return (max(0, min(1, (cx-ox)/nw)), max(0, min(1, (cy-oy)/nh)))

    def demap(self, nx, ny):
        if self.curr_fr is None: return (0,0)
        h,w = self.curr_fr.shape[:2]
        cw = self.canvas.winfo_width(); ch = self.canvas.winfo_height()
        r = min(cw/w, ch/h)
        nw, nh = int(w*r), int(h*r)
        ox, oy = (cw-nw)//2, (ch-nh)//2
        return (ox + nx*nw, oy + ny*nh)

    def draw_ov(self):
        self.canvas.delete("ov")
        
        # 1. Tracking Points
        if self.mode=="wand_track" or self.points:
            for p in self.points:
                cx, cy = self.demap(*p)
                self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill=C_ACCENT, outline=C_ACCENT, tags="ov")

        # 2. Pencil Strokes
        for s in self.strokes:
            if len(s)>1:
                flat=[]
                for p in s: flat.extend(self.demap(*p))
                self.canvas.create_line(flat, fill="red", width=5, capstyle="round", smooth=True, tags="ov")
                
        # 3. Flood Masks (Polygon)
        h,w = 0,0
        if self.curr_fr is not None: h,w = self.curr_fr.shape[:2]
        
        for m in self.masks:
             cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
             for c in cnts:
                 flat_poly = []
                 for pt in c:
                     px, py = pt[0]
                     nx, ny = px/w, py/h
                     cx, cy = self.demap(nx, ny)
                     flat_poly.extend([cx, cy])
                 
                 if len(flat_poly) > 4:
                     # Robust rendering for Linux (No stipple)
                     self.canvas.create_polygon(flat_poly, outline=C_ACCENT, fill="", width=3, tags="ov")

    def get_mask(self, w, h):
        m = np.zeros((h, w), dtype=np.uint8)
        # Pencil
        for s in self.strokes:
            pts = np.array([(int(p[0]*w), int(p[1]*h)) for p in s], np.int32)
            if len(pts)>1: cv2.polylines(m, [pts], False, 255, 20)
            
        # Wand
        for bm in self.masks:
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
        self.stop(); self.path=p; self.points=[]; self.strokes=[]; self.masks=[]
        c=cv2.VideoCapture(p); r,f=c.read(); c.release()
        if r: self.canvas.update(); self.show(f)

    def play(self):
        if not self.path or self.playing: return
        self.playing = True
        if PYGAME_AVAILABLE:
            try: 
                 subprocess.run(["ffmpeg","-y","-i",self.path,"-vn","-acodec","pcm_s16le","-ar","44100","-ac","2",self.aud], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                 if os.path.exists(self.aud): 
                     pygame.mixer.music.load(self.aud)
                     pygame.mixer.music.play()
            except: pass
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
