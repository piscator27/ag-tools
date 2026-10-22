#!/usr/bin/env python3
"""
JSON-Generator für Einmaleins-Aufgaben.

Erzeugt eine Aufgabendatenbank (siehe README.md) mit allen Einmaleins-
Aufgaben in einem einstellbaren Reihen-Bereich (z.B. 2er- bis 15er-Reihe).
Bestimmte Reihen (z.B. 10er/11er, die meist schon sicher sitzen) können
gezielt seltener vorkommen als die übrigen.

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
MIN_REIHE = 2                # kleinste Einmaleins-Reihe (z.B. 2 = 2er-Reihe)
MAX_REIHE = 15                # größte Einmaleins-Reihe (z.B. 15 = 15er-Reihe)

SELTENERE_REIHEN = [10, 11]   # diese Reihen sollen seltener vorkommen
SELTENER_ANTEIL = 0.35        # Anteil ihrer Aufgaben, der behalten wird (0.0 - 1.0)

SEED: int | None = 42         # Ganzzahl für reproduzierbare Auswahl, None = jedes Mal neu
KARTENFELD = "antwort"        # "frage" oder "antwort" -- was später auf der Karte steht

AUSGABE_DATEI = Path(__file__).resolve().parent / f"einmaleins_{MIN_REIHE}bis{MAX_REIHE}.json"
TITEL = f"Einmaleins {MIN_REIHE}er bis {MAX_REIHE}er Reihe"
# ============================================================================


def niveau_von(a: int, b: int) -> int:
    """Grober Schwierigkeitsgrad anhand des größeren Faktors."""
    hoechster = max(a, b)
    if hoechster <= 5:
        return 1
    if hoechster <= 9:
        return 2
    return 3


def erzeuge_eintraege(rng: random.Random) -> list[dict]:
    # Jede Aufgabe (a,b) mit a<=b nur einmal -- 3*4 und 4*3 sind dieselbe
    # Rechenaufgabe, ein zweites Mal in der Datenbank würde nur unnötig
    # Duplikate erzeugen statt den Aufgabenpool wirklich zu vergrößern.
    alle_paare = [
        (a, b)
        for a in range(MIN_REIHE, MAX_REIHE + 1)
        for b in range(a, MAX_REIHE + 1)
    ]

    normale_paare = [
        (a, b) for (a, b) in alle_paare
        if a not in SELTENERE_REIHEN and b not in SELTENERE_REIHEN
    ]
    seltene_paare = [
        (a, b) for (a, b) in alle_paare
        if a in SELTENERE_REIHEN or b in SELTENERE_REIHEN
    ]

    gemischt = seltene_paare[:]
    rng.shuffle(gemischt)
    anzahl_behalten = round(len(seltene_paare) * SELTENER_ANTEIL)
    behaltene_seltene_paare = gemischt[:anzahl_behalten]

    paare = sorted(normale_paare + behaltene_seltene_paare)

    eintraege = []
    for i, (a, b) in enumerate(paare, start=1):
        eintraege.append({
            "id": i,
            "frage": {"typ": "latex", "text": f"{a} \\cdot {b}"},
            "antwort": {"typ": "text", "text": str(a * b)},
            "thema": "Einmaleins",
            "niveau": niveau_von(a, b),
        })

    print(f"Reguläre Aufgaben: {len(normale_paare)}")
    print(f"Aufgaben aus {SELTENERE_REIHEN}: {len(behaltene_seltene_paare)} von "
          f"{len(seltene_paare)} möglichen behalten ({SELTENER_ANTEIL:.0%}).")
    return eintraege


def main() -> int:
    if MIN_REIHE < 1 or MAX_REIHE < MIN_REIHE:
        print("FEHLER: MIN_REIHE/MAX_REIHE ungültig (MIN_REIHE >= 1, MAX_REIHE >= MIN_REIHE).", file=sys.stderr)
        return 1

    rng = random.Random(SEED)
    eintraege = erzeuge_eintraege(rng)

    daten = {
        "meta": {"titel": TITEL, "version": 1, "kartenfeld": KARTENFELD},
        "eintraege": eintraege,
    }

    AUSGABE_DATEI.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")

    distinct_antworten = len({e["antwort"]["text"] for e in eintraege})
    print(f"\n{len(eintraege)} Aufgaben insgesamt, davon {distinct_antworten} unterschiedliche Ergebnisse.")
    print(f"Datei geschrieben: {AUSGABE_DATEI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
