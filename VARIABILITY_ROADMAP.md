# Variability & Realism Roadmap

Notes from model review session, Feb 2026.
Goal: evolve the model from a conservative envelope calculation to a credible system design tool.

---

## Current model: what it actually computes

The model answers: "Given 500 GWc solar + current nuclear/hydro, with no wind, no multi-day storage, and no demand flexibility, how much gas backup is needed?"

Answer: **114 TWh/year**. This is intentionally conservative.

The 60-slot resolution (12 months x 5 daily slots) uses monthly averages, which hides intra-month variability and tail-risk scenarios entirely.

---

## Three big physics gaps (in order of impact)

### 1. No seasonal / multi-day storage

The model forbids the system from carrying surplus across days or months. Each period stands alone. In reality:
- Daily battery cycling connects daytime surplus to nighttime deficit
- Pumped hydro (STEP) bridges multi-day gaps
- Even without hydrogen, 10-50 GWh of storage cuts winter peak gas by 10-30%

The storage module calculates daily peak surplus/deficit but never accumulates across time. This is the single largest distortion: probably +30-50 TWh of unnecessary gas.

### 2. No wind production

Wind is anti-correlated with solar seasonally (winter storms when solar is weakest). France has 30-50 GW of realistic potential. Excluding it biases the gas figure upward by 15-25 TWh and prevents meaningful system optimization.

### 3. No demand flexibility

All consumption is rigid. In reality:
- V2G from 30M+ EVs = 50-100 GWh distributed storage
- Industrial load shifting: 20-30% of industry can move +/-2-6 hours
- Smart heating: pre-heat during cheap solar, coast through evening peak
- Impact: -10 to -15 TWh gas

---

## Structural issues

### Temperature correlations are broken
- Cold winter = high heating demand AND low solar production (double hit) -- not correlated in the model
- Hot summer = PV efficiency loss (~0.5%/C above 25C) AND nuclear cooling shutdowns (2022: -20 GW) -- not modeled

### Monthly averages hide tail risk
- A 3-day January anticyclone (-10C, no sun, low wind) creates a 72h deficit invisible in monthly averages
- A single cloudy December week may dominate the annual gas need
- Worst January day is 2-3x the average January day in power demand

### Gas efficiency assumed at 100%
`Gas_TWh = max(0, deficit) * duration` implies 1 TWh gas in = 1 TWh electricity out. Real CCGT runs at 55-60% efficiency. Actual fuel consumption is ~1.7x what the model reports.

### No reserve margin
Real grids maintain 10-15% spinning reserve. The model allows 0 MW margin.

---

## Proposed architecture: Python engine + ODS summary

### The tension
The current ODS is valuable because a decision-maker can tweak a knob and watch results update (live formulas). But weather variability requires many runs, which can't be done in spreadsheet formulas.

### Solution: two-layer model

```
Python engine (hourly, multi-year)
  |-- For each knob combination:
  |     |-- Run against 10-20 historical weather years
  |     |-- Hourly production x consumption balance
  |     |-- Track daily/weekly storage state
  |     |-- Accumulate annual gas deficit
  |-- Compute P10, P25, P50, P75, P90 of gas backup
  |-- Export summary to ODS

ODS output
  |-- parametres sheet (same 142 knobs, still the source of truth)
  |-- resultats sheet: decile columns showing range of outcomes
  |-- moulinette_simplifiee kept as "median year" reference view
```

The knobs still live in the ODS. But instead of LibreOffice formulas recomputing, you re-run the Python engine when parameters change, and it writes fresh deciles.

### What the model should say
Not "114 TWh" but: **"70-160 TWh depending on the weather year, median 110 TWh."**

---

## What "variability" means concretely

Three layers of variability to capture:

1. **Intra-day solar**: cloudy Tuesday vs sunny Wednesday in January. A week of fog in December needs 3x the gas of an average December week.

2. **Inter-annual weather**: 2022 (drought + heat wave) vs 2023 (mild winter). Gas backup swings 50-80 TWh between years.

3. **Cold snap coincidence**: 5 days of -10C, no sun, low hydro, all at once. This is the scenario that sizes the gas fleet -- monthly averages make it invisible.

---

## Data requirements

The multi-year approach needs hourly historical data:

- **RTE eco2mix**: hourly production (nuclear, hydro) -- available via API, multiple years
- **PVGIS**: hourly irradiance for reference French locations -- available via API
- **Meteo France**: hourly temperatures for heating demand calculation

If 10+ years of hourly data available: multi-year run is straightforward.
If only monthly averages: would need synthetic variability, which gets speculative.

**First step**: inventory what hourly data we can actually pull from existing APIs.

---

## Corrections the current model could absorb immediately

These don't require the hourly engine and could be added to the existing 60-slot model:

| Fix | Difficulty | Impact |
|-----|-----------|--------|
| CCGT efficiency (divide gas by 0.55) | Trivial | Shows real fuel need (~190 TWh) |
| Reserve margin (add 15% to consumption) | Trivial | +15 TWh gas |
| Actual days per month (not fixed 30) | Easy | +/-2-3% accuracy |
| Add wind column (monthly RTE data) | Medium | -15 to -25 TWh gas |
| V2G as negative demand in night slots | Medium | -10 TWh gas |

---

## What we decided NOT to pursue

- **Seasonal hydrogen storage**: too speculative at this stage. Unproven at scale, efficiency uncertain (round-trip 30-40% electricity-to-electricity). Could revisit if the hourly model shows summer curtailment is massive.

---

## Realistic range after corrections

- **With wind + storage + flexibility**: 30-60 TWh gas/year (optimistic but achievable)
- **Current model**: 114 TWh gas/year (conservative envelope)
- **With reserve margin + CCGT efficiency**: 150-200 TWh fuel/year (what gas infrastructure actually needs to supply)

The honest answer is a range, not a point estimate.
