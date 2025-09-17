import torch
import yaml
from pathlib import Path

def load_yaml_config(config_path):
    with open(config_path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error loading YAML file: {e}")
            return None

def main():
    model_path = Path('best.pt')
    print(f"🔍 Inspecting model: {model_path.absolute()}")
    
    # Check if file exists
    if not model_path.exists():
        print("❌ Model file not found")
        return
    
    # Try to load the model
    try:
        # First try loading as a state dict
        checkpoint = torch.load(model_path, map_location='cpu')
        
        if isinstance(checkpoint, dict):
            print("\n📦 Model checkpoint keys:")
            for key in checkpoint.keys():
                print(f"  - {key}")
                
            # Check for model architecture
            if 'model' in checkpoint:
                print("\n🏗️  Model architecture found in checkpoint")
                
            # Check for class names
            if 'model' in checkpoint and hasattr(checkpoint['model'], 'names'):
                print("\n📋 Class names:")
                for i, name in enumerate(checkpoint['model'].names):
                    print(f"  {i}: {name}")
                    
            # Check for YAML config
            yaml_path = model_path.with_suffix('.yaml')
            if yaml_path.exists():
                print(f"\n📄 Found YAML config: {yaml_path}")
                config = load_yaml_config(yaml_path)
                if config and 'names' in config:
                    print("\n📋 Class names from YAML:")
                    for i, name in enumerate(config['names']):
                        print(f"  {i}: {name}")
        
    except Exception as e:
        print(f"\n❌ Error loading model: {e}")
        
    # Check for YAML file with same name
    yaml_path = model_path.with_suffix('.yaml')
    if yaml_path.exists():
        print(f"\n📄 Found YAML file: {yaml_path}")
        config = load_yaml_config(yaml_path)
        if config and 'names' in config:
            print("\n📋 Class names from YAML:")
            for i, name in enumerate(config['names']):
                print(f"  {i}: {name}")

if __name__ == "__main__":
    main()
