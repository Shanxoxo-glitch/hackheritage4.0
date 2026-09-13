"""
OpenCV FER+ Live Camera Emotion Perception & Session Averaging Service.
Uses the Microsoft FER+ ONNX deep convolutional network (AffectNet / FER2013+)
to compute softmax emotion distributions across 8 facial expressions:
  NEUTRAL, HAPPINESS, SURPRISE, SADNESS, ANGER, DISGUST, FEAR, CONTEMPT

Provides session averaging across video frames captured during live camera check-ins.
"""
import os
import cv2
import base64
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

EMOTIONS = ['NEUTRAL', 'HAPPINESS', 'SURPRISE', 'SADNESS', 'ANGER', 'DISGUST', 'FEAR', 'CONTEMPT']

# Find model path
_CANDIDATE_PATHS = [
    Path("e:/hh4/opencv/emotion_ferplus.onnx"),
    Path(__file__).resolve().parents[4] / "opencv" / "emotion_ferplus.onnx",
    Path("models/emotion_ferplus.onnx"),
]

MODEL_PATH = next((p for p in _CANDIDATE_PATHS if p.exists()), _CANDIDATE_PATHS[0])

# Global singleton net
_net = None
_face_cascade = None


def get_net():
    global _net
    if _net is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"OpenCV FER+ model not found at {MODEL_PATH}")
        _net = cv2.dnn.readNetFromONNX(str(MODEL_PATH))
    return _net


def get_face_cascade():
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _face_cascade = cv2.CascadeClassifier(cascade_path)
    return _face_cascade


def softmax(x: np.ndarray) -> np.ndarray:
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


def get_cascades():
    """Returns primary and fallback Haar cascades for robust facial landmark detection."""
    cascades = []
    names = [
        "haarcascade_frontalface_default.xml",
        "haarcascade_frontalface_alt2.xml",
        "haarcascade_frontalface_alt.xml",
    ]
    for n in names:
        path = cv2.data.haarcascades + n
        c = cv2.CascadeClassifier(path)
        if not c.empty():
            cascades.append(c)
    return cascades


def analyze_image_array(img: np.ndarray) -> Dict[str, Any]:
    """
    Processes an image frame (BGR format from OpenCV / base64 decode).
    Detects faces using multi-cascade detection with tight face framing,
    and runs FER+ ONNX forward pass.
    """
    if img is None or img.size == 0:
        raise ValueError("Invalid or empty image array")

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Try multi-cascade detection across equalized and raw grayscale
    faces = []
    for cascade in get_cascades():
        # Try raw
        detected = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(40, 40))
        if len(detected) > 0:
            faces = detected
            break
        # Try equalized
        eq = cv2.equalizeHist(gray)
        detected = cascade.detectMultiScale(eq, scaleFactor=1.1, minNeighbors=3, minSize=(40, 40))
        if len(detected) > 0:
            faces = detected
            break

    if len(faces) > 0:
        # Sort by face area (largest face first)
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, fw, fh = faces[0]
        # Pad slightly to capture full brow-to-chin context
        pad_x = int(fw * 0.1)
        pad_y = int(fh * 0.1)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(w, x + fw + pad_x)
        y2 = min(h, y + fh + pad_y)
        face_crop = gray[y1:y2, x1:x2]
        face_detected = True
    else:
        # Standard webcam selfie framing: user's face is centered horizontally in upper-middle
        # Center ~48% vertically, ~50% horizontally, bounding ~58% of video height
        face_sz = int(h * 0.58)
        cy_face = int(h * 0.48)
        cx_face = int(w * 0.50)
        y1 = max(0, cy_face - face_sz // 2)
        y2 = min(h, cy_face + face_sz // 2)
        x1 = max(0, cx_face - face_sz // 2)
        x2 = min(w, cx_face + face_sz // 2)
        face_crop = gray[y1:y2, x1:x2]
        face_detected = False

    resized = cv2.resize(face_crop, (64, 64)).astype(np.float32)
    blob = cv2.dnn.blobFromImage(resized, 1.0, (64, 64), (0, 0, 0), swapRB=False, crop=False)

    net = get_net()
    net.setInput(blob)
    logits = net.forward()[0]
    probs = softmax(logits)

    prob_dict = {EMOTIONS[i]: float(probs[i]) for i in range(len(EMOTIONS))}

    top_idx = int(np.argmax(probs))
    primary_emotion = EMOTIONS[top_idx]
    confidence = float(probs[top_idx])

    # Calibrated mathematical distress formula:
    # FER+ deep CNN emotion weights
    distress_score = (
        prob_dict['FEAR'] * 1.00 +
        prob_dict['SADNESS'] * 0.92 +
        prob_dict['ANGER'] * 0.88 +
        prob_dict['DISGUST'] * 0.82 +
        prob_dict['CONTEMPT'] * 0.55 +
        prob_dict['SURPRISE'] * 0.25
    )

    # When primary emotion is one of the distress emotions, ensure distress reflects that elevation
    distress_emotions = {'SADNESS', 'FEAR', 'ANGER', 'DISGUST', 'CONTEMPT'}
    if primary_emotion in distress_emotions:
        primary_prob = prob_dict[primary_emotion]
        distress_score = max(distress_score, primary_prob * 0.85, 0.62)
    elif primary_emotion == 'NEUTRAL' and prob_dict['SADNESS'] > 0.15:
        # Subtle grief / fatigue with masked neutral facade
        distress_score = max(distress_score, 0.45 + prob_dict['SADNESS'] * 0.8)

    distress_score = float(np.clip(distress_score, 0.08, 0.98))

    return {
        "primary_emotion": primary_emotion,
        "distress_score": round(distress_score, 3),
        "confidence": round(confidence, 3),
        "emotions": {k: round(v, 4) for k, v in prob_dict.items()},
        "face_detected": face_detected
    }


def analyze_base64_frame(b64_str: str) -> Dict[str, Any]:
    """Decodes a base64 data-URL or raw base64 frame and analyzes facial emotion."""
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    raw_bytes = base64.b64decode(b64_str)
    nparr = np.frombuffer(raw_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return analyze_image_array(img)


def compute_session_average(frame_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes mathematical arithmetic mean of distress scores and emotion probabilities
    across all frame snapshots recorded during the camera check-in session.
    """
    if not frame_results:
        return {
            "average_distress_score": 0.35,
            "primary_emotion": "NEUTRAL",
            "average_emotions": {emo: 0.125 for emo in EMOTIONS},
            "frames_analyzed": 0,
            "modality": "camera used"
        }

    total_distress = sum(f["distress_score"] for f in frame_results)
    avg_distress = round(total_distress / len(frame_results), 3)

    avg_emotions = {}
    for emo in EMOTIONS:
        total_p = sum(f["emotions"].get(emo, 0.0) for f in frame_results)
        avg_emotions[emo] = round(total_p / len(frame_results), 4)

    # Determine primary averaged emotion
    primary_emotion = max(avg_emotions.items(), key=lambda item: item[1])[0]

    return {
        "average_distress_score": avg_distress,
        "primary_emotion": primary_emotion,
        "average_emotions": avg_emotions,
        "frames_analyzed": len(frame_results),
        "modality": "camera used",
        "engine": "OpenCV FER+ ONNX"
    }
