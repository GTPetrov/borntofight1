"""Fighter portrait generator - a composed inline SVG built from a look dict.

Deterministic: the same look always yields the same portrait. Gradient ids are
salted with the look so several portraits can share one page (division lists,
tale of the tape) without their <defs> colliding.
"""

from __future__ import annotations

DEFAULT_LOOK = {
    "skin": "#e0ac7e",
    "hair": "short",
    "hair_color": "#3b2417",
    "beard": "stubble",
    "build": "athletic",
    "trunks": "#e63946",
    "stance": "ortho",
}

# shoulder half-width and trap height by build
BUILD = {
    "wiry":     {"sw": 150, "trap": 6},
    "athletic": {"sw": 178, "trap": 12},
    "hulk":     {"sw": 214, "trap": 24},
}


def _shade(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return hex_color
    r, g, b = (max(0, min(255, int(v * factor))) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def _sid(look: dict) -> str:
    raw = f'{look.get("skin","")}{look.get("hair_color","")}{look.get("trunks","")}'
    return f"a{abs(hash(raw)) % 100000:05d}"


def url(look: dict | None, size: int = 120, wear: int = 0) -> str:
    from urllib.parse import urlencode
    q = {k: v for k, v in (look or {}).items() if k in DEFAULT_LOOK}
    q["size"] = size
    q["wear"] = wear
    return "/avatar.svg?" + urlencode(q)


def portrait(look: dict | None, size: int = 180, wear: int = 0) -> str:
    L = {**DEFAULT_LOOK, **(look or {})}
    sid = _sid(L)
    skin = L["skin"]
    skin_l = _shade(skin, 1.12)
    skin_d = _shade(skin, 0.84)
    skin_dd = _shade(skin, 0.66)
    hc = L["hair_color"]
    hc_l = _shade(hc, 1.28)
    hc_d = _shade(hc, 0.72)
    tr = L["trunks"]
    b = BUILD.get(L["build"], BUILD["athletic"])
    sw, trap = b["sw"], b["trap"]
    south = L["stance"] == "south"
    tx = 110 - sw / 2

    p = [
        f'<svg viewBox="0 0 220 220" width="{size}" height="{size}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="fighter portrait">',
        '<defs>',
        f'<radialGradient id="bg{sid}" cx="50%" cy="38%" r="75%">'
        f'<stop offset="0" stop-color="#26313f"/><stop offset="1" stop-color="#0d1218"/></radialGradient>',
        f'<linearGradient id="sk{sid}" x1="0" y1="0" x2="1" y2="0.35">'
        f'<stop offset="0" stop-color="{skin_l}"/><stop offset="0.55" stop-color="{skin}"/>'
        f'<stop offset="1" stop-color="{skin_d}"/></linearGradient>',
        f'<linearGradient id="tk{sid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{_shade(tr, 1.25)}"/><stop offset="1" stop-color="{_shade(tr, 0.8)}"/></linearGradient>',
        '</defs>',
        f'<rect width="220" height="220" fill="url(#bg{sid})"/>',
        f'<ellipse cx="110" cy="212" rx="120" ry="42" fill="#0a0e13" opacity="0.55"/>',
    ]

    # --- shoulders / traps / torso ---
    p.append(
        f'<path d="M{tx},220 '
        f'L{tx},{176 - trap * 0.2} '
        f'Q{110 - sw * 0.34},{150 - trap} {110 - 26},{140 - trap} '
        f'Q110,{132 - trap} {110 + 26},{140 - trap} '
        f'Q{110 + sw * 0.34},{150 - trap} {tx + sw},{176 - trap * 0.2} '
        f'L{tx + sw},220 Z" fill="url(#sk{sid})"/>'
    )
    # collarbone + chest shading
    p.append(f'<path d="M{110 - 30},152 Q110,146 {110 + 30},152" stroke="{skin_d}" '
             f'stroke-width="3" fill="none" opacity="0.5"/>')
    p.append(f'<path d="M110,150 v40" stroke="{skin_d}" stroke-width="3" fill="none" opacity="0.35"/>')
    p.append(f'<path d="M{tx},220 Q{tx + 12},185 {tx + 4},{178 - trap * 0.2} L{tx},220 Z" '
             f'fill="{skin_dd}" opacity="0.35"/>')
    p.append(f'<path d="M{tx + sw},220 Q{tx + sw - 12},185 {tx + sw - 4},{178 - trap * 0.2} L{tx + sw},220 Z" '
             f'fill="{skin_dd}" opacity="0.35"/>')

    # --- trunks waistband peeking at the bottom ---
    p.append(f'<rect x="{tx + 4}" y="205" width="{sw - 8}" height="15" fill="url(#tk{sid})"/>')
    p.append(f'<rect x="{tx + 4}" y="205" width="{sw - 8}" height="4" fill="{_shade(tr, 1.4)}"/>')

    # --- neck ---
    p.append(f'<path d="M96,118 h28 v20 q-14,11 -28,0 Z" fill="{skin_d}"/>')
    p.append(f'<path d="M96,118 h28 v6 q-14,7 -28,0 Z" fill="{skin_dd}" opacity="0.7"/>')

    # --- ears (draw before head so they tuck in) ---
    for ex, cauli in ((62, wear >= 2), (158, wear >= 2 and south is False)):
        p.append(f'<ellipse cx="{ex}" cy="98" rx="9" ry="13" fill="{skin_d}"/>')
        if cauli:
            p.append(f'<ellipse cx="{ex}" cy="100" rx="8" ry="10" fill="{skin_dd}"/>')
        else:
            p.append(f'<path d="M{ex + (3 if ex < 110 else -3)},92 q-4,6 0,12" '
                     f'stroke="{skin_dd}" stroke-width="2" fill="none"/>')

    # --- head: forehead + cheeks + jaw ---
    p.append(
        f'<path d="M110,34 '
        f'C140,34 156,58 156,86 '
        f'C156,104 150,120 136,132 '
        f'C127,140 118,146 110,146 '
        f'C102,146 93,140 84,132 '
        f'C70,120 64,104 64,86 '
        f'C64,58 80,34 110,34 Z" fill="url(#sk{sid})"/>'
    )
    # side shadow on the right cheek/jaw
    p.append(f'<path d="M158,86 C158,104 152,120 138,132 C130,140 120,145 110,145 '
             f'C118,140 128,128 134,112 C140,98 140,70 132,52 C144,60 158,66 158,86 Z" '
             f'fill="{skin_d}" opacity="0.4"/>')
    # cheekbone highlights
    p.append(f'<ellipse cx="86" cy="98" rx="10" ry="7" fill="{skin_l}" opacity="0.35"/>')
    p.append(f'<ellipse cx="132" cy="98" rx="9" ry="6" fill="{skin_l}" opacity="0.18"/>')

    # --- brows ---
    p.append(f'<path d="M75,76 Q88,69 100,73" stroke="{hc_d}" stroke-width="6" '
             f'fill="none" stroke-linecap="round"/>')
    p.append(f'<path d="M145,76 Q132,69 120,73" stroke="{hc_d}" stroke-width="6" '
             f'fill="none" stroke-linecap="round"/>')

    # --- eyes ---
    for ex in (91, 129):
        p.append(f'<path d="M{ex - 9},85 Q{ex},79 {ex + 9},85 Q{ex},90 {ex - 9},85 Z" fill="#f4f1ec"/>')
        p.append(f'<circle cx="{ex + (1 if ex < 110 else -1)}" cy="85" r="3.4" fill="#241a12"/>')
        p.append(f'<circle cx="{ex + (2 if ex < 110 else 0)}" cy="83.5" r="1" fill="#fff" opacity="0.8"/>')
        p.append(f'<path d="M{ex - 9},84 Q{ex},79 {ex + 9},84" stroke="{skin_d}" '
                 f'stroke-width="1.6" fill="none" stroke-linecap="round"/>')
        p.append(f'<path d="M{ex - 8},88 Q{ex},91 {ex + 8},88" stroke="{skin_d}" '
                 f'stroke-width="1" fill="none" opacity="0.5"/>')

    # --- nose ---
    crook = 4 if wear >= 3 else 0
    p.append(f'<path d="M110,80 L{106 - crook},106 Q110,111 {114 + crook // 2},106 '
             f'Q112,92 110,80 Z" fill="{skin_d}"/>')
    p.append(f'<path d="M110,82 L108,104" stroke="{skin_l}" stroke-width="2" '
             f'fill="none" opacity="0.4" stroke-linecap="round"/>')
    p.append(f'<ellipse cx="105" cy="107" rx="2.2" ry="1.6" fill="{skin_dd}"/>')
    p.append(f'<ellipse cx="116" cy="107" rx="2.2" ry="1.6" fill="{skin_dd}"/>')

    # --- mouth ---
    p.append('<path d="M99,124 Q110,129 121,124" stroke="#8a4a46" stroke-width="3.5" '
             'fill="none" stroke-linecap="round"/>')
    p.append(f'<path d="M100,127 Q110,130 120,127" stroke="{skin_d}" stroke-width="2" '
             f'fill="none" opacity="0.4"/>')

    # --- hair + beard ---
    p.append(_hair(L["hair"], hc, hc_l, hc_d))
    p.append(_beard(L["beard"], hc, hc_d))

    # --- battle wear ---
    if wear >= 1:
        p.append('<path d="M120,58 L128,70" stroke="#c07a63" stroke-width="3" stroke-linecap="round"/>')
        p.append('<path d="M120,58 L128,70" stroke="#7d3b2c" stroke-width="1" stroke-linecap="round"/>')
    if wear >= 2:
        p.append(f'<ellipse cx="130" cy="93" rx="7" ry="4" fill="{skin_dd}" opacity="0.7"/>')  # swelling
    if wear >= 3:
        p.append('<path d="M88,74 q3,3 0,7" stroke="#8f2f2f" stroke-width="2.5" fill="none" stroke-linecap="round"/>')
        p.append('<path d="M126,118 q4,3 8,0" stroke="#8f2f2f" stroke-width="2" fill="none" stroke-linecap="round"/>')

    # --- gloves resting low ---
    gc = _shade(tr, 0.5)
    gcl = _shade(tr, 0.62)
    for gx in (28, 192):
        p.append(f'<ellipse cx="{gx}" cy="215" rx="23" ry="19" fill="{gc}"/>')
        p.append(f'<ellipse cx="{gx}" cy="209" rx="16" ry="9" fill="{gcl}"/>')

    p.append('</svg>')
    return "".join(x for x in p if x)


def _hair(style, hc, hc_l, hc_d):
    if style == "bald":
        return (f'<path d="M64,84 Q110,40 156,84 Q150,58 110,54 Q70,58 64,84 Z" '
                f'fill="#ffffff" opacity="0.05"/>'
                f'<ellipse cx="98" cy="56" rx="16" ry="8" fill="#ffffff" opacity="0.07"/>')
    if style == "buzz":
        return (f'<path d="M60,90 Q58,34 110,30 Q162,34 160,90 Q152,50 110,46 Q68,50 60,90 Z" '
                f'fill="{hc}" opacity="0.55"/>'
                f'<path d="M60,90 Q58,34 110,30 Q162,34 160,90 Q152,50 110,46 Q68,50 60,90 Z" '
                f'fill="{hc}" opacity="0.4"/>')
    if style == "short":
        return (f'<path d="M58,98 Q54,30 110,27 Q166,30 162,98 '
                f'Q154,56 110,52 Q66,56 58,98 Z" fill="{hc}"/>'
                f'<path d="M58,98 Q60,68 70,58 Q62,76 64,100 Z" fill="{hc_d}"/>'
                f'<path d="M162,98 Q160,68 150,58 Q158,76 156,100 Z" fill="{hc_d}"/>'
                f'<path d="M82,38 Q110,28 138,40 Q110,36 82,38 Z" fill="{hc_l}" opacity="0.5"/>')
    if style == "mohawk":
        return (f'<path d="M62,102 Q60,70 84,56 Q74,82 76,104 Z" fill="{hc_d}" opacity="0.35"/>'
                f'<path d="M158,102 Q160,70 136,56 Q146,82 144,104 Z" fill="{hc_d}" opacity="0.35"/>'
                f'<path d="M97,16 Q110,10 123,16 Q126,44 120,70 Q110,60 100,70 Q94,44 97,16 Z" fill="{hc}"/>'
                f'<path d="M99,18 Q110,13 121,18 Q122,34 118,44 Q110,38 102,44 Q98,34 99,18 Z" fill="{hc_l}"/>')
    if style == "long":
        return (f'<path d="M62,156 Q56,50 92,36 Q110,31 128,36 Q164,50 158,156 '
                f'Q154,124 146,150 Q148,80 110,72 Q72,80 74,150 Q66,124 62,156 Z" fill="{hc}"/>'
                f'<path d="M64,102 Q60,52 94,38 Q110,33 126,38 Q160,52 156,102 '
                f'Q148,62 110,58 Q72,62 64,102 Z" fill="{hc_d}"/>'
                f'<path d="M84,42 Q110,34 136,44 Q110,40 84,42 Z" fill="{hc_l}" opacity="0.45"/>')
    if style == "corn":
        rows = "".join(
            f'<path d="M{x},38 Q{x + dx},64 {x + dx},96" stroke="{hc}" stroke-width="6" '
            f'fill="none" stroke-linecap="round"/>'
            f'<path d="M{x},38 Q{x + dx},64 {x + dx},96" stroke="{hc_l}" stroke-width="2" '
            f'fill="none" stroke-linecap="round" opacity="0.5"/>'
            for x, dx in ((80, -10), (93, -5), (110, 0), (127, 5), (140, 10)))
        return (f'<path d="M62,88 Q110,40 158,88 Q150,52 110,48 Q70,52 62,88 Z" fill="{hc_d}"/>{rows}')
    return ""


def _beard(style, hc, hc_d):
    if style in ("", "none"):
        return ""
    if style == "stubble":
        return (f'<path d="M64,98 Q70,140 110,152 Q150,140 156,98 Q148,128 110,130 '
                f'Q72,128 64,98 Z" fill="{hc}" opacity="0.22"/>')
    if style == "mustache":
        return (f'<path d="M96,120 Q110,114 124,120 Q118,125 110,123 Q102,125 96,120 Z" fill="{hc}"/>')
    if style == "goatee":
        return (f'<path d="M97,120 Q110,115 123,120 Q116,125 110,123 Q104,125 97,120 Z" fill="{hc}"/>'
                f'<path d="M101,130 Q110,150 119,130 Q110,137 101,130 Z" fill="{hc}"/>'
                f'<path d="M101,130 Q110,150 119,130 Q110,137 101,130 Z" fill="{hc_d}" opacity="0.5"/>')
    if style == "full":
        return (f'<path d="M60,92 Q64,142 110,158 Q156,142 160,92 Q154,132 132,138 '
                f'Q124,130 110,130 Q96,130 88,138 Q66,132 60,92 Z" fill="{hc}"/>'
                f'<path d="M60,92 Q64,142 110,158 Q90,140 84,110 Q80,96 78,88 Z" fill="{hc_d}" opacity="0.55"/>'
                f'<path d="M96,120 Q110,114 124,120 Q110,126 96,120 Z" fill="{hc_d}"/>')
    return ""
