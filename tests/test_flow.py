"""Full-game HTTP walkthroughs + fight-engine sanity + new-system checks."""

import random
import re

import pytest
from starlette.testclient import TestClient

from app import content as C
from app import fight as F
from app import game as G
from app import world as W
from app import i18n as I
from app.main import app


@pytest.fixture(autouse=True)
def _clean(tmp_path, monkeypatch):
    from app import feedback as FB
    d = tmp_path / "saves"
    d.mkdir()
    monkeypatch.setattr(G, "SAVES_DIR", d)
    monkeypatch.setattr(G, "TEST_NS", "test")   # client + bare G.* share one namespace
    monkeypatch.setattr(FB, "_STATS", None)
    monkeypatch.setattr(FB, "_SEEN_TODAY", set())
    monkeypatch.setattr(FB, "_SEEN_HOUR", set())
    yield


def _client():
    return TestClient(app, follow_redirects=True)


def _create(c, **over):
    data = {"name": "Test Fighter", "nickname": "Block", "age": "22", "weight": "light",
            "style": "balanced", "difficulty": "normal", "mode": "standard",
            "attr_power": "44", "attr_striking": "42", "attr_wrestling": "36",
            "attr_bjj": "34", "attr_cardio": "30", "attr_chin": "30"}
    data.update(over)
    r = c.post("/create", data=data)
    assert str(r.url).endswith("/hub"), r.text[:300]
    return r


def _finish_fight(c, rng):
    r = c.get("/fight")
    for _ in range(600):
        if "result-banner" in r.text:
            return r.text
        if 'action="/fight/corner"' in r.text:
            r = c.post("/fight/corner", data={"tactic": rng.choice(list(C.TACTICS))})
            continue
        if 'action="/fight/continue"' in r.text:
            r = c.post("/fight/continue")
            continue
        moves = re.findall(r'name="move" value="([a-z_]+)"', r.text)
        combo = re.findall(r'class="comboadd" data-a="([a-z_]+)"', r.text)
        assert moves, ("no actions on the fight screen", str(r.url))
        if combo and rng.random() < 0.5:
            n = rng.randint(1, min(C.COMBO_MAX, len(combo)))
            r = c.post("/fight/action", data={"combo": ",".join(rng.choice(combo) for _ in range(n))})
        else:
            r = c.post("/fight/action", data={"move": rng.choice(moves)})
    raise AssertionError("fight did not finish")


@pytest.mark.parametrize("seed", [1, 7, 13, 21, 99])
def test_full_career(seed):
    rng = random.Random(seed)
    c = _client()
    c.get("/")
    _create(c, style=rng.choice(list(C.STYLES)),
            difficulty=rng.choice(list(C.DIFFICULTY)),
            mode="standard")

    for _ in range(200):
        st = G.load()
        if st["fighter"]["retired"]:
            break
        if st.get("offers"):
            oid = rng.choice(st["offers"])["id"]
            r = c.post("/offers/sign", data={"offer": oid})
            assert str(r.url).endswith("/hub")
            continue
        for _ in range(8):
            assert c.post("/train", data={"kind": rng.choice(list(C.TRAININGS))}).status_code == 200
        if rng.random() < 0.3:
            c.post("/staff/buy", data={"key": rng.choice(list(C.STAFF))})
        if rng.random() < 0.3:
            c.post("/sponsors/sign", data={"sid": rng.choice([s["id"] for s in C.SPONSORS] + ["none"])})
        assert c.get("/division").status_code == 200
        assert c.get("/career").status_code == 200
        assert c.get("/weighin").status_code == 200
        r = c.post("/weighin", data={"cut": rng.choice(list(C.CUTS))})
        txt = _finish_fight(c, rng)
        assert "Internal Server Error" not in txt
        assert c.post("/fight/result/ack").status_code == 200

    final = G.load()["fighter"]
    assert final["fights"] >= 3
    assert 0 <= final["brain"] <= 100
    assert final["record"]["w"] + final["record"]["l"] + final["record"]["d"] == final["fights"]
    # replays and records populated
    assert final["replays"]
    assert final["records"]["career_purses"] >= 0


