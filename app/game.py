"""Career state, save slots, character creation, camp + staff, weight cut, fight resolution, legacy."""

from __future__ import annotations

import contextvars
import json
import random
import re
import time
from pathlib import Path

from . import content as C
from . import world as W

ROOT = Path(__file__).resolve().parent.parent
SAVES_DIR = ROOT / "saves"

FINISH_METHODS = W.FINISH_METHODS

# Per-visitor isolation: middleware sets this from the visitor's cookie so each
# browser gets its own careers under saves/<namespace>/. TEST_NS forces a fixed
# namespace in tests (which also make bare G.* calls outside any request).
_ns: contextvars.ContextVar[str | None] = contextvars.ContextVar("bt_ns", default=None)
TEST_NS: str | None = None


def set_namespace(ns: str | None) -> None:
    _ns.set(ns or None)


def _base() -> Path:
    ns = TEST_NS if TEST_NS is not None else _ns.get()
    return SAVES_DIR / ns if ns else SAVES_DIR


def _active_file() -> Path:
    return _base() / "_active.txt"


def legacy_file() -> Path:
    return _base() / "_legacy.json"


# --- Save slots --------------------------------------------------------

def _slug(s: str) -> str:
    s = re.sub(r"[^\w-]+", "-", s.strip().lower(), flags=re.UNICODE).strip("-")
    return s or "career"


def _ensure_dir() -> None:
    _base().mkdir(parents=True, exist_ok=True)


def _path(slot: str) -> Path:
    return _base() / f"{slot}.json"


def list_saves() -> list[dict]:
    _ensure_dir()
    out = []
    for p in sorted(_base().glob("*.json")):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        f = s.get("fighter", {})
        out.append({
            "slot": p.stem,
            "name": f.get("name", "?"),
            "nickname": f.get("nickname", ""),
            "record": f.get("record", {"w": 0, "l": 0, "d": 0}),
            "tier": C.TIERS[f.get("tier", 0)]["short"],
            "champion": f.get("champion", False),
            "retired": f.get("retired", False),
            "mode": f.get("mode", "standard"),
            "created": s.get("created", 0),
            "look": f.get("look", C.DEFAULT_LOOK),
            "wear": wear(f),
        })
    out.sort(key=lambda x: x["created"], reverse=True)
    return out


def get_active() -> str | None:
    _ensure_dir()
    af = _active_file()
    if af.exists():
        slot = af.read_text(encoding="utf-8").strip()
        if _path(slot).exists():
            return slot
    return None


def set_active(slot: str) -> None:
    _ensure_dir()
    _active_file().write_text(slot, encoding="utf-8")


def load(slot: str | None = None) -> dict | None:
    slot = slot or get_active()
    if not slot:
        return None
    p = _path(slot)
    if not p.exists():
        return None
    try:
        s = json.loads(p.read_text(encoding="utf-8"))
        s["slot"] = slot
        return s
    except (json.JSONDecodeError, OSError):
        return None


def save(state: dict) -> None:
    _ensure_dir()
    slot = state.get("slot") or "career"
    state["slot"] = slot
    _path(slot).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_slot(slot: str) -> None:
    _path(slot).unlink(missing_ok=True)
    if get_active() == slot:
        _active_file().unlink(missing_ok=True)


def _free_slot(name: str) -> str:
    base = _slug(name)
    slot = base
    i = 2
    while _path(slot).exists():
        slot = f"{base}-{i}"
        i += 1
    return slot


# --- Character creation ------------------------------------------------

def default_attrs() -> dict:
    return {k: C.START_BASE for k in C.ATTRS}


def random_seed(points: int, rng=None) -> dict:
    """A randomized-but-valid starting point for the creation form."""
    rng = rng or random
    nation, name, nick = C.random_person(rng)
    attrs = {k: C.START_BASE for k in C.ATTRS}
    left = points
    keys = list(C.ATTRS)
    while left > 0:
        k = rng.choice(keys)
        if attrs[k] < C.START_ATTR_CAP:
            attrs[k] += 1
            left -= 1
    return {
        "name": name, "nickname": nick if rng.random() < 0.7 else "",
        "age": rng.randint(19, 29), "weight": rng.choice(list(C.WEIGHT_LABELS)),
        "style": rng.choice(list(C.STYLES)), "nation": nation,
        "look": C.random_look(rng), "attrs": attrs,
    }


