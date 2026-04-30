from fastapi import FastAPI
from schemas import PredictRequest, PredictResponse, PredictionItem
from model import predict_batch

app = FastAPI()


@app.get("/")
def health_check():
    return {"status": "ok", "message": "POST JSON to /predict"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Main prediction endpoint.
    Expects:
    {
        "cases": [...]
    }

    Returns:
    {
        "predictions": [...]
    }
    """
    predictions = []

    for case in request.cases:
        case_predictions = predict_batch(case)
        predictions.extend(case_predictions)

    return PredictResponse(predictions=predictions)
