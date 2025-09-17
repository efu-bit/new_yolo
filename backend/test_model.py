import torch
from pathlib import Path

def main():
    print("🔍 Testing YOLO model...")
    
    # Check if CUDA is available
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    # Check model file
    model_path = Path('best.pt')
    print(f"\n📂 Model path: {model_path.absolute()}")
    print(f"File exists: {model_path.exists()}")
    if model_path.exists():
        print(f"File size: {model_path.stat().st_size / (1024*1024):.2f} MB")
    
    # Try to load the model with error handling
    try:
        print("\n🔄 Attempting to load model...")
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path))
        print("✅ Model loaded successfully!")
        
        # Print model information
        print("\n📋 Model information:")
        print(f"Model type: {type(model)}")
        
        # Get class names
        if hasattr(model, 'names') and model.names:
            print("\n📋 Detected Classes:")
            for class_id, class_name in model.names.items():
                print(f"  {class_id}: {class_name}")
        else:
            print("\nℹ️ No class names found in the model")
            
        # Check if model has a model attribute (YOLOv5 specific)
        if hasattr(model, 'model'):
            print("\n🔍 Model architecture attributes:")
            for name, _ in model.model.named_children():
                print(f"  - {name}")
    
    except Exception as e:
        print(f"\n❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
