#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trade_plan_calculator import calculate_plan


class TradePlanCalculatorTest(unittest.TestCase):
    def test_risk_budget_binds_and_tranches_reconcile(self) -> None:
        result = calculate_plan(
            {
                "portfolio_value": 1_000_000,
                "entry_price": 50,
                "invalidation_price": 42,
                "loss_budget_pct": 1,
                "requested_target_weight_pct": 10,
                "hard_weight_cap_pct": 15,
                "round_trip_cost_bps": 20,
                "cash_available": 1_000_000,
                "cash_reserve_pct": 10,
                "lot_size": 100,
                "tranche_split": "25,35,40",
            }
        )

        self.assertEqual(result["binding_constraints"], ["loss_budget_cap"])
        self.assertEqual(result["target_shares"], 1200)
        self.assertEqual(result["target_value"], 60_000.0)
        self.assertEqual(result["actual_target_weight_pct"], 6.0)
        self.assertLessEqual(result["estimated_loss_cash"], result["loss_budget_cash"])
        self.assertEqual(sum(item["shares"] for item in result["tranches"]), 1200)
        self.assertEqual([item["shares"] for item in result["tranches"]], [300, 400, 500])
        self.assertEqual(result["execution"], "NOT_AN_ORDER")

    def test_factor_cap_can_bind(self) -> None:
        result = calculate_plan(
            {
                "portfolio_value": 1_000_000,
                "entry_price": 20,
                "invalidation_price": 10,
                "loss_budget_pct": 5,
                "requested_target_weight_pct": 10,
                "hard_weight_cap_pct": 15,
                "factor_cap_value": 30_000,
                "cash_available": 1_000_000,
                "cash_reserve_pct": 10,
                "lot_size": 100,
            }
        )
        self.assertEqual(result["binding_constraints"], ["factor_cap_value"])
        self.assertEqual(result["target_value"], 30_000.0)

    def test_rejects_invalid_long_invalidation_price(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be below"):
            calculate_plan(
                {
                    "portfolio_value": 100_000,
                    "entry_price": 10,
                    "invalidation_price": 10,
                    "loss_budget_pct": 1,
                    "requested_target_weight_pct": 10,
                    "hard_weight_cap_pct": 15,
                    "cash_available": 100_000,
                }
            )

    def test_rejects_non_three_stage_split(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly three"):
            calculate_plan(
                {
                    "portfolio_value": 100_000,
                    "entry_price": 10,
                    "invalidation_price": 8,
                    "loss_budget_pct": 1,
                    "requested_target_weight_pct": 10,
                    "hard_weight_cap_pct": 15,
                    "cash_available": 100_000,
                    "tranche_split": "50,50",
                }
            )


if __name__ == "__main__":
    unittest.main()
