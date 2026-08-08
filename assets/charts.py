"""Generate the README's two hand-built SVG charts, light + dark variants.

Palette: brand-adapted categorical (violet, teal, amber, blue) — this ordering
clears every gate of the dataviz validator in both modes against the GitHub
surfaces (#ffffff / #0d1117).
"""
import sys
from html import escape

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
W = 880
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"

THEME = {
    "light": {
        "surface": "#ffffff",
        "primary": "#0b0b0b",
        "secondary": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "track": "#f2f1ee",
        "series": ["#6D3BD1", "#0E8F7C", "#9A6B00", "#2a78d6"],
        "bar": "#6D3BD1",
    },
    "amber-light": {
        "surface": "#ffffff",
        "primary": "#1A1206",
        "secondary": "#4A3A20",
        "muted": "#8A7A5A",
        "grid": "#F2EADA",
        "axis": "#D8CCB0",
        "track": "#FFF9EC",
        # single-hue ordinal ramp: identity comes from the direct labels
        "series": ["#7A4A05", "#A06A0C", "#C08E1E", "#DCB04E"],
        "bar": "#A06A0C",
        "ordinal": True,
    },
    "amber-dark": {
        "surface": "#12100A",
        "primary": "#FFF6DF",
        "secondary": "#E0D3B8",
        "muted": "#A89878",
        "grid": "#251F12",
        "axis": "#3A3020",
        "track": "#1A1409",
        "series": ["#8A5A08", "#B37D12", "#D9A62E", "#F2CE72"],
        "bar": "#C68A16",
        "ordinal": True,
    },
    "noir-light": {
        "surface": "#ffffff",
        "primary": "#0B0708",
        "secondary": "#4A3A3C",
        "muted": "#8A7A7C",
        "grid": "#EDE6E4",
        "axis": "#CFC2C0",
        "track": "#F7F3F1",
        # single-hue ordinal ramp: identity comes from the direct labels
        "series": ["#6E1017", "#9B2226", "#C4494A", "#E8817C"],
        "bar": "#9B2226",
        "ordinal": True,
    },
    "noir-dark": {
        "surface": "#0B0708",
        "primary": "#F7F3F1",
        "secondary": "#D3C5C4",
        "muted": "#9A8A8B",
        "grid": "#241A1C",
        "axis": "#3A2C2E",
        "track": "#160F11",
        "series": ["#8A2229", "#B23F38", "#D4665F", "#F0AAA4"],
        "bar": "#C0504F",
        "ordinal": True,
    },
    "dark": {
        "surface": "#0d1117",
        "primary": "#ffffff",
        "secondary": "#c3c2b7",
        "muted": "#8b949e",
        "grid": "#21262d",
        "axis": "#383835",
        "track": "#161b22",
        "series": ["#9F7AEA", "#199E70", "#C98500", "#3987e5"],
        "bar": "#9F7AEA",
    },
}

TRACKS = ["Engineering", "AI / ML", "Delivery & PM", "Growth & Marketing"]

# (label, org, start_year_frac, end_year_frac, track_index, cv_id)
ROLES = [
    ("Middle Fullstack Developer + AI Engineer", "Tocan Solutions", 2025.0, 2026.6, 1, "tocan"),
    ("IT Project Manager", "Digitum NL", 2024.25, 2026.6, 2, "digitum"),
    ("Python / Full-Stack Developer", "Freelance & Commercial", 2020.08, 2026.6, 0, "freelance"),
    ("Media Buyer / Account Manager", "leeloo.ai", 2025.0, 2026.0, 3, "leeloo"),
    ("Project Manager / Client Communication Manager", "Veyrala Team", 2024.0, 2026.0, 2, "contract-manager"),
    ("IT Project Manager", "WebStork", 2025.0, 2025.9, 2, "webstork"),
    ("IT Project Manager / Media Buyer / Account Manager", "IndagoDev", 2024.0, 2025.0, 3, "indagodev"),
    ("Full-Stack Developer + AI Engineer", "Quorvane Team", 2023.0, 2025.0, 1, "kelvora"),
    ("Frontend / Full-Stack Developer", "Veyrala Team", 2023.0, 2025.0, 0, "contract-dev"),
    ("IT Copywriter", "Quintagroup", 2023.0, 2024.3, 3, "quintagroup"),
    ("Project Manager / Marketer", "Obrenda Team", 2022.08, 2023.99, 2, "marketing"),
]

