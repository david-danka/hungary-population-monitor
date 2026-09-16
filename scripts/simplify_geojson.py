import geopandas as gpd
import topojson as tp
from pathlib import Path


def simplify_topojson(path: Path, eps: float) -> None:
    gdf = gpd.read_file(path)

    # Builds shared-arc topology, then simplifies each shared arc once --
    # neighboring settlements stay seamlessly joined, no independent drift.
    topo = tp.Topology(gdf, prequantize=False)
    simplified = topo.toposimplify(eps).to_gdf()

    suffixed_path = path.parent / (path.stem + "_topo_simplified" + path.suffix)
    simplified.to_file(suffixed_path, driver="GeoJSON")

if __name__ == "__main__":
    county_geojson_path = Path(r"data/geo/hungary_counties.geojson")
    settlement_geojson_path = Path(r"data/geo/hungary_settlements.geojson")
    simplify_topojson(county_geojson_path, 0.001)
    simplify_topojson(settlement_geojson_path, 0.005)