"""Configuration for the deterministic relevant-prior scoring model.

The challenge data did not include a public training split with stable labels in this
repository, so these weights are manually selected from local error analysis and
made explicit here to avoid hiding tuned constants inside endpoint code.
"""

THRESHOLD = 3.0

WEIGHTS = {
    "exact_description": 5.0,
    "same_modality": 2.0,
    "related_modality": 1.0,
    "different_modality": -1.5,
    "body_overlap_base": 3.0,
    "body_overlap_bonus_cap": 1.0,
    "body_overlap_bonus_each": 0.25,
    "no_body_overlap": -2.0,
    "clinical_overlap": 1.0,
    "lexical_similarity_multiplier": 2.0,
    "recency_le_1_year": 1.0,
    "recency_le_3_years": 0.5,
    "old_prior_gt_8_years": -0.75,
    "negative_exam_penalty": -0.75,
    "stroke_brain_bonus": 1.25,
}

STOPWORDS = {
    "and", "or", "the", "of", "for", "with", "without", "w", "wo", "contrast",
    "cntrst", "limited", "complete", "exam", "study", "views", "view", "routine",
}

MODALITY_ALIASES = {
    "computed tomography": "ct",
    "ct": "ct",
    "cta": "cta",
    "mri": "mri",
    "mr": "mri",
    "mra": "mra",
    "x-ray": "xray",
    "xray": "xray",
    "xr": "xray",
    "radiograph": "xray",
    "us": "ultrasound",
    "ultrasound": "ultrasound",
    "pet": "pet",
    "nm": "nuclear",
    "nuclear": "nuclear",
    "fluoro": "fluoro",
    "mammogram": "mammogram",
    "mammo": "mammogram",
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

NEGATIVE_EXAM_TERMS = {"screening", "portable", "single", "preop", "pre-op"}
