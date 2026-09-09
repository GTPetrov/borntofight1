"""Turn-based fight engine: action combos, corner tactics, style passives, judges' cards, in-fight injuries."""

from __future__ import annotations

import random

from . import content as C

REST_BETWEEN_ROUNDS = 18
PASSIVE_REGEN = 4
HEAD_POWER = {"cross", "headkick", "knee"}


def init_fight(player_attrs, opp, max_rounds, for_title,
               p_style="balanced", cut_stamina=0, p_stance="ortho", p_plan="normal") -> dict:
    def side(name, nickname, sta=100.0):
        return {"name": name, "nickname": nickname, "hp": 100.0, "stamina": sta,
                "cards": 0, "rocked": 0, "cut": 0.0, "leg": 0.0,
                # per-round tallies (reset every round) - drive the judges' cards
                "r_sig": 0, "r_dmg": 0.0, "r_td": 0, "r_ctrl": 0.0, "r_sub": 0, "r_kd": 0}

    o_style = opp.get("style", "balanced")
    o_tier = max(0, min(opp.get("tier", 0), len(C.TIERS) - 1))
    return {
        "round": 1, "max_rounds": max_rounds, "exchange": 0,
        "pos": "stand", "top": None, "passed": False, "for_title": for_title,
        "player_attrs": dict(player_attrs), "opp": opp,
        "o_edge": C.TIERS[o_tier].get("edge", 0.0),
        "p_style": p_style, "o_style": o_style,
        "p_stance": p_stance, "o_stance": opp.get("look", {}).get("stance", "ortho"),
        "p_pass": C.STYLES.get(p_style, {}).get("passive", {}),
        "o_pass": C.STYLES.get(o_style, {}).get("passive", {}),
        "tactic": p_plan if p_plan in C.TACTICS else "normal",
        "plan": p_plan if p_plan in C.TACTICS else "normal",
        "p": side("You", "", max(35.0, 100.0 + cut_stamina)),
        "o": side(opp["name"], opp.get("nickname", "")),
        "scorecard": [],
        "log": [], "recap": None, "over": False, "result": None, "war": False,
        "injuries": [],
    }


# --- helpers -----------------------------------------------------------

def _passv(state, who, key, default=0.0):
    d = state["p_pass"] if who == "player" else state["o_pass"]
    return d.get(key, default)


def _eff(state, who, attrs, key, stamina):
    factor = 0.65 + 0.35 * (stamina / 100.0)
    if stamina < 25:
        factor *= 0.82
    base = attrs[key]
    allb = _passv(state, who, "all")
    if allb:
        base *= (1 + allb)
    leg = _side(state, who).get("leg", 0)
    if leg and key in ("wrestling", "cardio", "striking"):
        base *= (1 - min(0.16, leg / 400.0))
    return base * factor


def _attrs(state, who):
    return state["player_attrs"] if who == "player" else state["opp"]["attrs"]


def _side(state, who):
    return state["p"] if who == "player" else state["o"]


def allowed_actions(state):
    pos = state["pos"]
    if pos == "stand":
        return ["jab", "cross", "body", "lowkick", "midkick", "headkick", "td_stand", "clinch_up", "defend_stand"]
    if pos == "clinch":
        return ["dirtybox", "knee", "trip", "break_clinch", "defend_clinch"]
    if pos == "ground" and state["top"] == "player":
        return ["gnp", "pass_guard", "submit", "control", "standup_top"]
    if pos == "ground" and state["top"] == "opp":
        return ["sweep", "sub_bottom", "standup_bottom", "defend_bottom"]
    return ["defend_stand"]


def combo_actions(state):
    return [a for a in allowed_actions(state) if C.ACTIONS[a].get("combo")]


def pos_label(state):
    if state["pos"] == "stand":
        return C.POS_LABELS["stand"]
    if state["pos"] == "clinch":
        return C.POS_LABELS["clinch"]
    return C.POS_LABELS["top_player"] if state["top"] == "player" else C.POS_LABELS["top_opp"]


# --- opponent AI ------------------------------------------------------

def _weighted(weights):
    items = [(k, max(0.0, v)) for k, v in weights.items()]
    total = sum(v for _, v in items) or 1.0
    r = random.uniform(0, total)
    upto = 0.0
    for k, v in items:
        upto += v
        if r <= upto:
            return k
    return items[-1][0]


