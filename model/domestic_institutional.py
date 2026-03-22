"""
Domestic Institutional Flight Module
Models yield pressure from US pension funds, insurance companies,
mutual funds, and money market funds forced to sell Treasuries
under confidence events.

These holders operate under regulatory mandates that create CLIFF
behavior: they hold until a trigger fires, then rebalance in bulk.
Triggers: ratings downgrade, breach of internal risk limits,
mark-to-market loss forcing selling.

Calibration anchor: UK gilt crisis, September 2022.
  - LDI funds forced to sell gilts into falling market
  - 100+ bps rise in 4 days
  - LDI selling accounted for ~50% of price decline (Bank of England)
  - BoE emergency intervention on day 5 stopped the cascade

US analogues: SVB cascade (March 2023), repo spike (Sept 2019),
Treasury dash-for-cash (March 2020), S&P downgrade (Aug 2011).

Key insight: this channel is CONDITIONAL. In most iterations, nothing
happens. When it fires, it produces 40-120 bps of concentrated selling
that the market must absorb in days.
"""

import numpy as np
from config import (
    DOMESTIC_INSTITUTIONAL, DEBT_HELD_PUBLIC_T, MODEL_HORIZON_YEARS,
    sample_triangular
)


def _to_yield_bps(treasury_selling_B, elasticity):
    """Convert Treasury selling volume to yield basis points."""
    debt_B = DEBT_HELD_PUBLIC_T * 1000
    raw_bps = (treasury_selling_B / debt_B) * 10000
    return raw_bps * elasticity


def compute_shock_occurrence(rng, existing_pressure_bps=0):
    """
    Determine if a confidence shock fires over the model horizon.

    Existing pressure from other channels elevates shock probability:
    a system already under stress needs a smaller catalyst.

    Returns: (shock_occurred, n_shocks, max_severity)
    """
    base_prob = sample_triangular(rng, DOMESTIC_INSTITUTIONAL['shock_probability_per_year'])

    # Existing pressure boost: each 50 bps adds 3pp to annual probability
    pressure_boost = (existing_pressure_bps / 50) * 0.03
    effective_prob = min(base_prob + pressure_boost, 0.80)

    shocks = []
    for yr in range(MODEL_HORIZON_YEARS):
        if rng.random() < effective_prob:
            # Severity 0-1: scales which segments respond
            severity = rng.triangular(0.3, 0.6, 1.0)
            shocks.append(severity)

    if not shocks:
        return False, 0, 0.0, effective_prob

    return True, len(shocks), max(shocks), effective_prob


def compute_segment_selling(rng, severity):
    """
    Compute forced selling across holder segments for a given shock severity.

    Response speed determines the severity threshold at which each segment
    starts selling. Fast segments (money market, mutual funds) react to
    mild shocks. Slow segments (pensions) only sell in severe events.
    """
    segments = DOMESTIC_INSTITUTIONAL['segments']
    breakdown = {}
    total_selling_B = 0

    for name, seg in segments.items():
        base_pct = sample_triangular(rng, seg['rebalance_pct'])

        # Severity threshold by response speed
        if seg['response_speed'] == 'fast':
            threshold = 0.2   # reacts to mild shocks
        elif seg['response_speed'] == 'medium':
            threshold = 0.4
        else:  # slow
            threshold = 0.6   # only severe shocks

        if severity < threshold:
            effective_pct = 0
        else:
            ramp = min((severity - threshold) / (1.0 - threshold), 1.0)
            effective_pct = base_pct * ramp

        selling_B = seg['holdings_T'] * 1000 * (effective_pct / 100)

        breakdown[name] = {
            'holdings_T': seg['holdings_T'],
            'base_rebalance_pct': base_pct,
            'effective_rebalance_pct': effective_pct,
            'selling_B': selling_B,
        }
        total_selling_B += selling_B

    return total_selling_B, breakdown


