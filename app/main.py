"""Born to Fight - a web-based MMA career simulator. FastAPI + Jinja2."""

from __future__ import annotations

import json
import os
import re
import secrets
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeTimedSerializer

from . import avatar as AV
from . import content as C
from . import feedback as FB
from . import fight as F
from . import game as G
from . import i18n as I
from . import world as W

BASE = Path(__file__).resolve().parent.parent
_NS_RE = re.compile(r"^[a-f0-9]{8,64}$")

# Admin panel is off unless BT_ADMIN_KEY is set in the environment.
ADMIN_KEY = os.environ.get("BT_ADMIN_KEY", "")
_admin_signer = URLSafeTimedSerializer(ADMIN_KEY or "disabled", salt="bt-admin")
ADMIN_MAX_AGE = 60 * 60 * 12


def _is_admin(request: Request) -> bool:
    if not ADMIN_KEY:
        return False
    tok = request.cookies.get("bt_admin", "")
    try:
        return _admin_signer.loads(tok, max_age=ADMIN_MAX_AGE) == "ok"
    except (BadSignature, Exception):
        return False

app = FastAPI(title="Born to Fight")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.middleware("http")
async def _visitor_namespace(request: Request, call_next):
    """Give each browser its own save namespace via a long-lived cookie."""
    pid = request.cookies.get("bt_player")
    fresh = not (pid and _NS_RE.match(pid))
    if fresh:
        pid = secrets.token_hex(16)
    G.set_namespace(pid)
    request.state.ns = pid
    try:
        ev = {"/fight/sim": "sim", "/fight/action": "fight_action",
              "/create": "career"}.get(request.url.path, "") if request.method == "POST" else ""
        FB.bump(request.url.path, ns=pid, event=ev)
    except Exception:
        pass
    response = await call_next(request)
    if fresh:
        response.set_cookie("bt_player", pid, max_age=60 * 60 * 24 * 730,
                            samesite="lax", httponly=True)
    return response


def _legacy_file():
    return G.legacy_file()


templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.globals.update(
    C=C, ATTRS=C.ATTRS, ATTR_LABELS=C.ATTR_LABELS, ATTR_DESC=C.ATTR_DESC,
    TRAININGS=C.TRAININGS, ACTIONS=C.ACTIONS, WEIGHT_LABELS=C.WEIGHT_LABELS,
    STYLES=C.STYLES, TIERS=C.TIERS, STAFF=C.STAFF, CUTS=C.CUTS, TACTICS=C.TACTICS,
    LOOKS=C.LOOKS, DEFAULT_LOOK=C.DEFAULT_LOOK, DIFFICULTY=C.DIFFICULTY, PLANS=C.PLANS,
    GAME_MODES=C.GAME_MODES, SPONSORS=C.SPONSORS, ACHIEVEMENTS=C.ACHIEVEMENTS, NATIONS=C.NATIONS,
    flag=lambda e: C.NATIONS.get((e or {}).get("nation", ""), {}).get("flag", ""),
    overall=G.overall, rating=G.rating, career_progress=G.career_progress,
    injury_risk=G.injury_risk,
    wear=G.wear, avatar=AV.portrait, date_str=W.date_str, ava_url=AV.url,
)


import datetime as _dt
templates.env.filters["ts"] = lambda t: _dt.datetime.fromtimestamp(float(t or 0)).strftime("%Y-%m-%d %H:%M")


def _lang(request: Request) -> str:
    return I.normalize(request.cookies.get("lang"))


def render(name, request, **ctx):
    lang = _lang(request)
    ctx["lang"] = lang
    ctx["t"] = lambda s: I.t(s, lang)
    return templates.TemplateResponse(request, name, ctx)


def redirect(url):
    return RedirectResponse(url, status_code=303)


def _load():
    return G.load()