def _ai_combo(state):
    o, p = state["o"], state["p"]
    ai = C.STYLES[state["o_style"]]["ai"]
    pos = state["pos"]
    edge = state.get("o_edge", 0.0)
    aggr = 1.0
    if p["hp"] < 32 or p["rocked"] > 0:
        aggr = 1.4 + 0.5 * edge          # sharper pros jump on a hurt opponent
    if o["hp"] < 30 or o["stamina"] < 20:
        aggr = 0.55
    counter = 1.0
    if state["p_style"] in ("striker", "brawler") and state["o_style"] in ("wrestler", "grappler"):
        counter = 1.5 + 0.4 * edge
    # protect a clear lead late - only fighters with ring IQ do this
    ahead = o["hp"] - p["hp"]
    if (edge and ahead > 18 and state["round"] >= state["max_rounds"] - 1
            and random.random() < 0.4 * edge):
        if pos == "stand":
            return ["defend_stand"]
        if pos == "clinch":
            return ["defend_clinch"]
        if pos == "ground" and state["top"] == "opp":
            return ["control"]

    if pos == "stand":
        cat = _weighted({"strike": ai["strike"] * aggr, "takedown": ai["takedown"] * counter,
                         "clinch": ai["clinch"], "defend": ai["defend"] / aggr})
        if cat == "takedown":
            return ["td_stand"]
        if cat == "clinch":
            return ["clinch_up"]
        if cat == "defend":
            return ["defend_stand"]
        first = _weighted({"jab": 0.32, "cross": 0.22 * aggr, "body": 0.14,
                           "lowkick": 0.14, "midkick": 0.10, "headkick": 0.08 * aggr})
        combo = [first]
        if C.ACTIONS[first].get("combo") and random.random() < (0.3 + 0.4 * edge) * aggr:
            combo.append(_weighted({"jab": 0.45, "cross": 0.28 * aggr, "body": 0.17, "midkick": 0.1}))
            if edge > 0.6 and random.random() < 0.35 * edge and C.ACTIONS[combo[-1]].get("combo"):
                combo.append(_weighted({"cross": 0.4, "headkick": 0.25 * aggr, "body": 0.2, "jab": 0.15}))
        return combo

    if pos == "clinch":
        cat = _weighted({"strike": ai["strike"] * aggr, "takedown": ai["takedown"] + 0.1,
                         "break": 0.15, "defend": ai["defend"]})
        if cat == "takedown":
            return ["trip"]
        if cat == "break":
            return ["break_clinch"]
        if cat == "defend":
            return ["defend_clinch"]
        return ["knee" if random.random() < 0.4 * aggr else "dirtybox"]

    if pos == "ground" and state["top"] == "opp":
        grap = state["opp"]["attrs"]["bjj"]
        return [_weighted({"gnp": 0.4 * aggr,
                           "pass_guard": 0.2 if not state["passed"] else 0.05,
                           "submit": (0.3 if grap > 65 else 0.12) + (0.15 if p["hp"] < 45 else 0),
                           "control": 0.2})]

    if pos == "ground" and state["top"] == "player":
        st = state["o_style"]
        if st == "grappler":
            return [_weighted({"sub_bottom": 0.4, "sweep": 0.3, "standup_bottom": 0.2, "defend_bottom": 0.1})]
        if st in ("wrestler", "balanced"):
            return [_weighted({"sweep": 0.35, "standup_bottom": 0.4, "defend_bottom": 0.2, "sub_bottom": 0.05})]
        return [_weighted({"standup_bottom": 0.55, "defend_bottom": 0.3, "sweep": 0.1, "sub_bottom": 0.05})]

    return ["defend_stand"]


# --- exchange resolution (with combos) ------------------------------

