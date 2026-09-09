"""Tiny inline SVG flags (3:2). Simplified but recognizable - renders everywhere,
unlike emoji flags which Windows shows as two-letter codes."""

from __future__ import annotations

# each value is the inner markup for a viewBox="0 0 3 2" svg
_F: dict[str, str] = {
    "POL": '<rect width="3" height="2" fill="#fff"/><rect y="1" width="3" height="1" fill="#dc143c"/>',
    "RUS": '<rect width="3" height="2" fill="#fff"/><rect y=".667" width="3" height=".666" fill="#0039a6"/>'
           '<rect y="1.333" width="3" height=".667" fill="#d52b1e"/>',
    "NLD": '<rect width="3" height="2" fill="#fff"/><rect width="3" height=".667" fill="#ae1c28"/>'
           '<rect y="1.333" width="3" height=".667" fill="#21468b"/>',
    "FRA": '<rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#002395"/>'
           '<rect x="2" width="1" height="2" fill="#ed2939"/>',
    "IRL": '<rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#169b62"/>'
           '<rect x="2" width="1" height="2" fill="#ff883e"/>',
    "MEX": '<rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#006847"/>'
           '<rect x="2" width="1" height="2" fill="#ce1126"/><circle cx="1.5" cy="1" r=".28" fill="#8c6239"/>',
    "NGA": '<rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#008751"/>'
           '<rect x="2" width="1" height="2" fill="#008751"/>',
    "SWE": '<rect width="3" height="2" fill="#006aa7"/><rect x=".9" width=".4" height="2" fill="#fecc00"/>'
           '<rect y=".8" width="3" height=".4" fill="#fecc00"/>',
    "GEO": '<rect width="3" height="2" fill="#fff"/><rect x="1.25" width=".5" height="2" fill="#ff0000"/>'
           '<rect y=".75" width="3" height=".5" fill="#ff0000"/>',
    "JPN": '<rect width="3" height="2" fill="#fff"/><circle cx="1.5" cy="1" r=".55" fill="#bc002d"/>',
    "KOR": '<rect width="3" height="2" fill="#fff"/>'
           '<path d="M1.5 .45 A.55 .55 0 0 1 1.5 1.55 A.275 .275 0 0 0 1.5 1 A.275 .275 0 0 1 1.5 .45" fill="#cd2e3a"/>'
           '<path d="M1.5 1.55 A.55 .55 0 0 1 1.5 .45 A.275 .275 0 0 1 1.5 1 A.275 .275 0 0 0 1.5 1.55" fill="#0047a0"/>',
    "BRA": '<rect width="3" height="2" fill="#009c3b"/><path d="M1.5 .25 2.75 1 1.5 1.75 .25 1z" fill="#ffdf00"/>'
           '<circle cx="1.5" cy="1" r=".42" fill="#002776"/>',
    "CAN": '<rect width="3" height="2" fill="#fff"/><rect width=".75" height="2" fill="#d52b1e"/>'
           '<rect x="2.25" width=".75" height="2" fill="#d52b1e"/>'
           '<path d="M1.5 .55 1.6 .85 1.9 .8 1.75 1.05 2 1.2 1.7 1.25 1.72 1.5 1.5 1.35 1.28 1.5 1.3 1.25 1 1.2 1.25 1.05 1.1 .8 1.4 .85z" fill="#d52b1e"/>',
    "USA": '<rect width="3" height="2" fill="#b22234"/>'
           '<g fill="#fff"><rect y=".154" width="3" height=".154"/><rect y=".462" width="3" height=".154"/>'
           '<rect y=".769" width="3" height=".154"/><rect y="1.077" width="3" height=".154"/>'
           '<rect y="1.385" width="3" height=".154"/><rect y="1.692" width="3" height=".154"/></g>'
           '<rect width="1.2" height="1.077" fill="#3c3b6e"/>',
    "GBR": '<rect width="3" height="2" fill="#012169"/>'
           '<path d="M0 0 3 2M3 0 0 2" stroke="#fff" stroke-width=".4"/>'
           '<path d="M0 0 3 2M3 0 0 2" stroke="#c8102e" stroke-width=".24"/>'
           '<path d="M1.5 0V2M0 1H3" stroke="#fff" stroke-width=".6"/>'
           '<path d="M1.5 0V2M0 1H3" stroke="#c8102e" stroke-width=".36"/>',
    "AUS": '<rect width="3" height="2" fill="#012169"/>'
           '<path d="M0 0 1.5 1M1.5 0 0 1M0 .5H1.5M.75 0V1" stroke="#fff" stroke-width=".22"/>'
           '<path d="M.75 0V1M0 .5H1.5" stroke="#c8102e" stroke-width=".13"/>'
           '<circle cx="2.25" cy="1.35" r=".14" fill="#fff"/><circle cx="2.55" cy=".7" r=".08" fill="#fff"/>'
           '<circle cx="2.05" cy=".55" r=".08" fill="#fff"/><circle cx="2.6" cy="1.55" r=".08" fill="#fff"/>'
           '<circle cx="1.95" cy="1.7" r=".07" fill="#fff"/><circle cx="0.75" cy="1.5" r=".12" fill="#fff"/>',
}


def svg(code: str, w: int = 22) -> str:
    body = _F.get(code, '<rect width="3" height="2" fill="#556"/>')
    h = round(w * 2 / 3)
    return (f'<svg class="flag" viewBox="0 0 3 2" width="{w}" height="{h}" '
            f'preserveAspectRatio="xMidYMid slice" aria-hidden="true">{body}</svg>')
