# Relevant Priors API

This project exposes a FastAPI `/predict` endpoint for the relevant-priors challenge.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Test:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

## Deploy

Recommended quick deployment: Render, Railway, Fly.io, or any VM.

Start command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Endpoint to submit:

```text
https://YOUR-DOMAIN/predict
```

## Method

The model is a deterministic rule-based classifier. It parses the current and prior study descriptions into modality, body region, clinical terms, and lexical tokens. It predicts a prior as relevant when the prior shares strong body-region/modality similarity with the current examination, with additional boosts for exact exam matches, clinical terms, and recency.

## Experiments

Baseline: mark only exact study-description matches as relevant. This is high precision but misses many useful priors such as CT head for MRI brain stroke.

Improved version: add body-region, modality, clinical-keyword, and recency scoring. This handles cases where the wording differs but the prior is clinically useful.

What worked: same body region plus same/related modality was the strongest signal. A special stroke/head rule improved cases where CT head and MRI brain stroke are not exact string matches but are still useful priors.

What failed: overly strict modality matching missed related exams. Overly broad lexical matching caused unrelated same-word exams to be marked relevant, so the final rule requires body-region agreement.

Next improvements: train a small text classifier on the public split, add more medical synonym mappings, calibrate thresholds by exam family, and use batch LLM labeling only offline to generate weak labels rather than calling an LLM during evaluation.
