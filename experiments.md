"""Offline evaluation and threshold search.

Expected labeled input format:
- Same top-level request JSON used by the API, with cases/current_study/prior_studies.
- Each prior study should include one label field, either:
  - is_relevant
  - relevant
  - label
  - predicted_is_relevant

Usage:
    python eval.py --data public_eval.json
    python eval.py --data public_eval.json --threshold-search
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

from model import predict_pair, score_pair
from schemas import Case, CurrentStudy, Study

LABEL_KEYS = ("is_relevant", "relevant", "label", "predicted_is_relevant")


@dataclass
class EvalRow:
    case_id: str
    study_id: str
    score: float
    prediction: bool
    label: bool
    current_description: str
    prior_description: str


def read_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_label(prior: dict[str, Any]) -> Optional[bool]:
    for key in LABEL_KEYS:
        if key in prior:
            value = prior[key]
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                return value.lower().strip() in {"true", "1", "yes", "relevant"}
    return None


def iter_cases(raw: dict[str, Any]) -> Iterable[dict[str, Any]]:
    if "cases" in raw:
        yield from raw["cases"]
    elif isinstance(raw, list):
        yield from raw
    else:
        raise ValueError("Input JSON must be a list of cases or contain a top-level 'cases' key.")


def evaluate(raw: dict[str, Any], threshold: float) -> List[EvalRow]:
    rows: List[EvalRow] = []
    for case_dict in iter_cases(raw):
        current = CurrentStudy(**case_dict["current_study"])
        case_id = case_dict["case_id"]
        for prior_dict in case_dict.get("prior_studies", []):
            label = extract_label(prior_dict)
            if label is None:
                continue
            prior = Study(
                study_id=str(prior_dict["study_id"]),
                study_description=prior_dict["study_description"],
                study_date=prior_dict["study_date"],
            )
            score = score_pair(current, prior)
            pred = predict_pair(current, prior, threshold=threshold)
            rows.append(
                EvalRow(
                    case_id=case_id,
                    study_id=prior.study_id,
                    score=score,
                    prediction=pred,
                    label=label,
                    current_description=current.study_description,
                    prior_description=prior.study_description,
                )
            )
    return rows


def metrics(rows: List[EvalRow]) -> dict[str, float]:
    total = len(rows)
    if total == 0:
        return {"total": 0, "accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
    correct = sum(r.prediction == r.label for r in rows)
    tp = sum(r.prediction and r.label for r in rows)
    fp = sum(r.prediction and not r.label for r in rows)
    fn = sum((not r.prediction) and r.label for r in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "total": total,
        "accuracy": correct / total,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to labeled public eval JSON")
    parser.add_argument("--threshold", type=float, default=3.0)
    parser.add_argument("--threshold-search", action="store_true")
    parser.add_argument("--show-errors", type=int, default=5)
    args = parser.parse_args()

    raw = read_json(args.data)
    thresholds = [args.threshold]
    if args.threshold_search:
        thresholds = [round(x / 10, 1) for x in range(10, 61)]

    best = None
    best_rows = None
    for threshold in thresholds:
        rows = evaluate(raw, threshold)
        m = metrics(rows)
        print(
            f"threshold={threshold:.1f} total={m['total']} "
            f"accuracy={m['accuracy']:.4f} precision={m['precision']:.4f} "
            f"recall={m['recall']:.4f} f1={m['f1']:.4f}"
        )
        if best is None or m["accuracy"] > best[1]["accuracy"]:
            best = (threshold, m)
            best_rows = rows

    if best and best_rows is not None:
        threshold, m = best
        print("\nBest threshold by accuracy:", threshold, m)
        errors = [r for r in best_rows if r.prediction != r.label]
        if args.show_errors and errors:
            print(f"\nFirst {min(args.show_errors, len(errors))} errors:")
            for r in errors[: args.show_errors]:
                kind = "FP" if r.prediction else "FN"
                print(f"[{kind}] case={r.case_id} prior={r.study_id} score={r.score:.2f}")
                print(f"  current: {r.current_description}")
                print(f"  prior:   {r.prior_description}")


if __name__ == "__main__":
    main()
