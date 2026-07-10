"""Context builders and data containers for the Streamlit app pages."""

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
from hpm.analysis.facts import (
    find_attribute_changes,
    find_appearance_events,
    least_populated,
    most_male_skewed,
    most_female_skewed,
    most_recent_new_settlement,
    most_recent_county_change,
    build_history,
)


@dataclass(frozen=True)
class AppData:
    """Container for the base dataset and the first/last observed years."""

    df: pd.DataFrame
    first_year: int
    last_year: int


def load_app_data() -> AppData:
    """Load the app's base dataset and derive the observation bounds.

    Returns:
        A populated AppData object containing the base DataFrame and the
        earliest/latest years in the data.
    """
    df = population_settlements()
    first_year, last_year = year_bounds(df)
    return AppData(df=df, first_year=first_year, last_year=last_year)


@dataclass(frozen=True)
class HeadlineMetrics:
    """Key headline metrics for the overview page."""

    latest: int
    previous: int
    first: int
    change: int
    change_pct: float
    cagr: float
    n_settlements: int


@dataclass
class OverviewPageContext:
    """Context object for the overview page and its derived indicators."""

    app: AppData
    metrics: HeadlineMetrics
    top_bottom_n: int
    top_n_settlements: int

    @cached_property
    def national_trend(self):
        """Return the yearly national population trend."""
        return national_population_by_year(self.app.df)

    @cached_property
    def settlements(self):
        """Return the settlement-level data for the latest year."""
        return settlements_by_year(self.app.df, self.app.last_year)

    @cached_property
    def settlement_type_mix(self):
        """Return the settlement type mix for the latest year."""
        return settlement_type_mix_by_year(self.app.df, self.app.last_year)

    @cached_property
    def settlement_rank(self):
        """Return the settlement rank-size distribution for the latest year."""
        return settlement_rank_size_by_year(self.app.df, self.app.last_year)

    @cached_property
    def largest_settlements(self):
        """Return the largest settlements for the latest year."""
        return largest_settlements_by_year(
            self.app.df, self.app.last_year, self.top_n_settlements
        )

    @cached_property
    def change_extremes(self) -> PopulationChangeExtremes:
        """Return the settlements with the largest gains and losses."""
        return population_change_extremes(
            self.app.df,
            self.app.first_year,
            self.app.last_year,
            self.top_bottom_n,
        )

    @cached_property
    def concentration_share(self) -> float:
        """Return the concentration share for the top settlements."""
        return concentration_share_by_year(
            self.app.df,
            self.app.last_year,
            self.top_n_settlements,
        )

    @cached_property
    def decline_yardstick(self) -> pd.Series:
        """Return the settlement closest to the observed decline magnitude."""
        return closest_settlement_by_population(
            self.app.df, self.app.last_year, abs(self.metrics.change)
        )


def build_overview_context(
    app: AppData, top_n_settlements: int, top_bottom_n: int
) -> OverviewPageContext:
    """Build the overview-page context from the base app data.

    Args:
        app: The loaded application data.
        top_n_settlements: Number of largest settlements to include in the
            concentration summary.
        top_bottom_n: Number of extreme gain/loss settlements to include.

    Returns:
        A fully populated overview page context.
    """
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
    """Context object for the geography page and related charts."""

    app: AppData
    concentration_n: int

    @cached_property
    def county_change(self) -> pd.DataFrame:
        """Return county-level population change percentages."""
        return county_population_change(
            self.app.df, self.app.first_year, self.app.last_year
        )

    @cached_property
    def county_geojson(self) -> dict:
        """Return the county boundary GeoJSON for mapping."""
        return county_boundaries()

    @cached_property
    def concentration_trend(self) -> pd.DataFrame:
        """Return the concentration trend of the largest settlements."""
        return concentration_share_trend(self.app.df, self.concentration_n)

    @cached_property
    def largest_settlement_dominance(self) -> pd.DataFrame:
        """Return how dominant each county's largest settlement is."""
        return largest_settlement_share_by_county(
            self.app.df, self.app.last_year
        )

    @cached_property
    def county_population_trend(self) -> pd.DataFrame:
        """Return the population trend for each county."""
        return county_population_trend(self.app.df)

    @cached_property
    def county_trend_indexed(self) -> pd.DataFrame:
        """Return the county trend indexed to the first year."""
        return index_to_first_year(self.county_population_trend, "county_name")

    @cached_property
    def lorenz(self) -> pd.DataFrame:
        """Return the Lorenz curve data for settlement inequality."""
        return lorenz_curve(self.app.df, self.app.last_year)

    @cached_property
    def gini_trend(self) -> pd.DataFrame:
        """Return the settlement Gini coefficient trend over time."""
        return settlement_gini_by_year(self.app.df)


def build_geography_context(
    app: AppData, concentration_n: int
) -> GeographyPageContext:
    """Build the geography-page context for the current app data.

    Args:
        app: The loaded application data.
        concentration_n: Number of largest settlements used in concentration
            analysis.

    Returns:
        A geography page context object.
    """
    return GeographyPageContext(app=app, concentration_n=concentration_n)


