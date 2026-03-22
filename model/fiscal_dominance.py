"""
Fiscal Dominance Regime Shift Module
Models the threshold at which monetary policy stops working and
starts amplifying the crisis.

This is NOT a pressure channel. It is a REGIME SWITCH.
Once interest payments consume enough revenue, rate hikes increase
the interest burden faster than they cool inflation. The central bank
loses its primary tool.

Theoretical basis: Leeper (1991), "Equilibria under 'Active' and
'Passive' Monetary and Fiscal Policies."

When the model's interest-to-revenue ratio crosses the threshold:
  1. Policy response damping FLIPS SIGN
  2. Instead of reducing pressure by 15 bps, rate hikes ADD 10-30 bps
  3. The defense disappears and becomes an accelerant

Calibration:
  - Brazil 2015: ~42% interest/revenue, rate hikes amplified crisis
  - Turkey 2018: ~25%, Erdogan forced rate cuts, lira collapsed
  - Italy 2011: ~25-30%, ECB had to backstop
  - Japan ongoing: kept rates near zero for decades to avoid this
  - US current: ~19% (FY2025)

CBO projection: net interest from 3.2% to 6.3% of GDP, but
nonlinear acceleration happens sooner if rates stay elevated.
"""

import numpy as np
from config import (
    FISCAL_DOMINANCE, ANNUAL_INTEREST_B, FEDERAL_REVENUE_T,
    MODEL_HORIZON_YEARS, CURRENT_AVG_RATE_PCT, DEBT_HELD_PUBLIC_T,
    ANNUAL_DEFICIT_GROWTH_T, sample_triangular
)


def compute_interest_ratio_trajectory(rng, yield_pressure_bps):
    """
    Project the interest-to-revenue ratio over the model horizon.

    The ratio grows because:
      1. Rolling debt reprices at higher rates (yield pressure from model)
      2. Debt stock grows ($2T+/yr deficits)
      3. Revenue grows more slowly than interest burden

    Args:
        rng: numpy random generator
        yield_pressure_bps: combined yield pressure from all other channels

    Returns:
        ratios_by_year: list of interest/revenue ratios, year 0 to horizon
        crossed: whether fiscal dominance threshold was crossed
        crossing_year: year of crossing (None if not crossed)
    """
    threshold = sample_triangular(rng, FISCAL_DOMINANCE['threshold_ratio'])
    current_ratio = FISCAL_DOMINANCE['current_ratio']

    # Project forward
    debt_T = DEBT_HELD_PUBLIC_T
    avg_rate = CURRENT_AVG_RATE_PCT / 100
    revenue_T = FEDERAL_REVENUE_T
    interest_B = ANNUAL_INTEREST_B

    # Yield pressure converts to rate increase on rolling debt
    # 33% of debt rolls within 1 year; the pressure reprices that tranche
    rollover_pct_yr = 0.33
    rate_increase = yield_pressure_bps / 100 / 100  # bps to decimal

    ratios = [current_ratio]
    crossed = False
    crossing_year = None

    for yr in range(1, MODEL_HORIZON_YEARS + 1):
        # Debt grows
        deficit_growth = sample_triangular(rng, ANNUAL_DEFICIT_GROWTH_T)
        debt_T += deficit_growth

        # Rate on rolled portion increases
        rolled_debt_T = debt_T * rollover_pct_yr
        new_rate_on_rolled = avg_rate + (rate_increase * min(yr, 3) / 3)  # phase in
        # Blended rate: rolled at new rate, rest at old
        blended_rate = (
            rolled_debt_T * new_rate_on_rolled +
            (debt_T - rolled_debt_T) * avg_rate
        ) / debt_T

        # Interest burden
        interest_B = debt_T * 1000 * blended_rate  # in $B

        # Revenue grows modestly (2-4% nominal)
        revenue_growth = rng.triangular(0.02, 0.03, 0.04)
        revenue_T *= (1 + revenue_growth)

        ratio = (interest_B / 1000) / revenue_T
        ratios.append(ratio)

        if ratio >= threshold and not crossed:
            crossed = True
            crossing_year = yr

    return ratios, crossed, crossing_year, threshold


