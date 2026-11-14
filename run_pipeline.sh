#!/usr/bin/env bash
set -euo pipefail
python -m inflow.generate --seed 42 --out data/
python -m inflow.normalise data/ --out out/
python -m inflow.check_truth data/ out/
python -m inflow.categorise out/ --provider fake
python -m inflow.eval --provider fake
python -m inflow.features out/ --out out/features.json
pytest -q
