"""Static game data: attributes, tiers, styles, staff, tactics, actions, name pools.

All user-facing strings here are English (the source language). Polish translations
live in app/i18n.py and are looked up by the English string via t()."""

# --- Fighter attributes ------------------------------------------------------

ATTRS = ["power", "striking", "wrestling", "bjj", "cardio", "chin"]

ATTR_LABELS = {
    "power": "Power",
    "striking": "Striking",
    "wrestling": "Wrestling",
    "bjj": "BJJ",
    "cardio": "Cardio",
    "chin": "Chin",
}

ATTR_DESC = {
    "power": "Punching power, knockout chance, strength in the clinch.",
    "striking": "Standup accuracy and defense, footwork.",
    "wrestling": "Takedowns, takedown defense, top control.",
    "bjj": "Submissions, ground game, escapes from bottom.",
    "cardio": "Stamina pool and recovery rate between exchanges.",
    "chin": "Resistance to knockout and damage accumulation.",
}

START_BASE = 30
START_POINTS = 36
START_ATTR_CAP = 55

# --- Weight classes --------------------------------------------------------

WEIGHT_CLASSES = [
    ("bantam", "Bantamweight (61 kg)", 0.92),
    ("feather", "Featherweight (66 kg)", 0.96),
    ("light", "Lightweight (70 kg)", 1.00),
    ("welter", "Welterweight (77 kg)", 1.05),
    ("middle", "Middleweight (84 kg)", 1.10),
    ("lightheavy", "Light Heavyweight (93 kg)", 1.16),
    ("heavy", "Heavyweight (120 kg)", 1.24),
]
WEIGHT_LABELS = {k: label for k, label, _ in WEIGHT_CLASSES}
WEIGHT_KO_MOD = {k: mod for k, _, mod in WEIGHT_CLASSES}

# --- Tiers / organizations ------------------------------------------------

TIERS = [
    {"name": "Amateur circuit", "short": "Amateur", "purse": 0, "win_bonus": 0,
     "opp_base": 32, "defenses_to_promote": 2},
    {"name": "Regional promotion (Fight Night)", "short": "Regional", "purse": 1200,
     "win_bonus": 1500, "opp_base": 42, "defenses_to_promote": 2},
    {"name": "National promotion (Kombat Zone)", "short": "National", "purse": 6000,
     "win_bonus": 9000, "opp_base": 51, "defenses_to_promote": 2},
    {"name": "Continental league (Iron League)", "short": "Continental", "purse": 20000,
     "win_bonus": 30000, "opp_base": 60, "defenses_to_promote": 3},
    {"name": "Global promotion (Titan FC)", "short": "Global", "purse": 65000,
     "win_bonus": 110000, "opp_base": 69, "defenses_to_promote": 3},
    {"name": "Apex MMA - the pinnacle", "short": "Apex", "purse": 200000,
     "win_bonus": 450000, "opp_base": 77, "defenses_to_promote": 99},
]
TITLE_ROUNDS = 5
MAX_TIER = len(TIERS) - 1

# --- Fighting styles (player + opponents) --------------------------------

STYLES = {
    "striker": {
        "label": "Striker",
        "desc": "Kickboxer. Lives at range, sharp combinations, defends the takedown.",
        "mods": {"striking": 8, "power": 5, "cardio": 2, "wrestling": -6, "bjj": -6},
        "ai": {"strike": 0.72, "takedown": 0.06, "clinch": 0.12, "defend": 0.10},
        "passive": {"strike_acc": 0.08, "td_def": 0.10},
    },
    "brawler": {
        "label": "Brawler",
        "desc": "Marches forward swinging for the fences. Iron jaw, poor gas tank.",
        "mods": {"power": 10, "chin": 6, "striking": -3, "cardio": -4, "bjj": -5},
        "ai": {"strike": 0.82, "takedown": 0.03, "clinch": 0.10, "defend": 0.05},
        "passive": {"ko_power": 0.14, "stamina_cost": 0.15},
    },
    "wrestler": {
        "label": "Wrestler",
        "desc": "Wrestling dictates the pace. Takes you down, holds you there, scores from top.",
        "mods": {"wrestling": 12, "power": 4, "cardio": 3, "bjj": -2, "striking": -6},
        "ai": {"strike": 0.30, "takedown": 0.52, "clinch": 0.12, "defend": 0.06},
        "passive": {"td_success": 0.14, "td_def": 0.14},
    },
    "grappler": {
        "label": "Grappler",
        "desc": "Submission hunter. Seeks the ground, finishes with locks and chokes.",
        "mods": {"bjj": 12, "wrestling": 6, "cardio": 2, "power": -5, "striking": -5},
        "ai": {"strike": 0.24, "takedown": 0.50, "clinch": 0.14, "defend": 0.12},
        "passive": {"sub_success": 0.16, "sweep": 0.12},
    },
    "balanced": {
        "label": "Well-rounded (MMA)",
        "desc": "No holes. Good everywhere, elite nowhere, excellent cardio.",
        "mods": {"striking": 3, "wrestling": 3, "cardio": 3},
        "ai": {"strike": 0.52, "takedown": 0.26, "clinch": 0.12, "defend": 0.10},
        "passive": {"all": 0.05, "cardio_regen": 0.15},
    },
}

