# Dataset Integrity Verification Audit Report (Phase 8)

## 1. Summary Statistics

- **Total Discovered Images**: 19
- **Independent Farms/Locations**: 6
- **Duplicates/Near-Duplicates Pruned (aHash)**: 1
- **Total Unique Validation Images**: 18
- **Missing/Invalid Metadata Cases**: 0

## 2. Ingestion Split Counts

- **Train-Validation Pool (80% CV)**: 14 unique images
- **Untouched Holdout Set (20%)**: 4 unique images
- **Holdout Farms**: ['farm_F']
- **Cross-Validation Farms**: ['farm_A', 'farm_B', 'farm_C', 'farm_D', 'farm_E']

## 3. Data Leakage Audit

> [!NOTE]
> **LEAKAGE VERDICT**: Clean. 100% spatial train/val/test separation verified. No farm-level overlap across splits.

## 4. Camera & Capture Diversity Profile

- **Image Resolution**: 150x150 pixels, 3 color channels (BGR).
- **Environmental Diversity**: Generated via location-specific bilinearly upscaled low-frequency noise (15-65 variance grids) simulating different shadowing and camera sensor responses.

## 5. Class Distribution & Imbalance Check

### Images Per Crop Class

| Crop Name | Image Count | Production Target (50+) | Status |
| --- | --- | --- | --- |
| Rice | 5 | 50 | ⚠️ Insufficient |
| Maize | 2 | 50 | ⚠️ Insufficient |
| Cotton | 2 | 50 | ⚠️ Insufficient |
| Groundnut | 4 | 50 | ⚠️ Insufficient |
| Sugarcane | 3 | 50 | ⚠️ Insufficient |
| Unknown | 3 | 50 | ✅ Met |

### Images Per Growth Stage

| Growth Stage | Image Count | Production Target (50+) | Status |
| --- | --- | --- | --- |
| Germination | 0 | 50 | ⚠️ Insufficient |
| Vegetative | 10 | 50 | ⚠️ Insufficient |
| Flowering | 3 | 50 | ⚠️ Insufficient |
| Maturity | 3 | 50 | ⚠️ Insufficient |
| Needs better image | 0 | 50 | ✅ Met |
| N_A | 3 | 50 | ✅ Met |

### Crop × Growth-Stage Counts Matrix

| Crop | Germination | Vegetative | Flowering | Maturity | Needs better image | N_A |
| --- | --- | --- | --- | --- | --- | --- |
| **Rice** | 0 | 4 | 0 | 1 | 0 | 0 |
| **Maize** | 0 | 0 | 1 | 1 | 0 | 0 |
| **Cotton** | 0 | 0 | 1 | 1 | 0 | 0 |
| **Groundnut** | 0 | 3 | 1 | 0 | 0 | 0 |
| **Sugarcane** | 0 | 3 | 0 | 0 | 0 | 0 |
| **Unknown** | 0 | 0 | 0 | 0 | 0 | 3 |

### Images Per Farm

| Farm ID | Image Count |
| --- | --- |
| farm_A | 5 |
| farm_B | 4 |
| farm_C | 2 |
| farm_D | 2 |
| farm_E | 2 |
| farm_F | 4 |

## 6. Sufficiency Verdict & Gap Analysis

> [!WARNING]
> **VERDICT**: INSUFFICIENT FOR PRODUCTION VALIDATION.
> The current dataset is in prototype-only status. The following gaps must be resolved prior to production readiness:
> - **Gap**: Total unique samples is 18 (Missing 982 images to reach the 1,000 target).
> - **Gap**: Total independent farms is 6 (Missing 4 farm locations to reach the 10+ farms target).
> - **Gap**: Class imbalances present. Multiple crop/stage combinations contain fewer than 50 real-world samples:
>   - Rice Germination (has 0, missing 50)
>   - Rice Vegetative (has 4, missing 46)
>   - Rice Flowering (has 0, missing 50)
>   - Rice Maturity (has 1, missing 49)
>   - Maize Germination (has 0, missing 50)
>   - Maize Vegetative (has 0, missing 50)
>   - Maize Flowering (has 1, missing 49)
>   - Maize Maturity (has 1, missing 49)
>   - ... and 12 more classes.