# Named cuts of the same history, mirroring data/experiencePresets.ts in the
# portfolio app. `None` means every role.
VIEWS = {
    "": ("Career timeline", None),
    "pm": ("Career timeline &#183; delivery &amp; PM", ["digitum", "contract-manager", "webstork", "indagodev", "marketing"]),
    "dev": ("Career timeline &#183; engineering", ["tocan", "freelance", "kelvora", "contract-dev"]),
    "highlights": ("Career timeline &#183; most significant", ["tocan", "digitum", "kelvora", "freelance"]),
    "dev-plus": ("Career timeline &#183; engineering + most significant",
                 ["tocan", "digitum", "freelance", "kelvora", "contract-dev"]),
}

# (technology, years)
STACK = [
    ("Python", 6.0),
    ("PostgreSQL", 6.0),
    ("React", 6.0),
    ("TypeScript", 5.0),
    ("FastAPI", 4.5),
    ("Docker", 4.5),
    ("Django", 4.5),
    ("Redis", 4.5),
    ("ML / NLP", 4.0),
    ("LLM / RAG systems", 3.5),
    ("Next.js", 3.5),
    ("Vue 3", 3.5),
    ("Node.js", 3.5),
    ("LangChain / LangGraph", 2.5),
    ("Computer vision (OpenCV / YOLO)", 2.5),
    ("Web3 / ethers.js", 2.5),
    ("Qdrant / pgvector", 2.0),
    ("Kubernetes", 2.0),
    ("AWS", 2.0),
    ("Solidity", 2.0),
]


def right_rounded(x, y, w, h, r):
    """Bar path with only the data end rounded, per the mark spec."""
    r = min(r, w, h / 2)
    return (
        f"M{x:.1f},{y:.1f}H{x + w - r:.1f}Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f}"
        f"V{y + h - r:.1f}Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f}"
        f"H{x:.1f}Z"
    )


def timeline(mode, view=""):
    t = THEME[mode]
    W = 1080
    left, right, top = 372, 150, 64
    heading, keep = VIEWS[view]
    roles = ROLES if keep is None else [r for r in ROLES if r[5] in keep]
    row_h, gap = 30, 8
    plot_w = W - left - right
    x0, x1 = 2020.0, 2026.75
    height = top + len(roles) * (row_h + gap) + 62

    def sx(v):
        return left + (v - x0) / (x1 - x0) * plot_w

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" '
        f'height="{height}" font-family="{FONT}" role="img" '
        f'aria-label="Career timeline 2020 to 2026 by track">',
        f'<rect width="{W}" height="{height}" fill="{t["surface"]}"/>',
        f'<text x="34" y="34" fill="{t["primary"]}" font-size="17" font-weight="700">'
        f"{heading} &#183; 2020 &#8594; 2026</text>",
    ]

    # legend — identity is never carried by color alone
    lx = 34
    present = {r[4] for r in roles}
    for i, name in enumerate([] if t.get("ordinal") else TRACKS):
        if i not in present:
            continue
        p.append(f'<rect x="{lx}" y="{47}" width="10" height="10" rx="2" fill="{t["series"][i]}"/>')
        p.append(
            f'<text x="{lx + 16}" y="{56}" fill="{t["secondary"]}" font-size="12">{escape(name)}</text>'
        )
        lx += 22 + len(name) * 6.9

    # year gridlines
    for yr in range(2020, 2027):
        gx = sx(yr)
        p.append(
            f'<line x1="{gx:.1f}" y1="{top}" x2="{gx:.1f}" y2="{height - 44:.0f}" '
            f'stroke="{t["grid"]}" stroke-width="1"/>'
        )
        p.append(
            f'<text x="{gx:.1f}" y="{height - 24}" fill="{t["muted"]}" font-size="12" '
            f'text-anchor="middle">{yr}</text>'
        )

    y = top
    for label, org, start, end, track, _ in roles:
        bx, bw = sx(start), max(sx(end) - sx(start), 6)
        p.append(
            f'<text x="{left - 14}" y="{y + 13}" fill="{t["primary"]}" font-size="12.5" '
            f'text-anchor="end">{escape(label)}</text>'
        )
        p.append(
            f'<text x="{left - 14}" y="{y + 26}" fill="{t["muted"]}" font-size="11" '
            f'text-anchor="end">{escape(org)}</text>'
        )
        p.append(
            f'<rect x="{bx:.1f}" y="{y + 5}" width="{bw:.1f}" height="{row_h - 10}" rx="4" '
            f'fill="{t["series"][track]}"/>'
        )
        if t.get("ordinal"):
            # one hue cannot carry four identities, so name the track on the bar
            p.append(
                f'<text x="{bx + bw + 8:.1f}" y="{y + 19}" fill="{t["muted"]}" font-size="10.5">'
                f"{escape(TRACKS[track])}</text>"
            )
        y += row_h + gap

    p.append(
        f'<line x1="{left}" y1="{height - 44:.0f}" x2="{W - right}" y2="{height - 44:.0f}" '
        f'stroke="{t["axis"]}" stroke-width="1"/>'
    )
    p.append("</svg>")
    return "\n".join(p)


