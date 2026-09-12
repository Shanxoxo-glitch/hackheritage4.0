---
library_name: transformers
pipeline_tag: text-classification
base_model: google/muril-base-cased
---

# HackHeritage26 Distress V3

Prototype text-based distress perception model developed for the HackHeritage26 perception layer.

## Model

This model fine-tunes Google's MuRIL (`google/muril-base-cased`) for three-level text distress classification.

Labels:

- `LOW`
- `MODERATE`
- `HIGH`

These labels are perception categories for the HackHeritage26 prototype. They are **not clinical diagnoses or medical severity ratings**.

## Evaluation

Held-out test set:

- Test examples: 54
- Accuracy: 90.74%
- Macro Precision: 91.06%
- Macro Recall: 90.74%
- Macro F1: 90.72%

Per-class results:

| Class | Precision | Recall | F1 |
|---|---:|---:|---:|
| LOW | 85.00% | 94.44% | 89.47% |
| MODERATE | 93.75% | 83.33% | 88.24% |
| HIGH | 94.44% | 94.44% | 94.44% |

Confusion matrix:

```text
                 Predicted
              LOW  MODERATE  HIGH
Actual LOW     17     ---
library_name: transformers
pipeline_tag:Aclialpipeline_tag: text-classi7
base
## Calibration

A temperature-scaling calibration artifact is included as `calibration.json`.

Calibration was fitted on the validation split and evaluated on the held-out test split.

Test ECE improved from approximately 0.451 before calibration to approximately 0.084 after calibration, while test accuracy remained 90.74%.

Because the calibration set is relatively small, calibrated confidence should be treated as a prototype confidence estimate rather than a real-world probability guarantee.

## Intended Use

This model is designed for:

- text-based distress perception
- safety-oriented multimodal systems
- English and Indian-language/code-mixed text experiments
- downstream human-in-the-loop decision support

The model should be interpreted together with other available signals and case context.

## Limitations

The training corpus is a prototype dataset created for HackHeritage26. It is not a representative sample of real-world distress across populations, languages, cultures, or circumstances.

The model should not be used to make medical diagnoses, determine clinical severity, or make high-stakes decisions without appropriate human review.

Distress perception is inherently contextual. A model score should therefore be treated as one signal rather than a definitive statement about a person's mental or emotional state.

## Files

- `model.safetensors`: trained model weights
- `config.json`: Transformers model configuration
- `tokenizer.json`: tokenizer
- `tokenizer_config.json`: tokenizer configuration
- `calibration.json`: temperature-scaling calibration artifact
- `metrics.json`: evaluation metrics

## Base Model

`google/muril-base-cased`
