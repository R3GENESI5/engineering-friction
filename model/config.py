"""
Clock 3 Model V2 - Configuration
All parameters, distributions, and assumptions in one place.
Every number has a source or is labeled ASSUMPTION.
"""

import numpy as np

# ============================================================
# MONTE CARLO
# ============================================================
N_ITERATIONS = 10_000
RNG_SEED = 42
MODEL_HORIZON_YEARS = 5  # FIX 3: explicit time dimension

# ============================================================
# DEBT ISSUANCE GROWTH (FIX 7: missing channel)
# ============================================================
# US adds ~$2T/year in new debt. Over 5 years, $29.6T -> ~$39.6T.
# This increases the denominator but also the interest burden.
ANNUAL_DEFICIT_GROWTH_T = {
    'min': 1.5,    # modest (some fiscal restraint)
    'mode': 2.0,   # current trajectory (CBO baseline)
    'max': 3.0,    # war spending + recession + no cuts
}

# ============================================================
# POLICY RESPONSE DAMPING (FIX 4)
# ============================================================
# When pressure exceeds X% of headroom, US deploys countermeasures:
# rate cuts, bilateral deals, sanctions threats, fiscal adjustment.
# Modeled as: if pressure/headroom > trigger, reduce pressure by damping_pct.
POLICY_RESPONSE = {
    'trigger_pct': 40,  # policy mobilizes when 40%+ of headroom consumed
    'damping_pct': {
        'min': 5,       # weak response (political gridlock, slow Fed)
        'mode': 15,     # moderate (rate cut + bilateral deals)
        'max': 30,      # strong (coordinated fiscal + monetary + diplomatic)
    },
    # Probability that response actually materializes
    'response_probability': {
        'min': 0.40,    # low (political dysfunction)
        'mode': 0.65,   # moderate
        'max': 0.85,    # high (existential threat galvanizes response)
    },
}

# ============================================================
# US FISCAL STRUCTURE (sources inline)
# ============================================================
GROSS_DEBT_T = 38.8          # Treasury Dept, Feb 2026
DEBT_HELD_PUBLIC_T = 29.6    # CRFB, Aug 2025
FEDERAL_REVENUE_T = 5.1      # Derived: $970B interest / 19% of revenue
CURRENT_AVG_RATE_PCT = 3.355 # TreasuryDirect, Feb 2026
ANNUAL_INTEREST_B = 970      # FY2025 actual

# Maturity structure (TreasuryDirect, Dec 2025)
MATURES_WITHIN_1YR_PCT = 33  # ~$9.8T rolls over annually
AVG_MATURITY_MONTHS = 70     # 5.8 years average
# Breakdown estimate (Treasury Bulletin + FRED maturity tables):
MATURITY_BUCKETS = {
    '0-1yr': 0.33,
    '1-5yr': 0.37,
    '5-10yr': 0.18,
    '10+yr': 0.12,
}

# Crisis threshold: interest-to-revenue ratio
# Historical precedents:
#   Argentina pre-default: ~50%
#   Italy 2011 stress: ~25-30%
#   US current: 19%
# ASSUMPTION: crisis zone begins at 30-35%, hard default risk at 45%+
CRISIS_RATIO_DISTRIBUTION = {
    'min': 0.28,     # optimistic: system cracks at 28%
    'mode': 0.33,    # central: 33% (Italy-level stress)
    'max': 0.42,     # pessimistic: system holds to 42% (Argentina-level)
}

# ============================================================
# MONETARY VELOCITY DATA (FRED M2V, hardcoded quarterly)
# Source: FRED series M2V, GS10
# ============================================================
# Full dataset in regression.py - key reference points here
M2V_CURRENT = 1.39           # FRED M2V, 2025Q2
M2V_PEAK = 2.19              # 1997 historical high
M2V_TROUGH = 1.13            # 2020 pandemic low
GS10_CURRENT = 4.3           # Approx late 2025

# Regime break dates (for regime-switching model)
# ASSUMPTION: calibrated from visual inspection + Chow test
REGIME_BREAKS = {
    'pre_volcker_end': '1979Q4',
    'great_moderation_start': '1985Q1',
    'gfc': '2008Q4',
    'qe_end': '2014Q4',
    'pandemic_qe_start': '2020Q1',
    'qt_start': '2022Q2',
}

