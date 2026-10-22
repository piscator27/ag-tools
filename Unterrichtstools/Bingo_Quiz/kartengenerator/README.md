# Kartengenerator (`generiere_karten.py`)

Erzeugt aus einer Aufgabendatenbank (JSON, dasselbe Format wie Editor,
Bingo-Spiel und Quiz des Projekts) ein **druckfertiges PDF mit paarweise
verschiedenen Bingokarten** und zusätzlich eine **Kontrollliste als CSV**
(welche Aufgaben-IDs auf welcher Karte stehen).

Das Skript ist Teil des Bingo-Werkzeugsets — siehe `../README.md` für den
Gesamtüberblick und die Beschreibung des JSON-Formats.

---

## Voraussetzungen

- **Python 3** — nur Standardbibliothek, keine Zusatzpakete nötig.
- **LaTeX mit `pdflatex` im PATH** (empfohlen: TeXLive). Genutzte Pakete:
  `babel` (ngerman), `inputenc`, `fontenc`, `geometry`, `tikz`, `pgfplots`,
  `array`, `xcolor`, `graphicx` — in einer vollständigen TeXLive-Installation
  alle enthalten.
  - Linux (Debian/Ubuntu): `sudo apt install texlive-full` (schlanker:
    `texlive-latex-extra texlive-pictures texlive-lang-german`)
  - Windows: [MiKTeX](https://miktex.org/) — fehlende Pakete werden beim
    ersten Gebrauch automatisch nachgefragt
  - macOS: [MacTeX](https://tug.org/mactex/)

Bereitschaft prüfen: `pdflatex --version`

---

## Schnellstart

```bash
# mit den Voreinstellungen oben im Skript
python3 generiere_karten.py

# oder mit explizit angegebener Datenbank und Parametern
python3 generiere_karten.py ../daten/beispiel_einmaleins.json -n 32 -g 4
```

Ausgabe (am Beispiel `beispiel_einmaleins.json`):

| Datei                                        | Inhalt                                             |
| -------------------------------------------- | -------------------------------------------------- |
| `beispiel_einmaleins_karten.pdf`             | die fertigen Karten, **2 Karten pro A4-Seite**, getrennt durch eine gestrichelte Schneidelinie |
| `beispiel_einmaleins_karten_kontrollliste.csv` | Karte → enthaltene Aufgaben-IDs (Spalten `karte_nr`, `id`, `thema`, `inhalt_<feld>`); semikolongetrennt und mit BOM, öffnet sich in deutschem Excel und LibreOffice direkt korrekt |
| `beispiel_einmaleins_karten/`                | Zwischendateien: erzeugtes `karten.tex`, LaTeX-Log, ggf. extrahierte Bilder |

Der LaTeX-Bau läuft einmal durch; nur wenn LaTeX im Log ausdrücklich einen
zweiten Durchlauf anfordert („Rerun"), wird er nachgeholt. Kommen bei großem
Aufgabenpool und wenigen Karten nicht alle Aufgaben vor, meldet das Skript am
Ende, welche IDs auf keiner Karte stehen.

Alle Dateien werden **neben der JSON-Datei** abgelegt (bzw. neben dem mit
`-o` angegebenen Ziel).

---

## Zwei Wege, das Skript zu steuern

**1. Konstanten oben im Skript** (Zeilen ~35–45) — gedacht für den Aufruf
ohne jede Kommandozeile, z. B. per Doppelklick oder `python3
generiere_karten.py`:

| Konstante        | Bedeutung                                                                 |
| ---------------- | -------------------------------------------------------------------------- |
| `JSON_DATEI`     | Pfad zur Aufgabendatenbank. `None` = einzige JSON-Datei in `../daten/` automatisch verwenden |
| `ANZAHL_KARTEN`  | Wie viele Karten erzeugt werden                                            |
| `RASTERGROESSE`  | 3, 4 oder 5 (N×N-Raster)                                                   |
| `SEED`           | Ganzzahl für reproduzierbare Kartensätze, sonst `None`                     |
| `KARTENFELD`     | `"frage"`, `"antwort"` oder `None` (= `meta.kartenfeld` aus der JSON)       |
| `JOKER`          | `"auto"` (Joker nur bei ungerader Rastergröße), `"ja"`, `"nein"`           |
| `AUSGABE_PDF`    | Zieldatei, `None` = automatisch nach der JSON-Datei benannt                |
| `KARTENBREITE_CM`| Breite einer Karte in cm (Voreinstellung 12); die Zellen werden bei größerem Raster entsprechend kleiner |

> `JSON_DATEI = None` (Voreinstellung) heißt: Das Skript sucht die Datenbank
> selbst — und zwar die **einzige** JSON-Datei im Ordner `daten/` neben dem
> Projekt (`../daten/`, unabhängig davon, aus welchem Verzeichnis heraus man
> das Skript startet). Liegt dort keine oder mehr als eine JSON-Datei, bricht
> es mit einer klaren Meldung ab statt zu raten; dann die gewünschte Datei als
> Parameter übergeben oder hier fest eintragen. Ein relativer Pfad in
> `JSON_DATEI` würde dagegen vom aktuellen Arbeitsverzeichnis aus aufgelöst —
> im Zweifel also lieber einen vollständigen Pfad eintragen.

**2. Kommandozeilenparameter** — überschreiben jeweils die Konstante:

```
python3 generiere_karten.py [json_pfad] [Optionen]

  json_pfad                Aufgabendatenbank (Default: JSON_DATEI bzw. Suche in ../daten/)
  -n, --anzahl-karten N    Anzahl Karten
  -g, --groesse {3,4,5}    Rastergröße N×N
      --seed N             Zufalls-Seed für reproduzierbare Sätze
      --kartenfeld {frage,antwort}
                           Welches Feld auf der Karte steht
      --joker {auto,ja,nein}
                           Joker-Mittelfeld
  -o, --ausgabe DATEI      Ausgabe-PDF (fehlt die .pdf-Endung, wird sie ergänzt)
      --nur-pruefen        Nur Plausibilitätsprüfung, kein PDF
  -h, --help               Hilfe anzeigen
```

---

## Was auf der Karte landet

Gedruckt wird **ein** Feld je Eintrag — üblicherweise die `antwort`, während
die Lehrkraft im Spiel die `frage` vorliest. Die Wahl trifft (in dieser
Reihenfolge) `--kartenfeld`, die Konstante `KARTENFELD` oder
`meta.kartenfeld` der JSON-Datei; ohne alles davon: `antwort`.

Unterstützte Feldtypen (`typ` im JSON):

| Typ     | Darstellung auf der Karte                                                       |
| ------- | -------------------------------------------------------------------------------- |
| `text`  | einfacher Text; die Schriftgröße wird automatisch nach Textlänge gestuft         |
| `latex` | Mathe-Satz im LaTeX-Mathemodus (z. B. Brüche)                                   |
| `graph` | Funktionsgraph, mit pgfplots gezeichnet (`term`, `xmin`/`xmax`, `ymin`/`ymax`)   |
| `bild`  | eingebettetes Bild als `data:image/...;base64,...`, wird beim Bau entpackt — möglich sind **PNG, JPEG und PDF**; andere Formate (z. B. SVG) kann `pdflatex` nicht einbinden und werden mit einer klaren Meldung abgelehnt |

Layout: Karten sind konstant **12 cm breit**, unabhängig von der
Rastergröße; die Zellen werden entsprechend kleiner. Bei 5×5 sind die Zellen
für Graph-Achsenbeschriftungen zu klein — dort zeichnet das Skript nur das
Achsenkreuz ohne Zahlen.

**Kopfzeile:** Über jeder Karte steht rechts die laufende Nummer („Karte
Nr. 01") und links der Titel des Kartensatzes aus `meta.titel`, sofern die
Datenbank einen hat — praktisch, sobald mehrere Kartensätze gleichzeitig im
Umlauf sind.

**Joker:** Bei ungerader Rastergröße (3×3, 5×5) wird das Mittelfeld
standardmäßig zum Joker-Feld; entsprechend braucht eine Karte dann ein Feld
weniger aus dem Aufgabenpool. Mit `--joker ja/nein` lässt sich das erzwingen
bzw. abschalten.

---

## Prüfung der Datenbank

Vor dem Kartenbau prüft das Skript die Datenbank und meldet Probleme
verständlich — mit `--nur-pruefen` lässt sich das auch isoliert ausführen,
ohne PDF zu erzeugen.

**Abbruch (Fehler):**
- JSON ohne gültiges `eintraege`-Array oder leer
- Eintrag ohne `id` bzw. mit nicht-ganzzahliger `id` (mit Angabe der Position
  im `eintraege`-Array)
- doppelt vergebene `id`
- Eintrag ohne gültiges `frage`- bzw. `antwort`-Feld
- **zu wenige *unterschiedliche* Werte** im Kartenfeld: entscheidend ist
  nicht die Anzahl der Einträge, sondern die Anzahl verschiedener Werte —
  drei Aufgaben mit der Antwort „24" füllen nur *ein* Kartenfeld, weil
  derselbe Wert nie zweimal auf derselben Karte stehen darf.

**Warnungen (Lauf geht weiter):**
- doppelte Werte im Kartenfeld, mit Angabe der betroffenen IDs
- knapper Pool (weniger als das Doppelte der Feldzahl pro Karte) — die Karten
  ähneln sich dann stark
- Graph-Terme mit nicht unterstützten Zeichen (erlaubt sind Ziffern, `x`,
  `+ - * / ^ ( )` sowie `sin`, `cos`, `sqrt`, `abs`) oder unvollständige/
  vertauschte Wertebereiche

---

## Wie die Karten verteilt werden

1. **Faire Häufigkeiten:** Die insgesamt benötigten Felder
   (`Karten × Felder pro Karte`) werden gleichmäßig auf die unterschiedlichen
   Werte verteilt, der Rest zufällig.
2. **Round-Robin-Füllung:** Diese Häufigkeiten werden reihum auf die Karten
   verteilt, so dass jede Karte exakt voll wird und kein Wert doppelt auf
   einer Karte landet.
3. **Dubletten-Reparatur:** Weil das Verfahren regelmäßig ist, können zufällig
   zwei Karten identisch werden — einzelne Werte werden dann gezielt getauscht,
   bis alle Karten **paarweise verschieden** sind.
4. **ID-Auswahl zuletzt:** Erst wenn feststeht, welche *Werte* auf welcher
   Karte stehen, wird pro Vorkommen eine konkrete Aufgaben-`id` gezogen —
   jeweils die bisher am wenigsten genutzte. So gleicht sich bei mehreren
   Aufgaben mit gleichem Ergebnis die Nutzung über den Kartensatz aus.

Mit `--seed` wird der ganze Vorgang reproduzierbar: derselbe Seed plus
dieselbe Datenbank ergibt denselben Kartensatz.

---

## Wenn etwas schiefgeht

| Meldung / Symptom                                              | Ursache und Abhilfe                                                                 |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| „Zu wenige UNTERSCHIEDLICHE Werte …"                           | Aufgabenpool vergrößern oder Rastergröße verkleinern                                 |
| „Konnte nach 50 Versuchen keinen Satz … erzeugen"              | Pool zu klein für so viele verschiedene Karten — Kartenzahl oder Rastergröße senken   |
| „Keine/Mehrere JSON-Datei(en) in … gefunden"                   | Datenbank als Parameter angeben oder `JSON_DATEI` im Skript setzen                    |
| „'pdflatex' wurde nicht gefunden"                              | LaTeX-Distribution installieren (siehe Voraussetzungen); die Meldung nennt den Befehl je System. `--nur-pruefen` funktioniert auch ohne LaTeX |
| „FEHLER bei pdflatex-Kompilierung"                             | `pdflatex --version` prüfen; der Pfad zum vollständigen Log wird mit ausgegeben        |
| „Bildformat '…' wird von pdflatex nicht unterstützt"            | Bild als PNG, JPEG oder PDF einbetten                                                 |
| „Eintrag ohne gültige ganzzahlige 'id' an Position …"           | Der genannte Eintrag hat keine `id` — im Editor nachtragen                            |
| „Anzahl Karten muss mindestens 1 sein"                          | `-n` bzw. `ANZAHL_KARTEN` auf einen sinnvollen Wert setzen                            |
| Karten sehen sich sehr ähnlich                                 | Warnung zum knappen Pool beachten — mehr Aufgaben ergänzen                            |

Hinweis: `meta.titel` der Datenbank wird gelesen, aber derzeit nicht auf die
Karten gedruckt — die Karten tragen nur ihre laufende Nummer („Karte Nr. 01").
