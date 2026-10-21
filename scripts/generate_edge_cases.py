#!/usr/bin/env python3
"""Generate edge cases for all problems using reference solutions as oracles.

For each problem, generates 20-50 random valid inputs and uses the reference
solution to compute expected outputs. Stores results in scripts/extras/<topic>.json.
"""
from __future__ import annotations

import json
import random
import sys
import types
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from grind import problems
from grind.scheduler import bank

HERE = Path(__file__).parent
EXTRAS_DIR = HERE / "extras"
REFERENCES_DIR = HERE / "references"

random.seed(42)  # deterministic

# Type-specific generators based on problem signatures/constraints
GENERATORS = {}

def register(typename):
    def deco(fn):
        GENERATORS[typename] = fn
        return fn
    return deco

@register("list[int]")
def gen_list_int(constraints: dict = None) -> list[int]:
    n = random.randint(1, 20)
    if constraints and "length" in constraints:
        n = random.randint(constraints["length"][0], min(constraints["length"][1], 20))
    lo = -1000
    hi = 1000
    if constraints and "value_range" in constraints:
        lo, hi = constraints["value_range"]
    return [random.randint(lo, hi) for _ in range(n)]

@register("str")
def gen_str(constraints: dict = None) -> str:
    n = random.randint(1, 15)
    if constraints and "length" in constraints:
        n = random.randint(constraints["length"][0], min(constraints["length"][1], 15))
    alphabet = constraints.get("alphabet", "abcdefghijklmnopqrstuvwxyz")
    return "".join(random.choice(alphabet) for _ in range(n))

@register("int")
def gen_int(constraints: dict = None) -> int:
    lo, hi = -1000, 1000
    if constraints and "range" in constraints:
        lo, hi = constraints["range"]
    return random.randint(lo, hi)
@register("float")
def gen_float(constraints: dict = None) -> float:
    lo, hi = -100.0, 100.0
    if constraints and "range" in constraints:
        lo, hi = constraints["range"]
    return random.uniform(lo, hi)


@register("list[str]")
def gen_list_str(constraints: dict = None) -> list[str]:
    n = random.randint(1, 10)
    if constraints and "length" in constraints:
        n = random.randint(constraints["length"][0], min(constraints["length"][1], 10))
    return [gen_str(constraints) for _ in range(n)]

@register("list[list[int]]")
def gen_matrix_int(constraints: dict = None) -> list[list[int]]:
    rows = random.randint(1, 5)
    cols = random.randint(1, 5)
    if constraints and "dims" in constraints:
        rows = random.randint(constraints["dims"][0][0], min(constraints["dims"][0][1], 5))
        cols = random.randint(constraints["dims"][1][0], min(constraints["dims"][1][1], 5))
    lo, hi = -10, 10
    if constraints and "value_range" in constraints:
        lo, hi = constraints["value_range"]
    return [[random.randint(lo, hi) for _ in range(cols)] for _ in range(rows)]

@register("list[list[str]]")
def gen_matrix_str(constraints: dict = None) -> list[list[str]]:
    rows = random.randint(1, 4)
    cols = random.randint(1, 4)
    if constraints and "dims" in constraints:
        rows = random.randint(constraints["dims"][0][0], min(constraints["dims"][0][1], 4))
        cols = random.randint(constraints["dims"][1][0], min(constraints["dims"][1][1], 4))
    return [[gen_str(constraints) for _ in range(cols)] for _ in range(rows)]

@register("List[str]")
def gen_list_str_alias(constraints: dict = None) -> list[str]:
    return gen_list_str(constraints)


def infer_signature(entry: dict) -> tuple[list[tuple[str, str]], str]:
    """Extract parameter names and types from the starter code."""
    code = entry["python"]
    method_name = entry["method"]
    
    # Simple parsing to get parameter names and types
    # e.g., "def containsDuplicate(self, nums: list[int]) -> bool:"
    pattern = rf"def\s+{method_name}\s*\(self\s*,\s*([^)]+)\)\s*->\s*(\w+)"
    match = re.search(pattern, code)
    if not match:
        return [], "bool"
    
    params_str, ret_type = match.groups()
    params = []
    for p in params_str.split(","):
        p = p.strip()
        if ":" in p:
            name, typ = p.split(":")
            params.append((name.strip(), typ.strip()))
        else:
            params.append((p, "any"))
    return params, ret_type


def load_reference(slug: str):
    """Load the reference solution module."""
    ref_path = REFERENCES_DIR / f"{slug}.py"
    if not ref_path.exists():
        return None
    mod = types.ModuleType(f"ref_{slug.replace('-', '_')}")
    mod.__file__ = str(ref_path)
    exec(compile(ref_path.read_text(), str(ref_path), "exec"), mod.__dict__)
    return mod


