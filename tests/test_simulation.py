import unittest
import numpy as np
import pandas as pd
from src.simulation import generate_synthetic_applicants,select_top_k,N_APPLICANTS
from src.metrics import subgroup_metrics,all_metrics,fairness_summary,wilson_interval,rate

class SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate_synthetic_applicants()
        cls.stats = all_metrics(cls.data)
        cls.summary = fairness_summary(cls.stats)

    def test_size_and_no_duplicate_ids(self):
        self.assertEqual(len(self.data),N_APPLICANTS)
        self.assertEqual(self.data.applicant_id.nunique(),len(self.data))

    def test_is_explicitly_synthetic(self):
        self.assertEqual(set(self.data.record_origin),{'SYNTHETIC_GENERATED_NOT_REAL'})

    def test_generator_reproducible(self):
        again=generate_synthetic_applicants()
        pd.testing.assert_frame_equal(self.data,again)

    def test_top_k_capacity_fixed(self):
        self.assertEqual(int(self.data.baseline_selected.sum()),2100)
        self.assertEqual(int(self.data.mitigated_selected.sum()),2100)

    def test_no_real_identifiers(self):
        for column in ['name','email','phone','address','date_of_birth']:
            self.assertNotIn(column,self.data.columns)

    def test_selection_exact_on_ties(self):
        np.testing.assert_array_equal(select_top_k([3,3,2,1],2),[1,1,0,0])

    def test_population_counts_partition(self):
        for attribute in ['gender','age_band','nationality_group']:
            self.assertEqual(int(self.stats[(self.stats.scenario=='Baseline') & (self.stats.attribute==attribute)].n.sum()),6000)

    def test_wilson_interval_valid(self):
        lo,hi=wilson_interval(30,100)
        self.assertLess(lo,.30); self.assertGreater(hi,.30)

    def test_division_by_zero_is_not_a_misleading_zero(self):
        self.assertTrue(np.isnan(rate(0,0)))

    def test_four_fifths_flag_is_heuristic(self):
        rates=subgroup_metrics(self.data,'nationality_group','baseline_selected')
        self.assertTrue(rates.four_fifths_flag.any())

    def test_mitigation_improves_min_ratios(self):
        piv=self.summary.pivot(index='attribute',columns='scenario',values='min_selection_ratio')
        self.assertTrue((piv.Mitigated>piv.Baseline).all())

    def test_synthetic_label_is_binary(self):
        self.assertTrue(set(self.data.synthetic_qualified_label.unique()) <= {0,1})

    def test_metrics_bounded(self):
        self.assertTrue(self.stats.selection_rate.between(0,1).all())
        self.assertTrue(self.stats.tpr.between(0,1).all())
        self.assertTrue(self.stats.fpr.between(0,1).all())

if __name__ == '__main__':unittest.main()
