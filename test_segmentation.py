
import numpy as np
import mediapipe as mp
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = 'selfie_segmenter.tflite'

def test_model():
    print("Testing MediaPipe Segmentation Headless...")
    
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model file {MODEL_PATH} not found.")
        return

    try:
        # Create an options object
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.ImageSegmenterOptions(base_options=base_options,
                                              output_category_mask=True)
        
        # Create the image segmenter
        with vision.ImageSegmenter.create_from_options(options) as segmenter:
            
            # Create a simple dummy image (RGB)
            # 256x256 image, slightly gray
            fake_frame = np.full((256, 256, 3), 100, dtype=np.uint8)
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=fake_frame)
            
            # Segment
            segmentation_result = segmenter.segment(mp_image)
            mask_np = segmentation_result.category_mask.numpy_view()
            
            print(f"Success! Model loaded.")
            print(f"Mask Shape: {mask_np.shape}")
            print(f"Mask Unique Values: {np.unique(mask_np)}")
            
            if len(np.unique(mask_np)) == 1:
                print("NOTE: Mask has only one value (expected for blank image, but confirms logic runs).")
            else:
                print("Mask has multiple values.")

    except Exception as e:
        print(f"CRITICAL ERROR during segmentation: {e}")

if __name__ == "__main__":
    test_model()
