"""Reproduce the frequency and mesh tables in CLAUDE_FINDINGS.md.

Run from the repository root: make && python3 -m tools.reproduce_findings
Uses the real binary and temporary inputs; no additional Python dependencies.
These are diagnostic measurements, not converged reference solutions.
"""

from pathlib import Path
import re
from tempfile import TemporaryDirectory

from tools.fh_crosscheck.parse_weeks import (
    parse_line_params, parse_weeks_output, run_weeks_text,
)


def main():
    root = Path(__file__).resolve().parents[1]
    template = (root / "examples/test_microstrip.yaml").read_text()
    # Keep the ground mesh unchanged; the shipped example has two conductors.
    ground, signal = template.split("  # Signal trace;", 1)
    with TemporaryDirectory(prefix="weeks-findings-") as directory:
        case = Path(directory) / "input.yaml"

        def measure(frequency, refined=False):
            trace = signal
            if refined:
                for key, value in (("nw", 41), ("nh", 21), ("b", 0.3)):
                    trace, count = re.subn(
                        rf"(?m)^(    {key}:) [^\n]+$", rf"\g<1> {value}", trace
                    )
                    if count != 1:
                        raise ValueError(f"Expected one signal {key} field")
            text, count = re.subn(
                r"(?m)^frequency:.*$", f"frequency: {frequency}",
                ground + "  # Signal trace;" + trace,
            )
            if count != 1:
                raise ValueError("Expected one frequency field")
            case.write_text(text)
            output = run_weeks_text(case, str(root / "weeks"), str(root))
            r, l = parse_weeks_output(output)
            params = parse_line_params(output)[0]
            return r[0][0], l[0][0], params["z0"], params["c"]

        print("frequency_Hz R_Ohm/m L_H/m Z0_Ohm C_F/m", flush=True)
        for frequency in (1e4, 1e6, 1e7, 1e8, 1e10):
            print(frequency, *measure(frequency), flush=True)
        print("frequency_Hz trace_mesh R_Ohm/m (not converged)", flush=True)
        for frequency in (1e9, 1e10):
            for refined in (False, True):
                mesh = "41x21,b=0.3" if refined else "21x7,b=0.9"
                print(frequency, mesh, measure(frequency, refined)[0], flush=True)


if __name__ == "__main__":
    main()
