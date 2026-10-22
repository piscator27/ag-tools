#!/usr/bin/env python3
"""
JSON-Generator für Bingo/Quiz zum Thema "Römische Zahlen".

Erzeugt eine Aufgabendatenbank mit einer zufälligen Auswahl von Zahlen aus
einem wählbaren Bereich (z.B. 150 zufällige Zahlen zwischen 1 und 2000):
Frage = arabische Zahl (wird beim Spiel angesagt/gezogen), Antwort = die
zugehörige römische Zahl (steht auf den gedruckten Bingokarten).

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
MIN_ZAHL = 1                    # kleinste Zahl (0 hat kein römisches Symbol, daher ab 1)
MAX_ZAHL = 2000                 # größte Zahl im Auswahlbereich

ANZAHL_ZAHLEN = 150             # wie viele zufällige Zahlen aus [MIN_ZAHL, MAX_ZAHL] gezogen werden
SEED: int | None = 42           # Ganzzahl für reproduzierbare Auswahl, None = jedes Mal neu

KARTENFELD = "antwort"          # "antwort" -> Karten zeigen die römische Zahl, Ansage die arabische
THEMA = "Römische Zahlen"

AUSGABE_DATEI = Path(__file__).resolve().parent / f"roemische_zahlen_{MIN_ZAHL}bis{MAX_ZAHL}_zufall{ANZAHL_ZAHLEN}.json"
TITEL = f"Römische Zahlen {MIN_ZAHL}-{MAX_ZAHL} (Zufallsauswahl)"
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


def niveau_von(zahl: int) -> int:
    """Grober Schwierigkeitsgrad: mehr Stellen/Symbole -> höheres Niveau."""
    if zahl <= 50:
        return 1
    if zahl <= 300:
        return 2
    return 3


def main() -> int:
    if MIN_ZAHL < 1 or MAX_ZAHL < MIN_ZAHL:
        print("FEHLER: MIN_ZAHL/MAX_ZAHL ungültig (MIN_ZAHL >= 1, MAX_ZAHL >= MIN_ZAHL).", file=sys.stderr)
        return 1
    if MAX_ZAHL > 3999:
        print("FEHLER: MAX_ZAHL > 3999 -- klassische römische Zahlen sind nur bis 3999 eindeutig darstellbar.", file=sys.stderr)
        return 1
    groesse_bereich = MAX_ZAHL - MIN_ZAHL + 1
    if ANZAHL_ZAHLEN < 16:
        print("FEHLER: ANZAHL_ZAHLEN < 16 -- für ein 4x4-Raster werden mindestens 16 unterschiedliche Zahlen benötigt.", file=sys.stderr)
        return 1
    if ANZAHL_ZAHLEN > groesse_bereich:
        print(f"FEHLER: ANZAHL_ZAHLEN ({ANZAHL_ZAHLEN}) > verfügbare Zahlen im Bereich ({groesse_bereich}).", file=sys.stderr)
        return 1

    rng = random.Random(SEED)
    gezogene_zahlen = sorted(rng.sample(range(MIN_ZAHL, MAX_ZAHL + 1), ANZAHL_ZAHLEN))

    eintraege = []
    for i, zahl in enumerate(gezogene_zahlen, start=1):
        eintraege.append({
            "id": i,
            "frage": {"typ": "text", "text": str(zahl)},
            "antwort": {"typ": "text", "text": zu_roemisch(zahl)},
            "thema": THEMA,
            "niveau": niveau_von(zahl),
        })

    daten = {
        "meta": {"titel": TITEL, "version": 1, "kartenfeld": KARTENFELD},
        "eintraege": eintraege,
    }
    AUSGABE_DATEI.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")

    distinct_antworten = len({e["antwort"]["text"] for e in eintraege})
    print(f"{len(eintraege)} zufällige Zahlen aus [{MIN_ZAHL}, {MAX_ZAHL}] gezogen, davon {distinct_antworten} unterschiedliche römische Schreibweisen.")
    print(f"Datei geschrieben: {AUSGABE_DATEI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