# ============================================================
# GEOGRAPHY-SPECIFIC WITHDRAWAL PARAMETERS
# ============================================================
GEOGRAPHIES = {
    'Pakistan': {
        'gdp_T': 0.37,
        'population_M': 240,
        'informal_pct_gdp': 59,     # IPRI 2025
        'grid_dependency_pct': 35,
        'treasury_holdings_B': 3,
        'dollar_imports_B_yr': 55,
        'fx_reserves_usd_B': 8,
        'cost_per_hh_usd': 500,
        'primary_clock': 'clock2',
        'time_to_scale_yr': (3, 5),
        'policy_friction': {'min': 0.05, 'mode': 0.15, 'max': 0.30},
        'survival_5yr': {'min': 0.45, 'mode': 0.65, 'max': 0.80},
        # FIX 5: geography-specific withdrawal rate
        # High: food inflation, sanctions exposure, strong informal networks
        'withdrawal_pct': {'min': 0.08, 'mode': 0.15, 'max': 0.25},
    },
    'India': {
        'gdp_T': 3.9,
        'population_M': 1450,
        'informal_pct_gdp': 52,     # ILO est.
        'grid_dependency_pct': 40,
        'treasury_holdings_B': 240,
        'dollar_imports_B_yr': 350,
        'fx_reserves_usd_B': 450,
        'cost_per_hh_usd': 800,
        'primary_clock': 'clock2',
        'time_to_scale_yr': (3, 5),
        'policy_friction': {'min': 0.10, 'mode': 0.25, 'max': 0.40},
        'survival_5yr': {'min': 0.50, 'mode': 0.68, 'max': 0.82},
        # Moderate: $53B non-dollar oil trade already active, strong rural base
        'withdrawal_pct': {'min': 0.05, 'mode': 0.10, 'max': 0.18},
    },
    'Sub-Saharan Africa': {
        'gdp_T': 1.9,
        'population_M': 1200,
        'informal_pct_gdp': 38,     # World Bank avg
        'grid_dependency_pct': 25,
        'treasury_holdings_B': 10,
        'dollar_imports_B_yr': 200,
        'fx_reserves_usd_B': 50,
        'cost_per_hh_usd': 600,
        'primary_clock': 'clock2',
        'time_to_scale_yr': (5, 8),
        'policy_friction': {'min': 0.05, 'mode': 0.12, 'max': 0.25},
        'survival_5yr': {'min': 0.35, 'mode': 0.55, 'max': 0.75},
        # High: already low grid dependency, food price sensitivity, BRICS pull
        'withdrawal_pct': {'min': 0.06, 'mode': 0.12, 'max': 0.22},
    },
    'China': {
        'gdp_T': 18.5,
        'population_M': 1425,
        'informal_pct_gdp': 12,     # World Economics est.
        'grid_dependency_pct': 75,
        'treasury_holdings_B': 760,
        'dollar_imports_B_yr': 600,
        'fx_reserves_usd_B': 800,
        'cost_per_hh_usd': 5000,
        'primary_clock': 'clock1_2',
        'time_to_scale_yr': (5, 8),
        'policy_friction': {'min': 0.30, 'mode': 0.50, 'max': 0.70},
        'survival_5yr': {'min': 0.55, 'mode': 0.72, 'max': 0.85},
        # Low household withdrawal (state-directed economy), but state-level action is high
        'withdrawal_pct': {'min': 0.01, 'mode': 0.03, 'max': 0.08},
    },
    'Europe': {
        'gdp_T': 18.0,
        'population_M': 450,
        'informal_pct_gdp': 15,     # World Economics est.
        'grid_dependency_pct': 90,
        'treasury_holdings_B': 2500,
        'dollar_imports_B_yr': 1200,
        'fx_reserves_usd_B': 1500,
        'cost_per_hh_usd': 12000,
        'primary_clock': 'clock2',
        'time_to_scale_yr': (10, 15),
        'policy_friction': {'min': 0.25, 'mode': 0.45, 'max': 0.65},
        'survival_5yr': {'min': 0.65, 'mode': 0.80, 'max': 0.90},
        # Low: high grid dependency, high cost, but some degrowth/local food movements
        'withdrawal_pct': {'min': 0.01, 'mode': 0.03, 'max': 0.07},
    },
    'Gulf States': {
        'gdp_T': 2.1,
        'population_M': 60,
        'informal_pct_gdp': 8,      # World Economics est.
        'grid_dependency_pct': 85,
        'treasury_holdings_B': 300,
        'dollar_imports_B_yr': 250,
        'fx_reserves_usd_B': 400,
        'cost_per_hh_usd': 10000,
        'primary_clock': 'clock2',
        'time_to_scale_yr': (10, 15),
        'policy_friction': {'min': 0.40, 'mode': 0.60, 'max': 0.80},
        'survival_5yr': {'min': 0.60, 'mode': 0.75, 'max': 0.88},
        # Very low household withdrawal (state provides), but sovereign action is captured elsewhere
        'withdrawal_pct': {'min': 0.01, 'mode': 0.02, 'max': 0.05},
    },
    'USA': {
        'gdp_T': 29.8,             # BEA Q4 2025
        'population_M': 335,
        'informal_pct_gdp': 8,      # World Economics est.
        'grid_dependency_pct': 95,
        'treasury_holdings_B': 0,    # domestic, not foreign holder
        'dollar_imports_B_yr': 0,    # domestic
        'fx_reserves_usd_B': 0,     # domestic
        'cost_per_hh_usd': 15000,
        'primary_clock': 'clock3',
        'time_to_scale_yr': (10, 15),
        'policy_friction': {'min': 0.20, 'mode': 0.40, 'max': 0.60},
        'survival_5yr': {'min': 0.65, 'mode': 0.78, 'max': 0.90},
        # Very low: high cost, high grid dependency, but homesteading/prepper growth
        'withdrawal_pct': {'min': 0.01, 'mode': 0.03, 'max': 0.06},
        # US-specific
        'total_households_M': 131,   # Census Bureau
        'household_consumption_pct_gdp': 68,  # BEA PCE share
        'avg_reducible_spend_usd': 22000,
        'self_sufficiency_capture_pct': 70,
        'tax_loss_per_hh_usd': 5000,
    },
}

