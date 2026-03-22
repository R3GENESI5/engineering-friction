"""
Energy Price Feedback Module
Models the two-phase effect of war-driven oil price shocks on
Treasury yields.

Phase 1 (0-12 months): DOLLAR SUPPORT
  Oil priced in dollars -> buyers need more dollars -> petrodollar
  inflows increase -> Treasury demand rises temporarily.
  Effect: yield DECREASES by 5-15 bps (false calm).

Phase 2 (12-60 months): FISCAL DRAG
  Higher oil -> input costs rise -> GDP slows -> deficit widens ->
  inflation rises -> rate hikes increase debt burden.
  Effect: yield INCREASES by 10-40 bps.

Net over 5-year horizon: more pressure than relief.
But Phase 1 creates a MASKING window during which debt self-feeding
consumes additional headroom before the market reprices.

Historical calibration:
  1973: oil 4x, yields +250 bps over 18 months (inflation-driven)
  1979: oil 2.5x, yields +400 bps (Volcker tightening)
  1990: oil +130%, yields +50 bps then reversed (short war)
  2008: oil $147, yields collapsed (GFC overwhelmed)
  2022: oil +60%, yields +200 bps (Fed tightening dominant)

The interesting modeling question: does Phase 1 mask the pressure
long enough for debt self-feeding to consume additional headroom
before repricing? If yes, the system looks stable right until it isn't.
"""

import numpy as np
from config import (
    ENERGY_FEEDBACK, DEBT_HELD_PUBLIC_T, MODEL_HORIZON_YEARS,
    sample_triangular
)


def _to_yield_bps(treasury_pressure_B, elasticity):
    """Convert Treasury pressure ($B) to yield basis points."""
    debt_B = DEBT_HELD_PUBLIC_T * 1000
    raw_bps = (treasury_pressure_B / debt_B) * 10000
    return raw_bps * elasticity


def compute_oil_shock(rng):
    """Sample the war-driven oil price increase."""
    return sample_triangular(rng, ENERGY_FEEDBACK['oil_price_increase_pct'])


def compute_phase1_relief(rng, oil_increase_pct):
    """
    Phase 1: dollar support from oil price increase.

    Higher oil -> more dollar demand for oil purchases ->
    petrodollar recycling into Treasuries increases ->
    yield pressure temporarily REDUCED.

    Returns: relief in bps (positive number, to be subtracted from pressure)
    """
    relief_per_10pct = sample_triangular(
        rng, ENERGY_FEEDBACK['phase1_relief_bps_per_10pct_oil']
    )
    relief_bps = (oil_increase_pct / 10) * relief_per_10pct

    # Phase 1 lasts 12 months out of 60-month horizon = 20% of the period
    # Weight the relief by the fraction of horizon it covers
    phase1_months = ENERGY_FEEDBACK['phase1_duration_months']
    horizon_months = MODEL_HORIZON_YEARS * 12
    time_weight = phase1_months / horizon_months

    weighted_relief = relief_bps * time_weight

    return weighted_relief, {
        'oil_increase_pct': oil_increase_pct,
        'relief_per_10pct': relief_per_10pct,
        'raw_relief_bps': relief_bps,
        'time_weight': time_weight,
        'weighted_relief_bps': weighted_relief,
    }


def compute_phase2_drag(rng, oil_increase_pct, elasticity):
    """
    Phase 2: fiscal drag from oil price increase.

    Higher oil -> GDP drag -> wider deficit -> more issuance ->
    yield pressure INCREASES.

    Also: inflation from oil costs -> rate hikes -> higher interest
    burden on rolling debt.

    Returns: additional pressure in bps
    """
    drag_per_10pct = sample_triangular(
        rng, ENERGY_FEEDBACK['phase2_drag_bps_per_10pct_oil']
    )
    raw_drag_bps = (oil_increase_pct / 10) * drag_per_10pct

    # Phase 2 covers months 12-60 = 48 months out of 60 = 80%
    phase2_onset = ENERGY_FEEDBACK['phase2_onset_months']
    horizon_months = MODEL_HORIZON_YEARS * 12
    phase2_months = horizon_months - phase2_onset
    time_weight = phase2_months / horizon_months

    weighted_drag = raw_drag_bps * time_weight

    # GDP drag computation (for reporting)
    gdp_drag_pct = sample_triangular(
        rng, ENERGY_FEEDBACK['gdp_drag_per_10pct_oil']
    ) * (oil_increase_pct / 10)

    deficit_widening_B = sample_triangular(
        rng, ENERGY_FEEDBACK['deficit_widening_B_per_1pct_gdp']
    ) * gdp_drag_pct

    return weighted_drag, {
        'drag_per_10pct': drag_per_10pct,
        'raw_drag_bps': raw_drag_bps,
        'time_weight': time_weight,
        'weighted_drag_bps': weighted_drag,
        'gdp_drag_pct': gdp_drag_pct,
        'deficit_widening_B': deficit_widening_B,
    }


