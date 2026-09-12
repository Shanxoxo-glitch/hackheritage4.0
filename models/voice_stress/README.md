---
pipeline_tag: audio-classification
---

# HackHeritage26 Voice Stress V1

Prototype voice-stress perception model developed for the HackHeritage26 perception layer.

## Model

This model uses acoustic features extracted from speech with `librosa` and a LightGBM classifier.

The production inference bundle contains a NumPy-compatible dump of the trained LightGBM trees, allowing inference without importing LightGBM alongside PyTorch on macOS.

Labels:

- `NOT_STRESSED`
- `STRESSED`

Audio is resampled to 16 kHz during inference.

## Training Data

The model was trained and evaluated using the RAVDESS speech dataset.

The evaluation uses speaker-independent splits so that speakers in evaluation are separated from the corresponding training data.

RAVDESS contains acted emotional speech, so there is an important domain gap between this dataset and real-world victim speech.

## Evaluation

Speaker-independent cross-validation:

- Accuracy: approximately 75.2%
- AUC: approximately 0.82

Per-speaker baseline normalization experiments reached approximately 78.3% accuracy and 0.87 AUC.

These results should be interpreted as prototype research metrics, not as evidence of reliable real-world stress detection.

## Intended Use

This model is intended as one acoustic perception signal within the HackHeritage26 multimodal safety system.

It may be used for:

- voice-stress perception experiments
- multimodal safety research
- downstream human-in-the-loop decision support
- prototyping acoustic feature pipelines

## Limitations

This is **not a reliable detector of psychological stress in real victims**.

The model is trained on acted English speech from RAVDESS. Real speech varies substantially by speaker, language, microphone, environment, culture, emotional expression, and context.

A high stress score must not be interpreted as proof that a person is distressed, unsafe, or experiencing a particular psychological state.

The voice signal should be combined with other perception signals and human review.

## Files

- `voice_stress_ravdess.joblib`: primary inference bundle used by the HackHeritage26 perception API
- `metrics_ravdess.json`: evaluation metrics

The `.joblib` bundle contains the dumped model representation, feature names, labels, training source, and inference metadata required by the NumPy tree evaluator.

## Inference

The HackHeritage26 API:

1. Loads the audio.
2. Resamples it to 16 kHz.
3. Extracts acoustic features using `librosa`.
4. Evaluates the dumped LightGBM trees using the project's NumPy tree evaluator.
5. Returns a stress score between 0 and 1.

The `voice_stress_ravdess.lgbm.joblib` training artifact is intentionally not included in this repository because the API uses the NumPy-compatible inference bundle instead.

## Project

HackHeritage26, Perception Models & Data.
