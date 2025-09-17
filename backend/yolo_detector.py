import torch
from pathlib import Path
import numpy as np
from typing import List, Dict, Any

class YOLODetector:
    def __init__(self, weights_path: str = None, device: str = None):
        # Set default weights path if not provided
        if weights_path is None:
            weights_path = str(Path(__file__).parent / 'best.pt')
        """
        Initialize YOLO detector with the specified weights.
        
        Args:
            weights_path: Path to the YOLO weights file
            device: Device to run the model on (cuda or cpu)
        """
        self.weights_path = Path(weights_path)
        if not self.weights_path.exists():
            raise FileNotFoundError(f"YOLO weights not found at {weights_path}")
            
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model()
        
    def _load_model(self):
        """Load YOLO model from weights"""
        try:
            # First try using ultralytics package
            from ultralytics import YOLO
            model = YOLO(str(self.weights_path))
            model.to(self.device)
            model.eval()
            self._is_ultralytics = True
            
            # Define class name mapping for better detection
            self.class_mapping = {
                'frame': 'photo frame',
                'picture_frame': 'photo frame',
                'photo': 'photo frame',
                'painting': 'photo frame',
                'art': 'photo frame',
                'mirror': 'mirror',
                'vase': 'vase',
                'plant': 'plant',
                'candle': 'candle',
                'lamp': 'lamp',
                'clock': 'clock',
                'statue': 'statue',
                'sculpture': 'statue'
            }
            
            # Print class names for debugging
            if hasattr(model, 'names') and model.names:
                print("✅ YOLO Model Classes:", model.names)
                print("🔍 Using class mapping:", self.class_mapping)
            else:
                print("ℹ️ No class names found in YOLO model")
        except ImportError:
            # Fall back to torch.hub
            model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(self.weights_path))
            model = model.to(self.device)
            model.eval()
            self._is_ultralytics = False
            print("ℹ️ Using torch.hub YOLOv5")
            
        return model
    
    def detect(self, image, min_box_area=3000, target_class=None):
        """
        Run object detection on the input image and filter detections.
        
        Args:
            image: PIL Image or numpy array
            min_box_area: Minimum area (in pixels) for a detection to be considered valid.
                        Detections smaller than this will be skipped.
            target_class: Optional class name to filter detections
            
        Returns:
            List of detections, each with 'bbox' (xyxy format), 'confidence', 'class_id', and 'class_name'
        """
        """
        Run object detection on the input image and filter out small boxes.
        
        Args:
            image: PIL Image or numpy array
            min_box_area: Minimum area (in pixels) for a detection to be considered valid
            target_class: Optional class name to filter detections (e.g., 'photo frame')
            
        Returns:
            List of detections, each with 'bbox' (xyxy format), 'confidence', 'class_id', and 'class_name'
        """
        # Run inference
        results = self.model(image)
        
        # Get image dimensions for relative size filtering
        if hasattr(image, 'size'):  # PIL Image
            img_w, img_h = image.size
        else:  # numpy array
            img_h, img_w = image.shape[:2]
            
        # Parse results based on model type
        detections = []
        
        if hasattr(self, '_is_ultralytics') and self._is_ultralytics:
            # For ultralytics YOLO
            for result in results:
                boxes = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()
                cls_ids = result.boxes.cls.cpu().numpy()
                
                for box, conf, cls_id in zip(boxes, confs, cls_ids):
                    x1, y1, x2, y2 = map(float, box)
                    # Calculate box area and aspect ratio
                    box_w = x2 - x1
                    box_h = y2 - y1
                    box_area = box_w * box_h
                    aspect_ratio = box_w / box_h if box_h > 0 else 0
                    
                    # Skip small boxes
                    if box_area < min_box_area:
                        continue
                    
                    # Get class name and apply mapping
                    class_name = result.names.get(int(cls_id), str(int(cls_id))).lower()
                    mapped_class = self.class_mapping.get(class_name, class_name)
                    
                    # Skip if target class is specified and doesn't match
                    if target_class and mapped_class != target_class.lower():
                        continue
                    
                    # Additional filtering for photo frames based on aspect ratio
                    if mapped_class == 'photo frame':
                        # Expanded frame aspect ratios (0.2 to 2.0) to include more variations
                        if not (0.2 <= aspect_ratio <= 2.0):
                            continue  # Skip very wide or very tall detections
                    
                    detections.append({
                        'bbox': [x1, y1, x2, y2],  # xyxy format
                        'confidence': float(conf),
                        'class_id': int(cls_id),
                        'class_name': mapped_class,
                        'area': box_area,
                        'aspect_ratio': aspect_ratio
                    })
        else:
            # For torch.hub YOLOv5
            for *xyxy, conf, cls_id in results.xyxy[0]:
                x1, y1, x2, y2 = map(float, xyxy)
                # Calculate box area
                box_w = x2 - x1
                box_h = y2 - y1
                box_area = box_w * box_h
                
                # Skip small boxes
                if box_area < min_box_area:
                    continue
                    
                detections.append({
                    'bbox': [x1, y1, x2, y2],  # xyxy format
                    'confidence': float(conf),
                    'class_id': int(cls_id),
                    'class_name': self.model.names.get(int(cls_id), str(int(cls_id))),
                    'area': box_area
                })
            
        return detections

# Singleton instance
_yolo_detector = None

def get_yolo_detector():
    """Get or create YOLO detector instance"""
    global _yolo_detector
    if _yolo_detector is None:
        _yolo_detector = YOLODetector()
    return _yolo_detector
