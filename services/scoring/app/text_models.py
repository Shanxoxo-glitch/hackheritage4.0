"""Inference wrapper around a fine-tuned MuRIL sequence classifier (+ optional temperature calibration)."""
import json
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

_DTYPES = {"float32": torch.float32, "bfloat16": torch.bfloat16, "float16": torch.float16}


def softmax(logits, axis=-1):
    z = logits - logits.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def pick_device():
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class TextClassifier:
    def __init__(self, model_dir, label_names, name=None, device="cpu", dtype="float32", max_length=128):
        self.model_dir = Path(model_dir)
        if not self.model_dir.exists():
            raise FileNotFoundError(f"model dir not found: {self.model_dir}")
        self.label_names = list(label_names)
        self.name = name or self.model_dir.name
        self.max_length = max_length
        self.device = device or pick_device()
        self.dtype = dtype

        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
        kwargs = {}
        if dtype != "float32":
            kwargs = {"dtype": _DTYPES[dtype]}
        try:
            self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_dir), **kwargs)
        except TypeError:  # transformers < 5 used torch_dtype
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_dir), torch_dtype=_DTYPES[dtype])
        self.model.to(self.device).eval()

        n_out = int(self.model.config.num_labels)
        if n_out != len(self.label_names):
            raise ValueError(f"{self.name}: model has {n_out} outputs, expected {len(self.label_names)}")

        self.temperature, self.calibrated, self.calibration = 1.0, False, None
        cal_path = self.model_dir / "calibration.json"
        if cal_path.exists():
            self.calibration = json.loads(cal_path.read_text())
            self.temperature = float(self.calibration["temperature"])
            self.calibrated = True

    @torch.no_grad()
    def logits(self, texts, batch_size=32):
        texts = [str(t) for t in texts]
        out = []
        for i in range(0, len(texts), batch_size):
            enc = self.tokenizer(texts[i:i + batch_size], padding=True, truncation=True,
                                 max_length=self.max_length, return_tensors="pt").to(self.device)
            out.append(self.model(**enc).logits.float().cpu().numpy())
        if not out:
            return np.zeros((0, len(self.label_names)), dtype=np.float32)
        return np.concatenate(out)

    def predict(self, texts, batch_size=32):
        lg = self.logits(texts, batch_size)
        raw, cal = softmax(lg), softmax(lg / self.temperature)
        k = len(self.label_names)
        results = []
        for r, c in zip(raw, cal):
            idx = int(np.argmax(c))
            results.append({
                "label": self.label_names[idx], "label_id": idx,
                "probs": {n: float(p) for n, p in zip(self.label_names, c)},
                "raw_probs": {n: float(p) for n, p in zip(self.label_names, r)},
                "confidence": float(c[idx]),
                "entropy": float(-(c * np.log(c + 1e-12)).sum() / np.log(k)),
                "calibrated": self.calibrated, "temperature": float(self.temperature), "model": self.name,
            })
        return results

    def info(self):
        return {"name": self.name, "path": str(self.model_dir), "labels": self.label_names,
                "device": self.device, "dtype": self.dtype, "calibrated": self.calibrated,
                "temperature": float(self.temperature), "base_model": "google/muril-base-cased"}
