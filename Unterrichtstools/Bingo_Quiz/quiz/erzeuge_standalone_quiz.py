#!/usr/bin/env python3
"""
Standalone-Generator für die Quiz Show-App.

Bettet eine Aufgabendatenbank (JSON) direkt in eine Kopie von quiz.html ein,
sodass die erzeugte Datei die Datenbank nicht mehr per Datei-Dialog/Drag&Drop
laden muss -- das Quiz startet beim Öffnen sofort mit dem Einstellungen-Panel.
Gedacht für Geräte/Apps, auf denen FileReader bzw. Drag&Drop nicht zuverlässig
funktioniert (z.B. ein Dienst-iPad, auf dem die HTML nur über einen
Code-Editor wie "Koder" statt im Browser geöffnet werden kann).

Gleiches Prinzip wie spiel/erzeuge_standalone_spiel.py beim Bingo-Werkzeugset.
quiz.html selbst bleibt unverändert nutzbar (Datei laden wie gehabt) -- das
Skript hier erzeugt zusätzlich eine zweite, in sich geschlossene HTML-Datei.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ============================================================================
# KONFIGURATION -- hier direkt anpassen, wenn ihr das Skript ohne
# Kommandozeilen-Parameter per "python3 erzeuge_standalone_quiz.py" aufrufen
# wollt. Jeder Wert kann beim Aufruf trotzdem per Parameter überschrieben
# werden (siehe "python3 erzeuge_standalone_quiz.py --help").
# ============================================================================

# Pfad zur Aufgabendatenbank (JSON). None = automatisch die einzige JSON-Datei
# im Ordner "daten/" neben diesem Projekt verwenden (Fehler, falls dort keine
# oder mehrere JSON-Dateien liegen -- dann hier den Pfad konkret eintragen).
JSON_DATEI: str | None = None

AUSGABE_HTML: str | None = None  # Zieldatei, None = automatisch benannt nach der JSON-Datei
# ============================================================================

QUIZ_HTML = Path(__file__).resolve().parent / "quiz.html"
EINFUEGE_MARKER = "<script>\n'use strict';"


def finde_json_automatisch() -> Path:
    # Quiz nutzt dieselbe Datenbank wie Bingo -- daher exakt dieselbe Suche/Fehlermeldung
    # wie in spiel/erzeuge_standalone_spiel.py: die (einzige) JSON-Datei aus daten/.
    daten_ordner = Path(__file__).resolve().parent.parent / "daten"
    kandidaten = sorted(daten_ordner.glob("*.json")) if daten_ordner.is_dir() else []
    if len(kandidaten) == 1:
        return kandidaten[0]
    if len(kandidaten) == 0:
        raise SystemExit(
            f"Keine JSON-Datei in {daten_ordner} gefunden. "
            f"Entweder eine Aufgabendatenbank dorthin legen, oder JSON_DATEI oben im "
            f"Skript setzen, oder den Pfad als Parameter übergeben."
        )
    raise SystemExit(
        f"Mehrere JSON-Dateien in {daten_ordner} gefunden ({', '.join(k.name for k in kandidaten)}). "
        f"Bitte den gewünschten Pfad als Parameter übergeben oder JSON_DATEI oben im Skript setzen."
    )


def lade_datenbank(pfad: Path) -> dict:
    # Exakt dieselbe Prüfung wie in spiel/erzeuge_standalone_spiel.py -- jede gültige
    # Bingo-Datenbank ist automatisch auch eine gültige Quiz-Datenbank. Multiple-Choice-
    # Optionen werden im Quiz zur Laufzeit aus den vorhandenen Antworten erzeugt, nicht
    # in der JSON gespeichert.
    with pfad.open("r", encoding="utf-8") as f:
        daten = json.load(f)
    if "eintraege" not in daten or not isinstance(daten["eintraege"], list) or not daten["eintraege"]:
        raise ValueError("JSON enthält kein gültiges, nicht-leeres 'eintraege'-Array.")
    for e in daten["eintraege"]:
        if "frage" not in e or "antwort" not in e:
            raise ValueError(f"Eintrag mit id={e.get('id')} hat kein gültiges Feld 'frage' oder 'antwort'.")
    return daten


def erzeuge_standalone_html(daten: dict) -> str:
    vorlage = QUIZ_HTML.read_text(encoding="utf-8")
    if EINFUEGE_MARKER not in vorlage:
        raise SystemExit(
            f"quiz.html hat nicht die erwartete Struktur (Marker {EINFUEGE_MARKER!r} nicht gefunden) -- "
            f"Skript muss an die aktuelle quiz.html angepasst werden."
        )
    # </script> darf im JSON-Inhalt nicht vorkommen, sonst würde der Browser
    # das eingebettete <script> vorzeitig beenden.
    daten_json = json.dumps(daten, ensure_ascii=False).replace("</script", "<\\/script")
    einbettung = f"<script>\nwindow.__QUIZ_EINGEBETTETE_DATEN__ = {daten_json};\n</script>\n{EINFUEGE_MARKER}"
    return vorlage.replace(EINFUEGE_MARKER, einbettung, 1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Erzeugt eine eigenständige Quiz-HTML mit eingebetteter Aufgabendatenbank "
                     "(kein Datei-Laden mehr nötig). Ohne Parameter aufgerufen werden die "
                     "Konstanten oben im Skript verwendet."
    )
    parser.add_argument("json_pfad", type=Path, nargs="?", default=None,
                         help="Pfad zur Aufgabendatenbank (Default: Konstante JSON_DATEI bzw. automatische Suche in daten/)")
    parser.add_argument("-o", "--ausgabe", type=Path, default=None,
                         help="Ausgabe-HTML (Default: Konstante AUSGABE_HTML bzw. <json_name>_standalone.html)")
    args = parser.parse_args()

    json_pfad = args.json_pfad or (Path(JSON_DATEI) if JSON_DATEI else None) or finde_json_automatisch()
    ausgabe = args.ausgabe or (Path(AUSGABE_HTML) if AUSGABE_HTML else None) \
        or json_pfad.with_name(json_pfad.stem + "_standalone.html")

    try:
        daten = lade_datenbank(json_pfad)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"FEHLER beim Laden der Datenbank: {exc}", file=sys.stderr)
        return 1

    print(f"Verwende Aufgabendatenbank: {json_pfad} ({len(daten['eintraege'])} Einträge)")

    html = erzeuge_standalone_html(daten)
    ausgabe.write_text(html, encoding="utf-8")

    print(f"Standalone-Quiz erzeugt: {ausgabe}")
    print("Diese Datei enthält die Datenbank fest eingebettet und startet beim Öffnen sofort mit")
    print("dem Einstellungen-Panel -- ideal für Geräte/Apps ohne zuverlässiges Datei-Laden (z.B. iPad-Kodierer).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
