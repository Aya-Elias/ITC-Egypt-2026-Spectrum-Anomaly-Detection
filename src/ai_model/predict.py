"""
predict.py
----------
تستخدم هذا الملف لتصنيف إشارة واحدة أو مجموعة إشارات باستخدام النموذج المدرب.
ملاحظة: النموذج تم تدريبه باستخدام Min-Max Normalization (x / 255.0)
"""

import numpy as np
import tensorflow as tf
import os

# ============================================
# تحميل النموذج ومعاملات التطبيع
# ============================================
def load_model_and_params(model_path, norm_path):
    """
    تحميل النموذج المدرب ومعاملات التطبيع (Min-Max)
    
    Args:
        model_path (str): مسار ملف النموذج (.keras)
        norm_path (str): مسار ملف norm_params.npy
    
    Returns:
        model: النموذج المحمّل
        min_val: الحد الأدنى للتطبيع (0.0)
        max_val: الحد الأقصى للتطبيع (255.0)
    """
    model = tf.keras.models.load_model(model_path)
    norm_data = np.load(norm_path, allow_pickle=True).item()
    
    # Min-Max normalization
    min_val = norm_data['min']
    max_val = norm_data['max']
    
    return model, min_val, max_val

# ============================================
# معالجة الصورة المفردة (Min-Max Normalization)
# ============================================
def preprocess_image(image, min_val, max_val):
    """
    معالجة صورة واحدة قبل تمريرها للنموذج
    التطبيع: (x - min) / (max - min)
    
    Args:
        image (np.ndarray): الصورة الخام (224, 224, 3) بقيم 0-255
        min_val (np.ndarray): الحد الأدنى لكل قناة
        max_val (np.ndarray): الحد الأقصى لكل قناة
    
    Returns:
        np.ndarray: الصورة بعد التطبيع (0-1)
    """
    image = image.astype(np.float32)
    image = (image - min_val) / (max_val - min_val + 1e-8)
    return np.expand_dims(image, axis=0)

# ============================================
# تصنيف صورة واحدة
# ============================================
def predict_single(model, image, min_val, max_val, class_names=None):
    """
    تصنيف إشارة واحدة
    
    Args:
        model: النموذج المحمّل
        image (np.ndarray): الصورة الخام (224, 224, 3) بقيم 0-255
        min_val, max_val: معاملات التطبيع
        class_names (list): أسماء الفئات (اختياري)
    
    Returns:
        dict: {
            'class_id': int,
            'class_name': str,
            'confidence': float,
            'probabilities': dict
        }
    """
    if class_names is None:
        class_names = ['Drone', 'Normal', 'Jamming']
    
    processed = preprocess_image(image, min_val, max_val)
    probs = model.predict(processed, verbose=0)[0]
    class_id = np.argmax(probs)
    
    return {
        'class_id': int(class_id),
        'class_name': class_names[class_id],
        'confidence': float(np.max(probs)),
        'probabilities': {
            class_names[i]: float(probs[i]) for i in range(len(class_names))
        }
    }

# ============================================
# تصنيف مجموعة صور
# ============================================
def predict_batch(model, images, min_val, max_val, class_names=None, batch_size=32):
    """
    تصنيف مجموعة إشارات
    
    Args:
        model: النموذج المحمّل
        images (list): قائمة بالصور (224,224,3) بقيم 0-255
        min_val, max_val: معاملات التطبيع
        class_names (list): أسماء الفئات
        batch_size (int): حجم الدفعة
    
    Returns:
        list: قائمة بنتائج التصنيف لكل صورة
    """
    if class_names is None:
        class_names = ['Drone', 'Normal', 'Jamming']
    
    # تطبيع كل الصور
    processed = []
    for img in images:
        img_norm = (img.astype(np.float32) - min_val) / (max_val - min_val + 1e-8)
        processed.append(img_norm)
    
    processed = np.array(processed)
    
    results = []
    for i in range(0, len(processed), batch_size):
        batch = processed[i:i+batch_size]
        probs_batch = model.predict(batch, verbose=0)
        
        for probs in probs_batch:
            class_id = np.argmax(probs)
            results.append({
                'class_id': int(class_id),
                'class_name': class_names[class_id],
                'confidence': float(np.max(probs)),
                'probabilities': {
                    class_names[j]: float(probs[j]) for j in range(len(class_names))
                }
            })
    
    return results

# ============================================
# مثال الاستخدام (للبيئة التفاعلية)
# ============================================
if __name__ == "__main__":
    # في Kaggle/Colab، استخدم المسار المطلق
    import sys
    import os
    
    # لو عايز تشغله في Notebook
    MODEL_PATH = "/kaggle/working/src/ai_model/saved_models/best_model.keras"
    NORM_PATH = "/kaggle/working/src/ai_model/saved_models/norm_params.npy"
    
    # لو الملفات مش موجودة، حاول تدور عليهم
    if not os.path.exists(MODEL_PATH):
        # جرب في نفس المجلد
        MODEL_PATH = "saved_models/best_model.keras"
        NORM_PATH = "saved_models/norm_params.npy"
    
    if os.path.exists(MODEL_PATH):
        model, min_val, max_val = load_model_and_params(MODEL_PATH, NORM_PATH)
        print("✅ Model loaded successfully!")
        print(f"   Min value: {min_val}")
        print(f"   Max value: {max_val}")
        print(f"   Input shape: {model.input_shape}")
        print(f"   Output classes: {model.output_shape[-1]}")
    else:
        print("❌ Model file not found. Please check the path.")