def new_state(name, nickname, age, weight, style, attrs, legacy: dict | None = None,
              look: dict | None = None, difficulty="normal", mode="standard",
              nation="USA") -> dict:
    legacy = legacy or {}
    difficulty = difficulty if difficulty in C.DIFFICULTY else "normal"
    mode = mode if mode in C.GAME_MODES else "standard"
    world = {"seq": 0, "year": 1, "month": 1, "difficulty": difficulty, "mode": mode}
    fid = f"pf{int(time.time())}"
    look = {**C.DEFAULT_LOOK, **{k: v for k, v in (look or {}).items() if k in C.LOOKS}}
    a = {k: int(attrs[k]) for k in C.ATTRS}
    if look["build"] == "hulk":
        a["power"] = min(99, a["power"] + 2); a["cardio"] = max(15, a["cardio"] - 2)
    elif look["build"] == "wiry":
        a["cardio"] = min(99, a["cardio"] + 2); a["power"] = max(15, a["power"] - 2)
    f = {
        "id": fid,
        "name": name.strip() or "Nameless",
        "nickname": nickname.strip(),
        "age": float(age),
        "weight": weight,
        "style": style if style in C.STYLES else "balanced",
        "nation": nation if nation in C.NATIONS else "USA",
        "look": look,
        "difficulty": difficulty,
        "mode": mode,
        "attrs": a,
        "xp": {k: 0.0 for k in C.ATTRS},
        "record": {"w": 0, "l": 0, "d": 0},
        "form": [],
        "ko_wins": 0, "sub_wins": 0,
        "money": legacy.get("money", 0),
        "hype": legacy.get("hype", 0),
        "tier": 0,
        "rank": C.DIVISION_SIZE,
        "champion": False,
        "title_shot": False,
        "title_defenses": 0,
        "belts": [],
        "fights": 0,
        "injury_weeks": 0,
        "suspension_camps": 0,
        "loss_streak": 0, "win_streak": 0,
        "brain": C.BRAIN_START,
        "body": C.BODY_START,
        "staff": {k: legacy.get("staff", {}).get(k, 0) for k in C.STAFF},
        "contract": {"org": C.TIERS[0]["name"], "tier": 0, "purse": 0, "bonus": 0,
                     "fights_left": 6, "hype_mult": 1.0},
        "sponsor": None,
        "rivalries": {},
        "achievements": [],
        "records": {"fastest_ko": None, "longest_streak": 0, "career_purses": 0,
                    "distance": 0, "biggest_upset": 0},
        "replays": [],
        "next_cut": "standard",
        "next_plan": "normal",
        "retired": False,
        "legacy_of": legacy.get("mentor"),
        "history": [],
        "log": [],
    }
    state = {
        "slot": _free_slot(name),
        "created": time.time(),
        "fighter": f,
        "world": world,
    }
    W.build_division(world, weight, 0, f)
    W.sync_player(state)
    f["log"].insert(0, f"Pro debut at {C.WEIGHT_LABELS[weight]} as a {C.STYLES[f['style']]['label'].lower()}.")
    if legacy.get("mentor"):
        f["log"].insert(0, f"Protege of {legacy['mentor']}. The world is watching with interest.")
    start_camp(state)
    return state


# --- Staff -----------------------------------------------------------

def staff_gain_mult(f: dict, attr: str) -> float:
    mult = 1.0
    for key, meta in C.STAFF.items():
        if attr in meta["attrs"]:
            mult += f["staff"].get(key, 0) * C.STAFF_GAIN_PER_LEVEL
    return mult


def buy_staff(state: dict, key: str) -> str:
    f = state["fighter"]
    if key not in C.STAFF:
        return "No such coach."
    lvl = f["staff"].get(key, 0)
    if lvl >= C.STAFF_MAX_LEVEL:
        return "That coach is already at the maximum level."
    cost = C.STAFF_COST[lvl + 1]
    if f["money"] < cost:
        return f"Not enough money (need ${cost})."
    f["money"] -= cost
    f["staff"][key] = lvl + 1
    return f"Hired: {C.STAFF[key]['label']} (level {lvl + 1})."


