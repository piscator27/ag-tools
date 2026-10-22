#!/usr/bin/env python3
"""
JSON-Generator für einfache Bruchrechenaufgaben (+ - * :).

Erzeugt eine Aufgabendatenbank (siehe README.md) mit Bruchrechenaufgaben aus
zwei bereits gekürzten echten Brüchen. Als Divisionszeichen wird ':'
verwendet (nicht '/' oder '\\div'). Ergebnisse werden über Python's
`fractions.Fraction` exakt berechnet und automatisch gekürzt.

Nur Python-Standardbibliothek, kein Server, keine Abhängigkeiten.
"""

from __future__ import annotations

import json
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

# ============================================================================
# KONFIGURATION -- hier direkt anpassen.
# ============================================================================
MIN_NENNER = 2                 # kleinster erlaubter Nenner der Ausgangsbrüche
MAX_NENNER = 12                # größter erlaubter Nenner der Ausgangsbrüche

OPERATIONEN = ["+", "-", "*", ":"]   # welche Rechenarten vorkommen sollen
ANZAHL_AUFGABEN = 60                  # wie viele (unterschiedliche) Aufgaben erzeugt werden

SEED: int | None = 42          # Ganzzahl für reproduzierbare Auswahl, None = jedes Mal neu
KARTENFELD = "antwort"         # "frage" oder "antwort" -- was später auf der Karte steht

AUSGABE_DATEI = Path(__file__).resolve().parent / "bruchrechnen.json"
TITEL = "Bruchrechnen"
# ============================================================================

_OP_LATEX = {"+": "+", "-": "-", "*": r"\cdot", ":": ":"}


def ziehe_echten_bruch(rng: random.Random) -> Fraction:
    """Ein bereits gekürzter echter Bruch (Zähler < Nenner)."""
    while True:
        nenner = rng.randint(MIN_NENNER, MAX_NENNER)
        zaehler = rng.randint(1, nenner - 1)
        if math.gcd(zaehler, nenner) == 1:
            return Fraction(zaehler, nenner)


def bruch_latex(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    vorzeichen = "-" if f.numerator < 0 else ""
    return f"{vorzeichen}\\frac{{{abs(f.numerator)}}}{{{f.denominator}}}"


def niveau_von(op: str, f1: Fraction, f2: Fraction) -> int:
    if op in ("*", ":"):
        return 1
    return 1 if f1.denominator == f2.denominator else 2


def erzeuge_aufgabe(rng: random.Random) -> tuple[Fraction, str, Fraction, Fraction]:
    op = rng.choice(OPERATIONEN)
    f1 = ziehe_echten_bruch(rng)
    f2 = ziehe_echten_bruch(rng)
    if op == "-" and f1 < f2:
        f1, f2 = f2, f1  # Ergebnis soll nicht negativ werden
    if op == "+":
        ergebnis = f1 + f2
    elif op == "-":
        ergebnis = f1 - f2
    elif op == "*":
        ergebnis = f1 * f2
    else:
        ergebnis = f1 / f2
    return f1, op, f2, ergebnis


def erzeuge_eintraege(rng: random.Random) -> list[dict]:
    gesehen: set[tuple[Fraction, str, Fraction]] = set()
    eintraege: list[dict] = []
    versuche = 0
    max_versuche = ANZAHL_AUFGABEN * 50

    while len(eintraege) < ANZAHL_AUFGABEN and versuche < max_versuche:
        versuche += 1
        f1, op, f2, ergebnis = erzeuge_aufgabe(rng)
        schluessel = (f1, op, f2)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)

        eintraege.append({
            "id": len(eintraege) + 1,
            "frage": {"typ": "latex", "text": f"{bruch_latex(f1)} {_OP_LATEX[op]} {bruch_latex(f2)}"},
            "antwort": {"typ": "latex", "text": bruch_latex(ergebnis)},
            "thema": "Bruchrechnung",
            "niveau": niveau_von(op, f1, f2),
        })

    if len(eintraege) < ANZAHL_AUFGABEN:
        print(
            f"Hinweis: Nur {len(eintraege)} von {ANZAHL_AUFGABEN} gewünschten Aufgaben "
            f"gefunden (Nenner-Bereich {MIN_NENNER}-{MAX_NENNER} zu klein für so viele "
            f"unterschiedliche Aufgaben). MAX_NENNER erhöhen oder ANZAHL_AUFGABEN senken.",
            file=sys.stderr,
        )
    return eintraege


def main() -> int:
    if MIN_NENNER < 2 or MAX_NENNER < MIN_NENNER:
        print("FEHLER: MIN_NENNER/MAX_NENNER ungültig (MIN_NENNER >= 2, MAX_NENNER >= MIN_NENNER).", file=sys.stderr)
        return 1
    if not OPERATIONEN:
        print("FEHLER: OPERATIONEN darf nicht leer sein.", file=sys.stderr)
        return 1

    rng = random.Random(SEED)
    eintraege = erzeuge_eintraege(rng)

    daten = {
        "meta": {"titel": TITEL, "version": 1, "kartenfeld": KARTENFELD},
        "eintraege": eintraege,
    }
    AUSGABE_DATEI.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    op_zaehler = Counter(
        next(k for k, v in _OP_LATEX.items() if v == e["frage"]["text"].split()[1])
        for e in eintraege
    )
    distinct_antworten = len({e["antwort"]["text"] for e in eintraege})
    print("Aufgaben pro Rechenart:", dict(op_zaehler))
    print(f"{len(eintraege)} Aufgaben insgesamt, davon {distinct_antworten} unterschiedliche Ergebnisse.")
    print(f"Datei geschrieben: {AUSGABE_DATEI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
