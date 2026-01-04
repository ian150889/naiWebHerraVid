import cv2
import sys
import argparse
import gc
import os
import subprocess
import time

def process_video(input_path, mask_path, output_path, is_mov):
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(mask_path):
        print(f"Error: Mask file not found: {mask_path}", file=sys.stderr)
        sys.exit(1)

    temp_video = output_path + "_temp.mp4"

    try:
        # Load Mask
        mask_img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if mask_img is None:
            print("Error: Could not load mask image.", file=sys.stderr)
            sys.exit(1)

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            print("Error: Could not open video.", file=sys.stderr)
            sys.exit(1)

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Resolution Warning
        if w > 1920 or h > 1080:
             print(f"Warning: High resolution video ({w}x{h}). Memory usage may be high.")

        # Resize mask if needed
        if mask_img.shape[:2] != (h, w):
            print(f"Resizing mask from {mask_img.shape[:2]} to {(h, w)}")
            mask_img = cv2.resize(mask_img, (w, h), interpolation=cv2.INTER_NEAREST)

        # Output Setup - ALWAYS use mp4v for temp to avoid OOM
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_video, fourcc, fps, (w, h))

        if not writer.isOpened():
             print("Error: Could not open video writer.", file=sys.stderr)
             sys.exit(1)

        print(f"Starting processing: {total_frames} frames.")
        
        # Processing Loop with Retry Logic
        cnt = 0
        retry_count = 0
        MAX_RETRIES = 5
        
        while True:
            ret, frame = cap.read()
            if not ret:
                # If we are effectively at the end (within 5 frames), stop.
                if total_frames > 0 and (total_frames - cnt) < 5:
                    break
                
                # Otherwise, try to retry reading (sometimes CV2 hiccups)
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    print(f"Warning: Stopped reading at frame {cnt}/{total_frames}. Stream might be corrupted.")
                    break
                print(f"Warning: Frame read failed at {cnt}. Retrying ({retry_count})...")
                time.sleep(0.1)
                continue
            
            retry_count = 0 # Reset on success
            cnt += 1
            
            # Inpaint
            clean_frame = cv2.inpaint(frame, mask_img, 3, cv2.INPAINT_TELEA)
            writer.write(clean_frame)

            # Progress update
            if total_frames > 0 and cnt % 10 == 0:
                progress = (cnt / total_frames) * 0.9 
                print(f"PROGRESS:{progress:.4f}")
                sys.stdout.flush()

            # Aggressive GC
            if cnt % 30 == 0:
                gc.collect()

        cap.release()
        writer.release()
        
        del mask_img
        del frame
        del clean_frame
        gc.collect()
        
        print("PROGRESS:0.92")
        print("Merging Audio (Final Step)...")
        sys.stdout.flush()

        # FFmpeg Merge
        c_v = "prores" if is_mov else "copy" # Changed from prores_ks to prores (standard)
        c_a = "pcm_s16le" if is_mov else "aac"
         
        cmd = [
            "ffmpeg", "-y", "-i", temp_video, "-i", input_path,
            "-c:v", c_v, "-c:a", c_a, 
            "-map", "0:v:0", "-map", "1:a:0?", "-shortest",
            "-preset", "medium" # Relax preset
        ]
        # Removed profile:v 3 to allow standard profile (lighter)
        if is_mov:
             # Force pix_fmt for compatibility
             cmd.extend(["-pix_fmt", "yuv422p10le"])
            
        cmd.append(output_path)
        
        log_path = output_path + ".log"
        with open(log_path, "w") as log_file:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=log_file)
            
        if res.returncode != 0:
            print(f"Critical: FFmpeg Audio Merge Failed! Return Code: {res.returncode}", file=sys.stderr)
            print(f"Check log file for details: {log_path}", file=sys.stderr)
            # DO NOT RENAME TEMP FILE. 
            # We want the process to error out so the UI shows "Error" instead of "Done" with a broken file.
            sys.exit(1)
        else:
            # Success
            if os.path.exists(temp_video): os.remove(temp_video)
            if os.path.exists(log_path): os.remove(log_path) 
            print("PROGRESS:1.0")
            print("Done.")

    except Exception as e:
        print(f"Critical Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        gc.collect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Watermark Remover Worker Process")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--mask", required=True, help="Mask image path")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--mov", action="store_true", help="Export as MOV")
    
    args = parser.parse_args()
    
    process_video(args.input, args.mask, args.output, args.mov)
