"""Living division: rival roster with memory, rankings, NPC fight sim, calendar, contract offers."""

from __future__ import annotations

import random

from . import content as C

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

FINISH_METHODS = {"KO", "TKO", "TKO (cut)", "Submission"}


def _uid(world) -> str:
    world["seq"] = world.get("seq", 0) + 1
    return f"f{world['seq']}"


def _person(used: set) -> tuple[str, str, str]:
    for _ in range(200):
        code, name, nick = C.random_person(random)
        if name not in used:
            return code, name, nick
    code, name, nick = C.random_person(random)
    return code, f"{name} {random.randint(2, 9)}", nick


def _diff_opp(world) -> float:
    return C.DIFFICULTY.get(world.get("difficulty", "normal"), C.DIFFICULTY["normal"])["opp"]


def make_npc(world, weight: str, tier: int, rank: int, used: set) -> dict:
    style_key = random.choice(list(C.STYLES))
    style = C.STYLES[style_key]
    lvl = C.TIERS[tier]["opp_base"] + (C.DIVISION_SIZE - rank) * 1.5 + _diff_opp(world) + random.uniform(-5, 5)
    attrs = {}
    for k in C.ATTRS:
        v = lvl + style["mods"].get(k, 0) + random.uniform(-6, 6)
        attrs[k] = int(max(20, min(97, v)))
    code, name, nick = _person(used)
    used.add(name)
    fights = max(3, rank + tier * 5 + random.randint(0, 10))
    wins = int(fights * random.uniform(0.5, 0.82))
    losses = max(0, fights - wins - random.randint(0, 2))
    return {
        "id": _uid(world),
        "name": name, "nickname": nick, "weight": weight, "nation": code,
        "style": style_key, "attrs": attrs, "tier": tier,
        "look": C.random_look(random),
        "wear": random.randint(0, 2),
        "record": {"w": wins, "l": losses, "d": 0},
        "rank": rank, "champion": False,
        "age": random.randint(23, 34),
        "hype": max(0, 40 - rank * 3 + random.randint(-5, 10)),
        "form": [],
        "is_player": False, "retired": False,
        "ko": int(wins * random.uniform(0.2, 0.5)),
        "sub": int(wins * random.uniform(0.1, 0.35)),
    }


def build_division(world: dict, weight: str, tier: int, player: dict) -> None:
    used = {player["name"]}
    fighters = {}
    player_rank = player.get("rank", C.DIVISION_SIZE)
    for r in range(1, C.DIVISION_SIZE + 1):
        if r == player_rank:
            continue
        npc = make_npc(world, weight, tier, r, used)
        fighters[npc["id"]] = npc
    champ = next((f for f in fighters.values() if f["rank"] == 1), None)
    if champ:
        champ["champion"] = True
        world["champion_id"] = champ["id"]
    else:
        world["champion_id"] = None
    world["division"] = fighters
    world["weight"] = weight
    world["tier"] = tier


def roster(world: dict) -> list[dict]:
    return sorted(world.get("division", {}).values(), key=lambda f: f["rank"])


# --- other weight divisions (flavour: champions + a short roster) ----------

EXT_SIZE = 8


def ensure_other_divisions(world: dict) -> None:
    ext = world.setdefault("ext_div", {})
    player_weight = world.get("weight")
    tier = world.get("tier", 0)
    for wkey, _label, _mod in C.WEIGHT_CLASSES:
        if wkey == player_weight or wkey in ext:
            continue
        used: set = set()
        ext[wkey] = [make_npc(world, wkey, tier, r, used) for r in range(1, EXT_SIZE + 1)]
        ext[wkey][0]["champion"] = True


def advance_other_divisions(world: dict) -> None:
    for fighters in world.get("ext_div", {}).values():
        active = [f for f in fighters if not f.get("retired")]
        if len(active) < 2:
            continue
        a, b = random.sample(active, 2)
        wnr, lsr, mth, _ = quick_sim(a, b)
        _apply_npc_result(wnr, lsr, mth)
        wnr["form"] = (wnr.get("form", []) + ["W"])[-5:]
        lsr["form"] = (lsr.get("form", []) + ["L"])[-5:]
        for f in fighters:
            f["age"] = f.get("age", 27) + C.AGE_PER_FIGHT / 2
        fighters.sort(key=lambda f: f["rank"])
        for i, f in enumerate(fighters, 1):
            f["rank"] = i
            f["champion"] = i == 1


