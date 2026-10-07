# PhishGuard AI project report

## Introduction

Phishing remains an effective social-engineering attack because a URL can resemble a trusted service while leading to an attacker-controlled destination. PhishGuard AI studies whether structural URL features can provide an early warning.

## Methodology

Licensed labelled URL data is cleaned, deduplicated, stratified into training, validation, and test partitions, and transformed into a fixed vector of structural features. A scaled multilayer perceptron is trained with binary cross entropy. The saved model and scaler are loaded by the FastAPI service.

## System design

The React client authenticates with FastAPI. The API validates the URL, extracts string-only features, predicts with the Keras model, generates separately-labelled rule indicators, and persists the result in SQLite.

## Evaluation

`ml/train.py` writes actual test metrics to `backend/model/metrics.json` after training. No performance values are hardcoded in this report. Accuracy, precision, recall, F1, ROC-AUC, and confusion matrices should be interpreted against the selected dataset and split.

## Limitations and future work

URL-only signals do not establish website intent or reputation. Future work may add permitted threat-intelligence feeds, character-sequence models, browser and email integrations, and stronger explainability while preserving privacy and consent.
