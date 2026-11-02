"""Deterministic recruitment-screening fairness experiment."""
from __future__ import annotations

import numpy as np
import pandas as pd

SEED = 20261102
N_APPLICANTS = 6000
CAPACITY_RATE = 0.35


def select_top_k(scores: np.ndarray, k: int) -> np.ndarray:
    """Select exactly k largest values with deterministic stable tie breaking."""
    values = np.asarray(scores, dtype=float)
    if k < 0 or k > len(values):
        raise ValueError("k outside valid range")
    output = np.zeros(len(values), dtype=int)
    if k:
        order = np.argsort(-values, kind="stable")
        output[order[:k]] = 1
    return output


def generate_synthetic_applicants(n: int = N_APPLICANTS, seed: int = SEED,
                                  capacity_rate: float = CAPACITY_RATE) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    if not (0 < capacity_rate < 1):
        raise ValueError("capacity_rate must be between 0 and 1")

    gender = rng.choice(["Female", "Male"], n, p=[0.48, 0.52])
    age_band = rng.choice(["18-35", "36-45", "46+"], n, p=[0.45, 0.34, 0.21])
    nationality = rng.choice(["Polish", "Other EU", "Non-EU"], n, p=[0.68, 0.18, 0.14])
    job_family = rng.choice(["Data Analyst", "Software Engineer", "Cybersecurity Analyst"], n,
                            p=[0.37, 0.39, 0.24])

    # Cohort feature distributions.
    skills_match = np.clip(rng.normal(66.0, 13.5, n), 5, 100).round(1)
    experience_years = np.clip(rng.gamma(2.5, 1.65, n), 0, 14).round(1)
    assessment_score = np.clip(rng.normal(68.0, 15.0, n), 0, 100).round(1)
    employment_gap_months = np.minimum(rng.poisson(5.3, n), 36)

    # Proxy features correlated with demographic attributes.
    prestige_score = np.clip(rng.normal(2.8, 1.1, n) - 0.5 * (nationality == "Non-EU"), 0, 5)
    networking_score = np.clip(rng.normal(48, 22, n) - 12 * (nationality == "Non-EU"), 0, 100)
    name_origin_proxy = np.clip(0.25 + 0.55 * (nationality == "Non-EU") + rng.normal(0, 0.16, n), 0, 1)

    # Reference classification label based on the composite qualification score.
    job_role_adj = np.select([job_family == "Software Engineer", job_family == "Cybersecurity Analyst"],
                             [1.2, -1.0], default=0.0)
    merit = (0.55 * skills_match + 2.3 * experience_years + 0.19 * assessment_score
             - 0.20 * employment_gap_months + job_role_adj)
    qualified = (merit + rng.normal(0, 5.5, n) >= 60).astype(int)

    # Initial screening rule applies explicit penalties and proxy adjustments.
    baseline_penalty = (-4.5 * (gender == "Female")
                        - 5.5 * (age_band == "46+")
                        - 5.5 * (nationality == "Non-EU"))
    proxy_effect = (1.5 * prestige_score + 0.035 * networking_score
                    - 3.0 * name_origin_proxy)
    baseline_score = merit + baseline_penalty + proxy_effect + rng.normal(0, 3.0, n)

    # Revised rule excludes explicit penalties and proxy features; capacity is fixed.
    mitigated_score = merit + rng.normal(0, 3.0, n)
    k = round(n * capacity_rate)
    baseline_selected = select_top_k(baseline_score, k)
    mitigated_selected = select_top_k(mitigated_score, k)

    return pd.DataFrame({
        "applicant_id": [f"SYN-{i:05d}" for i in range(1, n + 1)],
        "record_origin": "SYNTHETIC_GENERATED_NOT_REAL",
        "job_family": job_family,
        "gender": gender,
        "age_band": age_band,
        "nationality_group": nationality,
        "skills_match": skills_match,
        "experience_years": experience_years,
        "assessment_score": assessment_score,
        "employment_gap_months": employment_gap_months,
        "prestige_proxy": prestige_score.round(2),
        "networking_proxy": networking_score.round(2),
        "name_origin_proxy": name_origin_proxy.round(3),
        "synthetic_merit_score": merit.round(3),
        "synthetic_qualified_label": qualified,
        "baseline_score": baseline_score.round(3),
        "baseline_selected": baseline_selected,
        "mitigated_score": mitigated_score.round(3),
        "mitigated_selected": mitigated_selected,
    })
