import re
from typing import Dict, List, Set

from config import ANATOMY_GROUPS, IMPORTANT_KEYWORDS, MODALITIES, THRESHOLD, WEIGHTS
from schemas import Case, PredictionItem, PriorStudy


def normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).lower().replace("_", " ").replace("-", " ")


def tokenize(text: str) -> Set[str]:
    text = normalize_text(text)
    return set(re.findall(r"[a-z0-9]+", text))


def collect_study_text(study) -> str:
    if study is None:
        return ""

    if isinstance(study, dict):
        parts = []
        for key in ["description", "modality", "body_part", "report", "reason", "indication", "procedure"]:
            if key in study and study[key]:
                parts.append(str(study[key]))
        return " ".join(parts)

    parts = []
    for attr in ["description", "modality", "body_part", "report"]:
        value = getattr(study, attr, "")
        if value:
            parts.append(str(value))
    return " ".join(parts)


def detect_modality(text: str) -> str:
    text = normalize_text(text)
    for modality, terms in MODALITIES.items():
        for term in terms:
            if term in text:
                return modality
    return ""


def detect_anatomy(text: str) -> Set[str]:
    text = normalize_text(text)
    groups = set()

    for group, terms in ANATOMY_GROUPS.items():
        for term in terms:
            if term in text:
                groups.add(group)
                break

    return groups


def keyword_overlap_score(current_tokens: Set[str], prior_tokens: Set[str]) -> float:
    overlap = current_tokens.intersection(prior_tokens)

    if not overlap:
        return 0.0

    score = 0.0
    score += min(len(overlap), 4) * WEIGHTS["keyword_overlap"]

    important_overlap = overlap.intersection(IMPORTANT_KEYWORDS)
    if important_overlap:
        score += WEIGHTS["strong_keyword_overlap"]

    return score


def has_negative_conflict(current_anatomy: Set[str], prior_anatomy: Set[str]) -> bool:
    if not current_anatomy or not prior_anatomy:
        return False

    return current_anatomy.isdisjoint(prior_anatomy)


def score_pair(current_study: Dict, prior: PriorStudy) -> float:
    current_text = collect_study_text(current_study)
    prior_text = collect_study_text(prior)

    current_tokens = tokenize(current_text)
    prior_tokens = tokenize(prior_text)

    current_modality = detect_modality(current_text)
    prior_modality = detect_modality(prior_text)

    current_anatomy = detect_anatomy(current_text)
    prior_anatomy = detect_anatomy(prior_text)

    score = 0.0

    if current_modality and prior_modality and current_modality == prior_modality:
        score += WEIGHTS["same_modality"]

    if current_modality and prior_modality and current_modality != prior_modality:
        if current_anatomy and prior_anatomy and not current_anatomy.isdisjoint(prior_anatomy):
            score += WEIGHTS["cross_modality_related"]

    if current_anatomy and prior_anatomy and not current_anatomy.isdisjoint(prior_anatomy):
        score += WEIGHTS["same_anatomy"]

    score += keyword_overlap_score(current_tokens, prior_tokens)

    if has_negative_conflict(current_anatomy, prior_anatomy):
        score += WEIGHTS["negative_conflict"]

    return score


def predict_is_relevant(current_study: Dict, prior: PriorStudy) -> bool:
    return score_pair(current_study, prior) >= THRESHOLD


def predict_batch(case: Case) -> List[PredictionItem]:
    predictions = []

    current_study = case.current_study or {}

    for prior in case.prior_studies:
        predictions.append(
            PredictionItem(
                case_id=case.case_id,
                study_id=prior.study_id,
                predicted_is_relevant=predict_is_relevant(current_study, prior),
            )
        )

    return predictions