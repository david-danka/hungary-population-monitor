from dataclasses import dataclass
from functools import cached_property
import pandas as pd

from hpm.analysis.datasets import population_settlements, county_boundaries
from hpm.analysis.overview import (
    year_bounds,
    national_population_at,
    percent_change,
    compound_annual_growth_rate,
    settlement_count,
    national_population_by_year,
    settlements_by_year,
    settlement_rank_size_by_year,
    settlement_type_mix_by_year,
    largest_settlements_by_year,
    population_change_extremes,
    concentration_share_by_year,
    closest_settlement_by_population,
    PopulationChangeExtremes,
)
from hpm.analysis.geography import (
    county_population_change,
    concentration_share_trend,
    largest_settlement_share_by_county,
    county_population_trend,
    index_to_first_year,
    lorenz_curve,
    settlement_gini_by_year,
)
from hpm.analysis.change import (
    settlement_change,
    national_decline_contribution,
    count_by_direction,
    total_change_by_direction,
    relative_change_category,
    yearly_change_totals,
)
from hpm.analysis.settlements import (
    settlement_options,
    settlement_series,
    settlement_summary,
    gender_ratio_series,
    SettlementSummary,
)


@dataclass(frozen=True)
class AppData:
    """
    The one raw dataset every page's context is built from.
    """

    df: pd.DataFrame
    first_year: int
    last_year: int


def load_app_data() -> AppData:
    df = population_settlements()
    first_year, last_year = year_bounds(df)
    return AppData(df=df, first_year=first_year, last_year=last_year)


@dataclass(frozen=True)
class HeadlineMetrics:
    latest: int
    previous: int
    first: int
    change: int
    change_pct: float
    cagr: float
    n_settlements: int


@dataclass
class OverviewPageContext:
    app: AppData
    metrics: HeadlineMetrics
    top_bottom_n: int
    top_n_settlements: int

    @cached_property
    def national_trend(self):
        return national_population_by_year(self.app.df)

    @cached_property
    def settlements(self):
        return settlements_by_year(self.app.df, self.app.last_year)

    @cached_property
    def settlement_type_mix(self):
        return settlement_type_mix_by_year(self.app.df, self.app.last_year)

    @cached_property
    def settlement_rank(self):
        return settlement_rank_size_by_year(self.app.df, self.app.last_year)

    @cached_property
    def largest_settlements(self):
        return largest_settlements_by_year(
            self.app.df, self.app.last_year, self.top_n_settlements
        )

    @cached_property
    def change_extremes(self) -> PopulationChangeExtremes:
        return population_change_extremes(
            self.app.df,
            self.app.first_year,
            self.app.last_year,
            self.top_bottom_n,
        )

    @cached_property
    def concentration_share(self) -> float:
        return concentration_share_by_year(
            self.app.df,
            self.app.last_year,
            self.top_n_settlements,
        )

    @cached_property
    def decline_yardstick(self) -> pd.Series:
        return closest_settlement_by_population(
            self.app.df, self.app.last_year, abs(self.metrics.change)
        )


def build_overview_context(
    app: AppData, top_n_settlements: int, top_bottom_n: int
) -> OverviewPageContext:
    latest = national_population_at(app.df, app.last_year)
    previous = national_population_at(app.df, app.last_year - 1)
    first = national_population_at(app.df, app.first_year)

    metrics = HeadlineMetrics(
        latest=latest,
        previous=previous,
        first=first,
        change=latest - previous,
        change_pct=percent_change(first, latest),
        cagr=compound_annual_growth_rate(
            first, latest, app.last_year - app.first_year
        ),
        n_settlements=settlement_count(app.df),
    )

    return OverviewPageContext(
        app=app,
        metrics=metrics,
        top_n_settlements=top_n_settlements,
        top_bottom_n=top_bottom_n,
    )


@dataclass
class GeographyPageContext:
    app: AppData
    concentration_n: int

    @cached_property
    def county_change(self) -> pd.DataFrame:
        return county_population_change(
            self.app.df, self.app.first_year, self.app.last_year
        )

    @cached_property
    def county_geojson(self) -> dict:
        return county_boundaries()

    @cached_property
    def concentration_trend(self) -> pd.DataFrame:
        return concentration_share_trend(self.app.df, self.concentration_n)

    @cached_property
    def largest_settlement_dominance(self) -> pd.DataFrame:
        return largest_settlement_share_by_county(
            self.app.df, self.app.last_year
        )
    
    @cached_property
    def county_population_trend(self) -> pd.DataFrame:
        return county_population_trend(self.app.df)
    
    @cached_property
    def county_trend_indexed(self) -> pd.DataFrame:
        return index_to_first_year(self.county_population_trend, "county_name")
    
    @cached_property
    def lorenz(self) -> pd.DataFrame:
        return lorenz_curve(self.app.df, self.app.last_year)

    @cached_property
    def gini_trend(self) -> pd.DataFrame:
        return settlement_gini_by_year(self.app.df)


def build_geography_context(
    app: AppData, concentration_n: int
) -> GeographyPageContext:
    return GeographyPageContext(app=app, concentration_n=concentration_n)


@dataclass
class ChangePageContext:
    """No params — every property here is the full, unfiltered answer.
    Widgets that slice/filter (min_baseline_pop, row counts, ranking metric,
    population range) live in page.py as local st.* calls over these."""

    app: AppData
    n_largest_losers: int

    @cached_property
    def change(self) -> pd.DataFrame:
        return settlement_change(
            self.app.df,
            self.app.first_year,
            self.app.last_year,
        )

    @cached_property
    def direction_counts(self) -> dict[str, int]:
        return count_by_direction(self.change)

    @cached_property
    def total_change_by_direction(self) -> pd.DataFrame:
        return total_change_by_direction(self.change)

    @cached_property
    def national_pct_change(self) -> float:
        first = national_population_at(self.app.df, self.app.first_year)
        last = national_population_at(self.app.df, self.app.last_year)
        return percent_change(first, last)

    @cached_property
    def change_with_category(self) -> pd.DataFrame:
        return relative_change_category(self.change, self.national_pct_change)

    @cached_property
    def yearly_totals(self) -> pd.DataFrame:
        return yearly_change_totals(self.app.df)

    @cached_property
    def decline_contribution(self) -> float:
        return national_decline_contribution(
            self.change, self.n_largest_losers
        )


def build_change_context(
    app: AppData, n_largest_losers: int
) -> ChangePageContext:
    return ChangePageContext(app=app, n_largest_losers=n_largest_losers)


@dataclass
class ExplorerPageContext:
    """No params — settlement_name is a per-call argument, not baked into
    context, since it changes on every selectbox interaction and there's
    nothing expensive to protect by caching per-settlement."""

    app: AppData

    @cached_property
    def options(self) -> pd.DataFrame:
        return settlement_options(self.app.df)

    def series(self, settlement_name: str) -> pd.DataFrame:
        return settlement_series(self.app.df, settlement_name)

    def summary(self, settlement_name: str) -> SettlementSummary:
        return settlement_summary(
            self.app.df,
            settlement_name,
            self.app.first_year,
            self.app.last_year,
        )
    
    def gender_ratio(self, settlement_name: str) -> pd.DataFrame:
        return gender_ratio_series(self.app.df, settlement_name)


def build_explorer_context(app: AppData) -> ExplorerPageContext:
    return ExplorerPageContext(app=app)
