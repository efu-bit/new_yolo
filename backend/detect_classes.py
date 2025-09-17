import torch
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random

def generate_test_image(width=640, height=640):
    """Generate a test image with random shapes"""
    # Create a white image
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Draw some random shapes
    for _ in range(5):
        # Random position and size
        x1 = random.randint(0, width-100)
        y1 = random.randint(0, height-100)
        x2 = x1 + random.randint(50, 200)
        y2 = y1 + random.randint(50, 200)
        
        # Random color
        color = (random.randint(0, 255), 
                random.randint(0, 255), 
                random.randint(0, 255))
        
        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
    
    return image

def test_detection():
    print("🔍 Testing YOLO model detection...")
    
    # Generate a test image
    image = generate_test_image()
    image_path = "test_detection.jpg"
    image.save(image_path)
    print(f"📸 Generated test image: {image_path}")
    
    # Initialize detector
    try:
        from yolo_detector import YOLODetector
        detector = YOLODetector()
        
        # Run detection
        print("\n🔄 Running detection...")
        detections = detector.detect(image)
        
        if not detections:
            print("ℹ️ No objects detected in the test image")
            return
            
        # Print detected classes
        print("\n📋 Detected classes:")
        class_counts = {}
        for det in detections:
            class_name = det.get('class_name', 'unknown')
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
        for class_name, count in class_counts.items():
            print(f"  - {class_name}: {count} detections")
            
        # Draw detections
        draw = ImageDraw.Draw(image)
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            label = f"{det.get('class_name', 'object')} {det.get('confidence', 0):.2f}"
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
            
            # Draw label
            text_bbox = draw.textbbox((x1, y1 - 15), label)
            draw.rectangle(text_bbox, fill="red")
            draw.text((x1, y1 - 15), label, fill="white")
        
        # Save result
        output_path = "detection_result.jpg"
        image.save(output_path)
        print(f"\n💾 Saved detection result to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error during detection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detection()
