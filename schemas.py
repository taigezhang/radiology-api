from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


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
