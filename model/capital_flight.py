"""
Regional Capital Flight Module
Models yield pressure from Middle East / Gulf private wealth fleeing
the war zone to London, Zurich, Istanbul, Delhi, and Singapore.

The existing model covers:
  - Sovereign de-dollarization (central banks selling Treasuries)
  - Household withdrawal (Clock 3 biology)

This fills a different gap: private capital flight from the region
under conflict. Gulf families, Iranian diaspora capital, Lebanese
offshore wealth, Saudi corporate treasuries -- money that currently
sits in or passes through USD assets, pulled out and redeployed to
non-dollar havens as the war makes the region unstable.

Two transmission paths to Treasury yield pressure:
  A. Direct: Gulf private holdings of US Treasuries get sold, proceeds
     moved to London gilts, Swiss bonds, Singapore sovereign bonds,
     Indian government bonds, Istanbul real estate, gold.
  B. Indirect: petrodollar recycling collapses. Gulf private sector
     used to recycle oil revenue into US assets. Flight breaks that loop.

Calibration anchors:
  - Lebanon 2019-2020: $10B+ pulled in months, moved to Dubai/Zurich/London.
    Currency lost 98%. Deposits above $100K frozen.
  - Russia 2022: $50-80B moved before asset freeze (ASSUMPTION).
    Redirected to Dubai, Istanbul, Delhi.
  - Iran ongoing: $200-300B diaspora capital (scattered estimates),
    concentrated in Dubai, Istanbul, London, Toronto.

Key structural point: the DESTINATIONS matter. Money going to London
partially stays in dollar assets (London has deep USD markets). Money
going to Istanbul, Delhi, Singapore mostly exits the dollar entirely.
The dollar-exit fraction is what creates Treasury pressure.
"""

import numpy as np
from config import (
    CAPITAL_FLIGHT, DEBT_HELD_PUBLIC_T, DEMAND_ELASTICITY,
    MODEL_HORIZON_YEARS, sample_triangular
)


def _to_yield_bps(treasury_pressure_B, elasticity):
    """Convert Treasury pressure ($B) to yield basis points."""
    debt_B = DEBT_HELD_PUBLIC_T * 1000
    raw_bps = (treasury_pressure_B / debt_B) * 10000
    return raw_bps * elasticity


def compute_direct_treasury_selling(rng, horizon_years=MODEL_HORIZON_YEARS):
    """
    Channel A: Gulf private holders sell US Treasuries directly.

    Gulf private USD assets (family offices, HNWI, corporate treasuries)
    hold a fraction in Treasuries. War triggers annual flight, cumulating
    over the model horizon. Flight accelerates if Hormuz is threatened.

    Returns: total selling in $B over horizon, breakdown dict
    """
    # Sample total Gulf private USD holdings
    total_usd_B = sample_triangular(rng, CAPITAL_FLIGHT['gulf_private_usd_T']) * 1000
    treasury_frac = sample_triangular(rng, CAPITAL_FLIGHT['treasury_fraction'])
    treasury_holdings_B = total_usd_B * treasury_frac

    # Annual flight rate
    annual_flight_pct = sample_triangular(rng, CAPITAL_FLIGHT['annual_flight_pct'])

    # Hormuz escalation: check each year
    cumulative_flight_B = 0
    hormuz_triggered = False
    remaining_B = treasury_holdings_B

    for yr in range(horizon_years):
        hormuz_prob = sample_triangular(rng, CAPITAL_FLIGHT['hormuz_threat_prob_per_year'])
        if rng.random() < hormuz_prob:
            hormuz_triggered = True
            multiplier = sample_triangular(rng, CAPITAL_FLIGHT['hormuz_flight_multiplier'])
            yr_flight_pct = min(annual_flight_pct * multiplier, 60)  # cap at 60% in one year
        else:
            yr_flight_pct = annual_flight_pct

        yr_flight_B = remaining_B * (yr_flight_pct / 100)
        cumulative_flight_B += yr_flight_B
        remaining_B -= yr_flight_B

        if remaining_B < 0:
            remaining_B = 0

    # Not all of the sold Treasuries create NET pressure.
    # Some flight goes to destinations that keep the money in USD.
    # Compute dollar-exit fraction based on destination mix.
    destinations = CAPITAL_FLIGHT['destinations']
    dollar_exit_fraction = 0
    dest_breakdown = {}

    for dest, params in destinations.items():
        share_pct = sample_triangular(rng, params['share_pct'])
        stays_usd_pct = params['stays_in_usd_pct']
        exits_usd_pct = 100 - stays_usd_pct
        # This destination's contribution to dollar exit
        dest_dollar_exit = (share_pct / 100) * (exits_usd_pct / 100)
        dollar_exit_fraction += dest_dollar_exit
        dest_breakdown[dest] = {
            'share_pct': share_pct,
            'stays_in_usd_pct': stays_usd_pct,
            'dollar_exit_contribution': dest_dollar_exit,
        }

    # Normalize: destination shares may not sum to 100
    total_share = sum(d['share_pct'] for d in dest_breakdown.values())
    if total_share > 0:
        dollar_exit_fraction = dollar_exit_fraction * (100 / total_share)

    # Net Treasury pressure = flight * dollar-exit fraction
    net_treasury_pressure_B = cumulative_flight_B * dollar_exit_fraction

    return net_treasury_pressure_B, {
        'total_usd_B': total_usd_B,
        'treasury_holdings_B': treasury_holdings_B,
        'annual_flight_pct': annual_flight_pct,
        'hormuz_triggered': hormuz_triggered,
        'cumulative_flight_B': cumulative_flight_B,
        'dollar_exit_fraction': dollar_exit_fraction,
        'net_treasury_pressure_B': net_treasury_pressure_B,
        'destinations': dest_breakdown,
    }