# --- Sponsors -------------------------------------------------------

def available_sponsors(f: dict) -> list[dict]:
    return [s for s in C.SPONSORS if f["hype"] >= s["min_hype"]]


def sign_sponsor(state: dict, sid: str) -> str:
    f = state["fighter"]
    if sid == "none":
        f["sponsor"] = None
        return "Sponsor dropped."
    s = next((x for x in C.SPONSORS if x["id"] == sid), None)
    if not s:
        return "No such sponsor."
    if f["hype"] < s["min_hype"]:
        return "Your profile isn't big enough for that deal yet."
    f["sponsor"] = sid
    return f"Signed with {s['name']}."


def _sponsor(f: dict) -> dict | None:
    return next((s for s in C.SPONSORS if s["id"] == f.get("sponsor")), None)


# --- Training camp ---------------------------------------------------

def start_camp(state: dict) -> None:
    f = state["fighter"]
    base = C.CAMP_SESSIONS - min(3, f["injury_weeks"])
    if f["suspension_camps"] > 0:
        f["suspension_camps"] -= 1
        base = 3
        f["brain"] = min(100, f["brain"] + 10)
    f["injury_weeks"] = 0
    nutri = f["staff"].get("nutrition", 0)
    f["brain"] = min(100, f["brain"] + C.BRAIN_HEAL_PER_CAMP + nutri)
    f["body"] = min(100, f["body"] + C.BODY_HEAL_PER_CAMP + nutri * 2)
    state["camp"] = {"left": max(2, base), "total": max(2, base), "gains": {}, "notes": []}


def _rating_for(v: float) -> float:
    return max(0.25, 1.9 - v / 65.0)


def _progress_mult(state: dict) -> float:
    return C.DIFFICULTY.get(state["world"].get("difficulty", "normal"), C.DIFFICULTY["normal"])["progress"]


def train(state: dict, kind: str) -> dict:
    f = state["fighter"]
    camp = state["camp"]
    t = C.TRAININGS[kind]
    pm = _progress_mult(state)
    res = {"notes": [], "injury": False}
    for attr, w in ((t["primary"], 1.0), (t["secondary"], 0.4)):
        gain = _rating_for(f["attrs"][attr]) * w * random.uniform(0.7, 1.15) * staff_gain_mult(f, attr) * pm
        f["xp"][attr] += gain
        camp["gains"][attr] = camp["gains"].get(attr, 0.0) + gain
        while f["xp"][attr] >= 1.0 and f["attrs"][attr] < 99:
            f["xp"][attr] -= 1.0
            f["attrs"][attr] += 1
    risk = t.get("risk", 0.05) + (0.03 if f["age"] >= 34 else 0)
    risk *= max(0.4, 1 - f["staff"].get("nutrition", 0) * 0.2)
    if random.random() < risk:
        f["injury_weeks"] += 1
        f["body"] = max(0, f["body"] - random.randint(3, 8))
        res["injury"] = True
    camp["left"] -= 1
    res["done"] = camp["left"] <= 0
    return res


# --- Fight preparation -----------------------------------------------

def set_cut(state: dict, cut: str) -> None:
    if cut in C.CUTS:
        state["fighter"]["next_cut"] = cut


def set_plan(state: dict, plan: str) -> None:
    if plan in C.PLANS:
        state["fighter"]["next_plan"] = plan


def injury_risk(f: dict, kind: str) -> int:
    """Effective injury chance (%) for a training session - matches train()."""
    t = C.TRAININGS[kind]
    risk = t.get("risk", 0.05) + (0.03 if f["age"] >= 34 else 0)
    risk *= max(0.4, 1 - f["staff"].get("nutrition", 0) * 0.2)
    return round(risk * 100)


