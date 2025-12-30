import cv2
import numpy as np
from rembg import remove, new_session
from src.utils.file_manager import FileManager

class ImageEngine:
    def __init__(self, stat_callback=None):
        self.stat = stat_callback
        self.session = None
        self.curr_model = ""

    def process(self, in_path, model="u2net", fmt="png"):
        try:
            img = cv2.imread(in_path)
            if img is None: return None
            
            # Session Handling
            if self.session is None or self.curr_model != model:
                if self.stat: self.stat(f"Cargando Modelo {model}...")
                self.session = new_session(model)
                self.curr_model = model
            
            # Process
            res = remove(img, session=self.session, alpha_matting=True)
            
            # Save
            if fmt == "jpg":
                # Compose white background for JPG
                bg = np.zeros_like(res); bg[:] = 255
                alpha = res[:,:,3] / 255.0
                fg = res[:,:,:3]
                comp = (fg * alpha[:,:,None] + bg[:,:,:3] * (1-alpha[:,:,None])).astype(np.uint8)
                out = FileManager.get_unique_path(in_path, "NoBG", "jpg")
                cv2.imwrite(out, comp)
            else:
                suffix = "NoBG_WebP" if fmt=="webp" else "NoBG"
                out = FileManager.get_unique_path(in_path, suffix, fmt)
                cv2.imwrite(out, res)
                
            return out
        except Exception as e:
            print(f"Error IMG: {e}")
            return None
