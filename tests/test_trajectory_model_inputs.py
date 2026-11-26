"""Small, hand-calculated checks for notebook matching and model time boundaries."""

import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


NOTEBOOK = Path(__file__).resolve().parents[1] / 'notebooks' / 'trajectory_reconstruction.ipynb'
CELLS = {
    cell['id']: ''.join(cell['source'])
    for cell in json.loads(NOTEBOOK.read_text(encoding='utf-8'))['cells']
    if cell['cell_type'] == 'code'
}


def run_cell(name, context):
    context.update(pd=pd, np=np, display=lambda *args: None)
    exec(compile(CELLS[name], name, 'exec'), context)


class ModelInputTests(unittest.TestCase):
    def test_pair_order_repeated_offers_and_time_boundaries(self):
        # Two completions share a timestamp with three transactions. The third
        # transaction must remain unmatched, and another customer cannot consume it.
        rows = [
            ('a', 'transaction', 0, None, 10),
            ('a', 'offer completed', 0, 'same_offer', 0),
            ('a', 'transaction', 0, None, 20),
            ('a', 'offer completed', 0, 'other_offer', 0),
            ('a', 'transaction', 0, None, 30),
            ('b', 'offer completed', 0, 'other_offer', 0),
            ('a', 'transaction', 71, None, 5),
            ('a', 'transaction', 72, None, 40),
            ('a', 'offer completed', 72, 'same_offer', 0),
        ]
        events = pd.DataFrame(rows, columns=['person', 'event', 'time', 'offer_id', 'amount'])
        events['_event_order'] = range(len(events))
        context = {'events': events}
        run_cell('model-history-matching', context)
        pairs = context['completion_pairs'].set_index('_event_order')
        self.assertEqual(pairs.loc[1, 'amount'], 10)
        self.assertEqual(pairs.loc[3, 'amount'], 20)
        self.assertTrue(pd.isna(pairs.loc[5, 'transaction_event_order']))
        self.assertEqual(pairs.loc[8, 'amount'], 40)  # repeated offer is retained
        self.assertEqual(context['history_transactions']['unmatched'].tolist(),
                         [False, False, True, True, False])

        # At t=72, the purchase at t=72 is an outcome, never a history feature.
        context.update(
            decision_times=np.array([0, 72]), HOURS_PER_DAY=24, FOLLOWUP_HOURS=72,
            receipts=pd.DataFrame({'person': ['a'], 'time': [0]}),
            model_base=pd.DataFrame({'person': ['a', 'b', 'a', 'b'],
                                     'decision_time': [0, 0, 72, 72]}),
        )
        run_cell('model-history-features', context)
        run_cell('model-outcomes', context)
        table = context['training_table'].set_index(['person', 'decision_time'])
        self.assertEqual(table.loc[('a', 0), 'prior_purchase_count'], 0)
        self.assertEqual(table.loc[('a', 0), 'spend'], 65)
        self.assertEqual(table.loc[('a', 72), 'prior_total_spend'], 65)
        self.assertEqual(table.loc[('a', 72), 'prior_unmatched_spend'], 35)
        self.assertEqual(table.loc[('a', 72), 'spend'], 40)
        self.assertEqual(table.loc[('b', 72), 'purchased'], 0)

    def test_controls_and_exposure_exclusions(self):
        # All profiles, including customers with no events, enter the grid.
        # Prior informational exposure invalidates a no-offer control as well.
        receipts = pd.DataFrame([
            ('carryover', 0, 'info', 'informational', 200),
            ('treated', 168, 'bogo', 'bogo', 300),
            ('multiple', 168, 'bogo', 'bogo', 300),
            ('multiple', 168, 'discount', 'discount', 300),
            ('info_now', 168, 'info', 'informational', 240),
        ], columns=['person', 'time', 'offer_id', 'offer_type', 'expiry_time'])
        context = {
            'receipts': receipts,
            'profile': pd.DataFrame({'person': ['control', 'carryover', 'treated', 'multiple', 'info_now']}),
            'events': pd.DataFrame({'person': ['treated']}),
            'FOLLOWUP_HOURS': 72, 'OBSERVATION_END_HOUR': 300,
            'TREATMENT_ARMS': {0: 'no_offer', 1: 'bogo', 2: 'discount', 3: 'informational'},
            'ARM_BY_TYPE': {'no_offer': 0, 'bogo': 1, 'discount': 2, 'informational': 3},
        }
        run_cell('model-decision-grid', context)
        run_cell('model-eligibility', context)
        table = context['decision_audit'].set_index(['person', 'decision_time'])
        self.assertTrue(table.loc[('control', 168), 'eligible'])
        self.assertEqual(table.loc[('control', 168), 'treatment'], 0)
        self.assertEqual(table.loc[('carryover', 168), 'exclusion_reason'], 'prior_active_offer')
        self.assertEqual(table.loc[('multiple', 168), 'exclusion_reason'], 'multiple_new_offers')
        self.assertEqual(table.loc[('info_now', 168), 'treatment'], 3)
        self.assertEqual(table.loc[('treated', 168), 'treatment'], 1)


if __name__ == '__main__':
    unittest.main()