# ============================================================
# YCC FEEDBACK LOOP COEFFICIENTS
# ============================================================
# Fed balance sheet expansion to CPI (12-18 month lag)
# Source: QE1-3 and pandemic QE data
# Pandemic: $4.8T expansion -> ~6% CPI overshoot above 2% baseline
# QE1-3: $3.5T combined -> ~1% temporary CPI bump
# ASSUMPTION: nonlinear. Small expansion absorbed into reserves.
# Coefficient: CPI_overshoot = alpha * (expansion / threshold)^beta
YCC_PARAMS = {
    'balance_sheet_to_cpi': {
        'alpha': {'min': 0.8, 'mode': 1.25, 'max': 2.0},    # % CPI per $1T
        'lag_quarters': {'min': 4, 'mode': 6, 'max': 8},     # 12-24 months
        'absorption_threshold_T': 1.0,  # first $1T absorbed into reserves
    },
    # CPI to informal economy growth
    # Source: Lebanon 2019-2022: ~130% avg inflation -> 8pp informal growth (3 yr)
    # Argentina 2018-2023: ~70% avg inflation -> informal >50% (already high base)
    # ASSUMPTION: coefficient applies above a pain threshold
    'cpi_to_informal': {
        'pain_threshold_pct': 5.0,     # below 5% CPI, no meaningful exit
        'coefficient': {'min': 0.03, 'mode': 0.06, 'max': 0.10},  # pp informal per 1% CPI above threshold
    },
    # Damping: inflation boosts nominal GDP, improving debt-to-GDP ratio
    'nominal_gdp_boost_per_cpi_pct': 0.7,  # 1% CPI -> ~0.7% nominal GDP (imperfect passthrough)
}

# ============================================================
# CLOCK 1: SILVER SUBSTITUTION
# ============================================================
CLOCK1 = {
    'current_silver_per_cell_g': 0.08,     # Silver Institute
    'target_substitution_g': 0.02,          # Industry roadmap
    'solar_pct_industrial_ag_demand': 30,   # Silver Institute
    'substitution_timeline_yr': (5, 8),
    # Yield transmission: reduced silver demand -> reduced mining GDP
    # -> reduced dollar export revenue -> BoP channel
    # Top silver producers: Mexico ($5.6B), Peru ($3.2B), China ($3.8B)
    # Total silver mining revenue globally: ~$25B
    # 22.5% demand drop (from model) -> ~$5.6B revenue loss
    # -> roughly $2-4B reduced dollar flows -> 0.7-1.4 bps via BoP
    # Plus narrative effect on war-economy logic (unquantified)
    'yield_transmission_bps': {'min': 0.5, 'mode': 2.0, 'max': 5.0},
}

# ============================================================
# DEMAND ELASTICITY (FIX 1: replaces linear dollar-to-bps conversion)
# ============================================================
# The linear formula (pressure_B / debt_B * 10000) assumes each dollar
# of reduced Treasury demand produces proportional yield movement.
# Reality: depends on speed, market depth, and who else bids.
#
# Empirical anchors:
#   - UK gilt crisis 2022: ~$65B forced selling over days -> ~150 bps spike
#     implied elasticity: (150 / (65/2500*10000)) = ~5.8x
#   - Japan steady selling 2022-2024: ~$200B over 2 years -> ~0 bps movement
#     implied elasticity: ~0.0x (absorbed by domestic buyers)
#   - China selling 2016-2024: ~$350B over 8 years -> ~50 bps (uncertain attribution)
#     implied elasticity: ~0.3x
#
# Distribution reflects: gradual shifts absorbed (low), normal (mid), panic (high)
# ASSUMPTION: triangular distribution
DEMAND_ELASTICITY = {
    'min': 0.25,    # gradual shift, Fed/domestic absorb most
    'mode': 0.60,   # moderate: some market impact, some absorption
    'max': 2.50,    # sudden stop / panic selling (gilt crisis dynamics)
}

