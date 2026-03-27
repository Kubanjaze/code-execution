# Phase 69 — Claude with Code Execution Tool (Local Pattern)

**Version:** 1.0 | **Tier:** Standard | **Date:** 2026-03-27

## Goal
Demonstrate a code execution pattern where Claude generates Python/RDKit code in response to a chemistry question, and the code is executed locally to produce results. This simulates the server-side code execution tool pattern.

CLI: `python main.py --input data/compounds.csv --question "Calculate the mean molecular weight per scaffold family"`

Outputs: code_execution_results.json

## Logic
- Send a chemistry question + compound data to Claude
- Ask Claude to respond with executable Python code (RDKit + pandas)
- Extract the code block from Claude's response
- Execute the code in a sandboxed local environment (restricted globals)
- Capture stdout output and return it as the result
- Report: generated code, execution success/failure, output

## Key Concepts
- Claude generates executable code, not just text answers
- Code extraction: parse ```python ... ``` blocks from response
- Local execution: `exec()` with restricted globals (only safe modules)
- Sandboxing: only allow rdkit, pandas, numpy — no os, sys, subprocess
- Pattern mirrors Claude's server-side code execution tool

## Verification Checklist
- [ ] Claude generates syntactically valid Python code
- [ ] Code executes successfully with restricted globals
- [ ] Output matches expected computation
- [ ] One API call

## Risks
- Generated code may have syntax errors
- RDKit imports may be missing or wrong
- Security: exec() must be restricted to safe modules only
