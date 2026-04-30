from __future__ import annotations

import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional

from config import (
    BODY_TERMS,
    CLINICAL_TERMS,
    MODALITY_ALIASES,
    NEGATIVE_EXAM_TERMS,
    STOPWORDS,
    THRESHOLD,
    WEIGHTS,
)
from schemas import CurrentStudy, Study


def normalize(text: str) -> str:
    text = text.lower().replace("cntrst", "contrast")
    text = re.sub(r"[^a-z0-9+/-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=20000)
def parse_description(desc: str) -> Dict[str, Any]:
    s = normalize(desc)
    tokens = {t for t in s.split() if t and t not in STOPWORDS}

    modality = None
    for alias, canonical in sorted(MODALITY_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(alias)}\b", s):
            modality = canonical
            break

    bodies = {t for t in tokens if t in BODY_TERMS}
    clinical = {t for t in tokens if t in CLINICAL_TERMS}
    negative = {t for t in tokens if t in NEGATIVE_EXAM_TERMS}

    # Compound and synonym-style expansions used during error analysis.
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


def score_pair(current: CurrentStudy, prior: Study) -> float:
    cur = parse_description(current.study_description)
    prv = parse_description(prior.study_description)
    yrs = years_between(current.study_date, prior.study_date)

    score = 0.0

    if cur["raw"] == prv["raw"]:
        score += WEIGHTS["exact_description"]

    if cur["modality"] and prv["modality"]:
        if cur["modality"] == prv["modality"]:
            score += WEIGHTS["same_modality"]
        elif {cur["modality"], prv["modality"]} in [{"mri", "mra"}, {"ct", "cta"}]:
            score += WEIGHTS["related_modality"]
        else:
            score += WEIGHTS["different_modality"]

    body_overlap = cur["bodies"] & prv["bodies"]
    if body_overlap:
        score += WEIGHTS["body_overlap_base"]
        score += min(
            WEIGHTS["body_overlap_bonus_cap"],
            len(body_overlap) * WEIGHTS["body_overlap_bonus_each"],
        )
    else:
        score += WEIGHTS["no_body_overlap"]

    if cur["clinical"] & prv["clinical"]:
        score += WEIGHTS["clinical_overlap"]

    score += WEIGHTS["lexical_similarity_multiplier"] * text_similarity(cur["tokens"], prv["tokens"])

    if yrs is not None:
        if yrs <= 1:
            score += WEIGHTS["recency_le_1_year"]
        elif yrs <= 3:
            score += WEIGHTS["recency_le_3_years"]
        elif yrs > 8:
            score += WEIGHTS["old_prior_gt_8_years"]

    if prv["negative"] and not (body_overlap and cur["modality"] == prv["modality"]):
        score += WEIGHTS["negative_exam_penalty"]

    if (
        ("stroke" in cur["clinical"] or "stroke" in prv["clinical"])
        and ({"brain", "head"} & cur["bodies"])
        and ({"brain", "head"} & prv["bodies"])
    ):
        score += WEIGHTS["stroke_brain_bonus"]

    return score


def predict_pair(current: CurrentStudy, prior: Study, threshold: float = THRESHOLD) -> bool:
    return score_pair(current, prior) >= threshold
