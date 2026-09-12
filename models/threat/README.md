---
library_name: transformers
pipeline_tag: text-classification
base_model: google/muril-base-cased
---

# HackHeritage26 Threat V7

Threat and intimidation perception model developed for the HackHeritage26 perception layer.

## Model

This model fine-tunes Google's MuRIL (`google/muril-base-cased`) for binary threat/intimidation classification.

Labels:

- `NOT_THREAT`
- `THREAT`

The model is intended to provide a perception signal to the HackHeritage26 multimodal safety system. It is not a standalone decision-maker and should not be treated as a definitive assessment of whether a real-world threat exists.

## Evaluation

Held-out test set:

- Accuracy: 96.15%
- Precision: 100.00%
- Recall: 92.31%
- F1: 96.00%

Test set size: 78 examples.

Confusion matrix:

```text
                 Predicted
              NOT_THREAT  THREAT
Actual NOT       39         0
Actual THREAT     3        36

