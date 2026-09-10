"""Player feedback: appended to saves/_feedback.jsonl (global, not per-visitor). Read from the admin panel."""

from __future__ import annotations

import json
import re
import time
from collections import Counter

from . import content as C
from . import game as G

KINDS = ("idea", "bug", "other")

# --- lightweight site stats ----------------------------------------

_STATS: dict | None = None
_SEEN_TODAY: set = set()
_SEEN_HOUR: set = set()


def _stats_file():
    return G.SAVES_DIR / "_stats.json"


def _load_stats() -> dict:
    global _STATS
    if _STATS is None:
        try:
            _STATS = json.loads(_stats_file().read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            _STATS = {}
        _STATS.setdefault("requests", 0)
        _STATS.setdefault("by_day", {})
        _STATS.setdefault("dau", {})
        _STATS.setdefault("by_hour", {})     # "YYYY-MM-DD HH" -> request count
        _STATS.setdefault("hau", {})         # "YYYY-MM-DD HH" -> unique visitors
        _STATS.setdefault("by_path", {})
        _STATS.setdefault("started", time.time())
        _STATS.setdefault("sims", 0)
        _STATS.setdefault("fight_actions", 0)
        _STATS.setdefault("careers_created", 0)
    return _STATS


def _flush() -> None:
    if _STATS is None:
        return
    try:
        G.SAVES_DIR.mkdir(parents=True, exist_ok=True)
        _stats_file().write_text(json.dumps(_STATS), encoding="utf-8")
    except OSError:
        pass


def bump(path: str, ns: str = "", event: str = "") -> None:
    if path.startswith(("/static", "/avatar", "/admin")) or path in ("/favicon.ico", "/ads.txt", "/robots.txt"):
        return
    s = _load_stats()
    s["requests"] += 1
    now = time.localtime()
    day = time.strftime("%Y-%m-%d", now)
    hour = time.strftime("%Y-%m-%d %H", now)
    s["by_day"][day] = s["by_day"].get(day, 0) + 1
    s["by_hour"][hour] = s["by_hour"].get(hour, 0) + 1
    p = re.sub(r"/[0-9]+(\.[0-9]+)?", "/:n", re.sub(r"/[a-f0-9]{12,}", "/:id", path)) or "/"
    s["by_path"][p] = s["by_path"].get(p, 0) + 1
    key = f"{day}|{ns}"
    if ns and key not in _SEEN_TODAY:
        _SEEN_TODAY.add(key)
        s["dau"][day] = s["dau"].get(day, 0) + 1
    hkey = f"{hour}|{ns}"
    if ns and hkey not in _SEEN_HOUR:
        _SEEN_HOUR.add(hkey)
        s["hau"][hour] = s["hau"].get(hour, 0) + 1
    if event == "sim":
        s["sims"] += 1
    elif event == "fight_action":
        s["fight_actions"] += 1
    elif event == "career":
        s["careers_created"] += 1
    # trim history
    if len(s["by_day"]) > 120:
        for d in sorted(s["by_day"])[:-120]:
            s["by_day"].pop(d, None); s["dau"].pop(d, None)
    if len(s["by_hour"]) > 168:                     # keep ~1 week of hours
        for h in sorted(s["by_hour"])[:-168]:
            s["by_hour"].pop(h, None); s["hau"].pop(h, None)
    if len(_SEEN_HOUR) > 4000:                      # drop stale per-hour dedupe keys
        _SEEN_HOUR.difference_update({k for k in _SEEN_HOUR if not k.startswith(hour + "|")})
    if s["requests"] % 20 == 0:
        _flush()


def site_stats() -> dict:
    s = _load_stats()
    days = sorted(s["by_day"])[-14:]
    series = [{"day": d[5:], "reqs": s["by_day"].get(d, 0), "dau": s["dau"].get(d, 0)} for d in days]
    peak = max((r["reqs"] for r in series), default=1) or 1
    for r in series:
        r["pct"] = round(100 * r["reqs"] / peak)
    up = time.time() - s.get("started", time.time())
    today = time.strftime("%Y-%m-%d")
    cur_hour = int(time.strftime("%H"))
    hours = []
    for h in range(24):
        hk = f"{today} {h:02d}"
        hours.append({"h": h, "label": f"{h:02d}",
                      "reqs": s["by_hour"].get(hk, 0),
                      "visitors": s["hau"].get(hk, 0),
                      "now": h == cur_hour})
    hpeak = max((x["reqs"] for x in hours), default=1) or 1
    for x in hours:
        x["pct"] = round(100 * x["reqs"] / hpeak)
    return {
        "requests": s["requests"],
        "today": s["by_day"].get(today, 0),
        "dau_today": s["dau"].get(today, 0),
        "sims": s["sims"], "fight_actions": s["fight_actions"],
        "careers_created": s["careers_created"],
        "uptime_days": round(up / 86400, 1),
        "avg_per_day": round(s["requests"] / max(1, len(s["by_day"]))),
        "top_paths": sorted(s["by_path"].items(), key=lambda kv: -kv[1])[:10],
        "series": series,
        "hours": hours,
        "hours_visitors": sum(x["visitors"] for x in hours),
    }


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