def _legacy():
    if _legacy_file().exists():
        try:
            return json.loads(_legacy_file().read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def upcoming_opp(state: dict) -> dict:
    world = state["world"]
    fid = state.get("next_opp_id")
    opp = W.get_fighter(world, fid) if fid else None
    if not opp or opp.get("retired") or opp.get("is_player"):
        opp = W.pick_opponent(world, state["fighter"])
        state["next_opp_id"] = opp["id"]
        G.save(state)
    return opp


def stakes_for(state: dict) -> dict:
    f = state["fighter"]
    c = f.get("contract") or {}
    for_title = bool(f.get("title_shot") or f["champion"])
    opp = upcoming_opp(state)
    return {
        "org": c.get("org", C.TIERS[f["tier"]]["name"]),
        "rounds": C.TITLE_ROUNDS if for_title else 3,
        "for_title": for_title,
        "purse": c.get("purse", 0),
        "win_bonus": c.get("bonus", 0),
        "opp": opp,
        "rivalry": f.get("rivalries", {}).get(opp["id"], {}),
        "date": W.date_str(state["world"]),
        "prob": F.win_prob(f["attrs"], opp),
    }


# --- Menu / slots -------------------------------------------------------

@app.get("/lang/{code}")
def set_lang(code: str, request: Request):
    ref = request.headers.get("referer") or "/"
    resp = RedirectResponse(ref, status_code=303)
    resp.set_cookie("lang", I.normalize(code), max_age=60 * 60 * 24 * 365, samesite="lax")
    return resp


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return render("index.html", request, saves=G.list_saves(), active=G.get_active(),
                  legacy=_legacy())


# --- Feedback + admin -------------------------------------------------

@app.post("/feedback")
def feedback_submit(request: Request, text: str = Form(...), kind: str = Form("other"),
                    page: str = Form("")):
    ns = getattr(request.state, "ns", "")
    if FB.recent_rate(ns) >= 5:
        return Response('{"ok":false,"error":"rate"}', media_type="application/json")
    fighter = ""
    st = G.load()
    if st:
        fighter = st.get("fighter", {}).get("name", "")
    ok = FB.add(text, kind, page=page, ns=ns, fighter=fighter)
    return Response(f'{{"ok":{str(ok).lower()}}}', media_type="application/json")


@app.get("/admin/{key}")
def admin_login(key: str):
    if not ADMIN_KEY or not secrets.compare_digest(key, ADMIN_KEY):
        return Response("Not found", status_code=404)
    resp = RedirectResponse("/admin", status_code=303)
    resp.set_cookie("bt_admin", _admin_signer.dumps("ok"), max_age=ADMIN_MAX_AGE,
                    samesite="lax", httponly=True)
    return resp


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    if not _is_admin(request):
        return Response("Not found", status_code=404)
    return render("admin.html", request, stats=FB.world_stats(),
                  site=FB.site_stats(), items=FB.all_items())


@app.post("/admin/fb/{ts}")
def admin_fb_toggle(request: Request, ts: float):
    if not _is_admin(request):
        return Response("Not found", status_code=404)
    FB.toggle_resolved(ts)
    return redirect("/admin")


@app.get("/admin-logout")
def admin_logout():
    resp = redirect("/")
    resp.delete_cookie("bt_admin")
    return resp


@app.get("/avatar.svg")
def avatar_svg(request: Request):
    q = request.query_params
    look = {k: q[k] for k in C.LOOK_KEYS if k in q}
    try:
        size = max(48, min(320, int(q.get("size", 180))))
    except ValueError:
        size = 180
    try:
        w = max(0, min(3, int(q.get("wear", 0))))
    except ValueError:
        w = 0
    return Response(AV.portrait(look, size=size, wear=w), media_type="image/svg+xml",
                    headers={"Cache-Control": "no-cache"})


@app.post("/slot/activate")
def slot_activate(slot: str = Form(...)):
    if G.load(slot):
        G.set_active(slot)
    return redirect("/hub")


@app.post("/slot/delete")
def slot_delete(slot: str = Form(...)):
    G.delete_slot(slot)
    return redirect("/")


@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request):
    legacy = _legacy()
    pts = C.START_POINTS + (legacy["bonus_points"] if legacy else 0)
    seed = G.random_seed(pts)                     # every new career starts different
    return render("create.html", request, attrs=seed["attrs"], points=pts,
                  cap=C.START_ATTR_CAP, base=C.START_BASE, weights=C.WEIGHT_CLASSES,
                  legacy=legacy, error=None, seed=seed)


