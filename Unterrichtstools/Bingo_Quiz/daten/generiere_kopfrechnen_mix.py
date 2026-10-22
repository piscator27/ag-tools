#!/usr/bin/env python3
"""
JSON-Generator für ein gemischtes Kopfrechen-Bingo (Klasse 5).

Schwerpunkt kleines Einmaleins plus 11er- und 12er-Reihe, dazu ein paar
andere Rechenarten (Geteilt, Plus/Minus, Verdoppeln/Halbieren) und zwei, drei
Umwandlungen römisch <-> arabisch als Überraschung.

Alle Ergebnisse sind paarweise verschieden: Beim Bingo würde eine zweite
Aufgabe mit demselben Ergebnis sonst ein Feld treffen, das schon angekreuzt
ist, und die Runde zieht sich unnötig.

Nur Python-Standardbibliothek, kein Server, keine Abhängigkeiten.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

# ============================================================================
# KONFIGURATION -- hier direkt anpassen.
# ============================================================================
EINMALEINS_REIHEN = range(3, 10)   # kleines Einmaleins: Faktoren 3..9 (1er/2er/10er sind zu leicht)
ANZAHL_EINMALEINS = 24             # Aufgaben aus dem kleinen Einmaleins
ANZAHL_ELFER = 5                   # 11 · 3..12
ANZAHL_ZWOELFER = 6                # 12 · 3..12
ANZAHL_GETEILT = 5                 # Umkehraufgaben, Ergebnis 11..19, Dividend höchstens 120
ANZAHL_PLUS_MINUS = 6              # zweistellig plus/minus mit Übertrag
ANZAHL_DOPPELT_HALB = 3            # "Das Doppelte von 36", "Die Hälfte von 150"

# Römische Zahlen: Frage -> Antwort. Bei "arabisch -> römisch" steht die
# römische Zahl auf der Bingokarte, das ist der Überraschungseffekt.
ROEMISCH_NACH_ARABISCH = [62]      # Ansage "LXII", Karte zeigt 62
ARABISCH_NACH_ROEMISCH = [49]      # Ansage "49 römisch", Karte zeigt XLIX

SEED: int | None = 2509            # Ganzzahl für reproduzierbare Auswahl, None = jedes Mal neu
KARTENFELD = "antwort"             # Karten zeigen die Ergebnisse, angesagt wird die Aufgabe

AUSGABE_DATEI = Path(__file__).resolve().parent / "kopfrechnen_mix_5.json"
TITEL = "Kopfrechen-Bingo"
# ============================================================================

_WERTE = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def zu_roemisch(zahl: int) -> str:
    ergebnis = []
    for wert, symbol in _WERTE:
        while zahl >= wert:
            ergebnis.append(symbol)
            zahl -= wert
    return "".join(ergebnis)


class Pool:
    """Sammelt Aufgaben und achtet darauf, dass jedes Ergebnis nur einmal vorkommt."""

    def __init__(self) -> None:
        self.eintraege: list[dict] = []
        self.belegt: set[str] = set()

    def frei(self, antwort: str) -> bool:
        return antwort not in self.belegt

    def neu(self, frage: dict, antwort: str, thema: str, niveau: int) -> None:
        self.belegt.add(antwort)
        self.eintraege.append({
            "id": len(self.eintraege) + 1,
            "frage": frage,
            "antwort": {"typ": "text", "text": antwort},
            "thema": thema,
            "niveau": niveau,
        })

    def ziehe(self, kandidaten: list[tuple[dict, str]], anzahl: int,
              thema: str, niveau: int, rng: random.Random) -> None:
        """Zieht `anzahl` Kandidaten (frage, antwort) mit noch freiem Ergebnis."""
        rng.shuffle(kandidaten)
        gezogen = 0
        for frage, antwort in kandidaten:
            if gezogen == anzahl:
                break
            if self.frei(antwort):
                self.neu(frage, antwort, thema, niveau)
                gezogen += 1
        if gezogen < anzahl:
            raise ValueError(f"{thema}: nur {gezogen} von {anzahl} Aufgaben mit freiem Ergebnis gefunden.")


def latex(text: str) -> dict:
    return {"typ": "latex", "text": text}


def text(t: str) -> dict:
    return {"typ": "text", "text": t}


def erzeuge_eintraege(rng: random.Random) -> list[dict]:
    pool = Pool()

    # Römisch zuerst, damit deren Ergebnisse garantiert frei sind.
    for zahl in ROEMISCH_NACH_ARABISCH:
        pool.neu(text(f"{zu_roemisch(zahl)} = ?"), str(zahl), "Römische Zahlen", 2)
    for zahl in ARABISCH_NACH_ROEMISCH:
        pool.neu(text(f"{zahl} als römische Zahl"), zu_roemisch(zahl), "Römische Zahlen", 3)

    einmaleins = []
    for a in EINMALEINS_REIHEN:
        for b in EINMALEINS_REIHEN:
            if a <= b:
                # Faktoren zufällig vertauschen, damit nicht immer der kleinere vorne steht.
                x, y = (b, a) if rng.random() < 0.5 else (a, b)
                einmaleins.append((latex(f"{x} \\cdot {y}"), str(a * b)))
    pool.ziehe(einmaleins, ANZAHL_EINMALEINS, "Einmaleins", 1, rng)

    # 11er/12er nach dem Einmaleins: dort sind nur 26 verschiedene Ergebnisse
    # möglich, die 11er-/12er-Reihe hat dagegen genug Ausweichkandidaten.
    elfer = [(latex(f"11 \\cdot {b}"), str(11 * b)) for b in range(3, 13)]
    pool.ziehe(elfer, ANZAHL_ELFER, "11er-Reihe", 2, rng)

    zwoelfer = [(latex(f"12 \\cdot {b}"), str(12 * b)) for b in range(3, 13)]
    pool.ziehe(zwoelfer, ANZAHL_ZWOELFER, "12er-Reihe", 3, rng)

    geteilt = [(latex(f"{d * q} : {d}"), str(q)) for d in range(3, 10) for q in range(11, 20) if d * q <= 120]
    pool.ziehe(geteilt, ANZAHL_GETEILT, "Geteilt", 2, rng)

    plus_minus = []
    for _ in range(200):
        a, b = rng.randint(25, 69), rng.randint(15, 39)
        if (a % 10) + (b % 10) >= 10:               # nur mit Übertrag
            plus_minus.append((latex(f"{a} + {b}"), str(a + b)))
        c, d = rng.randint(51, 99), rng.randint(15, 48)
        if c % 10 < d % 10:                         # nur mit Zehnerübergang
            plus_minus.append((latex(f"{c} - {d}"), str(c - d)))
    pool.ziehe(plus_minus, ANZAHL_PLUS_MINUS, "Plus/Minus", 2, rng)

    doppelt_halb = (
        [(text(f"das Doppelte von {n}"), str(2 * n)) for n in (35, 45, 38, 47, 36)]
        + [(text(f"die Hälfte von {n}"), str(n // 2)) for n in (130, 150, 170, 190, 114)]
    )
    pool.ziehe(doppelt_halb, ANZAHL_DOPPELT_HALB, "Doppelt/Halb", 2, rng)

    # Nach Thema sortieren und IDs neu vergeben -- nur für die Übersicht im Editor,
    # die Spiel-App mischt ohnehin.
    reihenfolge = ["Einmaleins", "11er-Reihe", "12er-Reihe", "Geteilt",
                   "Plus/Minus", "Doppelt/Halb", "Römische Zahlen"]
    eintraege = sorted(pool.eintraege, key=lambda e: reihenfolge.index(e["thema"]))
    for i, e in enumerate(eintraege, start=1):
        e["id"] = i
    return eintraege


def main() -> int:
    rng = random.Random(SEED)
    try:
        eintraege = erzeuge_eintraege(rng)
    except ValueError as fehler:
        print(f"FEHLER: {fehler}", file=sys.stderr)
        return 1

    daten = {
        "meta": {"titel": TITEL, "version": 1, "kartenfeld": KARTENFELD},
        "eintraege": eintraege,
    }
    AUSGABE_DATEI.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")

    themen: dict[str, int] = {}
    for e in eintraege:
        themen[e["thema"]] = themen.get(e["thema"], 0) + 1
    for thema, anzahl in themen.items():
        print(f"  {thema:<16} {anzahl:>3}")
    print(f"{len(eintraege)} Aufgaben, alle Ergebnisse verschieden.")
    print(f"Datei geschrieben: {AUSGABE_DATEI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
