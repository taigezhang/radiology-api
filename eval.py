import argparse
import json
from typing import Any, Dict, List

from model import score_pair
from schemas import Case, PriorStudy


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(data: Dict[str, Any], threshold: float) -> Dict[str, float]:
    total = 0
    correct = 0
    tp = fp = tn = fn = 0

    for raw_case in data.get("cases", []):
        case = Case(**raw_case)
        current = case.current_study or {}

        for prior in case.prior_studies:
            label = getattr(prior, "label", None)

            if label is None:
                raw_prior = prior.model_dump()
                label = raw_prior.get("is_relevant", raw_prior.get("label"))

            if label is None:
                continue

            pred = score_pair(current, prior) >= threshold
            gold = bool(label)

            total += 1
            correct += int(pred == gold)

            if pred and gold:
                tp += 1
            elif pred and not gold:
                fp += 1
            elif not pred and not gold:
                tn += 1
            elif not pred and gold:
                fn += 1

    accuracy = correct / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "threshold": threshold,
        "total": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to labeled validation JSON")
    parser.add_argument("--threshold", type=float, default=5.0)
    parser.add_argument("--search", action="store_true")
    args = parser.parse_args()

    data = load_json(args.data)

    if args.search:
        best = None
        for threshold in [x / 2 for x in range(2, 21)]:
            result = evaluate(data, threshold)
            if best is None or result["accuracy"] > best["accuracy"]:
                best = result
            print(result)
        print("\nBest:", best)
    else:
        print(evaluate(data, args.threshold))


if __name__ == "__main__":
    main()