# ============================================================
# SILVER STRATEGIC SCISSORS (FIX 2: rebuilt Clock 1)
# ============================================================
# The US imports 64-70% of its silver (USGS MCS 2025).
# China controls 60-70% of global refining (SD Bullion 2025).
# China enacted export controls Jan 1, 2026.
# Silver added to US critical minerals list 2025.
# Market in structural deficit: 820M oz cumulative 2021-2025 (Silver Institute).
#
# Three transmission channels:
#   A. US defense/infrastructure cost inflation (silver price -> deficit -> headroom)
#   B. De-dollarization credibility multiplier (demonstrated supply chain control)
#   C. Supply disruption tail risk (rare-earths-style export ban)

SILVER_PARAMS = {
    # --- Channel A: Cost multiplier on US federal expenditure ---
    # Silver-intensive budget items (annual):
    #   Defense procurement: $170B (subset of $886B defense budget)
    #   Energy transition (IRA solar/grid): ~$50B/yr in silver-intensive projects
    #   AI/data center power infrastructure: ~$30B/yr growing
    # Estimated silver cost share of these programs: 1-4%
    # If silver price doubles (already happened 2024-2025), cost share rises
    'silver_sensitive_federal_spend_B': 250,  # defense + energy + AI infrastructure
    'silver_cost_share_pct': {
        'min': 0.8,
        'mode': 2.0,
        'max': 4.5,
    },
    'silver_price_increase_pct': {
        'min': 50,      # already realized (2024-2025 doubling)
        'mode': 120,    # continued deficit + export controls
        'max': 300,     # rare-earths-style spike if China restricts
    },

    # --- Channel B: De-dollarization credibility accelerant ---
    # China's demonstrated supply chain control makes BRICS alternatives more credible.
    # Modeled as a multiplier on de-dollarization channel parameters.
    # When a country sees China can choke US silver supply, joining mBridge
    # looks less like a gamble and more like insurance.
    'credibility_multiplier': {
        'min': 1.00,   # no effect (countries don't connect the dots)
        'mode': 1.15,  # modest acceleration of de-dollarization adoption
        'max': 1.35,   # significant (rare-earths precedent: countries hedged fast)
    },

    # --- Channel C: Supply disruption tail risk ---
    # Binary event: China restricts silver exports rare-earths-style
    # Probability per year given wartime conditions
    'disruption_prob_per_year': {
        'min': 0.05,    # 5%/yr: already have export controls, partial restriction
        'mode': 0.15,   # 15%/yr: wartime escalation makes full restriction plausible
        'max': 0.30,    # 30%/yr: active hostilities with Iran (China's oil supplier)
    },
    # If disruption occurs: immediate silver price spike
    'disruption_price_spike_pct': {
        'min': 200,     # 3x (rare earths spiked 10x, silver more liquid)
        'mode': 400,    # 5x
        'max': 800,     # 9x (approaches rare earth precedent)
    },
    # Fiscal shock from disruption: emergency procurement, stockpile costs, program delays
    'disruption_fiscal_shock_B': {
        'min': 15,      # modest: some programs delayed, costs absorbed
        'mode': 40,     # significant: defense procurement disrupted
        'max': 80,      # severe: multiple strategic programs stalled
    },

    # --- Silver substitution (original Clock 1, retained) ---
    'current_silver_per_cell_g': 0.08,     # Silver Institute
    'target_substitution_g': 0.02,          # Industry roadmap
    'solar_pct_industrial_ag_demand': 30,   # Silver Institute
    'substitution_timeline_yr': (5, 8),

    # --- US import dependency ---
    'us_import_dependency_pct': 67,         # USGS 2025: 64-70%, midpoint
    'china_refining_share_pct': 65,         # SD Bullion: 60-70%, midpoint
    'global_deficit_moz_yr': 95,            # Silver Institute 2025
    'cumulative_deficit_moz': 820,          # Silver Institute 2021-2025
}

# ============================================================
# OVERLAP CORRECTION
# ============================================================
# Method: for each geography, take max(sovereign_selling, bop_pressure)
# and add only marginal contribution of the smaller channel
OVERLAP_MARGINAL_FRACTION = {
    # What fraction of the smaller channel adds on top of the larger
    # ASSUMPTION: 30-50% additive (rest is correlated)
    'min': 0.20,
    'mode': 0.35,
    'max': 0.55,
}


