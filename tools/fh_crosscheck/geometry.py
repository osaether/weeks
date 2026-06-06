"""Minimal reader for the flat weeks YAML input files.

Deliberately dependency-free (no PyYAML). It only understands the known shape:
a top-level ``frequency: <float>`` and a ``conductors:`` list of ``- name: ...``
mappings with numeric fields. Not a general YAML parser.
"""

INT_KEYS = {"nw", "nh"}


def _strip_comment(line):
    return line.split("#", 1)[0].rstrip()


def _coerce(key, value):
    if key == "name":
        return value
    if key in INT_KEYS:
        return int(value)
    return float(value)


def load_case(path):
    """Return ``(frequency, conductors)``.

    ``frequency`` is a float (Hz). ``conductors`` is a list of dicts with the
    conductor fields (``name`` str; numeric fields float; ``nw``/``nh`` int).
    Conductor 0 is the ground plane.
    """
    frequency = None
    conductors = []
    current = None
    in_conductors = False

    with open(path) as handle:
        for raw in handle:
            line = _strip_comment(raw)
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()

            if indent == 0 and not stripped.startswith("- "):
                in_conductors = stripped.startswith("conductors:")
                if not in_conductors and ":" in stripped:
                    key, _, value = stripped.partition(":")
                    if key.strip() == "frequency":
                        frequency = float(value.strip())
                continue

            if not in_conductors:
                continue

            if stripped.startswith("- "):
                if current is not None:
                    conductors.append(current)
                current = {}
                stripped = stripped[2:].strip()

            if current is not None and ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                current[key] = _coerce(key, value.strip())

    if current is not None:
        conductors.append(current)
    if frequency is None:
        raise ValueError("no 'frequency' found in %s" % path)
    if not conductors:
        raise ValueError("no conductors found in %s" % path)
    return frequency, conductors
