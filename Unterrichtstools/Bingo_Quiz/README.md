# Bingo-Werkzeugset

Ein Werkzeugset, um Aufgabe-Antwort-Paare einmal zu erfassen und daraus
Unterrichtsspiele zu erzeugen — Bingo und ein Kahoot-ähnliches Quiz, später
ggf. weitere Formate (Memory, Domino, Trimino).

**Herzstück ist die JSON-Datei** (die Aufgabendatenbank), nicht die
einzelnen Werkzeuge. **Bingo und Quiz nutzen exakt dieselbe Datenbank** —
jede mit dem Editor erstellte oder per Generator-Skript erzeugte Datei
funktioniert unverändert in beiden Spielen. Das Quiz braucht dafür keine
eigenen Multiple-Choice-Optionen in der JSON: falsche Antwortoptionen werden
beim Start automatisch aus den `antwort`-Werten *anderer* Einträge derselben
Datenbank gezogen (siehe „Quiz-App" weiter unten).

## Projektstruktur

```
Bingo/
├── daten/
│   ├── beispiel_einmaleins.json          Beispieldatenbank (Einmaleins bis 13er-Reihe)
│   ├── beispiel_lineare_funktionen.json  Beispieldatenbank (Funktionsgraphen)
│   ├── generiere_einmaleins.py           Generator: Einmaleins-Aufgaben
│   ├── generiere_bruchrechnen.py         Generator: Bruchrechenaufgaben (+ − · :)
│   └── generiere_bingo_zahlen.py         Generator: klassisches Zahlen-Bingo
├── editor/
│   └── editor.html                JSON-Editor mit Live-Vorschau (Bingo-Datenbanken)
├── kartengenerator/
│   └── generiere_karten.py        Erzeugt Bingokarten-PDFs
├── spiel/
│   ├── spiel.html                    Beamer-Spiel-App (Bingo)
│   └── erzeuge_standalone_spiel.py   Bettet JSON fest in eine Kopie von spiel.html ein
├── quiz/
│   ├── quiz.html                     Beamer-Quiz-App (Kahoot-ähnlich, ohne Schülergeräte)
│   └── erzeuge_standalone_quiz.py    Bettet JSON fest in eine Kopie von quiz.html ein
└── README.md                      diese Datei
```

`editor.html`, `spiel.html` und `quiz.html` sind jeweils vollständig
eigenständige Dateien (KaTeX ist komplett eingebettet) — sie funktionieren
auch, wenn man nur diese eine Datei irgendwohin kopiert, ohne den Rest des
Projektordners.

## Quiz-App (`quiz/quiz.html`)

Kahoot-ähnliches Quiz für den Unterricht, komplett offline, ohne
Schülergeräte: Die Klasse wird in Gruppen eingeteilt und antwortet analog
(Antwortkarte/Whiteboard hochhalten), die Lehrkraft liest ab und trägt die
Antworten im selben Fenster ein (Beamer-Ansicht und Eingabe-Panel teilen
sich den Bildschirm, dafür ausgelegt).

**Nutzt exakt dieselbe JSON-Datenbank wie Bingo** — keine eigene
Quiz-Datenbank, kein separater Editor-Modus nötig. Jede mit `editor.html`
gepflegte oder per Generator-Skript erzeugte Datei funktioniert direkt.

1. `quiz/quiz.html` öffnen, Aufgabendatenbank laden (Button/Drag&Drop) —
   z. B. `daten/beispiel_einmaleins.json`.
2. Im Einstellungen-Panel festlegen:
   - **Fragemodus**: „Multiple-Choice" (Standard) erzeugt beim Start pro
     Aufgabe automatisch 4 Optionen A–D — die richtige Antwort plus 3
     zufällig aus den `antwort`-Werten *anderer* Einträge derselben
     (gefilterten) Datenbank gezogene Distraktoren. Dafür braucht die
     Datenbank mindestens 4 unterschiedliche Antworten, sonst erscheint
     eine Fehlermeldung (analog zur „Zu wenige unterschiedliche Werte"-
     Prüfung des Kartengenerators). „Offene Fragen" — dann wird wie bei
     Bingo nur die Frage gezeigt, die Lehrkraft markiert pro Gruppe
     richtig/falsch, die `antwort` erscheint danach als Lösung. „Gemischt"
     entscheidet pro Aufgabe zufällig zwischen den beiden, mit einem
     einstellbaren Anteil (z. B. 60 % Multiple-Choice, Rest offen).
   - Anzahl Gruppen, Fragenreihenfolge, Timer, Punktesystem.
   - Enthält die Datenbank mehrere unterschiedliche `thema`-Werte, lässt
     sich hier zusätzlich nach Thema filtern.

   Danach „Quiz starten".
3. Bedienung, für schnelle Eingabe während des Unterrichts als
   Tastenkürzel ausgelegt:

   | Taste       | Aktion                                             |
   | ----------- | --------------------------------------------------- |
   | 1–9         | Gruppe auswählen                                     |
   | A/B/C/D     | Antwort der ausgewählten Gruppe setzen (Multiple-Choice), springt automatisch zur nächsten Gruppe |
   | J/N         | Antwort als richtig/falsch markieren (offene Aufgabe), springt automatisch weiter |
   | Enter       | Auswerten (Verteilung zeigen, Punkte vergeben)       |
   | → / Leertaste | Nächste Frage                                      |
   | ←           | Vorherige Frage (Rückblick, nur Anzeige)             |
   | S           | Frage ohne Wertung überspringen                      |
   | Z           | Eingaben der aktuellen Frage zurücksetzen            |
   | T           | Timer starten/pausieren                              |
   | R           | Rangliste ein-/ausblenden (Punkte dort auch manuell korrigierbar) |
   | F           | Vollbild ein/aus                                     |

   Ist der Timer aktiv, bekommt eine Gruppe automatisch einen Tempo-Bonus,
   wenn ihre Antwort eingetragen wird, während noch Restzeit lief — ganz
   ohne zusätzliche Bedienung.

**Standalone-Version ohne Datei-Laden** (z. B. Dienst-iPad mit „Koder"),
exakt analog zu Bingo — inklusive derselben „Mehrere JSON-Dateien gefunden"-
Logik, falls mehr als eine Datei in `daten/` liegt:

```bash
python3 quiz/erzeuge_standalone_quiz.py daten/beispiel_einmaleins.json
# erzeugt: daten/beispiel_einmaleins_standalone.html
```

---

## Installation

### JSON-Editor & Spiel-App (`editor.html`, `spiel.html`)

Keine Installation nötig. Einfach per Doppelklick in einem aktuellen
**Firefox** oder **Chrome** öffnen. Beide laufen komplett offline
(`file://`), laden nichts aus dem Internet und schicken nichts irgendwohin.

### Kartengenerator (`generiere_karten.py`)

Benötigt:

- **Python 3** (nur Standardbibliothek, keine zusätzlichen Pakete nötig)
- **Eine LaTeX-Distribution mit `pdflatex` im PATH**, empfohlen TeXLive.
  Benötigte LaTeX-Pakete: `babel` (ngerman), `inputenc`, `fontenc`,
  `geometry`, `tikz`, `pgfplots`, `array`, `xcolor`, `graphicx`. Bei einer
  vollständigen TeXLive-Installation sind alle bereits dabei.

Installation der LaTeX-Distribution, je nach System:

- **Linux (Debian/Ubuntu):** `sudo apt install texlive-full` (oder schlanker:
  `texlive-latex-extra texlive-pictures texlive-lang-german`)
- **Windows:** [MiKTeX](https://miktex.org/) installieren — fehlende Pakete
  fragt MiKTeX beim ersten Gebrauch automatisch nach
- **macOS:** [MacTeX](https://tug.org/mactex/) installieren

Testen, ob alles bereit ist:

```
pdflatex --version
```

---

## Aufruf

### 1. Aufgabendatenbank automatisch erzeugen — Generator-Skripte (optional)

Für ein paar häufige Themen liegen fertige Python-Skripte in `daten/` bereit,
die eine passende JSON-Datei direkt erzeugen — ohne dass du die Aufgaben von
Hand im Editor eintippen musst. Gleiches Prinzip wie beim Kartengenerator:
alle Einstellungen stehen als Konstanten oben im jeweiligen Skript.

| Skript                      | Erzeugt                                                           | Wichtigste Konstanten                                          |
| --------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------- |
| `generiere_einmaleins.py`   | Einmaleins-Aufgaben (`a · b`) über einen wählbaren Reihen-Bereich | `MIN_REIHE`/`MAX_REIHE`, `SELTENERE_REIHEN`, `SELTENER_ANTEIL` |
| `generiere_bruchrechnen.py` | Bruchrechenaufgaben (`+ − · :`) mit exakt gekürzten Ergebnissen   | `MIN_NENNER`/`MAX_NENNER`, `OPERATIONEN`, `ANZAHL_AUFGABEN`    |
| `generiere_bingo_zahlen.py` | Klassisches Zahlen-Bingo (Frage = Antwort, keine Kopfrechnung)    | `MIN_ZAHL`/`MAX_ZAHL`                                          |

Aufruf, jeweils aus dem Projektordner:

```
python3 daten/generiere_einmaleins.py
python3 daten/generiere_bruchrechnen.py
python3 daten/generiere_bingo_zahlen.py
```

Jedes Skript schreibt seine eigene JSON-Datei nach `daten/` und gibt eine
kurze Zusammenfassung aus (Anzahl Aufgaben, Anzahl unterschiedlicher
Ergebnisse). Die erzeugte Datei lässt sich danach wie jede andere im Editor
öffnen, nachbearbeiten oder direkt an den Kartengenerator übergeben.

Kleine Besonderheiten:

- Bei `generiere_bruchrechnen.py` ist das Divisionszeichen bewusst `:`
  (nicht `/` oder `\div`) — so wie es in der Schule üblich ist.
- Bei `generiere_einmaleins.py` kommen die in `SELTENERE_REIHEN` genannten
  Reihen (Standard: 10er/11er) automatisch seltener vor, weil das Skript für
  sie von vornherein weniger Aufgaben in die Datenbank aufnimmt — sowohl
  Kartengenerator als auch Spiel-App schöpfen gleichmäßig aus dem Pool, ein
  kleinerer Anteil im Pool wirkt sich also direkt auf die Häufigkeit aus.
- Sobald mehrere JSON-Dateien in `daten/` liegen, muss der Kartengenerator
  wissen, welche gemeint ist (siehe „Mehrere JSON-Dateien gefunden" weiter
  unten).

### 2. Aufgaben erfassen oder bearbeiten — JSON-Editor

1. `editor/editor.html` per Doppelklick öffnen.

2. Entweder **„Neue Datenbank"** für einen leeren Start, oder **„Datei
   öffnen"** / eine JSON-Datei ins Fenster ziehen, um eine bestehende
   Datenbank weiterzubearbeiten.

3. Titel, Version und **Kartenfeld** (was später auf den Bingokarten steht —
   Frage oder Antwort) oben festlegen.

4. Links **„+ Neuer Eintrag"**, rechts Thema/Niveau (optional) sowie Frage
   und Antwort ausfüllen. Typ pro Feld wählen:
   
   - **Text** — Klartext
   - **LaTeX** — Mathe-Code ohne `$`-Zeichen, z. B. `\frac{3}{4}+\frac{1}{8}`
   - **Funktionsgraph** — Term (erlaubt: `+ - * / ^`, Klammern, `x`, sowie
     `sin`, `cos`, `sqrt`, `abs`) plus x-/y-Wertebereich
   - **Bild** — Datei auswählen, wird automatisch eingebettet
   
   Die Vorschau darunter zeigt sofort, wie es aussehen wird.

5. Die gelbe/grüne Leiste unter der Kopfzeile zeigt laufend, ob es
   unvollständige Einträge oder doppelte Antwort-/Frage-Werte gibt.

6. **„Speichern (Download)"** lädt die JSON-Datei herunter. Am einfachsten:
   im `daten/`-Ordner ablegen, dann findet der Kartengenerator sie automatisch.

Der Editor warnt vor dem Schließen/Neuladen, wenn noch ungespeicherte
Änderungen offen sind.

### 3. Bingokarten erzeugen — Kartengenerator

Terminal im Projektordner öffnen. Der einfachste Aufruf — nutzt automatisch
die (einzige) JSON-Datei aus `daten/` und alle Standardwerte:

```
python3 kartengenerator/generiere_karten.py
```

Alle Standardwerte stehen als Konstanten **oben in `generiere_karten.py`**
(Abschnitt „KONFIGURATION") und können dort dauerhaft angepasst werden:

| Konstante       | Bedeutung                            | Standard                           |
| --------------- | ------------------------------------ | ---------------------------------- |
| `JSON_DATEI`    | Pfad zur Datenbank                   | automatische Suche in `daten/`     |
| `ANZAHL_KARTEN` | Anzahl zu erzeugender Karten         | `40`                               |
| `RASTERGROESSE` | 3, 4 oder 5 (NxN)                    | `3`                                |
| `SEED`          | Zahl für reproduzierbare Kartensätze | `None` (zufällig)                  |
| `KARTENFELD`    | „frage"/„antwort"/`None`             | aus der JSON übernehmen            |
| `JOKER`         | „auto"/„ja"/„nein"                   | `"auto"` (nur bei ungerader Größe) |
| `AUSGABE_PDF`   | Zieldatei                            | automatisch benannt                |

Für einen einmaligen Testlauf mit anderen Werten, ohne die Datei zu
bearbeiten, gibt es dieselben Einstellungen auch als Parameter:

```
python3 kartengenerator/generiere_karten.py -g 5 -n 25 --seed 42
python3 kartengenerator/generiere_karten.py --nur-pruefen      # nur prüfen, kein PDF
python3 kartengenerator/generiere_karten.py --help              # alle Optionen
```

Ergebnis:

- `<name>_karten.pdf` — die fertigen Bingokarten, 2 pro A4-Seite, nummeriert
- `<name>_kontrollliste.csv` — welche Aufgaben-IDs auf welcher Karte stehen
  (zum Nachprüfen bei „Bingo!", nicht für die Schüler bestimmt)
- ein gleichnamiger Ordner mit den LaTeX-Zwischendateien (u. a. `karten.log`
  zur Fehlersuche, falls `pdflatex` mal scheitert)

### 4. Im Unterricht spielen — Spiel-App

1. `spiel/spiel.html` auf dem Beamer-Rechner per Doppelklick öffnen.

2. JSON-Datei laden (Button oder Drag&Drop).

3. Bedienung:
   
   | Taste                   | Aktion                                  |
   | ----------------------- | --------------------------------------- |
   | → / Leertaste / Bild ab | Nächste Aufgabe                         |
   | ← / Bild auf            | Vorherige Aufgabe                       |
   | Enter                   | Lösung (Karten-Feld) zeigen/verbergen   |
   | F                       | Vollbild ein/aus                        |
   | O                       | Übersicht der bisher gezogenen Aufgaben |
   | Esc                     | Übersicht schließen                     |
   
   Alles auch über die Knöpfe oben erreichbar. **„Felder tauschen"**, falls
   die im Editor festgelegte Kartenfeld-Richtung doch nicht passt.
   **🔔 Ton** und **✨ Blitz** oben rechts schalten den Aufmerksamkeits-Hinweis
   bei jeder neuen Aufgabe ein/aus (Einstellung wird gemerkt).

### 5. Standalone-Version ohne Datei-Laden (z. B. Dienst-iPad)

Auf Geräten, auf denen `spiel.html` nicht im Browser geöffnet werden kann
(z. B. ein Dienst-iPad, auf dem nur ein Code-Editor wie „Koder" zur
Vorschau zur Verfügung steht) funktioniert das Laden der JSON per
Datei-Dialog/Drag&Drop meist nicht zuverlässig. Dafür gibt es
`spiel/erzeuge_standalone_spiel.py`: es bettet eine Aufgabendatenbank fest
in eine Kopie von `spiel.html` ein. Die erzeugte Datei braucht keine
JSON-Datei mehr und startet beim Öffnen sofort mit der ersten Aufgabe.

```bash
python3 spiel/erzeuge_standalone_spiel.py daten/beispiel_einmaleins.json
# erzeugt: daten/beispiel_einmaleins_standalone.html
```

Ohne Parameter verwendet es (wie der Kartengenerator) die einzige JSON-Datei
in `daten/`. Die erzeugte HTML-Datei einfach anstelle von `spiel.html` auf
das iPad übertragen (z. B. per AirDrop/iCloud/USB) und dort mit Koder öffnen
oder ausführen — `spiel.html` selbst bleibt unverändert und lädt JSON-Dateien
weiterhin wie gewohnt.

---

## Typische Fehler

**„FEHLER bei pdflatex-Kompilierung"**
`pdflatex` ist nicht installiert oder nicht im PATH. `pdflatex --version` im
Terminal testen. Im `<name>_karten/`-Ordner liegt `karten.log` mit dem
vollständigen Fehlerprotokoll, falls die Ursache unklar bleibt.

**„Zu wenige unterschiedliche Werte im Feld..."**
Die Datenbank hat zu wenige *unterschiedliche* Frage-/Antwortwerte für die
gewählte Rastergröße (doppelte Werte zählen nur einmal). Mehr Aufgaben
ergänzen oder ein kleineres Raster (`-g 3` statt `-g 5`) wählen.

**„Mehrere JSON-Dateien gefunden"**
Es liegt mehr als eine `.json`-Datei in `daten/`. Entweder die nicht
benötigten woanders hin verschieben, oder `JSON_DATEI` oben im Skript auf
den gewünschten Dateinamen setzen.

**„Zu wenige unterschiedliche Antworten für Multiple-Choice" (Quiz-App)**
Entspricht der „Zu wenige unterschiedliche Werte"-Meldung des Kartengenerators:
die (ggf. nach Thema gefilterte) Datenbank hat weniger als 4 unterschiedliche
`antwort`-Werte, aus denen die Quiz-App Optionen bauen könnte. Weniger Themen
ausschließen, eine größere Datenbank laden, oder im Quiz „Offene Fragen" statt
„Multiple-Choice" wählen.

**„Konnte keinen Satz paarweise verschiedener Karten erzeugen"**
Bei sehr kleiner Datenbank in Kombination mit vielen gewünschten Karten
reicht die Kombinatorik nicht aus. Aufgabenpool vergrößern oder Kartenzahl
senken.

**Ton spielt beim Laden nicht sofort**
Browser verhindern grundsätzlich automatisch startenden Ton ohne
Klick — normal und gewollt. Einmal auf den 🔔-Knopf klicken, danach
funktioniert er bei jeder weiteren Aufgabe.

**Editor/Spiel-App reagieren träge**
Meist durch sehr viele oder sehr große eingebettete Bilder — die werden als
Base64-Text direkt in der JSON gespeichert. Bilder vor dem Einfügen auf eine
vernünftige Größe verkleinern (Bingokarten und Beamer brauchen keine
Fotoauflösung).

**Warnungen zu doppelten Werten ignorieren?**
Bei Rechenaufgaben sind doppelte Ergebnisse (z. B. zwei Aufgaben mit Antwort
„24") normal und kein Fehler — der Kartengenerator sorgt automatisch dafür,
dass nie zwei davon auf derselben Karte landen. Die Warnung ist nur ein
Hinweis, kein Blocker.

---

## Kleines Glossar

- **`meta.kartenfeld`** in der JSON legt fest, welches Feld (Frage oder
  Antwort) auf den gedruckten Karten erscheint. Kartengenerator und Spiel-App
  können das jeweils einzeln überschreiben (`--kartenfeld` bzw. „Felder
  tauschen").
- **Funktionsterm-Syntax** (Feldtyp `graph`): bewusst eingeschränkt auf
  `+ - * / ^`, Klammern, die Variable `x` sowie `sin`, `cos`, `sqrt`, `abs`.
  Dieselbe Syntax wird von Kartengenerator (pgfplots), Editor- und
  Spiel-App-Vorschau (eigener kleiner Parser) verstanden — exotischere Terme
  bitte vermeiden.
- **IDs** werden vom Editor bzw. den Generator-Skripten vergeben (fortlaufend,
  nie wiederverwendet) und sollten nicht von Hand geändert werden — spätere
  Spielvarianten könnten sich einmal stabil auf sie beziehen.

## Bekannte Grenzen

- Die Duplikat-Erkennung vergleicht Feldtyp und Text exakt. Zwei Einträge,
  die dieselbe Zahl einmal als `text` und einmal als `latex` speichern,
  werden aktuell *nicht* als Duplikat erkannt.
- Unterstützt wird der Basis-Sprachumfang von LaTeX-Mathematik, den sowohl
  KaTeX (Browser) als auch `pdflatex` beherrschen. Exotische Pakete/Befehle
  im `latex`-Feldtyp können in einem der beiden Renderer abweichend oder gar
  nicht dargestellt werden.
