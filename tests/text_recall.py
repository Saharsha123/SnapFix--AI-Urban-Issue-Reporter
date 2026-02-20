import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix
import numpy as np

# Load data
df = pd.read_csv("../complaints_text_dataset.csv")

X = df["text"]
y_true = df["label"].astype(str)   # force string labels

# Load model and label mapping
vectorizer = joblib.load("../text_vectorizer.joblib")
model = joblib.load("../text_classifier.joblib")
label_to_idx = joblib.load("../label_to_idx.joblib")

# Create reverse mapping (idx to label)
idx_to_label = {v: k for k, v in label_to_idx.items()}

# Predict
X_vec = vectorizer.transform(X)
y_pred = model.predict(X_vec)

# Convert numeric predictions back to class names
y_pred = np.array([idx_to_label[idx] for idx in y_pred])

# Get labels safely
labels = sorted(y_true.unique())

# Confusion matrix
cm = confusion_matrix(y_true, y_pred, labels=labels)

print("\nPer-class Accuracy (Text Model):\n")

for i, label in enumerate(labels):
    support = cm[i].sum()
    if support == 0:
        print(f"{label:30s} : N/A")
    else:
        acc = cm[i, i] / support
        print(f"{label:30s} : {acc:.4f}")