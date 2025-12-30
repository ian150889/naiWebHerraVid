import os
import time

class FileManager:
    @staticmethod
    def get_unique_path(base, suffix, ext):
        """
        Genera una ruta única en la carpeta 'Descargas' para evitar sobrescribir archivos.
        Formato: Descargas/NombreBase_Sufijo_001.ext
        """
        f = "Descargas"
        if not os.path.exists(f): os.makedirs(f)
        
        # Limpiar nombre base
        if base:
            b = os.path.splitext(os.path.basename(base))[0]
            b = "".join([c for c in b if c.isalnum() or c in (' ','_','-')]).strip()
        else:
            b = "Output"
            
        # Buscar el primer número disponible
        for i in range(1, 1000):
            p = os.path.join(f, f"{b}_{suffix}_{i:03d}.{ext}")
            if not os.path.exists(p): return p
            
        # Fallback con timestamp si hay más de 1000 archivos iguales
        return os.path.join(f, f"{b}_{suffix}_{int(time.time())}.{ext}")

    @staticmethod
    def get_seq_dir(base):
        """Creates a unique directory for PNG sequences."""
        f = "Descargas"
        if not os.path.exists(f): os.makedirs(f)
        
        b = os.path.splitext(os.path.basename(base))[0]
        for i in range(1, 1000):
            sd = os.path.join(f, f"{b}_Frames_{i:03d}")
            if not os.path.exists(sd):
                os.makedirs(sd)
                return sd
        return os.path.join(f, f"{b}_Frames_{int(time.time())}")