def test_engine_balance():
    import collections
    rng = random.Random(0)
    methods = collections.Counter()
    world = {"seq": 0, "difficulty": "normal"}
    for _ in range(300):
        attrs = {k: rng.randint(40, 80) for k in C.ATTRS}
        opp = W.make_npc(world, "light", rng.randint(0, 3), rng.randint(1, 12), set())
        fs = F.init_fight(attrs, opp, 3, False, rng.choice(list(C.STYLES)))
        guard = 0
        while not fs["over"] and guard < 400:
            guard += 1
            if fs.get("recap"):
                fs["recap"] = None
                continue
            acts = F.allowed_actions(fs)
            F.resolve(fs, [rng.choice(acts)])
            F.end_exchange(fs)
        assert fs["over"]
        methods[fs["result"]["method"]] += 1
    total = sum(methods.values())
    finishes = sum(v for k, v in methods.items() if k in W.FINISH_METHODS)
    assert 0.12 < finishes / total < 0.75, methods


def test_i18n_toggle():
    c = _client()
    assert I.t("Camp", "pl") == "Obóz"
    assert I.t("Camp", "en") == "Camp"
    assert I.t("totally missing string", "pl") == "totally missing string"
    r = c.get("/")
    assert ">Camp<" in r.text
    c.get("/lang/pl")
    r = c.get("/")
    assert ">Obóz<" in r.text


def test_ironman_ends_on_loss():
    c = _client()
    _create(c, mode="ironman")
    # force a loss via apply_result
    st = G.load()
    st["world"]["mode"] = "ironman"
    opp = W.pick_opponent(st["world"], st["fighter"])
    ch = G.apply_result(st, {"outcome": "loss", "method": "Unanimous decision", "round": 3,
                             "opp": opp, "stakes": {"purse": 0, "win_bonus": 0}})
    assert st["fighter"]["retired"]
    assert any("Ironman" in ln for ln in ch["lines"])


def test_retired_save_is_reaped():
    c = _client()
    _create(c)
    assert len(G.list_saves()) == 1
    r = c.post("/retire")
    assert str(r.url).endswith("/career")
    # the payoff screen still works while the player is looking at it
    assert c.get("/career").status_code == 200
    assert G.load() is not None
    # ...but once they're back at the menu the retired career's cache is gone
    c.get("/")
    assert G.list_saves() == []
    assert G.load() is None
    assert c.get("/career").status_code == 200  # redirects home, no crash


def test_visitor_isolation(monkeypatch):
    monkeypatch.setattr(G, "TEST_NS", None)   # use real per-cookie namespacing
    a, b = _client(), _client()
    _create(a, name="Alpha One")
    # Alpha's client keeps its cookie and sees the career
    assert "Alpha One" in a.get("/").text
    # a fresh visitor sees nothing
    assert "Alpha One" not in b.get("/").text
    _create(b, name="Bravo Two")
    assert "Bravo Two" in b.get("/").text and "Bravo Two" not in a.get("/").text


def test_static_pages_and_ads(monkeypatch):
    import app.main as M
    c = _client()
    assert c.get("/privacy").status_code == 200
    assert "Privacy Policy" in c.get("/privacy").text
    assert c.get("/about").status_code == 200
    assert c.get("/ads.txt").status_code == 404          # off by default
    monkeypatch.setattr(M, "ADSENSE_CLIENT", "ca-pub-9999999999999999")
    r = c.get("/ads.txt")
    assert r.status_code == 200 and "pub-9999999999999999" in r.text
    assert "googlesyndication.com" in c.get("/").text     # loader injected when configured


def test_nation_flags_render():
    from app import flags as FL
    for code in C.NATION_CODES:
        s = FL.svg(code)
        assert s.startswith("<svg") and "viewBox" in s
    c = _client()
    _create(c, nation="GEO")
    assert G.load()["fighter"]["nation"] == "GEO"
    assert "<svg class=\"flag\"" in c.get("/hub").text


