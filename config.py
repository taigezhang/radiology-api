THRESHOLD = 5.0

WEIGHTS = {
    "same_modality": 2.0,
    "same_anatomy": 3.0,
    "keyword_overlap": 1.0,
    "strong_keyword_overlap": 2.0,
    "cross_modality_related": 1.0,
    "negative_conflict": -3.0,
}

MODALITIES = {
    "ct": ["ct", "computed tomography", "cat scan"],
    "mri": ["mri", "magnetic resonance"],
    "xr": ["xray", "x-ray", "radiograph", "xr"],
    "us": ["ultrasound", "sonogram", "us"],
    "pet": ["pet"],
    "nm": ["nuclear medicine", "nm"],
}

ANATOMY_GROUPS = {
    "head_brain": [
        "head", "brain", "skull", "intracranial", "cerebral",
        "stroke", "infarct", "hemorrhage", "ich"
    ],
    "chest_lung": [
        "chest", "lung", "pulmonary", "thorax", "pe", "embolism",
        "pneumonia", "pleural"
    ],
    "abdomen_pelvis": [
        "abdomen", "pelvis", "abdominal", "hepatic", "liver",
        "kidney", "renal", "bowel", "appendix", "pancreas"
    ],
    "spine": [
        "spine", "cervical", "thoracic", "lumbar", "vertebra",
        "disc", "cord"
    ],
    "extremity": [
        "arm", "hand", "wrist", "elbow", "shoulder", "leg",
        "knee", "ankle", "foot", "hip", "femur", "tibia"
    ],
    "cardiac": [
        "heart", "cardiac", "coronary", "aorta", "vascular"
    ],
}

IMPORTANT_KEYWORDS = {
    "stroke", "infarct", "hemorrhage", "mass", "tumor", "cancer",
    "metastasis", "fracture", "embolism", "aneurysm", "infection",
    "abscess", "pneumonia", "appendicitis", "obstruction"
}