def fight_stakes(state: dict) -> dict:
    f = state["fighter"]
    c = f.get("contract") or C.TIERS[f["tier"]]
    for_title = bool(f.get("title_shot") or f["champion"])
    opp = W.pick_opponent(state["world"], f)
    return {
        "org": c.get("org", C.TIERS[f["tier"]]["name"]),
        "rounds": C.TITLE_ROUNDS if for_title else 3,
        "for_title": for_title,
        "purse": c.get("purse", 0),
        "win_bonus": c.get("bonus", 0),
        "opp": opp,
        "rivalry": f.get("rivalries", {}).get(opp["id"], {}),
        "date": W.date_str(state["world"]),
    }


def combat_attrs(f: dict, cut: str) -> dict:
    a = dict(f["attrs"])
    meta = C.CUTS[cut]
    if meta.get("attr_hit"):
        for k in random.sample(C.ATTRS, 2):
            a[k] = max(15, a[k] - random.randint(2, 5))
    if f["brain"] < 80:
        a["chin"] = max(15, int(a["chin"] * (0.6 + 0.4 * f["brain"] / 100)))
    if f["body"] < 80:
        a["cardio"] = max(15, int(a["cardio"] * (0.7 + 0.3 * f["body"] / 100)))
    return a


# --- Achievements & records ----------------------------------------

def _ovr(attrs: dict) -> float:
    return sum(attrs.values()) / len(C.ATTRS)


def _check_achievements(f: dict, result: dict, opp: dict, ch: dict) -> None:
    have = set(f["achievements"])
    unlocked = []

    def give(aid):
        if aid not in have:
            have.add(aid)
            unlocked.append(aid)

    outcome = result["outcome"]
    method = result["method"]
    if outcome == "win":
        give("first_win")
        if method in ("KO", "TKO", "TKO (cut)"):
            give("ko")
        if method == "Submission":
            give("sub")
        if result["round"] == 1 and method in FINISH_METHODS:
            give("r1")
        if result.get("rocked") and method in FINISH_METHODS:
            give("comeback")
        if _ovr(opp.get("attrs", {})) - _ovr(f["attrs"]) >= 12:
            give("upset")
        riv = f.get("rivalries", {}).get(opp["id"], {})
        if riv.get("pw", 0) >= 3:
            give("nemesis")
    if f["champion"]:
        give("champ")
        if f["tier"] == C.MAX_TIER:
            give("apex_champ")
        if f["record"]["l"] == 0:
            give("flawless")
    if f["win_streak"] >= 5:
        give("streak5")
    if f["win_streak"] >= 10:
        give("streak10")
    if f["records"]["distance"] >= 10:
        give("distance10")
    if f["fights"] >= 25:
        give("veteran")
    if f["records"]["career_purses"] >= 500000:
        give("millionaire")
    if len(f["belts"]) >= 2:
        give("hof")

    f["achievements"] = sorted(have)
    if unlocked:
        names = {a[0]: a[1] for a in C.ACHIEVEMENTS}
        ch["achievements"] = [names[u] for u in unlocked if u in names]


# --- Fight resolution ------------------------------------------------

