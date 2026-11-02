# TechHire applicant cohort — data dictionary

| Column | Purpose |
| --- | --- |
| applicant_id | Deterministic record identifier (`SYN-00001` etc.) |
| record_origin | Dataset origin indicator |
| job_family | Job family |
| gender | Grouping used in subgroup analysis |
| age_band | Broad age group |
| nationality_group | Nationality grouping |
| skills_match | Generated job skills match (0–100) |
| experience_years | Generated experience years |
| assessment_score | Generated structured assessment (0–100) |
| employment_gap_months | Synthetic gap length |
| prestige_proxy | Prestige proxy signal that is non-job-related in this simulation |
| networking_proxy | Networking proxy signal |
| name_origin_proxy | Category-correlated signal; **not derived from names or real people** |
| synthetic_merit_score | Composite qualification score |
| synthetic_qualified_label | Qualification reference for TPR/FPR |
| baseline_score | Baseline screening score with intentionally injected demographic effects |
| baseline_selected | Top 35% by baseline_score |
| mitigated_score | Job-related-only selection score with injected non-job effects removed |
| mitigated_selected | Top 35% by mitigated_score |

`subgroup_metrics.csv` and `fairness_summary.csv` are derived automatically from the applicant CSV by the supplied Python pipeline.
