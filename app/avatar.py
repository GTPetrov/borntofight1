"""Generator portretu zawodnika – składany inline SVG na podstawie słownika wyglądu."""

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

SHOULDER_W = {"wiry": 150, "athletic": 180, "hulk": 212}


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


def url(look: dict | None, size: int = 120, wear: int = 0) -> str:
    from urllib.parse import urlencode
    q = {k: v for k, v in (look or {}).items() if k in DEFAULT_LOOK}
    q["size"] = size
    q["wear"] = wear
    return "/avatar.svg?" + urlencode(q)


def portrait(look: dict | None, size: int = 180, wear: int = 0) -> str:
    L = {**DEFAULT_LOOK, **(look or {})}
    skin = L["skin"]
    skin_d = _shade(skin, 0.82)
    skin_dd = _shade(skin, 0.68)
    hc = L["hair_color"]
    hcd = _shade(hc, 0.8)
    sw = SHOULDER_W.get(L["build"], 180)
    tx = 110 - sw / 2

    p = [
        f'<svg viewBox="0 0 220 220" width="{size}" height="{size}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="portret zawodnika">',
        '<rect width="220" height="220" fill="#12171f"/>',
        '<rect y="150" width="220" height="70" fill="#0e131a"/>',
        # tors + barki
        f'<path d="M{tx},220 L{110 - sw * 0.30},150 Q110,120 {110 + sw * 0.30},150 '
        f'L{110 + sw / 2},220 Z" fill="{skin}"/>',
        f'<path d="M110,138 L110,180 M90,168 Q110,178 130,168 M78,150 Q88,158 90,150 '
        f'M142,150 Q132,158 130,150" stroke="{skin_d}" stroke-width="3" fill="none" opacity="0.6"/>',
        # szorty
        f'<rect x="{tx + 6}" y="196" width="{sw - 12}" height="24" rx="4" fill="{L["trunks"]}"/>',
        f'<rect x="{tx + 6}" y="196" width="{sw - 12}" height="6" fill="{_shade(L["trunks"], 1.3)}"/>',
        # szyja
        f'<path d="M96,120 h28 v22 q-14,10 -28,0 Z" fill="{skin_d}"/>',
        # uszy
        f'<ellipse cx="63" cy="96" rx="9" ry="13" fill="{skin}"/>',
        f'<ellipse cx="157" cy="96" rx="9" ry="13" fill="{skin}"/>',
    ]
    if wear >= 2:  # kalafiorowe ucho
        p.append(f'<ellipse cx="157" cy="99" rx="8" ry="10" fill="{skin_dd}"/>')
    # głowa
    p.append(f'<ellipse cx="110" cy="88" rx="47" ry="55" fill="{skin}"/>')
    p.append(f'<path d="M70,120 Q110,150 150,120 Q140,138 110,140 Q80,138 70,120 Z" fill="{skin_d}" opacity="0.5"/>')

    # brwi
    p.append(f'<path d="M76,74 L100,68" stroke="{hcd}" stroke-width="7" stroke-linecap="round"/>')
    p.append(f'<path d="M144,74 L120,68" stroke="{hcd}" stroke-width="7" stroke-linecap="round"/>')
    # oczy
    for ex in (91, 129):
        p.append(f'<ellipse cx="{ex}" cy="84" rx="8" ry="4.5" fill="#fcfcfc"/>')
        p.append(f'<circle cx="{ex + 1}" cy="84" r="3" fill="#22160e"/>')
    # blizna nad brwią
    if wear >= 1:
        p.append('<path d="M118,60 L127,72" stroke="#b07059" stroke-width="3" stroke-linecap="round"/>')
    # nos
    crook = 5 if wear >= 3 else 0
    p.append(f'<path d="M110,84 L{103 - crook},112 Q110,118 117,112 Z" fill="{skin_d}"/>')
    # usta
    p.append('<path d="M97,128 Q110,135 123,128" stroke="#8a4a46" stroke-width="4" '
             'fill="none" stroke-linecap="round"/>')

    p.append(_hair(L["hair"], hc, hcd))
    p.append(_beard(L["beard"], hc))

    # rękawice u dołu
    gc = _shade(L["trunks"], 0.55)
    p.append(f'<ellipse cx="30" cy="214" rx="22" ry="18" fill="{gc}"/>')
    p.append(f'<ellipse cx="190" cy="214" rx="22" ry="18" fill="{gc}"/>')

    p.append('</svg>')
    return "".join(x for x in p if x)


