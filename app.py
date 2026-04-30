from fastapi import FastAPI
from schemas import PredictRequest, PredictResponse
from model import predict_batch

app = FastAPI(title="Relevant Priors API")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "POST JSON to /predict"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    predictions = []

    for case in request.cases:
        predictions.extend(predict_batch(case))

    return PredictResponse(predictions=predictions)