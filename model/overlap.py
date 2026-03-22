"""
Overlap Correction Module
Joint estimation of Treasury demand impact, avoiding double-counting
between sovereign selling and balance-of-payments pressure.
"""

import numpy as np
from config import GEOGRAPHIES, OVERLAP_MARGINAL_FRACTION, sample_triangular


def correct_overlap(sovereign_selling_bps, bop_bps_by_geo, rng):
    """
    Correct for overlap between sovereign selling (Clock 2) and
    balance-of-payments withdrawal pressure (Multi-Country).

    Method: for each geography that contributes to both channels,
    take the larger contribution and add only a fraction of the smaller.

    Args:
        sovereign_selling_bps: dict of {geo: bps} from Clock 2 sovereign selling
        bop_bps_by_geo: dict of {geo: bps} from BoP withdrawal channel
        rng: numpy random generator

    Returns:
        corrected_total_bps, breakdown dict
    """
    marginal_frac = sample_triangular(rng, OVERLAP_MARGINAL_FRACTION)

    total_bps = 0
    breakdown = {}

    # Geographies that appear in both channels
    all_geos = set(list(sovereign_selling_bps.keys()) + list(bop_bps_by_geo.keys()))

    for geo in all_geos:
        sov = sovereign_selling_bps.get(geo, 0)
        bop = bop_bps_by_geo.get(geo, 0)

        if sov > 0 and bop > 0:
            # Both channels active: take max + marginal fraction of min
            larger = max(sov, bop)
            smaller = min(sov, bop)
            corrected = larger + smaller * marginal_frac
            breakdown[geo] = {
                'sovereign': sov,
                'bop': bop,
                'corrected': corrected,
                'overlap_removed': (sov + bop) - corrected,
                'method': 'max_plus_marginal',
            }
        else:
            # Only one channel: no overlap
            corrected = sov + bop
            breakdown[geo] = {
                'sovereign': sov,
                'bop': bop,
                'corrected': corrected,
                'overlap_removed': 0,
                'method': 'single_channel',
            }

        total_bps += corrected

    return total_bps, breakdown, marginal_frac


# Default sovereign selling estimates (from Clock 2 data)
# Source: China $86B, BRICS combined $194B in year to Nov 2025
# Convert to bps: selling / outstanding debt * 10000
def estimate_sovereign_selling_bps():
    """
    Estimate sovereign selling yield impact by geography.
    Based on observed selling rates.
    """
    debt_outstanding_B = 29600  # $29.6T

    # Known selling (annual rate)
    selling = {
        'China': 86,        # $86B/yr
        'India': 15,        # estimated
        'Europe': 30,       # estimated (diversification)
        'Gulf States': 20,  # estimated
        'Sub-Saharan Africa': 2,
        'Pakistan': 1,
    }

    bps = {}
    for geo, sell_B in selling.items():
        bps[geo] = (sell_B / debt_outstanding_B) * 10000

    return bps, selling


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    sov_bps, sov_B = estimate_sovereign_selling_bps()
    print("=== SOVEREIGN SELLING (Clock 2) ===")
    total_sov = 0
    for geo, bps in sov_bps.items():
        print(f"  {geo}: ${sov_B[geo]}B/yr = {bps:.1f} bps")
        total_sov += bps
    print(f"  TOTAL sovereign selling: {total_sov:.1f} bps")
    print()

    # Mock BoP data for testing
    bop_mock = {
        'Pakistan': 0.9,
        'India': 3.6,
        'Sub-Saharan Africa': 1.0,
        'China': 6.1,
        'Europe': 12.7,
        'Gulf States': 2.5,
    }

    corrected, breakdown, mf = correct_overlap(sov_bps, bop_mock, rng)
    print(f"=== OVERLAP CORRECTION (marginal fraction: {mf:.2f}) ===")
    total_raw = sum(sov_bps.values()) + sum(bop_mock.values())
    for geo, b in breakdown.items():
        print(f"  {geo}: sov={b['sovereign']:.1f} + bop={b['bop']:.1f} "
              f"-> corrected={b['corrected']:.1f} (removed {b['overlap_removed']:.1f}) [{b['method']}]")
    print(f"  RAW TOTAL: {total_raw:.1f} bps")
    print(f"  CORRECTED TOTAL: {corrected:.1f} bps")
    print(f"  OVERLAP REMOVED: {total_raw - corrected:.1f} bps")
