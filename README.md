# Relevant Priors API

FastAPI endpoint that predicts whether prior radiology examinations should be shown while a radiologist reads the current examination.

## Endpoint

```bash
POST /predict
```

Response format:

```json
{
  "predictions": [
    {
      "case_id": "1001016",
      "study_id": "2453245",
      "predicted_is_relevant": true
    }
  ]
}
```

## Local run

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

## Render deployment

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

The repository includes `.python-version` and `runtime.txt` to pin Python 3.11.9.

## Project structure

```text
app.py              FastAPI app and API route
schemas.py          Pydantic request/response models
model.py            scoring and prediction logic
config.py           weights, threshold, vocabularies
eval.py             offline evaluation + threshold search
tests/test_model.py unit tests for representative exam-pair behavior
experiments.md      experiment log and improvement plan
```

## Offline evaluation

For a labeled public eval JSON where each prior study contains `is_relevant`, `relevant`, `label`, or `predicted_is_relevant`:

```bash
python eval.py --data public_eval.json
python eval.py --data public_eval.json --threshold-search --show-errors 10
```

The script reports accuracy, precision, recall, F1, and example false positives/false negatives.
