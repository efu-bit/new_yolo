import torch
from pathlib import Path

def main():
    print("🔍 Inspecting YOLO model...")
    
    model_path = Path('best.pt')
    print(f"Model path: {model_path.absolute()}")
    print(f"File exists: {model_path.exists()}")
    
    if not model_path.exists():
        print("❌ Model file not found")
        return
    
    # Try loading with Ultralytics YOLO
    try:
        from ultralytics import YOLO
        print("\n🔄 Loading with Ultralytics YOLO...")
        model = YOLO(str(model_path))
        
        print("\n✅ Model loaded successfully!")
        print(f"Model type: {type(model)}")
        
        # Print model information
        if hasattr(model, 'names') and model.names:
            print("\n📋 Class Names:")
            for id, name in model.names.items():
                print(f"  {id}: {name}")
        
        # Print model architecture
        if hasattr(model, 'model'):
            print("\n🏗️  Model Architecture:")
            print(model.model)
            
    except Exception as e:
        print(f"\n❌ Error loading with Ultralytics YOLO: {e}")
        import traceback
        traceback.print_exc()
    
    # Try loading with torch.hub (YOLOv5)
    try:
        print("\n🔄 Trying torch.hub (YOLOv5) loading...")
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path), force_reload=True)
        
        print("\n✅ Model loaded with torch.hub!")
        print(f"Model type: {type(model)}")
        
        # Print class names
        if hasattr(model, 'names') and model.names:
            print("\n📋 Class Names:")
            for id, name in model.names.items():
                print(f"  {id}: {name}")
                
    except Exception as e:
        print(f"\n❌ Error loading with torch.hub: {e}")

if __name__ == "__main__":
    main()
