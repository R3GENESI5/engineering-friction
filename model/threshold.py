"""
Threshold Module
Derives the yield threshold (headroom to debt spiral) from actual debt service math
instead of assuming it.

The question: at what 10-year yield does annual interest consume X% of federal revenue?
X is drawn from a distribution based on historical sovereign crisis precedents.
"""

import numpy as np
from config import (
    GROSS_DEBT_T, DEBT_HELD_PUBLIC_T, FEDERAL_REVENUE_T,
    CURRENT_AVG_RATE_PCT, ANNUAL_INTEREST_B, MATURITY_BUCKETS,
    CRISIS_RATIO_DISTRIBUTION, sample_triangular
)


def compute_steady_state_interest(new_yield_pct, years_to_roll=5):
    """
    Compute what annual interest payments would be after debt rolls over
    at the new yield.

    The debt doesn't reprice instantly. Only maturing tranches reprice.
    Model the rollover year by year using maturity buckets.

    Args:
        new_yield_pct: the new 10-year Treasury yield
        years_to_roll: how many years to simulate

    Returns:
        dict with yearly interest payments in $B
    """
    debt_B = DEBT_HELD_PUBLIC_T * 1000  # convert to $B

    # Split debt into buckets
    buckets = {
        '0-1yr': debt_B * MATURITY_BUCKETS['0-1yr'],
        '1-5yr': debt_B * MATURITY_BUCKETS['1-5yr'],
        '5-10yr': debt_B * MATURITY_BUCKETS['5-10yr'],
        '10+yr': debt_B * MATURITY_BUCKETS['10+yr'],
    }

    old_rate = CURRENT_AVG_RATE_PCT / 100
    new_rate = new_yield_pct / 100

    results = {}

    # Track how much debt has repriced each year
    repriced_B = 0
    not_repriced_B = debt_B

    for year in range(1, years_to_roll + 1):
        # In year 1: 0-1yr bucket reprices
        # In years 2-5: 1-5yr bucket reprices (~9.25% per year)
        # In years 6-10: 5-10yr bucket reprices (~3.6% per year)
        # 10+yr: stays at old rate for this horizon

        if year == 1:
            new_repriced = buckets['0-1yr']
        elif year <= 5:
            new_repriced = buckets['1-5yr'] / 4  # spread evenly over years 2-5
        elif year <= 10:
            new_repriced = buckets['5-10yr'] / 5  # spread evenly over years 6-10
        else:
            new_repriced = 0

        repriced_B += new_repriced
        not_repriced_B -= new_repriced

        # Interest = repriced portion at new rate + remainder at old rate
        interest_B = (repriced_B * new_rate) + (not_repriced_B * old_rate)
        interest_to_revenue = interest_B / (FEDERAL_REVENUE_T * 1000)

        results[year] = {
            'interest_B': interest_B,
            'interest_to_revenue': interest_to_revenue,
            'pct_repriced': repriced_B / debt_B * 100,
        }

    return results


def find_crisis_yield(crisis_ratio, year_horizon=3):
    """
    Find the 10-year yield at which interest-to-revenue hits the crisis ratio,
    given that debt rolls over at the new yield over the specified horizon.

    Uses binary search.

    Args:
        crisis_ratio: the interest-to-revenue ratio that triggers crisis (e.g., 0.33)
        year_horizon: how many years of rollover to consider (default 3)

    Returns:
        crisis_yield_pct: the yield (%) that triggers the crisis ratio
    """
    lo, hi = CURRENT_AVG_RATE_PCT, 15.0  # search between current rate and 15%

    for _ in range(100):  # binary search iterations
        mid = (lo + hi) / 2
        results = compute_steady_state_interest(mid, years_to_roll=year_horizon)
        ratio_at_horizon = results[year_horizon]['interest_to_revenue']

        if ratio_at_horizon < crisis_ratio:
            lo = mid
        else:
            hi = mid

        if abs(hi - lo) < 0.001:
            break

    return (lo + hi) / 2


def compute_headroom(crisis_ratio, year_horizon=3):
    """
    Compute headroom in basis points from current yield to crisis yield.

    Args:
        crisis_ratio: drawn from CRISIS_RATIO_DISTRIBUTION
        year_horizon: rollover horizon

    Returns:
        headroom_bps: basis points of headroom
        crisis_yield: the yield at which crisis ratio is hit
    """
    crisis_yield = find_crisis_yield(crisis_ratio, year_horizon)
    headroom_bps = (crisis_yield - GS10_CURRENT) * 100
    return headroom_bps, crisis_yield


# Import here to avoid circular (GS10_CURRENT is in config but also used in regression)
from config import sample_triangular

GS10_CURRENT = 4.3  # repeated for clarity


def sample_headroom(rng, year_horizon=3):
    """
    Sample headroom from the crisis ratio distribution.

    Returns:
        headroom_bps, crisis_yield, crisis_ratio
    """
    crisis_ratio = sample_triangular(rng, CRISIS_RATIO_DISTRIBUTION)
    headroom_bps, crisis_yield = compute_headroom(crisis_ratio, year_horizon)
    return headroom_bps, crisis_yield, crisis_ratio


if __name__ == '__main__':
    # Quick test
    rng = np.random.default_rng(42)

    print("=== THRESHOLD DERIVATION ===")
    print(f"Current avg rate: {CURRENT_AVG_RATE_PCT}%")
    print(f"Current 10yr yield: {GS10_CURRENT}%")
    print(f"Annual interest: ${ANNUAL_INTEREST_B}B")
    print(f"Revenue: ${FEDERAL_REVENUE_T}T")
    print(f"Current interest/revenue: {ANNUAL_INTEREST_B / (FEDERAL_REVENUE_T * 1000) * 100:.1f}%")
    print()

    # Show rollover at various yields
    for test_yield in [4.5, 5.0, 5.5, 6.0, 6.5, 7.0]:
        results = compute_steady_state_interest(test_yield, years_to_roll=5)
        print(f"At {test_yield}% yield:")
        for yr, r in results.items():
            print(f"  Year {yr}: interest ${r['interest_B']:.0f}B, "
                  f"int/rev {r['interest_to_revenue']*100:.1f}%, "
                  f"repriced {r['pct_repriced']:.0f}%")
        print()

    # Show headroom at different crisis thresholds
    print("=== HEADROOM ===")
    for ratio in [0.28, 0.33, 0.38, 0.42]:
        h, cy = compute_headroom(ratio, year_horizon=3)
        print(f"Crisis at {ratio*100:.0f}% int/rev: yield {cy:.2f}%, headroom {h:.0f} bps")

    print()
    print("=== MONTE CARLO SAMPLE (20 draws) ===")
    for _ in range(20):
        h, cy, cr = sample_headroom(rng)
        print(f"  ratio={cr:.2f}, crisis_yield={cy:.2f}%, headroom={h:.0f} bps")