def resolve(state, player_actions) -> list[str]:
    if isinstance(player_actions, str):
        player_actions = [player_actions]
    lines: list[str] = []

    allowed = allowed_actions(state)
    pa0 = player_actions[0] if player_actions else "defend_stand"
    if pa0 not in allowed:
        pa0 = allowed[0]
    seq = [pa0]
    if C.ACTIONS[pa0].get("combo"):
        for a in player_actions[1:C.COMBO_MAX]:
            if a in allowed and C.ACTIONS[a].get("combo"):
                seq.append(a)

    opp_seq = _ai_combo(state)
    p, o = state["p"], state["o"]

    def cost(who, act, idx=0):
        base = C.ACTIONS[act]["stamina"] * (1 + _passv(state, who, "stamina_cost"))
        base *= (1 + 0.25 * idx)
        if who == "player" and state["tactic"] == "conserve":
            base *= 0.9
        return base

    for i, a in enumerate(seq):
        p["stamina"] = max(0.0, p["stamina"] - cost("player", a, i))
    for i, a in enumerate(opp_seq):
        o["stamina"] = max(0.0, o["stamina"] - cost("opp", a, i))

    start_pos = state["pos"]
    p_kind0 = C.ACTIONS[seq[0]]["kind"]
    o_kind0 = C.ACTIONS[opp_seq[0]]["kind"]
    o_def = o_kind0 == "defend"
    p_def = p_kind0 == "defend"

    def strike_side(who, actions, def_first):
        out = []
        for i, a in enumerate(actions):
            ln, missed = _do_strike(state, who, a, def_first, extra_acc=-0.07 * i)
            out.extend(ln)
            if state["over"]:
                return out, True
            if missed and C.ACTIONS[a]["power"] >= 0.85 and random.random() < 0.14:
                other = "opp" if who == "player" else "player"
                nm = state["o"]["name"] if who == "player" else "You"
                out.append(f'  {nm} counter{"s" if who == "player" else ""} the miss...')
                cl, _ = _do_strike(state, other, "cross", "none")
                out.extend(cl)
                if state["over"]:
                    return out, True
        return out, False

    p_strikes = p_kind0 == "strike"
    o_strikes = o_kind0 == "strike"
    if p_strikes and o_strikes:
        order = [("player", seq, opp_seq[0]), ("opp", opp_seq, seq[0])]
        random.shuffle(order)
    elif p_strikes:
        order = [("player", seq, opp_seq[0])]
    elif o_strikes:
        order = [("opp", opp_seq, seq[0])]
    else:
        order = []
    for who, acts, dfirst in order:
        ln, done = strike_side(who, acts, dfirst)
        lines += ln
        if done:
            return lines

    # doctor's check on a bad cut
    for who in ("player", "opp"):
        s = _side(state, who)
        if s["cut"] >= 80 and random.random() < 0.28:
            winner = "opp" if who == "player" else "player"
            nm = "You" if who == "player" else s["name"]
            _finish(state, winner, "TKO (cut)", f'The cut on {nm.lower() if who=="player" else nm} is too deep — the doctor waves it off.')
            wn = "You win" if winner == "player" else state["o"]["name"] + " wins" if winner == "opp" else "?"
            lines.append(f'  >>> DOCTOR STOPPAGE - {wn} by TKO! <<<')
            return lines

    # --- grappling / movement (from start position) ---
    if start_pos == "stand":
        if p_kind0 == "takedown":
            lines += _takedown(state, "player", "opp", resisted=o_kind0 in ("takedown", "defend") or opp_seq[0] == "clinch_up")
        elif o_kind0 == "takedown":
            lines += _takedown(state, "opp", "player", resisted=p_kind0 in ("takedown", "defend") or seq[0] == "clinch_up")
        elif seq[0] == "clinch_up" or opp_seq[0] == "clinch_up":
            if random.random() < 0.78:
                state["pos"] = "clinch"
                lines.append("They tie up against the cage — into the clinch.")
    elif start_pos == "clinch":
        if p_kind0 == "takedown":
            lines += _takedown(state, "player", "opp", resisted=o_def, from_clinch=True)
        elif o_kind0 == "takedown":
            lines += _takedown(state, "opp", "player", resisted=p_def, from_clinch=True)
        elif seq[0] == "break_clinch" or opp_seq[0] == "break_clinch":
            who = "player" if seq[0] == "break_clinch" else "opp"
            other = _attrs(state, "opp" if who == "player" else "player")
            mine = _attrs(state, who)
            if random.random() < 0.55 + (_eff(state, who, mine, "wrestling", 60) - _eff(state, "opp" if who == "player" else "player", other, "wrestling", 60)) * 0.01:
                state["pos"] = "stand"
                lines.append("They separate — back to striking range.")
    elif start_pos == "ground":
        lines += _ground(state, seq[0], opp_seq[0])

    # control / stall
    if seq[0] == "control":
        o["stamina"] = max(0.0, o["stamina"] - 8)
        p["r_ctrl"] += 2.5 * (1.4 if state["tactic"] == "ground" else 1)
        lines.append("You control from the top and drain their gas tank.")
    if opp_seq[0] == "control":
        p["stamina"] = max(0.0, p["stamina"] - 8)
        o["r_ctrl"] += 2.5
        lines.append(f'{o["name"]} pins you down and controls.')
    for who, act in (("player", seq[0]), ("opp", opp_seq[0])):
        if act == "standup_top":
            state["pos"] = "stand"; state["top"] = None; state["passed"] = False
            lines.append("Back up to the feet.")

    # octagon control: pressuring forward, or holding a dominant ground position
    if state["tactic"] == "pressure" and p_kind0 == "strike":
        p["r_ctrl"] += 0.6
    if state["pos"] == "ground" and state["top"]:
        _side(state, state["top"])["r_ctrl"] += 1.2

    # recovery
    for who, act in (("player", seq[0]), ("opp", opp_seq[0])):
        s = _side(state, who)
        regen = PASSIVE_REGEN + (12 if C.ACTIONS[act]["kind"] == "defend" else 0)
        regen *= (1 + _passv(state, who, "cardio_regen"))
        if who == "player" and state["tactic"] == "conserve":
            regen *= 1.5
        if who == "player" and state["tactic"] == "pressure":
            regen *= 0.7
        card = _attrs(state, who)["cardio"]
        if who == "opp" and state.get("o_edge"):
            regen *= 1 + 0.14 * state["o_edge"]        # elite pros pace themselves
        s["stamina"] = min(100.0, s["stamina"] + regen * (0.6 + card / 150.0))
        if s["rocked"] > 0:
            s["rocked"] -= 1

    if p["hp"] < 55 and o["hp"] < 55:
        state["war"] = True

    return lines


