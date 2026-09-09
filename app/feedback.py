"""Player feedback: appended to saves/_feedback.jsonl (global, not per-visitor). Read from the admin panel."""

from __future__ import annotations

import json
import time
from collections import Counter

from . import content as C
from . import game as G

KINDS = ("idea", "bug", "other")


def _file():
    return G.SAVES_DIR / "_feedback.jsonl"


def add(text: str, kind: str, page: str = "", ns: str = "", fighter: str = "") -> bool:
    text = (text or "").strip()[:2000]
    if not text:
        return False
    kind = kind if kind in KINDS else "other"
    G.SAVES_DIR.mkdir(parents=True, exist_ok=True)
    rec = {"ts": round(time.time(), 3), "kind": kind, "text": text,
           "page": page[:200], "ns": ns[:16], "fighter": fighter[:60], "resolved": False}
    with _file().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return True


def all_items() -> list[dict]:
    p = _file()
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    out.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return out


def toggle_resolved(ts: float) -> None:
    items = list(reversed(all_items()))  # back to chronological for rewrite
    for r in items:
        if abs(r.get("ts", 0) - ts) < 0.0015:
            r["resolved"] = not r.get("resolved", False)
    _file().write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in items) + ("\n" if items else ""),
        encoding="utf-8")


def recent_rate(ns: str, window: int = 120) -> int:
    now = time.time()
    return sum(1 for r in all_items() if r.get("ns") == ns and now - r.get("ts", 0) < window)


# --- world stats for the admin panel --------------------------------

def world_stats() -> dict:
    root = G.SAVES_DIR
    players = careers = retired = champs = total_fights = 0
    tiers = Counter(); styles = Counter(); weights = Counter(); modes = Counter(); diff = Counter()
    top_records: list[tuple] = []
    if root.exists():
        for ns_dir in root.iterdir():
            if not ns_dir.is_dir():
                continue
            saves = list(ns_dir.glob("*.json"))
            if not saves:
                continue
            players += 1
            for sp in saves:
                try:
                    s = json.loads(sp.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                f = s.get("fighter", {})
                if not f:
                    continue
                careers += 1
                total_fights += f.get("fights", 0)
                retired += 1 if f.get("retired") else 0
                champs += 1 if f.get("champion") else 0
                tiers[C.TIERS[min(f.get("tier", 0), len(C.TIERS) - 1)]["short"]] += 1
                styles[C.STYLES.get(f.get("style"), {}).get("label", f.get("style", "?"))] += 1
                weights[C.WEIGHT_LABELS.get(f.get("weight", ""), "?")] += 1
                modes[C.GAME_MODES.get(f.get("mode", "standard"), {}).get("label", "?")] += 1
                diff[C.DIFFICULTY.get(f.get("difficulty", "normal"), {}).get("label", "?")] += 1
                rec = f.get("record", {})
                top_records.append((
                    rec.get("w", 0), -(rec.get("l", 0)),
                    f'{f.get("name", "?")}  {rec.get("w", 0)}-{rec.get("l", 0)}-{rec.get("d", 0)}  '
                    f'{C.TIERS[min(f.get("tier", 0), len(C.TIERS) - 1)]["short"]}'
                    f'{"  (champ)" if f.get("champion") else ""}'
                    f'{"  [retired]" if f.get("retired") else ""}'))
    top_records.sort(reverse=True)
    fb = all_items()
    return {
        "players": players, "careers": careers, "retired": retired, "champions": champs,
        "total_fights": total_fights,
        "tiers": tiers.most_common(), "styles": styles.most_common(),
        "weights": weights.most_common(), "modes": modes.most_common(),
        "difficulty": diff.most_common(),
        "top_records": [t[2] for t in top_records[:15]],
        "feedback_total": len(fb),
        "feedback_open": sum(1 for r in fb if not r.get("resolved")),
    }
