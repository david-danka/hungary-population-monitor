from dataclasses import dataclass


@dataclass(frozen=True)
class OverviewParams:
    top_n_settlements: int = 20
    top_bottom_n: int = 10

    def __post_init__(self):
        if self.top_n_settlements <= 0:
            raise ValueError("top_n_settlements must be positive")
        if self.top_bottom_n <= 0:
            raise ValueError("top_bottom_n must be positive")


@dataclass(frozen=True)
class GeographyParams:
    concentration_n: int = 10

    def __post_init__(self):
        if self.concentration_n <= 0:
            raise ValueError("concentration_n must be positive")


@dataclass(frozen=True)
class ChangeParams:
    min_baseline_pop: int
    n_leaderboard: int
    n_decline_contribution: int

    def __post_init__(self):
        if self.min_baseline_pop < 0:
            raise ValueError("min_baseline_pop must be non-negative")
        if self.n_leaderboard <= 0:
            raise ValueError("n_leaderboard must be positive")
        if self.n_decline_contribution <= 0:
            raise ValueError("n_decline_contribution must be positive")


def read_overview_params() -> OverviewParams:
    """The only place that touches st.* widgets for this page."""
    # e.g. top_n = st.sidebar.slider("Top N", 5, 50, 20)
    return OverviewParams()


def read_geography_params() -> GeographyParams:
    """The only place that touches st.* widgets for the Geography page."""
    return GeographyParams()

def read_change_params(
    *, default_min_baseline_pop: int, default_n_leaderboard: int, n_decline_contribution: int
) -> ChangeParams:
    """The only place that touches st.* widgets for this page."""
    min_baseline_pop = default_min_baseline_pop
    n_leaderboard = default_n_leaderboard
    return ChangeParams(
        min_baseline_pop=min_baseline_pop,
        n_leaderboard=n_leaderboard,
        n_decline_contribution=n_decline_contribution,
    )