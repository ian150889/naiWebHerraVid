import customtkinter as ctk

# --- CONSTANTES DE TEMA / THEME CONSTANTS ---
# Centralizamos los colores para cambiar el estilo fácilmente.
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

C_BG = "#161616"       # Fondo Principal (Casi negro)
C_PANEL = "#252525"    # Paneles (Gris oscuro para diferenciar áreas)
C_ACCENT = "#00E676"   # Acento (Verde Neón para acciones importantes)
C_TEXT = "#E0E0E0"     # Texto (Blanco suave para lectura cómoda)

FONT_MAIN = ("Roboto", 12)
FONT_BOLD = ("Roboto", 12, "bold")
FONT_TITLE = ("Roboto", 24, "bold")

# --- LOCALIZACIÓN / LOCALIZATION ---
LOCALES = {
    "ES": {
        "app_title": "NaiWeb Magic Studio",
        "tab_vid": "VIDEO", 
        "tab_img": "IMAGENES", 
        "tab_aud": "AUDIO", 
        "tab_mark": "QUITAR MARCA DE AGUA",
        "tab_voice": "CLONAR VOZ",
        "tab_clones": "MIS DESCARGAS",
        
        "btn_load": "📂 IMPORTAR MEDIA",
        "btn_run": "🚀 INICIAR PROCESO",
        
        "wand_on": "🪄 Varita (Activa)",
        "wand_off": "🪄 Varita (Inactiva)",
        
        "status_ready": "Sistema Listo.",
        "status_proc": "Procesando...",
        "status_done": "¡Listo!",
        
        "lang": "🇺🇸 EN"
    },
    "EN": {
        "app_title": "NaiWeb Magic Studio",
        "tab_vid": "VIDEO", 
        "tab_img": "IMAGE", 
        "tab_aud": "AUDIO", 
        "tab_mark": "WATERMARK REMOVER",
        "tab_voice": "VOICE CLONER",
        "tab_clones": "MY DOWNLOADS",
        
        "btn_load": "📂 IMPORT MEDIA",
        "btn_run": "🚀 START PROCESS",
        
        "wand_on": "🪄 Wand (Active)",
        "wand_off": "🪄 Wand (Inactive)",
        
        "status_ready": "System Ready.",
        "status_proc": "Processing...",
        "status_done": "Done!",
        
        "lang": "🇪🇸 ES"
    }
}
