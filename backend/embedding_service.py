import os
from typing import List
import numpy as np
from PIL import Image, ImageFile
import torch
from transformers import AutoProcessor, AutoModel

# Robust image loader
ImageFile.LOAD_TRUNCATED_IMAGES = True

class EmbeddingService:
	def __init__(self):
		# Using SigLIP BASE 768-D model for real embeddings
		model_id = os.getenv("SIGLIP_MODEL_ID", "google/siglip-base-patch16-384")
		# Optional: use HF accelerate device mapping if requested
		device_map = os.getenv("SIGLIP_DEVICE_MAP", "auto")
		self.device = "cuda" if torch.cuda.is_available() else "cpu"
		
		# Load model/processor with optional device mapping
		# trust_remote_code is needed for SigLIP to expose get_image_features
		if device_map and device_map != "none":
			self.model = AutoModel.from_pretrained(
				model_id,
				device_map=device_map,
				trust_remote_code=True,
			).eval()
		else:
			self.model = AutoModel.from_pretrained(
				model_id,
				trust_remote_code=True,
			).to(self.device).eval()
		self.processor = AutoProcessor.from_pretrained(model_id, use_fast=True, trust_remote_code=True)

	def load_rgb(self, image: Image.Image) -> Image.Image:
		"""Convert image to RGB if needed"""
		if image.mode != "RGB":
			image = image.convert("RGB")
		return image

	@torch.inference_mode()
	def compute_embedding(self, image: Image.Image) -> List[float]:
		# Ensure RGB format
		image = self.load_rgb(image)
		
		# Process image
		inputs = self.processor(images=[image], return_tensors="pt").to(self.model.device)
		
		# Get image features using SigLIP method
		with torch.no_grad():
			feats = self.model.get_image_features(**inputs)  # [1, 768]
		
		# L2 normalize (optional but recommended)
		feats = torch.nn.functional.normalize(feats, p=2, dim=-1)
		
		# Convert to list of floats
		return feats.squeeze(0).cpu().tolist() 