def compute_fiscal_dominance_effect(rng, raw_combined_bps, adjusted_headroom_bps,
                                     policy_damping_bps):
    """
    Determine if fiscal dominance activates and compute its effect.

    When activated:
      - Policy damping is REMOVED (the 15-30 bps of defense gone)
      - Rate hikes now AMPLIFY pressure by 10-30 bps
      - Net swing: from -damping to +amplification

    Args:
        rng: numpy random generator
        raw_combined_bps: combined pressure before policy response
        adjusted_headroom_bps: the system's tolerance threshold
        policy_damping_bps: what the standard policy response would remove

    Returns:
        activated: bool
        net_effect_bps: change in pressure (positive = more pressure)
        info: breakdown dict
    """
    # Project interest ratio using current pressure
    ratios, crossed, crossing_year, threshold = compute_interest_ratio_trajectory(
        rng, raw_combined_bps
    )

    if not crossed:
        return False, 0.0, {
            'activated': False,
            'crossing_year': None,
            'threshold': threshold,
            'final_ratio': ratios[-1],
            'ratio_trajectory': ratios,
            'net_effect_bps': 0,
        }

    # Fiscal dominance activated.
    # Effect 1: policy damping disappears (we ADD BACK the damping)
    # Effect 2: rate hikes now amplify pressure
    amplification = sample_triangular(rng, FISCAL_DOMINANCE['amplification_bps'])

    # Net swing: policy was going to REMOVE damping_bps. Now it ADDS amplification.
    # Total change = damping_bps (restored) + amplification (added)
    net_effect_bps = policy_damping_bps + amplification

    # Phase in: if crossing happens in year 4, less time for full effect
    # than if it happens in year 1
    remaining_years = MODEL_HORIZON_YEARS - crossing_year
    phase_in = min(remaining_years / MODEL_HORIZON_YEARS, 1.0)
    net_effect_bps *= phase_in

    return True, net_effect_bps, {
        'activated': True,
        'crossing_year': crossing_year,
        'threshold': threshold,
        'final_ratio': ratios[-1],
        'ratio_trajectory': ratios,
        'amplification_bps': amplification,
        'damping_restored_bps': policy_damping_bps,
        'phase_in': phase_in,
        'net_effect_bps': net_effect_bps,
    }


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== FISCAL DOMINANCE MODULE ===\n")

    # Single draw at various pressure levels
    for pressure in [100, 200, 300, 400]:
        activated, effect, info = compute_fiscal_dominance_effect(
            rng, raw_combined_bps=pressure, adjusted_headroom_bps=180,
            policy_damping_bps=25
        )
        print(f"At {pressure} bps pressure:")
        print(f"  Activated: {activated}")
        if activated:
            print(f"  Crossing year: {info['crossing_year']}")
        print(f"  Final interest/revenue: {info['final_ratio']:.1%}")
        print(f"  Threshold: {info['threshold']:.1%}")
        print(f"  Net effect: {effect:.1f} bps")
        print()

    # Monte Carlo
    print("=== MONTE CARLO (1000 draws) ===\n")
    activations = 0
    effects = []
    for _ in range(1000):
        pressure = rng.triangular(100, 300, 700)
        a, e, i = compute_fiscal_dominance_effect(
            rng, pressure, 180, 25
        )
        if a:
            activations += 1
        effects.append(e)

    arr = np.array(effects)
    print(f"Activation frequency: {activations/10:.1f}%")
    print(f"Effect (all): median {np.median(arr):.1f}, mean {np.mean(arr):.1f} bps")
    if np.any(arr > 0):
        print(f"Effect (activated): median {np.median(arr[arr > 0]):.1f} bps")
    print(f"90% CI: [{np.percentile(arr, 5):.1f}, {np.percentile(arr, 95):.1f}]")
