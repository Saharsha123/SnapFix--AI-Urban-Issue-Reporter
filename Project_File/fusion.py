"""
fusion.py
Fusion logic for combining image and text classification outputs.

Priority:
- Text prediction is primary.
- Image is used for agreement boosting or fallback.
- Low confidence cases are flagged for manual review.
"""

import numpy as np

def fuse_predictions(image_probs, text_probs, class_names):
    img_label = img_conf = None
    txt_label = txt_conf = None

    if image_probs is not None:
        img_idx = int(np.argmax(image_probs))
        img_label = class_names[img_idx]
        img_conf = float(image_probs[img_idx])

    if text_probs is not None:
        txt_idx = int(np.argmax(text_probs))
        txt_label = class_names[txt_idx]
        txt_conf = float(text_probs[txt_idx])

    # --- BOTH PRESENT: text is primary ---
    if txt_label and img_label:
        # same class → boost confidence a bit
        if txt_label == img_label:
            base_conf = max(txt_conf, img_conf)
            final_conf = min(1.0, base_conf + 0.15)
            source = "image_text_agree"
        else:
            # disagree → keep text label, but damp confidence
            final_conf = max(0.0, txt_conf - 0.20)
            source = "text_primary_image_disagree"

        if final_conf < 0.50:
            return "needs_manual_review", final_conf, source
        return txt_label, final_conf, source

    # --- TEXT ONLY: still primary ---
    if txt_label:
        source = "text_only"
        if txt_conf < 0.50:
            return "needs_manual_review", txt_conf, source
        return txt_label, txt_conf, source

    # --- IMAGE ONLY: fallback ---
    if img_label:
        source = "image_only"
        if img_conf < 0.50:
            return "needs_manual_review", img_conf, source
        return img_label, img_conf, source

    return "unknown", 0.0, "no_input"