def apply_result(state: dict, result: dict) -> dict:
    f = state["fighter"]
    world = state["world"]
    opp = result["opp"]
    stakes = result.get("stakes") or fight_stakes(state)
    outcome = result["outcome"]
    method = result["method"]
    finish = method in FINISH_METHODS
    diff = C.DIFFICULTY.get(world.get("difficulty", "normal"), C.DIFFICULTY["normal"])
    mode = world.get("mode", "standard")
    ch = {"lines": [], "news": []}

    rec_before = f'{f["record"]["w"]}-{f["record"]["l"]}-{f["record"]["d"]}'
    was_title = bool(stakes.get("for_title"))
    was_champ = f["champion"]
    opp_div = W.get_fighter(world, opp["id"]) or opp

    # record / streaks
    if outcome == "win":
        f["record"]["w"] += 1
        f["win_streak"] += 1
        f["loss_streak"] = 0
        f["form"] = (f["form"] + ["W"])[-5:]
        if method in ("KO", "TKO", "TKO (cut)"):
            f["ko_wins"] += 1
        elif method == "Submission":
            f["sub_wins"] += 1
    elif outcome == "loss":
        f["record"]["l"] += 1
        f["loss_streak"] += 1
        f["win_streak"] = 0
        f["form"] = (f["form"] + ["L"])[-5:]
    else:
        f["record"]["d"] += 1
        f["win_streak"] = f["loss_streak"] = 0
        f["form"] = (f["form"] + ["D"])[-5:]

    # health
    if outcome == "loss" and method == "KO":
        f["brain"] = max(0, f["brain"] - random.randint(*C.BRAIN_HIT_KO))
        ch["lines"].append("A bad knockout. The brain isn't a joke - real damage taken.")
    elif outcome == "loss" and method in ("TKO", "TKO (cut)"):
        f["brain"] = max(0, f["brain"] - random.randint(*C.BRAIN_HIT_TKO))
    if result.get("war"):
        f["body"] = max(0, f["body"] - random.randint(8, 16))
        ch["lines"].append("A five-round war left a mark on the body.")

    # money
    purse = int(stakes["purse"] * diff["purse"])
    win_bonus = int(stakes["win_bonus"] * diff["purse"])
    money = purse + (win_bonus if outcome == "win" else 0)
    if outcome == "win" and finish and win_bonus > 0:
        b = int(win_bonus * 0.35)
        money += b
        ch["lines"].append(f"Performance bonus for the finish: +${b}.")
    riv = f.get("rivalries", {}).get(opp["id"], {})
    if riv.get("heat", 0) >= 40 and purse > 0:
        gate = int(purse * 0.5)
        money += gate
        ch["lines"].append(f"The rivalry drove ticket sales: +${gate}.")
    sp = _sponsor(f)
    if sp:
        pay = sp["per_fight"] - int((purse + (win_bonus if outcome == "win" else 0)) * sp["cut"])
        money += pay
        ch["lines"].append(f"{sp['name']} sponsorship: {'+' if pay >= 0 else ''}${pay}.")
    f["money"] += money
    f["records"]["career_purses"] += max(0, money)
    ch["purse"] = money

    # hype
    hm = (f.get("contract") or {}).get("hype_mult", 1.0)
    dh = {"win": 8, "loss": -12, "draw": 1}[outcome] * hm
    if finish and outcome == "win":
        dh += 10 * hm
    f["hype"] = max(0, int(f["hype"] + dh))

    # rivalry
    r = W.update_rivalry(f, opp, outcome, method, result["round"])
    if r["fights"] >= 2:
        lead = "you lead" if r["pw"] > r["ow"] else "you trail" if r["ow"] > r["pw"] else "even"
        ch["lines"].append(f'Series with {opp["name"]}: {r["pw"]}-{r["ow"]} ({lead}).')

    # ranking / belt
    ch["promoted"] = False
    opp_rank = opp_div.get("rank", C.DIVISION_SIZE)
    if outcome == "win":
        if opp_div.get("champion"):
            f["champion"] = True
            f["title_shot"] = False
            f["rank"] = 1
            f["title_defenses"] = 0
            opp_div["champion"] = False
            opp_div["rank"] = 2
            world["champion_id"] = f["id"]
            f["belts"].append(C.TIERS[f["tier"]]["short"] + f' ({W.date_str(world)})')
            ch["lines"].append(f'YOU WIN THE {C.TIERS[f["tier"]]["short"].upper()} TITLE!')
        elif f["champion"]:
            f["title_defenses"] += 1
            ch["lines"].append(f"Title defense #{f['title_defenses']}.")
        else:
            if opp_rank < f["rank"]:
                f["rank"], opp_div["rank"] = opp_rank, f["rank"]
                ch["lines"].append(f"You jump to #{f['rank']} in the division.")
            else:
                f["rank"] = max(1, f["rank"] - 1)
            if f["rank"] == 1 and not f["champion"]:
                f["title_shot"] = True
                ch["lines"].append("You're the #1 contender - next fight is for the belt!")
    elif outcome == "loss":
        if f["champion"]:
            f["champion"] = False
            f["rank"] = 2
            f["title_defenses"] = 0
            opp_div["champion"] = True
            opp_div["rank"] = 1
            world["champion_id"] = opp["id"]
            ch["lines"].append("You lose the belt.")
        else:
            f["title_shot"] = False
            if opp_rank > f["rank"]:
                f["rank"], opp_div["rank"] = opp_rank, f["rank"]
            else:
                f["rank"] = min(C.DIVISION_SIZE, f["rank"] + 1)
            ch["lines"].append(f"You drop to #{f['rank']}.")

    # contract
    c = f.get("contract")
    if c and c.get("fights_left", 99) < 99:
        c["fights_left"] = max(0, c["fights_left"] - 1)

    # records
    f["records"]["longest_streak"] = max(f["records"]["longest_streak"], f["win_streak"])
    if outcome == "win" and method in ("KO", "TKO") and (
            f["records"]["fastest_ko"] is None or result["round"] < f["records"]["fastest_ko"]):
        f["records"]["fastest_ko"] = result["round"]
    if not finish:
        f["records"]["distance"] += 1
    if outcome == "win":
        up = round(_ovr(opp.get("attrs", {})) - _ovr(f["attrs"]))
        f["records"]["biggest_upset"] = max(f["records"]["biggest_upset"], up)

    # age / calendar
    f["fights"] += 1
    old_year = int(f["age"])
    f["age"] += C.MONTHS_BETWEEN_FIGHTS / 12.0
    if int(f["age"]) > old_year:
        ch["lines"].append(f"Another year - you're now {int(f['age'])}.")
        if f["age"] >= 34:
            declined = random.sample(C.ATTRS, 2)
            for a in declined:
                f["attrs"][a] = max(20, f["attrs"][a] - random.randint(1, 3))
            ch["lines"].append("Age takes a step off your " + " and ".join(C.ATTR_LABELS[a] for a in declined) + ".")

    # post-fight injury
    inj = 0.12 + (0.18 if outcome == "loss" else 0) + (0.1 if finish and outcome == "loss" else 0)
    inj += C.CUTS[f["next_cut"]]["risk"]
    inj *= max(0.5, 1 - f["staff"].get("nutrition", 0) * 0.18)
    if random.random() < inj:
        f["injury_weeks"] += random.randint(1, 3)
        ch["lines"].append("You leave the fight with an injury - shorter next camp.")

    # world moves on
    W.sync_player(state)
    ch["news"] = W.advance(world, f)
    W.sync_player(state)
    W.maybe_offer(state)
    if state.get("offers"):
        ch["lines"].append("New contract offers are on the table - check them before your next camp.")

    # achievements
    _check_achievements(f, result, opp, ch)

    # replay
    f["replays"].insert(0, {
        "opp": opp["name"], "nick": opp.get("nickname", ""),
        "outcome": outcome, "method": method, "round": result["round"],
        "date": W.date_str(world), "tier": C.TIERS[f["tier"]]["short"],
        "log": (result.get("log") or [])[:60],
    })
    f["replays"] = f["replays"][:6]

    # medical suspension / retirement
    ch["forced_retire"] = False
    if f["brain"] < C.BRAIN_RETIRE:
        ch["lines"].append("The medical board pulls your license. It's over - health comes first.")
        ch["forced_retire"] = True
    elif f["brain"] < C.BRAIN_SUSPEND and f["suspension_camps"] == 0:
        f["suspension_camps"] = 2
        ch["lines"].append("Medical suspension - a longer forced layoff before you return.")
    if f["loss_streak"] >= 5 or (f["loss_streak"] >= 4 and f["age"] >= 33):
        ch["lines"].append("A long losing skid - the promotion cuts you. Time to hang them up.")
        ch["forced_retire"] = True
    elif f["loss_streak"] == 3:
        ch["lines"].append("Three straight losses - you drop down the card and need to turn it around.")
    if f["age"] >= 40:
        ch["lines"].append("You're 40. The body says enough.")
        ch["forced_retire"] = True
    if mode == "ironman" and outcome == "loss":
        ch["lines"].append("Ironman run: one loss ends the career.")
        ch["forced_retire"] = True
    if mode == "title_run" and outcome == "loss" and (was_title or was_champ):
        ch["lines"].append("Title or Bust: you lost with a belt on the line. The run is over.")
        ch["forced_retire"] = True
    if ch["forced_retire"]:
        f["retired"] = True

    # history
    opp_label = opp["name"] + (f' "{opp["nickname"]}"' if opp.get("nickname") else "")
    entry = (f'{"W" if outcome == "win" else "L" if outcome == "loss" else "D"} '
             f'{method}, R{result["round"]} vs {opp_label} '
             f'({opp["record"]["w"]}-{opp["record"]["l"]}) | {C.TIERS[f["tier"]]["short"]} | '
             f'{rec_before} -> {f["record"]["w"]}-{f["record"]["l"]}-{f["record"]["d"]} | {W.date_str(world)}')
    f["history"].insert(0, entry)
    f["log"].insert(0, entry)

    state.pop("fight", None)
    return ch