# --- Appearance --------------------------------------------------------

LOOKS = {
    "skin": [("Light", "#f1c9a5"), ("Tan", "#e0ac7e"), ("Olive", "#c68642"),
             ("Brown", "#8d5524"), ("Dark", "#5c3a21")],
    "hair": [("Short", "short"), ("Buzz cut", "buzz"), ("Mohawk", "mohawk"),
             ("Long", "long"), ("Cornrows", "corn"), ("Bald", "bald")],
    "hair_color": [("Black", "#141414"), ("Dark brown", "#3b2417"), ("Brown", "#6b4423"),
                   ("Blond", "#c99a52"), ("Ginger", "#a5442a"), ("Grey", "#c9c9c9")],
    "beard": [("Stubble", "stubble"), ("Clean-shaven", "none"), ("Moustache", "mustache"),
              ("Goatee", "goatee"), ("Full beard", "full")],
    "build": [("Athletic", "athletic"), ("Wiry", "wiry"), ("Hulking", "hulk")],
    "trunks": [("Red", "#e63946"), ("Navy", "#1d3557"), ("Green", "#2a9d8f"),
               ("Gold", "#e9c46a"), ("Purple", "#6a4c93"), ("Black", "#20232a")],
    "stance": [("Orthodox", "ortho"), ("Southpaw", "south")],
}
LOOK_KEYS = list(LOOKS)
DEFAULT_LOOK = {k: v[0][1] for k, v in LOOKS.items()}


def random_look(rng):
    return {k: rng.choice([code for _, code in opts]) for k, opts in LOOKS.items()}


# --- Coaching staff ---------------------------------------------------

STAFF = {
    "striking": {"label": "Striking coach", "attrs": ["striking", "power"],
                 "desc": "Speeds up boxing and muay thai progress."},
    "grappling": {"label": "Wrestling / BJJ coach", "attrs": ["wrestling", "bjj"],
                  "desc": "Speeds up wrestling and BJJ progress."},
    "strength": {"label": "S&C coach", "attrs": ["power", "cardio", "chin"],
                 "desc": "More power, gas and toughness from camp."},
    "nutrition": {"label": "Nutritionist / physio", "attrs": [],
                  "desc": "Easier weight cut, lower injury risk, faster recovery."},
}
STAFF_MAX_LEVEL = 3
STAFF_COST = [0, 4000, 12000, 30000]
STAFF_GAIN_PER_LEVEL = 0.14

# --- Weight cut -------------------------------------------------------

CUTS = {
    "safe": {"label": "Safe cut", "desc": "You come in fresh, but the opponent may be bigger.",
             "stamina": -4, "risk": 0.0},
    "standard": {"label": "Standard cut", "desc": "The MMA norm. A small tax at the opening bell.",
                 "stamina": -12, "risk": 0.04},
    "hard": {"label": "Hard cut", "desc": "You walk into the cage much bigger, but drained.",
             "stamina": -24, "risk": 0.12, "attr_hit": True},
}

# --- Corner tactics (between rounds) ---------------------------------

