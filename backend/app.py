
'''
source .venv/bin/activate && export SAM2_CONFIG=configs/sam2.1/sam2.1_hiera_t.yaml && export SAM2_CHECKPOINT=checkpoints/sam2.1_hiera_tiny.pt && python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
source .venv/bin/activate && export SAM2_CONFIG=configs/sam2.1/sam2.1_hiera_t.yaml && export SAM2_CHECKPOINT=checkpoints/sam2.1_hiera_tiny.pt && export GOOGLE_CLOUD_PROJECT=hubx-ml-playground && python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
bash -lc 'source .venv/bin/activate && export GOOGLE_CLOUD_PROJECT=hubx-ml-playground SAM2_CONFIG=configs/sam2.1/sam2.1_hiera_l.yaml SAM2_CHECKPOINT=checkpoints/sam2.1_hiera_large.pt && python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload'
'''

import io
import os
from pathlib import Path
import math
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from PIL import Image
from PIL import ImageDraw
import numpy as np
from dotenv import load_dotenv

from .embedding_service import EmbeddingService
from .db import ProductsDb
from .gcs_service import GCSService
from .yolo_detector import get_yolo_detector

# Load environment from backend/.env explicitly so it works from any CWD
load_dotenv(dotenv_path=Path(__file__).with_name('.env'))

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="Decor Detective Backend")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

_embedder: Optional[EmbeddingService] = None

def get_embedder() -> EmbeddingService:
	global _embedder
	if _embedder is None:
		_embedder = EmbeddingService()
	return _embedder

db = ProductsDb()
gcs = GCSService()


class BBox(BaseModel):
	x: int
	y: int
	width: int
	height: int


class PolygonPoint(BaseModel):
	x: float
	y: float


class MaskDto(BaseModel):
    id: str
    x: int
    y: int
    width: int
    height: int
    score: float
    mask: List[List[int]]  
    color: Optional[List[int]] = None
    colored_mask: Optional[List[List[List[int]]]] = None  


class CropRequest(BaseModel):
	image: str  # base64 encoded image
	polygon: List[PolygonPoint]


class SearchRequest(BaseModel):
	embedding: List[float]
	top_k: int = 12


class ProductDto(BaseModel):
	id: str
	name: str
	price: Optional[str] = None
	brand: Optional[str] = None
	rating: Optional[float] = None
	imageUrl: Optional[str] = None
	original_url: Optional[str] = None
	similarity: float
	inStock: Optional[bool] = True


