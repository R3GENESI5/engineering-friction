"""
Monte Carlo Integration Module - V3
Incorporates all audit fixes:
  Fix 1: Demand elasticity (sampled once per iteration, shared across channels)
  Fix 2: Clock 1 rebuilt as silver strategic scissors (3 channels + credibility multiplier)
  Fix 3: Time dimension (year-by-year pressure accumulation vs threshold)
  Fix 4: US policy defensive response damping
  Fix 5: Geography-specific withdrawal rates (from config)
  Fix 6: Consolidated overlap (single pass)
  Fix 7: Deficit growth, debt issuance growth
"""

import numpy as np
from config import (
    N_ITERATIONS, RNG_SEED, MODEL_HORIZON_YEARS,
    DEMAND_ELASTICITY, ANNUAL_DEFICIT_GROWTH_T, POLICY_RESPONSE,
    GEOGRAPHIES, DEBT_HELD_PUBLIC_T, FEDERAL_REVENUE_T,
    sample_triangular
)
from threshold import sample_headroom, compute_steady_state_interest
from regression import run_regime_regressions, velocity_to_yield_bps
from withdrawal import compute_all_withdrawals, aggregate_bop_impact, bop_to_yield_bps
from overlap import correct_overlap, estimate_sovereign_selling_bps
from clock1 import compute_clock1_impact
from ycc_loop import run_ycc_simulation
from dedollarization import compute_all_dedollarization
from capital_flight import compute_capital_flight_impact
from domestic_institutional import compute_domestic_institutional_impact
from fiscal_dominance import compute_fiscal_dominance_effect
from energy_feedback import compute_energy_feedback_impact
from israel_pipeline import compute_israel_pipeline_impact


def apply_policy_response(pressure_bps, headroom_bps, rng):
    """
    Fix 4: Model US defensive response when pressure exceeds trigger level.

    When pressure/headroom exceeds trigger_pct, there's a probability
    of policy response (rate cuts, bilateral deals, sanctions, fiscal adjustment)
    that reduces effective pressure.

    Returns:
        damped_pressure_bps, damping_applied_bps, response_triggered
    """
    if headroom_bps <= 0:
        return pressure_bps, 0, False

    consumed_pct = (pressure_bps / headroom_bps) * 100
    trigger = POLICY_RESPONSE['trigger_pct']

    if consumed_pct < trigger:
        return pressure_bps, 0, False

    # Roll for response probability
    response_prob = sample_triangular(rng, POLICY_RESPONSE['response_probability'])
    if rng.random() > response_prob:
        return pressure_bps, 0, False  # policy paralysis

    # Response materializes: dampen pressure
    damping_pct = sample_triangular(rng, POLICY_RESPONSE['damping_pct'])
    damping_bps = pressure_bps * (damping_pct / 100)
    damped = pressure_bps - damping_bps

    return damped, damping_bps, True


def compute_debt_growth_headroom_shift(rng, year):
    """
    Fix 7: Growing debt changes both the denominator (more outstanding)
    and the numerator (more interest burden). Net effect on headroom.

    Returns:
        headroom_adjustment_bps: positive = more headroom, negative = less
    """
    annual_growth_T = sample_triangular(rng, ANNUAL_DEFICIT_GROWTH_T)
    cumulative_new_debt_T = annual_growth_T * year

    # New debt issued at current market rates (higher than avg coupon)
    # This REDUCES headroom by adding to interest burden faster than revenue grows
    # Net effect: each $1T of new debt at 4.3% adds ~$43B interest/yr
    # Against $5.1T revenue, that's 0.84pp on the interest/revenue ratio
    # Which reduces headroom by roughly 25-30 bps per $1T of new debt
    headroom_reduction_per_T = 20  # bps, calibrated: $10T growth -> ~196 bps consumed
    headroom_adjustment_bps = -cumulative_new_debt_T * headroom_reduction_per_T

    return headroom_adjustment_bps


