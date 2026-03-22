# Engineering Friction

Monte Carlo stress model measuring yield pressure on the US Treasury market through eight independent channels. Companion code for the [Engineering Friction](https://ehadnameh.substack.com) series on Substack.

## The series

Engineering Friction is a seven-piece analytical series on the structural mechanics of the Iran-US-Israel war, how it gets paid for, and what survives the payment.

| # | Title | What it does |
|---|-------|-------------|
| 69.1 | **The Engineered Friction** | Documents twenty-something structural outcomes the war produces simultaneously. Nine problems solved at once, three channels of institutional capture, carrying capacity destroyed across the Middle East to build the Hard State. Establishes the thesis: the war is not a policy failure, it is an architecture. |
| 69.2 | **The Trigger Point** | Traces the war-finance coupling from Laurion silver mines to the Federal Reserve. Identifies three clocks running against the war coalition: Clock 1 (Chinese material science solving silver dependency), Clock 2 (Treasury market confidence eroding), Clock 3 (household withdrawal from the grid). |
| 69.3 | **The Board Holds** | Runs the war-suppressed Monte Carlo model. Eight channels, ten thousand iterations, five-year horizon. Result: 63.4 basis points of combined pressure against 396 basis points of headroom. 0% threshold crossing. The board holds. Then documents what the headroom hides: the debt curve, velocity decline, fiscal dominance trajectory, demand elasticity cliffs, and de-dollarization rebuild. Also covers the US mineral pivot (Orinoco, DRC, Argentina), Israel's territorial logic, Iran's rehabilitation play, and the institutional harvest running under wartime cover. |
| 69.4 | **The Third Clock** | Runs the coupled model with post-2010 demand elasticity, channel interactions, and adjusted headroom. Result: 516 basis points against 168 adjusted headroom. 92.6% threshold crossing. Then pivots: if Clock 3 (household withdrawal) produces only 11% of the pressure, what does it do that the other clocks cannot? Introduces Garrett's thermodynamic double-bind, the second energy pathway (hydrological cycle), and a 1,400-year-old operational specification for the exit. Includes a full technical addendum walking through every channel, parameter, and chart. |
| 69.5 | **The Three Jerusalems** | Forthcoming. The eschatological architecture driving all three actors. |
| 69.6 | **The Fourth Direction** | Forthcoming. |
| A | **Addendum A** | Forthcoming. Full parameter tables and model audit. |

All published at [ehadnameh.substack.com](https://ehadnameh.substack.com). Free. Always free.

## Two scenarios, one model

The model runs two configurations on the same eight channels:

| | War-suppressed (69.3) | Coupled (69.4) |
|---|---|---|
| Channel coupling | Off | On (one channel's output feeds another's probability) |
| Demand elasticity | Pre-2010 regime | Post-2010 regime (Somogyi, Wallen, Xu 2025) |
| Headroom | 396 bps raw | 168 bps adjusted (debt self-feeding consumes 213, energy masking 12) |
| Combined pressure | 63.4 bps median | 516 bps median |
| Threshold crossing | 0.0% | 92.6% |
| Interpretation | The war buys 5-8 years of headroom | The pressure surfaces when suppressive effects fade |

The war-suppressed model shows what the system looks like while the war is doing what it was designed to do. The coupled model shows what accumulates underneath.

## The eight channels

| # | Channel | Module | War-suppressed (bps) | Coupled (bps) | Mechanism |
|---|---------|--------|---------------------|---------------|-----------|
| 1 | De-dollarization | `dedollarization.py` | 23.5 | 271 | Oil settlement shift, FX reserve diversification, BRICS bilateral trade, accelerated Treasury dumping, consumer boycotts |
| 2 | Domestic institutional | `domestic_institutional.py` | 10.2 | 155 | Cliff behavior in US pension funds, insurance, money markets ($8.7T). Standalone probability 65%, under stress 93% |
| 3 | Household withdrawal | `withdrawal.py` | 8.1 | 58 | Sovereign selling and balance-of-payments pressure from seven geographies as families exit the formal economy |
| 4 | Regional capital flight | `capital_flight.py` | 6.3 | 25 | Gulf private wealth ($1.5-3.5T) fleeing to London, Istanbul, Delhi, Singapore. Net 57% leaves dollar system |
| 5 | Silver scissors | `clock1.py` | 3.8 | 11 + 1.16x multiplier | Cost inflation on $250B silver-sensitive spending, credibility multiplier on de-dollarization, disruption tail risk |
| 6 | Energy feedback | `energy_feedback.py` | 5.1 | 9 net + 12 masking | Two-phase: dollar strengthens short-run (masking), deficit widens long-run |
| 7 | Israel pipeline | `israel_pipeline.py` | 1.5 | 1.5 | Tech workforce emigration (8,300 since Oct 2023), replacement costs, program delays |
| 8 | Fiscal dominance | `fiscal_dominance.py` | inactive | 19 (when active) | Regime switch (Leeper 1991): rate hikes become self-defeating. Activates in 63% of coupled runs |

Policy response (rate cuts, bilateral deals, fiscal adjustment) absorbs ~50 bps but gets neutralized when fiscal dominance activates.

## Charts

### 69.3 charts (war-suppressed model + structural analysis)

| Chart | File | What it shows |
|-------|------|--------------|
| Board Holds scatter | `chart_693a_board_holds_scatter.png` | 10,000 iterations, all blue (below threshold). 0% crossing. The visual proof the board holds. |
| Mineral pivot | `chart_693c_mineral_pivot.png` | US strategic mineral positioning: Orinoco gold (7,000t est.), DRC cobalt (70% of global), Argentine lithium, Orinoco rare earths and coltan. All signed at wartime speed. |
| Headroom distribution | `chart1_headroom_distribution.png` | Raw headroom (396 bps) vs adjusted (168 bps). Shows the system narrowing its own survival window through debt self-feeding before any external pressure arrives. |
| Fiscal dominance trajectory | `chart_693b_fiscal_dominance_trajectory.png` | Interest-to-revenue ratio climbing from 19% toward the 33% threshold. Central estimate crosses year 6-7. High estimate crosses year 3-4. |
| Phase 1 vs Phase 2 | `chart4_phase1_vs_phase2.png` | Paired bars showing how the war's short-term signals (small Phase 1) mask long-term structural damage (large Phase 2). Bridges to 69.4. |
| Convergent destruction | `chart_693d_convergent_destruction.png` | Three actors (US, Israel, Iran) with divergent goals converging on one war. Shared outcomes below: corridors destroyed, architecture hardened, exits close. |

### 69.4 charts (coupled model, in addendum)

| Chart | File | What it shows |
|-------|------|--------------|
| Headroom distribution | `chart1_headroom_distribution.png` | Same chart, provides context for adjusted headroom calculation in the addendum. |
| Pressure vs headroom scatter | `chart2_pressure_vs_headroom.png` | 10,000 iterations: 92.6% red (above threshold). The payoff chart. Median at (168, 516). |
| Component breakdown | `chart3_component_breakdown.png` | All 8 channels as horizontal bars at coupled values. De-dollarization (271) and institutional (155) dominate. Policy response goes negative (-50). |
| Phase 1 vs Phase 2 | `chart4_phase1_vs_phase2.png` | Same chart, sits alongside full channel analysis in the addendum. |
| Sensitivity tornado | `chart5_sensitivity_tornado.png` | P10-to-P90 uncertainty range per channel. De-dollarization has the widest bar. Shows where the model is most and least certain. |
| Coupling cascade | `chart6_coupling_cascade.png` | Directed flow diagram showing how channels trigger each other. De-dollarization and withdrawal feed combined pressure, which triggers institutional shock, which activates fiscal dominance. |

### Model development (wiki only)

| Chart | File | What it shows |
|-------|------|--------------|
| v1 vs v2 | `chart4_v1_vs_v2.png` | Original point estimate vs war-suppressed Monte Carlo. |
| v1 vs v3 | `chart4_v1_vs_v3.png` | Original point estimate vs coupled Monte Carlo. Shows how headroom, pressure, and consumption changed between model versions. |

## Repository structure

```
model/
  config.py              # Global parameters, distribution definitions, RNG seed
  monte_carlo.py         # Main simulation loop (10,000 iterations)
  regression.py          # Regime regressions feeding into monte_carlo
  dedollarization.py     # Channel 1: five sub-channels of dollar abandonment
  domestic_institutional.py  # Channel 2: cliff behavior, confidence shock
  withdrawal.py          # Channel 3: household withdrawal across 7 geographies
  capital_flight.py      # Channel 4: Gulf private wealth flight
  clock1.py              # Channel 5: silver scissors (material dependency)
  energy_feedback.py     # Channel 6: oil price two-phase effect
  israel_pipeline.py     # Channel 7: tech-defense workforce drain
  fiscal_dominance.py    # Channel 8: regime switch
  overlap.py             # Cross-channel overlap corrections
  threshold.py           # Headroom derivation and threshold calibration
  ycc_loop.py            # Yield curve control scenario (optional)
  charts.py              # Chart generation (charts 1-6)
charts/
  chart1_headroom_distribution.png
  chart2_pressure_vs_headroom.png
  chart3_component_breakdown.png
  chart4_phase1_vs_phase2.png
  chart5_sensitivity_tornado.png
  chart6_coupling_cascade.png
  chart_693a_board_holds_scatter.png
  chart_693b_fiscal_dominance_trajectory.png
  chart_693c_mineral_pivot.png
  chart_693d_convergent_destruction.png
```

## How to run

Requires Python 3.9+ with `numpy`, `matplotlib`, and `scipy`.

```bash
pip install numpy matplotlib scipy
cd model
python monte_carlo.py
python charts.py
```

Each module runs standalone. Import any channel module and call its function with a seeded `numpy.random.Generator` to get that channel's output in isolation.

## Parameter sources

Every parameter is drawn from a named source. Key references:

- **Demand elasticity**: Somogyi, Wallen, and Xu, [HBS Working Paper 26-033](https://www.hbs.edu/faculty/Pages/item.aspx?num=68237), December 2025. Post-2010 sensitivity: 9 bps per 1% supply increase (up from 2 bps pre-2010).
- **USD reserve share**: [IMF COFER](https://data.imf.org/regular.aspx?key=41175). 72% (2014) to 57.8% (2024).
- **Silver deficit**: [Silver Institute 2025](https://silverinstitute.org/the-silver-market-is-on-course-for-fifth-successive-structural-market-deficit/). Five consecutive years of structural supply deficit.
- **USGS silver imports**: [Mineral Commodity Summaries 2025](https://pubs.usgs.gov/periodicals/mcs2025/mns2025-silver.pdf). US imports 67% of silver supply.
- **Domestic institutional holdings**: FRED Financial Accounts Q4 2024. $8.7 trillion in Treasuries.
- **UK gilt crisis**: Bank of England, September 2022. LDI-driven forced selling, 100+ bps in 4 days.
- **Debt structure**: TreasuryDirect maturity buckets. 33% rolls within one year, 37% within five years.
- **Fiscal dominance theory**: Leeper, E., "Equilibria under 'active' and 'passive' monetary and fiscal policies," Journal of Monetary Economics, 27(1), 129-147, 1991.
- **Garrett's constant**: Garrett, T. J., "No way out? The double-bind in seeking global prosperity alongside mitigated climate change," Earth Syst. Dynam., 3, 1-17, 2012. Lambda = 9.7 +/- 0.3 mW per 1990 USD.
- **Cox critique**: Cox et al., "Emergent constraint on equilibrium climate sensitivity from global temperature variability," Nature, 553, 319-322, 2018.
- **Pakistan labour force**: Pakistan Bureau of Statistics, Labour Force Survey 2023-24. ~70% informal.
- **Israel tech emigration**: Israeli Central Bureau of Statistics via Calcalist. 8,300 workers since October 2023.

Parameters marked ASSUMPTION in `config.py` are explicitly labeled. Change any assumption and rerun.

## Limitations

This is a structural stress test, not a forecast. It identifies which levers produce how much pressure, at what cost, in which geographies. It does not predict timing. The model will be wrong in ways not yet identified. The difference between a model that earns trust and one that claims truth is whether the author names the assumptions before the reader has to.

## Tools

Model code and documentation built with assistance from Claude (Anthropic).

## License

MIT