def get_generator_for_param(param_name: str, param_type: str, entry: dict):
    """Map parameter to a generator function."""
    # Custom per-problem constraints
    constraints = {}
    
    # Known constraints from problem analysis
    if param_type == "list[int]":
        if "length" in entry.get("constraints", {}):
            constraints["length"] = entry["constraints"]["length"]
        if "value_range" in entry.get("constraints", {}):
            constraints["value_range"] = entry["constraints"]["value_range"]
        return lambda: gen_list_int(constraints)
    elif param_type == "str":
        # Special case: letter-combinations-of-a-phone-number expects digits 2-9
        if entry.get("method") == "letterCombinations":
            return lambda: "".join(random.choice("23456789") for _ in range(random.randint(1, 4)))
        return lambda: gen_str(constraints)
    elif param_type == "int":
        return lambda: gen_int(constraints)
    elif param_type == "list[str]":
        return lambda: gen_list_str(constraints)
    elif param_type == "list[list[int]]":
        return lambda: gen_matrix_int(constraints)
    elif param_type == "list[list[str]]":
        return lambda: gen_matrix_str(constraints)
    elif param_type == "List[str]":
        return lambda: gen_list_str(constraints)
    elif param_type == "float":
        return lambda: gen_float(constraints)
    elif param_type == "List[List[int]]":
        return lambda: gen_matrix_int(constraints)
    elif param_type == "List[List[str]]":
        return lambda: gen_matrix_str(constraints)
    return None


def generate_cases_for_slug(slug: str, num_cases: int = 30) -> list[dict]:
    """Generate edge cases for a single problem slug."""
    entry = problems.get(slug)
    if not entry:
        return []
    
    ref = load_reference(slug)
    if not ref:
        print(f"  No reference for {slug}")
        return []
    
    sol_class = getattr(ref, "Solution", None)
    if not sol_class:
        print(f"  No Solution class in reference for {slug}")
        return []
    
    # Instantiate the solution class
    sol = sol_class()
    method_name = entry["method"]
    method = getattr(sol, method_name, None)
    if not method:
        print(f"  No method {method_name} in reference for {slug}")
        return []
    
    params, ret_type = infer_signature(entry)
    if not params:
        print(f"  Could not infer signature for {slug}")
        return []
    
    # Build generators for each parameter
    generators = []
    for param_name, param_type in params:
        gen = get_generator_for_param(param_name, param_type, entry)
        if gen is None:
            print(f"  No generator for {param_name}: {param_type} in {slug}")
            return []
        generators.append(gen)
    
    cases = []
    seen = set()
    
    for _ in range(num_cases * 2):  # Generate extra to account for duplicates
        args = tuple(gen() for gen in generators)
        # Hash for deduplication
        key = json.dumps(args, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        
        try:
            want = method(*args)
            cases.append({"args": args, "want": want})
            if len(cases) >= num_cases:
                break
        except Exception as e:
            # Skip invalid inputs
            continue
    
    return cases


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="Generate for specific slug only")
    ap.add_argument("--topic", help="Generate for specific topic only")
    ap.add_argument("--num", type=int, default=30, help="Number of cases per problem")
    ap.add_argument("--dry-run", action="store_true", help="Don't write files")
    args = ap.parse_args()
    
    # Load bank
    all_problems = bank()
    slug_to_topic = {p["slug"]: p["topic"] for p in all_problems}
    by_topic = {}
    for p in all_problems:
        by_topic.setdefault(p["topic"], []).append(p["slug"])
    
    if args.slug:
        if args.slug not in slug_to_topic:
            print(f"Unknown slug: {args.slug}")
            return
        topics_to_process = [slug_to_topic[args.slug]]
        slugs_to_process = [args.slug]
    elif args.topic:
        if args.topic not in by_topic:
            print(f"Unknown topic: {args.topic}")
            return
        topics_to_process = [args.topic]
        slugs_to_process = None
    else:
        topics_to_process = sorted(by_topic.keys())
        slugs_to_process = None
    
    total_generated = 0
    
    for topic in topics_to_process:
        slugs = slugs_to_process if slugs_to_process else by_topic[topic]
        extras_path = EXTRAS_DIR / f"{topic.lower().replace(' ', '-').replace('&', '').replace('/', '-')}.json"
        
        # Load existing
        existing = {}
        if extras_path.exists():
            existing = json.loads(extras_path.read_text())
        
        print(f"\n=== {topic} ===")
        for slug in slugs:
            print(f"  {slug}...", end=" ", flush=True)
            cases = generate_cases_for_slug(slug, args.num)
            if cases:
                existing[slug] = cases
                total_generated += len(cases)
                print(f"{len(cases)} cases")
            else:
                print("skipped")
        
        if not args.dry_run:
            extras_path.write_text(json.dumps(existing, indent=1))
            print(f"  Saved to {extras_path}")
    
    print(f"\nTotal generated: {total_generated}")


if __name__ == "__main__":
    main()