def stack(mode):
    t = THEME[mode]
    left, right, top = 178, 60, 58
    row_h, gap = 20, 6
    plot_w = W - left - right
    vmax = 5.5
    height = top + len(STACK) * (row_h + gap) + 46

    def sx(v):
        return v / vmax * plot_w

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" '
        f'height="{height}" font-family="{FONT}" role="img" '
        f'aria-label="Years of hands-on experience per technology">',
        f'<rect width="{W}" height="{height}" fill="{t["surface"]}"/>',
        f'<text x="34" y="32" fill="{t["primary"]}" font-size="17" font-weight="700">'
        f"Stack depth &#183; years hands-on</text>",
        f'<text x="34" y="49" fill="{t["muted"]}" font-size="12">'
        f"Commercial and production use, not tutorials</text>",
    ]

    for v in range(0, 6):
        gx = left + sx(v)
        p.append(
            f'<line x1="{gx:.1f}" y1="{top - 6}" x2="{gx:.1f}" y2="{height - 34:.0f}" '
            f'stroke="{t["grid"]}" stroke-width="1"/>'
        )
        p.append(
            f'<text x="{gx:.1f}" y="{height - 14}" fill="{t["muted"]}" font-size="11" '
            f'text-anchor="middle">{v}y</text>'
        )

    y = top
    for name, years in STACK:
        p.append(
            f'<text x="{left - 14}" y="{y + 14}" fill="{t["primary"]}" font-size="12.5" '
            f'text-anchor="end">{escape(name)}</text>'
        )
        p.append(
            f'<path d="{right_rounded(left, y + 2, max(sx(years), 4), row_h - 4, 4)}" '
            f'fill="{t["bar"]}"/>'
        )
        p.append(
            f'<text x="{left + sx(years) + 10:.1f}" y="{y + 14}" fill="{t["secondary"]}" '
            f'font-size="11.5">{years:g}</text>'
        )
        y += row_h + gap

    p.append(
        f'<line x1="{left}" y1="{height - 34:.0f}" x2="{W - right}" y2="{height - 34:.0f}" '
        f'stroke="{t["axis"]}" stroke-width="1"/>'
    )
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    for mode in THEME:
        for view in VIEWS:
            suffix = f"-{view}" if view else ""
            path = f"{OUT}/timeline{suffix}-{mode}.svg"
            with open(path, "w", encoding="utf-8") as f:
                f.write(timeline(mode, view))
            print("wrote", path)
        path = f"{OUT}/stack-{mode}.svg"
        with open(path, "w", encoding="utf-8") as f:
            f.write(stack(mode))
        print("wrote", path)
