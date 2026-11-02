"""Fairness-screening metrics (descriptive, not legal conclusions)."""
from __future__ import annotations
import math
import pandas as pd

GROUP_ORDER = {
    "gender": ["Female", "Male"],
    "age_band": ["18-35", "36-45", "46+"],
    "nationality_group": ["Polish", "Other EU", "Non-EU"],
}

def rate(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return float("nan"), float("nan")
    p = successes / n
    denom = 1 + z*z/n
    mid = (p + z*z/(2*n)) / denom
    half = z / denom * math.sqrt((p*(1-p)/n) + (z*z/(4*n*n)))
    return max(0., mid-half), min(1., mid+half)


def subgroup_metrics(df: pd.DataFrame, attribute: str, outcome: str) -> pd.DataFrame:
    if attribute not in GROUP_ORDER:
        raise ValueError("Unsupported attribute")
    rows = []
    for group in GROUP_ORDER[attribute]:
        sample = df.loc[df[attribute] == group]
        y = sample["synthetic_qualified_label"].astype(int)
        p = sample[outcome].astype(int)
        tp = int(((p == 1) & (y == 1)).sum())
        fp = int(((p == 1) & (y == 0)).sum())
        positives = int((y == 1).sum())
        negatives = int((y == 0).sum())
        selected = int((p == 1).sum())
        low, high = wilson_interval(selected, len(sample))
        rows.append({
            "attribute": attribute, "group": group,
            "n": int(len(sample)), "selected": selected,
            "qualified_n": positives, "unqualified_n": negatives,
            "true_positives": tp, "false_positives": fp,
            "selection_rate": rate(selected, len(sample)),
            "selection_ci_low": low, "selection_ci_high": high,
            "tpr": rate(tp, positives), "fpr": rate(fp, negatives),
        })
    out = pd.DataFrame(rows)
    max_s = out["selection_rate"].max()
    out["selection_ratio_to_max"] = out["selection_rate"] / max_s
    out["four_fifths_flag"] = out["selection_ratio_to_max"] < 0.8
    return out


def all_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Produce group-level fairness metrics for both synthetic scoring rules."""
    return pd.concat([
        subgroup_metrics(df, attribute, outcome).assign(
            scenario="Baseline" if outcome == "baseline_selected" else "Mitigated"
        )
        for outcome in ["baseline_selected", "mitigated_selected"]
        for attribute in GROUP_ORDER
    ], ignore_index=True)


def fairness_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (scenario, attr), subset in metrics.groupby(["scenario", "attribute"], sort=False):
        out.append({
            "scenario": scenario, "attribute": attr,
            "min_selection_ratio": subset["selection_ratio_to_max"].min(),
            "selection_rate_gap_pp": 100 * (subset["selection_rate"].max() - subset["selection_rate"].min()),
            "tpr_gap_pp": 100 * (subset["tpr"].max() - subset["tpr"].min()),
            "fpr_gap_pp": 100 * (subset["fpr"].max() - subset["fpr"].min()),
            "equalized_odds_gap_pp": 100 * max(
                subset["tpr"].max() - subset["tpr"].min(),
                subset["fpr"].max() - subset["fpr"].min(),
            ),
        })
    return pd.DataFrame(out)
