import torch
from pathlib import Path

def check_model():
    model_path = Path('best.pt')
    print(f"🔍 Checking model: {model_path.absolute()}")
    
    # Check file size
    if model_path.exists():
        print(f"📏 Model size: {model_path.stat().st_size / (1024*1024):.2f} MB")
    else:
        print("❌ Model file not found")
        return
    
    # Try loading with ultralytics
    try:
        from ultralytics import YOLO
        print("\n🔄 Trying to load with Ultralytics YOLO...")
        model = YOLO(str(model_path))
        print("✅ Successfully loaded with Ultralytics YOLO")
        
        # Try to get class names
        if hasattr(model, 'names') and model.names:
            print("\n📋 Detected Classes:")
            for class_id, class_name in model.names.items():
                print(f"  {class_id}: {class_name}")
        
        # Check if model has been moved to device
        if hasattr(model, 'device'):
            print(f"\n⚙️ Model device: {model.device}")
            
    except Exception as e:
        print(f"❌ Error with Ultralytics YOLO: {e}")
    
    # Try loading with torch.hub (YOLOv5)
    try:
        print("\n🔄 Trying to load with torch.hub (YOLOv5)...")
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path), force_reload=True)
        print("✅ Successfully loaded with torch.hub YOLOv5")
        
        # Get class names
        if hasattr(model, 'names') and model.names:
            print("\n📋 Detected Classes:")
            for class_id, class_name in model.names.items():
                print(f"  {class_id}: {class_name}")
                
    except Exception as e:
        print(f"❌ Error with torch.hub YOLOv5: {e}")

if __name__ == "__main__":
    check_model()
