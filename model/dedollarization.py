"""
De-dollarization Module
Models the yield pressure from state-level dollar abandonment.

Five channels:
1. Oil settlement shift (petrodollar erosion)
2. FX reserve diversification (central banks leaving USD)
3. BRICS bilateral trade settlement (bypassing dollar)
4. Consumer boycott (direct demand destruction)
5. Accelerated Treasury dumping (geopolitical retaliation)

The war is meant to prevent de-dollarization. The model asks:
what if the war accelerates it instead?
"""

import numpy as np
from config import DEBT_HELD_PUBLIC_T, DEMAND_ELASTICITY, sample_triangular


# ============================================================
# CHANNEL 1: OIL SETTLEMENT SHIFT
# ============================================================
# Global oil trade: ~$6.3T/year (2025, Yahoo Finance / Precedence Research)
# Currently 80% in USD (OilPrice.com, 2023)
# 20% already non-USD and rising
#
# Key shifts:
# - China-Saudi swap: $7B capacity, Saudi joined mBridge
# - India-Russia: $53B in non-dollar (rupee, ruble, yuan)
# - China-Russia: 99.1% in local currencies
# - Iran oil sales: entirely non-dollar (sanctions)

OIL_PARAMS = {
    'global_oil_trade_B_yr': 6300,
    'current_usd_share_pct': 80,
    # Scenario: USD share drops over time
    # Conservative: 80 -> 70 (10pp shift) over 5-8 years
    # Central: 80 -> 60 (20pp shift) over 5-8 years
    # Aggressive: 80 -> 45 (35pp shift) over 5-8 years
    'usd_share_decline_pp': {
        'min': 8,       # conservative
        'mode': 18,     # central
        'max': 32,      # aggressive (if Saudi fully pivots)
    },
    # What fraction of reduced dollar oil demand translates to Treasury pressure?
    # Petrodollar recycling: oil exporters hold ~$300B+ in Treasuries (Gulf states)
    # Reduced dollar revenue = reduced Treasury purchases
    'recycling_fraction': {
        'min': 0.15,    # loose coupling
        'mode': 0.30,   # moderate
        'max': 0.50,    # tight coupling (classic petrodollar recycling)
    },
}


def _to_yield_bps(treasury_pressure_B, elasticity):
    """Convert Treasury pressure to yield bps using demand elasticity."""
    debt_B = DEBT_HELD_PUBLIC_T * 1000
    raw_bps = (treasury_pressure_B / debt_B) * 10000
    return raw_bps * elasticity


def compute_oil_channel(rng, elasticity=1.0):
    """
    Compute yield pressure from petrodollar erosion.

    Transmission: less oil trade in USD -> less dollar demand ->
    less petrodollar recycling into Treasuries -> yield pressure.
    """
    decline_pp = sample_triangular(rng, OIL_PARAMS['usd_share_decline_pp'])
    recycling_frac = sample_triangular(rng, OIL_PARAMS['recycling_fraction'])

    dollar_oil_reduction_B = OIL_PARAMS['global_oil_trade_B_yr'] * (decline_pp / 100)
    treasury_pressure_B = dollar_oil_reduction_B * recycling_frac

    yield_bps = _to_yield_bps(treasury_pressure_B, elasticity)

    return yield_bps, {
        'decline_pp': decline_pp,
        'dollar_oil_reduction_B': dollar_oil_reduction_B,
        'treasury_pressure_B': treasury_pressure_B,
    }


# ============================================================
# CHANNEL 2: FX RESERVE DIVERSIFICATION
# ============================================================
# USD share of global reserves: 72% (2014) -> 57.8% (2024)
# That's 14.2pp over 10 years = ~1.4pp/year
# Global FX reserves: ~$12.3T (IMF, 2024)
# Shift: $12.3T * 14.2% = $1.75T moved out of USD over 10 years
#
# Central bank gold purchases: 1000+ tonnes/year (2022-2024)
# At ~$2500/oz, that's ~$80B/year in gold replacing dollar assets
#
# This channel is ALREADY in motion. The war accelerates it.

RESERVE_PARAMS = {
    'global_reserves_T': 12.3,
    'current_usd_share_pct': 57.8,
    # Additional decline over model horizon (5-10 years)
    'additional_decline_pp': {
        'min': 5,       # business as usual (0.5pp/yr)
        'mode': 10,     # acceleration (war effect, BRICS growth)
        'max': 18,      # aggressive (if USD loses reserve currency premium)
    },
    # Fraction that translates to Treasury selling vs other USD assets
    'treasury_fraction': {
        'min': 0.40,
        'mode': 0.55,
        'max': 0.70,
    },
}


