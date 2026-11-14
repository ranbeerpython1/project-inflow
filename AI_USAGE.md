# AI usage disclosure

AI assistance was used to scaffold modules, propose parser and pipeline structure, draft tests and documentation. The candidate must review, run, debug and understand every line before submission.

## Prompts / use
- Scaffold a Python package for synthetic bank statement parsing, reconciliation, categorisation and explainable features.
- Review Decimal money handling, source-line provenance, PII masking and offline tests.
- Generate an execution guide and identify gaps against the assignment's Done means criteria.

## Verification performed
Record the exact commands run, outputs, failures fixed and any remaining limitations here before submission. Do not state that tests passed unless they were run successfully in the final environment.

## Known areas requiring candidate review
- Parser edge cases and format detection need adversarial fixtures.
- Fake categorisation is deterministic and is not an independent model benchmark.
- Validate all output metrics and feature calculations against hand-computed examples before presenting them.
