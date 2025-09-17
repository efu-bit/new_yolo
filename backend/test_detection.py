from yolo_detector import YOLODetector
from PIL import Image, ImageDraw, ImageFont
import os

def test_detection(image_path, output_dir='output'):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize detector
    detector = YOLODetector()
    
    # Open image
    image = Image.open(image_path)
    
    # Run detection
    print(f"🔍 Running detection on {image_path}...")
    detections = detector.detect(image, min_box_area=1000)
    
    # Draw detections
    draw = ImageDraw.Draw(image)
    for i, det in enumerate(detections):
        x1, y1, x2, y2 = det['bbox']
        label = f"{det['class_name']} {det['confidence']:.2f}"
        
        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        
        # Draw label background
        text_bbox = draw.textbbox((x1, y1 - 20), label)
        draw.rectangle(text_bbox, fill="red")
        
        # Draw text
        draw.text((x1, y1 - 20), label, fill="white")
    
    # Save result
    output_path = os.path.join(output_dir, os.path.basename(image_path))
    image.save(output_path)
    print(f"✅ Saved result to {output_path}")
    print("\nDetected objects:")
    for i, det in enumerate(detections, 1):
        print(f"{i}. {det['class_name']} (confidence: {det['confidence']:.2f}, area: {det['area']:.0f} px²)")

if __name__ == "__main__":
    # Test with a sample image (replace with your image path)
    test_image = "test_image.jpg"  # Change this to your test image path
    if os.path.exists(test_image):
        test_detection(test_image)
    else:
        print(f"❌ Test image not found: {test_image}")
        print("Please place a test image named 'test_image.jpg' in the current directory.")