def _do_strike(state, atk_who, action_key, def_action_key, extra_acc=0.0):
    lines = []
    a = C.ACTIONS[action_key]
    atk = _side(state, atk_who)
    dfn_who = "opp" if atk_who == "player" else "player"
    dfn = _side(state, dfn_who)
    atk_at = _attrs(state, atk_who)
    dfn_at = _attrs(state, dfn_who)
    d_act = C.ACTIONS.get(def_action_key, {"kind": "none"})

    off = _eff(state, atk_who, atk_at, a["off"], atk["stamina"]) * 0.7 + _eff(state, atk_who, atk_at, "striking", atk["stamina"]) * 0.3
    dfn_def = _eff(state, dfn_who, dfn_at, "striking", dfn["stamina"])
    if state["pos"] == "ground":
        dfn_def *= 0.7

    acc = 0.52 + (off - dfn_def) * 0.012 - 0.05 * a["power"] + extra_acc
    acc += _passv(state, atk_who, "strike_acc")
    if atk_who == "player":
        acc += 0.03
    if state["p_stance"] != state["o_stance"]:
        south = state["p_stance"] == "south" if atk_who == "player" else state["o_stance"] == "south"
        acc += 0.03 if south else -0.01
    if d_act["kind"] == "defend":
        acc -= 0.22
    if d_act["kind"] == "strike":
        acc += 0.08
    if atk["rocked"] > 0:
        acc -= 0.15
    if state["passed"] and action_key == "gnp":
        acc += 0.12
    if atk_who == "player" and state["tactic"] == "counter":
        acc += 0.12 if d_act["kind"] == "strike" else -0.08
    if atk_who == "player" and state["tactic"] == "pressure":
        acc += 0.03
    if atk_who == "player" and state["tactic"] == "conserve":
        acc -= 0.03
    if atk_who == "opp" and state["tactic"] == "counter" and d_act["kind"] != "strike":
        acc -= 0.05
    edge = state.get("o_edge", 0.0)
    if edge:
        acc += 0.045 * edge if atk_who == "opp" else -0.03 * edge
    acc = min(0.95, max(0.05, acc))

    subj = "You" if atk_who == "player" else atk["name"]
    obj = "you" if dfn_who == "player" else dfn["name"]

    if random.random() > acc:
        lines.append(f'{subj}: {a["label"].lower()} — misses.')
        return lines, True

    dmg = a["base_dmg"] * (0.55 + off / 78.0) * random.uniform(0.8, 1.2) * 0.86
    if d_act["kind"] == "defend":
        dmg *= 0.45
    if state["passed"] and action_key == "gnp":
        dmg *= 1.4
    dmg *= (1 - min(0.22, (dfn_at["chin"] - 40) / 320.0))
    if dfn["rocked"] > 0:
        dmg *= 1.25
    if atk_who == "player" and state["tactic"] == "counter" and d_act["kind"] == "strike":
        dmg *= 1.15
    if atk_who == "player" and state["tactic"] == "conserve":
        dmg *= 0.8
    if atk_who == "opp" and edge:
        dmg *= 1 + 0.07 * edge
    dmg = max(1.0, dmg)
    dfn["hp"] = max(0.0, dfn["hp"] - dmg)
    atk["r_dmg"] += dmg
    atk["r_sig"] += 1

    wmod = C.WEIGHT_KO_MOD.get(state["opp"].get("weight", "light"), 1.0)
    power_action = a["power"] >= 0.85 or action_key in ("gnp", "knee")
    ko = 0.0
    if power_action or dfn["rocked"] > 0:
        ko = 0.014 + 0.038 * a["power"] * (off / 74.0)
        ko *= wmod * (1 + _passv(state, atk_who, "ko_power"))
        ko *= (1 + (100 - dfn["hp"]) / 110.0)
        ko *= (58.0 / max(25.0, dfn_at["chin"]))
        if dfn["rocked"] > 0:
            ko += 0.22
        if d_act["kind"] == "defend":
            ko *= 0.4
        ko = min(0.7, max(0.0, ko))

    lines.append(f'{subj}: {a["label"].lower()} — lands! (-{int(dmg)})')
    if dfn["hp"] <= 0 or random.random() < ko:
        method = "KO" if (power_action and dfn["rocked"] == 0 and random.random() < 0.6) else "TKO"
        atk["r_kd"] += 1
        _finish(state, atk_who, method, f'{a["label"]} drops {obj} - it\'s over.')
        lines.append(f'  >>> {subj} WIN{"" if atk_who == "player" else "S"} BY {method}! <<<')
        return lines, False

    # cuts and leg damage
    if action_key in HEAD_POWER and dmg >= 9 and random.random() < 0.05:
        dfn["cut"] += random.randint(16, 34)
        who_lbl = "You are" if dfn_who == "player" else dfn["name"] + " is"
        lines.append(f'  {who_lbl} cut — blood coming down.')
    if action_key == "lowkick" and random.random() < 0.09:
        dfn["leg"] += random.randint(8, 18)
        who_lbl = "Your" if dfn_who == "player" else dfn["name"] + "'s"
        lines.append(f'  {who_lbl} lead leg is buckling.')
    if action_key == "midkick" and random.random() < 0.06:
        dfn["stamina"] = max(0.0, dfn["stamina"] - random.randint(6, 14))
        who_lbl = "You take" if dfn_who == "player" else dfn["name"] + " takes"
        lines.append(f'  {who_lbl} it flush to the body — visibly winded.')

    if power_action and dmg >= 13 and random.random() < 0.33:
        dfn["rocked"] = 2
        dfn["r_kd"] += 1
        atk["r_sig"] += 1
        state["injuries"].append("rocked_player" if dfn_who == "player" else "rocked_opp")
        lines.append(f'  {"You are" if dfn_who == "player" else dfn["name"] + " is"} badly rocked!')
    if a.get("drain"):
        dfn["stamina"] = max(0.0, dfn["stamina"] - a["drain"])
    return lines, False


