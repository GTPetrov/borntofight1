"""Lightweight i18n. English is the source language; strings are looked up by their
English text. Only UI chrome and static descriptions are translated - the fight
play-by-play and career log stay English in both languages."""

from __future__ import annotations

LANGS = ("en", "pl")
DEFAULT_LANG = "en"

# English source string -> Polish
PL: dict[str, str] = {
    # nav / chrome
    "Camp": "Obóz",
    "Division": "Dywizja",
    "All divisions": "Wszystkie dywizje",
    "Staff": "Sztab",
    "Career": "Kariera",
    "Menu": "Menu",
    "Sponsors": "Sponsorzy",
    "Language": "Język",
    "About": "O grze",
    "Privacy": "Prywatność",
    "Manage deals": "Zarządzaj umowami",
    "Back": "Wstecz",
    "Continue": "Dalej",
    "Play": "Graj",
    "New career": "Nowa kariera",
    # menu / index
    "A career simulator: build a fighter, run camp and a coaching team, cut weight, "
    "fight turn-based - combo by combo - and climb a living division of rivals to the top.":
        "Symulator kariery: stwórz zawodnika, prowadź obóz i sztab, tnij wagę, walcz turowo "
        "- kombinacja po kombinacji - i wspinaj się przez żywą dywizję rywali na sam szczyt.",
    "Saved careers": "Zapisane kariery",
    "Fighter": "Zawodnik",
    "Record": "Rekord",
    "Level": "Poziom",
    "Status": "Status",
    "active": "aktywna",
    "champ": "mistrz",
    "retired": "emerytura",
    "active fighter": "aktywny",
    "How it works": "Jak to działa",
    "Fighter & style": "Zawodnik i styl",
    "Camp, staff, weight": "Obóz, sztab, waga",
    "Turn-based fight": "Walka turowa",
    "Living division": "Żywa dywizja",
    "Rivalries": "Rywalizacje",
    "Health & legacy": "Zdrowie i legacy",
    # creation
    "New fighter": "Nowy zawodnik",
    "Name": "Imię i nazwisko",
    "Nickname": "Ksywa",
    "Age": "Wiek",
    "Weight class": "Kategoria wagowa",
    "Nationality": "Narodowość",
    "Randomize": "Losuj",
    "Appearance": "Wygląd",
    "Skin": "Karnacja",
    "Hair": "Włosy",
    "Hair colour": "Kolor włosów",
    "Beard": "Zarost",
    "Build": "Budowa",
    "Trunks": "Spodenki",
    "Stance": "Postawa",
    "Fighting style": "Styl walki",
    "Attributes": "Atrybuty",
    "Base": "Baza",
    "Difficulty": "Poziom trudności",
    "Game mode": "Tryb gry",
    "Start career": "Rozpocznij karierę",
    "points left": "pozostało pkt",
    "max per attribute": "maks. na atrybut",
    # hub
    "yrs": "lat",
    "Cash": "Kasa",
    "Popularity": "Popularność",
    "Fights": "Walki",
    "Brain health": "Zdrowie mózgu",
    "Body health": "Zdrowie ciała",
    "Contract": "Kontrakt",
    "fights": "walk",
    "Training camp": "Obóz treningowy",
    "Sessions": "Jednostki",
    "injury shortened the camp": "uraz skrócił obóz",
    "medical suspension": "pauza lekarska",
    "Camp complete. Go to the weigh-in.": "Obóz zakończony. Idź na ważenie.",
    "Camp complete.": "Obóz zakończony.",
    "You're ready. Head to the weigh-in.": "Jesteś gotów. Czas na ważenie.",
    "Tale of the tape": "Tale of the tape",
    "Fight details": "Szczegóły walki",
    "Rounds": "Rundy",
    "Date": "Data",
    "Rivalry heat": "Temperatura rywalizacji",
    "Camp log": "Dziennik obozu",
    "injury": "uraz",
    "Coaching staff": "Sztab szkoleniowy",
    "Next fight": "Następna walka",
    "for the title": "o pas",
    "Record / rank": "Rekord / miejsce",
    "Style": "Styl",
    "Estimated chance": "Szacowana szansa",
    "Rivalry": "Rywalizacja",
    "Purse": "Gaża",
    "Go to weigh-in": "Idź na ważenie",
    "End career": "Zakończ karierę",
    "title shot": "walka o pas",
    "CHAMPION": "MISTRZ",
    # staff page
    "Every coach level speeds up the relevant attributes in camp by":
        "Każdy poziom trenera przyspiesza progres odpowiednich atrybutów w obozie o",
    "level": "poziom",
    "Promote for": "Awansuj za",
    "maximum level": "maksymalny poziom",
    "Back to camp": "Wróć do obozu",
    # sponsors
    "Sponsorship deals": "Umowy sponsorskie",
    "A sponsor pays a flat fee every fight; some take a cut of your purse. "
    "Bigger deals unlock as your popularity grows.":
        "Sponsor płaci stałą stawkę za każdą walkę; niektórzy biorą procent gaży. "
        "Więksi odblokowują się wraz z popularnością.",
    "per fight": "za walkę",
    "purse cut": "procent gaży",
    "Current deal": "Obecna umowa",
    "Sign": "Podpisz",
    "Drop sponsor": "Zrezygnuj ze sponsora",
    "No deal": "Brak umowy",
    "Locked - need popularity": "Zablokowane - wymaga popularności",
    # division
    "Champion": "Mistrz",
    "vacant title": "pas wakujący",
    "Form": "Forma",
    # fighter profile
    "Tale of the tape": "Tale of the tape",
    "Your history": "Wasza historia",
    "Estimated chance for you": "Szacowana szansa dla Ciebie",
    # weigh-in
    "Weigh-in": "Ważenie",
    "Fight": "Walka",
    "Weight cut strategy": "Strategia cięcia wagi",
    "starting stamina": "stamina na starcie",
    "temporary attribute drop": "chwilowy spadek atrybutów",
    "To the cage": "Do klatki",
    "Not yet - back to camp": "Jeszcze nie, wróć do obozu",
    # fight
    "cards": "karty",
    "Round": "Runda",
    "exchange": "wymiana",
    "You're rocked": "jesteś zamroczony",
    "Opponent rocked": "rywal zamroczony",
    "guard passed": "przejęta garda",
    "Corner after round": "Narożnik po rundzie",
    "Fight over - decision": "Koniec walki - werdykt",
    "round for": "runda dla",
    "points": "punkty",
    "Tactic for round": "Taktyka na rundę",
    "Verdict": "Werdykt",
    "Your move": "Twój ruch",
    "Game plan": "Plan na walkę",
    "Simulate fight": "Symuluj walkę",
    "Simulate round": "Symuluj rundę",
    "Simulate to the end": "Symuluj do końca",
    "Combo: pick strikes...": "Seria: wybierz ciosy...",
    "Throw the combo": "Wykonaj serię",
    "Clear": "Wyczyść",
    "Single actions": "Pojedyncze akcje",
    "The fight": "Przebieg walki",
    "See result": "Zobacz wynik",
    "even": "remisowa",
    # result
    "WIN": "WYGRANA",
    "LOSS": "PORAŻKA",
    "DRAW": "REMIS",
    "Settlement": "Rozliczenie",
    "Fight purse": "Gaża za walkę",
    "Account": "Konto",
    "What changed": "Co się zmieniło",
    "Rest of the division": "Reszta dywizji",
    "Achievement unlocked": "Nowe osiągnięcie",
    # career
    "KO / Submissions": "KO / Poddania",
    "Career earnings": "Zarobki",
    "Titles": "Pasy",
    "CAREER OVER": "KARIERA ZAKOŃCZONA",
    "Legacy": "Dziedzictwo",
    "Coach a protege": "Poprowadź podopiecznego",
    "Records": "Rekordy",
    "Longest win streak": "Najdłuższa seria zwycięstw",
    "Fastest KO (round)": "Najszybszy nokaut (runda)",
    "Biggest upset (OVR gap)": "Największa niespodzianka (różnica OVR)",
    "Times to the distance": "Walki do dystansu",
    "Achievements": "Osiągnięcia",
    "Hall of Fame": "Galeria Sław",
    "All-time rank": "Miejsce wszech czasów",
    "Fight history": "Historia walk",
    "Chronicle": "Kronika",
    "Replays": "Powtórki",
    "Main menu": "Menu główne",
    "Back to camp ": "Wróć do obozu",
    # offers
    "Contract offers": "Oferty kontraktu",
    "Your current contract is ending. Choose your next move.":
        "Twój obecny kontrakt się kończy. Wybierz następny krok kariery.",
    "Win bonus": "Bonus za wygraną",
    "Fights on the deal": "Walki w umowie",
    "Exposure": "Ekspozycja",
}


def t(s: str, lang: str = DEFAULT_LANG) -> str:
    if lang == "pl":
        return PL.get(s, s)
    return s


def normalize(lang: str | None) -> str:
    return lang if lang in LANGS else DEFAULT_LANG
