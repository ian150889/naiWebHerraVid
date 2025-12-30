import customtkinter as ctk
import os
from PIL import Image
from src.utils.config import LOCALES, C_PANEL, C_BG, C_ACCENT, C_TEXT, FONT_TITLE
from src.ui.video_tab import VideoTab
from src.ui.image_tab import ImageTab
from src.ui.audio_tab import AudioTab
from src.ui.mark_tab import MarkTab
from src.ui.audio_tab import AudioTab
from src.ui.mark_tab import MarkTab
from src.ui.voice_tab import VoiceTab
from src.ui.downloads_tab import DownloadsTab

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1280x900")
        self.title("NaiWeb Magic Studio Architect")
        self.configure(fg_color=C_BG)
        
        self.lang = "ES"
        self.init_ui()

    def tr(self, key):
        return LOCALES[self.lang].get(key, key)

    def init_ui(self):
        # 1. Header
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)
        
        # Logo Check
        logo_path = "img_logo/logNaiWeb.png"
        if os.path.exists(logo_path):
            try:
                im = Image.open(logo_path)
                im.thumbnail((350, 80)) # Slightly bigger
                cim = ctk.CTkImage(im, im, (im.width, im.height))
                ctk.CTkLabel(top, text="", image=cim).pack(side="top", pady=10) # Center Top
            except:
                ctk.CTkLabel(top, text=self.tr("app_title"), font=FONT_TITLE, text_color=C_ACCENT).pack(side="top", pady=10)
        else:
            ctk.CTkLabel(top, text=self.tr("app_title"), font=FONT_TITLE, text_color=C_ACCENT).pack(side="top", pady=10)

        # Lang Toggle (Absolute Positioning or Frame)
        # Using a frame for header structure
        # Let's repack button to right
        self.btn_lang = ctk.CTkButton(self, text=self.tr("lang"), width=60, fg_color=C_PANEL, command=self.toggle_lang)
        self.btn_lang.place(relx=0.95, rely=0.02, anchor="ne")

        # 2. Tabs
        self.tabs = ctk.CTkTabview(self, fg_color=C_PANEL, corner_radius=15, 
                                   segmented_button_fg_color=C_BG, 
                                   segmented_button_selected_color=C_ACCENT,
                                   segmented_button_selected_hover_color=C_ACCENT,
                                   text_color=C_TEXT)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)

        # Create Tabs
        self.tab_map = {
            "tab_vid": VideoTab,
            "tab_img": ImageTab,
            "tab_aud": AudioTab,
            "tab_mark": MarkTab,
            "tab_voice": VoiceTab,
            "tab_clones": DownloadsTab
        }
        
        for k in self.tab_map:
            name = self.tr(k)
            self.tabs.add(name)
            # Initialize Tab Class inside the tab frame
            self.tab_map[k](self.tabs.tab(name))

    def toggle_lang(self):
        # Requires restart for full logic, but we can switch button text
        self.lang = "EN" if self.lang == "ES" else "ES"
        self.btn_lang.configure(text=self.tr("lang"))
        # Ideally we'd reload UI, but for architect version simplicity, we just toggle state for next new windows