# ============================================================
# REGIONAL CAPITAL FLIGHT (GAP 1)
# ============================================================
# War destabilizes the Middle East / Gulf. Private wealth flees the
# region to safer jurisdictions: London, Zurich, Istanbul, Delhi,
# Singapore. Transmission to Treasury yield pressure:
#   A. Gulf private capital currently IN US Treasuries gets pulled
#      and redeployed to non-dollar havens (direct selling pressure)
#   B. Petrodollar recycling collapses as Gulf wealth bypasses
#      the dollar system entirely (reduced demand for new issuance)
#   C. Flight destinations (London, Zurich, Singapore) absorb capital
#      in local-currency assets, reducing global dollar demand
#
# Scale of Gulf/ME private wealth (multiple sources):
#   - GCC sovereign wealth funds: ~$4T (SWF Institute, 2025)
#     ADIA $990B, PIF $930B, KIA $800B, QIA $520B, others
#   - GCC HNWI private wealth: ~$2.5T (Knight Frank, Capgemini 2024)
#   - Iranian diaspora capital: ~$300-500B (ASSUMPTION, scattered estimates)
#   - Lebanese diaspora / pre-crisis offshore: ~$50-100B
#   - Total addressable: ~$7T, of which roughly 30-40% in USD assets
#
# Precedent: Lebanon 2019-2020
#   - $10B+ pulled from Lebanese banks in months
#   - Wealth moved to Dubai, Zurich, London
#   - 90% of deposits above $100K effectively frozen
#   - Currency lost 98% of value
#
# Precedent: Russia 2022
#   - $250B+ frozen, but $50-80B moved before freeze (ASSUMPTION)
#   - Redirected to Dubai, Istanbul, Delhi
#   - Accelerated UAE/Turkey as financial hubs
#
# Precedent: Iran ongoing
#   - Estimated $200-300B in diaspora capital (various estimates)
#   - Concentrated in Dubai, Istanbul, London, Toronto
#   - hawala/informal channels handle ~$10-20B/yr (ASSUMPTION)

CAPITAL_FLIGHT = {
    # --- Source pool: Gulf + ME private wealth in USD assets ---
    # GCC private sector USD holdings (Treasuries, US equities, dollar deposits)
    # Gulf central bank reserves modeled separately in de-dollarization.
    # This is PRIVATE: family offices, HNWI, corporate treasuries.
    'gulf_private_usd_T': {
        'min': 1.5,     # conservative: only direct Treasury/bond holdings
        'mode': 2.5,    # central: includes dollar deposits and USD equities
        'max': 3.5,     # aggressive: includes indirect USD exposure via London
    },
    # Fraction that is in US Treasuries specifically (rest in equities, deposits, RE)
    'treasury_fraction': {
        'min': 0.20,    # diversified portfolios
        'mode': 0.35,   # Gulf preference for sovereign bonds (safety)
        'max': 0.50,    # concentrated in Treasuries (older wealth)
    },

    # --- Flight triggers and severity ---
    # War escalation probability is ALREADY given (this is the war model).
    # What varies: how much wealth moves, how fast, and where it goes.
    #
    # Flight percentage: share of Gulf private USD assets that relocate
    # per year of active regional conflict.
    'annual_flight_pct': {
        'min': 3,       # slow drip (war is contained, Gulf feels safe)
        'mode': 8,      # moderate (war spreads, Gulf hedges)
        'max': 18,      # panic (direct Gulf involvement, Strait of Hormuz)
    },

    # --- Destination split (where does the money go?) ---
    # Key: money going to London/Zurich PARTIALLY stays in dollar assets.
    # Money going to Istanbul/Delhi/Singapore mostly exits the dollar.
    # This matters because only the dollar-exit fraction creates Treasury pressure.
    'destinations': {
        'london': {
            'share_pct': {'min': 25, 'mode': 35, 'max': 45},
            'stays_in_usd_pct': 60,  # London: deep USD markets, partial dollar retention
        },
        'zurich': {
            'share_pct': {'min': 10, 'mode': 18, 'max': 25},
            'stays_in_usd_pct': 40,  # Swiss: CHF preference, but some USD kept
        },
        'istanbul': {
            'share_pct': {'min': 8, 'mode': 15, 'max': 22},
            'stays_in_usd_pct': 15,  # Turkey: TRY/EUR/gold preference, low USD retention
        },
        'delhi_mumbai': {
            'share_pct': {'min': 5, 'mode': 12, 'max': 20},
            'stays_in_usd_pct': 20,  # India: INR assets, some USD kept for trade
        },
        'singapore': {
            'share_pct': {'min': 8, 'mode': 15, 'max': 22},
            'stays_in_usd_pct': 45,  # Singapore: dollar-friendly but diversifying
        },
    },

    # --- Strait of Hormuz premium ---
    # If conflict closes or threatens the Strait, flight accelerates sharply.
    # ~21% of global oil transits the Strait. Closure = energy shock + Gulf panic.
    'hormuz_threat_prob_per_year': {
        'min': 0.05,    # low: Iran avoids escalation
        'mode': 0.12,   # moderate: brinkmanship, near-misses
        'max': 0.25,    # high: active naval confrontation
    },
    'hormuz_flight_multiplier': {
        'min': 1.5,     # modest acceleration
        'mode': 2.5,    # sharp acceleration (panic selling)
        'max': 4.0,     # full panic (2x Lebanon speed)
    },

    # --- Petrodollar recycling collapse ---
    # Gulf states currently recycle oil revenue into US Treasuries.
    # Capital flight breaks this loop: wealth leaves the region entirely,
    # reducing the pool of capital that would have been recycled.
    # This is ADDITIONAL to the sovereign de-dollarization channel,
    # which covers central bank decisions. This covers private recycling.
    'private_recycling_B_yr': {
        'min': 60,      # conservative (private sector contribution to recycling)
        'mode': 120,    # central
        'max': 200,     # aggressive (includes indirect flows)
    },
    'recycling_disruption_pct': {
        'min': 10,      # war has little effect on private recycling
        'mode': 30,     # moderate: Gulf families diversify away from USD
        'max': 55,      # severe: systematic exit from USD recycling
    },
}


