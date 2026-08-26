# 🇭🇺 Hungary Population Monitor

An automated ETL pipeline and Streamlit dashboard that tracks Hungary's
settlement-level population from official government statistics — where
the population is shrinking, where it's concentrating, and which
settlements are the biggest winners and losers.

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
   of the decline: the national trend, where it concentrates
   geographically, which settlements are gaining or losing the most, and
   notable administrative/demographic facts along the way.

## The app

| Page | What it shows |
|---|---|
| 🇭🇺 **Overview** | National population trend, headline KPIs (latest population, % change, CAGR), settlement-concentration teaser, and an interactive map of settlements sized by population. |
| 🧭 **Geography** | County-level choropleth of population change, share of population held by the largest settlements over time, county-seat dominance, county population trends, and inequality metrics (Lorenz curve, Gini coefficient). |
| 📊 **Winners & Losers** | Growth vs. decline waterfall and year-by-year breakdown, a sortable leaderboard of the biggest gainers/losers, and a map colored by performance relative to the national trend. |
| 🔎 **Explorer** | Look up any settlement and see its own population history, growth vs. the national baseline, and male/female ratio over time. |
| 🔎 **Fun Facts** | Newly independent settlements, county/type reassignments, mergers, and gender-ratio extremes — a year-by-year timeline of administrative change. |

## Architecture

```
data/raw/            Downloaded source files (Excel, GeoNames dump)
data/geo/             Hungary county & settlement boundary GeoJSON (OSM)
data/database/        SQLite database produced by the pipeline

src/hpm/
├── settings.py       Central path configuration
├── etl/
│   ├── data_collection/  Scrape & download population Excel files + GeoNames data
│   ├── transform/        Clean, validate, and build the star schema
│   ├── load/              Persist the star schema to SQLite
│   └── pipeline.py        Orchestrates collection → transform → load
├── semantics/         SQL views defining the canonical analytical dataset
├── bootstrap/          One-time setup (materializes semantic views)
├── db/                 Thin SQLite connection/query layer
├── analysis/            Pure pandas/numpy analysis functions, one module per page:
│                        overview, geography, change, facts, settlements, datasets
├── ui/context.py      Page-context builders that wire analysis functions to the UI
└── cli.py              `hpm` console entrypoint (runs the full pipeline)

streamlit_app/
├── app.py              Entrypoint & page navigation
├── shared.py            Cached, shared data loading across pages
└── pages/                One file per page (rendering only; logic lives in hpm.ui.context)

notebooks/data_profile/  Exploratory notebooks profiling and validating the raw data
scripts/                  One-off/manual scripts (fetch boundaries, simplify GeoJSON, etc.)
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

## Development

Exploratory/validation notebooks live in `notebooks/data_profile/` and
are exported to static HTML in `docs/notebooks/` via
`scripts/export_notebooks.ps1`. Geometry sources are fetched and
simplified once with the scripts in `scripts/` and committed under
`data/geo/` rather than regenerated at runtime.