def _takedown(state, atk_who, dfn_who, resisted=False, from_clinch=False):
    atk_at = _attrs(state, atk_who)
    dfn_at = _attrs(state, dfn_who)
    atk = _side(state, atk_who)
    dfn = _side(state, dfn_who)
    att = _eff(state, atk_who, atk_at, "wrestling", atk["stamina"]) * 0.8 + _eff(state, atk_who, atk_at, "power", atk["stamina"]) * 0.2
    dff = _eff(state, dfn_who, dfn_at, "wrestling", dfn["stamina"]) * 0.7 + _eff(state, dfn_who, dfn_at, "cardio", dfn["stamina"]) * 0.3
    att *= (1 + _passv(state, atk_who, "td_success"))
    dff *= (1 + _passv(state, dfn_who, "td_def"))
    if dfn_who == "player":
        dff *= 1.06
    if atk_who == "player":
        att *= 1.04
    _edge = state.get("o_edge", 0.0)
    if _edge:
        att *= 1 + 0.06 * _edge if atk_who == "opp" else 1.0
        dff *= 1 + 0.07 * _edge if dfn_who == "opp" else 1.0
    if resisted:
        dff *= 1.15
    if from_clinch:
        att *= 1.1
    if atk_who == "player" and state["tactic"] == "ground":
        att *= 1.12
    pr = min(0.9, max(0.08, 0.5 + (att - dff) * 0.012))
    subj = "You" if atk_who == "player" else atk["name"]
    if random.random() < pr:
        state["pos"] = "ground"
        state["top"] = atk_who
        state["passed"] = False
        atk["r_td"] += 1
        where = "you on top" if atk_who == "player" else atk["name"] + " on top"
        return [f'{subj}: takedown lands — on the ground, {where}.']
    atk["stamina"] = max(0.0, atk["stamina"] - 5)
    if _attrs(state, dfn_who)["wrestling"] > 70 and random.random() < 0.22:
        state["pos"] = "ground"
        state["top"] = dfn_who
        state["passed"] = False
        dfn["r_td"] += 1
        return [f'{subj}: takedown countered — you land on bottom.' if atk_who == "player"
                else f'{subj}: takedown countered, you take top.']
    return [f'{subj}: takedown stuffed.']


