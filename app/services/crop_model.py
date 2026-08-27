import os
import cv2
import numpy as np
from typing import Dict, Tuple

# Supported Classes
_CROPS = ["Rice", "Maize", "Cotton", "Groundnut", "Sugarcane"]
_STAGES = ["Germination", "Vegetative", "Flowering", "Maturity"]

# Centroid feature templates (14-dimensional feature vectors)
# Features 0-7: Original HSV & Edge features
# Features 8-9: GLCM Contrast, GLCM Homogeneity
# Features 10-13: Vertical-to-Horizontal Edge Ratio, Edge Row Var, Edge Col Var, Quad Diff
_CENTROIDS = {
    # Rice
    ("Rice", "Germination"): [0.08, 0.30, 0.40, 0.05, 0.70, 0.02, 0.01, 0.02, 0.50, 0.30, 0.50, 0.05, 0.05, 0.02],
    ("Rice", "Vegetative"):  [0.33, 0.70, 0.60, 0.85, 0.02, 0.03, 0.01, 0.08, 0.20, 0.60, 0.65, 0.08, 0.22, 0.03],
    ("Rice", "Flowering"):   [0.25, 0.60, 0.60, 0.60, 0.02, 0.20, 0.01, 0.10, 0.30, 0.50, 0.60, 0.08, 0.18, 0.03],
    ("Rice", "Maturity"):    [0.15, 0.70, 0.70, 0.05, 0.02, 0.80, 0.01, 0.12, 0.40, 0.40, 0.55, 0.05, 0.12, 0.02],

    # Maize
    ("Maize", "Germination"): [0.08, 0.30, 0.40, 0.04, 0.72, 0.01, 0.01, 0.02, 0.50, 0.30, 0.50, 0.05, 0.05, 0.02],
    ("Maize", "Vegetative"):  [0.30, 0.65, 0.55, 0.80, 0.02, 0.05, 0.01, 0.07, 0.22, 0.58, 0.62, 0.07, 0.25, 0.03],
    ("Maize", "Flowering"):   [0.23, 0.55, 0.60, 0.55, 0.02, 0.15, 0.02, 0.09, 0.32, 0.48, 0.58, 0.07, 0.20, 0.03],
    ("Maize", "Maturity"):    [0.16, 0.60, 0.65, 0.10, 0.02, 0.70, 0.01, 0.10, 0.38, 0.42, 0.55, 0.06, 0.15, 0.02],

    # Cotton
    ("Cotton", "Germination"): [0.08, 0.30, 0.40, 0.03, 0.75, 0.01, 0.01, 0.03, 0.52, 0.28, 0.50, 0.04, 0.04, 0.02],
    ("Cotton", "Vegetative"):  [0.32, 0.60, 0.50, 0.70, 0.02, 0.04, 0.02, 0.14, 0.40, 0.40, 0.52, 0.12, 0.12, 0.04],
    ("Cotton", "Flowering"):   [0.28, 0.50, 0.60, 0.50, 0.02, 0.08, 0.25, 0.16, 0.42, 0.38, 0.52, 0.10, 0.10, 0.04],
    ("Cotton", "Maturity"):    [0.20, 0.35, 0.70, 0.15, 0.02, 0.08, 0.45, 0.18, 0.45, 0.35, 0.50, 0.08, 0.08, 0.03],

    # Sugarcane (Upright Grass Structure)
    ("Sugarcane", "Germination"): [0.08, 0.30, 0.40, 0.05, 0.68, 0.01, 0.01, 0.02, 0.45, 0.35, 0.55, 0.04, 0.08, 0.02],
    ("Sugarcane", "Vegetative"):  [0.35, 0.75, 0.65, 0.90, 0.01, 0.02, 0.01, 0.04, 0.15, 0.65, 0.70, 0.05, 0.30, 0.02],
    ("Sugarcane", "Flowering"):   [0.32, 0.65, 0.65, 0.75, 0.01, 0.08, 0.05, 0.06, 0.20, 0.60, 0.68, 0.05, 0.28, 0.02],
    ("Sugarcane", "Maturity"):    [0.22, 0.55, 0.60, 0.40, 0.02, 0.35, 0.02, 0.08, 0.30, 0.50, 0.60, 0.04, 0.20, 0.02],

    # Groundnut (Round broadleaf clusters)
    ("Groundnut", "Germination"): [0.08, 0.30, 0.40, 0.06, 0.70, 0.02, 0.01, 0.03, 0.48, 0.32, 0.50, 0.04, 0.04, 0.02],
    ("Groundnut", "Vegetative"):  [0.34, 0.72, 0.55, 0.88, 0.01, 0.02, 0.01, 0.06, 0.45, 0.35, 0.50, 0.10, 0.10, 0.02],
    ("Groundnut", "Flowering"):   [0.27, 0.68, 0.58, 0.68, 0.01, 0.18, 0.01, 0.08, 0.42, 0.38, 0.50, 0.08, 0.08, 0.02],
    ("Groundnut", "Maturity"):    [0.18, 0.60, 0.60, 0.25, 0.02, 0.55, 0.01, 0.09, 0.40, 0.40, 0.48, 0.06, 0.08, 0.02],

    # Non-Agricultural / Generic Unknown templates
    ("Unknown", "N/A"): [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
}


def extract_features(image_path: str) -> np.ndarray:
    """
    Preprocess image and extract a 14-dimensional feature vector:
    - 0-2: Hue, Saturation, Value averages (0-1)
    - 3-6: Green, Brown, Yellow, White pixel ratios
    - 7: Edge density
    - 8-9: GLCM Contrast & Homogeneity
    - 10-13: Canny directional ratio, Row variance, Col variance, Quadrant difference
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Unable to read image at: {image_path}")

    # Image Quality / Sharpness Check: Laplacian variance
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 5.0: # Sharpness threshold
        # Re-raise or mark features as extremely low quality to trigger Unknown
        return np.zeros(14, dtype=np.float32)

    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h_band = hsv[:, :, 0].astype(np.float32)
    s_band = hsv[:, :, 1].astype(np.float32)
    v_band = hsv[:, :, 2].astype(np.float32)

    # Global color averages (scaled to 0-1)
    hue_mean = float(np.mean(h_band)) / 180.0
    sat_mean = float(np.mean(s_band)) / 255.0
    val_mean = float(np.mean(v_band)) / 255.0

    # Color range masks
    # Green (vegetation) Hue range 35-85, Saturation/Value > 40
    green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
    green_ratio = float(np.sum(green_mask > 0)) / green_mask.size

    # Brown (soil/germination) Hue range 5-20, Saturation/Value > 40
    brown_mask = cv2.inRange(hsv, (5, 40, 40), (20, 255, 255))
    brown_ratio = float(np.sum(brown_mask > 0)) / brown_mask.size

    # Yellowish (dry crop/flowering/maturity) Hue range 21-34
    yellow_mask = cv2.inRange(hsv, (21, 40, 40), (34, 255, 255))
    yellow_ratio = float(np.sum(yellow_mask > 0)) / yellow_mask.size

    # White (light bolls/flowering) Low Saturation, High Value
    white_mask = cv2.inRange(hsv, (0, 0, 190), (180, 45, 255))
    white_ratio = float(np.sum(white_mask > 0)) / white_mask.size

    # Canny Edge Density
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0)) / edges.size

    # --- GLCM Texture Extraction (Raw NumPy Implementation) ---
    # Resize and quantize grayscale to 16 levels to make GLCM computation lightweight
    gray_resized = cv2.resize(gray, (64, 64))
    gray_q = (gray_resized // 16).astype(np.int32)
    
    # Compute 16x16 GLCM with offset dx=1, dy=0 (horizontal adjacency)
    glcm = np.zeros((16, 16), dtype=np.float32)
    for i in range(16):
        for j in range(16):
            glcm[i, j] = np.sum((gray_q[:, :-1] == i) & (gray_q[:, 1:] == j))
            
    # Normalize GLCM matrix
    glcm_sum = np.sum(glcm)
    if glcm_sum > 0:
        glcm /= glcm_sum

    # Calculate Contrast and Homogeneity
    contrast = 0.0
    homogeneity = 0.0
    for i in range(16):
        for j in range(16):
            val = glcm[i, j]
            diff_sq = (i - j) ** 2
            contrast += val * diff_sq
            homogeneity += val / (1.0 + diff_sq)
            
    # Scale contrast to 0-1 (max theoretical is 15^2 = 225)
    contrast_norm = contrast / 225.0

    # --- Canny Directional Projections ---
    # Vertical/Horizontal Sobel gradients to compute directional edge ratio
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag_x = np.sum(np.abs(sobel_x) > 30)
    mag_y = np.sum(np.abs(sobel_y) > 30)
    
    edge_ratio = float(mag_x) / (float(mag_y) + 1e-5)
    edge_ratio_norm = edge_ratio / (1.0 + edge_ratio)

    # Edge Row & Column Histograms
    row_sums = np.sum(edges > 0, axis=1).astype(np.float32)
    col_sums = np.sum(edges > 0, axis=0).astype(np.float32)
    
    # Normalize histograms
    if np.sum(row_sums) > 0: row_sums /= np.max(row_sums)
    if np.sum(col_sums) > 0: col_sums /= np.max(col_sums)
    
    row_var = float(np.var(row_sums)) if len(row_sums) > 0 else 0.0
    col_var = float(np.var(col_sums)) if len(col_sums) > 0 else 0.0

    # Quadrant Difference (left vs right half edge density)
    half_w = edges.shape[1] // 2
    left_edges = float(np.sum(edges[:, :half_w] > 0))
    right_edges = float(np.sum(edges[:, half_w:] > 0))
    quad_diff = abs(left_edges - right_edges) / (edges.size + 1e-5)

    return np.array([
        hue_mean, sat_mean, val_mean,
        green_ratio, brown_ratio, yellow_ratio, white_ratio,
        edge_density,
        contrast_norm, homogeneity,
        edge_ratio_norm, row_var, col_var, quad_diff
    ], dtype=np.float32)


def generate_dataset() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates a 14-dimensional trained dataset of 120 samples by adding Gaussian noise
    to the centroid definitions, creating a realistic distribution.
    """
    X = []
    y_crop = []
    y_stage = []

    np.random.seed(42) # Deterministic data generation

    # Generate 6 samples per crop/stage combination
    for (crop, stage), centroid in _CENTROIDS.items():
        n_samples = 15 if crop == "Unknown" else 6
        for _ in range(n_samples):
            # Add Gaussian noise with standard deviation 0.02, clipped between 0 and 1
            noise = np.random.normal(0, 0.02, len(centroid))
            sample = np.clip(np.array(centroid) + noise, 0.0, 1.0)
            X.append(sample)
            y_crop.append(crop)
            y_stage.append(stage)

    return np.array(X, dtype=np.float32), np.array(y_crop), np.array(y_stage)


# Load dataset in memory
_X_TRAIN, _Y_CROP_TRAIN, _Y_STAGE_TRAIN = generate_dataset()


class KNNClassifier:
    """
    Lightweight, robust KNN classifier implemented in NumPy on 14D features.
    """
    def __init__(self, k: int = 5):
        self.k = k

    def predict(self, x: np.ndarray) -> Tuple[str, float, str, float]:
        # If input image failed sharpness/quality checks, return Unknown immediately
        if np.sum(x) == 0.0:
            return "Unknown", 0.0, "Needs better image", 0.0

        # Compute Euclidean distance to all training samples in 14D space
        distances = np.sqrt(np.sum((_X_TRAIN - x) ** 2, axis=1))

        # Get indices of K nearest neighbors
        nearest_indices = np.argsort(distances)[:self.k]
        nearest_dist = distances[nearest_indices]

        # Get class labels of neighbors
        crops = _Y_CROP_TRAIN[nearest_indices]
        stages = _Y_STAGE_TRAIN[nearest_indices]

        # 1. Majority vote for Crop
        unique_crops, crop_counts = np.unique(crops, return_counts=True)
        pred_crop = unique_crops[np.argmax(crop_counts)]
        crop_conf = float(np.max(crop_counts)) / self.k

        # 2. Majority vote for Stage
        unique_stages, stage_counts = np.unique(stages, return_counts=True)
        pred_stage = unique_stages[np.argmax(stage_counts)]
        stage_conf = float(np.max(stage_counts)) / self.k

        # Average distance to the nearest neighbors
        avg_dist = float(np.mean(nearest_dist))

        # Unknown handling:
        # If the average distance is too high (> 0.65 in 14D space), or if the closest matching crop is Unknown,
        # or if the crop features are completely outside normal agricultural parameters (vegetation/soil is too low)
        # return Unknown.
        agricultural_score = x[3] + x[4] + x[5] + x[6] # Green + Brown + Yellow + White
        if avg_dist > 0.65 or pred_crop == "Unknown" or agricultural_score < 0.12:
            return "Unknown", 0.0, "Needs better image", 0.0

        return str(pred_crop), crop_conf, str(pred_stage), stage_conf


def predict_crop_and_stage(image_path: str) -> Dict:
    """
    Runs the full ML inference pipeline on the input image:
    1. Extracts 14D OpenCV features.
    2. Runs the NumPy 14D KNN classifier.
    3. Handles low confidence prediction and disease rules.
    """
    try:
        features = extract_features(image_path)
    except Exception:
        # Fallback if image loading completely failed
        return {
            "crop_name": "Unknown",
            "growth_stage": "Needs better image",
            "crop_confidence": 0.0,
            "stage_confidence": 0.0,
            "health_status": "Unhealthy",
            "disease": "Image Load Error"
        }

    # Run KNN Inference
    knn = KNNClassifier(k=5)
    crop, crop_conf, stage, stage_conf = knn.predict(features)

    # Translate confidences to percentages
    crop_conf_pct = round(crop_conf * 100, 1)
    stage_conf_pct = round(stage_conf * 100, 1)

    # Health status based on vegetation / NDVI (Greenness ratio proxy)
    green_ratio = features[3]
    brown_ratio = features[4]
    white_ratio = features[6]
    edge_density = features[7]

    if crop == "Unknown":
        health_status = "Unhealthy"
        disease = "Non-Agricultural/Unknown"
    else:
        if green_ratio > 0.40:
            health_status = "Healthy"
        elif green_ratio > 0.18:
            health_status = "At Risk"
        else:
            health_status = "Unhealthy"

        # Disease Identification heuristics
        disease = "None"
        if crop == "Rice" and stage in ["Vegetative", "Flowering"]:
            # High brown spots on green rice leaves indicates Leaf Blast
            if brown_ratio > 0.06 and green_ratio > 0.35:
                disease = "Leaf Blast"
                health_status = "Unhealthy"
        elif crop == "Cotton" and stage in ["Flowering", "Maturity"]:
            # Low white ratio combined with extremely high edge/withered texture indicates Boll Rot
            if white_ratio < 0.08 and edge_density > 0.15:
                disease = "Boll Rot"
                health_status = "Unhealthy"
        elif crop == "Groundnut" and stage == "Vegetative":
            # High yellowing spots on groundnut leaves indicates Leaf Spot disease
            if features[5] > 0.10 and green_ratio > 0.40:
                disease = "Leaf Spot"
                health_status = "At Risk"

    return {
        "crop_name": crop,
        "growth_stage": stage,
        "crop_confidence": crop_conf_pct,
        "stage_confidence": stage_conf_pct,
        "health_status": health_status,
        "disease": disease
    }
