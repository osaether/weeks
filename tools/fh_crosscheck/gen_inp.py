"""Generate FastHenry .inp text from weeks conductor definitions.

Each conductor is tiled into ``min(nw, max_segs)`` sub-segments (bars) running
along +z, covering the full cross-section width.  Using explicit sub-segments
rather than a single wide bar with nwinc>1 gives FastHenry the spatial
resolution needed to model the distributed ground-return current accurately when
multiple signal traces are present.  Sub-segments within the same conductor are
shorted together at both the near and far ends via ``.equiv``.  All conductor
far ends are shorted to the ground far end; one port per signal conductor is
declared between its near-end node and the ground near-end node.
"""

import math

COPPER_SIGMA = 5.8e7  # S/m, matches weeks' hardcoded conductivity


def odd_clamp(value, low, high):
    """Clamp ``value`` into [low, high] then force odd (FastHenry nwinc/nhinc)."""
    v = max(low, min(high, int(value)))
    if v % 2 == 0:
        v -= 1
    return max(low, v)


def _g(x):
    """Format a float compactly (FastHenry tolerates %g-style)."""
    return "%g" % x


def build_inp(frequency, conductors, length, sigma=COPPER_SIGMA, inc_max=21, max_segs=20):
    """Build a FastHenry .inp file.

    Each conductor is tiled into ``min(nw, max_segs)`` width sub-segments with
    ``nwinc=1``.  Sub-segments of the same conductor are shorted at both ends.
    All conductor far ends are shorted to the ground (conductor 0) far end; one
    port per signal conductor is declared near-end vs ground near-end.

    nhinc is set to 1 for conductors thinner than the skin depth (uniform current
    through height) and to odd_clamp(nh) otherwise.
    """
    mu0 = 4.0 * math.pi * 1e-7
    skin_depth = 1.0 / math.sqrt(math.pi * frequency * mu0 * sigma)

    n = len(conductors)
    lines = [".units m", ".default sigma=%s" % _g(sigma)]

    seg_id = 0       # global segment / node counter
    cond_first = []  # first seg_id for each conductor (representative node base)

    for ci, c in enumerate(conductors):
        n_segs = min(c["nw"], max_segs)
        seg_w = c["w"] / n_segs
        cy = c["y"] + c["h"] / 2.0
        if c["h"] < skin_depth:
            nhinc = 1
        else:
            nhinc = odd_clamp(c["nh"], 1, inc_max)

        first = seg_id
        for si in range(n_segs):
            cx = c["x"] + (si + 0.5) * seg_w
            lines.append("N%ds x=%s y=%s z=0" % (seg_id, _g(cx), _g(cy)))
            lines.append("N%de x=%s y=%s z=%s" % (seg_id, _g(cx), _g(cy), _g(length)))
            lines.append(
                "E%d N%ds N%de w=%s h=%s nwinc=1 nhinc=%d wx=1 wy=0 wz=0"
                % (seg_id, seg_id, seg_id, _g(seg_w), _g(c["h"]), nhinc)
            )
            seg_id += 1

        # Short all sub-segments of this conductor together at both ends
        for si in range(1, n_segs):
            lines.append(".equiv N%ds N%ds" % (first, first + si))
            lines.append(".equiv N%de N%de" % (first, first + si))

        cond_first.append(first)

    # Short every signal conductor's far end to the ground far end
    for ci in range(1, n):
        lines.append(".equiv N%de N%de" % (cond_first[0], cond_first[ci]))

    # One port per signal conductor: near end vs ground near end
    for ci in range(1, n):
        lines.append(".external N%ds N%ds" % (cond_first[ci], cond_first[0]))

    lines.append(".freq fmin=%d fmax=%d ndec=1" % (frequency, frequency))
    lines.append(".end")
    return "\n".join(lines) + "\n"