@app.post("/segment", response_model=List[MaskDto])
async def segment(image: UploadFile = File(...), use_yolo: bool = True):
    """
    Segment an image using YOLO for detection and SAM2 for segmentation.
    
    Args:
        image: Input image file
        use_yolo: Whether to use YOLO for detection (True) or use SAM2 directly (False)
    """
    try:
        image_bytes = await image.read()
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Import from the sam2 package
        try:
            from backend.sam2.sam2.segment_api import segment_pil as _segment_pil
        except ImportError:
            from sam2.sam2.segment_api import segment_pil as _segment_pil
        
        # Initialize YOLO detector if needed
        yolo_detector = None
        if use_yolo:
            try:
                yolo_detector = get_yolo_detector()
                # Run YOLO detection with minimum box area of 2000 pixels
                detections = yolo_detector.detect(pil, min_box_area=2000)
                print(f"✅ YOLO detected {len(detections)} objects after size filtering")
                
                # Log details about filtered detections
                if detections:
                    areas = [d.get('area', 0) for d in detections]
                    print(f"  - Min area: {min(areas):.0f}px², Max area: {max(areas):.0f}px²")
            except Exception as e:
                print(f"⚠️ YOLO detection failed, falling back to SAM2 only: {e}")
                use_yolo = False
                detections = []
        
        # If YOLO is not used or failed, use SAM2 directly
        if not use_yolo or not detections:
            print("ℹ️ Using SAM2 without YOLO detection")
            masks = _segment_pil(pil)
        else:
            print(f"✅ Using {len(detections)} YOLO detections with SAM2")
            
            # Convert YOLO detections to SAM2 input format (xyxy to xywh)
            # Note: detections have already been filtered by min_box_area in yolo_detector.detect()
            boxes = []
            valid_detections = []
            
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                w = x2 - x1
                h = y2 - y1
                area = w * h
                
                # Additional safety check (should already be filtered by yolo_detector)
                if area >= 2000:  # Ensure minimum area
                    boxes.append([x1, y1, w, h])
                    valid_detections.append(det)
            
            # Update detections to only include valid ones
            detections = valid_detections
            print(f"  - {len(detections)} detections passed final size check for SAM2")
            
            try:
                # Try with boxes parameter if supported
                masks = _segment_pil(pil, boxes=boxes)
            except Exception as e:
                print(f"⚠️ Error using box prompts, falling back to standard segmentation: {e}")
                # Fall back to standard segmentation if boxes parameter is not supported
                masks = _segment_pil(pil)
        
        # Process masks and calculate bounding boxes with colorful visualization
        processed_masks = []
        # Use purple for all masks (RGB: 128, 0, 255)
        colors = [
            [128, 0, 255]   # Purple
        ]
        
        for i, m in enumerate(masks):
            # Convert mask to numpy array if needed
            mask_array = m.get("mask")
            if isinstance(mask_array, list):
                mask_array = np.array(mask_array)
            elif not isinstance(mask_array, np.ndarray):
                continue
                
            # Calculate bounding box from mask
            coords = np.where(mask_array > 0)
            if len(coords[0]) > 0:
                y_min, y_max = coords[0].min(), coords[0].max()
                x_min, x_max = coords[1].min(), coords[1].max()
                
                # Create purple mask for visualization
                purple = [128, 0, 255]  # RGB for purple
                colored_mask = np.zeros((mask_array.shape[0], mask_array.shape[1], 3), dtype=np.uint8)
                colored_mask[mask_array > 0] = purple
                
                # Get confidence score (use YOLO's confidence if available)
                score = m.get("score", 0.9)
                if use_yolo and i < len(detections):
                    score = detections[i].get('confidence', score)
                
                # Create mask dto with bounding box and color
                mask_dto = {
                    "id": str(i),
                    "x": int(x_min),
                    "y": int(y_min), 
                    "width": int(x_max - x_min),
                    "height": int(y_max - y_min),
                    "score": float(score),
                    "mask": mask_array.astype(int).tolist(),
 "color": purple,
                    "colored_mask": colored_mask.tolist()
                }
                processed_masks.append(mask_dto)
        
        print(f"✅ Segmentation successful: {len(processed_masks)} objects with bounding boxes")
        return [MaskDto(**m) for m in processed_masks]
    except Exception as e:
        # Provide clearer client-side error with likely causes
        sam2_cfg = os.environ.get("SAM2_CONFIG")
        sam2_ckpt = os.environ.get("SAM2_CHECKPOINT")
        detail = {
            "error": "Segmentation failed",
            "message": str(e),
            "sam2_config": sam2_cfg,
            "sam2_checkpoint": sam2_ckpt,
        }
        print(f"❌ Segmentation failed: {detail}")
        raise HTTPException(status_code=500, detail=detail)
