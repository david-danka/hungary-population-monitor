from dataclasses import dataclass

# ChangeParams and read_change_params removed — Winners & Losers no longer
# threads user input through context; all its widgets are local to page.py.
# OverviewParams/GeographyParams left as-is for now, pending the same treatment.


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


def read_overview_params() -> OverviewParams:
    """The only place that touches st.* widgets for this page."""
    # e.g. top_n = st.sidebar.slider("Top N", 5, 50, 20)
    return OverviewParams()


def read_geography_params() -> GeographyParams:
    """The only place that touches st.* widgets for the Geography page."""
    return GeographyParams()