@app.post("/create")
async def create_submit(request: Request):
    form = await request.form()
    legacy = _legacy()
    pts = C.START_POINTS + (legacy["bonus_points"] if legacy else 0)

    name = form.get("name", "")
    nickname = form.get("nickname", "")
    try:
        age = int(form.get("age", "22"))
    except ValueError:
        age = 22
    age = max(18, min(33, age))
    weight = form.get("weight", "light")
    style = form.get("style", "balanced")
    nation = form.get("nation", "USA")
    difficulty = form.get("difficulty", "normal")
    mode = form.get("mode", "standard")
    attrs = {}
    for k in C.ATTRS:
        try:
            attrs[k] = int(form.get(f"attr_{k}", C.START_BASE))
        except ValueError:
            attrs[k] = C.START_BASE
    look = {}
    for k, opts in C.LOOKS.items():
        v = form.get(f"look_{k}")
        if v in {code for _, code in opts}:
            look[k] = v

    submitted = {"name": name, "nickname": nickname, "age": age, "weight": weight,
                 "style": style, "nation": nation, "look": {**C.DEFAULT_LOOK, **look},
                 "difficulty": difficulty, "mode": mode, "attrs": attrs}

    spent = sum(attrs[k] - C.START_BASE for k in C.ATTRS)
    err = None
    if spent > pts or any(v < C.START_BASE or v > C.START_ATTR_CAP for v in attrs.values()):
        err = "Invalid point spread."
    elif len(G.list_saves()) >= 25:
        err = "Save slots full - delete an old career first."
    if err:
        return render("create.html", request, attrs=attrs, points=pts, cap=C.START_ATTR_CAP,
                      base=C.START_BASE, weights=C.WEIGHT_CLASSES, legacy=legacy,
                      error=err, seed=submitted)

    state = G.new_state(name, nickname, age, weight, style, attrs, legacy, look, difficulty, mode, nation)
    G.save(state)
    G.set_active(state["slot"])
    _legacy_file().unlink(missing_ok=True)
    return redirect("/hub")


# --- Hub / camp -------------------------------------------------------

@app.get("/hub", response_class=HTMLResponse)
def hub(request: Request):
    state = _load()
    if not state:
        return redirect("/")
    f = state["fighter"]
    if f["retired"]:
        return redirect("/career")
    if "fight" in state:
        return redirect("/fight")
    if state.get("offers"):
        return redirect("/offers")
    if "camp" not in state:
        G.start_camp(state)
    stakes = stakes_for(state)
    G.save(state)
    return render("hub.html", request, f=f, camp=state["camp"], stakes=stakes,
                  tier=C.TIERS[f["tier"]], world=state["world"])


@app.post("/plan")
def set_plan(plan: str = Form(...)):
    state = _load()
    if state and "fight" not in state:
        G.set_plan(state, plan)
        G.save(state)
    return redirect("/hub")


@app.post("/train")
def do_train(kind: str = Form(...)):
    state = _load()
    if not state or "camp" not in state or kind not in C.TRAININGS:
        return redirect("/hub")
    if state["camp"]["left"] > 0:
        res = G.train(state, kind)
        state["camp"]["notes"].insert(0, {"kind": C.TRAININGS[kind]["label"], "injury": res["injury"]})
        G.save(state)
    return redirect("/hub")


@app.get("/staff", response_class=HTMLResponse)
def staff_page(request: Request):
    state = _load()
    if not state:
        return redirect("/")
    return render("staff.html", request, f=state["fighter"])


@app.post("/staff/buy")
def staff_buy(key: str = Form(...)):
    state = _load()
    if not state:
        return redirect("/")
    G.buy_staff(state, key)
    G.save(state)
    return redirect("/staff")


@app.get("/sponsors", response_class=HTMLResponse)
def sponsors_page(request: Request):
    state = _load()
    if not state:
        return redirect("/")
    return render("sponsors.html", request, f=state["fighter"],
                  current=next((s for s in C.SPONSORS if s["id"] == state["fighter"].get("sponsor")), None))


@app.post("/sponsors/sign")
def sponsors_sign(sid: str = Form(...)):
    state = _load()
    if not state:
        return redirect("/")
    G.sign_sponsor(state, sid)
    G.save(state)
    return redirect("/sponsors")


# --- Division / profiles --------------------------------------------

@app.get("/division", response_class=HTMLResponse)
def division_page(request: Request):
    state = _load()
    if not state:
        return redirect("/")
    W.sync_player(state)
    G.save(state)
    return render("division.html", request, f=state["fighter"],
                  roster=W.roster(state["world"]), world=state["world"],
                  champ=W.get_fighter(state["world"], state["world"].get("champion_id")))