def _ground(state, p_act, o_act):
    lines = []
    top = state["top"]

    def do_submit(atk_who, dfn_who, from_bottom=False):
        atk_at = _attrs(state, atk_who); dfn_at = _attrs(state, dfn_who)
        atk = _side(state, atk_who); dfn = _side(state, dfn_who)
        att = _eff(state, atk_who, atk_at, "bjj", atk["stamina"]) * 0.85 + _eff(state, atk_who, atk_at, "wrestling", atk["stamina"]) * 0.15
        dff = _eff(state, dfn_who, dfn_at, "bjj", dfn["stamina"]) * 0.7 + _eff(state, dfn_who, dfn_at, "cardio", dfn["stamina"]) * 0.3
        pr = 0.10 + (att - dff) * 0.009 + (100 - dfn["hp"]) / 300.0 + _passv(state, atk_who, "sub_success")
        if state["passed"] and not from_bottom:
            pr += 0.06
        if dfn["rocked"] > 0:
            pr += 0.12
        if from_bottom:
            pr *= 0.55
        pr = min(0.85, max(0.02, pr))
        subj = "You" if atk_who == "player" else atk["name"]
        if random.random() < pr:
            _finish(state, atk_who, "Submission", f'{subj} lock{"" if atk_who == "player" else "s"} it in — the tap comes.')
            return [f'  >>> {subj} WIN{"" if atk_who == "player" else "S"} BY SUBMISSION! <<<']
        atk["stamina"] = max(0.0, atk["stamina"] - 4)
        atk["r_sub"] += 1
        return [f'{subj}: submission attempt — defended.']

    def do_sweep(atk_who, dfn_who):
        atk_at = _attrs(state, atk_who); dfn_at = _attrs(state, dfn_who)
        atk = _side(state, atk_who)
        att = _eff(state, atk_who, atk_at, "bjj", atk["stamina"]) * 0.5 + _eff(state, atk_who, atk_at, "wrestling", atk["stamina"]) * 0.5
        dff = _eff(state, dfn_who, dfn_at, "wrestling", 60) * 0.6 + _eff(state, dfn_who, dfn_at, "bjj", 60) * 0.4
        pr = min(0.85, max(0.05, 0.32 + (att - dff) * 0.011 + _passv(state, atk_who, "sweep")))
        subj = "You" if atk_who == "player" else atk["name"]
        if random.random() < pr:
            state["top"] = atk_who
            state["passed"] = False
            atk["r_ctrl"] += 3
            return [f'{subj}: sweep! Now {"you" if atk_who == "player" else atk["name"]} on top.']
        return [f'{subj}: sweep attempt fails.']

    def do_standup(atk_who):
        atk_at = _attrs(state, atk_who)
        dfn_who = "opp" if atk_who == "player" else "player"
        dfn_at = _attrs(state, dfn_who)
        atk = _side(state, atk_who)
        att = _eff(state, atk_who, atk_at, "wrestling", atk["stamina"]) * 0.5 + _eff(state, atk_who, atk_at, "cardio", atk["stamina"]) * 0.5
        dff = _eff(state, dfn_who, dfn_at, "wrestling", 60) * 0.7 + _eff(state, dfn_who, dfn_at, "bjj", 60) * 0.3
        pr = min(0.85, max(0.08, 0.4 + (att - dff) * 0.011))
        subj = "You" if atk_who == "player" else atk["name"]
        if random.random() < pr:
            state["pos"] = "stand"; state["top"] = None; state["passed"] = False
            return [f'{subj}: back up to the feet.']
        return [f'{subj}: scramble to stand — dragged back down.']

    def do_pass(atk_who):
        atk_at = _attrs(state, atk_who)
        dfn_who = "opp" if atk_who == "player" else "player"
        dfn_at = _attrs(state, dfn_who)
        atk = _side(state, atk_who)
        pr = 0.45 + (_eff(state, atk_who, atk_at, "bjj", atk["stamina"]) - _eff(state, dfn_who, dfn_at, "bjj", 60)) * 0.012
        subj = "You" if atk_who == "player" else atk["name"]
        if random.random() < min(0.9, max(0.1, pr)):
            state["passed"] = True
            _side(state, atk_who)["r_ctrl"] += 2
            return [f'{subj}: pass the guard — dominant position.']
        return [f'{subj}: guard pass stuffed.']

    if top == "player":
        if p_act == "submit":
            lines += do_submit("player", "opp")
        elif p_act == "pass_guard":
            lines += do_pass("player")
        if state["over"]:
            return lines
        if o_act == "sweep":
            lines += do_sweep("opp", "player")
        elif o_act == "sub_bottom":
            lines += do_submit("opp", "player", from_bottom=True)
        elif o_act == "standup_bottom":
            lines += do_standup("opp")
    else:
        if o_act == "submit":
            lines += do_submit("opp", "player")
        elif o_act == "pass_guard":
            lines += do_pass("opp")
        if state["over"]:
            return lines
        if p_act == "sweep":
            lines += do_sweep("player", "opp")
        elif p_act == "sub_bottom":
            lines += do_submit("player", "opp", from_bottom=True)
        elif p_act == "standup_bottom":
            lines += do_standup("player")
    return lines


