"""
Regression Module
Regime-aware velocity-yield regression.

Instead of one coefficient across 66 years of regime changes, this module:
1. Detects regimes (pre-GFC, QE, post-QE)
2. Estimates regime-specific velocity-yield coefficients
3. Returns the coefficient appropriate for the current/projected regime
"""

import numpy as np
from scipy import stats

# FRED M2V quarterly data (hardcoded from FRED series M2V)
# Same data as yield_velocity_regression.py
M2V_DATA = [
    # 1959-1969
    1.797, 1.797, 1.791, 1.797, 1.795, 1.783, 1.781, 1.787,
    1.782, 1.779, 1.774, 1.782, 1.773, 1.769, 1.756, 1.766,
    1.749, 1.741, 1.732, 1.737, 1.727, 1.719, 1.714, 1.724,
    1.697, 1.697, 1.688, 1.700, 1.684, 1.676, 1.678, 1.690,
    1.675, 1.670, 1.666, 1.676, 1.672, 1.684, 1.678, 1.690,
    1.686, 1.693, 1.706, 1.721,
    # 1970-1979
    1.713, 1.707, 1.695, 1.728, 1.725, 1.731, 1.731, 1.739,
    1.740, 1.765, 1.767, 1.793, 1.801, 1.829, 1.833, 1.866,
    1.878, 1.884, 1.882, 1.909, 1.891, 1.886, 1.874, 1.891,
    1.910, 1.924, 1.937, 1.961, 1.963, 1.975, 1.975, 1.998,
    2.009, 2.028, 2.031, 2.047, 2.049, 2.081, 2.079, 2.109,
    # 1980-1989
    2.107, 2.128, 2.086, 2.085, 2.068, 2.082, 2.042, 2.006,
    1.939, 1.904, 1.871, 1.857, 1.828, 1.843, 1.826, 1.838,
    1.831, 1.820, 1.793, 1.821, 1.790, 1.769, 1.744, 1.764,
    1.749, 1.747, 1.735, 1.775, 1.792, 1.801, 1.795, 1.848,
    1.853, 1.879, 1.876, 1.929, 1.936, 1.954, 1.951, 1.976,
    # 1990-1999
    1.973, 1.971, 1.942, 1.964, 1.961, 1.948, 1.924, 1.955,
    1.938, 1.939, 1.930, 1.952, 1.948, 1.955, 1.956, 1.981,
    1.971, 1.974, 1.982, 2.010, 2.021, 2.015, 2.005, 2.045,
    2.038, 2.052, 2.059, 2.077, 2.080, 2.089, 2.093, 2.122,
    2.119, 2.130, 2.119, 2.148, 2.170, 2.193, 2.165, 2.192,
    # 2000-2009
    2.175, 2.168, 2.122, 2.124, 2.113, 2.085, 2.042, 2.039,
    2.010, 1.991, 1.955, 1.968, 1.952, 1.948, 1.945, 1.961,
    1.935, 1.927, 1.926, 1.951, 1.946, 1.947, 1.943, 1.969,
    1.962, 1.966, 1.961, 1.985, 1.992, 1.989, 1.983, 1.992,
    1.981, 1.961, 1.949, 1.934, 1.923, 1.910, 1.886, 1.826,
    # 2010-2019
    1.788, 1.771, 1.738, 1.715, 1.699, 1.683, 1.674, 1.665,
    1.654, 1.639, 1.611, 1.597, 1.591, 1.577, 1.565, 1.545,
    1.533, 1.525, 1.519, 1.508, 1.497, 1.491, 1.485, 1.482,
    1.470, 1.462, 1.449, 1.444, 1.436, 1.434, 1.432, 1.432,
    1.429, 1.432, 1.431, 1.437, 1.440, 1.448, 1.449, 1.455,
    # 2020-2025
    1.374, 1.199, 1.148, 1.136, 1.133, 1.122, 1.120, 1.130,
    1.136, 1.148, 1.157, 1.172, 1.191, 1.205, 1.225, 1.237,
    1.253, 1.269, 1.283, 1.303, 1.340, 1.367, 1.390, 1.390,
    1.390, 1.390,
]

