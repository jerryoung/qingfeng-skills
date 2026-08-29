#!/usr/bin/env python3
"""Calculate a long-only draft position size and tranche quantities."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_FLOOR
from typing import Iterable, Union


HUNDRED = Decimal("100")
TEN_THOUSAND = Decimal("10000")


def decimal(value: object) -> Decimal:
    return Decimal(str(value))


def positive(name: str, value: Decimal) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")


def non_negative(name: str, value: Decimal) -> None:
    if value < 0:
        raise ValueError(f"{name} must not be negative")


def floor_to_lot(shares: Decimal, lot_size: int) -> int:
    if lot_size <= 0:
        raise ValueError("lot_size must be greater than zero")
    lots = (shares / Decimal(lot_size)).to_integral_value(rounding=ROUND_FLOOR)
    return int(lots) * lot_size


def parse_split(raw: Union[str, Iterable[object]]) -> list[Decimal]:
    values = raw.split(",") if isinstance(raw, str) else list(raw)
    split = [decimal(value) for value in values]
    if len(split) != 3 or any(value < 0 for value in split):
        raise ValueError("tranche split must contain exactly three non-negative values")
    if sum(split) != HUNDRED:
        raise ValueError("tranche split must sum to 100")
    return split


def allocate_tranches(total_shares: int, lot_size: int, split: list[Decimal]) -> list[int]:
    allocated: list[int] = []
    remaining = total_shares
    for ratio in split[:-1]:
        shares = floor_to_lot(Decimal(total_shares) * ratio / HUNDRED, lot_size)
        allocated.append(shares)
        remaining -= shares
    allocated.append(remaining)
    return allocated


def calculate_plan(inputs: dict[str, object]) -> dict[str, object]:
    portfolio_value = decimal(inputs["portfolio_value"])
    entry_price = decimal(inputs["entry_price"])
    invalidation_price = decimal(inputs["invalidation_price"])
    loss_budget_pct = decimal(inputs["loss_budget_pct"])
    requested_weight_pct = decimal(inputs["requested_target_weight_pct"])
    hard_cap_pct = decimal(inputs["hard_weight_cap_pct"])
    round_trip_cost_bps = decimal(inputs.get("round_trip_cost_bps", 0))
    cash_available = decimal(inputs["cash_available"])
    cash_reserve_pct = decimal(inputs.get("cash_reserve_pct", 10))
    lot_size = int(inputs.get("lot_size", 1))
    split = parse_split(inputs.get("tranche_split", "25,35,40"))

    for name, value in (
        ("portfolio_value", portfolio_value),
        ("entry_price", entry_price),
        ("loss_budget_pct", loss_budget_pct),
        ("requested_target_weight_pct", requested_weight_pct),
        ("hard_weight_cap_pct", hard_cap_pct),
    ):
        positive(name, value)
    for name, value in (
        ("invalidation_price", invalidation_price),
        ("round_trip_cost_bps", round_trip_cost_bps),
        ("cash_available", cash_available),
        ("cash_reserve_pct", cash_reserve_pct),
    ):
        non_negative(name, value)
    if invalidation_price >= entry_price:
        raise ValueError("invalidation_price must be below entry_price for a long plan")
    if cash_reserve_pct > HUNDRED:
        raise ValueError("cash_reserve_pct must not exceed 100")

    price_loss_fraction = (entry_price - invalidation_price) / entry_price
    round_trip_cost_fraction = round_trip_cost_bps / TEN_THOUSAND
    planned_loss_fraction = price_loss_fraction + round_trip_cost_fraction
    loss_budget_cash = portfolio_value * loss_budget_pct / HUNDRED
    loss_budget_cap_value = loss_budget_cash / planned_loss_fraction
    requested_value = portfolio_value * requested_weight_pct / HUNDRED
    hard_cap_value = portfolio_value * hard_cap_pct / HUNDRED
    reserve_cash = portfolio_value * cash_reserve_pct / HUNDRED
    deployable_cash = max(cash_available - reserve_cash, Decimal("0"))

    constraint_values: dict[str, Decimal] = {
        "requested_target": requested_value,
        "hard_weight_cap": hard_cap_value,
        "loss_budget_cap": loss_budget_cap_value,
        "deployable_cash": deployable_cash,
    }
    for key in ("factor_cap_value", "liquidity_cap_value", "opportunity_cost_cap_value"):
        if inputs.get(key) is not None:
            value = decimal(inputs[key])
            non_negative(key, value)
            constraint_values[key] = value

    raw_target_value = min(constraint_values.values())
    target_shares = floor_to_lot(raw_target_value / entry_price, lot_size)
    target_value = Decimal(target_shares) * entry_price
    tranche_shares = allocate_tranches(target_shares, lot_size, split)
    estimated_loss_cash = target_value * planned_loss_fraction
    actual_weight_pct = target_value / portfolio_value * HUNDRED
    minimum = min(constraint_values.values())
    binding_constraints = [key for key, value in constraint_values.items() if value == minimum]

    def number(value: Decimal) -> float:
        return float(value.quantize(Decimal("0.0001")))

    return {
        "status": "DRAFT" if target_shares > 0 else "NO_ACTION",
        "approval": "REQUIRES_USER_APPROVAL",
        "execution": "NOT_AN_ORDER",
        "planned_loss_fraction_pct": number(planned_loss_fraction * HUNDRED),
        "loss_budget_cash": number(loss_budget_cash),
        "constraint_values": {key: number(value) for key, value in constraint_values.items()},
        "binding_constraints": binding_constraints,
        "target_shares": target_shares,
        "target_value": number(target_value),
        "actual_target_weight_pct": number(actual_weight_pct),
        "estimated_loss_cash": number(estimated_loss_cash),
        "tranches": [
            {"stage": stage, "ratio_pct": number(ratio), "shares": shares}
            for stage, ratio, shares in zip(
                ("trial", "confirmation", "completion"), split, tranche_shares
            )
        ],
        "rounding_note": f"share quantities are rounded down to lot size {lot_size}",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portfolio-value", required=True)
    parser.add_argument("--entry-price", required=True)
    parser.add_argument("--invalidation-price", required=True)
    parser.add_argument("--loss-budget-pct", required=True)
    parser.add_argument("--requested-target-weight-pct", required=True)
    parser.add_argument("--hard-weight-cap-pct", required=True)
    parser.add_argument("--round-trip-cost-bps", default="0")
    parser.add_argument("--cash-available", required=True)
    parser.add_argument("--cash-reserve-pct", default="10")
    parser.add_argument("--factor-cap-value")
    parser.add_argument("--liquidity-cap-value")
    parser.add_argument("--opportunity-cost-cap-value")
    parser.add_argument("--lot-size", default=1, type=int)
    parser.add_argument("--tranche-split", default="25,35,40")
    return parser


def main() -> None:
    args = vars(build_parser().parse_args())
    inputs = {key: value for key, value in args.items() if value is not None}
    print(json.dumps(calculate_plan(inputs), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
