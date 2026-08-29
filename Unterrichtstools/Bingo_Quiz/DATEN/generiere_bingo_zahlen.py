#!/usr/bin/env python3
"""
JSON-Generator für klassisches Zahlen-Bingo.

Erzeugt eine Aufgabendatenbank, bei der Frage und Antwort dieselbe Zahl
sind -- für ein ganz normales Bingo-Spiel ohne Kopfrechnen: Die Zahl wird
angesagt/gezogen, die Klasse sucht dieselbe Zahl auf der eigenen Karte.

Nur Python-Standardbibliothek, kein Server, keine Abhängigkeiten.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ============================================================================
# KONFIGURATION -- hier direkt anpassen.
# ============================================================================
MIN_ZAHL = 1                   # kleinste Zahl
MAX_ZAHL = 60                  # größte Zahl (klassisch z.B. 60, 75 oder 90)

KARTENFELD = "antwort"         # "frage" oder "antwort" -- bei gleichen Werten ohne Bedeutung
THEMA = "BINGO"

AUSGABE_DATEI = Path(__file__).resolve().parent / f"bingo_zahlen_{MIN_ZAHL}bis{MAX_ZAHL}.json"
TITEL = f"Zahlen-Bingo {MIN_ZAHL}-{MAX_ZAHL}"
# ============================================================================


def main() -> int:
    if MIN_ZAHL < 1 or MAX_ZAHL < MIN_ZAHL:
        print("FEHLER: MIN_ZAHL/MAX_ZAHL ungültig (MIN_ZAHL >= 1, MAX_ZAHL >= MIN_ZAHL).", file=sys.stderr)
        return 1

    eintraege = []
    for i, zahl in enumerate(range(MIN_ZAHL, MAX_ZAHL + 1), start=1):
        text = str(zahl)
        eintraege.append({
            "id": i,
            "frage": {"typ": "text", "text": text},
            "antwort": {"typ": "text", "text": text},
            "thema": THEMA,
        })

    daten = {
        "meta": {"titel": TITEL, "version": 1, "kartenfeld": KARTENFELD},
        "eintraege": eintraege,
    }
    AUSGABE_DATEI.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(eintraege)} Zahlen ({MIN_ZAHL} bis {MAX_ZAHL}) erzeugt.")
    print(f"Datei geschrieben: {AUSGABE_DATEI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