def overall(f: dict) -> int:
    """Raw attribute average (30-99). Used by the fight engine."""
    return round(sum(f["attrs"].values()) / len(C.ATTRS))


def rating(entity: dict, tier: int | None = None) -> int:
    """Composite fighter rating shown in the UI. Roughly 35 for a raw amateur up to
    ~145 for an all-time great at the top of Apex. Works for the player dict and for
    NPC roster dicts."""
    a = entity["attrs"]
    base = sum(a.values()) / len(a)
    t = entity.get("tier", tier if tier is not None else 0)
    rec = entity.get("record", {})
    wins = rec.get("w", 0)
    titles = len(entity.get("belts", []))
    if not titles and entity.get("champion"):
        titles = 1
    champ = 8 if entity.get("champion") else 0
    hype = entity.get("hype", 0)
    streak = entity.get("win_streak", 0)
    r = base + t * 3.8 + titles * 6 + champ + min(22, wins * 0.65) + min(14, hype / 16) + min(8, streak)
    return int(round(r))


def career_progress(f: dict) -> int:
    """0-100: how close the player is to being the Apex champion."""
    val = f["tier"] * 20 + (C.DIVISION_SIZE - f["rank"]) + (60 if f["champion"] else 0) \
        + (10 if f.get("title_shot") else 0)
    top = C.MAX_TIER * 20 + C.DIVISION_SIZE + 60
    return int(min(100, round(100 * val / top)))