def all_divisions(state: dict) -> list[dict]:
    """Player's division + the others, for the overview page."""
    world = state["world"]
    ensure_other_divisions(world)
    sync_player(state)
    out = [{
        "weight": world["weight"], "label": C.WEIGHT_LABELS[world["weight"]],
        "mine": True, "roster": roster(world)[:EXT_SIZE],
        "champ": get_fighter(world, world.get("champion_id")),
    }]
    for wkey, label, _mod in C.WEIGHT_CLASSES:
        if wkey == world["weight"]:
            continue
        fs = sorted(world["ext_div"].get(wkey, []), key=lambda f: f["rank"])
        out.append({"weight": wkey, "label": label, "mine": False,
                    "roster": fs, "champ": fs[0] if fs else None})
    order = {w: i for i, (w, _l, _m) in enumerate(C.WEIGHT_CLASSES)}
    out.sort(key=lambda d: order.get(d["weight"], 99))
    return out


def get_fighter(world: dict, fid: str) -> dict | None:
    return world.get("division", {}).get(fid)


# --- quick NPC-vs-NPC sim -------------------------------------------

def _power(f: dict) -> float:
    a = f["attrs"]
    return (a["power"] * 1.1 + a["striking"] * 1.2 + a["wrestling"] + a["bjj"]
            + a["cardio"] * 0.9 + a["chin"] * 0.8) / 6.0


def quick_sim(a: dict, b: dict) -> tuple[dict, dict, str, int]:
    pa, pb = _power(a), _power(b)
    edge = pa - pb + random.uniform(-14, 14)
    winner, loser = (a, b) if edge >= 0 else (b, a)
    margin = abs(edge)
    rr = random.random()
    if margin > 16 and rr < 0.45:
        method = random.choice(["KO", "TKO", "Submission"])
        rnd = random.randint(1, 3)
    elif margin > 8 and rr < 0.3:
        method = random.choice(["TKO", "Submission"])
        rnd = random.randint(2, 3)
    else:
        method = "Unanimous decision" if margin > 6 else "Split decision"
        rnd = 3
    return winner, loser, method, rnd


def _apply_npc_result(w, l, method):
    w["record"]["w"] += 1
    l["record"]["l"] += 1
    w["form"] = (w.get("form", []) + ["W"])[-5:]
    l["form"] = (l.get("form", []) + ["L"])[-5:]
    if method in ("KO", "TKO"):
        w["ko"] = w.get("ko", 0) + 1
    elif method == "Submission":
        w["sub"] = w.get("sub", 0) + 1
    w["hype"] = w.get("hype", 0) + (6 if method.endswith("decision") else 12)
    l["hype"] = max(0, l.get("hype", 0) - 8)
    if w["rank"] > l["rank"]:
        w["rank"], l["rank"] = l["rank"], w["rank"]


