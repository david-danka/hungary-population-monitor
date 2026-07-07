from hpm.semantics.loader import create_views


def prepare():
    """
    Prepare the analytical environment.

    Ensures all semantic objects required by the analysis
    layer exist.
    """
    create_views()