@app.get("/fighter/{fid}", response_class=HTMLResponse)
def fighter_page(request: Request, fid: str):
    state = _load()
    if not state:
        return redirect("/")
    W.sync_player(state)
    other = W.get_fighter(state["world"], fid)
    if not other:
        return redirect("/division")
    f = state["fighter"]
    riv = f.get("rivalries", {}).get(fid)
    tale = [(C.ATTR_LABELS[k], f["attrs"][k], other["attrs"][k]) for k in C.ATTRS]
    return render("fighter.html", request, f=f, o=other, riv=riv, tale=tale,
                  prob=F.win_prob(f["attrs"], other))


# --- Contract offers ----------------------------------------------

@app.get("/offers", response_class=HTMLResponse)
def offers_page(request: Request):
    state = _load()
    if not state:
        return redirect("/")
    if not state.get("offers"):
        return redirect("/hub")
    return render("offers.html", request, f=state["fighter"], offers=state["offers"])


@app.post("/offers/sign")
def offers_sign(offer: str = Form(...)):
    state = _load()
    if not state:
        return redirect("/")
    o = W.sign(state, offer)
    if o:
        state.pop("next_opp_id", None)
        state["fighter"]["log"].insert(0, f'Signed a contract: {o["org"]} ({o["fights"]} fights).')
        G.save(state)
    return redirect("/hub")


# --- Weigh-in / weight cut ---------------------------------------

@app.get("/weighin", response_class=HTMLResponse)
def weighin_page(request: Request):
    state = _load()
    if not state or state["fighter"]["retired"]:
        return redirect("/hub")
    return render("weighin.html", request, f=state["fighter"], stakes=stakes_for(state))


@app.post("/weighin")
def weighin_submit(cut: str = Form("standard"), go: str = Form("play")):
    state = _load()
    if not state or state["fighter"]["retired"]:
        return redirect("/hub")
    if "fight" in state:
        return redirect("/fight")
    G.set_cut(state, cut)
    f = state["fighter"]
    stakes = stakes_for(state)
    cut = f.get("next_cut", "standard")
    catk = G.combat_attrs(f, cut)
    fs = F.init_fight(catk, stakes["opp"], stakes["rounds"], stakes["for_title"],
                      f["style"], C.CUTS[cut]["stamina"],
                      f.get("look", {}).get("stance", "ortho"),
                      f.get("next_plan", "normal"))
    fs["stakes"] = {"purse": stakes["purse"], "win_bonus": stakes["win_bonus"],
                    "for_title": stakes["for_title"], "org": stakes["org"]}
    state["fight"] = fs
    state.pop("camp", None)
    if go == "sim":
        _run_sim(fs, to_end=True)
    G.save(state)
    return redirect("/fight/result" if fs["over"] and not fs.get("recap") else "/fight")


def _run_sim(fs, to_end: bool):
    guard = 0
    while guard < 600:
        guard += 1
        if fs["over"]:
            if to_end and fs.get("recap"):
                fs["recap"] = None       # skip the "Verdict" click
            return
        if fs.get("recap"):
            if to_end:
                fs["recap"] = None
                continue
            return
        lines = F.resolve(fs, F.auto_action(fs))
        fs["log"].insert(0, {"round": fs["round"], "exch": fs["exchange"] + 1, "lines": lines, "sim": True})
        F.end_exchange(fs)


# --- Fight ------------------------------------------------------

@app.get("/fight", response_class=HTMLResponse)
def fight_screen(request: Request):
    state = _load()
    if not state or "fight" not in state:
        return redirect("/hub")
    fs = state["fight"]
    if fs["over"] and not fs.get("recap"):
        return redirect("/fight/result")
    return render("fight.html", request, fs=fs, f=state["fighter"], bars=F.bars(fs),
                  pos=F.pos_label(fs), actions=F.allowed_actions(fs),
                  combo=F.combo_actions(fs), recap=fs.get("recap"),
                  rstats=F.round_stats(fs),
                  advice=F.corner_advice(fs) if fs.get("recap") else None)


@app.post("/fight/action")
def fight_action(combo: str = Form(""), move: str = Form("")):
    state = _load()
    if not state or "fight" not in state:
        return redirect("/hub")
    fs = state["fight"]
    if fs["over"] or fs.get("recap"):
        return redirect("/fight")
    raw = combo or move
    moves = [m for m in raw.split(",") if m][:C.COMBO_MAX]
    if not moves:
        return redirect("/fight")
    lines = F.resolve(fs, moves)
    fs["log"].insert(0, {"round": fs["round"], "exch": fs["exchange"] + 1, "lines": lines})
    F.end_exchange(fs)
    G.save(state)
    return redirect("/fight")