@app.post("/crop", response_model=dict)
async def crop_image(
	image: UploadFile = File(...),
	polygon_points: str = Form(...)  # JSON string of polygon points
):
	"""Crop an image based on polygon coordinates"""
	try:
		import json
		import base64
		
		# Parse polygon points
		polygon = json.loads(polygon_points)
		if not polygon or len(polygon) < 3:
			raise ValueError("Polygon must have at least 3 points")
		
		# Load image
		image_bytes = await image.read()
		pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
		W, H = pil.width, pil.height
		
		# Rasterize polygon to mask for object area estimation
		poly_tuples = [(float(p["x"]), float(p["y"])) for p in polygon]
		mask_img = Image.new("L", (W, H), 0)
		draw = ImageDraw.Draw(mask_img)
		draw.polygon(poly_tuples, outline=1, fill=1)
		mask = np.array(mask_img, dtype=np.uint8)
		
		# Compute tight bbox around polygon
		x_coords = [p["x"] for p in polygon]
		y_coords = [p["y"] for p in polygon]
		x_min, x_max = int(max(0, min(x_coords))), int(min(W, max(x_coords)))
		y_min, y_max = int(max(0, min(y_coords))), int(min(H, max(y_coords)))
		bbox_w, bbox_h = max(1, x_max - x_min), max(1, y_max - y_min)
		
		# Object area inside bbox and metrics
		object_area = int(mask[y_min:y_max, x_min:x_max].sum())
		bbox_area = bbox_w * bbox_h
		thinness = object_area / (bbox_area + 1e-6)  # fraction of bbox occupied
		aspect = max(bbox_w, bbox_h) / (min(bbox_w, bbox_h) + 1e-6)
		img_frac = bbox_area / float(W * H)
		
		# Determine object type and set size limits
		is_thin = thinness < 0.4 or aspect > 2.5 or img_frac < 0.05
		
		# Set max crop size as a fraction of original image (max 50% of width/height)
		max_crop_w = int(W * 0.5)
		max_crop_h = int(H * 0.5)
		
		# Dynamic max coverage: bulky objects can go up to 0.9; thin objects lower
		if is_thin:
			max_cov = 0.6  # thin/long/tiny objects
			min_cov = 0.2  # allow more padding for thin objects
		else:
			max_cov = 0.9  # bulky objects (e.g., sofas)
			min_cov = 0.25
		
		# Calculate desired coverage based on object type
		desired_cov = min(max_cov, max(0.4 if is_thin else 0.7, min_cov))
		
		# Starting crop is the bbox; compute current coverage ~ thinness
		current_cov = thinness
		
		# Compute required crop area to hit desired coverage with size limits
		required_area = min(
			object_area / max(desired_cov, 0.01),  # Ensure we don't divide by zero
			max_crop_w * max_crop_h  # Don't exceed max crop area
		)
		
		# Calculate scale factor while maintaining aspect ratio
		scale = min(
			(required_area / (bbox_area + 1e-6)) ** 0.5,  # Scale for desired coverage
			min(max_crop_w / max(bbox_w, 1), max_crop_h / max(bbox_h, 1))  # Scale for max dimensions
		)
		new_w = int(round(bbox_w * scale))
		new_h = int(round(bbox_h * scale))
		
		# Center expand around bbox center with padding for thin objects
		cx = (x_min + x_max) // 2
		cy = (y_min + y_max) // 2
		
		# For thin objects, add more padding in the direction of the thin dimension
		if is_thin and aspect > 2.0:
			if bbox_w > bbox_h:  # Wide and thin (landscape)
				padding_ratio = 0.3  # More padding on top/bottom
				half_w = new_w // 2
				half_h = int(new_h * (1 + padding_ratio) // 2)
			else:  # Tall and thin (portrait)
				padding_ratio = 0.3  # More padding on sides
				half_w = int(new_w * (1 + padding_ratio) // 2)
				half_h = new_h // 2
		else:
			half_w = new_w // 2
			half_h = new_h // 2
		
		# Calculate crop bounds with image boundary checks
		new_x1 = max(0, cx - half_w)
		new_y1 = max(0, cy - half_h)
		new_x2 = min(W, cx + half_w)
		new_y2 = min(H, cy + half_h)
		
		# Adjust if we hit image boundaries
		if new_x1 == 0 and new_x2 < W:
			new_x2 = min(W, new_x1 + 2 * half_w)
		if new_x2 == W and new_x1 > 0:
			new_x1 = max(0, new_x2 - 2 * half_w)
		if new_y1 == 0 and new_y2 < H:
			new_y2 = min(H, new_y1 + 2 * half_h)
		if new_y2 == H and new_y1 > 0:
			new_y1 = max(0, new_y2 - 2 * half_h)
		
		# Final dimensions
		new_w = max(1, new_x2 - new_x1)
		new_h = max(1, new_y2 - new_y1)
		
		# Final crop
		cropped = pil.crop((new_x1, new_y1, new_x1 + new_w, new_y1 + new_h))
		
		# Convert to base64 for response
		buffer = io.BytesIO()
		cropped.save(buffer, format="PNG")
		img_str = base64.b64encode(buffer.getvalue()).decode()
		
		return {
			"cropped_image": img_str,
			"bbox": {
				"x": int(new_x1),
				"y": int(new_y1),
				"width": int(new_w),
				"height": int(new_h)
			},
			"coverage": {
				"object_area": int(object_area),
				"bbox_area": int(bbox_area),
				"estimated_coverage": float(current_cov),
				"target_max": float(max_cov),
				"target_min": float(min_cov)
			}
		}
	except Exception as e:
		print(f"❌ Cropping failed: {e}")
		raise


@app.post("/crop_bbox", response_model=dict)
async def crop_bbox(
	image: UploadFile = File(...),
	x: int = Form(...),
	y: int = Form(...),
	width: int = Form(...),
	height: int = Form(...),
):
	"""Crop an image based on bounding box coordinates"""
	try:
		import base64
		
		# Load image
		image_bytes = await image.read()
		pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
		
		# Ensure coordinates are within image bounds
		x = max(0, x)
		y = max(0, y)
		x_max = min(pil.width, x + width)
		y_max = min(pil.height, y + height)
		
		# Crop the image
		cropped = pil.crop((x, y, x_max, y_max))
		
		# Convert to base64 for response
		buffer = io.BytesIO()
		cropped.save(buffer, format="PNG")
		img_str = base64.b64encode(buffer.getvalue()).decode()
		
		return {
			"cropped_image": img_str,
			"bbox": {
				"x": x,
				"y": y,
				"width": x_max - x,
				"height": y_max - y
			}
		}
	except Exception as e:
		print(f"❌ Bounding box cropping failed: {e}")
		raise

@app.get("/images/{filename:path}")
async def get_image(filename: str):
    """
    Proxy endpoint to serve images from private GCS bucket.
    Images are streamed from RAM without saving to disk.
    
    Args:
        filename: GCS path to the image (e.g., "oguzhan/ikea_filtered_prompt_updated/0000d4775...")
    """
    try:
        # Stream image directly from GCS to memory
        image_data, content_type = gcs.stream_image(filename)
        
        if image_data is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Image not found: {filename}"
            )
        
        # Use the content type from GCS or default to image/jpeg
        content_type = content_type or 'image/jpeg'
        
        # Stream the response directly from memory
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                "Content-Length": str(len(image_data)),
                "Content-Disposition": f"inline; filename=\"{filename.split('/')[-1]}\""
            }
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        print(f"❌ Image proxy failed for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load image: {str(e)}"
        )

