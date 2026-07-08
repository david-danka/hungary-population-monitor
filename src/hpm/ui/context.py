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
)
from hpm.ui.selectors import OverviewParams, GeographyParams


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
    df: pd.DataFrame
    first_year: int
    last_year: int
    metrics: HeadlineMetrics
    params: OverviewParams

    @cached_property
    def national_trend(self):
        return national_population_by_year(self.df)

    @cached_property
    def settlements(self):
        return settlements_by_year(self.df, self.last_year)

    @cached_property
    def settlement_type_mix(self):
        return settlement_type_mix_by_year(self.df, self.last_year)

    @cached_property
    def settlement_rank(self):
        return settlement_rank_size_by_year(self.df, self.last_year)

    @cached_property
    def largest_settlements(self):
        return largest_settlements_by_year(
            self.df, self.last_year, self.params.top_n_settlements
        )

    @cached_property
    def change_extremes(self) -> PopulationChangeExtremes:
        return population_change_extremes(
            self.df, self.first_year, self.last_year, self.params.top_bottom_n
        )

    def concentration_share(self, n: int) -> float:
        return concentration_share_by_year(self.df, self.last_year, n)

    @cached_property
    def decline_yardstick(self) -> pd.Series:
        return closest_settlement_by_population(
            self.df, self.last_year, abs(self.metrics.change)
        )


def load_overview_context(params: OverviewParams) -> OverviewPageContext:
    df = population_settlements()
    first_year, last_year = year_bounds(df)

    latest = national_population_at(df, last_year)
    previous = national_population_at(df, last_year - 1)
    first = national_population_at(df, first_year)

    metrics = HeadlineMetrics(
        latest=latest,
        previous=previous,
        first=first,
        change=latest - previous,
        change_pct=percent_change(first, latest),
        cagr=compound_annual_growth_rate(
            first, latest, last_year - first_year
        ),
        n_settlements=settlement_count(df),
    )

    return OverviewPageContext(
        df=df,
        first_year=first_year,
        last_year=last_year,
        metrics=metrics,
        params=params,
    )


@dataclass
class GeographyPageContext:
    df: pd.DataFrame
    first_year: int
    last_year: int
    params: GeographyParams

    @cached_property
    def county_change(self) -> pd.DataFrame:
        return county_population_change(self.df, self.first_year, self.last_year)

    @cached_property
    def county_geojson(self) -> dict:
        return county_boundaries()

    @cached_property
    def concentration_trend(self) -> pd.DataFrame:
        return concentration_share_trend(self.df, self.params.concentration_n)

    @cached_property
    def largest_settlement_dominance(self) -> pd.DataFrame:
        return largest_settlement_share_by_county(self.df, self.last_year)


def load_geography_context(params: GeographyParams) -> GeographyPageContext:
    df = population_settlements()
    first_year, last_year = year_bounds(df)
    return GeographyPageContext(
        df=df, first_year=first_year, last_year=last_year, params=params
    )
