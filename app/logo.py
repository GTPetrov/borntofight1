"""Born to Fight mark: two crossed boxing gloves in the site palette.

Used for the favicon, the header lockup and the social share image.
"""

from __future__ import annotations

RED = "#e63946"
RED_DK = "#a5283a"
RED_DKR = "#71182a"
BLUE = "#4cc9f0"
BLUE_DK = "#2f8fbe"
BLUE_DKR = "#1f5f80"
WARM = "#f4a261"
WARM_DK = "#d97e37"
LACE = "#f7f3ec"

# One glove pointing RIGHT: long wrist wrap on the left, fist on the right,
# thumb on top. Long and lean so two of them read as an X when crossed.
_GLOVE = (
    # wrist wrap
    '<path d="M-96,-17 h64 v34 h-64 q-9,0 -9,-9 v-16 q0,-9 9,-9 Z" fill="{cuff}"/>'
    '<path d="M-84,-17 l10,34 M-68,-17 l10,34 M-52,-17 l10,34" '
    'stroke="{cuffdk}" stroke-width="4" opacity="0.55"/>'
    '<path d="M-96,-17 h64 v7 h-70 q0,-7 6,-7 Z" fill="#ffffff" opacity="0.14"/>'
    # fist
    '<path d="M-34,-26 C-6,-34 44,-33 50,-3 C54,19 39,35 12,35 '
    'C-14,35 -34,22 -36,-2 C-37,-12 -37,-22 -34,-26 Z" fill="{fill}"/>'
    # thumb
    '<path d="M-20,-27 C-27,-44 -9,-53 2,-46 C10,-41 8,-27 -2,-23 '
    'C-9,-20 -16,-22 -20,-27 Z" fill="{fill}"/>'
    # form shadow (underside)
    '<path d="M50,-3 C54,19 39,35 12,35 C-14,35 -34,22 -36,-2 '
    'C-26,14 -6,22 14,20 C34,18 44,4 43,-14 C46,-12 49,-9 50,-3 Z" '
    'fill="{dark}" opacity="0.45"/>'
    # knuckle sheen
    '<ellipse cx="10" cy="-15" rx="17" ry="9" fill="#ffffff" opacity="0.16"/>'
    # seam where fist meets wrap
    '<path d="M-33,30 C-42,8 -42,-12 -34,-30" stroke="{lace}" stroke-width="4" '
    'fill="none" stroke-linecap="round"/>'
)


def _glove(fill: str, dark: str) -> str:
    return _GLOVE.format(fill=fill, dark=dark, cuff=WARM, cuffdk=WARM_DK, lace=LACE)


def mark(size: int = 64, bg: str | None = None) -> str:
    """Crossed-gloves mark as a standalone <svg> string - one blue glove, one
    red, fists raised, wrist wraps crossing below."""
    bg_rect = f'<rect width="200" height="200" rx="36" fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" '
        f'width="{size}" height="{size}" role="img" aria-label="Born to Fight">'
        f'{bg_rect}'
        # blue glove: fist raised to the upper-left, wrap crossing down-right
        f'<g transform="translate(100,104) rotate(-135) translate(62,-5)">'
        f'{_glove(BLUE, BLUE_DK)}</g>'
        # red glove: fist raised to the upper-right (drawn last -> on top)
        f'<g transform="translate(100,104) rotate(-45) translate(62,5)">'
        f'{_glove(RED, RED_DK)}</g>'
        f'</svg>'
    )
