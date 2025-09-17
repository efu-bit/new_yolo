import os
import sys
import json
from pathlib import Path
from typing import List, Dict

import numpy as np
from PIL import Image
import torch

from sam2.build_sam import build_sam2
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator


def mask_to_bbox(mask: np.ndarray) -> Dict[str, int]:
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


def main(image_path: str) -> None:
    # Relative defaults (do not use absolute paths)
    config_file = os.environ.get("SAM2_CONFIG", "configs/sam2.1/sam2.1_hiera_t.yaml")
    ckpt_path = os.environ.get("SAM2_CHECKPOINT", "../checkpoints/sam2.1_hiera_tiny.pt")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = build_sam2(config_file=config_file, ckpt_path=ckpt_path, device=device)
    mask_gen = SAM2AutomaticMaskGenerator(model)

    pil = Image.open(image_path).convert("RGB")
    image_np = np.array(pil)
    masks = mask_gen.generate(image_np)

    results: List[Dict] = []
    for idx, m in enumerate(masks):
        bbox = mask_to_bbox(m["segmentation"])
        if bbox["width"] < 10 or bbox["height"] < 10:
            continue
        results.append({
            "id": str(idx),
            "x": bbox["x"],
            "y": bbox["y"],
            "width": bbox["width"],
            "height": bbox["height"],
            "score": float(m.get("stability_score", 0.0)),
        })

    sys.stdout.write(json.dumps(results))
    sys.stdout.flush()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rest_segmenter_cli.py /path/to/image", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1]) 