def run_single_iteration(rng, regression_results,
                         clock1_progress=50, run_ycc=False, ycc_years=10):
    """
    Run one complete iteration of the v3 model.

    Key changes from v2:
    - Demand elasticity sampled once, shared across all channels
    - Geography-specific withdrawal rates
    - Clock 1 returns yield pressure + credibility multiplier
    - Policy response damping
    - Debt growth adjustment to headroom
    """
    # 0. Sample demand elasticity ONCE for this iteration
    #    (represents market conditions: panic vs orderly)
    elasticity = sample_triangular(rng, DEMAND_ELASTICITY)

    # 1. Sample headroom
    headroom_bps, crisis_yield, crisis_ratio = sample_headroom(rng)

    # 1b. Adjust headroom for debt growth over model horizon (Fix 7)
    debt_growth_adj = compute_debt_growth_headroom_shift(rng, MODEL_HORIZON_YEARS)
    adjusted_headroom_bps = headroom_bps + debt_growth_adj  # debt_growth_adj is negative

    # 2. Compute withdrawal impacts with geography-specific rates (Fix 5)
    withdrawal_results = []
    for name, geo in GEOGRAPHIES.items():
        geo_withdrawal_pct = sample_triangular(rng, geo['withdrawal_pct'])
        survival = sample_triangular(rng, geo['survival_5yr'])
        friction = sample_triangular(rng, geo['policy_friction'])
        from withdrawal import compute_withdrawal_impact
        impact = compute_withdrawal_impact(name, geo, geo_withdrawal_pct, survival, friction, rng)
        withdrawal_results.append(impact)

    # 3. US velocity channel
    us_result = [r for r in withdrawal_results if r['geo'] == 'USA'][0]
    velocity_decline = us_result['velocity_decline_pct']
    velocity_bps = velocity_to_yield_bps(velocity_decline, rng, regression_results)

    # 4. Balance-of-payments channel (with elasticity)
    total_import_reduction, total_treasury_pressure = aggregate_bop_impact(withdrawal_results)
    raw_bop_bps = bop_to_yield_bps(total_treasury_pressure, elasticity=elasticity)

    # 5. Sovereign selling (Clock 2) - also apply elasticity
    sov_bps, sov_B = estimate_sovereign_selling_bps()
    # Scale sovereign bps by elasticity (they were computed with linear assumption)
    sov_bps_scaled = {k: v * elasticity for k, v in sov_bps.items()}

    # 6. Overlap correction
    bop_by_geo = {}
    for r in withdrawal_results:
        if r['channel'] == 'bop':
            geo_bps = bop_to_yield_bps(r['treasury_demand_pressure_B'], elasticity=elasticity)
            if geo_bps > 0:
                bop_by_geo[r['geo']] = geo_bps

    corrected_bps, overlap_breakdown, marginal_frac = correct_overlap(sov_bps_scaled, bop_by_geo, rng)

    # 7. Clock 1: Silver strategic scissors (Fix 2)
    clock1_bps, credibility_mult, clock1_info = compute_clock1_impact(
        clock1_progress, rng, model_horizon_years=MODEL_HORIZON_YEARS
    )

    # 8. De-dollarization channels (with elasticity + credibility multiplier)
    dedollar_bps, dedollar_info = compute_all_dedollarization(
        rng,
        credibility_multiplier=credibility_mult,
        elasticity=elasticity
    )

    # 9. Dedollar-sovereign overlap correction
    sov_total_bps = sum(sov_bps_scaled.values())
    reserve_depletion_bps = dedollar_info['reserve_bps']
    if reserve_depletion_bps > 0 and sov_total_bps > 0:
        larger = max(sov_total_bps, reserve_depletion_bps)
        smaller = min(sov_total_bps, reserve_depletion_bps)
        marginal_reserve = smaller * marginal_frac
        dedollar_adjusted = dedollar_bps - reserve_depletion_bps + marginal_reserve
        dedollar_adjusted = max(dedollar_adjusted, 0)
    else:
        dedollar_adjusted = dedollar_bps

    # 10. Combine core pressure channels
    withdrawal_subtotal = corrected_bps + max(velocity_bps, 0)
    clock1_subtotal = clock1_bps
    dedollar_subtotal = dedollar_adjusted
    core_bps = withdrawal_subtotal + clock1_subtotal + dedollar_subtotal

    # 10b. Regional capital flight (Gulf/ME -> London, Zurich, Istanbul, Delhi, Singapore)
    capflight_bps, capflight_info = compute_capital_flight_impact(
        rng, elasticity, existing_pressure_bps=core_bps
    )

    # 10c. Energy feedback (two-phase: Phase 1 relief, Phase 2 drag)
    energy_net_bps, energy_headroom_erosion, energy_info = compute_energy_feedback_impact(
        rng, elasticity
    )
    # Energy masking erodes headroom (issued debt during false calm)
    adjusted_headroom_bps = max(adjusted_headroom_bps - energy_headroom_erosion, 0)

    # 10d. Israel tech-defense pipeline (cost inflation + program delays)
    israel_bps, israel_info = compute_israel_pipeline_impact(rng, elasticity)

    # 10e. Domestic institutional (conditional: fires only on confidence shock)
    # Uses total pressure from all other channels as input
    pre_institutional_bps = (core_bps + capflight_bps +
                             max(energy_net_bps, 0) + israel_bps)
    institutional_bps, institutional_info = compute_domestic_institutional_impact(
        rng, elasticity, existing_pressure_bps=pre_institutional_bps
    )

    # 10f. Raw combined pressure (all channels)
    raw_combined_bps = (core_bps + capflight_bps + energy_net_bps +
                        israel_bps + institutional_bps)

    # 11. Apply policy response damping (Fix 4)
    combined_bps, damping_bps, policy_triggered = apply_policy_response(
        raw_combined_bps, adjusted_headroom_bps, rng
    )

    # 11b. Fiscal dominance regime switch
    # Checks if interest/revenue ratio crosses threshold.
    # If so: policy damping is REMOVED and replaced with amplification.
    fiscal_dom_activated, fiscal_dom_effect, fiscal_dom_info = compute_fiscal_dominance_effect(
        rng, raw_combined_bps, adjusted_headroom_bps, damping_bps
    )
    if fiscal_dom_activated:
        # Undo the damping and add amplification
        combined_bps = combined_bps + fiscal_dom_effect

    # 12. Headroom consumed (against adjusted headroom, which now includes energy erosion)
    if adjusted_headroom_bps > 0:
        headroom_consumed_pct = (combined_bps / adjusted_headroom_bps * 100)
    else:
        headroom_consumed_pct = 100.0  # headroom already gone

    result = {
        # Headroom
        'headroom_bps': headroom_bps,
        'debt_growth_adj_bps': debt_growth_adj,
        'adjusted_headroom_bps': adjusted_headroom_bps,
        'crisis_yield': crisis_yield,
        'crisis_ratio': crisis_ratio,

        # Demand elasticity (shared)
        'demand_elasticity': elasticity,

        # Withdrawal channels
        'velocity_decline_pct': velocity_decline,
        'velocity_bps': velocity_bps,
        'raw_bop_bps': raw_bop_bps,
        'sovereign_selling_bps': sov_total_bps,
        'corrected_clock2_bop_bps': corrected_bps,
        'withdrawal_subtotal_bps': withdrawal_subtotal,

        # Clock 1: Silver scissors
        'clock1_bps': clock1_bps,
        'clock1_cost_inflation_bps': clock1_info['channel_a_cost_yield_bps'],
        'clock1_disruption_triggered': clock1_info['channel_c_disruption_triggered'],
        'clock1_disruption_bps': clock1_info['channel_c_disruption_yield_bps'],
        'clock1_credibility_mult': credibility_mult,

        # De-dollarization
        'dedollar_raw_bps': dedollar_bps,
        'dedollar_adjusted_bps': dedollar_adjusted,
        'dedollar_oil_bps': dedollar_info['oil_bps'],
        'dedollar_reserve_bps': dedollar_info['reserve_bps'],
        'dedollar_brics_bps': dedollar_info['brics_bps'],
        'dedollar_boycott_bps': dedollar_info['boycott_bps'],
        'dedollar_dumping_bps': dedollar_info['dumping_bps'],

        # Regional capital flight (Gulf/ME)
        'capflight_bps': capflight_bps,
        'capflight_selling_B': capflight_info.get('total_selling_B', 0),
        'capflight_recycling_B': capflight_info.get('recycling_reduction_B', 0),
        'capflight_hormuz_triggered': capflight_info.get('hormuz_triggered', False),

        # Energy feedback
        'energy_net_bps': energy_net_bps,
        'energy_relief_bps': energy_info['phase1_relief_bps'],
        'energy_drag_bps': energy_info['phase2_drag_bps'],
        'energy_headroom_erosion_bps': energy_headroom_erosion,
        'energy_oil_increase_pct': energy_info['oil_increase_pct'],

        # Israel pipeline
        'israel_bps': israel_bps,
        'israel_cost_bps': israel_info['cost_bps'],
        'israel_delay_bps': israel_info['delay_bps'],
        'israel_emigration': israel_info['cumulative_emigration'],

        # Domestic institutional
        'institutional_bps': institutional_bps,
        'institutional_shock_occurred': institutional_info['shock_occurred'],
        'institutional_severity': institutional_info.get('severity', 0),
        'institutional_selling_B': institutional_info.get('total_selling_B', 0),
        'institutional_fed_intervention': institutional_info.get('fed_intervention', False),

        # Fiscal dominance
        'fiscal_dom_activated': fiscal_dom_activated,
        'fiscal_dom_effect_bps': fiscal_dom_effect,
        'fiscal_dom_crossing_year': fiscal_dom_info.get('crossing_year'),
        'fiscal_dom_final_ratio': fiscal_dom_info.get('final_ratio', 0),

        # Policy response
        'policy_triggered': policy_triggered,
        'policy_damping_bps': damping_bps,

        # Combined (all gaps integrated)
        'core_bps': core_bps,
        'pre_institutional_bps': pre_institutional_bps,
        'raw_combined_bps': raw_combined_bps,
        'combined_bps': combined_bps,
        'headroom_consumed_pct': headroom_consumed_pct,
        'crosses_threshold': combined_bps >= adjusted_headroom_bps,
        'total_import_reduction_B': total_import_reduction,
        'total_treasury_pressure_B': total_treasury_pressure,
        'marginal_frac': marginal_frac,
    }

    # Optional: YCC feedback simulation
    if run_ycc and combined_bps > 0:
        avg_withdrawal = np.mean([
            sample_triangular(rng, geo['withdrawal_pct'])
            for geo in GEOGRAPHIES.values()
        ])
        ycc_result = run_ycc_simulation(
            initial_yield_pressure_bps=combined_bps,
            initial_withdrawal_pct=avg_withdrawal,
            years=ycc_years,
            rng=rng
        )
        if ycc_result:
            result['ycc_final_withdrawal'] = ycc_result['withdrawal_pct'][-1]
            result['ycc_final_cpi'] = ycc_result['cpi_overshoot_pct'][-1]
            result['ycc_final_fed_purchases'] = ycc_result['fed_purchases_T'][-1]
            result['ycc_peak_cpi'] = max(ycc_result['cpi_overshoot_pct'])

    return result


