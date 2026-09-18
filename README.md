# <img src="streamlit_app/assets/hungary_flag.png" alt="Hungarian flag" height="30"> Hungary Population Monitor

An automated ETL pipeline and Streamlit dashboard that tracks Hungary's
settlement-level population from official government statistics — how
fast the population is shrinking, and which counties and settlements are
absorbing the loss.

**Live demo:** https://hungary-population-monitor.streamlit.app

## What it does

Hungary's national statistics office publishes yearly settlement-level
population counts as scattered Excel files. This project:

1. **Collects** those files automatically, plus a reference dataset of
   settlement coordinates from GeoNames.
2. **Transforms** them into a clean, validated, analysis-ready shape —
   reconciling naming inconsistencies, settlement mergers/splits, and
   county reassignments across years.
3. **Loads** the result into a small star-schema SQLite database.
4. **Serves** it through a multi-page Streamlit app that tells the story
   of the decline in two parts — the national trend over time, then the
   specific counties and settlements gaining or losing the most — plus a
   settlement explorer and notable administrative/demographic facts.

## The app

The sidebar groups the pages into **The Argument** (the two-part story)
and **Explore It Yourself** (tools for poking at the data).

| Page | What it shows |
|---|---|
| 📉 **Overview** *(Part 1: The Decline)* | National population trend, headline KPIs (latest population, % change, CAGR), a "decline yardstick" translating the latest yearly loss into the size of a named settlement, and the growth-vs-decline breakdown: a total waterfall plus a year-by-year view. |
| 📊 **Winners & Losers** *(Part 2)* | County- and settlement-level maps with a color-mode toggle (relative to the national trend, percent change, or absolute headcount) and a sortable leaderboard of the biggest gainers and losers. |
| 🔎 **Explorer** | Look up any settlement (defaults to Budapest) and see its population summary and national rank, male/female composition over time, and male-to-female ratio. |
| 💡 **Fun Facts** | Newly independent settlements, county/type reassignments, mergers, and gender-ratio extremes — a year-by-year timeline of administrative change. |

## Architecture

```
data/raw/                  Downloaded source files (Excel, GeoNames dump)
data/geo/                  Hungary county & settlement boundary GeoJSON (OSM)
data/database/             SQLite database produced by the pipeline (committed,
                           so the deployed app needs no pipeline run)

src/hpm/
├── settings.py            Central path configuration
├── etl/
│   ├── data_collection/   Scrape & download population Excel files + GeoNames data
│   ├── transform/         Clean, validate, and build the star schema
│   ├── load/              Persist the star schema to SQLite
│   └── pipeline.py        Orchestrates collection → transform → load
├── semantics/             SQL views defining the canonical analytical dataset
├── bootstrap/             One-time setup (materializes semantic views)
├── db/                    Thin SQLite connection/query layer
├── analysis/              Pure pandas/numpy analysis functions, grouped by domain:
│                          overview, change, facts, settlements, geography, datasets
├── ui/context.py          Page-context builders that wire analysis functions to the UI
└── cli.py                 `hpm` console entrypoint (runs the full pipeline)

streamlit_app/
├── app.py                 Entrypoint, grouped page navigation, favicon & page config
├── shared.py              Cached data loading and map color constants shared across pages
├── assets/                Favicon (Hungarian tricolor)
└── pages/                 One file per page (rendering only; logic lives in hpm.ui.context)

notebooks/data_profile/    Exploratory notebooks profiling and validating the raw data
scripts/                   One-off/manual scripts (fetch boundaries, simplify GeoJSON, etc.)
```

The pipeline follows a **star schema**: `dim_county` and `dim_settlement`
(enriched with GeoNames coordinates via a tiered name/county matching
strategy) surround a `fact_population` table keyed by settlement and
year. A semantic SQL view (`population_settlements`) sits on top,
synthesizing Budapest as a single entity from its 23 capital-district
rows, and is the single canonical source the analysis layer reads from.

The analysis layer is deliberately UI-agnostic — every module under
`src/hpm/analysis/` is pure pandas/numpy taking DataFrames in and out.
`src/hpm/ui/context.py` builds typed, cached, per-page context objects
on top of it, and the Streamlit pages under `streamlit_app/pages/` only
render — they contain no analysis logic.

## Data sources

- **Population**: [kormany.hu — Lakossági számadatok](https://kormany.hu/nyilvantartasok/statisztika/lakossagi-szamadatok) (Hungarian government statistics)
- **Settlement coordinates**: [GeoNames HU dump](https://download.geonames.org/export/dump/HU.zip)
- **Boundary geometry**: OpenStreetMap relations (county & settlement boundaries), fetched via [polygons.openstreetmap.fr](http://polygons.openstreetmap.fr)

## Getting started

```bash
pip install -e .

# Run the full ETL pipeline (download sources, transform, build the DB)
hpm

# Launch the dashboard
streamlit run streamlit_app/app.py
```

Requires Python ≥ 3.11. See [pyproject.toml](pyproject.toml) for pinned
dependencies.

### Deployment

The app is deployed on Streamlit Community Cloud from `streamlit_app/app.py`.
Community Cloud's `pyproject.toml` support only reliably handles Poetry
projects, so a one-line [requirements.txt](requirements.txt) (`-e .`)
installs the package and its dependencies via plain pip instead, without
duplicating the version pins. The pre-built SQLite database and simplified
GeoJSON are committed, so no ETL runs at deploy time.

## Development

Exploratory/validation notebooks live in `notebooks/data_profile/` and
are exported to static HTML in `docs/notebooks/` via
`scripts/export_notebooks.ps1`. Geometry sources are fetched and
simplified once with the scripts in `scripts/` and committed under
`data/geo/` rather than regenerated at runtime.
