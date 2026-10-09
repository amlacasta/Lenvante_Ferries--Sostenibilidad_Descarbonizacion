"""Restore the synthetic voyage CSV from the compressed repository asset."""
from pathlib import Path
import gzip
import shutil

root = Path(__file__).resolve().parents[1]
source = root / "data" / "voyages_2026_synthetic.csv.gz"
target = source.with_suffix("")
with gzip.open(source, "rb") as compressed, target.open("wb") as csv_file:
    shutil.copyfileobj(compressed, csv_file)
print(f"Restored {target.relative_to(root)}")