def run_monte_carlo(n_iterations=N_ITERATIONS, clock1_progress=50,
                    run_ycc=False, ycc_years=10, seed=RNG_SEED):
    """
    Run the full Monte Carlo simulation.
    """
    rng = np.random.default_rng(seed)
    regression_results = run_regime_regressions()

    results = []
    for i in range(n_iterations):
        r = run_single_iteration(
            rng, regression_results,
            clock1_progress=clock1_progress,
            run_ycc=run_ycc,
            ycc_years=ycc_years
        )
        results.append(r)

        if (i + 1) % 1000 == 0:
            print(f"  Completed {i+1}/{n_iterations} iterations")

    return results


def summarize(results):
    """
    Compute summary statistics from Monte Carlo results.
    """
    keys = [
        'headroom_bps', 'adjusted_headroom_bps', 'debt_growth_adj_bps',
        'combined_bps', 'raw_combined_bps', 'headroom_consumed_pct',
        'demand_elasticity',
        'velocity_bps', 'corrected_clock2_bop_bps', 'withdrawal_subtotal_bps',
        'clock1_bps', 'clock1_cost_inflation_bps', 'clock1_disruption_bps',
        'clock1_credibility_mult',
        'dedollar_raw_bps', 'dedollar_adjusted_bps',
        'dedollar_oil_bps', 'dedollar_reserve_bps', 'dedollar_brics_bps',
        'dedollar_boycott_bps', 'dedollar_dumping_bps',
        'capflight_bps', 'capflight_selling_B', 'capflight_recycling_B',
        'energy_net_bps', 'energy_relief_bps', 'energy_drag_bps',
        'energy_headroom_erosion_bps', 'energy_oil_increase_pct',
        'israel_bps', 'israel_cost_bps', 'israel_delay_bps',
        'institutional_bps', 'institutional_selling_B',
        'fiscal_dom_effect_bps',
        'core_bps',
        'policy_damping_bps',
        'crisis_yield',
    ]

    summary = {}
    for k in keys:
        vals = [r[k] for r in results if k in r]
        if not vals:
            continue
        arr = np.array(vals)
        summary[k] = {
            'mean': np.mean(arr),
            'median': np.median(arr),
            'std': np.std(arr),
            'p5': np.percentile(arr, 5),
            'p25': np.percentile(arr, 25),
            'p75': np.percentile(arr, 75),
            'p95': np.percentile(arr, 95),
            'min': np.min(arr),
            'max': np.max(arr),
        }

    # Probability of crossing threshold
    crosses = [r['crosses_threshold'] for r in results]
    summary['prob_crosses_threshold'] = sum(crosses) / len(crosses)

    # Probability of policy response
    policy = [r['policy_triggered'] for r in results]
    summary['prob_policy_response'] = sum(policy) / len(policy)

    # Probability of silver disruption
    disruptions = [r['clock1_disruption_triggered'] for r in results]
    summary['prob_silver_disruption'] = sum(disruptions) / len(disruptions)

    # Probability of Hormuz threat (capital flight accelerant)
    hormuz_triggers = [r['capflight_hormuz_triggered'] for r in results]
    summary['prob_hormuz_threat'] = sum(hormuz_triggers) / len(hormuz_triggers)

    # Probability of domestic institutional shock
    inst_shocks = [r['institutional_shock_occurred'] for r in results]
    summary['prob_institutional_shock'] = sum(inst_shocks) / len(inst_shocks)

    # Fed intervention rate (conditional on institutional shock)
    fed_int = [r['institutional_fed_intervention'] for r in results if r['institutional_shock_occurred']]
    summary['prob_fed_intervention'] = sum(fed_int) / len(fed_int) if fed_int else 0

    # Fiscal dominance activation
    fiscal_dom = [r['fiscal_dom_activated'] for r in results]
    summary['prob_fiscal_dominance'] = sum(fiscal_dom) / len(fiscal_dom)

    return summary


