from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PriorStudy(BaseModel):
    case_id: Optional[str] = None
    study_id: str
    description: Optional[str] = ""
    modality: Optional[str] = ""
    body_part: Optional[str] = ""
    report: Optional[str] = ""
    date: Optional[str] = None

    class Config:
        extra = "allow"


class Case(BaseModel):
    case_id: str
    current_study: Optional[Dict[str, Any]] = Field(default_factory=dict)
    prior_studies: List[PriorStudy] = Field(default_factory=list)

    class Config:
        extra = "allow"


class PredictRequest(BaseModel):
    cases: List[Case]


class PredictionItem(BaseModel):
    case_id: str
    study_id: str
    predicted_is_relevant: bool


class PredictResponse(BaseModel):
    predictions: List[PredictionItem]