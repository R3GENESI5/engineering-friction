"""
Clock 1: Silver Strategic Scissors

Three transmission channels from silver to US fiscal/monetary pressure:

Channel A: US defense/infrastructure cost inflation
  Silver price rises -> higher costs for defense, solar, AI, grid -> wider deficit -> more issuance

Channel B: De-dollarization credibility accelerant
  China's demonstrated supply chain control -> BRICS alternatives look more credible -> faster adoption

Channel C: Supply disruption tail risk
  China restricts silver exports (rare-earths-style) -> fiscal shock + industrial disruption

Also retains the original substitution pathway (China reducing own silver dependency).
"""

import numpy as np
from config import (
    SILVER_PARAMS, DEBT_HELD_PUBLIC_T, FEDERAL_REVENUE_T,
    DEMAND_ELASTICITY, sample_triangular
)


def compute_channel_a_cost_inflation(rng):
    """
    Channel A: Silver price increase -> US federal expenditure increase -> wider deficit.

    Returns:
        additional_deficit_B: additional annual deficit from silver cost inflation
        info dict
    """
    p = SILVER_PARAMS
    cost_share_pct = sample_triangular(rng, p['silver_cost_share_pct'])
    price_increase_pct = sample_triangular(rng, p['silver_price_increase_pct'])

    # Current silver cost in federal programs
    silver_cost_B = p['silver_sensitive_federal_spend_B'] * (cost_share_pct / 100)

    # Additional cost from price increase
    additional_cost_B = silver_cost_B * (price_increase_pct / 100)

    return additional_cost_B, {
        'silver_sensitive_spend_B': p['silver_sensitive_federal_spend_B'],
        'cost_share_pct': cost_share_pct,
        'silver_cost_B': silver_cost_B,
        'price_increase_pct': price_increase_pct,
        'additional_cost_B': additional_cost_B,
    }


def compute_channel_a_yield_impact(additional_deficit_B, rng):
    """
    Convert additional deficit from silver costs to yield pressure.

    Transmission: more deficit -> more Treasury issuance -> yield pressure.
    Uses demand elasticity (not linear conversion).
    """
    debt_B = DEBT_HELD_PUBLIC_T * 1000
    elasticity = sample_triangular(rng, DEMAND_ELASTICITY)

    # Additional issuance as fraction of outstanding
    raw_bps = (additional_deficit_B / debt_B) * 10000
    yield_bps = raw_bps * elasticity

    return yield_bps, {
        'additional_deficit_B': additional_deficit_B,
        'raw_bps': raw_bps,
        'elasticity': elasticity,
        'yield_bps': yield_bps,
    }


def compute_channel_b_credibility(rng):
    """
    Channel B: Silver supply chain control demonstrates China's leverage.
    Returns a multiplier to apply to de-dollarization channels.
    """
    multiplier = sample_triangular(rng, SILVER_PARAMS['credibility_multiplier'])
    return multiplier


def compute_channel_c_disruption(rng, model_horizon_years=5):
    """
    Channel C: Tail risk of full silver export restriction.

    Binary event: each year, probability of disruption.
    Over the model horizon, compound probability.
    If triggered: fiscal shock + price spike.

    Returns:
        fiscal_shock_B: 0 if no disruption, or sampled shock if triggered
        triggered: bool
        info dict
    """
    p = SILVER_PARAMS
    annual_prob = sample_triangular(rng, p['disruption_prob_per_year'])

    # Probability of at least one disruption over horizon
    prob_none = (1 - annual_prob) ** model_horizon_years
    prob_at_least_one = 1 - prob_none

    # Roll the dice
    triggered = rng.random() < prob_at_least_one

    if triggered:
        price_spike_pct = sample_triangular(rng, p['disruption_price_spike_pct'])
        fiscal_shock_B = sample_triangular(rng, p['disruption_fiscal_shock_B'])
    else:
        price_spike_pct = 0
        fiscal_shock_B = 0

    return fiscal_shock_B, triggered, {
        'annual_prob': annual_prob,
        'horizon_years': model_horizon_years,
        'cumulative_prob': prob_at_least_one,
        'triggered': triggered,
        'price_spike_pct': price_spike_pct,
        'fiscal_shock_B': fiscal_shock_B,
    }


def compute_substitution_progress(substitution_progress_pct, rng):
    """
    Original Clock 1 mechanism: China substituting silver out of solar cells.
    Retained for completeness but now feeds into Channel B credibility.

    Returns:
        demand_drop_pct: % of global industrial silver demand removed
    """
    p = SILVER_PARAMS
    current_g = p['current_silver_per_cell_g']
    target_g = p['target_substitution_g']
    solar_pct = p['solar_pct_industrial_ag_demand']

    reduction_frac = (current_g - target_g) / current_g
    actual_reduction = reduction_frac * (substitution_progress_pct / 100)
    demand_drop_pct = actual_reduction * solar_pct

    return demand_drop_pct


