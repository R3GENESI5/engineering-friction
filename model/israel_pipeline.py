"""
Israel Tech-Defense Pipeline Module
Models the yield pressure from degradation of the US-Israel defense
innovation pipeline due to war-driven brain drain.

Mechanism: US outsources defense innovation through Israel (Unit 8200
alumni -> cybersecurity, AI, defense tech companies). War drives
emigration. Pipeline degrades. Two effects:

  A. Cost channel: US pays more for same capabilities (replacement
     cost 2-3x). Widens deficit -> yield pressure.
  B. Strategic channel: some capabilities cannot be replaced
     domestically in the relevant timeframe. Program delays cost
     $1-2B per year per $10B program (GAO typical overrun rates).

Data point: 8,300 tech workers emigrated from Israel since October 2023
(Israeli Central Bureau of Statistics, via Calcalist).

Yield impact is small (2-5 bps). This gap matters more for the
"war becomes self-defeating" narrative than for bond math.
"""

import numpy as np
from config import (
    ISRAEL_PIPELINE, DEBT_HELD_PUBLIC_T, MODEL_HORIZON_YEARS,
    sample_triangular
)


def _to_yield_bps(deficit_increase_B, elasticity):
    """Convert deficit increase to yield pressure via issuance."""
    debt_B = DEBT_HELD_PUBLIC_T * 1000
    raw_bps = (deficit_increase_B / debt_B) * 10000
    return raw_bps * elasticity


def compute_emigration(rng):
    """
    Project cumulative emigration of defense-tech workforce
    over the model horizon.

    Returns: cumulative emigration count, annual rate
    """
    workforce = ISRAEL_PIPELINE['pre_war_workforce']
    annual_rate = sample_triangular(rng, ISRAEL_PIPELINE['annual_emigration_pct'])

    cumulative = 0
    remaining = workforce
    for yr in range(MODEL_HORIZON_YEARS):
        yr_emigration = remaining * (annual_rate / 100)
        cumulative += yr_emigration
        remaining -= yr_emigration

    return cumulative, annual_rate, remaining


def compute_cost_channel(rng, cumulative_emigration, elasticity):
    """
    Channel A: replacement cost inflation.

    Emigrated roles get filled by US-based engineers at 2-3x cost.
    The cost difference flows through defense budget to deficit.

    Returns: yield pressure in bps, breakdown
    """
    dependent_spend_B = sample_triangular(
        rng, ISRAEL_PIPELINE['us_dependent_defense_spend_B']
    )
    cost_mult = sample_triangular(
        rng, ISRAEL_PIPELINE['replacement_cost_multiplier']
    )

    # What fraction of the dependent spend is affected by emigration?
    workforce = ISRAEL_PIPELINE['pre_war_workforce']
    affected_fraction = min(cumulative_emigration / workforce, 0.80)

    # Replaceability: not all emigrated roles get replaced
    unreplaceable = sample_triangular(rng, ISRAEL_PIPELINE['unreplaceable_fraction'])
    replaced_fraction = affected_fraction * (1 - unreplaceable)

    # Cost increase: replaced roles cost more
    cost_increase_B = dependent_spend_B * replaced_fraction * (cost_mult - 1) / cost_mult

    # This is annual additional deficit spending
    yield_bps = _to_yield_bps(cost_increase_B, elasticity)

    return yield_bps, {
        'dependent_spend_B': dependent_spend_B,
        'cost_multiplier': cost_mult,
        'affected_fraction': affected_fraction,
        'replaced_fraction': replaced_fraction,
        'unreplaceable_fraction': unreplaceable,
        'annual_cost_increase_B': cost_increase_B,
    }


def compute_delay_channel(rng, cumulative_emigration, elasticity):
    """
    Channel B: program delay costs from unreplaceable capability gaps.

    Capabilities that cannot be replaced cause schedule slips.
    Each year of delay on major programs costs 8-25% of program value.

    Returns: yield pressure in bps, breakdown
    """
    dependent_spend_B = sample_triangular(
        rng, ISRAEL_PIPELINE['us_dependent_defense_spend_B']
    )
    unreplaceable = sample_triangular(rng, ISRAEL_PIPELINE['unreplaceable_fraction'])
    delay_mult = sample_triangular(rng, ISRAEL_PIPELINE['delay_cost_multiplier'])

    workforce = ISRAEL_PIPELINE['pre_war_workforce']
    affected_fraction = min(cumulative_emigration / workforce, 0.80)

    # Unreplaced portion causes delays
    unreplaced_spend_B = dependent_spend_B * affected_fraction * unreplaceable
    delay_cost_B = unreplaced_spend_B * delay_mult

    yield_bps = _to_yield_bps(delay_cost_B, elasticity)

    return yield_bps, {
        'unreplaced_spend_B': unreplaced_spend_B,
        'delay_cost_multiplier': delay_mult,
        'annual_delay_cost_B': delay_cost_B,
    }


def compute_israel_pipeline_impact(rng, elasticity):
    """
    Full Israel pipeline channel.

    Combines cost inflation and program delay costs.

    Returns:
        yield_bps: total yield pressure
        info: full breakdown
    """
    cumulative_emigration, annual_rate, remaining = compute_emigration(rng)

    cost_bps, cost_info = compute_cost_channel(rng, cumulative_emigration, elasticity)
    delay_bps, delay_info = compute_delay_channel(rng, cumulative_emigration, elasticity)

    total_bps = cost_bps + delay_bps

    return total_bps, {
        'cumulative_emigration': cumulative_emigration,
        'annual_emigration_pct': annual_rate,
        'remaining_workforce': remaining,
        'cost_bps': cost_bps,
        'delay_bps': delay_bps,
        'total_bps': total_bps,
        'total_annual_deficit_increase_B': (
            cost_info['annual_cost_increase_B'] + delay_info['annual_delay_cost_B']
        ),
        'cost_info': cost_info,
        'delay_info': delay_info,
    }


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== ISRAEL PIPELINE MODULE ===\n")

    bps, info = compute_israel_pipeline_impact(rng, elasticity=0.60)
    print(f"Single draw:")
    print(f"  Emigration: {info['cumulative_emigration']:.0f} workers "
          f"({info['annual_emigration_pct']:.1f}%/yr)")
    print(f"  Remaining workforce: {info['remaining_workforce']:.0f}")
    print(f"  Cost inflation: {info['cost_bps']:.1f} bps")
    print(f"  Program delays: {info['delay_bps']:.1f} bps")
    print(f"  Total: {bps:.1f} bps")
    print(f"  Annual deficit increase: ${info['total_annual_deficit_increase_B']:.1f}B")
    print()

    # Monte Carlo
    print("=== MONTE CARLO (1000 draws) ===\n")
    results = []
    for _ in range(1000):
        e = rng.triangular(0.25, 0.60, 2.50)
        b, _ = compute_israel_pipeline_impact(rng, e)
        results.append(b)

    arr = np.array(results)
    print(f"Median: {np.median(arr):.1f} bps, Mean: {np.mean(arr):.1f} bps")
    print(f"90% CI: [{np.percentile(arr, 5):.1f}, {np.percentile(arr, 95):.1f}]")