def compute_reserve_channel(rng, elasticity=1.0):
    """
    Compute yield pressure from FX reserve diversification.
    """
    decline_pp = sample_triangular(rng, RESERVE_PARAMS['additional_decline_pp'])
    treasury_frac = sample_triangular(rng, RESERVE_PARAMS['treasury_fraction'])

    reserves_B = RESERVE_PARAMS['global_reserves_T'] * 1000
    usd_reduction_B = reserves_B * (decline_pp / 100)
    treasury_reduction_B = usd_reduction_B * treasury_frac

    annual_treasury_reduction_B = treasury_reduction_B / 7

    yield_bps = _to_yield_bps(annual_treasury_reduction_B, elasticity)

    return yield_bps, {
        'decline_pp': decline_pp,
        'usd_reduction_B': usd_reduction_B,
        'annual_treasury_reduction_B': annual_treasury_reduction_B,
    }


# ============================================================
# CHANNEL 3: BRICS TRADE SETTLEMENT
# ============================================================
# Intra-BRICS trade: ~$1.5T/year (estimate)
# Currently 40-50% in local currencies, up from ~15% in 2018
# mBridge: 5 central banks, 31 observers, MVP stage
# BRICS pay system: in development
#
# The shift here is INCREMENTAL dollar demand destruction from trade settlement

BRICS_PARAMS = {
    'intra_brics_trade_B_yr': 1500,
    'current_local_currency_pct': 45,
    # Additional shift to local currencies
    'additional_local_shift_pp': {
        'min': 10,
        'mode': 25,
        'max': 40,
    },
    # Non-BRICS adoption: other countries join local currency settlement
    # BRICS+: now includes Egypt, Ethiopia, Iran, UAE, Saudi Arabia
    'spillover_multiplier': {
        'min': 1.2,     # modest spillover
        'mode': 1.8,    # moderate
        'max': 2.5,     # if BRICS pay succeeds broadly
    },
    # Dollar demand reduction to Treasury pressure
    'transmission_fraction': {
        'min': 0.10,
        'mode': 0.20,
        'max': 0.35,
    },
}


def compute_brics_channel(rng, elasticity=1.0):
    """
    Compute yield pressure from BRICS trade de-dollarization.
    """
    shift_pp = sample_triangular(rng, BRICS_PARAMS['additional_local_shift_pp'])
    spillover = sample_triangular(rng, BRICS_PARAMS['spillover_multiplier'])
    transmission = sample_triangular(rng, BRICS_PARAMS['transmission_fraction'])

    dollar_reduction_B = BRICS_PARAMS['intra_brics_trade_B_yr'] * (shift_pp / 100)
    total_dollar_reduction_B = dollar_reduction_B * spillover

    treasury_pressure_B = total_dollar_reduction_B * transmission

    yield_bps = _to_yield_bps(treasury_pressure_B, elasticity)

    return yield_bps, {
        'shift_pp': shift_pp,
        'spillover': spillover,
        'dollar_reduction_B': total_dollar_reduction_B,
        'treasury_pressure_B': treasury_pressure_B,
    }


# ============================================================
# CHANNEL 4: CONSUMER BOYCOTT
# ============================================================
# Data: 70% of Malaysian consumers, 69% Indonesian boycotting US brands
# McDonald's: missed revenue targets across Middle East
# Starbucks Malaysia: 36% sales decline
# Coca-Cola Turkey: 22% sales fall
#
# This is small relative to state-level channels but has signaling value

BOYCOTT_PARAMS = {
    # Estimated annual US brand revenue loss in boycotting countries
    'annual_revenue_loss_B': {
        'min': 5,
        'mode': 15,
        'max': 40,
    },
    # Revenue loss to dollar demand: boycotted spending shifts to local brands
    # Local brands don't import as much from US, reducing dollar demand
    'dollar_demand_fraction': {
        'min': 0.20,
        'mode': 0.35,
        'max': 0.50,
    },
}


def compute_boycott_channel(rng, elasticity=1.0):
    """
    Compute yield pressure from consumer boycotts.
    Small but additive.
    """
    revenue_loss_B = sample_triangular(rng, BOYCOTT_PARAMS['annual_revenue_loss_B'])
    dollar_frac = sample_triangular(rng, BOYCOTT_PARAMS['dollar_demand_fraction'])

    dollar_reduction_B = revenue_loss_B * dollar_frac
    yield_bps = _to_yield_bps(dollar_reduction_B, elasticity)

    return yield_bps, {
        'revenue_loss_B': revenue_loss_B,
        'dollar_reduction_B': dollar_reduction_B,
    }


# ============================================================
# CHANNEL 5: ACCELERATED TREASURY DUMPING
# ============================================================
# Current baseline: BRICS selling $194B/year (already in main model)
# This channel models ACCELERATION beyond baseline
# Triggers: geopolitical escalation, sanctions expansion, war widening
#
# China holds $760B (down from $1.1T). Could accelerate.
# Japan holds $1.1T. Not adversarial but diversifying.
# If war escalates to sanctions on more countries, forced selling increases.

DUMPING_PARAMS = {
    # Additional Treasury selling beyond current $194B/yr baseline
    # This is the WAR ACCELERATION premium
    'additional_selling_B_yr': {
        'min': 30,      # modest acceleration
        'mode': 100,    # significant (China doubles rate + others follow)
        'max': 250,     # severe (coordinated BRICS dump or sanctions cascade)
    },
}


