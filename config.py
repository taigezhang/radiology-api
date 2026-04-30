from __future__ import annotations

import hashlib
from typing import Dict, List

from fastapi import FastAPI, Request

from model import predict_pair
from schemas import PredictRequest, Prediction, PredictResponse

app = FastAPI(title="Relevant Priors API", version="2.0.0")


@app.get("/")
def health() -> Dict[str, str]:
    return {"status": "ok", "message": "POST JSON to /predict"}


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest, request: Request) -> PredictResponse:
    predictions: List[Prediction] = []
    total_priors = 0

    for case in payload.cases:
        total_priors += len(case.prior_studies)
        for prior in case.prior_studies:
            predictions.append(
                Prediction(
                    case_id=case.case_id,
                    study_id=prior.study_id,
                    predicted_is_relevant=predict_pair(case.current_study, prior),
                )
            )

    req_id = hashlib.md5(str(payload.model_dump()).encode()).hexdigest()[:8]
    print(
        f"request_id={req_id} cases={len(payload.cases)} "
        f"priors={total_priors} predictions={len(predictions)}"
    )
    return PredictResponse(predictions=predictions)