def compute_recycling_disruption(rng, horizon_years=MODEL_HORIZON_YEARS):
    """
    Channel B: Private petrodollar recycling collapses.

    Gulf private sector recycles oil revenue into US assets (Treasuries,
    equities, deposits). Capital flight breaks this loop: wealth leaves
    the region, reducing the pool that would have been recycled.

    This is ADDITIONAL to sovereign de-dollarization (central bank
    decisions). This covers private-sector recycling: corporate treasuries,
    family offices parking oil profits in T-bills, etc.

    Returns: annual Treasury demand reduction in $B, breakdown dict
    """
    private_recycling_B = sample_triangular(rng, CAPITAL_FLIGHT['private_recycling_B_yr'])
    disruption_pct = sample_triangular(rng, CAPITAL_FLIGHT['recycling_disruption_pct'])

    annual_reduction_B = private_recycling_B * (disruption_pct / 100)

    # Cumulate over horizon (this is annual reduced demand, not selling)
    # Each year of reduced demand means that much less buying at auction.
    # The effect is the average annual shortfall, not the sum.
    # (Unlike selling, reduced demand is a flow, not a stock.)

    return annual_reduction_B, {
        'private_recycling_B_yr': private_recycling_B,
        'disruption_pct': disruption_pct,
        'annual_reduction_B': annual_reduction_B,
    }