def _finish(state, winner_who, method, text):
    state["over"] = True
    won = winner_who == "player"
    state["result"] = {"outcome": "win" if won else "loss", "method": method,
                       "round": state["round"], "text": text, "opp": state["opp"],
                       "war": state["war"], "rocked": "rocked_player" in state.get("injuries", [])}


# --- round / fight end ---------------------------------------------

SCORE_W = {"sig": 2.4, "dmg": 0.55, "td": 7.0, "ctrl": 2.2, "sub": 4.0, "kd": 20.0}


def _round_points(s) -> float:
    return (s["r_sig"] * SCORE_W["sig"] + s["r_dmg"] * SCORE_W["dmg"] + s["r_td"] * SCORE_W["td"]
            + s["r_ctrl"] * SCORE_W["ctrl"] + s["r_sub"] * SCORE_W["sub"] + s["r_kd"] * SCORE_W["kd"])


def _round_stat(s) -> dict:
    return {"sig": int(round(s["r_sig"])), "td": s["r_td"], "ctrl": round(s["r_ctrl"], 1),
            "kd": s["r_kd"], "sub": s["r_sub"], "dmg": int(s["r_dmg"])}


def round_stats(state) -> dict:
    """Live per-round tally for the fight screen."""
    return {"p": _round_stat(state["p"]), "o": _round_stat(state["o"]),
            "p_pts": round(_round_points(state["p"])), "o_pts": round(_round_points(state["o"]))}


def end_exchange(state):
    if state["over"]:
        return
    state["exchange"] += 1
    if state["exchange"] < C.EXCHANGES_PER_ROUND:
        return
    p, o = state["p"], state["o"]
    ps, os_ = _round_points(p), _round_points(o)
    margin = ps - os_
    kd = p["r_kd"] - o["r_kd"]

    if abs(margin) <= 3 and kd == 0:
        pc, oc, winner = 10, 10, "even"
        dominant = False
    elif margin > 0:
        dominant = kd >= 1 or (margin >= 40 and os_ < 11)
        pc, oc = (10, 8) if dominant else (10, 9)
        winner = "You"
    else:
        dominant = kd <= -1 or (-margin >= 40 and ps < 11)
        pc, oc = (8, 10) if dominant else (9, 10)
        winner = o["name"]
    p["cards"] += pc
    o["cards"] += oc
    state["scorecard"].append({"round": state["round"], "p": pc, "o": oc})

    recap = {"round": state["round"], "winner": winner,
             "p_score": round(ps), "o_score": round(os_),
             "p_cards": p["cards"], "o_cards": o["cards"], "dominant": dominant,
             "p_stats": _round_stat(p), "o_stats": _round_stat(o),
             "scorecard": list(state["scorecard"])}

    for s in (p, o):
        s["r_sig"] = 0
        s["r_dmg"] = 0.0
        s["r_td"] = 0
        s["r_ctrl"] = 0.0
        s["r_sub"] = 0
        s["r_kd"] = 0
    p["rocked"] = o["rocked"] = 0
    p["cut"] *= 0.6
    o["cut"] *= 0.6
    p["stamina"] = min(100.0, p["stamina"] + REST_BETWEEN_ROUNDS)
    o["stamina"] = min(100.0, o["stamina"] + REST_BETWEEN_ROUNDS)
    state["pos"] = "stand"; state["top"] = None; state["passed"] = False
    state["exchange"] = 0

    if state["round"] >= state["max_rounds"]:
        _decision(state, recap)
    else:
        state["round"] += 1
        recap["next_round"] = state["round"]
        recap["can_corner"] = True
        state["recap"] = recap


def _decision(state, recap):
    p, o = state["p"], state["o"]
    if p["cards"] > o["cards"]:
        outcome, method = "win", ("Unanimous decision" if p["cards"] - o["cards"] >= 3 else "Split decision")
    elif o["cards"] > p["cards"]:
        outcome, method = "loss", ("Unanimous decision" if o["cards"] - p["cards"] >= 3 else "Split decision")
    else:
        outcome, method = "draw", "Draw"
    recap["final"] = True
    state["recap"] = recap
    state["over"] = True
    state["result"] = {"outcome": outcome, "method": method, "round": state["max_rounds"],
                       "text": f'Scorecards: {p["cards"]}-{o["cards"]}.',
                       "opp": state["opp"], "war": state["war"],
                       "rocked": "rocked_player" in state.get("injuries", [])}