TACTICS = {
    "normal": {"label": "Normal", "desc": "No changes."},
    "pressure": {"label": "Pressure", "desc": "March forward. More points for activity, less gas."},
    "counter": {"label": "Counter", "desc": "Wait for the mistake. Bigger counters, weaker own offense."},
    "ground": {"label": "Take it down", "desc": "More takedowns and control, fewer standup exchanges."},
    "conserve": {"label": "Conserve gas", "desc": "Recover faster, but hit lighter."},
}

# Pre-fight game plan set on the hub - seeds the round-1 tactic. Keys match TACTICS.
PLANS = {
    "normal": {"label": "Balanced", "desc": "No bias - read the fight and adapt from the corner."},
    "pressure": {"label": "Pressure & volume", "desc": "March them down and outwork them. Needs a big gas tank."},
    "counter": {"label": "Counter-striker", "desc": "Patient, punish their mistakes. Slow starts, strong finishes."},
    "ground": {"label": "Wrestle & grind", "desc": "Take it to the mat, hold top position, bank the rounds."},
    "conserve": {"label": "Measured pace", "desc": "Pick your spots and keep fuel for the championship rounds."},
}

# --- Training ---------------------------------------------------------

TRAININGS = {
    "boxing": {"label": "Boxing", "primary": "striking", "secondary": "power",
               "desc": "Accuracy, combinations, head movement."},
    "muaythai": {"label": "Muay Thai", "primary": "power", "secondary": "striking",
                 "desc": "Kicks, knees, power in the strikes."},
    "wrestling": {"label": "Wrestling", "primary": "wrestling", "secondary": "power",
                  "desc": "Getting it to the mat and stopping it."},
    "bjj": {"label": "BJJ", "primary": "bjj", "secondary": "wrestling",
            "desc": "Submissions, position control, guard game."},
    "strength": {"label": "Strength & conditioning", "primary": "power", "secondary": "chin",
                 "desc": "Explosive strength and toughness."},
    "cardio": {"label": "Roadwork / cardio", "primary": "cardio", "secondary": "chin",
               "desc": "Gas for a full five rounds."},
    "sparring": {"label": "Hard sparring", "primary": "striking", "secondary": "chin",
                 "desc": "Big progress, but injury risk.", "risk": 0.22},
}
CAMP_SESSIONS = 6

# --- Long-term health ----------------------------------------------

BRAIN_START = 100
BODY_START = 100
BRAIN_HIT_KO = (6, 13)
BRAIN_HIT_TKO = (3, 8)
BRAIN_HEAL_PER_CAMP = 4
BODY_HEAL_PER_CAMP = 7
BRAIN_SUSPEND = 46
BRAIN_RETIRE = 24

# --- Difficulty ----------------------------------------------------

DIFFICULTY = {
    "easy": {"label": "Easy", "opp": -6, "progress": 1.2, "purse": 1.15,
             "desc": "Softer fields, faster gains, bigger purses."},
    "normal": {"label": "Normal", "opp": 0, "progress": 1.0, "purse": 1.0,
               "desc": "The intended challenge."},
    "hard": {"label": "Hard", "opp": 5, "progress": 0.9, "purse": 0.9,
             "desc": "Tougher divisions, slower camps."},
    "realistic": {"label": "Realistic", "opp": 9, "progress": 0.8, "purse": 0.85,
                  "desc": "Brutal. Every fight is a war and mistakes end nights."},
}

# --- Game modes --------------------------------------------------

GAME_MODES = {
    "standard": {"label": "Standard", "desc": "The full career. Retire whenever you choose."},
    "title_run": {"label": "Title or Bust",
                  "desc": "Lose a title fight or your belt and the run is over."},
    "ironman": {"label": "Ironman", "desc": "One loss ends the career. Zero margin for error."},
}

# --- Sponsors --------------------------------------------------

SPONSORS = [
    {"id": "gym", "name": "Iron Den Gym", "min_hype": 0, "per_fight": 400, "cut": 0.0,
     "desc": "Local gym patch on the shorts. Small but steady."},
    {"id": "supp", "name": "RawFuel Supplements", "min_hype": 45, "per_fight": 3000, "cut": 0.05,
     "desc": "Nutrition brand. Wants its logo on your chest (takes 5% of the purse)."},
    {"id": "energy", "name": "VOLT Energy", "min_hype": 100, "per_fight": 11000, "cut": 0.04,
     "desc": "Big energy drink. Media days and appearances required."},
    {"id": "apparel", "name": "APEX Fightwear", "min_hype": 170, "per_fight": 26000, "cut": 0.0,
     "desc": "Flagship apparel deal. You are the face of the brand."},
]