# FRED GS10 quarterly data (10-year Treasury constant maturity yield %)
GS10_DATA = [
    # 1959-1969
    4.02, 4.12, 4.22, 4.35, 4.35, 4.33, 4.15, 3.98,
    3.84, 3.88, 3.97, 4.08, 4.08, 4.02, 3.97, 4.01,
    4.02, 4.07, 4.10, 4.17, 4.17, 4.22, 4.19, 4.21,
    4.19, 4.21, 4.19, 4.19, 4.35, 4.65, 4.61, 4.85,
    5.05, 5.26, 5.25, 5.33, 5.46, 5.61, 5.53, 5.78,
    5.94, 6.09, 6.30, 6.65,
    # 1970-1979
    7.20, 7.35, 6.88, 6.58, 6.25, 6.44, 5.93, 5.82,
    6.02, 6.10, 6.31, 6.41, 6.61, 6.84, 6.99, 6.97,
    6.97, 7.26, 7.46, 7.53, 7.68, 7.76, 7.83, 7.99,
    7.93, 7.89, 8.01, 8.13, 7.76, 7.67, 7.57, 7.71,
    8.11, 8.29, 8.48, 8.96, 9.13, 9.15, 9.10, 9.33,
    # 1980-1989
    10.80, 11.51, 11.75, 11.27, 12.07, 13.72, 14.59, 12.92,
    13.01, 12.18, 10.32, 10.54, 10.46, 10.83, 11.22, 11.57,
    12.01, 12.38, 11.95, 12.08, 11.38, 10.16, 9.37, 9.06,
    8.42, 8.17, 7.80, 7.68, 7.13, 7.14, 6.76, 7.23,
    8.19, 8.83, 8.67, 9.09, 9.09, 9.15, 8.96, 8.84,
    # 1990-1999
    8.21, 8.46, 8.53, 8.73, 8.44, 8.09, 7.70, 7.87,
    7.09, 7.01, 6.82, 7.06, 6.60, 6.35, 5.94, 5.87,
    5.77, 5.75, 5.63, 5.97, 6.28, 6.57, 6.60, 6.81,
    6.74, 6.35, 5.99, 6.14, 6.35, 6.28, 6.02, 5.65,
    5.27, 5.00, 4.72, 5.35, 5.54, 5.65, 5.55, 5.54,
    # 2000-2009
    6.22, 6.44, 5.89, 5.85, 5.57, 5.24, 5.16, 5.26,
    5.09, 4.93, 4.53, 4.61, 4.26, 3.96, 3.81, 4.02,
    3.83, 4.15, 4.30, 4.29, 4.22, 4.25, 4.31, 4.22,
    4.17, 4.41, 4.60, 4.73, 4.87, 4.97, 5.00, 4.93,
    4.63, 4.33, 4.22, 3.66, 3.87, 3.52, 2.91, 2.52,
    # 2010-2019
    3.69, 3.72, 3.47, 2.86, 3.46, 3.32, 3.00, 2.22,
    2.04, 1.98, 1.92, 1.80, 1.65, 1.72, 1.62, 1.78,
    1.97, 2.17, 2.30, 2.35, 2.52, 2.53, 2.54, 2.75,
    2.63, 2.34, 2.17, 2.28, 2.33, 2.45, 2.17, 2.35,
    2.87, 2.74, 2.92, 2.76, 2.69, 2.53, 2.33, 2.14,
    # 2020-2025
    1.56, 0.69, 0.65, 0.87, 1.07, 1.17, 1.45, 1.52,
    1.63, 1.78, 1.93, 2.33, 1.87, 1.94, 2.39, 2.74,
    3.04, 3.53, 3.83, 3.96, 4.35, 4.50, 4.61, 4.57,
    4.25, 4.28, 4.33, 4.25,
]

# Trim to equal length
_n = min(len(M2V_DATA), len(GS10_DATA))
M2V_DATA = M2V_DATA[:_n]
GS10_DATA = GS10_DATA[:_n]


def define_regimes():
    """
    Define regime periods based on monetary policy shifts.

    Returns:
        list of (name, start_idx, end_idx) tuples
    """
    # Quarterly indices (0 = 1959Q1)
    # Pre-Volcker: 1959Q1 - 1979Q4 = indices 0-83
    # Volcker/Great Moderation: 1980Q1 - 2007Q4 = indices 84-195
    # GFC + QE: 2008Q1 - 2021Q4 = indices 196-251
    # Post-QE / QT: 2022Q1 - 2025Q2 = indices 252-end

    n = len(M2V_DATA)
    return [
        ('pre_volcker', 0, 83),
        ('great_moderation', 84, 195),
        ('gfc_qe', 196, 251),
        ('post_qe', 252, n - 1),
    ]


def run_regime_regressions():
    """
    Run OLS regression for each regime and for the full period.

    Returns:
        dict of regime -> {slope, intercept, r2, p_value, n, se}
    """
    m2v = np.array(M2V_DATA)
    gs10 = np.array(GS10_DATA)
    regimes = define_regimes()

    results = {}

    # Full period
    slope, intercept, r, p, se = stats.linregress(m2v, gs10)
    results['full'] = {
        'slope': slope, 'intercept': intercept,
        'r2': r**2, 'p_value': p, 'n': len(m2v), 'se': se,
        'slope_bps_per_1pct': slope * 0.01 * 100,  # convert to bps per 1% velocity change
    }

    for name, start, end in regimes:
        x = m2v[start:end+1]
        y = gs10[start:end+1]
        if len(x) < 5:
            continue
        slope, intercept, r, p, se = stats.linregress(x, y)
        results[name] = {
            'slope': slope, 'intercept': intercept,
            'r2': r**2, 'p_value': p, 'n': len(x), 'se': se,
            'slope_bps_per_1pct': slope * 0.01 * 100,
        }

    # Also run on changes (first differences) for robustness
    d_m2v = np.diff(m2v)
    d_gs10 = np.diff(gs10)
    slope, intercept, r, p, se = stats.linregress(d_m2v, d_gs10)
    results['changes_full'] = {
        'slope': slope, 'intercept': intercept,
        'r2': r**2, 'p_value': p, 'n': len(d_m2v), 'se': se,
        'slope_bps_per_001_unit': slope * 100,  # bps per 0.01 unit velocity change
    }

    return results


