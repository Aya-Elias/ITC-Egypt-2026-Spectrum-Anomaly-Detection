# 📡 AI-Powered Spectrum Anomaly Detection System
### ITC-EGYPT 2026 — Intelligent Software Systems Track

<div align="center">

![Accuracy](https://img.shields.io/badge/Accuracy-93.47%25-brightgreen?style=for-the-badge)
![Model](https://img.shields.io/badge/Model-EfficientNet--B0-blue?style=for-the-badge)
![Framework](https://img.shields.io/badge/Framework-TensorFlow%202.x-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)

</div>

---

## 🎯 Overview

An AI-powered real-time system for detecting anomalies in the RF (Radio Frequency) spectrum. The system classifies signals into three categories using deep learning:

| Class | Description | F1-Score |
|-------|-------------|:--------:|
| ✈️ **Drone** | Unmanned aerial vehicle RF signatures | 0.89 |
| 📡 **Normal** | Standard radio frequency signals | 0.98 |
| 🔴 **Jamming** | Intentional interference / jamming signals | 0.92 |

> **Final Test Accuracy: 93.47%** on 1,179 unseen samples

---

## 🏗️ System Architecture

```
RTL-SDR Hardware
      │
   I/Q Samples
      │
  STFT Transform
      │
 Spectrogram (224×224×3)
      │
 EfficientNet-B0
      │
 ┌────┴────┐
 │ FastAPI │ ← REST API
 └────┬────┘
      │
 ┌────┴──────────┐
 │ Dashboard     │ ← Streamlit UI
 │ AI Agent      │ ← Ollama LLM
 │ Alert System  │ ← Email / WhatsApp
 └───────────────┘
```

---

## 📂 Project Structure

```
ITC-Egypt-2026-Spectrum-Anomaly-Detection/
│
├── src/
│   ├── ai_model/               # 🧠 Core ML model
│   │   ├── saved_models/
│   │   │   ├── best_model.keras
│   │   │   ├── norm_params.npy
│   │   │   └── model_report.json
│   │   ├── predict.py
│   │   ├── train.py
│   │   └── data_preprocessing.py
│   │
│   ├── dashboard/              # 📊 Streamlit Dashboard
│   │   ├── app.py
│   │   └── pages/
│   │
│   ├── api/                    # 🔌 FastAPI Backend
│   │   ├── main.py
│   │   └── routes.py
│   │
│   ├── ai_agent/               # 🤖 LLM AI Agent (Ollama)
│   ├── signal_processing/      # 📶 STFT / IQ Processing
│   ├── hardware/               # 🔧 SDR Hardware Interface
│   ├── alerting/               # 🚨 Alert System
│   └── database/               # 🗄️ SQLite + Encrypted Storage
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_model_training.ipynb
│   └── 03_results_analysis.ipynb
│
├── data/
│   ├── raw/RadioML/
│   └── processed/spectrograms/
│
├── docs/
│   └── reports/FINAL_REPORT.md
│
├── tests/
├── requirements.txt
└── README.md
```

---

## 🗂️ Datasets

| Class | Source | Size | Link |
|-------|--------|------|------|
| ✈️ Drone | RFUAV — Hugging Face | 19,088 spectrograms | [kitofrank/RFUAV](https://huggingface.co/datasets/kitofrank/RFUAV) |
| 📡 Normal | RadioML 2018.01A — Kaggle | 2.5M IQ samples | [pinxau1000/radioml2018](https://www.kaggle.com/datasets/pinxau1000/radioml2018) |
| 🔴 Jamming | UAVs Jamming Detection | 1,578 spectrograms | [daniaherzalla/radio-frequency-jamming](https://www.kaggle.com/datasets/daniaherzalla/radio-frequency-jamming) |

---

## 🌐 Project Website

A professional static website is included in `website/` for showcasing SADAR's mission, architecture, model performance, and local setup.

```bash
python -m http.server 8080 -d website
# open http://localhost:8080
```

The site can be deployed directly to GitHub Pages, Netlify, Vercel, or any static hosting provider.

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/godaemade/ITC-Egypt-2026-Spectrum-Anomaly-Detection.git
cd ITC-Egypt-2026-Spectrum-Anomaly-Detection

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Dashboard
streamlit run src/dashboard/app.py

# 5. Run the API
uvicorn src.api.main:app --reload
```

---

## 🚀 Quick Inference

```python
from src.ai_model.predict import load_model_and_params, predict_single

# Load model
model, min_val, max_val = load_model_and_params(
    "src/ai_model/saved_models/best_model.keras",
    "src/ai_model/saved_models/norm_params.npy"
)

# Predict
result = predict_single(model, spectrogram_array, min_val, max_val)

print(result)
# {
#   'class_name': 'Drone',
#   'confidence': 0.95,
#   'probabilities': {'Drone': 0.95, 'Normal': 0.03, 'Jamming': 0.02}
# }
```

---

## 📊 Model Performance

```
Confusion Matrix:
                  Predicted
              Drone  Normal  Jamming
True  Drone │  316  │   13  │   64  │  ← 80% Recall
     Normal │    0  │  393  │    0  │  ← 100% Recall ✅
    Jamming │    0  │    0  │  393  │  ← 100% Recall ✅

Overall Accuracy: 93.47% (1,102/1,179)
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Classify a spectrogram image |
| `GET` | `/health` | System health check |
| `GET` | `/history` | Detection history |
| `WS` | `/ws/live` | Real-time WebSocket stream |

---

## 🧠 Model Details

| Parameter | Value |
|-----------|-------|
| Architecture | EfficientNet-B0 + Custom Head |
| Pre-training | ImageNet |
| Input Shape | `(224, 224, 3)` |
| Trainable Params | 164,355 |
| Total Params | 4,213,926 |
| Model Size | 18.6 MB |
| Inference Time | < 100ms (GPU) |

---

## 🔧 Hardware Integration

```python
# RTL-SDR → Spectrogram → Model
from src.hardware.rtl_sdr_reader import RTLSDRReader
from src.signal_processing.stft import iq_to_spectrogram
from src.ai_model.predict import predict_single

sdr = RTLSDRReader(center_freq=2.4e9, sample_rate=2.4e6)
iq_samples = sdr.read_samples(1024)
spectrogram = iq_to_spectrogram(iq_samples, nfft=256, hop=128)
result = predict_single(model, spectrogram, min_val, max_val)
```

---

## 📈 Results Summary

| Metric | Value |
|--------|-------|
| **Test Accuracy** | **93.47%** |
| Normal F1-Score | 0.98 |
| Jamming F1-Score | 0.92 |
| Drone F1-Score | 0.89 |
| Total Test Samples | 1,179 |
| Training Time | ~14 epochs (Early Stopping) |

---

## 👥 Team

| Role | Responsibility |
|------|----------------|
| **Goda Emad** — AI Lead | Model training, data pipeline, integration |
| Signal Processing Team | IQ → Spectrogram conversion, SDR interface |
| Backend Team | FastAPI, Database, Security |
| Frontend Team | Streamlit Dashboard, UI/UX |

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

> **Dataset Licenses:**
> - RadioML 2018.01A: CC BY-NC-SA 4.0
> - RFUAV: Research use only
> - RF Jamming Dataset: Kaggle Terms of Service

---

## 📚 References

1. O'Shea, T. J., & West, N. (2019). *Radio Machine Learning Dataset Generation with GNU Radio.* GNU Radio Conference.
2. Tan, M., & Le, Q. V. (2019). *EfficientNet: Rethinking Model Scaling for CNNs.* ICML 2019.
3. RadioML 2018.01A: https://www.deepsig.ai/datasets
4. RFUAV Dataset: https://huggingface.co/datasets/kitofrank/RFUAV

---

<div align="center">

**ITC-EGYPT 2026 — Intelligent Software Systems Track**

*Built with ❤️ by Team Goda Emad*

</div>