def compute_clock1_impact(substitution_progress_pct, rng, model_horizon_years=5):
    """
    Full Clock 1 computation across all three channels.

    Returns:
        yield_bps: direct yield pressure from Channel A + C
        credibility_multiplier: multiplier for de-dollarization channels (Channel B)
        info dict
    """
    # Channel A: cost inflation
    additional_cost_B, cost_info = compute_channel_a_cost_inflation(rng)
    cost_yield_bps, yield_info = compute_channel_a_yield_impact(additional_cost_B, rng)

    # Channel B: credibility accelerant
    credibility_mult = compute_channel_b_credibility(rng)

    # Channel C: disruption tail risk
    disruption_shock_B, disruption_triggered, disruption_info = compute_channel_c_disruption(
        rng, model_horizon_years
    )

    # If disruption triggered, add the fiscal shock to yield pressure
    if disruption_triggered:
        disruption_yield_bps, disruption_yield_info = compute_channel_a_yield_impact(
            disruption_shock_B, rng
        )
    else:
        disruption_yield_bps = 0
        disruption_yield_info = {'yield_bps': 0}

    # Substitution progress (feeds credibility narrative)
    demand_drop_pct = compute_substitution_progress(substitution_progress_pct, rng)

    # Total direct yield pressure from Clock 1
    total_yield_bps = cost_yield_bps + disruption_yield_bps

    return total_yield_bps, credibility_mult, {
        'channel_a_cost_yield_bps': cost_yield_bps,
        'channel_a_additional_cost_B': additional_cost_B,
        'channel_b_credibility_multiplier': credibility_mult,
        'channel_c_disruption_triggered': disruption_triggered,
        'channel_c_disruption_prob': disruption_info['cumulative_prob'],
        'channel_c_disruption_yield_bps': disruption_yield_bps,
        'channel_c_fiscal_shock_B': disruption_shock_B,
        'substitution_demand_drop_pct': demand_drop_pct,
        'total_yield_bps': total_yield_bps,
    }


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== CLOCK 1: SILVER STRATEGIC SCISSORS ===\n")

    # Single draw
    yield_bps, cred_mult, info = compute_clock1_impact(50, rng, model_horizon_years=5)

    print("Channel A (cost inflation):")
    print(f"  Additional federal cost: ${info['channel_a_additional_cost_B']:.1f}B/yr")
    print(f"  Yield pressure: {info['channel_a_cost_yield_bps']:.1f} bps")
    print()
    print("Channel B (credibility accelerant):")
    print(f"  De-dollarization multiplier: {cred_mult:.2f}x")
    print()
    print("Channel C (disruption tail risk):")
    print(f"  Cumulative probability (5yr): {info['channel_c_disruption_prob']*100:.1f}%")
    print(f"  Triggered this draw: {info['channel_c_disruption_triggered']}")
    print(f"  Fiscal shock: ${info['channel_c_fiscal_shock_B']:.1f}B")
    print(f"  Yield pressure: {info['channel_c_disruption_yield_bps']:.1f} bps")
    print()
    print(f"TOTAL Clock 1 yield pressure: {yield_bps:.1f} bps")
    print()

    # Monte Carlo (1000 draws)
    print("=== MONTE CARLO (1000 draws) ===\n")
    yields = []
    mults = []
    disruptions = 0
    for _ in range(1000):
        y, m, i = compute_clock1_impact(50, rng, model_horizon_years=5)
        yields.append(y)
        mults.append(m)
        if i['channel_c_disruption_triggered']:
            disruptions += 1

    arr = np.array(yields)
    marr = np.array(mults)
    print(f"Clock 1 yield pressure:")
    print(f"  Median: {np.median(arr):.1f} bps")
    print(f"  Mean: {np.mean(arr):.1f} bps")
    print(f"  90% CI: [{np.percentile(arr, 5):.1f}, {np.percentile(arr, 95):.1f}]")
    print(f"  (vs old Clock 1: 1.2 bps)")
    print()
    print(f"Credibility multiplier:")
    print(f"  Median: {np.median(marr):.2f}x, 90% CI: [{np.percentile(marr, 5):.2f}, {np.percentile(marr, 95):.2f}]")
    print()
    print(f"Disruption events: {disruptions}/1000 ({disruptions/10:.1f}%)")
