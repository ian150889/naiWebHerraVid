import cv2
import subprocess
import os
import numpy as np
import urllib.request
from src.utils.file_manager import FileManager

# Try imports
try:
    import mediapipe as mp
    MP_AVAIL = True
except: MP_AVAIL = False

try:
    from rembg import remove, new_session
    REMBG_AVAIL = True
except: REMBG_AVAIL = False

class VideoEngine:
    def __init__(self, callback_progress=None, callback_status=None):
        self.upd = callback_progress
        self.stat = callback_status
        self.stop_flag = False
        self.rembg_session = None
        self.current_model = None

    def load_rembg(self, model_name):
        if not REMBG_AVAIL: return False
        if self.rembg_session is None or self.current_model != model_name:
            if self.stat: self.stat(f"Cargando Modelo AI {model_name}...")
            self.rembg_session = new_session(model_name)
            self.current_model = model_name
        return True

    def process_video(self, in_path, engine="turbo", model="u2net", out_fmt="webm", wand_mode=False, tracking_points=None, thresh=0.5, soft=5):
        if not os.path.exists(in_path): return
        
        # Setup Cap
        cap = cv2.VideoCapture(in_path)
        w = int(cap.get(3)); h = int(cap.get(4)); fps = cap.get(5)
        tot = int(cap.get(7))
        
        # Configure Output Pipe
        pipe, out_path, seq_dir = self._get_pipe(in_path, out_fmt, w, h, fps)
        
        # Setup Engine
        seg = None
        if engine == "turbo" and MP_AVAIL:
            m_path = "src/assets/models/selfie_segmenter.tflite"
            if not os.path.exists(m_path):
                if self.stat: self.stat("Descargando modelo Turbo...")
                urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite", m_path)
            op = mp.tasks.vision.ImageSegmenterOptions(base_options=mp.tasks.BaseOptions(model_asset_path=m_path), running_mode=mp.tasks.vision.RunningMode.IMAGE, output_confidence_masks=True)
            seg = mp.tasks.vision.ImageSegmenter.create_from_options(op)
        elif engine == "magic":
            self.load_rembg(model)
            
        # Tracking Vars
        lk_params = dict(winSize=(15,15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,10,0.03))
        prev_gray = None
        if wand_mode and tracking_points:
             curr_pts = np.array(tracking_points, dtype=np.float32).reshape(-1, 1, 2)
        else: curr_pts = None

        cnt = 0
        while cap.isOpened() and not self.stop_flag:
            ret, frame = cap.read()
            if not ret: break
            cnt += 1
            
            # 1. Mask Generation
            mask = np.zeros((h,w), dtype=np.uint8)
            if engine == "magic" and REMBG_AVAIL:
                # Optimized: Convert only once
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = remove(rgb, session=self.rembg_session, alpha_matting=True)
                mask = res[:,:,3] # Alpha channel
                # Thresholding
                _, mask = cv2.threshold(mask, int(thresh*255), 255, cv2.THRESH_TOZERO)
                
            elif engine == "turbo" and seg:
                res = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                if res.confidence_masks:
                    m_float = res.confidence_masks[0].numpy_view()
                    mask = (m_float > thresh).astype(np.uint8) * 255

            # 2. Wand Tracking Overlay
            if wand_mode and curr_pts is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if prev_gray is not None:
                     p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, gray, curr_pts, None, **lk_params)
                     good_new = p1[st==1]
                     if len(good_new) > 0:
                         curr_pts = good_new.reshape(-1, 1, 2)
                         # Draw tracked mask
                         for pt in curr_pts:
                             cv2.circle(mask, (int(pt[0][0]), int(pt[0][1])), 30, 255, -1)
                prev_gray = gray

            # 3. Feathering
            if soft > 1 and soft % 2 == 1:
                mask = cv2.GaussianBlur(mask, (soft, soft), 0)

            # 4. Output Writing
            self._write_frame(frame, mask, out_fmt, pipe, seq_dir, cnt)
            
            # Progress
            if cnt % 5 == 0 and self.upd:
                self.upd(cnt/tot, f"Procesando: {int(cnt/tot*100)}%")

        cap.release()
        if pipe: pipe.stdin.close(); pipe.wait()
        
        # Audio Muxing
        if not self.stop_flag and out_fmt != "png_seq":
            self._mux_audio(in_path, out_path, out_fmt)
            
        return out_path if out_fmt != "png_seq" else seq_dir

    def _get_pipe(self, in_path, fmt, w, h, fps):
        if fmt == "png_seq":
            return None, None, FileManager.get_seq_dir(in_path)
            
        suffix = "WebM" if fmt == "webm" else "Green" if fmt == "green" else "Alpha"
        ext = "webm" if fmt == "webm" else "mp4" if fmt == "green" else "mov"
        
        out_path = FileManager.get_unique_path(in_path, suffix, ext)
        
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-s", f"{w}x{h}", 
               "-pix_fmt", "bgra" if fmt!="green" else "bgr24", "-r", str(fps), "-i", "-"]
               
        if fmt == "webm":
            cmd.extend(["-c:v", "libvpx-vp9", "-b:v", "2M", "-pix_fmt", "yuva420p", out_path])
        elif fmt == "green":
            cmd.extend(["-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", out_path])
        else: # mov alpha aka png
            cmd.extend(["-c:v", "png", "-pix_fmt", "rgba", out_path])
            
        return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE), out_path, None

    def _write_frame(self, frame, mask, fmt, pipe, seq_dir, cnt):
        if fmt == "green":
            bg = np.zeros_like(frame); bg[:] = (0, 255, 0)
            m_norm = mask / 255.0
            m3 = np.dstack((m_norm, m_norm, m_norm))
            fin = (frame * m3 + bg * (1-m3)).astype(np.uint8)
            pipe.stdin.write(fin.tobytes())
        else:
            b,g,r = cv2.split(frame)
            b = cv2.bitwise_and(b, b, mask=mask)
            g = cv2.bitwise_and(g, g, mask=mask)
            r = cv2.bitwise_and(r, r, mask=mask)
            fin = cv2.merge((b, g, r, mask))
            
            if fmt == "png_seq":
                cv2.imwrite(os.path.join(seq_dir, f"frame_{cnt:05d}.png"), fin)
            else:
                pipe.stdin.write(fin.tobytes())

    def _mux_audio(self, src, dst, fmt):
        if self.stat: self.stat("Uniendo Audio...")
        temp = dst + "_temp.mkv"
        
        # Verify source exists before rename
        if not os.path.exists(dst):
            print(f"Error: Output file {dst} not found.")
            return

        os.rename(dst, temp)
        
        # Map 1:a:0? makes audio optional so it doesn't fail if src has no audio
        cmd = ["ffmpeg", "-y", "-i", temp, "-i", src, "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0?", "-shortest"]
        
        if fmt == "webm": cmd.extend(["-c:a", "libvorbis", dst])
        elif fmt == "green": cmd.extend(["-c:a", "aac", dst])
        else: cmd.extend(["-c:a", "pcm_s16le", dst]) # MOV/ProRes usually pcm
        
        # Run and capture output for debug
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if res.returncode != 0:
             print(f"Mux Warning: {res.stderr.decode()}")
             # Restore temp if failed
             if os.path.exists(temp):
                 if os.path.exists(dst): os.remove(dst)
                 os.rename(temp, dst)
        else:
            if os.path.exists(temp): os.remove(temp)
