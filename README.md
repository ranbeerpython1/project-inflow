# Project Inflow

A Python 3.11+ reference implementation for synthetic bank-statement ingestion, reconciliation, transaction categorisation and explainable underwriting features.

## Architecture

```text
Synthetic exports (CSV / XLSX / fixed-width TXT)
        -> content-based parser detection
        -> canonical transaction schema (Decimal money)
        -> per-account reconciliation + duplicate checks
        -> rules / LLM-provider abstraction / hybrid categorisation
        -> explainable cash-flow features + review gate
```

## Setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e '.[test]'
```

## Run the pipeline

```bash
python -m inflow.generate --seed 42 --out data/
python -m inflow.normalise data/ --out out/
python -m inflow.check_truth data/ out/
python -m inflow.categorise out/ --provider fake
python -m inflow.eval --provider fake
python -m inflow.features out/ --out out/features.json
pytest -q
```

## Design decisions

- All monetary arithmetic uses `Decimal`; no float arithmetic is used in reconciliation or feature calculations.
- Parsers are selected from file contents (XLSX ZIP signature, CSV preamble, or printable statement header), not filename extension.
- Reconciliation checks running balance equations and duplicate transaction signatures. A failed statement must not be treated as ready by the feature gate.
- The LLM is isolated behind `LLMProvider`; the deterministic fake keeps tests offline. Six-or-more-digit runs are masked before provider calls.
- Features retain source transaction IDs for salary, EMI and bounce evidence.

## Results

Run the commands above to generate seed-specific metrics and `out/features.json`. The fake provider is deterministic and is not a substitute for a real model evaluation. Do not claim performance numbers from synthetic labels as production performance.

## Limitations / next steps

- Extend fixtures with adversarial bank layouts, robust XLSX date/Cr-Dr cases, and multi-page fixed-width statements.
- Add provider-specific JSON schema validation and a real-provider adapter selected by environment variable.
- Add calibrated confidence thresholds, stratified labelled data and independent human-reviewed evaluation.
- Add FastAPI endpoints, structured logs, role-based access and encrypted storage only after core correctness is established.

## Security

Synthetic data only. Never commit real customer statements, API keys, account numbers or secrets.

## Verified seed-42 run (local environment)

The following results were measured by running the commands in this repository:

- `check_truth`: **396 / 396 rows matched (100.00%)** on date, amount, balance and description.
- Reconciliation: ACC001 and ACC002 failed as expected due to injected dropped/duplicate rows; ACC003–ACC006 passed with no issues.
- Feature review gate: ACC001 and ACC002 are `needs_review` with `reconciliation_failed`; ACC003–ACC006 are `ready`.
- Offline test suite: **15 tests passed**.
- Labelled evaluation set: 180 examples, including 84 `hard=true` examples.

| Categoriser | Overall accuracy | Overall macro-F1 | Hard accuracy | Hard macro-F1 |
|---|---:|---:|---:|---:|
| Rules | 53.33% | 0.6967 | 0.00% | 0.0000 |
| Fake LLM | 95.56% | 0.9687 | 100.00% | 1.0000 |
| Hybrid | 100.00% | 1.0000 | 100.00% | 1.0000 |

Evaluation provider/model: deterministic `FakeLLMProvider`, model label `deterministic-rule-backed-fake-v1`; 8 batched calls in the evaluation run. These are synthetic benchmark results, not real-world model performance. The fake provider uses a broader deterministic mapping than the keyword rules, so it is an evaluation harness, not evidence of an external LLM's capability.

The hybrid threshold is 0.70: deterministic rules are used at or above the threshold; lower-confidence cases are sent to the provider. In this synthetic set, rules either match at 0.95 or fall below threshold at 0.35, so the hybrid routes hard cases to the fake provider.

Machine-readable run artifacts are retained under `reports/`.