def compute_dumping_channel(rng, elasticity=1.0):
    """
    Compute yield pressure from accelerated Treasury selling
    beyond the baseline already in the model.
    """
    additional_B = sample_triangular(rng, DUMPING_PARAMS['additional_selling_B_yr'])

    yield_bps = _to_yield_bps(additional_B, elasticity)

    return yield_bps, {
        'additional_selling_B': additional_B,
    }


# ============================================================
# COMBINED DE-DOLLARIZATION IMPACT
# ============================================================

def compute_all_dedollarization(rng, credibility_multiplier=1.0, elasticity=None):
    """
    Compute total yield pressure from all de-dollarization channels.

    Args:
        rng: numpy random generator
        credibility_multiplier: from Clock 1 Channel B (accelerates adoption rates)
        elasticity: pre-sampled demand elasticity. If None, samples here.

    Returns:
        total_bps, channel_breakdown dict
    """
    # Sample elasticity once for this iteration if not provided
    if elasticity is None:
        elasticity = sample_triangular(rng, DEMAND_ELASTICITY)

    # Apply credibility multiplier to adoption-rate channels (oil, BRICS)
    # This represents: China's demonstrated supply chain control makes
    # switching away from dollar more credible, so adoption rates accelerate.
    # We apply it by scaling the shift parameters before computing.
    # For simplicity, we scale the output bps (mathematically equivalent
    # for linear channels).
    oil_bps, oil_info = compute_oil_channel(rng, elasticity)
    oil_bps *= credibility_multiplier

    reserve_bps, reserve_info = compute_reserve_channel(rng, elasticity)
    # Reserve channel not multiplied: central bank decisions less affected by credibility signal

    brics_bps, brics_info = compute_brics_channel(rng, elasticity)
    brics_bps *= credibility_multiplier

    boycott_bps, boycott_info = compute_boycott_channel(rng, elasticity)
    boycott_bps *= credibility_multiplier

    dumping_bps, dumping_info = compute_dumping_channel(rng, elasticity)
    dumping_bps *= credibility_multiplier

    # Overlap correction
    oil_reserve_overlap = min(oil_bps, reserve_bps) * 0.30
    corrected_total = (oil_bps + reserve_bps + brics_bps + boycott_bps + dumping_bps
                      - oil_reserve_overlap)

    return corrected_total, {
        'oil_bps': oil_bps,
        'oil_info': oil_info,
        'reserve_bps': reserve_bps,
        'reserve_info': reserve_info,
        'brics_bps': brics_bps,
        'brics_info': brics_info,
        'boycott_bps': boycott_bps,
        'boycott_info': boycott_info,
        'dumping_bps': dumping_bps,
        'dumping_info': dumping_info,
        'oil_reserve_overlap_bps': oil_reserve_overlap,
        'corrected_total_bps': corrected_total,
        'credibility_multiplier': credibility_multiplier,
        'demand_elasticity': elasticity,
    }


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== DE-DOLLARIZATION CHANNELS ===\n")

    # Single draw
    total, breakdown = compute_all_dedollarization(rng)

    channels = [
        ('Oil settlement shift', 'oil_bps', 'oil_info'),
        ('FX reserve diversification', 'reserve_bps', 'reserve_info'),
        ('BRICS trade settlement', 'brics_bps', 'brics_info'),
        ('Consumer boycott', 'boycott_bps', 'boycott_info'),
        ('Accelerated Treasury dumping', 'dumping_bps', 'dumping_info'),
    ]

    for name, bps_key, info_key in channels:
        bps = breakdown[bps_key]
        info = breakdown[info_key]
        print(f"{name}: {bps:.1f} bps")
        for k, v in info.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.1f}")
            else:
                print(f"  {k}: {v}")
        print()

    print(f"Oil-reserve overlap removed: {breakdown['oil_reserve_overlap_bps']:.1f} bps")
    print(f"CORRECTED TOTAL: {total:.1f} bps")
    print()

    # Monte Carlo (1000 quick draws)
    print("=== MONTE CARLO (1000 draws) ===\n")
    totals = []
    channel_totals = {c[0]: [] for c in channels}

    for _ in range(1000):
        t, b = compute_all_dedollarization(rng)
        totals.append(t)
        for name, bps_key, _ in channels:
            channel_totals[name].append(b[bps_key])

    arr = np.array(totals)
    print(f"Total de-dollarization pressure:")
    print(f"  Median: {np.median(arr):.1f} bps")
    print(f"  Mean: {np.mean(arr):.1f} bps")
    print(f"  90% CI: [{np.percentile(arr, 5):.1f}, {np.percentile(arr, 95):.1f}]")
    print()

    for name in channel_totals:
        a = np.array(channel_totals[name])
        print(f"  {name}: median {np.median(a):.1f} bps, "
              f"90% CI [{np.percentile(a, 5):.1f}, {np.percentile(a, 95):.1f}]")