# ============================================================
# DOMESTIC INSTITUTIONAL FLIGHT (GAP 2)
# ============================================================
# US pension funds, insurance companies, mutual funds, money market funds
# hold ~$7-8.7T in Treasuries (FRED Financial Accounts Q4 2024).
# More than China and Japan combined.
#
# These holders operate under REGULATORY MANDATES that create cliff behavior:
#   - Pension funds: LDI strategies, quarterly rebalancing, duration matching
#   - Insurance: NAIC risk-based capital adequacy triggers
#   - Money market funds: SEC Rule 2a-7 weekly liquid asset requirements
#   - Mutual funds: redemption-driven forced selling (retail panic)
#
# UK gilt crisis 2022 (Bank of England):
#   - Mini-budget triggered 100+ bps gilt yield spike in 4 days
#   - LDI funds forced to sell into falling market (margin/collateral spiral)
#   - LDI selling accounted for ~50% of gilt price decline
#   - BoE emergency intervention on day 5 stopped the cascade
#   - Pre-crisis LDI headroom: ~150 bps. Post-crisis mandated: 300 bps.
#
# US analogues:
#   - SVB cascade March 2023 (deposit flight triggered HTM portfolio losses)
#   - 2019 repo spike (overnight rate hit 10%, Fed intervened next day)
#   - 2020 Treasury dash-for-cash (even Treasuries sold in liquidity panic)
#   - 2011 S&P downgrade (brief spike, quickly absorbed)
#   - 2013 taper tantrum (100 bps over 4 months)
#
# Historical base rate: ~6 confidence events in 13 years across US/UK
# sovereign markets = ~0.46/yr. Not all trigger institutional flight.

DOMESTIC_INSTITUTIONAL = {
    'total_holdings_T': 8.7,  # FRED Financial Accounts Q4 2024

    'segments': {
        'money_market_mutual': {
            'holdings_T': 3.0,           # FRED, mostly T-bills
            'response_speed': 'fast',     # days (redemption-driven)
            'rebalance_pct': {            # pct of holdings sold in shock
                'min': 2, 'mode': 8, 'max': 20,
            },
        },
        'bond_mutual_funds': {
            'holdings_T': 2.5,
            'response_speed': 'fast',     # days-weeks (redemption-driven)
            'rebalance_pct': {
                'min': 3, 'mode': 10, 'max': 25,
            },
        },
        'pension_funds': {
            'holdings_T': 2.55,           # state/local + private
            'response_speed': 'slow',     # quarterly rebalancing
            'rebalance_pct': {
                'min': 1, 'mode': 5, 'max': 15,
                # UK gilt crisis: LDI leverage forced 10-20% liquidation
            },
        },
        'insurance': {
            'holdings_T': 0.65,
            'response_speed': 'medium',   # regulatory capital triggers
            'rebalance_pct': {
                'min': 2, 'mode': 6, 'max': 18,
            },
        },
    },

    # Confidence shock probability per year
    'shock_probability_per_year': {
        'min': 0.08,    # calm period, no catalyst
        'mode': 0.18,   # baseline: ~1 shock per 5-6 years
        'max': 0.35,    # wartime + fiscal stress = elevated
    },

    # Feedback multiplier: forced selling depresses prices,
    # which triggers more selling (LDI/margin spiral)
    'feedback_multiplier': {
        'min': 1.0,     # no cascade (absorbed by buyers)
        'mode': 1.4,    # moderate cascade
        'max': 2.0,     # full LDI-style spiral (gilt crisis dynamics)
    },
}


