"""
YOLO Helper Module
Handles YOLO detection without interfering with SAM2.
"""
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional

class YOLOHelper:
    def __init__(self, weights_path: str = None):
        self.weights_path = Path(weights_path) if weights_path else Path(__file__).parent / 'best.pt'
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Safely load YOLO model"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(str(self.weights_path)).to(self.device)
            print(f"✅ YOLO model loaded from {self.weights_path}")
        except ImportError:
            print("⚠️ ultralytics not found, trying torch.hub")
            try:
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                         path=str(self.weights_path), 
                                         force_reload=True)
                self.model = self.model.to(self.device)
                print(f"✅ YOLO model loaded via torch.hub from {self.weights_path}")
            except Exception as e:
                print(f"❌ Failed to load YOLO model: {e}")
                self.model = None
    
    def detect(self, image) -> List[Dict[str, Any]]:
        """Run detection on an image"""
        if self.model is None:
            return []
            
        try:
            # Convert PIL to numpy if needed
            if hasattr(image, 'convert'):
                image = np.array(image.convert('RGB'))
                
            # Run inference
            results = self.model(image)
            
            # Parse results based on model type
            detections = []
            
            if hasattr(results, 'xyxy'):  # torch.hub format
                for *xyxy, conf, cls_id in results.xyxy[0]:
                    x1, y1, x2, y2 = map(float, xyxy)
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': float(conf),
                        'class_id': int(cls_id),
                        'class_name': str(int(cls_id))
                    })
            else:  # ultralytics format
                for result in results:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confs = result.boxes.conf.cpu().numpy()
                    cls_ids = result.boxes.cls.cpu().numpy()
                    
                    for box, conf, cls_id in zip(boxes, confs, cls_ids):
                        x1, y1, x2, y2 = map(float, box)
                        detections.append({
                            'bbox': [x1, y1, x2, y2],
                            'confidence': float(conf),
                            'class_id': int(cls_id),
                            'class_name': str(int(cls_id))
                        })
            
            return detections
            
        except Exception as e:
            print(f"⚠️ YOLO detection failed: {e}")
            return []

# Global instance
yolo_helper = None
try:
    yolo_helper = YOLOHelper()
    print("✅ YOLO helper initialized successfully")
except Exception as e:
    print(f"⚠️ Failed to initialize YOLO helper: {e}")