def set_tactic(state, tactic):
    if tactic in C.TACTICS:
        state["tactic"] = tactic


def corner_advice(state):
    p, o = state["p"], state["o"]
    tips = []
    if p["cards"] < o["cards"]:
        tips.append("You're behind on the cards — you need a finish or a clearly won round.")
    elif p["cards"] > o["cards"]:
        tips.append("You're ahead. Don't take stupid risks, bring it home.")
    if p["stamina"] < 45:
        tips.append("Your gas tank is dropping — think about conserving and clinching.")
    if o["stamina"] < 40:
        tips.append(f'{o["name"]} is sucking wind — pressure and pour it on.')
    if o["hp"] < 45:
        tips.append("They're hurt and fading — hunt the finish.")
    if o["cut"] >= 30:
        tips.append("They're cut — target it, force the doctor's hand.")
    if state["o_style"] in ("wrestler", "grappler"):
        tips.append("They want the ground — defend takedowns and get back up.")
    if p["leg"] >= 20:
        tips.append("Your lead leg is hurt — check the kicks or switch stance.")
    return tips or ["Stick to the plan. It's close."]


def bars(state):
    return {"p_hp": int(state["p"]["hp"]), "o_hp": int(state["o"]["hp"]),
            "p_sta": int(state["p"]["stamina"]), "o_sta": int(state["o"]["stamina"])}


def auto_action(state, rng=None):
    """Heuristic player policy for the Simulate button. Follows the game plan."""
    rng = rng or random
    p, o = state["p"], state["o"]
    S = allowed_actions(state)
    pos = state["pos"]
    plan = state["tactic"]

    if pos == "ground" and state["top"] == "opp":
        if p["hp"] < 30 and "defend_bottom" in S:
            return ["defend_bottom"]
        if "sub_bottom" in S and o["stamina"] < 30 and rng.random() < 0.3:
            return ["sub_bottom"]
        return ["standup_bottom"] if rng.random() < 0.62 else (["sweep"] if "sweep" in S else ["defend_bottom"])

    if pos == "ground" and state["top"] == "player":
        if "submit" in S and (o["hp"] < 55 or o["stamina"] < 35 or plan == "ground"):
            if rng.random() < (0.5 if plan == "ground" else 0.35):
                return ["submit"]
        if "pass_guard" in S and not state["passed"] and rng.random() < 0.4:
            return ["pass_guard"]
        if plan in ("ground", "conserve") and rng.random() < 0.45:
            return ["control"]
        return ["gnp"]

    if pos == "clinch":
        if plan == "ground" and "trip" in S and rng.random() < 0.5:
            return ["trip"]
        if "knee" in S and rng.random() < 0.45:
            return ["knee"]
        if plan == "counter" and rng.random() < 0.3:
            return ["defend_clinch"]
        return ["dirtybox"]

    # standing
    if p["hp"] < 24 and "defend_stand" in S:
        return ["defend_stand"]
    if p["stamina"] < 22:
        return ["jab"] if "jab" in S else ["defend_stand"]
    if o["hp"] < 45 or o["rocked"]:
        return ["cross", "cross"] if "cross" in S else ["jab", "cross"]
    if plan == "ground" and "td_stand" in S and rng.random() < 0.6:
        return ["td_stand"]
    if plan == "conserve" and rng.random() < 0.35:
        return ["defend_stand"] if o["stamina"] > 45 else ["jab", "body"]
    if plan == "counter" and rng.random() < 0.4:
        return rng.choice([["jab"], ["defend_stand"], ["lowkick"]])
    opts = [["jab", "cross"], ["jab", "body"], ["lowkick"], ["midkick", "cross"], ["jab", "jab", "cross"]]
    if plan == "pressure":
        opts += [["cross", "body"], ["jab", "cross", "body"], ["midkick"]]
    if state["p_style"] in ("wrestler", "grappler") and "td_stand" in S:
        opts += [["td_stand"], ["clinch_up"]]
    return rng.choice(opts)


def win_prob(player_attrs, opp) -> int:
    def pw(a):
        return (a["power"] * 1.1 + a["striking"] * 1.2 + a["wrestling"] + a["bjj"]
                + a["cardio"] * 0.9 + a["chin"] * 0.8) / 6.0
    d = pw(player_attrs) - pw(opp["attrs"])
    o_tier = max(0, min(opp.get("tier", 0), len(C.TIERS) - 1))
    edge = C.TIERS[o_tier].get("edge", 0.0)
    return int(max(5, min(95, 52 + d * 2.4 - edge * 6)))
