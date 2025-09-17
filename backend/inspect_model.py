from ultralytics import YOLO
import torch

def main():
    try:
        # Load the model
        print("🔍 Loading YOLO model...")
        model = YOLO('best.pt')
        
        # Print model architecture
        print("\n📊 Model Architecture:")
        print(model.model)
        
        # Print model metadata
        print("\n📋 Model Metadata:")
        if hasattr(model, 'names'):
            print("\nClass Names:")
            for id, name in model.names.items():
                print(f"  {id}: {name}")
        
        # Print model parameters
        print("\n⚙️ Model Parameters:")
        total_params = sum(p.numel() for p in model.parameters())
        print(f"Total parameters: {total_params:,}")
        
        # Check input shape
        if hasattr(model, 'model'):
            print("\n📐 Input Shape:")
            print(f"Input shape: {model.model.args.get('imgsz', 'Not specified')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
