# Energy Model - Claude Code Instructions

## Project Overview

This is a **French energy transition simulation model** that evaluates backup energy requirements (natural gas) for a scenario with 500-1000 GWc of solar PV capacity replacing fossil fuels for heating and transport.

**Key result**: ~114 TWh/year of backup gas needed with 500 GWc solar. Economic optimum at 700 GWc + 122 GWh storage (€550B over 30 years).

## Repository Structure

```
energy_model/
├── france_energy_transition.ipynb  # Main simulation (Jupyter notebook)
├── MODEL.md                        # Detailed model documentation
├── main.py                         # Entry point (placeholder)
├── pyproject.toml                  # Python dependencies (uv)
├── bilan_energetique_mensuel.csv   # Detailed monthly energy balance
├── resume_par_mois.csv             # Monthly summary
├── *.png                           # Visualization outputs
└── index.html                      # Static export
```

**Parent directory** (`../`) contains:
- `modélisation générale.ods` - Original spreadsheet model (17 sheets)
- `email_transcript_roland_transition_ecologique.md` - Project context/requirements

## Development

### Setup
```bash
uv sync
uv run jupyter lab france_energy_transition.ipynb
```

### Dependencies
- Python 3.13+
- pandas, numpy, matplotlib
- jupyter, ipykernel
- odfpy (for reading ODS files)

## Model Characteristics

### Production Assumptions
- **Solar PV**: 500 GWc baseline (200 GWc residential, 50 GWc collective, 250 GWc centralized)
- **Nuclear**: Current levels maintained (~30-50 GW)
- **Hydro**: Current levels maintained (~5-10 GW)
- **Wind**: NOT included (conservative assumption)

### Consumption Assumptions
- **Heating**: Electrified via heat pumps (COP=2)
- **Transport**: Electrified (×0.4 freight, ×0.2 passengers)
- **Industry/Tertiary**: Current levels maintained

### Temporal Granularity
- 12 months × 5 time slots per day = 60 periods
- Time slots: 8h-13h, 13h-18h, 18h-20h, 20h-23h, 23h-8h

## Key Findings

| Metric | Value |
|--------|-------|
| Backup gas (500 GWc) | 114 TWh/year |
| Economic optimum | 700 GWc + 122 GWh storage |
| 30-year cost (optimum) | €550B |
| Zero-gas threshold | 950 GWc + 128 GWh storage |

## Model Limitations

- No inter-seasonal storage (batteries, STEP, hydrogen)
- No European interconnections
- No demand flexibility or V2G
- Wind production ignored (conservative)

## Collaboration Context

This project supports work on a professional energy planning tool for French policymakers. The goal is an auditable, transparent model that:
1. Establishes physical feasibility of target scenario
2. Makes assumptions explicit and verifiable
3. Enables cost optimization and sensitivity analysis

## Coding Standards

- **Language**: French comments/documentation acceptable, code in English
- **Notebook**: Keep cells focused, include visualizations with interpretations
- **Data**: Export results to CSV for auditability
- **Sources**: Document all data sources (RTE, ADEME, PVGIS, etc.)

## Issue Tracking

This project uses **beads** (`bd`) for issue tracking. See `../AGENTS.md` for workflow.