# --- Achievements --------------------------------------------------
# check(f, r) where f = fighter dict, r = last result dict {outcome, method, round, opp, ...}

ACHIEVEMENTS = [
    ("first_win", "First Blood", "Win your first fight."),
    ("ko", "Lights Out", "Win a fight by knockout."),
    ("sub", "Tap or Snap", "Win a fight by submission."),
    ("r1", "Didn't Need the Judges", "Finish a fight in round 1."),
    ("champ", "Gold", "Win a title."),
    ("apex_champ", "Apex Predator", "Hold the Apex MMA belt."),
    ("streak5", "On a Tear", "Win 5 in a row."),
    ("streak10", "Untouchable", "Win 10 in a row."),
    ("flawless", "Perfect Record", "Win a title with zero losses."),
    ("comeback", "Never Say Die", "Win a fight after being badly rocked."),
    ("distance10", "Granite", "Go the distance 10 times in your career."),
    ("veteran", "Old Warhorse", "Reach 25 pro fights."),
    ("millionaire", "Cash Cow", "Earn 500,000 in career purses."),
    ("nemesis", "Nemesis", "Beat the same opponent three times."),
    ("upset", "Giant Killer", "Beat an opponent rated 12+ OVR above you."),
    ("hof", "Hall of Fame", "Retire with two or more titles."),
]

# --- Fight actions -------------------------------------------------

ACTIONS = {
    "jab": {"label": "Jab", "pos": "stand", "kind": "strike",
            "off": "striking", "power": 0.30, "stamina": 4, "base_dmg": 6, "combo": True,
            "desc": "Safe, scores points, low knockout chance."},
    "cross": {"label": "Power punch", "pos": "stand", "kind": "strike",
              "off": "power", "power": 1.0, "stamina": 9, "base_dmg": 13, "risk": 0.18, "combo": True,
              "desc": "Big damage and real KO threat, but you're exposed."},
    "body": {"label": "Body shot", "pos": "stand", "kind": "strike",
             "off": "striking", "power": 0.45, "stamina": 6, "base_dmg": 8, "drain": 7, "combo": True,
             "desc": "Drains the opponent's gas tank."},
    "lowkick": {"label": "Low kick", "pos": "stand", "kind": "strike",
                "off": "striking", "power": 0.4, "stamina": 5, "base_dmg": 7, "drain": 4, "combo": True,
                "desc": "Cheap, wrecks the opponent's mobility."},
    "midkick": {"label": "Body kick", "pos": "stand", "kind": "strike",
                "off": "power", "power": 0.85, "stamina": 9, "base_dmg": 11, "drain": 10, "risk": 0.15, "combo": True,
                "desc": "Thudding kick to the ribs and liver - drains the gas tank and can end nights."},
    "headkick": {"label": "Head kick", "pos": "stand", "kind": "strike",
                 "off": "power", "power": 1.35, "stamina": 13, "base_dmg": 16, "risk": 0.34,
                 "desc": "Highlight-reel KO or flat on your back."},
    "td_stand": {"label": "Shoot a takedown", "pos": "stand", "kind": "takedown",
                 "stamina": 12, "desc": "Depends on wrestling. Success = top position."},
    "clinch_up": {"label": "Close into the clinch", "pos": "stand", "kind": "move",
                  "stamina": 5, "desc": "Tie up against the cage."},
    "defend_stand": {"label": "Defend / circle out", "pos": "stand", "kind": "defend",
                     "stamina": 0, "desc": "Cuts incoming damage, catch your breath."},
    "dirtybox": {"label": "Dirty boxing", "pos": "clinch", "kind": "strike",
                 "off": "striking", "power": 0.5, "stamina": 6, "base_dmg": 8, "combo": True,
                 "desc": "Short punches from close range."},
    "knee": {"label": "Clinch knee", "pos": "clinch", "kind": "strike",
             "off": "power", "power": 1.1, "stamina": 10, "base_dmg": 14, "risk": 0.12,
             "desc": "Very powerful, ends fights."},
    "trip": {"label": "Clinch takedown", "pos": "clinch", "kind": "takedown",
             "stamina": 9, "desc": "Trip or throw from the clinch."},
    "break_clinch": {"label": "Break the clinch", "pos": "clinch", "kind": "move",
                     "stamina": 3, "desc": "Back to striking range."},
    "defend_clinch": {"label": "Defend in the clinch", "pos": "clinch", "kind": "defend",
                      "stamina": 0, "desc": "Underhooks, block the knees."},
    "gnp": {"label": "Ground and pound", "pos": "top", "kind": "strike",
            "off": "power", "power": 0.9, "stamina": 7, "base_dmg": 11, "risk": 0.05, "combo": True,
            "desc": "Rain down punches, TKO threat."},
    "pass_guard": {"label": "Pass the guard", "pos": "top", "kind": "pass",
                   "stamina": 8, "desc": "Better position: stronger G&P and submissions."},
    "submit": {"label": "Go for the submission", "pos": "top", "kind": "submit",
               "stamina": 11, "desc": "Win by submission if it lands."},
    "control": {"label": "Control / stall", "pos": "top", "kind": "control",
                "stamina": 3, "desc": "Drain the opponent's gas, score points."},
    "standup_top": {"label": "Let him up", "pos": "top", "kind": "move",
                    "stamina": 4, "desc": "Return to standing on your terms."},
    "sweep": {"label": "Sweep", "pos": "bottom", "kind": "sweep",
              "stamina": 9, "desc": "Reverse position - you end up on top."},
    "sub_bottom": {"label": "Submission off the back", "pos": "bottom", "kind": "submit",
                   "stamina": 10, "desc": "Triangle, armbar - harder from bottom."},
    "standup_bottom": {"label": "Stand back up", "pos": "bottom", "kind": "escape",
                       "stamina": 8, "desc": "Work back to your feet."},
    "defend_bottom": {"label": "Defend off the back", "pos": "bottom", "kind": "defend",
                      "stamina": 2, "desc": "Cover up, ride out the storm."},
}