@app.post("/embed_siglip", response_model=List[float])
async def embed_siglip(image: UploadFile = File(...)):
	"""Generate 768-dim embedding using SigLIP2 for a full image"""
	try:
		image_bytes = await image.read()
		pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
		embedding = get_embedder().compute_embedding(pil)
		print(f"✅ SigLIP2 embedding generated: {len(embedding)} dimensions")
		return embedding
	except Exception as e:
		print(f"❌ SigLIP2 embedding failed: {e}")
		detail = {
			"error": "Embedding failed",
			"message": str(e),
			"siglip_model_id": os.environ.get("SIGLIP_MODEL_ID", "google/siglip-base-patch16-384"),
			"siglip_device_map": os.environ.get("SIGLIP_DEVICE_MAP", "auto"),
		}
		raise HTTPException(status_code=500, detail=detail)

@app.post("/embed", response_model=List[float])
async def embed(
	image: UploadFile = File(...),
	x: int = Form(...),
	y: int = Form(...),
	width: int = Form(...),
	height: int = Form(...),
):
	"""Generate embedding for a cropped image region"""
	try:
		image_bytes = await image.read()
		pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
		crop = pil.crop((x, y, x + width, y + height))
		embedding = get_embedder().compute_embedding(crop)
		print(f"✅ Embedding generated: {len(embedding)} dimensions")
		return embedding
	except Exception as e:
		print(f"❌ Embedding failed: {e}")
		detail = {
			"error": "Embedding failed",
			"message": str(e),
			"siglip_model_id": os.environ.get("SIGLIP_MODEL_ID", "google/siglip-base-patch16-384"),
			"siglip_device_map": os.environ.get("SIGLIP_DEVICE_MAP", "auto"),
		}
		raise HTTPException(status_code=500, detail=detail)


