import torch
from yolo_detector import YOLODetector

def main():
    print("Testing YOLO model classes...")
    
    # Initialize the detector
    detector = YOLODetector()
    
    # Try to access model classes
    if hasattr(detector, 'model') and hasattr(detector.model, 'names'):
        print("\nYOLO Model Classes:")
        for class_id, class_name in detector.model.names.items():
            print(f"{class_id}: {class_name}")
    else:
        print("Could not find class names in the model")
        
        # Try alternative way to get class names
        try:
            if hasattr(detector.model, 'model'):
                if hasattr(detector.model.model, 'names'):
                    print("\nFound classes in model.model.names:")
                    for class_id, class_name in detector.model.model.names.items():
                        print(f"{class_id}: {class_name}")
        except Exception as e:
            print(f"Error accessing model classes: {e}")

if __name__ == "__main__":
    main()
