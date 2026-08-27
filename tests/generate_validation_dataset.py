import os
import cv2
import numpy as np

# Folder structure: validation_dataset/<group_id>/<crop>/<stage>/*.png
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "validation_dataset"))


def add_low_freq_noise_and_save(path: str, img: np.ndarray, noise_range: int):
    noise_small = np.random.randint(-noise_range, noise_range + 1, size=(10, 10, 3)).astype(np.float32)
    noise_large = cv2.resize(noise_small, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    img_noisy = np.clip(img.astype(np.int16) + noise_large.astype(np.int16), 0, 255).astype(np.uint8)
    cv2.imwrite(path, img_noisy)


def setup_dataset():
    print(f"Setting up expanded 6-farm validation dataset in {_BASE_DIR}...")
    
    # Clean up old directory structure
    import shutil
    if os.path.exists(_BASE_DIR):
        shutil.rmtree(_BASE_DIR)
        
    os.makedirs(_BASE_DIR, exist_ok=True)

    np.random.seed(42) # Deterministic generation

    # === FARM A ===
    farm_a = os.path.join(_BASE_DIR, "farm_A")
    
    # Rice Veg
    rice_veg_a = os.path.join(farm_a, "Rice", "Vegetative")
    os.makedirs(rice_veg_a, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [60, 210, 60]
    for _ in range(50):
        cx, cy = np.random.randint(5, 145, size=2)
        r = np.random.randint(3, 8)
        cv2.circle(img, (cx, cy), r, [15, 120, 15], -1)
    add_low_freq_noise_and_save(os.path.join(rice_veg_a, "rice_veg_1.png"), img, noise_range=20)
    # Duplicate for aHash validation
    import shutil
    shutil.copyfile(os.path.join(rice_veg_a, "rice_veg_1.png"), os.path.join(rice_veg_a, "rice_veg_1_dup.png"))
    
    # Sugarcane Veg
    sugarcane_veg_a = os.path.join(farm_a, "Sugarcane", "Vegetative")
    os.makedirs(sugarcane_veg_a, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [30, 180, 30]
    for x in range(10, 140, 20):
        cv2.line(img, (x, 5), (x, 145), [10, 90, 10], 4)
        cv2.line(img, (x+6, 5), (x+6, 145), [120, 240, 120], 3)
    add_low_freq_noise_and_save(os.path.join(sugarcane_veg_a, "sugarcane_veg_1.png"), img, noise_range=15)
    
    # Groundnut Veg
    groundnut_veg_a = os.path.join(farm_a, "Groundnut", "Vegetative")
    os.makedirs(groundnut_veg_a, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [5, 45, 5]
    for _ in range(55):
        cx, cy = np.random.randint(10, 140, size=2)
        r = np.random.randint(8, 16)
        cv2.circle(img, (cx, cy), r, [180, 255, 180], -1)
        cv2.circle(img, (cx, cy), r, [1, 20, 1], 2)
    add_low_freq_noise_and_save(os.path.join(groundnut_veg_a, "groundnut_veg_1.png"), img, noise_range=65)
    
    # Unknown
    unknown_na_a = os.path.join(farm_a, "Unknown", "N_A")
    os.makedirs(unknown_na_a, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [128, 128, 128]
    add_low_freq_noise_and_save(os.path.join(unknown_na_a, "non_agri_1.png"), img, noise_range=5)

    # === FARM B ===
    farm_b = os.path.join(_BASE_DIR, "farm_B")
    
    # Rice Veg
    rice_veg_b = os.path.join(farm_b, "Rice", "Vegetative")
    os.makedirs(rice_veg_b, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [65, 215, 65]
    for _ in range(50):
        cx, cy = np.random.randint(5, 145, size=2)
        r = np.random.randint(3, 8)
        cv2.circle(img, (cx, cy), r, [20, 130, 20], -1)
    add_low_freq_noise_and_save(os.path.join(rice_veg_b, "rice_veg_2.png"), img, noise_range=20)
    
    # Sugarcane Veg
    sugarcane_veg_b = os.path.join(farm_b, "Sugarcane", "Vegetative")
    os.makedirs(sugarcane_veg_b, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [28, 175, 28]
    for x in range(12, 138, 18):
        cv2.line(img, (x, 10), (x, 140), [8, 85, 8], 4)
        cv2.line(img, (x+5, 10), (x+5, 140), [115, 235, 115], 3)
    add_low_freq_noise_and_save(os.path.join(sugarcane_veg_b, "sugarcane_veg_2.png"), img, noise_range=15)
    
    # Groundnut Veg
    groundnut_veg_b = os.path.join(farm_b, "Groundnut", "Vegetative")
    os.makedirs(groundnut_veg_b, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [8, 48, 8]
    for _ in range(55):
        cx, cy = np.random.randint(10, 140, size=2)
        r = np.random.randint(8, 16)
        cv2.circle(img, (cx, cy), r, [175, 250, 175], -1)
        cv2.circle(img, (cx, cy), r, [2, 22, 2], 2)
    add_low_freq_noise_and_save(os.path.join(groundnut_veg_b, "groundnut_veg_2.png"), img, noise_range=65)
    
    # Unknown
    unknown_na_b = os.path.join(farm_b, "Unknown", "N_A")
    os.makedirs(unknown_na_b, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [50, 50, 200]
    add_low_freq_noise_and_save(os.path.join(unknown_na_b, "non_agri_2.png"), img, noise_range=5)

    # === FARM C ===
    farm_c = os.path.join(_BASE_DIR, "farm_C")
    
    # Rice Maturity
    rice_mat_c = os.path.join(farm_c, "Rice", "Maturity")
    os.makedirs(rice_mat_c, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [10, 150, 170]
    for _ in range(35):
        cx, cy = np.random.randint(5, 145, size=2)
        r = np.random.randint(4, 9)
        cv2.circle(img, (cx, cy), r, [150, 240, 255], -1)
    add_low_freq_noise_and_save(os.path.join(rice_mat_c, "rice_mat_1.png"), img, noise_range=20)
    
    # Cotton Flowering
    cotton_flow_c = os.path.join(farm_c, "Cotton", "Flowering")
    os.makedirs(cotton_flow_c, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [10, 100, 10]
    for _ in range(12):
        cx, cy = np.random.randint(15, 135, size=2)
        r = np.random.randint(12, 18)
        cv2.circle(img, (cx, cy), r, [255, 255, 255], -1)
    add_low_freq_noise_and_save(os.path.join(cotton_flow_c, "cotton_flow_1.png"), img, noise_range=25)

    # === FARM D ===
    farm_d = os.path.join(_BASE_DIR, "farm_D")
    
    # Maize Flowering
    maize_flow_d = os.path.join(farm_d, "Maize", "Flowering")
    os.makedirs(maize_flow_d, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [30, 160, 30]
    for x in range(15, 135, 25):
        cv2.line(img, (x, 10), (x, 140), [15, 110, 15], 5)
        cv2.circle(img, (x+2, 30), 6, [30, 200, 220], -1)
        cv2.circle(img, (x-2, 80), 5, [30, 200, 220], -1)
    add_low_freq_noise_and_save(os.path.join(maize_flow_d, "maize_flow_1.png"), img, noise_range=22)

    # Groundnut Flowering
    groundnut_flow_d = os.path.join(farm_d, "Groundnut", "Flowering")
    os.makedirs(groundnut_flow_d, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [25, 120, 25]
    for _ in range(35):
        cx, cy = np.random.randint(10, 140, size=2)
        r = np.random.randint(8, 16)
        cv2.circle(img, (cx, cy), r, [45, 185, 45], -1)
        if np.random.rand() > 0.5:
            cv2.circle(img, (cx+2, cy+2), 3, [30, 200, 220], -1)
    add_low_freq_noise_and_save(os.path.join(groundnut_flow_d, "groundnut_flow_1.png"), img, noise_range=25)

    # === FARM E ===
    farm_e = os.path.join(_BASE_DIR, "farm_E")
    
    # Maize Maturity
    maize_mat_e = os.path.join(farm_e, "Maize", "Maturity")
    os.makedirs(maize_mat_e, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [15, 140, 160]
    for x in range(12, 138, 20):
        cv2.line(img, (x, 5), (x, 145), [10, 100, 120], 4)
        cv2.line(img, (x+6, 5), (x+6, 145), [35, 185, 210], 2)
    add_low_freq_noise_and_save(os.path.join(maize_mat_e, "maize_mat_1.png"), img, noise_range=20)

    # Cotton Maturity
    cotton_mat_e = os.path.join(farm_e, "Cotton", "Maturity")
    os.makedirs(cotton_mat_e, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [20, 80, 110]
    for _ in range(15):
        cx, cy = np.random.randint(15, 135, size=2)
        r = np.random.randint(8, 14)
        cv2.circle(img, (cx, cy), r, [248, 248, 248], -1)
    add_low_freq_noise_and_save(os.path.join(cotton_mat_e, "cotton_mat_1.png"), img, noise_range=25)

    # === FARM F (UNTOUCHED HOLDOUT GROUP - 20%) ===
    farm_f = os.path.join(_BASE_DIR, "farm_F")
    
    # Rice Veg
    rice_veg_f = os.path.join(farm_f, "Rice", "Vegetative")
    os.makedirs(rice_veg_f, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [58, 208, 58]
    for _ in range(50):
        cx, cy = np.random.randint(5, 145, size=2)
        r = np.random.randint(3, 8)
        cv2.circle(img, (cx, cy), r, [18, 122, 18], -1)
    add_low_freq_noise_and_save(os.path.join(rice_veg_f, "rice_veg_f.png"), img, noise_range=20)

    # Sugarcane Veg
    sugarcane_veg_f = os.path.join(farm_f, "Sugarcane", "Vegetative")
    os.makedirs(sugarcane_veg_f, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [32, 182, 32]
    for x in range(10, 140, 20):
        cv2.line(img, (x, 5), (x, 145), [12, 92, 12], 4)
        cv2.line(img, (x+6, 5), (x+6, 145), [122, 242, 122], 3)
    add_low_freq_noise_and_save(os.path.join(sugarcane_veg_f, "sugarcane_veg_f.png"), img, noise_range=15)

    # Groundnut Veg
    groundnut_veg_f = os.path.join(farm_f, "Groundnut", "Vegetative")
    os.makedirs(groundnut_veg_f, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [6, 46, 6]
    for _ in range(55):
        cx, cy = np.random.randint(10, 140, size=2)
        r = np.random.randint(8, 16)
        cv2.circle(img, (cx, cy), r, [182, 255, 182], -1)
        cv2.circle(img, (cx, cy), r, [2, 22, 2], 2)
    add_low_freq_noise_and_save(os.path.join(groundnut_veg_f, "groundnut_veg_f.png"), img, noise_range=65)

    # Unknown
    unknown_na_f = os.path.join(farm_f, "Unknown", "N_A")
    os.makedirs(unknown_na_f, exist_ok=True)
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    img[:, :] = [128, 128, 128]
    add_low_freq_noise_and_save(os.path.join(unknown_na_f, "non_agri_f.png"), img, noise_range=5)

    print("Noise-augmented 6-farm validation dataset setup completed.")


if __name__ == "__main__":
    setup_dataset()
