# Born to Fight

A web-based MMA career simulator. Build a fighter, run camp and a coaching team, sign a
sponsor, cut weight, then fight **turn-based** (strike combos, corner tactics) and climb a
**living division** of twelve rivals to the top. Retire and coach a protege.

English by default, Polish available (toggle top-right; the fight play-by-play stays English).

## Run

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py
```

http://127.0.0.1:8000

## What's in it

**Fighter**
- 6 attributes (power, striking, wrestling, BJJ, cardio, chin), 36 points to spend
- 5 fighting styles with passive bonuses; appearance (skin/hair/beard/build/trunks/stance)
  as a composed SVG portrait, shown everywhere; veterans pick up scars
- weight class, **difficulty** (Easy - Realistic), **game mode** (Standard / Title or Bust / Ironman)

**Between fights**
- camp: 6 training sessions, progress tapers as attributes rise
- coaching staff (4 coaches x 3 levels) speeds up camp and cuts injury risk
- sponsors: flat fee per fight, some take a cut of the purse; better deals unlock with popularity
- weigh-in: safe / standard / hard weight cut - trade freshness for a size advantage
- contract offers near the end of a deal: stay a star, step up for money, or for exposure

**Fight (turn-based, your calls)**
- 1-3 action combos per exchange (later strikes cost more and land less)
- positions: standing / clinch / ground (top and bottom), each with its own actions
- corner tactics between rounds: pressure, counter, take it down, conserve gas
- coach advice, live judges' cards, "rocked" state, guard pass
- in-fight injuries: cuts (doctor stoppage risk) and leg damage
- endings: KO, TKO, TKO (cut), submission, unanimous / split decision, draw

**Career & world**
- 4 orgs (Amateur -> Regional -> National -> Apex), ranks 1-12 + a belt
- the division lives: rivals fight each other, the ranking shifts, the champ can lose the belt
- rivalries with memory: rematches, head-to-head record, grudge fights that pay more
- long-term health: knockouts damage the brain -> suspensions, forced retirement
- **achievements** (16), **career records**, **fight replays** (last 6), a **Hall of Fame** at retirement
- **legacy / New Game+**: retire and coach a protege with bonuses scaled to your resume
- multiple save slots

## Deploy

See [`deploy/DEPLOY.md`](deploy/DEPLOY.md) for a full walkthrough (Amazon Linux 2023 +
DuckDNS + Let's Encrypt): systemd service, nginx reverse proxy, HTTPS. Each visitor
gets their own careers via a `bt_player` cookie (saves under `saves/<id>/`) - no login.

## Tests

```bash
.venv\Scripts\python -m pytest -q
```

Covers: full-career HTTP walkthroughs across 5 seeds/styles, fight-engine balance,
i18n toggle, Ironman rules, avatar endpoint, Hall of Fame / legacy.

## Layout

| File | Role |
|------|------|
| `app/content.py` | static data: attributes, tiers, styles, staff, tactics, actions, difficulty, modes, sponsors, achievements |
| `app/i18n.py`    | Polish translations for the UI chrome (looked up by English string) |
| `app/world.py`   | living division, rival roster, quick NPC sim, rankings, calendar, offers |
| `app/game.py`    | save slots, character creation, camp + staff + sponsors, weight cut, fight resolution, achievements, Hall of Fame, legacy |
| `app/fight.py`   | turn-based fight engine: combos, tactics, style passives, judges' cards, in-fight injuries |
| `app/avatar.py`  | SVG fighter portrait generator |
| `app/main.py`    | FastAPI routing |
| `templates/`, `static/` | Jinja2 views and styling |

## Roadmap (not done yet)

- Changing weight class mid-career + a pound-for-pound ranking
- Joining a gym / having teammates
- Press conferences and walkouts