def wear(f: dict) -> int:
    n = f.get("fights", 0)
    return int(n > 8) + int(n > 20) + int(f.get("brain", 100) < 68)


# --- Hall of Fame / legacy ----------------------------------------

def hall_of_fame(f: dict) -> dict:
    """Rank the retired fighter among procedural all-time greats."""
    titles = len(f["belts"])
    score = (f["record"]["w"] * 3 - f["record"]["l"] * 2 + f["ko_wins"] * 2 + f["sub_wins"] * 2
             + titles * 40 + f["records"]["longest_streak"] * 2 + f["hype"] // 3
             + f["records"]["biggest_upset"])
    if score >= 260:
        tier, blurb = "First-ballot legend", "One of the greatest to ever do it. The blueprint."
    elif score >= 170:
        tier, blurb = "Hall of Famer", "A decorated champion whose name headlines any era."
    elif score >= 100:
        tier, blurb = "Fan favourite", "A tough out on any night, remembered fondly."
    elif score >= 45:
        tier, blurb = "Solid pro", "Paid the bills, had his nights, walked away on his feet."
    else:
        tier, blurb = "Journeyman", "A cautionary tale, or just a hard road that didn't break right."
    rank = max(1, 200 - score // 2)
    return {"score": score, "tier": tier, "blurb": blurb, "all_time_rank": rank}


def build_legacy(f: dict) -> dict:
    titles = len(f["belts"])
    quality = f["record"]["w"] * 2 + f["ko_wins"] + f["sub_wins"] + titles * 15 + f["hype"] // 5
    pts = min(10, 2 + quality // 25)
    money = min(60000, 3000 + f["money"] // 12)
    staff = {}
    if titles >= 1:
        staff["striking"] = 1
    if titles >= 2:
        staff["grappling"] = 1
    return {
        "mentor": f["name"] + (f' "{f["nickname"]}"' if f["nickname"] else ""),
        "bonus_points": pts,
        "money": money,
        "hype": min(40, 5 + titles * 10 + f["hype"] // 10),
        "staff": staff,
        "record": f'{f["record"]["w"]}-{f["record"]["l"]}-{f["record"]["d"]}',
        "titles": titles,
    }
