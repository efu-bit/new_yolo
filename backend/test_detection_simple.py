from yolo_detector import YOLODetector
from PIL import Image
import numpy as np

def main():
    print("🔍 Testing YOLO detection...")
    
    # Create a test image (black image with white rectangle)
    img = Image.new('RGB', (640, 480), color='black')
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 300, 300], fill='white')
    
    # Initialize detector
    detector = YOLODetector()
    
    # Run detection
    print("\n🔄 Running detection...")
    detections = detector.detect(img)
    
    # Print results
    print("\n📋 Detection Results:")
    if not detections:
        print("No objects detected")
    else:
        for i, det in enumerate(detections, 1):
            print(f"{i}. Class: {det.get('class_name', 'unknown')}")
            print(f"   Confidence: {det.get('confidence', 0):.2f}")
            print(f"   Bounding Box: {det.get('bbox', [])}")
            print(f"   Area: {det.get('area', 0):.0f} px²")
            if 'aspect_ratio' in det:
                print(f"   Aspect Ratio: {det['aspect_ratio']:.2f}")

if __name__ == "__main__":
    from PIL import ImageDraw  # Moved here to avoid import error if PIL not available
    main()
