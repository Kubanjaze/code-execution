import sys
if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse, os, json, re, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from dotenv import load_dotenv
import anthropic

load_dotenv()
os.environ.setdefault("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))


def extract_code(text: str) -> str:
    """Extract Python code from markdown code blocks."""
    match = re.search(r'```python\s*\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: try any code block
    match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def execute_safe(code: str, compounds_csv: str) -> tuple[bool, str]:
    """Execute generated code in a restricted environment."""
    import io
    # Build safe globals with only allowed modules
    # Allow imports of pre-approved modules only
    ALLOWED_MODULES = {"pandas", "pd", "rdkit", "numpy", "math"}
    def safe_import(name, *args, **kwargs):
        if name.split(".")[0] in ALLOWED_MODULES or name.startswith("rdkit"):
            return __import__(name, *args, **kwargs)
        raise ImportError(f"Module '{name}' not allowed")

    safe_globals = {"__builtins__": {"print": print, "range": range, "len": len, "round": round,
                                     "sum": sum, "min": min, "max": max, "sorted": sorted,
                                     "enumerate": enumerate, "zip": zip, "list": list, "dict": dict,
                                     "str": str, "int": int, "float": float, "abs": abs,
                                     "__import__": safe_import, "None": None, "True": True, "False": False}}
    try:
        import pandas as pd
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors
        safe_globals["pd"] = pd
        safe_globals["Chem"] = Chem
        safe_globals["Descriptors"] = Descriptors
        safe_globals["rdMolDescriptors"] = rdMolDescriptors
        safe_globals["df"] = pd.read_csv(compounds_csv)
    except Exception as e:
        return False, f"Setup error: {e}"

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    try:
        exec(code, safe_globals)
        output = captured.getvalue()
        return True, output
    except Exception as e:
        return False, f"Execution error: {e}"
    finally:
        sys.stdout = old_stdout


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", required=True)
    parser.add_argument("--question", default="Calculate the mean molecular weight per scaffold family and print the results")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    client = anthropic.Anthropic()

    prompt = (
        "You have a pandas DataFrame `df` with columns: compound_name, smiles, pic50.\n"
        "You also have RDKit available: `Chem`, `Descriptors`, `rdMolDescriptors`.\n\n"
        f"Question: {args.question}\n\n"
        "Write Python code to answer this question. Use the pre-loaded `df` DataFrame.\n"
        "Use `print()` to output results. Wrap your code in a ```python``` code block."
    )

    print(f"\nPhase 69 — Code Execution")
    print(f"Model: {args.model}")
    print(f"Question: {args.question}\n")

    response = client.messages.create(model=args.model, max_tokens=1024, messages=[{"role": "user", "content": prompt}])
    text = "".join(b.text for b in response.content if hasattr(b, "text"))

    code = extract_code(text)
    print(f"Generated code:\n{'─'*40}\n{code}\n{'─'*40}\n")

    if not code:
        print("ERROR: No code block found in response")
        return

    success, output = execute_safe(code, args.input)
    status = "SUCCESS" if success else "FAILED"
    print(f"Execution: {status}")
    print(f"Output:\n{output}")

    usage = response.usage
    cost = (usage.input_tokens / 1e6 * 0.80) + (usage.output_tokens / 1e6 * 4.0)

    result = {
        "question": args.question, "model": args.model,
        "generated_code": code, "execution_success": success, "output": output,
        "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "cost": round(cost, 4),
    }
    with open(os.path.join(args.output_dir, "code_execution_results.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nTokens: in={usage.input_tokens} out={usage.output_tokens} | Cost: ${cost:.4f}")
    print("Done.")


if __name__ == "__main__":
    main()
