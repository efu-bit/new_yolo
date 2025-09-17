import os
import sys
from typing import List, Dict, Tuple, Optional

import numpy as np
from PIL import Image
import torch

# Add the sam2 directory to Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sam2_root = os.path.dirname(current_dir)  # backend/sam2
if sam2_root not in sys.path:
    sys.path.insert(0, sam2_root)

# Constants for model files (SAM2 interprets these as relative to the package)
CONFIG_FILE = "configs/sam2.1/sam2.1_hiera_l.yaml"
CHECKPOINT_FILE = "../checkpoints/sam2.1_hiera_large.pt"

try:
    from sam2.build_sam import build_sam2
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
except ImportError:
    # Fallback: try to import from current directory
    try:
        from .build_sam import build_sam2
        from .automatic_mask_generator import SAM2AutomaticMaskGenerator
    except ImportError:
        # Last resort: try absolute imports
        from build_sam import build_sam2
        from automatic_mask_generator import SAM2AutomaticMaskGenerator

_model = None
_mask_gen = None

def _mask_to_bbox(mask: np.ndarray) -> Dict[str, int]:
    y_idx, x_idx = np.where(mask)
    if x_idx.size == 0 or y_idx.size == 0:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    x_min, x_max = int(x_idx.min()), int(x_idx.max())
    y_min, y_max = int(y_idx.min()), int(y_idx.max())
    return {
        "x": x_min,
        "y": y_min,
        "width": max(0, x_max - x_min + 1),
        "height": max(0, y_max - y_min + 1),
    }

def _verify_files_exist() -> Tuple[str, str]:
    """Verify that the required model files exist and return their paths.
    Note: CONFIG_FILE is a Hydra config path relative to the 'sam2' package, so we do not hard fail on os.path.exists for it.
    """
    # Best-effort check for config file on disk relative to this module for debugging
    config_fs_path = os.path.join(current_dir, CONFIG_FILE)
    if not os.path.exists(config_fs_path):
        print(f"⚠️ Config file not found on filesystem at: {config_fs_path} (this may be fine if Hydra loads it from the package)")
    
    # Verify checkpoint file exists using a resolved absolute path
    ckpt_fs_path = os.path.abspath(os.path.join(current_dir, CHECKPOINT_FILE))
    if not os.path.exists(ckpt_fs_path):
        print(f"❌ Checkpoint file not found: {ckpt_fs_path}")
        print(f"Current directory: {os.getcwd()}")
        print("Available checkpoints:")
        checkpoint_dir = os.path.dirname(ckpt_fs_path)
        if os.path.exists(checkpoint_dir):
            for f in os.listdir(checkpoint_dir):
                if f.endswith((".pt", ".pth")):
                    print(f"  - {f}")
        raise FileNotFoundError(f"Checkpoint file not found: {ckpt_fs_path}")
    
    # Return Hydra-relative config path and ABSOLUTE checkpoint path for build_sam2
    return CONFIG_FILE, ckpt_fs_path

def _get_device() -> str:
    """Determine the device to use for model inference."""
    if torch.cuda.is_available():
        try:
            # Test if CUDA is actually working
            torch.zeros(1).cuda()
            return "cuda"
        except Exception as e:
            print(f"⚠️ CUDA is not available: {e}, falling back to CPU")
    return "cpu"

def _ensure_model() -> None:
    """Ensure the SAM2 model is loaded and ready for inference."""
    global _model, _mask_gen
    if _model is not None and _mask_gen is not None:
        return
    
    print(f"🔍 Loading SAM2 model from: {CONFIG_FILE}")
    print(f"Checkpoint path: {CHECKPOINT_FILE}")
    
    # Verify files exist and get their paths
    config_file, ckpt_path = _verify_files_exist()
    device = _get_device()
    
    print(f"Using device: {device}")
    
    try:
        _model = build_sam2(config_file=config_file, ckpt_path=ckpt_path, device=device)
        # More permissive defaults to increase recall on household scenes
        _mask_gen = SAM2AutomaticMaskGenerator(
            _model,
            points_per_side=16,
            pred_iou_thresh=0.5,           # lower to include more masks
            stability_score_thresh=0.6,    # slightly lower than default
            min_mask_region_area=50,       # allow small objects
        )
        print("✅ SAM2 model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading SAM2 model: {e}")
        raise

def _process_boxes_with_sam(image_np: np.ndarray, boxes: List[List[float]]) -> List[Dict]:
    """Process image with SAM2 using the provided bounding boxes."""
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    from sam2.build_sam import build_sam2
    
    print(f"🔍 [Box Mode] Loading SAM2 model from: {CONFIG_FILE}")
    print(f"[Box Mode] Checkpoint path: {CHECKPOINT_FILE}")
    
    # Use the global model if available, otherwise create a new one
    if _model is not None:
        predictor = SAM2ImagePredictor(_model)
    else:
        # This should not happen as _ensure_model() is called first
        device = _get_device()
        sam_model = build_sam2(config_file=CONFIG_FILE, ckpt_path=CHECKPOINT_FILE, device=device)
        predictor = SAM2ImagePredictor(sam_model)
    
    predictor.set_image(image_np)
    
    all_masks = []
    for box in boxes:
        # Convert xywh to xyxy if needed
        if len(box) == 4:  # xywh
            x, y, w, h = box
            box_xyxy = [x, y, x + w, y + h]
        else:  # xyxy
            box_xyxy = box
            
        # Get mask for this box
        masks, scores, _ = predictor.predict(
            box=np.array(box_xyxy),
            multimask_output=False,
            return_logits=False
        )
        
        if len(masks) > 0:
            all_masks.append({
                'segmentation': masks[0],
                'stability_score': float(scores[0])
            })
    
    print(f"Generated {len(all_masks)} masks from {len(boxes)} boxes")
    return all_masks

def segment_pil(image: Image.Image, boxes: Optional[List[List[float]]] = None) -> List[Dict]:
    """
    Segment an image using SAM2.
    
    Args:
        image: Input PIL Image
        boxes: Optional list of bounding boxes in format [x, y, w, h] or [x1, y1, x2, y2]
    
    Returns:
        List of segmentation results, each containing id, bbox, score, and mask
    """
    _ensure_model()
    image_np = np.array(image.convert("RGB"))
    
    try:
        if boxes and len(boxes) > 0:
            masks = _process_boxes_with_sam(image_np, boxes)
        else:
            # Fall back to automatic mask generation if no boxes provided
            masks = _mask_gen.generate(image_np)
            print(f"Generated {len(masks)} masks with automatic segmentation")
    except Exception as e:
        print(f"❌ Error generating masks: {e}")
        raise
    
    results: List[Dict] = []
    for idx, m in enumerate(masks):
        bbox = _mask_to_bbox(m["segmentation"])
        if bbox["width"] < 10 or bbox["height"] < 10:
            continue
        results.append({
            "id": str(idx),
            "x": bbox["x"],
            "y": bbox["y"],
            "width": bbox["width"],
            "height": bbox["height"],
            "score": float(m.get("stability_score", 0.0)),
            "mask": m["segmentation"].astype(int).tolist(),  # Include actual mask array
        })
    
    print(f"Returning {len(results)} valid masks")
    return results 