"""CLI: python3 -m tools.fh_crosscheck <case.yaml> [options]."""

import argparse
import sys

from tools.fh_crosscheck.compare import cross_check
from tools.fh_crosscheck.run_fasthenry import FastHenryNotFound, FastHenryError


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python3 -m tools.fh_crosscheck",
        description="Cross-check weeks R/L against FastHenry.",
    )
    parser.add_argument("case_yaml", help="weeks YAML input file")
    parser.add_argument("--l1", type=float, default=5e-3, help="short bar length (m)")
    parser.add_argument("--l2", type=float, default=10e-3, help="long bar length (m)")
    parser.add_argument("--tol", type=float, default=12.0, help="flag tolerance (%%)")
    parser.add_argument("--keep-inp", default=None, help="dir to keep generated .inp")
    args = parser.parse_args(argv)

    try:
        report, _flagged = cross_check(
            args.case_yaml, l1=args.l1, l2=args.l2, tol=args.tol, keep_inp=args.keep_inp
        )
    except FastHenryNotFound as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    except FastHenryError as exc:
        sys.stderr.write("FastHenry failed:\n%s\n" % exc)
        return 2

    print(report)
    # Soft policy: the comparison itself always succeeds (flags are informational).
    return 0


if __name__ == "__main__":
    sys.exit(main())