def compute_masking_effect(rng):
    """
    The false calm of Phase 1 allows debt self-feeding to consume
    additional headroom before the market reprices.

    During the 12-month masking window, new debt issuance occurs
    at artificially low rates. When Phase 2 hits, this debt must
    be serviced at higher rates, but the damage is done: headroom
    was consumed while the market was asleep.

    Returns: additional headroom erosion in bps
    """
    erosion = sample_triangular(
        rng, ENERGY_FEEDBACK['masking_additional_headroom_erosion_bps']
    )
    return erosion


def compute_energy_feedback_impact(rng, elasticity):
    """
    Full energy feedback channel.

    Net effect = Phase 2 drag - Phase 1 relief + masking erosion.

    Args:
        rng: numpy random generator
        elasticity: pre-sampled demand elasticity (shared)

    Returns:
        net_yield_bps: net yield pressure (positive = more pressure)
        headroom_erosion_bps: additional headroom consumed during masking
        info: full breakdown dict
    """
    # Oil shock
    oil_increase = compute_oil_shock(rng)

    # Phase 1: temporary relief
    relief_bps, phase1_info = compute_phase1_relief(rng, oil_increase)

    # Phase 2: sustained drag
    drag_bps, phase2_info = compute_phase2_drag(rng, oil_increase, elasticity)

    # Net yield effect
    net_bps = drag_bps - relief_bps

    # Masking effect on headroom
    headroom_erosion = compute_masking_effect(rng)

    return net_bps, headroom_erosion, {
        'oil_increase_pct': oil_increase,
        'phase1_relief_bps': relief_bps,
        'phase2_drag_bps': drag_bps,
        'net_yield_bps': net_bps,
        'headroom_erosion_bps': headroom_erosion,
        'phase1': phase1_info,
        'phase2': phase2_info,
    }


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== ENERGY FEEDBACK MODULE ===\n")

    # Single draw
    net, erosion, info = compute_energy_feedback_impact(rng, elasticity=0.60)
    print(f"Single draw:")
    print(f"  Oil increase: {info['oil_increase_pct']:.0f}%")
    print(f"  Phase 1 relief: {info['phase1_relief_bps']:.1f} bps")
    print(f"  Phase 2 drag: {info['phase2_drag_bps']:.1f} bps")
    print(f"  Net yield effect: {net:.1f} bps")
    print(f"  Headroom erosion (masking): {erosion:.1f} bps")
    print(f"  GDP drag: {info['phase2']['gdp_drag_pct']:.2f}%")
    print(f"  Deficit widening: ${info['phase2']['deficit_widening_B']:.0f}B")
    print()

    # Monte Carlo
    print("=== MONTE CARLO (1000 draws) ===\n")
    nets = []
    erosions = []
    for _ in range(1000):
        e = rng.triangular(0.25, 0.60, 2.50)
        n, er, _ = compute_energy_feedback_impact(rng, e)
        nets.append(n)
        erosions.append(er)

    narr = np.array(nets)
    earr = np.array(erosions)
    print(f"Net yield effect:")
    print(f"  Median: {np.median(narr):.1f} bps, Mean: {np.mean(narr):.1f} bps")
    print(f"  90% CI: [{np.percentile(narr, 5):.1f}, {np.percentile(narr, 95):.1f}]")
    print(f"  Negative (Phase 1 dominates): {np.sum(narr < 0)/10:.1f}%")
    print()
    print(f"Headroom erosion (masking):")
    print(f"  Median: {np.median(earr):.1f} bps, Mean: {np.mean(earr):.1f} bps")
