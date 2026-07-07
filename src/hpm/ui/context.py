from dataclasses import dataclass
from functools import cached_property
import pandas as pd

from hpm.analysis.datasets import population_settlements
from hpm.analysis.overview import (
    year_bounds,
    population_at,
    pct_change,
    cagr,
    count_settlements,
    national_timeseries,
    rank_size_by_year,
    settlement_mix_by_year,
    county_population_by_year,
    top_settlements,
    absolutes,
    RankedChanges,
)
from hpm.ui.selectors import OverviewParams


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
    def national_ts(self):
        return national_timeseries(self.df)

    @cached_property
    def county_pop(self):
        return county_population_by_year(self.df, self.last_year)

    @cached_property
    def settlement_mix(self):
        return settlement_mix_by_year(self.df, self.last_year)

    @cached_property
    def rank_size(self):
        return rank_size_by_year(self.df, self.last_year)

    @cached_property
    def top_settlements(self):
        return top_settlements(
            self.df, self.last_year, self.params.top_n_settlements
        )

    @cached_property
    def absolutes(self) -> RankedChanges:
        return absolutes(
            self.df, self.first_year, self.last_year, self.params.top_bottom_n
        )


def load_overview_context(params: OverviewParams) -> OverviewPageContext:
    df = population_settlements()
    first_year, last_year = year_bounds(df)

    latest = population_at(df, last_year)
    previous = population_at(df, last_year - 1)
    first = population_at(df, first_year)

    metrics = HeadlineMetrics(
        latest=latest,
        previous=previous,
        first=first,
        change=latest - previous,
        change_pct=pct_change(first, latest),
        cagr=cagr(first, latest, last_year - first_year),
        n_settlements=count_settlements(df),
    )

    return OverviewPageContext(
        df=df,
        first_year=first_year,
        last_year=last_year,
        metrics=metrics,
        params=params,
    )