@dataclass
class ChangePageContext:
    """Context object for the winners-and-losers page."""

    app: AppData
    n_largest_losers: int

    @cached_property
    def change(self) -> pd.DataFrame:
        """Return settlement-level change data across the observation window."""
        return settlement_change(
            self.app.df,
            self.app.first_year,
            self.app.last_year,
        )

    @cached_property
    def direction_counts(self) -> dict[str, int]:
        """Return the counts of gaining versus declining settlements."""
        return count_by_direction(self.change)

    @cached_property
    def total_change_by_direction(self) -> pd.DataFrame:
        """Return a summary of total growth and decline by direction."""
        return total_change_by_direction(self.change)

    @cached_property
    def national_pct_change(self) -> float:
        """Return the national percentage change over the observation window."""
        first = national_population_at(self.app.df, self.app.first_year)
        last = national_population_at(self.app.df, self.app.last_year)
        return percent_change(first, last)

    @cached_property
    def change_with_category(self) -> pd.DataFrame:
        """Return settlement changes annotated with relative category labels."""
        return relative_change_category(self.change, self.national_pct_change)

    @cached_property
    def yearly_totals(self) -> pd.DataFrame:
        """Return yearly totals for growth, decline, and net change."""
        return yearly_change_totals(self.app.df)

    @cached_property
    def decline_contribution(self) -> float:
        """Return the share of total loss explained by the largest losers."""
        return national_decline_contribution(
            self.change, self.n_largest_losers
        )


def build_change_context(
    app: AppData, n_largest_losers: int
) -> ChangePageContext:
    """Build the change-page context for the current app data.

    Args:
        app: The loaded application data.
        n_largest_losers: Number of largest declining settlements to include.

    Returns:
        A change page context object.
    """
    return ChangePageContext(app=app, n_largest_losers=n_largest_losers)


@dataclass
class ExplorerPageContext:
    """Context object for the settlement explorer page."""

    app: AppData

    @cached_property
    def options(self) -> pd.DataFrame:
        """Return the settlement selection options for the explorer."""
        return settlement_options(self.app.df)

    def series(self, settlement_name: str) -> pd.DataFrame:
        """Return the yearly population series for one settlement.

        Args:
            settlement_name: The settlement to retrieve.

        Returns:
            A DataFrame with the requested settlement's yearly series.
        """
        return settlement_series(self.app.df, settlement_name)

    def summary(self, settlement_name: str) -> SettlementSummary:
        """Return a summary object for one settlement.

        Args:
            settlement_name: The settlement to summarize.

        Returns:
            A structured summary object with change and rank details.
        """
        return settlement_summary(
            self.app.df,
            settlement_name,
            self.app.first_year,
            self.app.last_year,
        )

    def gender_ratio(self, settlement_name: str) -> pd.DataFrame:
        """Return the gender-ratio series for one settlement.

        Args:
            settlement_name: The settlement to analyze.

        Returns:
            A DataFrame with the male-to-female ratio by year.
        """
        return gender_ratio_series(self.app.df, settlement_name)


def build_explorer_context(app: AppData) -> ExplorerPageContext:
    """Build the explorer-page context from the base app data.

    Args:
        app: The loaded application data.

    Returns:
        An explorer page context object.
    """
    return ExplorerPageContext(app=app)


@dataclass
class FactsPageContext:
    """Context object for the fun-facts page."""

    app: AppData
    min_pop_for_gender_ratio: int

    @cached_property
    def appearance_events(self) -> tuple[pd.Series, pd.Series]:
        """Return the appearance and disappearance events in the dataset."""
        return find_appearance_events(self.app.df)

    @cached_property
    def appeared(self) -> pd.Series:
        """Return the settlements that appeared in the dataset."""
        return self.appearance_events[0]

    @cached_property
    def disappeared(self) -> pd.Series:
        """Return the settlements that disappeared from the dataset."""
        return self.appearance_events[1]

    @cached_property
    def county_changes(self) -> pd.DataFrame:
        """Return county reassignment events for settlements."""
        return find_attribute_changes(self.app.df, "county_name")

    @cached_property
    def type_changes(self) -> pd.DataFrame:
        """Return settlement-type reclassification events."""
        return find_attribute_changes(self.app.df, "settlement_type")

    @cached_property
    def history(self) -> dict[int, dict]:
        """Return the combined history of appearance and change events."""
        return build_history(
            self.appeared, self.county_changes, self.type_changes
        )

    @cached_property
    def most_male_skewed_settlement(self) -> pd.Series:
        """Return the most male-skewed settlement for the latest year."""
        return most_male_skewed(
            self.app.df,
            self.app.last_year,
            min_pop=self.min_pop_for_gender_ratio,
        )

    @cached_property
    def most_female_skewed_settlement(self) -> pd.Series:
        """Return the most female-skewed settlement for the latest year."""
        return most_female_skewed(
            self.app.df,
            self.app.last_year,
            min_pop=self.min_pop_for_gender_ratio,
        )

    @cached_property
    def smallest_settlement_first_year(self) -> pd.Series:
        """Return the smallest settlement in the first observed year."""
        return least_populated(self.app.df, self.app.first_year)

    @cached_property
    def smallest_settlement_last_year(self) -> pd.Series:
        """Return the smallest settlement in the last observed year."""
        return least_populated(self.app.df, self.app.last_year)

    @cached_property
    def newest_settlement(self) -> tuple[str, int] | None:
        """Return the most recently created settlement, if any."""
        return most_recent_new_settlement(self.appeared)

    @cached_property
    def latest_county_change(self) -> pd.Series | None:
        """Return the most recent county reassignment event, if any."""
        return most_recent_county_change(self.county_changes)


def build_facts_context(
    app: AppData, min_pop_for_gender_ratio: int
) -> FactsPageContext:
    """Build the facts-page context from the base app data.

    Args:
        app: The loaded application data.
        min_pop_for_gender_ratio: Minimum population cutoff for gender-ratio
            highlights.

    Returns:
        A facts page context object.
    """
    return FactsPageContext(
        app=app, min_pop_for_gender_ratio=min_pop_for_gender_ratio
    )
