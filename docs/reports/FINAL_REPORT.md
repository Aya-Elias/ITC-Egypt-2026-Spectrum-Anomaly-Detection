# 📡 AI-Powered Spectrum Anomaly Detection System
## Technical Report — ITC-EGYPT 2026
### Intelligent Software Systems Track

---

<div align="center">

![Accuracy](https://img.shields.io/badge/Accuracy-93.47%25-brightgreen?style=for-the-badge)
![Model](https://img.shields.io/badge/Model-EfficientNet--B0-blue?style=for-the-badge)
![Framework](https://img.shields.io/badge/Framework-TensorFlow%202.x-orange?style=for-the-badge)
![Classes](https://img.shields.io/badge/Classes-3%20(Drone%20%7C%20Normal%20%7C%20Jamming)-purple?style=for-the-badge)

</div>

---

## 📌 Executive Summary

This report documents the complete development of an AI-powered system for **real-time RF spectrum anomaly detection**, capable of classifying radio frequency signals into three categories:

| Category | Description |
|----------|-------------|
| ✈️ **Drone** | Unmanned aerial vehicle RF signatures |
| 📡 **Normal** | Standard radio frequency signals |
| 🔴 **Jamming** | Intentional interference signals |

The system is built on **EfficientNet-B0** with ImageNet transfer learning, achieving **93.47% test accuracy** on 1,179 unseen samples. The model was trained on **7,860 balanced samples** (2,620 per class) sourced from three distinct public datasets.

---

## 🎯 Project Objectives

- Build a robust 3-class classifier for RF spectrum signals
- Achieve high accuracy while maintaining real-time inference **< 100ms**
- Design a Spectrogram-based pipeline compatible with SDR hardware (RTL-SDR)
- Fully document all steps for reproducibility and team integration

---

## 🗂️ Data Collection

| Class | Source | Original Size | Format |
|-------|--------|---------------|--------|
| ✈️ **Drone** | RFUAV — Hugging Face (`kitofrank/RFUAV`) | 19,088 spectrograms | 37 drone types, RGB images |
| 📡 **Normal** | RadioML 2018.01A — Kaggle | 2,555,904 IQ samples | 24 modulation types |
| 🔴 **Jamming** | UAVs Jamming Detection — Kaggle | 1,578 spectrograms | Passive scan (benign/malicious) |

> **Note:** Raw IQ samples from RadioML were converted to spectrograms using STFT (`nfft=256`, `hop=128`) prior to training.

---

## ⚙️ Data Preprocessing Pipeline

```
Raw Data
   │
   ├── Drone (RFUAV)          → Resize to 224×224 → Normalize /255
   ├── Normal (RadioML IQ)    → STFT → Spectrogram → Resize → Normalize
   └── Jamming (CSV/Images)   → FFT Features → Spectrogram → Normalize
                                          │
                                  Class Balancing
                              Drone 2,620 | Normal 2,620 | Jamming 2,620
                                          │
                                   Stratified Split
                              Train 70% | Val 15% | Test 15%
```

| Step | Description |
|------|-------------|
| **Resizing** | All images unified to `(224, 224, 3)` RGB |
| **Normalization** | Min-Max: `x / 255.0` → range `[0, 1]` |
| **Class Balancing** | 2,620 samples per class (total: 7,860) |
| **Dataset Split** | Train 5,502 / Val 1,179 / Test 1,179 with `stratify=True` |
| **Storage Format** | `.npy` files for fast batch loading via custom `DataGenerator` |

---

## 🧠 Model Architecture

```
Input (224, 224, 3)
       │
EfficientNet-B0 ← Pre-trained ImageNet weights (frozen initially)
       │
GlobalAveragePooling2D → (1280,)
       │
Dropout(0.3)
       │
Dense(128, activation='relu')
       │
Dropout(0.2)
       │
Dense(3, activation='softmax')
       │
Output: [P(Drone), P(Normal), P(Jamming)]
```

| Parameter | Value |
|-----------|-------|
| Base Model | EfficientNet-B0 |
| Pre-training | ImageNet |
| Trainable Parameters | 164,355 |
| Total Parameters | 4,213,926 |
| Input Shape | `(224, 224, 3)` |
| Output Shape | `(3,)` — Softmax probabilities |

---

## 🏋️ Training Configuration

| Setting | Value |
|---------|-------|
| Optimizer | Adam (`lr = 1e-3`) |
| Loss Function | Sparse Categorical Crossentropy |
| Batch Size | 32 |
| Max Epochs | 50 |
| Early Stopping | Patience = 10 (stopped at epoch 14) |
| Class Weights | Balanced — computed via `compute_class_weight('balanced')` |
| LR Scheduler | `ReduceLROnPlateau` (factor=0.5, patience=4) |
| Best Model | Saved via `ModelCheckpoint` on `val_accuracy` |

---

## 📊 Evaluation Results

### ✅ Final Test Accuracy: **93.47%** (1,102 / 1,179 correct)

### Classification Report

| Class | Precision | Recall | F1-Score | Support |
|-------|:---------:|:------:|:--------:|:-------:|
| ✈️ Drone | 1.00 | 0.80 | 0.89 | 393 |
| 📡 Normal | 0.97 | 1.00 | 0.98 | 393 |
| 🔴 Jamming | 0.86 | 1.00 | 0.92 | 393 |
| **Macro Avg** | **0.94** | **0.93** | **0.93** | **1,179** |

### Confusion Matrix

```
                  Predicted
                 Drone  Normal  Jamming
True  Drone  │  316  │   13  │   64  │
      Normal │    0  │  393  │    0  │
      Jamming│    0  │    0  │  393  │
```

- ✅ Normal: **Perfect recall** — 0 misclassifications
- ✅ Jamming: **Perfect recall** — 0 misclassifications
- ⚠️ Drone: **80% recall** — 64 samples misclassified as Jamming (spectral similarity)
- **Total Errors:** 77 / 1,179 (6.53%)

---

## 🧪 Ablation Study

| Experiment | Result |
|------------|--------|
| DroneRFa instead of RFUAV | ❌ Poor Drone recall — model ignored Drone class |
| Without class balancing | ❌ Strong bias toward Jamming |
| With data augmentation | ✅ Slight improvement in Drone recall |
| ViT-B/16 (Vision Transformer) | ➖ No significant gain — domain mismatch |
| Fine-tuning last 30 EfficientNet layers | ➖ Marginal gain — not deployed in final version |

---

## 📁 Model Artifacts

| File | Size | Description |
|------|------|-------------|
| `best_model.keras` | 18.6 MB | Final trained EfficientNet-B0 |
| `final_model.h5` | ~19 MB | HDF5 format for compatibility |
| `norm_params.npy` | < 1 KB | Min-Max parameters `([0,0,0], [255,255,255])` |
| `model_report.json` | < 1 KB | Accuracy, confusion matrix, metadata |
| `tfjs_model/` | ~20 MB | TensorFlow.js for browser deployment |

---

## 🔌 Integration Guide

### Python — Direct Inference

```python
from src.ai_model.predict import load_model_and_params, predict_single

model, min_val, max_val = load_model_and_params(
    "saved_models/best_model.keras",
    "saved_models/norm_params.npy"
)

result = predict_single(model, image_array, min_val, max_val)
# Returns:
# {
#   'class_name': 'Drone',
#   'confidence': 0.95,
#   'probabilities': {'Drone': 0.95, 'Normal': 0.03, 'Jamming': 0.02}
# }
```

### REST API — FastAPI Endpoint

```python
@app.post("/predict")
async def predict(file: UploadFile):
    img = preprocess_image(await file.read())
    return predict_single(model, img, min_val, max_val)
```

### SDR Hardware Pipeline

```
RTL-SDR Device
     │
  I/Q Samples (raw)
     │
  STFT Transform (nfft=256, hop=128)
     │
  Spectrogram Image (224×224×3)
     │
  EfficientNet-B0 Inference
     │
  Classification Result + Confidence Score
```

---

## 📂 Project Structure

```
src/ai_model/
├── saved_models/
│   ├── best_model.keras       ← Main model
│   ├── norm_params.npy        ← Normalization params
│   ├── model_report.json      ← Evaluation report
│   └── tfjs_model/            ← Browser deployment
├── predict.py                 ← Inference functions
├── model_loader.py            ← Model loading utilities
├── train.py                   ← Training script
├── data_preprocessing.py      ← Preprocessing pipeline
└── __init__.py

notebooks/
├── 01_data_exploration.ipynb
├── 02_model_training.ipynb
└── 03_results_analysis.ipynb

tests/
└── test_ai_model.py
```

---

## 🔮 Future Work

- [ ] Collect more Drone data to improve recall (80% → 90%+)
- [ ] Experiment with Contrastive Learning / Triplet Loss for Drone/Jamming separation
- [ ] Deploy to edge devices (Raspberry Pi + RTL-SDR)
- [ ] Extend to 5+ classes (LTE, Bluetooth, Wi-Fi, 5G NR)
- [ ] Add real-time confidence thresholding for alert system

---

## ✅ Conclusion

The system successfully classifies RF spectrum signals with **93.47% accuracy**, demonstrating strong performance on Normal and Jamming detection (F1 ≥ 0.92). The Drone class shows reliable precision (1.00) with moderate recall (0.80), a known challenge due to spectral overlap with Jamming signals.

The model is **production-ready**, exported in multiple formats, and fully integrated with the team's planned architecture including dashboard, API, database, and SDR hardware pipeline.

---

<div align="center">

| | |
|---|---|
| 📅 **Report Date** | April 25, 2026 |
| 👤 **Prepared by** | Goda Emad — Team Leader & AI Lead |
| 🏆 **Competition** | ITC-EGYPT 2026 |
| 🎯 **Track** | Intelligent Software Systems |

</div>
