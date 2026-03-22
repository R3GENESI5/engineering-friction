"""
Charts Module
Publication-quality figures from the full Monte Carlo simulation.
Eight pressure channels, policy response, fiscal dominance regime switch.
No version history. This is the model.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from monte_carlo import run_monte_carlo, summarize
from config import N_ITERATIONS

OUT_DIR = os.path.dirname(__file__)

COLORS = {
    'dedollar': '#D4513D',
    'institutional': '#E8872B',
    'withdrawal': '#2E75B6',
    'capflight': '#1B9E77',
    'clock1': '#8B5CF6',
    'energy': '#D4A017',
    'israel': '#7B8794',
    'policy': '#5BA55B',
    'fiscal_dom': '#CC3333',
    'combined': '#333333',
    'headroom_raw': '#AAAAAA',
    'headroom_adj': '#333333',
    'bg': '#fafafa',
    'threshold_line': '#CC3333',
    'safe': '#2E75B6',
}


def generate_all_charts(results, summary):
    """Generate all publication-quality charts."""
    chart1_headroom_distribution(results, summary)
    chart2_pressure_vs_headroom(results, summary)
    chart3_component_breakdown(results, summary)
    chart4_phase1_vs_phase2(results, summary)
    print("All charts generated.")


def chart1_headroom_distribution(results, summary):
    """Histogram of raw vs adjusted headroom, showing debt self-feeding
    and energy masking erosion."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    raw = [r['headroom_bps'] for r in results]
    adjusted = [r['adjusted_headroom_bps'] for r in results]

    med_raw = summary['headroom_bps']['median']
    med_adj = summary['adjusted_headroom_bps']['median']
    debt_eaten = med_raw - med_adj

    ax.hist(raw, bins=60, color=COLORS['headroom_raw'], alpha=0.5, edgecolor='white',
            linewidth=0.5, zorder=2,
            label=f'Raw headroom (median {med_raw:.0f} bps)')
    ax.hist(adjusted, bins=60, color=COLORS['headroom_adj'], alpha=0.6, edgecolor='white',
            linewidth=0.5, zorder=3,
            label=f'After debt self-feeding + energy masking (median {med_adj:.0f} bps)')

    # Annotation: how much self-feeding eats
    ax.annotate(f'Debt growth + energy masking\nconsume {debt_eaten:.0f} bps',
                xy=(med_adj, ax.get_ylim()[1] * 0.5),
                xytext=(med_raw + 50, ax.get_ylim()[1] * 0.7),
                fontsize=10, color=COLORS['combined'],
                arrowprops=dict(arrowstyle='->', color=COLORS['combined'], lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#999'))

    ax.set_xlabel('Headroom to debt spiral threshold (basis points)', fontsize=12)
    ax.set_ylabel('Frequency (out of 10,000 iterations)', fontsize=12)
    ax.set_title('The system narrows its own window for survival\n'
                'before external pressure arrives.',
                fontsize=13, fontweight='bold')
    ax.legend(fontsize=10, framealpha=0.9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'chart1_headroom_distribution.png'),
               dpi=200, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close()
    print("  chart1_headroom_distribution.png")


def chart2_pressure_vs_headroom(results, summary):
    """Scatter: combined pressure vs adjusted headroom, with threshold line."""
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    headroom = [r['adjusted_headroom_bps'] for r in results]
    pressure = [r['combined_bps'] for r in results]

    # Sample 2000 points for readability
    rng = np.random.default_rng(42)
    idx = rng.choice(len(results), size=min(2000, len(results)), replace=False)

    h_sample = [headroom[i] for i in idx]
    p_sample = [pressure[i] for i in idx]

    colors_pts = [COLORS['threshold_line'] if p_sample[i] >= h_sample[i]
                  else COLORS['safe'] for i in range(len(idx))]

    ax.scatter(h_sample, p_sample, c=colors_pts, s=8, alpha=0.4, zorder=3)

    # Threshold line
    max_val = max(max(headroom), max(pressure)) * 0.6  # cap for readability
    ax.plot([0, max_val], [0, max_val], color=COLORS['threshold_line'],
           linewidth=2, linestyle='--',
           label='Threshold (pressure = headroom)', zorder=4)

    # Median point
    med_h = summary['adjusted_headroom_bps']['median']
    med_p = summary['combined_bps']['median']
    ax.scatter([med_h], [med_p], color=COLORS['combined'], s=150, marker='D',
              zorder=6, edgecolors='white', linewidth=1.5,
              label=f'Median ({med_h:.0f} bps headroom, {med_p:.0f} bps pressure)')

    # Crossing probability annotation
    prob = summary['prob_crosses_threshold']
    ax.text(0.97, 0.03, f'{prob*100:.1f}% of iterations\ncross the threshold',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=12, fontweight='bold', color=COLORS['threshold_line'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                     edgecolor=COLORS['threshold_line'], alpha=0.9))

    ax.set_xlabel('Adjusted headroom (basis points)', fontsize=12)
    ax.set_ylabel('Combined yield pressure (basis points)', fontsize=12)
    ax.set_title('Every dot is one Monte Carlo iteration.\n'
                'Red crosses the threshold. Blue does not.',
                fontsize=13, fontweight='bold')
    ax.legend(fontsize=9, loc='upper left', framealpha=0.9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'chart2_pressure_vs_headroom.png'),
               dpi=200, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close()
    print("  chart2_pressure_vs_headroom.png")


def chart3_component_breakdown(results, summary):
    """Horizontal bar: all eight pressure channels + policy + fiscal dominance."""
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    components = [
        # De-dollarization sub-channels
        ('Oil settlement shift', 'dedollar_oil_bps', COLORS['dedollar']),
        ('BRICS trade settlement', 'dedollar_brics_bps', COLORS['dedollar']),
        ('Treasury dumping (acceleration)', 'dedollar_dumping_bps', COLORS['dedollar']),
        ('FX reserve diversification', 'dedollar_reserve_bps', COLORS['dedollar']),
        ('Consumer boycotts', 'dedollar_boycott_bps', COLORS['dedollar']),
        # Domestic institutional
        ('Domestic institutional (conditional)', 'institutional_bps', COLORS['institutional']),
        # Withdrawal
        ('Household withdrawal (Clock 2 + BoP)', 'corrected_clock2_bop_bps', COLORS['withdrawal']),
        ('US monetary velocity', 'velocity_bps', COLORS['withdrawal']),
        # Regional capital flight
        ('Gulf/ME capital flight', 'capflight_bps', COLORS['capflight']),
        # Silver
        ('Silver scissors (Clock 1)', 'clock1_bps', COLORS['clock1']),
        # Energy
        ('Energy feedback (net)', 'energy_net_bps', COLORS['energy']),
        # Israel
        ('Israel tech-defense pipeline', 'israel_bps', COLORS['israel']),
        # Defense mechanisms (negative)
        ('Policy response (damping)', 'policy_damping_bps', COLORS['policy']),
        # Fiscal dominance (positive, conditional)
        ('Fiscal dominance (regime switch)', 'fiscal_dom_effect_bps', COLORS['fiscal_dom']),
    ]

    labels = []
    medians = []
    colors_bars = []

    for name, key, color in components:
        if key not in summary:
            continue
        med = summary[key]['median']
        labels.append(name)
        if key == 'policy_damping_bps':
            medians.append(-med)  # Show as negative (defense)
        else:
            medians.append(med)
        colors_bars.append(color)

    y_pos = range(len(labels))
    bars = ax.barh(y_pos, medians, color=colors_bars, alpha=0.75,
                   edgecolor='white', linewidth=0.5, zorder=3)

    # Value labels
    for i, (med, label) in enumerate(zip(medians, labels)):
        offset = 3 if med >= 0 else -3
        ha = 'left' if med >= 0 else 'right'
        display_val = abs(med)
        suffix = ' bps'
        if display_val < 1:
            text = f'{display_val:.1f}{suffix}'
        else:
            text = f'{display_val:.0f}{suffix}'
        ax.text(med + offset, i, text, va='center', ha=ha,
               fontsize=9, fontweight='bold', color=colors_bars[i])

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('Yield pressure (basis points, median across 10,000 iterations)', fontsize=11)
    ax.set_title('Eight pressure channels. One policy defense. One regime switch.\n'
                'De-dollarization and domestic institutional flight dominate.',
                fontsize=13, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.axvline(x=0, color='#999999', linewidth=0.5, zorder=1)
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'chart3_component_breakdown.png'),
               dpi=200, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close()
    print("  chart3_component_breakdown.png")


def chart4_phase1_vs_phase2(results, summary):
    """The time structure: Phase 1 signals vs Phase 2 reality.
    Shows how each channel presents in the short run vs the long run."""
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    # Phase 1 (short-run apparent effects) vs Phase 2 (long-run actual effects)
    channels = [
        ('Oil/dollar\nstrength',
         -summary['energy_relief_bps']['median'],  # Phase 1: relief (negative pressure)
         summary['energy_drag_bps']['median'],      # Phase 2: drag (positive pressure)
         COLORS['energy']),
        ('Gulf capital\nto London',
         summary['capflight_bps']['median'] * 0.25,   # Phase 1: 60% stays in USD, looks ok
         summary['capflight_bps']['median'],            # Phase 2: 57% exits dollar permanently
         COLORS['capflight']),
        ('Institutional\ncalm',
         0,                                              # Phase 1: no selling yet
         summary['institutional_bps']['median'],         # Phase 2: cliff when shock fires
         COLORS['institutional']),
        ('Fiscal ratio\nat 19%',
         0,                                              # Phase 1: below threshold
         summary['fiscal_dom_effect_bps']['median'],     # Phase 2: threshold crossed, defense gone
         COLORS['fiscal_dom']),
        ('De-dollarization\n1.4pp/yr',
         summary['dedollar_adjusted_bps']['median'] * 0.15,  # Phase 1: first year, small
         summary['dedollar_adjusted_bps']['median'],          # Phase 2: cumulative over 5 years
         COLORS['dedollar']),
    ]

    x = np.arange(len(channels))
    width = 0.35

    phase1_vals = [c[1] for c in channels]
    phase2_vals = [c[2] for c in channels]
    labels = [c[0] for c in channels]
    bar_colors = [c[3] for c in channels]

    bars1 = ax.bar(x - width/2, phase1_vals, width, color=bar_colors, alpha=0.3,
                   edgecolor='white', linewidth=1, zorder=3, label='Phase 1 (0-12 months)')
    bars2 = ax.bar(x + width/2, phase2_vals, width, color=bar_colors, alpha=0.8,
                   edgecolor='white', linewidth=1, zorder=3, label='Phase 2 (12-60 months)')

    # Value labels on Phase 2 bars
    for i, (v1, v2) in enumerate(zip(phase1_vals, phase2_vals)):
        if v1 != 0:
            ax.text(i - width/2, v1 + 2, f'{v1:.0f}', ha='center', va='bottom',
                   fontsize=9, color=bar_colors[i])
        else:
            ax.text(i - width/2, 2, 'quiet', ha='center', va='bottom',
                   fontsize=8, color='#999', style='italic')
        ax.text(i + width/2, v2 + 2, f'{v2:.0f}', ha='center', va='bottom',
               fontsize=9, fontweight='bold', color=bar_colors[i])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel('Yield pressure (basis points)', fontsize=11)
    ax.set_title('The war looks like it is working.\n'
                'Phase 1 signals mask Phase 2 reality.',
                fontsize=13, fontweight='bold')
    ax.legend(fontsize=10, framealpha=0.9, loc='upper left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'chart4_phase1_vs_phase2.png'),
               dpi=200, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close()
    print("  chart4_phase1_vs_phase2.png")


if __name__ == '__main__':
    print("Running Monte Carlo for chart generation...\n")
    results = run_monte_carlo(n_iterations=N_ITERATIONS, run_ycc=False)
    summary = summarize(results)

    print("\nGenerating charts...\n")
    generate_all_charts(results, summary)