def advance(world: dict, player: dict, months: int = C.MONTHS_BETWEEN_FIGHTS) -> list[str]:
    news: list[str] = []
    y, m = world.get("year", 1), world.get("month", 1)
    m += months
    while m > 12:
        m -= 12
        y += 1
    world["year"], world["month"] = y, m

    div = world.get("division", {})
    active = [f for f in div.values() if not f["retired"] and f["id"] != player.get("id")]
    if not active:
        return news
    active.sort(key=lambda f: f["rank"])

    champ = get_fighter(world, world.get("champion_id"))
    contender = next((f for f in active if f["rank"] == 1 and not f["champion"]), None)
    if champ and not champ["is_player"] and contender and random.random() < 0.5:
        wnr, lsr, mth, rnd = quick_sim(champ, contender)
        _apply_npc_result(wnr, lsr, mth)
        if wnr is contender:
            champ["champion"] = False
            contender["champion"] = True
            contender["rank"] = 1
            champ["rank"] = 2
            world["champion_id"] = contender["id"]
            news.append(f"NEW {C.TIERS[world['tier']]['short']} CHAMPION: {contender['name']} beat {champ['name']} ({mth}).")
        else:
            news.append(f"{champ['name']} retains the belt against {contender['name']} ({mth}).")

    # most of the division is on the card too - fill the rest of the fight night
    pool = [f for f in active if not f["champion"]]
    random.shuffle(pool)
    max_pairs = max(3, len(pool) // 2 - 1)
    pairs = 0
    usedids = set()
    for a in pool:
        if pairs >= max_pairs:
            break
        if a["id"] in usedids:
            continue
        cand = [b for b in pool if b["id"] not in usedids and b["id"] != a["id"]
                and abs(b["rank"] - a["rank"]) <= 5]
        if not cand:
            continue
        b = random.choice(cand)
        usedids.update({a["id"], b["id"]})
        wnr, lsr, mth, rnd = quick_sim(a, b)
        _apply_npc_result(wnr, lsr, mth)
        pairs += 1
        if mth in FINISH_METHODS or abs(a["rank"] - b["rank"]) <= 6 or wnr["rank"] > lsr["rank"]:
            tag = f" ({mth}, R{rnd})" if mth in FINISH_METHODS else f" ({mth})"
            news.append(f"{wnr['name']} def. {lsr['name']}{tag}.")

    for f in list(div.values()):
        if f["is_player"] or f["retired"]:
            continue
        f["age"] += C.AGE_PER_FIGHT
        if f["age"] >= 36 and random.random() < 0.12 + (f["age"] - 36) * 0.05:
            f["retired"] = True
            news.append(f"{f['name']} ({f['record']['w']}-{f['record']['l']}) retires.")
    _refill(world, player, news)
    _renumber(world, player)
    if world.get("ext_div"):
        advance_other_divisions(world)
    return news


def _refill(world, player, news):
    div = world["division"]
    used = {f["name"] for f in div.values()} | {player["name"]}
    while len([f for f in div.values() if not f["retired"]]) < C.DIVISION_SIZE:
        npc = make_npc(world, world["weight"], world["tier"], C.DIVISION_SIZE, used)
        used.add(npc["name"])
        div[npc["id"]] = npc
        news.append(f'Division newcomer: {npc["name"]} "{npc["nickname"]}".')


def _renumber(world, player):
    div = world["division"]
    active = sorted([f for f in div.values() if not f["retired"]], key=lambda f: f["rank"])
    rank = 1
    for f in active:
        f["rank"] = rank
        rank += 1
    champ = get_fighter(world, world.get("champion_id"))
    if not champ or champ["retired"]:
        world["champion_id"] = None
        for f in active:
            f["champion"] = False


def pick_opponent(world: dict, player: dict) -> dict:
    div = world.get("division", {})
    pr = player.get("rank", C.DIVISION_SIZE)
    cands = [f for f in div.values() if not f["retired"] and not f["is_player"]]
    if player.get("champion"):
        cands.sort(key=lambda f: f["rank"])
        return cands[0]
    better = [f for f in cands if 0 < pr - f["rank"] <= 3]
    near = [f for f in cands if abs(f["rank"] - pr) <= 2]
    pool = better or near or cands
    return random.choice(pool)


# --- rivalries -------------------------------------------------------

def rivalry(player: dict, opp_id: str) -> dict:
    return player.setdefault("rivalries", {}).setdefault(opp_id, {
        "fights": 0, "pw": 0, "ow": 0, "draws": 0, "heat": 0, "log": [], "name": ""})


def update_rivalry(player, opp, outcome, method, rnd):
    r = rivalry(player, opp["id"])
    r["name"] = opp["name"]
    r["fights"] += 1
    if outcome == "win":
        r["pw"] += 1
    elif outcome == "loss":
        r["ow"] += 1
    else:
        r["draws"] += 1
    heat = 6
    if method == "Split decision":
        heat += 10
    if method in FINISH_METHODS:
        heat += 6
    if r["fights"] >= 2:
        heat += 8
    r["heat"] = min(100, r["heat"] + heat)
    r["log"].insert(0, f"{'W' if outcome == 'win' else 'L' if outcome == 'loss' else 'D'} - {method}, R{rnd}")
    return r


# --- contract offers ------------------------------------------------

def maybe_offer(state: dict) -> None:
    f = state["fighter"]
    if f["tier"] >= C.MAX_TIER:
        return
    if state.get("offers"):
        return
    c = f.get("contract") or {}
    near_end = c.get("fights_left", 99) <= 1
    enough_def = f["champion"] and f["title_defenses"] >= C.TIERS[f["tier"]]["defenses_to_promote"]
    if not (near_end or enough_def):
        return
    nxt = C.TIERS[f["tier"] + 1]
    cur = C.TIERS[f["tier"]]
    merit = enough_def or f["champion"] or f["rank"] <= 5 or f["win_streak"] >= 3
    offers = [
        {"id": "stay", "org": cur["name"], "tier": f["tier"],
         "purse": int(cur["purse"] * 1.4) or 500, "bonus": int(cur["win_bonus"] * 1.3),
         "fights": 4, "hype_mult": 1.0,
         "desc": "Stay with this promotion and build your resume. Safer, slower."},
    ]
    if merit:
        offers.append({"id": "up_money", "org": nxt["name"], "tier": f["tier"] + 1,
                       "purse": nxt["purse"], "bonus": nxt["win_bonus"], "fights": 3, "hype_mult": 1.15,
                       "desc": "Step up a level. Tougher field, much bigger money."})
        offers.append({"id": "up_expo", "org": nxt["name"], "tier": f["tier"] + 1,
                       "purse": int(nxt["purse"] * 0.6), "bonus": int(nxt["win_bonus"] * 0.6),
                       "fights": 5, "hype_mult": 1.5,
                       "desc": "Exposure deal - less money, more spotlight, fast track to a title shot."})
    else:
        offers.append({"id": "prove", "org": cur["name"], "tier": f["tier"],
                       "purse": max(300, int(cur["purse"] * 0.9)), "bonus": int(cur["win_bonus"]),
                       "fights": 3, "hype_mult": 0.95,
                       "desc": "Short prove-it deal. String some wins together and better offers come."})
    state["offers"] = offers


def sign(state: dict, offer_id: str) -> dict | None:
    offers = state.get("offers") or []
    offer = next((o for o in offers if o["id"] == offer_id), None)
    if not offer:
        return None
    f = state["fighter"]
    promoted = offer["tier"] > f["tier"]
    f["contract"] = {
        "org": offer["org"], "tier": offer["tier"],
        "purse": offer["purse"], "bonus": offer["bonus"],
        "fights_left": offer["fights"], "hype_mult": offer["hype_mult"],
    }
    if promoted:
        f["tier"] = offer["tier"]
        f["rank"] = C.DIVISION_SIZE
        f["champion"] = False
        f["title_shot"] = False
        f["title_defenses"] = 0
        build_division(state["world"], f["weight"], f["tier"], f)
        sync_player(state)
    state.pop("offers", None)
    return offer


def _player_shadow(f: dict) -> dict:
    return {
        "id": f["id"], "name": f["name"], "nickname": f["nickname"], "weight": f["weight"],
        "style": f["style"], "attrs": f["attrs"], "record": f["record"], "tier": f["tier"],
        "belts": f.get("belts", []), "win_streak": f.get("win_streak", 0),
        "nation": f.get("nation", "USA"),
        "look": f.get("look", C.DEFAULT_LOOK),
        "wear": int(f.get("fights", 0) > 8) + int(f.get("fights", 0) > 20) + int(f.get("brain", 100) < 68),
        "rank": f["rank"], "champion": f["champion"], "age": int(f["age"]),
        "hype": f["hype"], "form": f.get("form", []), "is_player": True, "retired": f["retired"],
        "ko": f["ko_wins"], "sub": f["sub_wins"],
    }


def sync_player(state: dict) -> None:
    f = state["fighter"]
    world = state["world"]
    div = world.setdefault("division", {})
    div[f["id"]] = _player_shadow(f)
    if f["champion"]:
        world["champion_id"] = f["id"]
    _renumber(world, f)


def date_str(world: dict) -> str:
    return f"{MONTHS[world.get('month', 1) - 1]} {2020 + world.get('year', 1)}"
