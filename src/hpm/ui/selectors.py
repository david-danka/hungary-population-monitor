from dataclasses import dataclass


@dataclass(frozen=True)
class GeographyParams:
    concentration_n: int = 10

    def __post_init__(self):
        if self.concentration_n <= 0:
            raise ValueError("concentration_n must be positive")


def read_geography_params() -> GeographyParams:
    """The only place that touches st.* widgets for the Geography page."""
    return GeographyParams()
