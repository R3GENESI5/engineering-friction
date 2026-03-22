"""
YCC Feedback Loop Module
Models the reinforcing dynamics when the Fed activates yield curve control.

The loop:
1. Withdrawal reduces Treasury demand -> yield pressure rises
2. Fed buys bonds (YCC) to cap yields -> balance sheet expands
3. Balance sheet expansion -> inflation (lagged)
4. Inflation -> higher cost of grid living -> more households exit
5. More exit -> more withdrawal -> back to step 1

Damping mechanisms:
- Inflation boosts nominal GDP, improving debt-to-GDP ratio
- Fed can adjust rates, forward guidance
- Not all inflation translates to withdrawal

Modeled as a system of coupled differential equations solved over time.
"""

import numpy as np
from scipy.integrate import solve_ivp
from config import YCC_PARAMS, sample_triangular


def build_ycc_system(params):
    """
    Build the YCC feedback system as a function suitable for solve_ivp.

    State vector y = [
        withdrawal_pct,     # fraction of population withdrawn (0-1)
        fed_purchases_T,    # cumulative Fed bond purchases ($T)
        cpi_overshoot_pct,  # inflation above 2% baseline
        nominal_gdp_boost_pct,  # GDP boost from inflation
    ]

    Args:
        params: sampled parameter dict

    Returns:
        function(t, y) -> dydt
    """
    alpha = params['bs_to_cpi_alpha']          # CPI per $1T of purchases
    lag_q = params['bs_to_cpi_lag_quarters']
    absorption_T = YCC_PARAMS['balance_sheet_to_cpi']['absorption_threshold_T']
    pain_threshold = YCC_PARAMS['cpi_to_informal']['pain_threshold_pct']
    cpi_to_informal = params['cpi_to_informal_coeff']
    gdp_boost_per_cpi = YCC_PARAMS['nominal_gdp_boost_per_cpi_pct']
    initial_yield_pressure_bps = params['initial_yield_pressure_bps']

    def system(t, y):
        withdrawal_pct, fed_purchases_T, cpi_overshoot, nom_gdp_boost = y

        # 1. Yield pressure from withdrawal (proportional)
        # More withdrawal -> more pressure -> more Fed buying needed
        yield_pressure = initial_yield_pressure_bps * (1 + withdrawal_pct * 10)
        # Factor of 10: 10% withdrawal roughly doubles the initial pressure

        # 2. Fed buying rate: proportional to yield pressure above cap
        # Fed buys to keep pressure from exceeding threshold
        buying_rate_T_per_yr = max(0, yield_pressure / 100 * 0.5)
        # 0.5T per year per 100bps of pressure (rough calibration from QE scale)

        # 3. CPI overshoot from purchases (with absorption threshold and lag)
        effective_purchases = max(0, fed_purchases_T - absorption_T)
        # Lag modeled as gradual effect (simplified from discrete lag)
        target_cpi = alpha * effective_purchases
        cpi_convergence_rate = 4 / lag_q  # converge over lag period
        d_cpi = (target_cpi - cpi_overshoot) * cpi_convergence_rate

        # 4. Nominal GDP boost from inflation (damping mechanism)
        d_nom_gdp = (cpi_overshoot * gdp_boost_per_cpi - nom_gdp_boost) * 2
        # Quick convergence: GDP responds to inflation within ~2 quarters

        # 5. Withdrawal acceleration from inflation
        excess_inflation = max(0, cpi_overshoot - pain_threshold)
        d_withdrawal = excess_inflation * cpi_to_informal / 100
        # Convert from percentage points to fraction per year

        # 6. Damping: GDP boost reduces effective yield pressure
        # (not modeled directly in state, but affects the buying rate)

        d_fed_purchases = buying_rate_T_per_yr

        return [d_withdrawal, d_fed_purchases, d_cpi, d_nom_gdp]

    return system


def run_ycc_simulation(initial_yield_pressure_bps, initial_withdrawal_pct, years, rng):
    """
    Run the YCC feedback simulation.

    Args:
        initial_yield_pressure_bps: starting yield pressure before Fed intervention
        initial_withdrawal_pct: starting withdrawal fraction
        years: simulation horizon
        rng: numpy random generator

    Returns:
        dict with time series of all state variables
    """
    # Sample parameters
    params = {
        'bs_to_cpi_alpha': sample_triangular(rng, YCC_PARAMS['balance_sheet_to_cpi']['alpha']),
        'bs_to_cpi_lag_quarters': sample_triangular(rng, YCC_PARAMS['balance_sheet_to_cpi']['lag_quarters']),
        'cpi_to_informal_coeff': sample_triangular(rng, YCC_PARAMS['cpi_to_informal']['coefficient']),
        'initial_yield_pressure_bps': initial_yield_pressure_bps,
    }

    system_fn = build_ycc_system(params)

    y0 = [initial_withdrawal_pct, 0.0, 0.0, 0.0]
    t_span = (0, years)
    t_eval = np.linspace(0, years, years * 4 + 1)  # quarterly resolution

    sol = solve_ivp(system_fn, t_span, y0, t_eval=t_eval, method='RK45',
                    max_step=0.25)  # max quarterly steps

    if not sol.success:
        return None

    return {
        'time_years': sol.t,
        'withdrawal_pct': sol.y[0],
        'fed_purchases_T': sol.y[1],
        'cpi_overshoot_pct': sol.y[2],
        'nominal_gdp_boost_pct': sol.y[3],
        'params': params,
    }


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    print("=== YCC FEEDBACK SIMULATION ===")
    print("Initial conditions: 50 bps yield pressure, 5% withdrawal")
    print()

    result = run_ycc_simulation(
        initial_yield_pressure_bps=50,
        initial_withdrawal_pct=0.05,
        years=15,
        rng=rng
    )

    if result:
        for i in range(0, len(result['time_years']), 4):  # yearly snapshots
            t = result['time_years'][i]
            w = result['withdrawal_pct'][i]
            fp = result['fed_purchases_T'][i]
            cpi = result['cpi_overshoot_pct'][i]
            gdp = result['nominal_gdp_boost_pct'][i]
            print(f"  Year {t:5.1f}: withdrawal {w*100:5.1f}%, "
                  f"Fed purchases ${fp:.1f}T, CPI overshoot {cpi:.1f}%, "
                  f"GDP boost {gdp:.1f}%")
    else:
        print("  Simulation failed to converge")