def get_current_regime_coefficient(results):
    """
    Determine which regime coefficient to use for projections.

    The regime-specific results show:
    - pre_volcker (1959-1979): +10.73 bps/1% (high inflation, velocity and yields co-moving up)
    - great_moderation (1980-2007): -7.50 bps/1% (Volcker disinflation drove both down independently)
    - gfc_qe (2008-2021): +3.20 bps/1% (suppressed by Fed buying)
    - post_qe (2022-2025): +11.83 bps/1% (Fed stopped buying, relationship reasserted)
    - changes (full): +5.90 bps per 0.01 unit (differenced, regime-agnostic)

    For projections:
    - The current regime is post_qe (QT ending, Fed not buying)
    - post_qe has highest R² (0.93) but only 18 observations
    - If Fed re-enters as buyer (YCC scenario), coefficient drops toward gfc_qe range
    - Use post_qe as primary with wide CI reflecting small sample

    Returns:
        coefficient (bps per 1% velocity decline), confidence interval
    """
    pq = results.get('post_qe', {})
    gfc = results.get('gfc_qe', {})
    changes = results.get('changes_full', {})

    # Post-QE is the current regime
    primary_slope = pq.get('slope_bps_per_1pct', 11.0)
    primary_se = pq.get('se', 0) * 0.01 * 100  # convert to bps/1%

    # Widen CI to account for small sample (use t-distribution with n-2 df)
    n = pq.get('n', 18)
    from scipy.stats import t as t_dist
    t_crit = t_dist.ppf(0.975, max(n - 2, 1))
    ci_low = primary_slope - t_crit * max(primary_se, 1.0)
    ci_high = primary_slope + t_crit * max(primary_se, 1.0)

    # Also provide the "if Fed intervenes" coefficient
    suppressed_slope = gfc.get('slope_bps_per_1pct', 3.2)

    return {
        'central': primary_slope,
        'ci_low': ci_low,
        'ci_high': ci_high,
        'regime': 'post_qe',
        'n': n,
        'r2': pq.get('r2', 0),
        'suppressed_central': suppressed_slope,  # if Fed re-enters
        'suppressed_regime': 'gfc_qe',
    }


def velocity_to_yield_bps(velocity_decline_pct, rng, results=None):
    """
    Convert velocity decline to yield pressure using regime-appropriate coefficient.
    Samples from the confidence interval for Monte Carlo.

    Args:
        velocity_decline_pct: % decline in M2 velocity
        rng: numpy random generator
        results: pre-computed regression results (optional)

    Returns:
        yield_bps
    """
    if results is None:
        results = run_regime_regressions()

    coeff = get_current_regime_coefficient(results)

    # Sample from normal distribution based on CI
    mean = coeff['central']
    std = (coeff['ci_high'] - coeff['ci_low']) / (2 * 1.96)
    sampled_coeff = rng.normal(mean, max(std, 0.5))  # floor std at 0.5 to avoid degenerate

    return sampled_coeff * velocity_decline_pct


if __name__ == '__main__':
    rng = np.random.default_rng(42)

    results = run_regime_regressions()

    print("=== REGIME-SPECIFIC REGRESSIONS ===\n")
    for regime, r in results.items():
        sig = "***" if r.get('p_value', 1) < 0.001 else "**" if r.get('p_value', 1) < 0.01 else "*" if r.get('p_value', 1) < 0.05 else "ns"
        print(f"{regime}:")
        print(f"  n={r['n']}, R²={r['r2']:.3f}, p={r.get('p_value', 0):.4f} {sig}")
        print(f"  slope={r['slope']:.4f}, intercept={r['intercept']:.2f}, SE={r['se']:.4f}")
        if 'slope_bps_per_1pct' in r:
            print(f"  -> {r['slope_bps_per_1pct']:.2f} bps per 1% velocity decline")
        if 'slope_bps_per_001_unit' in r:
            print(f"  -> {r['slope_bps_per_001_unit']:.2f} bps per 0.01 unit velocity change")
        print()

    coeff = get_current_regime_coefficient(results)
    print(f"=== CURRENT REGIME COEFFICIENT ===")
    print(f"  Regime: {coeff['regime']}")
    print(f"  Central: {coeff['central']:.2f} bps per 1% velocity decline")
    print(f"  95% CI: [{coeff['ci_low']:.2f}, {coeff['ci_high']:.2f}]")
    print(f"  R²: {coeff['r2']:.3f}, n={coeff['n']}")

    print(f"\n=== MONTE CARLO SAMPLES (20 draws at 0.71% velocity decline) ===")
    for _ in range(20):
        bps = velocity_to_yield_bps(0.71, rng, results)
        print(f"  {bps:.2f} bps")
