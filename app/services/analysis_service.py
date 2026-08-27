import os
import cv2
import numpy as np
from typing import Dict

from .crop_model import predict_crop_and_stage

_DISTRICTS = ["Davanagere", "Haveri", "Dharwad", "Gadag", "Belagavi", "Ballari"]

# Setup color lookup table for NDVI visualization (BGR format)
_NDVI_LUT = np.zeros((256, 1, 3), dtype=np.uint8)
for i in range(256):
    if i < 100:
        # Red to Yellow-ish
        r = 255
        g = int((i / 100.0) * 220)
        b = 30
    elif i < 185:
        # Yellow to Bright Green
        r = int((1.0 - (i - 100) / 85.0) * 255)
        g = 255
        b = 30
    else:
        # Bright Green to Deep Forest Green
        r = 0
        g = int((1.0 - 0.5 * (i - 185) / 70.0) * 255)
        b = 0
    _NDVI_LUT[i, 0] = [b, g, r] # BGR


def run_analysis(image_path: str) -> Dict:
    """
    Performs real OpenCV-based NDVI simulation and band analysis on the uploaded image.
    Then, invokes the NumPy-based crop and growth-stage KNN prediction pipeline.
    """
    # 1. Load image
    img = cv2.imread(image_path)
    if img is None:
        # Fallback if image load failed
        return {
            "crop": "Unknown",
            "crop_name": "Unknown",
            "district": "Unknown",
            "area_acres": 0.0,
            "growth_stage": "Needs better image",
            "health_status": "Unhealthy",
            "harvest_in_days": 0,
            "confidence": 0.0,
            "crop_confidence": 0.0,
            "stage_confidence": 0.0,
            "disease": "Image Load Error",
            "avg_ndvi": 0.0,
            "min_ndvi": 0.0,
            "max_ndvi": 0.0,
            "boundary_geojson": _get_default_boundary(),
            "ndvi_image_path": None,
        }

    # 2. Simulate NDVI using RGB bands: G is green reflectance, R is red absorption
    # OpenCV loads images in BGR format
    b_band = img[:, :, 0].astype(np.float32)
    g_band = img[:, :, 1].astype(np.float32)
    r_band = img[:, :, 2].astype(np.float32)

    # NDVI = (Green - Red) / (Green + Red)
    denominator = g_band + r_band + 1e-5
    ndvi_array = (g_band - r_band) / denominator

    # Clip values to range -1.0 to 1.0
    ndvi_array = np.clip(ndvi_array, -1.0, 1.0)

    # Calculate real stats
    mean_val = float(np.mean(ndvi_array))
    min_val = float(np.min(ndvi_array))
    max_val = float(np.max(ndvi_array))

    # 3. Create NDVI Visual Heatmap Image
    # Scale from [-1, 1] to [0, 255]
    ndvi_scaled = (((ndvi_array + 1.0) / 2.0) * 255.0).astype(np.uint8)
    
    # Apply custom green-to-red lookup table (requires 3-channel input for a 3-channel LUT)
    ndvi_scaled_3ch = cv2.merge([ndvi_scaled, ndvi_scaled, ndvi_scaled])
    ndvi_colored = cv2.LUT(ndvi_scaled_3ch, _NDVI_LUT)

    # Save visual NDVI heatmap
    directory, original_name = os.path.split(image_path)
    ndvi_name = f"ndvi_{original_name}"
    ndvi_save_path = os.path.join(directory, ndvi_name)
    cv2.imwrite(ndvi_save_path, ndvi_colored)

    # 4. Predict Crop & Stage using NumPy KNN classifier
    pred = predict_crop_and_stage(image_path)

    # Deterministic calculation of fields
    stage = pred["growth_stage"]
    if stage == "Germination":
        harvest_in_days = 90
    elif stage == "Vegetative":
        harvest_in_days = 60
    elif stage == "Flowering":
        harvest_in_days = 30
    elif stage == "Maturity":
        harvest_in_days = 10
    else:
        harvest_in_days = 0

    # Deterministic area based on average NDVI score
    area_acres = round(1.2 + abs(mean_val) * 3.1, 1)

    # Deterministic district based on image name hash
    district = _DISTRICTS[sum(ord(c) for c in original_name) % len(_DISTRICTS)]

    return {
        "crop": pred["crop_name"],  # legacy support
        "crop_name": pred["crop_name"],
        "district": district,
        "area_acres": area_acres,
        "growth_stage": pred["growth_stage"],
        "health_status": pred["health_status"],
        "harvest_in_days": harvest_in_days,
        "confidence": pred["crop_confidence"],  # legacy support
        "crop_confidence": pred["crop_confidence"],
        "stage_confidence": pred["stage_confidence"],
        "disease": pred["disease"],
        "avg_ndvi": round(mean_val, 2),
        "min_ndvi": round(min_val, 2),
        "max_ndvi": round(max_val, 2),
        "boundary_geojson": _get_default_boundary(),
        "ndvi_image_path": ndvi_save_path,
    }


def _get_default_boundary() -> Dict:
    return {
        "type": "Polygon",
        "coordinates": [[
            [75.9200, 14.4650], [75.9235, 14.4660],
            [75.9230, 14.4620], [75.9190, 14.4615],
            [75.9200, 14.4650],
        ]],
    }
