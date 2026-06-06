from tools.fh_crosscheck.gen_inp import build_inp, odd_clamp


def test_odd_clamp():
    assert odd_clamp(201, 1, 21) == 21      # clamped, odd
    assert odd_clamp(20, 1, 21) == 19       # even -> nearest lower odd
    assert odd_clamp(7, 1, 21) == 7
    assert odd_clamp(0, 1, 21) == 1


# Small fixture: 4-segment ground plane + 2-segment signal trace.
# Segment IDs: gnd=0..3 (cond_first[0]=0), sig=4..5 (cond_first[1]=4).
SMALL = [
    {"name": "line0", "w": 400e-6, "h": 2e-6,  "x": 0.0,    "y": 0.0,    "nw": 4, "nh": 1},
    {"name": "line1", "w": 100e-6, "h": 10e-6, "x": 150e-6, "y": 50e-6, "nw": 2, "nh": 2},
]

# Full fixture matching test_single.yaml geometry (ground nw=201 → 100 segs,
# signal nw=21 → 21 segs; cond_first[1] = 100).
FULL = [
    {"name": "line0", "w": 2800e-6, "h": 2e-6,  "x": 0.0,    "y": 0.0,    "nw": 201, "nh": 3},
    {"name": "line1", "w": 150e-6,  "h": 18e-6, "x": 600e-6, "y": 77e-6,  "nw": 21,  "nh": 7},
]


def test_build_inp_structure():
    text = build_inp(30e6, SMALL, length=10e-3)
    lines = text.splitlines()

    assert ".units m" in lines
    assert any(l.startswith(".default sigma=") for l in lines)

    # Ground plane: 4 sub-segments (E0..E3), signal: 2 sub-segments (E4..E5)
    for eid in range(6):
        assert any(l.startswith("E%d N%ds N%de" % (eid, eid, eid)) for l in lines), \
            "missing segment E%d" % eid

    # Within-conductor equivs for ground plane (N0s is the representative)
    assert ".equiv N0s N1s" in lines
    assert ".equiv N0s N2s" in lines
    assert ".equiv N0s N3s" in lines
    assert ".equiv N0e N1e" in lines
    assert ".equiv N0e N2e" in lines
    assert ".equiv N0e N3e" in lines

    # Within-conductor equivs for signal trace
    assert ".equiv N4s N5s" in lines
    assert ".equiv N4e N5e" in lines

    # Signal far end shorted to ground far end
    assert ".equiv N0e N4e" in lines

    # Port: signal representative near end vs ground representative near end
    assert ".external N4s N0s" in lines

    assert ".freq fmin=30000000 fmax=30000000 ndec=1" in lines
    assert lines[-1] == ".end"


def test_sub_segment_widths():
    """Each sub-segment has width = total_width / n_segs."""
    text = build_inp(30e6, SMALL, length=10e-3)
    seg_w_gnd = 400e-6 / 4   # 100 µm
    seg_w_sig = 100e-6 / 2   # 50 µm
    assert "w=%s" % ("%g" % seg_w_gnd) in text
    assert "w=%s" % ("%g" % seg_w_sig) in text


def test_sub_segment_positions():
    """Sub-segment centres tile the conductor width without gaps or overlaps."""
    text = build_inp(30e6, SMALL, length=10e-3)
    # Ground plane: 4 segs, each 100 µm wide, starting at x=0
    # centres: 50, 150, 250, 350 µm
    for i, cx in enumerate([50e-6, 150e-6, 250e-6, 350e-6]):
        assert "N%ds x=%s" % (i, "%g" % cx) in text, \
            "missing ground sub-seg %d at x=%.3e" % (i, cx)
    # Signal trace: 2 segs, each 50 µm wide, starting at x=150 µm
    # centres: 175, 225 µm
    for i, cx in enumerate([175e-6, 225e-6]):
        node_id = 4 + i
        assert "N%ds x=%s" % (node_id, "%g" % cx) in text, \
            "missing signal sub-seg %d at x=%.3e" % (i, cx)


def test_nwinc_is_one():
    """All segments use nwinc=1 (explicit sub-division, not FastHenry internal)."""
    text = build_inp(30e6, FULL, length=10e-3)
    for line in text.splitlines():
        if line.startswith("E"):
            assert "nwinc=1" in line, "segment without nwinc=1: %s" % line


def test_nhinc_thin_conductor():
    """Conductors thinner than the skin depth get nhinc=1 (uniform current)."""
    # At 30 MHz in copper, skin depth ≈ 12 µm.
    # Ground plane h=2 µm < skin_depth → nhinc=1.
    # Signal trace h=18 µm > skin_depth → nhinc=odd_clamp(7,1,21)=7.
    # With default max_segs=20: ground has E0..E19, signal has E20..E40.
    text = build_inp(30e6, FULL, length=10e-3)
    lines = text.splitlines()
    # Ground plane segments are E0..E19; all must have nhinc=1
    gnd_segs = [l for l in lines if l.startswith("E") and int(l.split()[0][1:]) < 20]
    for l in gnd_segs:
        assert "nhinc=1" in l, "ground segment should have nhinc=1: %s" % l
    # Signal trace segments are E20..E40; all must have nhinc=7
    sig_segs = [l for l in lines if l.startswith("E") and 20 <= int(l.split()[0][1:]) <= 40]
    for l in sig_segs:
        assert "nhinc=7" in l, "signal segment should have nhinc=7: %s" % l


def test_centre_segment_at_conductor_centre():
    """The middle sub-segment of an odd-count conductor falls at the conductor centre."""
    # Use a fixture with an odd n_segs so there is an exact centre segment.
    # ground nw=4 → min(4, 20)=4 segs (ids 0..3)
    # signal nw=3 → min(3, 20)=3 segs (ids 4..6); middle si=1 → N5s
    # signal centre x = 100e-6 + (1+0.5) * (300e-6/3) = 100e-6 + 150e-6 = 250e-6
    odd_signal = [
        {"name": "line0", "w": 400e-6, "h": 2e-6, "x": 0.0, "y": 0.0, "nw": 4, "nh": 1},
        {"name": "line1", "w": 300e-6, "h": 10e-6, "x": 100e-6, "y": 50e-6, "nw": 3, "nh": 2},
    ]
    text = build_inp(30e6, odd_signal, length=10e-3)
    assert "N5s x=0.00025 y=5.5e-05 z=0" in text


def test_single_freq_block():
    text = build_inp(30e6, SMALL, length=10e-3)
    assert ".freq fmin=30000000 fmax=30000000 ndec=1" in text.splitlines()


def test_max_segs_cap():
    """max_segs limits the number of sub-segments regardless of nw."""
    text = build_inp(30e6, FULL, length=10e-3, max_segs=5)
    # Ground plane: min(201, 5) = 5 segs → E0..E4
    # Signal trace: min(21, 5) = 5 segs → E5..E9
    assert any(l.startswith("E4 ") for l in text.splitlines())
    assert not any(l.startswith("E10 ") for l in text.splitlines())
