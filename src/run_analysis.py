"""Generate TechHire cohort data, fairness metrics, and dashboards."""
from pathlib import Path
from src.simulation import generate_synthetic_applicants, SEED
from src.metrics import all_metrics, fairness_summary
from src.charts import generate_figures

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT / 'data'; RESULTS=ROOT / 'results'; DATA.mkdir(exist_ok=True)

def main():
    applicants=generate_synthetic_applicants()
    metrics=all_metrics(applicants)
    summary=fairness_summary(metrics)
    applicants.to_csv(DATA/'synthetic_applicants.csv',index=False)
    metrics.to_csv(DATA/'subgroup_metrics.csv',index=False)
    summary.to_csv(DATA/'fairness_summary.csv',index=False)
    generated=generate_figures(applicants,metrics,summary,RESULTS)
    print('Analysis seed:',SEED,'| applicant profiles:',len(applicants))
    print('Selections',applicants.baseline_selected.sum(),applicants.mitigated_selected.sum())
    print(summary.to_string(index=False, float_format=lambda x:f'{x:.3f}'))
    print('Charts:',', '.join(generated))

if __name__=='__main__':main()