POS_LABELS = {
    "stand": "Standing", "clinch": "Clinch",
    "top_player": "Ground - you're on top", "top_opp": "Ground - opponent on top",
}
EXCHANGES_PER_ROUND = 5
COMBO_MAX = 3

# --- World / calendar ------------------------------------------------

DIVISION_SIZE = 16
MONTHS_BETWEEN_FIGHTS = 2
NEWCOMER_AGE = (19, 26)

# --- Name pools ------------------------------------------------------

FIRST_NAMES = [
    "Marcus", "Cody", "Dwight", "Rashad", "Vince", "Andre", "Bo", "Terrell",
    "Jamal", "Kyle", "Dominic", "Sean", "Curtis", "Ivan", "Nate", "Aleksei",
    "Brock", "Diego", "Khalil", "Tyrone", "Owen", "Petr", "Gunnar", "Renato",
    "Hideo", "Bruno", "Malik", "Chase", "Lorenzo", "Deon", "Viktor", "Isaiah",
    "Rory", "Damir",
]
LAST_NAMES = [
    "Kovac", "Ferreira", "Blackwood", "Nakamura", "Okafor", "Vasquez", "Doyle",
    "Petrov", "Hansen", "Silva", "Coleman", "Ruiz", "Antonov", "Mercer",
    "Brennan", "Osei", "Kruger", "Bishop", "Novak", "Wolfe", "Dane", "Cole",
    "Marek", "Voss", "Callahan", "Reyes", "Steele", "Barnes", "Diallo",
    "Larsen", "Munro", "Grant", "Ivarsson", "Kane",
]
NICKNAMES = [
    "The Butcher", "Cyclone", "Golem", "Pitbull", "Hurricane", "Cobra", "Concrete",
    "The Doctor", "Silent", "Hammer", "Wolf", "Torpedo", "The Bear", "Diesel",
    "The Professor", "Tank", "Anaconda", "The Reaper", "Bulldog", "Berserk",
    "The Vulture", "The Bull", "Shark", "Blade", "Buzzsaw", "The Anvil",
    "Freight Train", "Mad Dog",
]