def compute_domestic_institutional_impact(rng, elasticity, existing_pressure_bps=0):
    """
    Full domestic institutional channel.

    Conditional: fires only when a confidence shock occurs.
    When it fires: segment-specific selling with LDI feedback cascade.
    Fed can intervene (truncates tail, doesn't eliminate pressure).

    Args:
        rng: numpy random generator
        elasticity: pre-sampled demand elasticity (shared)
        existing_pressure_bps: pressure from other channels

    Returns:
        yield_bps, info dict
    """
    shock, n_shocks, severity, eff_prob = compute_shock_occurrence(
        rng, existing_pressure_bps
    )

    if not shock:
        return 0.0, {
            'shock_occurred': False,
            'n_shocks': 0,
            'severity': 0,
            'effective_annual_prob': eff_prob,
            'initial_selling_B': 0,
            'feedback_multiplier': 1.0,
            'total_selling_B': 0,
            'yield_bps_raw': 0,
            'fed_intervention': False,
            'yield_bps': 0,
        }

    # Forced selling
    initial_selling_B, segment_breakdown = compute_segment_selling(rng, severity)

    # LDI feedback cascade: selling depresses prices, triggers more selling
    feedback_mult = sample_triangular(rng, DOMESTIC_INSTITUTIONAL['feedback_multiplier'])
    total_selling_B = initial_selling_B * feedback_mult

    # Convert to yield pressure
    # Institutional selling is CONCENTRATED (days-weeks), so it hits
    # harder per dollar than gradual channels. Modest speed premium
    # on top of shared elasticity (which already captures regime).
    speed_premium = rng.triangular(1.0, 1.15, 1.35)
    effective_elasticity = elasticity * speed_premium
    yield_bps = _to_yield_bps(total_selling_B, effective_elasticity)

    # Fed intervention: standing repo facility, emergency lending
    # BoE intervened on day 5 of gilt crisis. Fed has more tools.
    fed_intervention = False
    if yield_bps > 60 and rng.random() < 0.70:
        cap_fraction = rng.triangular(0.3, 0.5, 0.7)
        yield_bps_capped = yield_bps * cap_fraction
        fed_intervention = True
    else:
        yield_bps_capped = yield_bps

    return yield_bps_capped, {
        'shock_occurred': True,
        'n_shocks': n_shocks,
        'severity': severity,
        'effective_annual_prob': eff_prob,
        'initial_selling_B': initial_selling_B,
        'feedback_multiplier': feedback_mult,
        'total_selling_B': total_selling_B,
        'speed_premium': speed_premium,
        'yield_bps_raw': yield_bps,
        'fed_intervention': fed_intervention,
        'yield_bps': yield_bps_capped,
        'segment_breakdown': segment_breakdown,
    }


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== DOMESTIC INSTITUTIONAL MODULE ===\n")

    bps, info = compute_domestic_institutional_impact(rng, elasticity=0.60)
    print(f"Single draw:")
    print(f"  Shock: {info['shock_occurred']}, severity: {info['severity']:.2f}")
    if info['shock_occurred']:
        print(f"  Initial selling: ${info['initial_selling_B']:.0f}B")
        print(f"  Feedback: {info['feedback_multiplier']:.2f}x -> ${info['total_selling_B']:.0f}B")
        print(f"  Fed intervention: {info['fed_intervention']}")
        print(f"  Yield: {bps:.1f} bps")
    print()

    # Monte Carlo
    print("=== MONTE CARLO (1000 draws) ===\n")
    results = []
    shock_count = 0
    for _ in range(1000):
        e = rng.triangular(0.25, 0.60, 2.50)
        b, i = compute_domestic_institutional_impact(rng, e, existing_pressure_bps=300)
        results.append(b)
        if i['shock_occurred']:
            shock_count += 1

    arr = np.array(results)
    print(f"With 300 bps existing pressure:")
    print(f"  Shock frequency: {shock_count/10:.1f}%")
    print(f"  Median (all): {np.median(arr):.1f} bps")
    if np.any(arr > 0):
        print(f"  Median (shocked): {np.median(arr[arr > 0]):.1f} bps")
    print(f"  Mean: {np.mean(arr):.1f} bps")
    print(f"  90% CI: [{np.percentile(arr, 5):.1f}, {np.percentile(arr, 95):.1f}]")
