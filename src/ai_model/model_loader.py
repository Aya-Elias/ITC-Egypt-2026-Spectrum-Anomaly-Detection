"""
model_loader.py
---------------
وظائف تحميل النموذج المدرب ومعاملات التطبيع من ملفات saved_models.

ملاحظة: هذا الملف يُستخدم في predict.py لتسهيل تحميل النموذج.
"""

import numpy as np
import tensorflow as tf
import os
import json

# ============================================
# تحميل النموذج
# ============================================
def load_model(model_path=None):
    """
    تحميل النموذج المدرب من مسار محدد أو المسار الافتراضي
    
    Args:
        model_path (str, optional): مسار ملف النموذج (.keras)
                                   إذا لم يُحدد، يبحث في المسار الافتراضي
    
    Returns:
        tf.keras.Model: النموذج المحمّل
    """
    if model_path is None:
        # المسار الافتراضي (نسبة لموقع الملف الحالي)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "saved_models", "best_model.keras")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    model = tf.keras.models.load_model(model_path)
    return model

# ============================================
# تحميل معاملات التطبيع
# ============================================
def load_norm_params(norm_path=None):
    """
    تحميل معاملات التطبيع (min, max) من ملف norm_params.npy
    
    Args:
        norm_path (str, optional): مسار ملف norm_params.npy
    
    Returns:
        tuple: (min_val, max_val) لكل قناة
    """
    if norm_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        norm_path = os.path.join(current_dir, "saved_models", "norm_params.npy")
    
    if not os.path.exists(norm_path):
        raise FileNotFoundError(f"Norm params not found at {norm_path}")
    
    norm_data = np.load(norm_path, allow_pickle=True).item()
    
    # دعم كل من Min-Max و Z-Score
    if 'min' in norm_data and 'max' in norm_data:
        # Min-Max normalization (المستخدم في التدريب)
        min_val = norm_data['min']
        max_val = norm_data['max']
        return min_val, max_val
    elif 'mean' in norm_data and 'std' in norm_data:
        # Z-Score normalization (للتوافق مع قيم ImageNet)
        # تحذير: يجب أن يكون التدريب استخدم Z-Score
        print("⚠️ Warning: Using Z-Score normalization. Ensure model was trained with Z-Score.")
        min_val = norm_data['mean'] - 3 * norm_data['std']  # تقريبي
        max_val = norm_data['mean'] + 3 * norm_data['std']
        return min_val, max_val
    else:
        raise ValueError("norm_params.npy must contain 'min'/'max' or 'mean'/'std'")

# ============================================
# تحميل تقرير النموذج
# ============================================
def load_model_report(report_path=None):
    """
    تحميل تقرير النموذج (accuracy, classification_report, إلخ)
    
    Args:
        report_path (str, optional): مسار ملف model_report.json
    
    Returns:
        dict: محتوى التقرير
    """
    if report_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        report_path = os.path.join(current_dir, "saved_models", "model_report.json")
    
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Model report not found at {report_path}")
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    return report

# ============================================
# تحميل كل شيء مرة واحدة
# ============================================
def load_all(model_path=None, norm_path=None, report_path=None):
    """
    تحميل النموذج، معاملات التطبيع، والتقرير مرة واحدة
    
    Returns:
        tuple: (model, min_val, max_val, report)
    """
    model = load_model(model_path)
    min_val, max_val = load_norm_params(norm_path)
    report = load_model_report(report_path)
    
    return model, min_val, max_val, report

# ============================================
# مثال الاستخدام
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("📦 تحميل النموذج والمعاملات")
    print("=" * 60)
    
    try:
        # تحميل كل شيء
        model, min_val, max_val, report = load_all()
        
        print("\n✅ Model loaded successfully!")
        print(f"   Input shape: {model.input_shape}")
        print(f"   Output classes: {model.output_shape[-1]}")
        print(f"\n📊 Normalization params (Min-Max):")
        print(f"   Min: {min_val}")
        print(f"   Max: {max_val}")
        print(f"\n📈 Model Report:")
        print(f"   Accuracy: {report.get('accuracy', 'N/A')}")
        print(f"   Test samples: {report.get('test_samples', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n   Make sure the following files exist in 'saved_models/':")
        print("   - best_model.keras")
        print("   - norm_params.npy")
        print("   - model_report.json")
    
    print("\n" + "=" * 60)