def compute_capital_flight_impact(rng, elasticity, existing_pressure_bps=0):
    """
    Full regional capital flight channel.

    Combines:
      A. Direct Treasury selling (Gulf private holders liquidate)
      B. Private recycling disruption (reduced demand at auction)

    Args:
        rng: numpy random generator
        elasticity: pre-sampled demand elasticity (shared with other channels)
        existing_pressure_bps: yield pressure from other channels.
            Higher existing pressure accelerates flight (rational hedging).

    Returns:
        yield_bps: total yield pressure from regional capital flight
        info: full breakdown dict
    """
    # Existing pressure from other channels accelerates flight.
    # If yields already rising, Gulf families see the signal and move faster.
    # Model: each 100 bps of existing pressure adds 2pp to annual flight rate.
    # (Modest: rational actors hedge gradually, not in panic.)
    pressure_boost_pp = (existing_pressure_bps / 100) * 2.0

    # Channel A: direct Treasury selling
    direct_selling_B, direct_info = compute_direct_treasury_selling(rng)

    # Apply pressure boost: more flight if yields already stressed
    boosted_selling_B = direct_selling_B * (1 + pressure_boost_pp / 100)

    # Annualize: spread the selling over the horizon for yield computation
    # (Unlike a panic event, regional flight is gradual -- months to years)
    annual_selling_B = boosted_selling_B / MODEL_HORIZON_YEARS

    # Channel B: recycling disruption
    recycling_reduction_B, recycling_info = compute_recycling_disruption(rng)

    # Total annual Treasury pressure
    total_annual_pressure_B = annual_selling_B + recycling_reduction_B

    # Convert to yield bps
    yield_bps = _to_yield_bps(total_annual_pressure_B, elasticity)

    # Overlap correction with sovereign de-dollarization:
    # Gulf sovereign selling (central banks) is already in the de-dollarization module.
    # Private capital flight is different actors (families, corporates, not SWFs).
    # But some SWF selling is guided by the same families who control the SWFs.
    # Correction: reduce by 15-25% to avoid double-counting the SWF/private overlap.
    overlap_correction = rng.triangular(0.15, 0.20, 0.25)
    corrected_bps = yield_bps * (1 - overlap_correction)

    return corrected_bps, {
        'shock_occurred': corrected_bps > 0,  # always true unless zero flight
        'n_shocks': 0,  # not event-driven; continuous flow
        'max_severity': 0,
        'direct_selling_B': boosted_selling_B,
        'annual_selling_B': annual_selling_B,
        'recycling_reduction_B': recycling_reduction_B,
        'total_annual_pressure_B': total_annual_pressure_B,
        'yield_bps_raw': yield_bps,
        'overlap_correction': overlap_correction,
        'yield_bps_corrected': corrected_bps,
        'pressure_boost_pp': pressure_boost_pp,
        'hormuz_triggered': direct_info['hormuz_triggered'],
        'dollar_exit_fraction': direct_info['dollar_exit_fraction'],
        'total_selling_B': boosted_selling_B,  # for monte_carlo.py compatibility
        'fed_intervention': False,  # not event-driven, no Fed intervention modeled
        'direct_info': direct_info,
        'recycling_info': recycling_info,
    }


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== REGIONAL CAPITAL FLIGHT MODULE ===\n")

    # Single draw
    bps, info = compute_capital_flight_impact(rng, elasticity=0.60)
    print("Single draw (no existing pressure):")
    print(f"  Direct selling (cumulative): ${info['direct_selling_B']:.0f}B")
    print(f"  Annualized selling: ${info['annual_selling_B']:.0f}B/yr")
    print(f"  Recycling disruption: ${info['recycling_reduction_B']:.0f}B/yr")
    print(f"  Total annual pressure: ${info['total_annual_pressure_B']:.0f}B/yr")
    print(f"  Dollar exit fraction: {info['dollar_exit_fraction']:.2f}")
    print(f"  Hormuz triggered: {info['hormuz_triggered']}")
    print(f"  Yield pressure (raw): {info['yield_bps_raw']:.1f} bps")
    print(f"  Overlap correction: {info['overlap_correction']:.1%}")
    print(f"  Yield pressure (final): {bps:.1f} bps")

    di = info['direct_info']
    print(f"\n  Source pool:")
    print(f"    Total Gulf private USD: ${di['total_usd_B']:.0f}B")
    print(f"    Treasury holdings: ${di['treasury_holdings_B']:.0f}B")
    print(f"    Annual flight rate: {di['annual_flight_pct']:.1f}%")
    print(f"    Cumulative flight: ${di['cumulative_flight_B']:.0f}B")

    print(f"\n  Destination breakdown:")
    for dest, d in di['destinations'].items():
        print(f"    {dest}: {d['share_pct']:.0f}% of flow, "
              f"{d['stays_in_usd_pct']}% stays USD, "
              f"exit contribution: {d['dollar_exit_contribution']:.3f}")

    print()

    # Monte Carlo (1000 draws)
    print("=== MONTE CARLO (1000 draws) ===\n")

    results_no_pressure = []
    results_with_pressure = []
    hormuz_count = 0

    for _ in range(1000):
        elasticity = rng.triangular(0.25, 0.60, 2.50)

        bps0, info0 = compute_capital_flight_impact(rng, elasticity, existing_pressure_bps=0)
        results_no_pressure.append(bps0)

        bps200, info200 = compute_capital_flight_impact(rng, elasticity, existing_pressure_bps=200)
        results_with_pressure.append(bps200)
        if info200['hormuz_triggered']:
            hormuz_count += 1

    arr0 = np.array(results_no_pressure)
    arr200 = np.array(results_with_pressure)

    print("No existing pressure:")
    print(f"  Median: {np.median(arr0):.1f} bps")
    print(f"  Mean: {np.mean(arr0):.1f} bps")
    print(f"  90% CI: [{np.percentile(arr0, 5):.1f}, {np.percentile(arr0, 95):.1f}]")
    print()

    print("With 200 bps existing pressure:")
    print(f"  Median: {np.median(arr200):.1f} bps")
    print(f"  Mean: {np.mean(arr200):.1f} bps")
    print(f"  90% CI: [{np.percentile(arr200, 5):.1f}, {np.percentile(arr200, 95):.1f}]")
    print(f"  Hormuz threat frequency: {hormuz_count/1000*100:.1f}%")