def _hair(style, hc, hcd):
    if style == "bald":
        return (f'<path d="M66,74 Q110,44 154,74 Q150,60 110,56 Q70,60 66,74 Z" '
                f'fill="#ffffff" opacity="0.06"/>')
    if style == "buzz":
        return (f'<path d="M64,86 Q64,36 110,32 Q156,36 156,86 Q150,52 110,48 Q70,52 64,86 Z" '
                f'fill="{hc}" opacity="0.8"/>')
    if style == "short":
        return (f'<path d="M62,92 Q60,34 110,30 Q160,34 158,92 Q150,54 110,50 Q70,54 62,92 Z" fill="{hc}"/>'
                f'<path d="M62,92 Q66,70 72,82 L70,96 Z" fill="{hcd}"/>'
                f'<path d="M158,92 Q154,70 148,82 L150,96 Z" fill="{hcd}"/>')
    if style == "mohawk":
        return (f'<path d="M62,92 Q64,60 88,52 Q80,66 82,90 Z" fill="{hcd}"/>'
                f'<path d="M158,92 Q156,60 132,52 Q140,66 138,90 Z" fill="{hcd}"/>'
                f'<path d="M99,24 Q110,20 121,24 L118,64 Q110,58 102,64 Z" fill="{hc}"/>'
                f'<path d="M99,24 Q110,20 121,24 L119,34 Q110,30 101,34 Z" fill="{_shade(hc, 1.25)}"/>')
    if style == "long":
        return (f'<path d="M58,96 Q56,32 110,28 Q164,32 162,96 L162,166 Q150,150 150,96 '
                f'Q150,52 110,48 Q70,52 70,96 Q70,150 58,166 Z" fill="{hc}"/>'
                f'<path d="M70,50 Q110,40 150,50 Q110,58 70,50 Z" fill="{hcd}"/>')
    if style == "corn":
        rows = "".join(
            f'<path d="M{x},40 Q{x},70 {x + (6 if x > 110 else -6)},96" stroke="{hc}" '
            f'stroke-width="5.5" fill="none" stroke-linecap="round"/>'
            for x in (84, 97, 110, 123, 136))
        return (f'<path d="M64,84 Q110,40 156,84 Q150,50 110,46 Q70,50 64,84 Z" fill="{hcd}"/>{rows}')
    return ""


def _beard(style, hc):
    if style in ("", "none"):
        return ""
    if style == "stubble":
        return (f'<path d="M64,96 Q72,150 110,160 Q148,150 156,96 Q146,132 110,134 '
                f'Q74,132 64,96 Z" fill="{hc}" opacity="0.26"/>')
    if style == "mustache":
        return f'<path d="M95,122 Q110,116 125,122 Q110,130 95,122 Z" fill="{hc}"/>'
    if style == "goatee":
        return (f'<path d="M95,122 Q110,116 125,122 Q110,129 95,122 Z" fill="{hc}"/>'
                f'<path d="M100,134 Q110,158 120,134 Q110,142 100,134 Z" fill="{hc}"/>')
    if style == "full":
        return (f'<path d="M62,92 Q68,152 110,166 Q152,152 158,92 Q154,140 130,144 '
                f'Q124,136 110,136 Q96,136 90,144 Q66,140 62,92 Z" fill="{hc}"/>'
                f'<path d="M95,122 Q110,116 125,122 Q110,129 95,122 Z" fill="{_shade(hc, 0.88)}"/>')
    return ""
