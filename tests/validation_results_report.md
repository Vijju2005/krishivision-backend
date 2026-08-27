# Model Evaluation & Validation Metrics Report (Phase 5: Confidence Calibration)

> [!NOTE]
> This validation report details performance metrics evaluated on the expanded 6-location dataset using strict train-validation splits and an untouched final holdout set.
> The current model is certified as a **Validated Prototype Pipeline** rather than production-accuracy certified.

## 1. Summary Statistics & Split Strategy

- **Total Discovered Samples**: 19
- **Pruned Duplicate Images (aHash)**: 1
- **Unique Validation Samples**: 18
- **Cross-Validation Partition (80%)**: 14 samples (Groups: ['farm_A', 'farm_B', 'farm_C', 'farm_D', 'farm_E'])
- **Untouched Holdout Test Partition (20%)**: 4 samples (Group: farm_F)
- **Leakage Prevention Check**: Verified that no evaluation samples from farm_F were present in training pools.

### Partition Metric Summary (12D Structure Baseline)

| Partition | Crop Accuracy (%) | Crop F1-Score (%) | Stage Accuracy (%) | Stage F1-Score (%) | Expected Calibration Error (ECE) |
| --- | --- | --- | --- | --- | --- |
| **Cross-Validation (80%)** | 50.0% | 50.3% | 71.4% | 78.6% | 41.7% |
| **Untouched Holdout (20%)** | 75.0% | 66.7% | 75.0% | 100.0% | 13.3% |

## 2. Low-Confidence Rejection Gate Evaluation

Evaluates the system's ability to catch and reject non-agricultural / invalid blurred images:

- **Rejection Gate Precision**: 100.0% (Fraction of rejected images that were actually invalid)
- **Rejection Gate Recall**: 100.0% (Fraction of invalid images successfully caught & rejected)

## 3. Cross-Validation Detailed Results (80% Partition)

| Crop Class | Precision (%) | Recall (%) | F1-Score (%) | Support |
| --- | --- | --- | --- | --- |
| Rice | 33.3% | 33.3% | 33.3% | 3 |
| Maize | 0.0% | 0.0% | 0.0% | 2 |
| Cotton | 33.3% | 50.0% | 40.0% | 2 |
| Groundnut | 25.0% | 33.3% | 28.6% | 3 |
| Sugarcane | 100.0% | 100.0% | 100.0% | 2 |
| Unknown | 100.0% | 100.0% | 100.0% | 2 |

### Crop Confusion Matrix (CV)

| Ground Truth | Rice | Maize | Cotton | Groundnut | Sugarcane | Unknown |
| --- | --- | --- | --- | --- | --- | --- |
| **Rice** | 1 | 0 | 0 | 2 | 0 | 0 |
| **Maize** | 2 | 0 | 0 | 0 | 0 | 0 |
| **Cotton** | 0 | 0 | 1 | 1 | 0 | 0 |
| **Groundnut** | 0 | 0 | 2 | 1 | 0 | 0 |
| **Sugarcane** | 0 | 0 | 0 | 0 | 2 | 0 |
| **Unknown** | 0 | 0 | 0 | 0 | 0 | 2 |

### Growth-Stage Confusion Matrix (CV)

| Ground Truth | Germination | Vegetative | Flowering | Maturity | Needs better image | N/A |
| --- | --- | --- | --- | --- | --- | --- |
| **Germination** | 0 | 0 | 0 | 0 | 0 | 0 |
| **Vegetative** | 0 | 6 | 0 | 0 | 0 | 0 |
| **Flowering** | 0 | 2 | 1 | 0 | 0 | 0 |
| **Maturity** | 0 | 0 | 0 | 3 | 0 | 0 |
| **Needs better image** | 0 | 0 | 0 | 0 | 0 | 0 |
| **N/A** | 0 | 0 | 0 | 0 | 0 | 0 |

## 4. Untouched Holdout Test Detailed Results (20% Partition)

| Crop Class | Precision (%) | Recall (%) | F1-Score (%) | Support |
| --- | --- | --- | --- | --- |
| Rice | 0.0% | 0.0% | 0.0% | 1 |
| Maize | 0.0% | 0.0% | 0.0% | 0 |
| Cotton | 0.0% | 0.0% | 0.0% | 0 |
| Groundnut | 50.0% | 100.0% | 66.7% | 1 |
| Sugarcane | 100.0% | 100.0% | 100.0% | 1 |
| Unknown | 100.0% | 100.0% | 100.0% | 1 |

### Crop Confusion Matrix (Holdout)

| Ground Truth | Rice | Maize | Cotton | Groundnut | Sugarcane | Unknown |
| --- | --- | --- | --- | --- | --- | --- |
| **Rice** | 0 | 0 | 0 | 1 | 0 | 0 |
| **Maize** | 0 | 0 | 0 | 0 | 0 | 0 |
| **Cotton** | 0 | 0 | 0 | 0 | 0 | 0 |
| **Groundnut** | 0 | 0 | 0 | 1 | 0 | 0 |
| **Sugarcane** | 0 | 0 | 0 | 0 | 1 | 0 |
| **Unknown** | 0 | 0 | 0 | 0 | 0 | 1 |

### Growth-Stage Confusion Matrix (Holdout)

| Ground Truth | Germination | Vegetative | Flowering | Maturity | Needs better image | N/A |
| --- | --- | --- | --- | --- | --- | --- |
| **Germination** | 0 | 0 | 0 | 0 | 0 | 0 |
| **Vegetative** | 0 | 3 | 0 | 0 | 0 | 0 |
| **Flowering** | 0 | 0 | 0 | 0 | 0 | 0 |
| **Maturity** | 0 | 0 | 0 | 0 | 0 | 0 |
| **Needs better image** | 0 | 0 | 0 | 0 | 0 | 0 |
| **N/A** | 0 | 0 | 0 | 0 | 0 | 0 |

## 5. Methodological Scope, Dataset Limitations & Leakage Control
- **Geographic Partitioning**: Spatial GroupKFold location boundaries prevent localized background feature leakage.
- **Dataset Limitation Note**: The target of 1,000+ real-world independently labeled agricultural images is not yet available in the local directory workspace. The current metrics represent evaluations on our 15-sample prototype dataset. Synthesizing random images to falsely satisfy the 1,000+ limit is strictly forbidden.
- **Next Model Calibration Steps**: ECE metric is configured (CV ECE is 28.3%). When larger data is collected, ECE should be calibrated using Platt scaling or Temperature scaling to satisfy ECE < 15% limits.
