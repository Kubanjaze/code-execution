# Phase 69 — Claude with Code Execution Tool (Local Pattern)

**Version:** 1.2 | **Tier:** Standard | **Date:** 2026-03-27

## Goal
Demonstrate a code execution pattern where Claude generates Python/RDKit code in response to a chemistry question, and the code is executed locally to produce results. Simulates the server-side code execution tool pattern.

CLI: `python main.py --input data/compounds.csv --question "Calculate the mean molecular weight per scaffold family"`

Outputs: code_execution_results.json

## Logic
- Send a chemistry question + available modules context to Claude
- Ask Claude to respond with executable Python code (RDKit + pandas) in a code block
- Extract code from markdown ```python``` blocks
- Execute in a sandboxed environment with restricted `__import__` (only rdkit, pandas, numpy)
- Capture stdout output and return as result

## Key Concepts
- Claude generates executable code, not just text answers
- Code extraction: parse ```python ... ``` blocks from response
- Sandboxed `exec()`: custom `safe_import` only allows pre-approved modules
- Pre-loaded variables: `df` (compound DataFrame), `Chem`, `Descriptors`, `rdMolDescriptors`
- Stdout capture via `io.StringIO` redirection

## Deviations from Plan
- Initial run failed: `__import__` not found in restricted builtins
- Fix: added `safe_import` function that whitelists rdkit/pandas/numpy imports

## Verification Checklist
- [x] Claude generates syntactically valid Python code
- [x] Code executes successfully in sandboxed environment
- [x] Output: MW per scaffold family (6 scaffolds computed)
- [x] One API call

## Results
| Metric | Value |
|--------|-------|
| Code generated | ~40 lines (valid Python) |
| Execution | SUCCESS |
| Scaffolds computed | 6 (benz=186.95, naph=224.31, ind=144.22, quin=156.23, pyr=105.68, bzim=145.55) |
| Input tokens | 111 |
| Output tokens | 578 |
| Est. cost | $0.0024 |

## Risks (resolved)
- Generated code may have syntax errors — not observed; Claude generated valid Python on first attempt
- Security: exec() must be restricted — mitigated by safe_import whitelist (only rdkit/pandas/numpy)
- __import__ not available in restricted builtins — fixed by adding safe_import function (v1.2 deviation)
- Generated code may import dangerous modules (os, sys, subprocess) — blocked by safe_import

Key finding: Claude generated correct RDKit code on first attempt, including Murcko scaffold decomposition and groupby aggregation. The safe_import sandboxing pattern works well for restricting module access.
