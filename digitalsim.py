"""Tiny combinational logic simulator producing WaveDrom JSON.

Usage:
  python digitalsim.py path/to/circuit.net [--out out.json]

Input format sections (fixed order): INPUTS, OUTPUTS, GATES, STIMULUS.
Gates: OUT = AND(A, B) | OR(A, B) | XOR(A, B) | NOT(A)

Note: this template file uses the `argparse` module to get arguments
from the command line.  You are expected to retain this part of it
to make testing easier.  The function calls given in the `main` function
are only suggestions, and you can rename them or create others as long
as the interface to the outside world does not change.

This may make it a bit harder to run purely from an editor like VSCode. 
However, in practice you almost never run code directly from an editor,
so this is something you need to be able to handle anyway.
"""

import sys
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Any

def parse_netlist(text: str) -> Dict[str, Any]:
    lines = []
    for ln in text.splitlines():
        stripped = ln.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    def expect(prefix: str, idx: int) -> int:
        if idx >= len(lines) or not lines[idx].startswith(prefix):
            raise ValueError(f"Expected section '{prefix}'")
        return idx

    i = expect("INPUTS:", 0)
    inputs = lines[i].split(":", 1)[1].strip().split()
    i += 1

    i = expect("OUTPUTS:", i)
    outputs = lines[i].split(":", 1)[1].strip().split()
    i += 1

    i = expect("GATES:", i)
    i += 1

    gate_re = re.compile(
        r"^(?P<out>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
        r"(?P<type>AND|OR|XOR|NOT)\s*\(\s*(?P<args>[A-Za-z0-9_,\s]+)\s*\)\s*$"
    )
    gates = []
    while i < len(lines) and not lines[i].startswith("STIMULUS:"):
        m = gate_re.match(lines[i])
        if not m:
            raise ValueError(f"Invalid gate line: '{lines[i]}'")
        out = m.group("out")
        gtype = m.group("type")
        args = [a.strip() for a in m.group("args").split(",")]
        gates.append((out, gtype, args))
        i += 1

    if i >= len(lines) or not lines[i].startswith("STIMULUS:"):
        raise ValueError("Missing STIMULUS section")
    i += 1

    stimulus = []
    last_time = -1
    while i < len(lines):
        parts = lines[i].split()
        if len(parts) < 1 + len(inputs):
            raise ValueError(f"Invalid STIMULUS line: '{lines[i]}'")
        time = int(parts[0])
        if time <= last_time:
            raise ValueError("STIMULUS times must increase")
        vals = [int(x) for x in parts[1:1 + len(inputs)]]
        stimulus.append((time, vals))
        last_time = time
        i += 1

    return {
        "inputs": inputs,
        "outputs": outputs,
        "gates": gates,
        "stimulus": stimulus,
    }

def eval_gate(gtype: str, args: List[int]) -> int:
    if gtype == "AND":
        return args[0] & args[1]
    elif gtype == "OR":
        return args[0] | args[1]
    elif gtype == "XOR":
        return args[0] ^ args[1]
    elif gtype == "NOT":
        return 1 - args[0]
    else:
        raise ValueError(f"Unknown gate type: {gtype}")

def simulate(nl: Dict[str, Any]) -> Dict[str, str]:
    inputs, outputs, gates, stimulus = (
        nl["inputs"],
        nl["outputs"],
        nl["gates"],
        nl["stimulus"],
    )

    # All signal names encountered
    signals = {name: [] for name in inputs + outputs}

    for _t, vals in stimulus:
        env: Dict[str, int] = {}

        # Set input values
        for name, v in zip(inputs, vals):
            env[name] = v

        # Evaluate gates in declared order
        for out, gtype, args in gates:
            arg_vals = [env[a] for a in args]
            env[out] = eval_gate(gtype, arg_vals)

        # Record final values for each signal
        for name in signals.keys():
            signals[name].append(str(env[name]))

    # Concatenate wave strings
    waveforms = {n: "".join(bits) for n, bits in signals.items()}
    return waveforms



def to_wavedrom_json(nl: Dict[str, Any], waves: Dict[str, str]) -> str:
    sigs = []
    for n in nl["inputs"]:
        sigs.append({"name": n, "wave": waves[n]})
    for n in nl["outputs"]:
        sigs.append({"name": n, "wave": waves[n]})
    return json.dumps({"signal": sigs}, indent=2)

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("netlist", help=".net file path")
    ap.add_argument("--out", "-o", help="output JSON path")
    args = ap.parse_args(argv)

    text = Path(args.netlist).read_text()
    nl = parse_netlist(text)
    waves = simulate(nl)
    js = to_wavedrom_json(nl, waves)

    out_path = args.out
    if not out_path:
        out_path = str(Path(args.netlist).with_suffix(".json"))
    Path(out_path).write_text(js + "\n")
    print(f"Wrote: {out_path}")
    return 0



if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