# ============================================================
# FISCAL DOMINANCE REGIME SHIFT (GAP 3)
# ============================================================
# Threshold effect, not a channel. Once interest payments consume enough
# revenue, rate hikes stop working because they increase the interest
# burden faster than they cool inflation. The central bank loses its
# primary tool.
#
# Theoretical basis: Leeper (1991) "Equilibria under 'Active' and
# 'Passive' Monetary and Fiscal Policies." When fiscal policy is
# "active" (deficits unconstrained), monetary policy must become
# "passive" (accommodate inflation) or the system destabilizes.
#
# Yellen flagged this publicly (2024): "I am concerned about the
# sustainability of the US fiscal path."
#
# CBO projection: net interest goes from 3.2% of GDP (2024) to
# 6.3% of GDP by 2054. But the nonlinear acceleration happens
# much sooner if rates stay elevated.
#
# Historical calibration:
#   - Brazil 2015: interest/revenue ~42%, rate hikes amplified crisis
#   - Turkey 2018: ~25%, Erdogan forced rate cuts, lira collapsed
#   - Japan ongoing: kept rates near zero for decades to avoid this
#   - Italy 2011: ~25-30%, ECB had to backstop
#   - US current: ~19% (FY2025)
#
# The regime switch: when interest/revenue exceeds threshold,
# policy_response damping FLIPS SIGN. Instead of reducing pressure
# by 15 bps, rate hikes ADD 10-30 bps of pressure (because higher
# rates immediately increase the interest burden on rolling debt).

FISCAL_DOMINANCE = {
    # Threshold: interest-to-revenue ratio at which regime shifts
    'threshold_ratio': {
        'min': 0.25,    # early shift (Turkey-like, political constraint)
        'mode': 0.33,   # central (Italy 2011 level, market forces action)
        'max': 0.42,    # late shift (system tolerates longer, Argentina-level)
    },

    # Current interest-to-revenue ratio
    'current_ratio': 0.19,  # FY2025: $970B / $5.1T

    # Annual ratio growth rate (driven by rolling debt at higher rates)
    # If avg rate rises from 3.35% to 5%, and debt grows $2T/yr:
    # Interest grows ~$150-200B/yr while revenue grows ~$100-150B/yr
    'annual_ratio_growth_pp': {
        'min': 1.5,     # optimistic: rates fall, revenue grows
        'mode': 2.5,    # central: rates stay elevated, deficit persists
        'max': 4.0,     # pessimistic: rates rise further, recession cuts revenue
    },

    # When fiscal dominance activates, rate hikes AMPLIFY pressure
    # instead of damping it. This replaces the policy_response damping.
    'amplification_bps': {
        'min': 8,       # mild: some fiscal adjustment offsets
        'mode': 20,     # moderate: each rate hike worsens deficit
        'max': 45,      # severe: debt spiral accelerates visibly
    },
}


# ============================================================
# ENERGY PRICE FEEDBACK (GAP 4)
# ============================================================
# War raises oil prices. Two-phase effect on Treasury yields:
#
# Phase 1 (0-12 months): DOLLAR SUPPORT
#   - Oil priced in dollars, buyers need more dollars
#   - Petrodollar inflows increase temporarily
#   - Treasury demand rises (flight to safety + recycling)
#   - Yield DECREASES by 5-15 bps
#
# Phase 2 (12-60 months): FISCAL DRAG
#   - Higher oil raises input costs across economy
#   - GDP growth slows (oil intensity of GDP: ~3.5% for US)
#   - Deficit widens (lower tax revenue + higher spending)
#   - Inflation rises, forcing rate hikes that increase debt burden
#   - Yield INCREASES by 10-40 bps
#
# Net over 5-year horizon: negative (more pressure than relief)
# But Phase 1 creates a false calm that masks building stress.
#
# Historical calibration (oil shock -> Treasury yield response):
#   1973 embargo: oil 4x. Yields +250 bps over 18 months (but inflation-driven)
#   1979 revolution: oil 2.5x. Yields +400 bps (Volcker tightening)
#   1990 Gulf War: oil +130%. Yields +50 bps then reversed (short war)
#   2008 spike: oil to $147. Yields collapsed (GFC overwhelmed oil effect)
#   2022 Russia: oil +60%. Yields +200 bps (but Fed tightening dominant)
#
# The interesting interaction: Phase 1 masks pressure long enough for
# debt self-feeding to consume additional headroom before repricing.

