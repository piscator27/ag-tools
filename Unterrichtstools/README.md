# Unterrichtstools

Sammlung eigenständiger HTML-Apps für den Unterricht — Beamer-tauglich, offline
lauffähig, ohne Build-Prozess. Einstieg über **[index.html](index.html)**.

## Kategorien

- **Klassenzimmer-Werkzeuge** — Arbeitslautstärke, Sanduhr, Namens-Randomizer,
  Gruppenbildung, Beteiligungsmonitor, Klassenrekord, Zahlenrad, Würfelsimulation
- **Spiele & Üben** — Einmaleins (+ Selbsttest), MatheFussball, Hangman,
  Kreuz und Quer, Winkel-Schätzer, Zahlenstrahl-Schätzer
- **Analytische Geometrie** — Skalarprodukt (2D/3D), Winkel Gerade–Ebene,
  Geraden- und Ebenengleichungen
- **Bingo & Quiz** — Bingo-Spiel, Zahlen-Bingo, Quiz-Show, Aufgaben-Editor
  (gemeinsame Aufgabendatenbank, siehe [Bingo_Quiz/README.md](Bingo_Quiz/README.md))

## Klassenlisten (personenbezogene Daten)

Beteiligungsmonitor, Randomizer und Gruppenbildung arbeiten mit Namenslisten.
Diese liegen **nicht** im Repository, sondern je App in einer lokalen Datei:

```
Beteiligungsmonitor/klassen.js
Zufallsauswahl/klassen.js
Gruppenbildung/klassen.js
```

Die Dateien sind über `.gitignore` ausgeschlossen. Fehlt eine davon (z. B. auf
GitHub Pages), greift automatisch die im HTML hinterlegte Beispielklasse.

Aufbau:

```js
window.KLASSEN = {
  "5d": ["Anna", "Ben", "Clara"]
};
```

Der Beteiligungsmonitor nutzt die Array-Form:

```js
window.KLASSEN = [
  { name: "5d", schueler: ["Anna", "Ben", "Clara"] }
];
```

Aus einer CSV-Kursliste erzeugen die Skripte `csv2randomizer.py`,
`csv2gruppenbildung.py` bzw. `csv2beteiligungsmonitor.py` den passenden
Namens-Block. **CSV-Exporte gehören ebenfalls nicht ins Repository** — die
gängigen Muster sind in `.gitignore` bereits abgedeckt.

## Hinweise

- Die Arbeitslautstärke-App braucht Mikrofonzugriff und damit HTTPS
  (GitHub Pages) — lokal per `file://` blockieren Browser das teilweise.
- Bingo, Quiz und Editor laden ihre Aufgaben per `fetch()`. Über einen Webserver
  bzw. GitHub Pages funktioniert das; für den Einsatz per Doppelklick oder auf
  dem iPad erzeugen die `erzeuge_standalone_*.py`-Skripte eigenständige Dateien.
- Neue Apps entstehen nach den Vorgaben in
  [.claude/skills/beamer-html-app/SKILL.md](.claude/skills/beamer-html-app/SKILL.md).
