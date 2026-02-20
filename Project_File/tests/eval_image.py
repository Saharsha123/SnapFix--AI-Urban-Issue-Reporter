import tensorflow as tf
import numpy as np
from sklearn.metrics import classification_report, accuracy_score

# ===== PATHS =====
MODEL_PATH = "../model_output/image_model_mobilenet.keras"
TEST_DIR = "../data/images/test"   # IMPORTANT: exact path

# ===== LOAD MODEL =====
model = tf.keras.models.load_model(MODEL_PATH)
print("✅ MobileNetV2 model loaded")

# ===== LOAD TEST DATA =====
test_ds = tf.keras.utils.image_dataset_from_directory(
    TEST_DIR,
    image_size=(224, 224),
    batch_size=32,
    shuffle=False
)

class_names = test_ds.class_names
print("Classes:", class_names)

# ===== GET PREDICTIONS =====
y_true = np.concatenate([y.numpy() for _, y in test_ds])
y_pred_probs = model.predict(test_ds)
y_pred = np.argmax(y_pred_probs, axis=1)

# ===== METRICS =====
accuracy = accuracy_score(y_true, y_pred)
print(f"\nOverall Accuracy: {accuracy:.4f}\n")

print("Classification Report:\n")
print(classification_report(
    y_true,
    y_pred,
    target_names=class_names,
    digits=4
))