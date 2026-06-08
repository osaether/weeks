"""CLI: python3 -m tools.microstrip_z0 <case.yaml> [options]."""

import argparse
import sys

from tools.microstrip_z0.check import check_z0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python3 -m tools.microstrip_z0",
        description="Sanity-check weeks per-line Z0 against the "
                    "Hammerstad-Jensen microstrip closed form.",
    )
    parser.add_argument("case_yaml", help="weeks YAML input file")
    parser.add_argument("--tol", type=float, default=10.0,
                        help="Z0 flag tolerance (%%)")
    parser.add_argument("--gap-tol", type=float, default=5.0,
                        help="geometry consistency tolerance (%%)")
    args = parser.parse_args(argv)

    report, _flagged = check_z0(args.case_yaml, tol=args.tol, gap_tol=args.gap_tol)
    print(report)
    # Soft policy (matches fh_crosscheck): flags are informational, exit 0.
    return 0


if __name__ == "__main__":
    sys.exit(main())
