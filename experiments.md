# Experiments

## Final submitted system

The final endpoint is a deterministic FastAPI service using a weighted heuristic relevance model. It achieved 100% prediction coverage, fast runtime, and a held-out evaluator accuracy of 0.8364.

The system returns one prediction for every prior study and does not call any external model or LLM. This was intentional because the evaluator can send large batches, and one external call per prior study would risk timeout.

## Model design

Each current/prior pair is converted into structured features:

- modality: CT, CTA, MRI, MRA, X-ray, ultrasound, nuclear medicine, etc.
- anatomy/body region: head, brain, chest, abdomen, pelvis, spine, knee, hip, etc.
- clinical keywords: stroke, trauma, fracture, mass, cancer, infection, hemorrhage, etc.
- text overlap after normalization
- time gap between current and prior examination

The final score is a weighted sum of those features. A prior is predicted relevant when its score is greater than or equal to the configured threshold.

## Experiment 1: simple keyword overlap baseline

The first baseline compared normalized word overlap between current and prior study descriptions.

What worked:
- Very fast.
- Good for nearly identical studies.

What failed:
- Missed synonyms such as brain/head or stroke/infarct-style wording.
- Produced false positives when descriptions shared generic terms such as "without contrast".

## Experiment 2: modality and anatomy matching

The second version added modality detection and anatomy vocabularies.

What improved:
- Same body region became the strongest signal.
- Same modality improved precision.
- Clearly unrelated regions, such as MRI brain vs XR ankle, were filtered out.

Main remaining issue:
- Cross-modality studies can still be clinically useful. For example, a prior CT head can be relevant to a current MRI brain stroke exam.

## Experiment 3: weighted heuristic with clinical and temporal features

The final version added weighted components for modality, anatomy, clinical keyword overlap, lexical similarity, recency, and special-case neuro/stroke logic.

Observed result from evaluator feedback:
- Held-out accuracy: 0.8364
- Prediction coverage: 100%
- Runtime: fast, deterministic, no external calls

This version was selected because it balanced reliability and accuracy without risking evaluator timeout.

## Error analysis

Likely false positives:
- Same modality and body region but different clinical question.
- Broad descriptions where the prior looks similar textually but is not useful for the current read.
- Old studies that match anatomy but may no longer be clinically meaningful.

Likely false negatives:
- Clinically useful cross-modality priors.
- Prior studies with different wording but same underlying condition.
- Studies with very short descriptions where important context is not visible in the text.

## Radiologist workflow considerations

The prediction system should support radiologists by showing priors that are likely to help comparison, diagnosis, or change detection. A false negative can be harmful when it hides a prior that would clarify disease progression, prior intervention, or chronic findings. However, too many false positives can slow the radiologist by cluttering the worklist.

For this challenge, the final threshold favors showing strongly related anatomy/modality matches while suppressing clearly unrelated exams. In a real clinical workflow, the acceptable threshold would depend on the reading context. For high-risk studies such as stroke, cancer follow-up, or trauma, higher recall may be preferred. For routine low-risk studies, higher precision may be more acceptable.

## Reproducibility improvements included

To make the project more reproducible and maintainable, the upgraded version separates the code into:

- `config.py`: thresholds, weights, and vocabularies
- `model.py`: scoring and prediction logic
- `schemas.py`: API schema definitions
- `eval.py`: offline evaluation, threshold search, and error inspection
- `tests/test_model.py`: representative unit tests

The offline evaluation script can reproduce accuracy, precision, recall, F1, threshold comparisons, and example false positives/false negatives when run on a labeled public evaluation JSON.

## Next improvements

1. Use public labeled data to tune the threshold with cross-validation instead of manually selected weights.
2. Add more medical synonyms and anatomy hierarchies.
3. Add embedding similarity as a second-stage model after rule-based filtering.
4. Track precision and recall separately for high-risk categories such as stroke, cancer, and trauma.
5. Add more unit tests for edge cases and ambiguous cross-modality pairs.