@app.post("/fight/sim")
def fight_sim(scope: str = Form("round")):
    state = _load()
    if not state or "fight" not in state:
        return redirect("/hub")
    fs = state["fight"]
    if fs["over"]:
        return redirect("/fight/result")
    if fs.get("recap"):
        return redirect("/fight")
    _run_sim(fs, to_end=(scope == "end"))
    G.save(state)
    if fs["over"] and not fs.get("recap"):
        return redirect("/fight/result")
    return redirect("/fight")


@app.post("/fight/corner")
def fight_corner(tactic: str = Form("normal")):
    state = _load()
    if not state or "fight" not in state:
        return redirect("/hub")
    fs = state["fight"]
    F.set_tactic(fs, tactic)
    fs["recap"] = None
    G.save(state)
    return redirect("/fight/result" if fs["over"] else "/fight")


@app.post("/fight/continue")
def fight_continue():
    state = _load()
    if not state or "fight" not in state:
        return redirect("/hub")
    fs = state["fight"]
    fs["recap"] = None
    G.save(state)
    return redirect("/fight/result" if fs["over"] else "/fight")


@app.get("/fight/result", response_class=HTMLResponse)
def fight_result(request: Request):
    state = _load()
    if not state:
        return redirect("/")
    if "fight" not in state and "last_result" not in state:
        return redirect("/hub")
    if "fight" in state:
        fs = state["fight"]
        if not fs["over"]:
            return redirect("/fight")
        if fs.get("recap"):
            return redirect("/fight")
        result = dict(fs["result"])
        result["stakes"] = fs.get("stakes")
        result["log"] = [ln for ex in fs.get("log", []) for ln in ex["lines"]]
        ch = G.apply_result(state, result)
        f = state["fighter"]
        state["last_result"] = {
            "outcome": result["outcome"], "method": result["method"], "round": result["round"],
            "text": result["text"], "opp_name": result["opp"]["name"],
            "opp_nick": result["opp"].get("nickname", ""),
            "lines": ch["lines"], "news": ch["news"], "purse": ch["purse"],
            "promoted": ch.get("promoted"), "forced_retire": ch["forced_retire"],
            "achievements": ch.get("achievements", []),
        }
        state.pop("next_opp_id", None)
        if not f["retired"]:
            G.start_camp(state)
        G.save(state)
    return render("result.html", request, lr=state["last_result"], f=state["fighter"])


@app.post("/fight/result/ack")
def fight_result_ack():
    state = _load()
    if not state:
        return redirect("/")
    state.pop("last_result", None)
    G.save(state)
    if state["fighter"]["retired"]:
        return redirect("/career")
    if state.get("offers"):
        return redirect("/offers")
    return redirect("/hub")


# --- Career / retirement / legacy -------------------------------

@app.post("/retire")
def retire():
    state = _load()
    if state:
        state["fighter"]["retired"] = True
        state["fighter"]["log"].insert(0, "The fighter announces his retirement.")
        state.pop("fight", None)
        state.pop("camp", None)
        G.save(state)
    return redirect("/career")


@app.get("/career", response_class=HTMLResponse)
def career(request: Request):
    state = _load()
    if not state:
        return redirect("/")
    f = state["fighter"]
    riv = sorted(f.get("rivalries", {}).values(), key=lambda r: -r.get("heat", 0))[:6]
    ach_names = {a[0]: (a[1], a[2]) for a in C.ACHIEVEMENTS}
    return render("career.html", request, f=f, tier=C.TIERS[f["tier"]],
                  rivalries=riv, ach_names=ach_names,
                  hof=(G.hall_of_fame(f) if f["retired"] else None),
                  legacy=(G.build_legacy(f) if f["retired"] else None))


@app.get("/replay/{idx}", response_class=HTMLResponse)
def replay_page(request: Request, idx: int):
    state = _load()
    if not state:
        return redirect("/")
    reps = state["fighter"].get("replays", [])
    if idx < 0 or idx >= len(reps):
        return redirect("/career")
    return render("replay.html", request, f=state["fighter"], rep=reps[idx], idx=idx)


@app.post("/legacy")
def legacy_start():
    state = _load()
    if not state or not state["fighter"]["retired"]:
        return redirect("/career")
    leg = G.build_legacy(state["fighter"])
    G.SAVES_DIR.mkdir(exist_ok=True)
    _legacy_file().write_text(json.dumps(leg, ensure_ascii=False, indent=2), encoding="utf-8")
    return redirect("/create")