if __name__ == '__main__':
    print("=== CLOCK 3 MODEL V3 + GAPS: MONTE CARLO ===")
    print("  V3 base: demand elasticity, silver scissors, policy response,")
    print("           geo-specific withdrawal, debt growth, de-dollarization")
    print("  + Gap 1: Regional capital flight (Gulf/ME)")
    print("  + Gap 2: Domestic institutional (pension/insurance/money market)")
    print("  + Gap 3: Fiscal dominance regime switch")
    print("  + Gap 4: Energy price feedback (two-phase)")
    print("  + Gap 5: Israel tech-defense pipeline\n")
    print(f"Running {N_ITERATIONS} iterations...\n")

    results = run_monte_carlo(n_iterations=N_ITERATIONS, run_ycc=False)
    s = summarize(results)

    print("\n=== RESULTS ===\n")

    print("HEADROOM:")
    h = s['headroom_bps']
    ah = s['adjusted_headroom_bps']
    dg = s['debt_growth_adj_bps']
    print(f"  Raw headroom:      median {h['median']:.0f} bps, 90% CI [{h['p5']:.0f}, {h['p95']:.0f}]")
    print(f"  Debt growth adj:   median {dg['median']:.0f} bps")
    print(f"  Adjusted headroom: median {ah['median']:.0f} bps, 90% CI [{ah['p5']:.0f}, {ah['p95']:.0f}]")
    print()

    print("DEMAND ELASTICITY (sampled):")
    de = s['demand_elasticity']
    print(f"  Median: {de['median']:.2f}, 90% CI: [{de['p5']:.2f}, {de['p95']:.2f}]")
    print()

    print("COMBINED YIELD PRESSURE:")
    rc = s['raw_combined_bps']
    c = s['combined_bps']
    pd_bps = s['policy_damping_bps']
    print(f"  Before policy response: median {rc['median']:.1f} bps, 90% CI [{rc['p5']:.1f}, {rc['p95']:.1f}]")
    print(f"  Policy damping:         median {pd_bps['median']:.1f} bps")
    print(f"  After policy response:  median {c['median']:.1f} bps, 90% CI [{c['p5']:.1f}, {c['p95']:.1f}]")
    print()

    print("HEADROOM CONSUMED:")
    hc = s['headroom_consumed_pct']
    print(f"  Median: {hc['median']:.1f}%, Mean: {hc['mean']:.1f}%")
    print(f"  90% CI: [{hc['p5']:.1f}%, {hc['p95']:.1f}%]")
    print()

    print(f"PROBABILITY OF CROSSING THRESHOLD: {s['prob_crosses_threshold']*100:.1f}%")
    print(f"PROBABILITY OF POLICY RESPONSE: {s['prob_policy_response']*100:.1f}%")
    print(f"PROBABILITY OF SILVER DISRUPTION: {s['prob_silver_disruption']*100:.1f}%")
    print(f"PROBABILITY OF HORMUZ THREAT: {s['prob_hormuz_threat']*100:.1f}%")
    print(f"PROBABILITY OF INSTITUTIONAL SHOCK: {s['prob_institutional_shock']*100:.1f}%")
    print(f"PROBABILITY OF FED INTERVENTION (given shock): {s['prob_fed_intervention']*100:.1f}%")
    print(f"PROBABILITY OF FISCAL DOMINANCE: {s['prob_fiscal_dominance']*100:.1f}%")
    print()

    print("COMPONENT BREAKDOWN (median bps):")
    print(f"  Withdrawal channels:")
    print(f"    Velocity (US):         {s['velocity_bps']['median']:.1f}")
    print(f"    Clock 2 + BoP:         {s['corrected_clock2_bop_bps']['median']:.1f}")
    print(f"    Subtotal:              {s['withdrawal_subtotal_bps']['median']:.1f}")
    print()
    print(f"  Clock 1 (Silver scissors):")
    print(f"    Cost inflation:        {s['clock1_cost_inflation_bps']['median']:.1f}")
    print(f"    Disruption tail risk:  {s['clock1_disruption_bps']['median']:.1f}")
    print(f"    Total:                 {s['clock1_bps']['median']:.1f}")
    print(f"    Credibility mult:      {s['clock1_credibility_mult']['median']:.2f}x")
    print()
    print(f"  De-dollarization:")
    print(f"    Oil settlement:        {s['dedollar_oil_bps']['median']:.1f}")
    print(f"    FX reserve divers.:    {s['dedollar_reserve_bps']['median']:.1f}")
    print(f"    BRICS settlement:      {s['dedollar_brics_bps']['median']:.1f}")
    print(f"    Consumer boycott:      {s['dedollar_boycott_bps']['median']:.1f}")
    print(f"    Treasury dumping:      {s['dedollar_dumping_bps']['median']:.1f}")
    print(f"    Adjusted total:        {s['dedollar_adjusted_bps']['median']:.1f}")
    print()
    print(f"  Regional capital flight (Gulf/ME):")
    cf = s['capflight_bps']
    print(f"    Yield pressure:        {cf['median']:.1f} (mean {cf['mean']:.1f})")
    print(f"    90% CI:                [{cf['p5']:.1f}, {cf['p95']:.1f}]")
    cfs = s['capflight_selling_B']
    cfr = s['capflight_recycling_B']
    print(f"    Direct selling ($B):   {cfs['median']:.0f} (mean {cfs['mean']:.0f})")
    print(f"    Recycling loss ($B/yr):{cfr['median']:.0f} (mean {cfr['mean']:.0f})")
    print()
    print(f"  Energy feedback (oil shock):")
    en = s['energy_net_bps']
    er = s['energy_relief_bps']
    ed = s['energy_drag_bps']
    eh = s['energy_headroom_erosion_bps']
    eo = s['energy_oil_increase_pct']
    print(f"    Oil price increase:    {eo['median']:.0f}%")
    print(f"    Phase 1 relief:        -{er['median']:.1f} bps")
    print(f"    Phase 2 drag:          +{ed['median']:.1f} bps")
    print(f"    Net yield effect:      {en['median']:.1f} bps")
    print(f"    Headroom erosion:      {eh['median']:.1f} bps (masking)")
    print()
    print(f"  Israel tech-defense pipeline:")
    il = s['israel_bps']
    print(f"    Total:                 {il['median']:.1f} bps (cost {s['israel_cost_bps']['median']:.1f} + delay {s['israel_delay_bps']['median']:.1f})")
    print()
    print(f"  Domestic institutional (conditional):")
    di = s['institutional_bps']
    print(f"    Yield pressure:        {di['median']:.1f} (mean {di['mean']:.1f})")
    print(f"    90% CI:                [{di['p5']:.1f}, {di['p95']:.1f}]")
    if 'institutional_selling_B' in s:
        dis = s['institutional_selling_B']
        print(f"    Selling volume ($B):   {dis['median']:.0f} (mean {dis['mean']:.0f})")
    print()
    print(f"  Fiscal dominance (regime switch):")
    fd = s['fiscal_dom_effect_bps']
    print(f"    Effect when activated: {fd['median']:.1f} (mean {fd['mean']:.1f}) bps")
    print(f"    Activation rate:       {s['prob_fiscal_dominance']*100:.1f}%")
    print()

    print("CRISIS YIELD:")
    cy = s['crisis_yield']
    print(f"  Median: {cy['median']:.2f}%, 90% CI: [{cy['p5']:.2f}%, {cy['p95']:.2f}%]")
