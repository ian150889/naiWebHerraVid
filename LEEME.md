# NaiWeb Magic Studio Architect

Una suite profesional de herramientas multimedia potenciada por Inteligencia Artificial.

## Funcionalidades Principales

### 🎬 Editor de Video (NaiWeb Video)

- **Eliminación de Fondo:**
  - **Modo Mágico (U2Net):** Eliminación precisa usando IA robusta (Rembg).
  - **Modo Turbo (MediaPipe):** Procesamiento ultra rápido en tiempo real.
- **Tracking:** Sistema de seguimiento por puntos para máscaras dinámicas.
- **Formatos de Salida:** WebM (Transparente), Pantalla Verde (MP4), Secuencia PNG, MOV (Alpha).

### 🖼️ Editor de Imágenes (NaiWeb Image)

- **Eliminación Instantánea:** Borra el fondo de imágenes con un solo clic.
- **Conversión Inteligente:**
  - **PNG:** Mantiene transparencia.
  - **JPG:** Añade fondo blanco automáticamente.
  - **WEBP:** Optimizado para web.

### 🎹 Editor de Audio (NaiWeb Audio)

- **Efectos de Voz:** Presets divertidos como Ardilla, Villano, Demonio.
- **Pitch Shift:** Ajuste manual de tonalidad por semitonos sin afectar la duración.
- **Soporte:** Procesa tanto archivos de audio como pistas de audio de videos.

### 🧹 Removedor de Marcas (Magic Eraser)

- **Inpainting Neural:** Borra marcas de agua, logos u objetos no deseados.
- **Herramientas:**
  - **✏️ Lápiz:** Selección manual precisa.
  - **🪄 Varita Mágica:** Selección por inundación de color (Flood Fill).

### 🎙️ Clonador y Sintetizador de Voz (NaiWeb Voice)

- **Voces Neurales Latinas:** Selecciona entre voces naturales de **México, Argentina y Perú**.
- **Clonación de Voz (Biometría IA):**
  - Analiza tu voz mediante `librosa` para encontrar tu coincidencia neural.
  - Genera clones personalizados basados en tu tono (Pitch Matching).
  - Soporta grabación en vivo o subida de archivos.

### 📂 Gestor de Descargas

- Explorador integrado para ver, reproducir y gestionar todos los archivos generados.

## 📂 Arquitectura del Proyecto

El proyecto sigue una estructura modular profesional:

```
quitarFondos/
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
├── src/
│   ├── core/               # Motores lógicos (Video, Audio, TTS, Imagen)
│   ├── ui/                 # Interfaz Gráfica (CustomTkinter)
│   ├── utils/              # Configuración y utilidades
│   └── assets/             # Modelos y recursos
└── temp/                   # Archivos temporales
```

## Requisitos del Sistema

- **Sistema Operativo:** Linux (Recomendado/Probado), Windows, macOS.
- **Python:** 3.10 o superior.
- **FFmpeg:** Debe estar instalado en el sistema y accesible desde la terminal.

### Librerías Clave

- `customtkinter`: Interfaz gráfica moderna.
- `rembg` & `mediapipe`: Motores de segmentación IA.
- `edge-tts`: Síntesis de voz neural.
- `librosa`: Análisis de audio.
- `pygame` & `moviepy`: Procesamiento multimedia.

## Instalación y Uso

1. **Crear entorno virtual (Recomendado):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

   > **Nota para Linux:** Si encuentras conflictos con OpenCV, usa la versión headless:
   >
   > ```bash
   > pip uninstall opencv-python
   > pip install opencv-python-headless
   > ```

3. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

## Autores

Desarrollado para la suite **NaiWeb Magic Studio**.