@app.post("/search", response_model=List[ProductDto])
async def search(req: SearchRequest):
    """Search for similar furniture using vector similarity in MongoDB"""
    try:
        # Perform vector search with Euclidean distance
        rows = db.vector_search(req.embedding, top_k=req.top_k)
        
        # Process and return results
        results = []
        for r in rows:
            try:
                # Convert MongoDB ObjectId to string if needed
                doc_id = str(r.get("_id")) if r.get("_id") else ""
                
                # Get the original URL or fall back to imageUrl
                orig_url = r.get("original_url") or r.get("imageUrl")
                image_url = None
                
                # Handle GCS paths (gs://bucket/path)
                if isinstance(orig_url, str) and orig_url.startswith("gs://"):
                    # Extract the path part after gs://bucket/
                    path_parts = orig_url.split("/", 3)
                    if len(path_parts) >= 4:
                        # Reconstruct the full path without gs://bucket/ prefix
                        filename = path_parts[3]
                        # URL encode the filename to handle special characters
                        from urllib.parse import quote
                        image_url = f"/images/{quote(filename, safe='')}"

                product = ProductDto(
                    id=doc_id,
                    name=r.get("name", "Unknown"),
                    price=r.get("price"),
                    brand=r.get("brand"),
                    rating=r.get("rating"),
                    imageUrl=image_url,  # Browser-friendly URL if possible
                    original_url=orig_url,  # Preserve original
                    similarity=float(r.get("similarity", 0.0)),
                    inStock=r.get("inStock", True),
                )
                results.append(product)
            except Exception as e:
                print(f"Error processing product {r.get('_id')}: {e}")
                continue
        
        # Sort by similarity in descending order
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results
        
    except Exception as e:
        print(f"Search failed: {e}")
        # Fallback to local search if needed
        try:
            print("Attempting fallback search...")
            query = np.asarray(req.embedding, dtype=np.float32)
            query /= (np.linalg.norm(query) + 1e-12)
            products = db.fetch_all_with_embeddings()
            results: List[ProductDto] = []
            q_len = int(query.shape[0])
            
            for p in products:
                vec = np.asarray(p.get("image_embedding") or p.get("embedding", []), dtype=np.float32)
                # Skip if empty or wrong dimension
                if vec.size == 0 or int(vec.shape[0]) != q_len:
                    continue
                vec /= (np.linalg.norm(vec) + 1e-12)
                sim = float(np.dot(query, vec))
                results.append(ProductDto(
                    id=str(p.get("id") or p.get("_id", "")),
                    name=p.get("name", "Unknown"),
                    price=p.get("price"),
                    brand=p.get("brand"),
                    rating=p.get("rating"),
                    imageUrl=p.get("imageUrl"),
                    similarity=sim,
                    inStock=p.get("inStock", True),
                ))
            results.sort(key=lambda r: r.similarity, reverse=True)
            return results[:req.top_k]
        except Exception as e:
            print(f"Fallback search failed: {e}")
            raise

# Optional: run via `python -m backend.app`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True) 