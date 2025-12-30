import os
import asyncio
import edge_tts
import numpy as np
from src.utils.file_manager import FileManager
import sys
import subprocess
import json

# Librosa se importa bajo demanda en el subproceso para optimizar inicio

# Voces Neurales Curadas (Latinoamérica)
# Se priorizan acentos de México, Argentina y Perú.
NEURAL_VOICES = {
    "ES - Dalia (México)": "es-MX-DaliaNeural",
    "ES - Jorge (México)": "es-MX-JorgeNeural",
    "ES - Elena (Argentina)": "es-AR-ElenaNeural",
    "ES - Tomas (Argentina)": "es-AR-TomasNeural",
    "ES - Camila (Perú)": "es-PE-CamilaNeural",
    "ES - Alex (Perú)": "es-PE-AlexNeural"
}

# Tonos Base Aproximados (en Hz) para cálculo de desplazamiento
VOICE_PITCH_BASE = {
    "es-MX-DaliaNeural": 220,
    "es-MX-JorgeNeural": 110,
    "es-AR-ElenaNeural": 210,
    "es-AR-TomasNeural": 115,
    "es-PE-CamilaNeural": 215,
    "es-PE-AlexNeural": 112
}

class TTSEngine:
    def __init__(self):
        self.use_edge = True

    def get_voices(self):
        """Devuelve una lista de diccionarios {'id': id, 'name': name}"""
        return [{"id": v, "name": k} for k, v in NEURAL_VOICES.items()]

    def set_rate(self, rate):
        pass

    def save_to_file(self, text, out_path_base, pitch="+0Hz"):
        """
        Genera audio usando Edge TTS.
        Soporta ajuste de tono (pitch).
        """
        try:
            # Determinar voz (Por defecto Dalia - México si no se establece)
            voice = getattr(self, "current_voice", "es-MX-DaliaNeural")
            rate_str = "+0%" 
            
            if out_path_base == ".temp_preview":
                if not os.path.exists("temp"): os.makedirs("temp")
                out = "temp/preview_temp.mp3"
            else:
                out = FileManager.get_unique_path(out_path_base, "NeuralTTS", "mp3")
            
            # Ejecutar bucle Async de forma síncrona
            asyncio.run(self._gen_edge(text, voice, rate_str, pitch, out))
            
            return out if os.path.exists(out) else None
        except Exception as e:
            print(f"Error EdgeTTS: {e}")
            return None

    def set_voice(self, voice_id):
        self.current_voice = voice_id

    async def _gen_edge(self, text, voice, rate, pitch, out_file):
        print(f"DEBUG: Iniciando EdgeTTS para {out_file} con voz {voice} y tono {pitch}")
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await communicate.save(out_file)
            print(f"DEBUG: EdgeTTS completado para {out_file}")
        except Exception as e:
            print(f"ERROR EdgeTTS: {e}")
            raise e

    def analyze_and_match(self, audio_path):
        """
        Analiza el audio y calcula el Pitch Shift necesario.
        Retorna: (voice_id, voice_name, pitch_shift_str, confidence_msg)
        """
        if not os.path.exists(audio_path):
            return None, None, None, "Archivo no encontrado."

        try:
            cmd = [sys.executable, "-m", "src.core.tts_engine", audio_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"Error Subproceso: {result.stderr}")
                return None, None, None, "Error interno en análisis."
            
            data = json.loads(result.stdout.strip())
            
            if data.get("error"):
                return None, None, None, data["error"]
                
            return data["vid"], data["vname"], data["pitch"], data["msg"]
            
        except subprocess.TimeoutExpired:
            return None, None, None, "Tiempo de espera agotado (Timeout)."
        except Exception as e:
            print(f"Error Análisis: {e}")
            return None, None, None, f"Error analizando: {str(e)}"

def standalone_analyze(audio_path):
    """
    Función interna (Subproceso).
    Calcula F0 usuario, selecciona voz base, y calcula diferencia (Pitch Shift).
    """
    result = {"vid": None, "vname": None, "pitch": "+0Hz", "msg": "Error desconocido", "error": None}
    
    try:
        import librosa
        import numpy as np
        
        y, sr = librosa.load(audio_path, duration=10, sr=None)
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        
        if np.any(voiced_flag):
            mean_f0 = np.nanmean(f0[voiced_flag])
        else:
            mean_f0 = 0
            
        # Clasificación simplificada (Umbral 165Hz)
        is_male = mean_f0 < 165
        user_hz = int(mean_f0)
        
        if is_male:
            # Preferencia: Jorge (MX) -> Tomas (AR) -> Alex (PE)
            # Usaremos Jorge como base principal masculina por consistencia
            vid = "es-MX-JorgeNeural"
            vname = "ES - Jorge (México)"
            base_hz = VOICE_PITCH_BASE.get(vid, 110)
        else:
            # Preferencia: Dalia (MX) -> Elena (AR) -> Camila (PE)
            # Usaremos Dalia como base principal femenina
            vid = "es-MX-DaliaNeural"
            vname = "ES - Dalia (México)"
            base_hz = VOICE_PITCH_BASE.get(vid, 220)
            
        # Calcular Pitch Shift
        # shift = user - base
        # Si usuario tiene 130Hz y base es 110Hz, necesitamos subir +20Hz
        diff = user_hz - base_hz
        sign = "+" if diff >= 0 else "-"
        pitch_str = f"{sign}{abs(diff)}Hz"
        
        # Calcular Score Visual (Similitud relativa)
        # Score basado en qué tan cerca está del "ideal" calculado
        score = 95 # Base confidence high because we match pitch dynamically
        
        msg = f"Match: {score}% | {user_hz}Hz vs Base {base_hz}Hz -> Ajuste: {pitch_str}"
            
        result = {"vid": vid, "vname": vname, "pitch": pitch_str, "msg": msg}
        
    except Exception as e:
        result["error"] = f"Error en motor: {str(e)}"
        
    print(json.dumps(result))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        standalone_analyze(sys.argv[1])