ENERGY_FEEDBACK = {
    # Oil price shock (% increase from pre-war baseline)
    'oil_price_increase_pct': {
        'min': 20,      # contained conflict, SPR releases
        'mode': 55,     # moderate escalation (2022 Russia-level)
        'max': 150,     # Hormuz closure, major supply disruption
    },

    # Phase 1: dollar support effect (negative = reduces pressure)
    'phase1_duration_months': 12,
    'phase1_relief_bps_per_10pct_oil': {
        'min': 0.3,     # weak dollar support
        'mode': 0.8,    # moderate
        'max': 1.5,     # strong petrodollar recycling boost
    },

    # Phase 2: fiscal drag effect (positive = increases pressure)
    'phase2_onset_months': 12,
    'phase2_drag_bps_per_10pct_oil': {
        'min': 0.5,     # modest GDP drag, some fiscal offset
        'mode': 1.8,    # moderate: deficit widens, inflation rises
        'max': 3.5,     # severe: stagflation, deficit spiral
    },

    # GDP drag coefficient: % GDP growth reduction per 10% oil price rise
    # Source: Hamilton (2003), Blanchard & Gali (2007)
    # Post-2000 estimate: ~0.15-0.25% GDP drag per 10% oil rise
    # ASSUMPTION: war scenario at higher end (supply shock, not demand-driven)
    'gdp_drag_per_10pct_oil': {
        'min': 0.10,
        'mode': 0.20,
        'max': 0.35,
    },

    # Deficit widening per 1% GDP drag
    # Rule of thumb: 1% GDP drop -> ~$50-60B wider deficit (CBO auto-stabilizers)
    'deficit_widening_B_per_1pct_gdp': {
        'min': 40,
        'mode': 55,
        'max': 75,
    },

    # Phase 1 masking effect: does the false calm allow debt self-feeding
    # to consume additional headroom before market reprices?
    # Model as: additional headroom consumed during masking period
    'masking_additional_headroom_erosion_bps': {
        'min': 3,       # market sees through it quickly
        'mode': 10,     # moderate: 12 months of false calm
        'max': 25,      # severe: market fully asleep during Phase 1
    },
}


# ============================================================
# ISRAEL TECH-DEFENSE PIPELINE (GAP 5)
# ============================================================
# US outsources significant defense innovation through Israel:
#   - Unit 8200 alumni feed into cybersecurity, AI, defense tech
#   - Israeli defense tech firms (Elbit, Rafael, IAI) supply US programs
#   - 8,300 tech workers emigrated from Israel since Oct 2023
#     (Israeli Central Bureau of Statistics, via Calcalist)
#
# Transmission: war continues -> emigration accelerates -> pipeline
# degrades -> US pays more for same capabilities (cost channel)
# or loses capabilities it cannot replace domestically (strategic).
#
# Cost channel: US-based defense engineers cost 2-3x Israeli ones
# for equivalent output (salary differentials + cluster effects).
# Partial replacement only: the Herzliya/Tel Aviv ecosystem has
# network effects that cannot be replicated by hiring individuals.
#
# Yield impact is small (2-5 bps) because it flows through the deficit.
# But it strengthens the "war becomes self-defeating" narrative.

ISRAEL_PIPELINE = {
    # Pre-war Israeli tech workforce in defense-adjacent roles
    'pre_war_workforce': 85000,  # ASSUMPTION: 8200 alumni + defense tech
    # based on Start-Up Nation Central data + IDF unit sizes

    # Emigration rate (% of defense-tech workforce per year of war)
    'annual_emigration_pct': {
        'min': 3,       # contained: reservist burden but economy holds
        'mode': 7,      # moderate: 8,300 in first year = ~10%, declining
        'max': 12,      # severe: prolonged war, brain drain accelerates
    },

    # US defense programs dependent on Israeli pipeline ($B/yr)
    # Iron Dome co-production, cybersecurity contracts, AI/ML defense,
    # electronic warfare, satellite/ISR technology
    'us_dependent_defense_spend_B': {
        'min': 15,      # narrow: direct co-production only
        'mode': 30,     # moderate: includes cybersecurity, AI contracts
        'max': 50,      # broad: includes indirect R&D pipeline effects
    },

    # Cost multiplier when replacing Israeli talent with domestic
    # Based on: US defense engineer avg $180K vs Israeli ~$80K (PPP-adjusted)
    # Plus cluster effect penalty: isolated hires less productive than ecosystem
    'replacement_cost_multiplier': {
        'min': 1.5,     # easy replacement (common skills)
        'mode': 2.2,    # moderate (specialized but replaceable)
        'max': 3.5,     # hard replacement (unique ecosystem capabilities)
    },

    # Fraction of emigration that is NOT replaced (capability gap)
    # Some roles simply cannot be filled: you can't hire the network
    'unreplaceable_fraction': {
        'min': 0.10,    # most roles filled eventually
        'mode': 0.25,   # quarter of capabilities degraded
        'max': 0.45,    # severe: half the pipeline hollow
    },

    # Program delay cost: unreplaced capabilities cause schedule slips
    # Each year of delay on a $10B program costs ~$1-2B (GAO typical)
    'delay_cost_multiplier': {
        'min': 0.08,    # minor delays
        'mode': 0.15,   # moderate schedule slips
        'max': 0.25,    # major program disruption
    },
}


def sample_triangular(rng, params):
    """Sample from triangular distribution given {min, mode, max}."""
    return rng.triangular(params['min'], params['mode'], params['max'])