def test_avatar_endpoint():
    c = _client()
    r = c.get("/avatar.svg", params={"skin": "#8d5524", "hair": "mohawk", "beard": "full",
                                     "build": "hulk", "size": "160", "wear": "3"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert r.text.startswith("<svg") and r.text.rstrip().endswith("</svg>")
    assert c.get("/avatar.svg", params={"skin": "javascript:x", "size": "999999"}).status_code == 200


def test_look_persists_and_npcs_have_looks():
    c = _client()
    _create(c, look_skin="#5c3a21", look_hair="corn", look_stance="south")
    st = G.load()
    assert st["fighter"]["look"]["skin"] == "#5c3a21"
    assert st["fighter"]["look"]["stance"] == "south"
    for fr in st["world"]["division"].values():
        assert "look" in fr and fr["look"].get("skin", "").startswith("#")


def test_rating_and_progress_scale():
    f = G.new_state("Prospect", "", 22, "light", "balanced", G.default_attrs())["fighter"]
    assert 25 <= G.rating(f) <= 45          # raw amateur
    assert G.career_progress(f) < 20
    # simulate a top-of-the-mountain fighter
    f["attrs"] = {k: 80 for k in C.ATTRS}
    f["tier"] = C.MAX_TIER
    f["champion"] = True
    f["belts"] = ["Apex (x)", "Global (y)"]
    f["record"] = {"w": 20, "l": 3, "d": 0}
    f["hype"] = 150
    f["win_streak"] = 5
    f["rank"] = 1
    assert 125 <= G.rating(f) <= 165        # "top league ~140"
    assert G.career_progress(f) >= 95


def test_game_plan_and_simulate():
    c = _client()
    _create(c, style="wrestler")
    r = c.post("/plan", data={"plan": "ground"})
    assert G.load()["fighter"]["next_plan"] == "ground"
    for _ in range(6):
        c.post("/train", data={"kind": "wrestling"})
    # simulate the whole fight straight from the weigh-in
    r = c.post("/weighin", data={"go": "sim"})
    assert "result-banner" in r.text, r.url          # ran the whole fight, landed on the result
    c.post("/fight/result/ack")
    assert G.load()["fighter"]["fights"] == 1

    # play the next one but use Simulate round / Simulate to the end
    for _ in range(6):
        c.post("/train", data={"kind": "boxing"})
    c.post("/weighin", data={"go": "play"})
    r = c.get("/fight")
    assert 'action="/fight/sim"' in r.text
    r = c.post("/fight/sim", data={"scope": "round"})
    assert "Corner after round" in r.text or "result-banner" in r.text
    for _ in range(30):
        if "result-banner" in r.text:
            break
        if 'action="/fight/corner"' in r.text:
            r = c.post("/fight/corner", data={"tactic": "pressure"})
        elif 'action="/fight/continue"' in r.text:
            r = c.post("/fight/continue")
        else:
            r = c.post("/fight/sim", data={"scope": "end"})
    assert "result-banner" in r.text
    assert c.post("/fight/result/ack").status_code == 200


def test_more_tiers_and_bigger_division():
    assert len(C.TIERS) == 6
    assert C.DIVISION_SIZE >= 16
    st = G.new_state("D", "", 22, "light", "balanced", G.default_attrs())
    active = [x for x in st["world"]["division"].values() if not x["retired"]]
    assert len(active) == C.DIVISION_SIZE
    assert "midkick" in C.ACTIONS


def test_feedback_and_admin(monkeypatch):
    from app import feedback as FB
    import app.main as M
    from itsdangerous import URLSafeTimedSerializer
    monkeypatch.setattr(M, "ADMIN_KEY", "secret123")
    monkeypatch.setattr(M, "_admin_signer", URLSafeTimedSerializer("secret123", salt="bt-admin"))
    monkeypatch.setattr(FB, "_file", lambda: G.SAVES_DIR / "_feedback.jsonl")

    c = _client()
    _create(c)                                   # gives the visitor a career
    r = c.post("/feedback", data={"text": "Please add southpaw stance switching", "kind": "idea", "page": "/hub"})
    assert '"ok":true' in r.text
    items = FB.all_items()
    assert items and items[0]["text"].startswith("Please add southpaw")
    assert items[0]["kind"] == "idea"

    # admin gated
    assert c.get("/admin").status_code == 404
    assert c.get("/admin/wrong").status_code == 404
    r = c.get("/admin/secret123")                 # sets cookie, redirects to /admin
    assert r.status_code == 200
    assert "Site stats" in r.text and "requests (total)" in r.text
    assert "Today by hour" in r.text
    site = FB.site_stats()
    assert len(site["hours"]) == 24
    assert sum(h["reqs"] for h in site["hours"]) == site["today"]
    assert any(h["visitors"] >= 1 for h in site["hours"])   # this test's own visits landed in some hour
    assert "Please add southpaw" in r.text
    ts = items[0]["ts"]
    c.post(f"/admin/fb/{ts}")
    assert FB.all_items()[0]["resolved"] is True


def test_hall_of_fame_and_legacy():
    f = G.new_state("Legend", "GOAT", 22, "light", "striker", G.default_attrs())["fighter"]
    f["record"] = {"w": 30, "l": 3, "d": 0}
    f["belts"] = ["Apex (x)", "National (y)"]
    f["ko_wins"] = 18
    f["money"] = 500000
    f["records"]["longest_streak"] = 12
    hof = G.hall_of_fame(f)
    assert hof["score"] > 100 and hof["tier"]
    leg = G.build_legacy(f)
    assert leg["bonus_points"] >= 2 and leg["money"] > 0 and "Legend" in leg["mentor"]
