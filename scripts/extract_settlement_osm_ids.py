"""One-off script: extract settlement_name -> OSM relation ID from the
OpenStreetMap wiki's Hungarian settlement PDF into a clean CSV.

Source PDF: https://wiki.openstreetmap.org/w/images/e/ed/Magyar_telepulesek.pdf

Run manually, not part of the ETL pipeline:
    pip install pdfplumber --break-system-packages
    python extract_settlement_osm_ids.py path/to/Magyar_telepulesek.pdf settlement_osm_ids.csv

This script could not be tested against the real PDF (network sandbox
does not allow fetching wiki.openstreetmap.org). It's written defensively:
it first tries pdfplumber's table extraction (works if the PDF has real
table structure), and falls back to line-based regex parsing (works if
each line is roughly "Settlement Name <whitespace> 123456"). Inspect the
printed sample after running -- you will likely need to tweak the regex
or column indices once you see the real layout.
"""

import csv
import re
import sys
from pathlib import Path

import pdfplumber

# Known gap in the source PDF (confirmed missing) -- add manually.
MANUAL_ADDITIONS = {
    "Balatonakarattya": "3854416",
}

# Fallback line pattern: settlement name, then whitespace, then a
# multi-digit OSM relation ID at the end of the line. Adjust if the
# actual PDF interleaves extra columns (e.g. county name, population).
LINE_PATTERN = re.compile(r"^(?P<name>.+?)\s+(?P<osm_id>\d{4,9})\s*$")


def extract_via_tables(pdf_path: Path) -> list[tuple[str, str]]:
    """Tries pdfplumber's structured table extraction first."""
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if row is None or len(row) < 2:
                        continue
                    name, osm_id = row[0], row[-1]
                    if name and osm_id and osm_id.strip().isdigit():
                        rows.append((name.strip(), osm_id.strip()))
    return rows


def extract_via_text_lines(pdf_path: Path) -> list[tuple[str, str]]:
    """Fallback: parse raw extracted text line by line with LINE_PATTERN."""
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                match = LINE_PATTERN.match(line.strip())
                if match:
                    rows.append((match.group("name"), match.group("osm_id")))
    return rows


def main():
    if len(sys.argv) != 3:
        print("Usage: python extract_settlement_osm_ids.py <input.pdf> <output.csv>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    rows = extract_via_tables(pdf_path)
    method = "table extraction"

    if not rows:
        rows = extract_via_text_lines(pdf_path)
        method = "text-line regex fallback"

    if not rows:
        print(
            "No rows extracted via either method. Open the PDF and check "
            "its actual layout -- you'll need to adjust LINE_PATTERN or "
            "the table-column indices in this script."
        )
        sys.exit(1)

    print(f"Extracted {len(rows)} rows via {method}. Sample of first 10:")
    for name, osm_id in rows[:10]:
        print(f"  {name!r} -> {osm_id}")

    seen = {name: osm_id for name, osm_id in rows}
    seen.update(MANUAL_ADDITIONS)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["settlement_name", "osm_relation_id"])
        for name, osm_id in sorted(seen.items()):
            writer.writerow([name, osm_id])

    print(f"\nWrote {len(seen)} settlement -> OSM ID pairs to {output_path}")
    print(
        "IMPORTANT: eyeball the output CSV before trusting it -- PDF table "
        "extraction is fragile, and this was not verified against the "
        "actual file. Cross-check row count against Hungary's known "
        "settlement count (~3,150) and spot-check a handful of names "
        "against dim_settlement.settlement_name for spelling/accent match."
    )


if __name__ == "__main__":
    main()