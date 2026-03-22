"""
Withdrawal Module
Per-geography withdrawal impact with survival rates and policy friction.
"""

import numpy as np
from config import GEOGRAPHIES, DEBT_HELD_PUBLIC_T, DEMAND_ELASTICITY, sample_triangular


def compute_withdrawal_impact(geo_name, geo, withdrawal_pct, survival_rate, policy_friction, rng):
    """
    Compute the yield impact of withdrawal for a single geography.

    Args:
        geo_name: geography name
        geo: geography dict from config
        withdrawal_pct: additional withdrawal as fraction (e.g., 0.10 for 10%)
        survival_rate: 5-year survival rate of withdrawal units (0-1)
        policy_friction: fraction of signal absorbed by government policy (0-1)
        rng: numpy random generator

    Returns:
        dict with impact breakdown
    """
    pop_M = geo['population_M']
    effective_withdrawal_M = pop_M * withdrawal_pct * survival_rate * (1 - policy_friction)

    result = {
        'geo': geo_name,
        'raw_withdrawal_M': pop_M * withdrawal_pct,
        'effective_withdrawal_M': effective_withdrawal_M,
        'survival_rate': survival_rate,
        'policy_friction': policy_friction,
    }

    if geo_name == 'USA':
        # US pathway: GDP drag + velocity channel
        hh_withdrawal_M = geo['total_households_M'] * withdrawal_pct * survival_rate * (1 - policy_friction)
        ledger_withdrawal_per_hh = geo['avg_reducible_spend_usd'] * (geo['self_sufficiency_capture_pct'] / 100)
        total_withdrawal_B = hh_withdrawal_M * ledger_withdrawal_per_hh / 1000  # convert to $B
        gdp_drag_pct = total_withdrawal_B / (geo['gdp_T'] * 1000) * 100

        # Velocity decline: proportional to GDP drag
        # M2V = GDP / M2. If GDP drops by X%, velocity drops by ~X% (M2 stays same)
        velocity_decline_pct = gdp_drag_pct

        # Tax revenue loss
        tax_loss_B = hh_withdrawal_M * geo['tax_loss_per_hh_usd'] / 1000

        result.update({
            'channel': 'gdp_velocity',
            'hh_withdrawal_M': hh_withdrawal_M,
            'ledger_withdrawal_B': total_withdrawal_B,
            'gdp_drag_pct': gdp_drag_pct,
            'velocity_decline_pct': velocity_decline_pct,
            'tax_loss_B': tax_loss_B,
            # Yield impact computed later using regime-specific coefficient
            'dollar_import_reduction_B': 0,
            'treasury_demand_pressure_B': 0,
        })
    else:
        # International pathway: dollar import demand + Treasury holdings
        # Effective population that stops importing
        effective_frac = effective_withdrawal_M / pop_M

        dollar_import_reduction_B = geo['dollar_imports_B_yr'] * effective_frac * 0.5
        # 0.5 factor: not all imports are dollar-denominated, and withdrawal
        # reduces imports partially, not fully

        # Treasury demand pressure: reduced holdings as import needs drop
        treasury_pressure_B = geo['treasury_holdings_B'] * effective_frac * 0.3
        # 0.3 factor: only partial holdings reduction per unit of import reduction

        result.update({
            'channel': 'bop',
            'dollar_import_reduction_B': dollar_import_reduction_B,
            'treasury_demand_pressure_B': treasury_pressure_B,
            'gdp_drag_pct': 0,
            'velocity_decline_pct': 0,
            'tax_loss_B': 0,
        })

    return result


def compute_all_withdrawals(withdrawal_pct, rng):
    """
    Compute withdrawal impacts across all geographies with sampled parameters.

    Args:
        withdrawal_pct: additional withdrawal fraction (same for all geos)
        rng: numpy random generator

    Returns:
        list of impact dicts, one per geography
    """
    results = []
    for name, geo in GEOGRAPHIES.items():
        survival = sample_triangular(rng, geo['survival_5yr'])
        friction = sample_triangular(rng, geo['policy_friction'])

        impact = compute_withdrawal_impact(name, geo, withdrawal_pct, survival, friction, rng)
        results.append(impact)

    return results


def aggregate_bop_impact(results):
    """
    Aggregate balance-of-payments impacts across all geographies.

    Returns:
        total_dollar_import_reduction_B, total_treasury_pressure_B
    """
    total_import = sum(r['dollar_import_reduction_B'] for r in results)
    total_treasury = sum(r['treasury_demand_pressure_B'] for r in results)
    return total_import, total_treasury


def bop_to_yield_bps(treasury_pressure_B, rng=None, elasticity=None):
    """
    Convert Treasury demand pressure to yield impact.
    Now uses demand elasticity parameter (Fix 1).

    Args:
        treasury_pressure_B: total Treasury demand pressure in $B
        rng: numpy random generator (if None, uses elasticity=1.0 for backward compat)
        elasticity: pre-sampled elasticity (overrides rng sampling)

    Returns:
        yield_impact_bps
    """
    debt_outstanding_B = DEBT_HELD_PUBLIC_T * 1000
    raw_bps = (treasury_pressure_B / debt_outstanding_B) * 10000

    if elasticity is not None:
        return raw_bps * elasticity
    elif rng is not None:
        e = sample_triangular(rng, DEMAND_ELASTICITY)
        return raw_bps * e
    else:
        return raw_bps  # backward compatible: no elasticity applied


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== WITHDRAWAL IMPACTS (10% additional, single draw) ===\n")
    results = compute_all_withdrawals(0.10, rng)

    for r in results:
        print(f"{r['geo']}:")
        print(f"  Raw withdrawal: {r['raw_withdrawal_M']:.1f}M people")
        print(f"  Effective (after survival + friction): {r['effective_withdrawal_M']:.1f}M")
        print(f"  Survival rate: {r['survival_rate']:.2f}")
        print(f"  Policy friction: {r['policy_friction']:.2f}")
        if r['channel'] == 'gdp_velocity':
            print(f"  Channel: GDP/velocity")
            print(f"  Households withdrawing: {r['hh_withdrawal_M']:.2f}M")
            print(f"  GDP drag: {r['gdp_drag_pct']:.3f}%")
            print(f"  Velocity decline: {r['velocity_decline_pct']:.3f}%")
        else:
            print(f"  Channel: Balance-of-payments")
            print(f"  Dollar import reduction: ${r['dollar_import_reduction_B']:.1f}B")
            print(f"  Treasury demand pressure: ${r['treasury_demand_pressure_B']:.1f}B")
        print()

    total_import, total_treasury = aggregate_bop_impact(results)
    bop_bps = bop_to_yield_bps(total_treasury)
    print(f"AGGREGATE BoP:")
    print(f"  Total dollar import reduction: ${total_import:.1f}B")
    print(f"  Total Treasury demand pressure: ${total_treasury:.1f}B")
    print(f"  Yield impact (BoP channel): {bop_bps:.1f} bps")
