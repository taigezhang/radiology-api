from __future__ import annotations

import re
import hashlib
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

app = FastAPI(title="Relevant Priors API", version="1.0.0")

# -----------------------------
# Request / response schemas
# -----------------------------
class Study(BaseModel):
    study_id: str
    study_description: str
    study_date: str

class CurrentStudy(BaseModel):
    study_id: str
    study_description: str
    study_date: str

class Case(BaseModel):
    case_id: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    current_study: CurrentStudy
    prior_studies: List[Study] = Field(default_factory=list)

class PredictRequest(BaseModel):
    challenge_id: Optional[str] = None
    schema_version: Optional[int] = None
    generated_at: Optional[str] = None
    cases: List[Case]

class Prediction(BaseModel):
    case_id: str
    study_id: str
    predicted_is_relevant: bool

class PredictResponse(BaseModel):
    predictions: List[Prediction]

# -----------------------------
# Rule-based relevance model
# Fast, deterministic, no external calls.
# -----------------------------
STOPWORDS = {
    "and", "or", "the", "of", "for", "with", "without", "w", "wo", "contrast",
    "cntrst", "limited", "complete", "exam", "study", "views", "view", "routine",
}

MODALITY_ALIASES = {
    "ct": "ct", "computed tomography": "ct", "cta": "cta",
    "mri": "mri", "mr": "mri", "mra": "mra",
    "xr": "xray", "xray": "xray", "x-ray": "xray", "radiograph": "xray",
    "us": "ultrasound", "ultrasound": "ultrasound",
    "pet": "pet", "nm": "nuclear", "nuclear": "nuclear",
    "fluoro": "fluoro", "mammogram": "mammogram", "mammo": "mammogram",
}

BODY_TERMS = {
    "brain", "head", "neck", "cervical", "thoracic", "lumbar", "spine", "chest",
    "abdomen", "pelvis", "knee", "hip", "shoulder", "ankle", "foot", "hand", "wrist",
    "elbow", "femur", "tibia", "fibula", "humerus", "forearm", "sinus", "face",
    "cardiac", "heart", "coronary", "renal", "kidney", "liver", "biliary", "breast",
    "prostate", "thyroid", "vascular", "aorta", "carotid", "lung", "mandible",
}

CLINICAL_TERMS = {
    "stroke", "trauma", "fracture", "mass", "tumor", "cancer", "metastasis", "pain",
    "infection", "abscess", "hemorrhage", "bleed", "aneurysm", "embolism", "pe",
    "pneumonia", "nodule", "seizure", "headache", "dizziness", "weakness",
}

NEGATIVE_EXAM_TERMS = {
    "screening", "portable", "single", "preop", "pre-op"
}

def normalize(text: str) -> str:
    text = text.lower().replace("cntrst", "contrast")
    text = re.sub(r"[^a-z0-9+/-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

@lru_cache(maxsize=20000)
def parse_description(desc: str) -> Dict[str, Any]:
    s = normalize(desc)
    tokens = set(t for t in s.split() if t and t not in STOPWORDS)

    modality = None
    # Check longer aliases first.
    for alias, canonical in sorted(MODALITY_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(alias)}\b", s):
            modality = canonical
            break

    bodies = {t for t in tokens if t in BODY_TERMS}
    clinical = {t for t in tokens if t in CLINICAL_TERMS}
    negative = {t for t in tokens if t in NEGATIVE_EXAM_TERMS}

    # Useful compound mappings.
    if "head" in tokens and modality == "ct":
        bodies.add("brain")
    if "brain" in tokens:
        bodies.add("head")
    if "c" in tokens and "spine" in tokens:
        bodies.add("cervical")
    if "l" in tokens and "spine" in tokens:
        bodies.add("lumbar")
    if "t" in tokens and "spine" in tokens:
        bodies.add("thoracic")

    return {
        "raw": s,
        "tokens": tokens,
        "modality": modality,
        "bodies": bodies,
        "clinical": clinical,
        "negative": negative,
    }

def years_between(current_date: str, prior_date: str) -> Optional[float]:
    try:
        c = datetime.fromisoformat(current_date[:10])
        p = datetime.fromisoformat(prior_date[:10])
        return abs((c - p).days) / 365.25
    except Exception:
        return None

def text_similarity(a_tokens: set[str], b_tokens: set[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / max(1, len(a_tokens | b_tokens))

def predict_pair(current: CurrentStudy, prior: Study) -> bool:
    cur = parse_description(current.study_description)
    prv = parse_description(prior.study_description)
    yrs = years_between(current.study_date, prior.study_date)

    score = 0.0

    # Same exact normalized description is strongly relevant.
    if cur["raw"] == prv["raw"]:
        score += 5.0

    # Modality matching matters, but related angiography MRI/CT studies can still be useful.
    if cur["modality"] and prv["modality"]:
        if cur["modality"] == prv["modality"]:
            score += 2.0
        elif {cur["modality"], prv["modality"]} in [{"mri", "mra"}, {"ct", "cta"}]:
            score += 1.0
        else:
            score -= 1.5

    # Same body region is the strongest signal.
    body_overlap = cur["bodies"] & prv["bodies"]
    if body_overlap:
        score += 3.0 + min(1.0, len(body_overlap) * 0.25)
    else:
        score -= 2.0

    # Similar clinical indication keywords help.
    if cur["clinical"] & prv["clinical"]:
        score += 1.0

    # General lexical overlap catches exact phrases not in dictionaries.
    score += 2.0 * text_similarity(cur["tokens"], prv["tokens"])

    # Recency: priors are usually more useful when recent, but same exam remains useful even old.
    if yrs is not None:
        if yrs <= 1:
            score += 1.0
        elif yrs <= 3:
            score += 0.5
        elif yrs > 8:
            score -= 0.75

    # Screening/portable/single-view exams are often less useful unless same body+modality.
    if prv["negative"] and not (body_overlap and cur["modality"] == prv["modality"]):
        score -= 0.75

    # Special rule: stroke brain MRI/CT head priors are often relevant to current stroke/head imaging.
    if ("stroke" in cur["clinical"] or "stroke" in prv["clinical"]) and ({"brain", "head"} & cur["bodies"]) and ({"brain", "head"} & prv["bodies"]):
        score += 1.25

    return score >= 3.0

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

    # Simple useful log for evaluator debugging.
    req_id = hashlib.md5(str(payload.model_dump()).encode()).hexdigest()[:8]
    print(f"request_id={req_id} cases={len(payload.cases)} priors={total_priors} predictions={len(predictions)}")
    return PredictResponse(predictions=predictions)
