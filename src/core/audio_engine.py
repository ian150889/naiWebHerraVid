import subprocess
import os
import math
from src.utils.file_manager import FileManager

class AudioEngine:
    @staticmethod
    def apply_effects(in_path, preset="Normal", semitones=0.0):
        if not os.path.exists(in_path): return None
        
        # Determine filters
        af = []
        
        # 1. Semitones (Pitch Shift without speed change if possible, or simple speed/pitch)
        # Using asetrate + atempo is the standard way without specialized libraries.
        # Ratio = 2^(n/12)
        if semitones != 0:
            ratio = 2 ** (semitones / 12.0)
            rate = int(44100 * ratio)
            # Filter: Change rate (pitch+speed) -> Correct speed (tempo) -> Resample
            af.append(f"asetrate={rate},atempo={1/ratio},aresample=44100")
            
        # 2. Presets (Simple overrides)
        if preset == "Ardilla": # Chipmunk
            af = ["asetrate=22050*2,aresample=44100"] # Simple 2x speed+pitch
        elif preset == "Goku / Villano": # Deep
            af = ["asetrate=44100*0.7,atempo=1.4,aresample=44100"] # 0.7x pitch, speed corrected
        elif preset == "Demonio":
            af = ["asetrate=44100*0.5,aresample=44100"] # Slow is scary
            
        out_path = FileManager.get_unique_path(in_path, f"FX_{preset}", "wav")
        
        cmd = ["ffmpeg", "-y", "-i", in_path]
        if af:
            cmd.extend(["-af", ",".join(af)])
            
        cmd.extend(["-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", out_path])
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return out_path
        except Exception as e:
            print(f"Audio Error: {e}")
            return None
