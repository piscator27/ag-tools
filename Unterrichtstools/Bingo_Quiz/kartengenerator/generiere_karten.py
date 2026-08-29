#!/usr/bin/env python3
"""
Kartengenerator für Unterrichts-Bingo.

Liest eine Aufgabendatenbank (JSON, siehe daten/beispiel_einmaleins.json) und
erzeugt daraus ein druckfertiges PDF mit paarweise verschiedenen Bingokarten
sowie eine Kontrollliste für den Lehrer (Karte -> enthaltene Aufgaben-IDs).

Abhängigkeiten: nur Python-Standardbibliothek. Für den PDF-Bau wird extern
`pdflatex` aufgerufen (muss im PATH liegen).
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import math
import random
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ============================================================================
# KONFIGURATION -- hier direkt anpassen, wenn ihr das Skript ohne
# Kommandozeilen-Parameter per "python3 generiere_karten.py" aufrufen wollt.
# Jeder Wert kann beim Aufruf trotzdem per Parameter überschrieben werden
# (siehe "python3 generiere_karten.py --help") -- die Konstanten hier sind
# nur die Vorgabe, falls der jeweilige Parameter weggelassen wird.
# ============================================================================

# Pfad zur Aufgabendatenbank (JSON). None = automatisch die einzige JSON-Datei
# im Ordner "daten/" neben diesem Projekt verwenden (Fehler, falls dort keine
# oder mehrere JSON-Dateien liegen -- dann hier den Pfad konkret eintragen).
JSON_DATEI: str | None = None
ANZAHL_KARTEN = 32          # Wie viele Bingokarten sollen erzeugt werden?
RASTERGROESSE = 4           # 3, 4 oder 5 (NxN-Raster)
SEED: int | None = None     # Ganzzahl für reproduzierbare Kartensätze, sonst None
KARTENFELD: str | None = None   # "frage", "antwort" oder None (= aus der JSON übernehmen)
JOKER = "auto"               # "auto" (nur bei ungerader Rastergröße), "ja" oder "nein"
AUSGABE_PDF: str | None = None  # Zieldatei, None = automatisch benannt nach der JSON-Datei
KARTENBREITE_CM = 12.0      # Breite einer Karte in cm, unabhängig von der Rastergröße
                            # (die einzelnen Zellen werden bei größerem Raster kleiner)
# ============================================================================


# ---------------------------------------------------------------------------
# Datenbank laden
# ---------------------------------------------------------------------------

def lade_datenbank(pfad: Path) -> dict:
    with pfad.open("r", encoding="utf-8") as f:
        daten = json.load(f)
    if "eintraege" not in daten or not isinstance(daten["eintraege"], list):
        raise ValueError("JSON enthält kein gültiges 'eintraege'-Array.")
    if not daten["eintraege"]:
        raise ValueError("Die Aufgabendatenbank enthält keine Einträge.")
    ohne_id = [i for i, e in enumerate(daten["eintraege"], start=1)
               if not isinstance(e, dict) or not isinstance(e.get("id"), int) or isinstance(e.get("id"), bool)]
    if ohne_id:
        stellen = ", ".join(str(i) for i in ohne_id[:10])
        weitere = f" (und {len(ohne_id) - 10} weitere)" if len(ohne_id) > 10 else ""
        raise ValueError(
            f"Eintrag ohne gültige ganzzahlige 'id' an Position {stellen}{weitere} "
            f"(gezählt ab 1 im 'eintraege'-Array). Jeder Eintrag braucht eine eindeutige "
            f"ganzzahlige id -- der Editor vergibt sie automatisch."
        )
    ids = [e["id"] for e in daten["eintraege"]]
    if len(ids) != len(set(ids)):
        doppelte = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"Doppelt vergebene IDs in der Datenbank: {doppelte}")
    for e in daten["eintraege"]:
        for feldname in ("frage", "antwort"):
            if feldname not in e or "typ" not in e[feldname]:
                raise ValueError(f"Eintrag mit id={e.get('id')} hat kein gültiges Feld '{feldname}'.")
    return daten


# ---------------------------------------------------------------------------
# Plausibilitätsprüfung
# ---------------------------------------------------------------------------

def feld_schluessel(feld: dict) -> tuple:
    """Normalisierter, hashbarer Schlüssel für 'inhaltlich gleiche' Feldwerte."""
    typ = feld.get("typ")
    if typ in ("text", "latex"):
        return (typ, feld.get("text", "").strip())
    if typ == "graph":
        return (typ, feld.get("term", "").strip(), feld.get("xmin"), feld.get("xmax"))
    if typ == "bild":
        return (typ, feld.get("daten", ""))
    return (typ, json.dumps(feld, sort_keys=True))


ERLAUBTE_GRAPH_ZEICHEN = re.compile(r"^[0-9x+\-*/^().\s a-z]*$", re.IGNORECASE)
ERLAUBTE_GRAPH_FUNKTIONEN = ("sin", "cos", "sqrt", "abs")


def pruefe_graph_terme(eintraege: list[dict]) -> list[str]:
    warnungen = []
    for e in eintraege:
        for feldname in ("frage", "antwort"):
            feld = e[feldname]
            if feld.get("typ") != "graph":
                continue
            term = feld.get("term", "")
            rest = term
            for fn in ERLAUBTE_GRAPH_FUNKTIONEN:
                rest = rest.replace(fn, "")
            if not ERLAUBTE_GRAPH_ZEICHEN.match(rest):
                warnungen.append(
                    f"id={e['id']}: Funktionsterm {term!r} enthält Zeichen außerhalb des "
                    f"unterstützten Vorrats (Ziffern, x, + - * / ^ ( ), {', '.join(ERLAUBTE_GRAPH_FUNKTIONEN)})."
                )
            xmin, xmax = feld.get("xmin"), feld.get("xmax")
            ymin, ymax = feld.get("ymin"), feld.get("ymax")
            if None in (xmin, xmax, ymin, ymax):
                warnungen.append(f"id={e['id']}: Graph-Feld ohne vollständige xmin/xmax/ymin/ymax-Angabe.")
            elif xmin >= xmax or ymin >= ymax:
                warnungen.append(f"id={e['id']}: Graph-Wertebereich ungültig (xmin/xmax bzw. ymin/ymax vertauscht).")
    return warnungen


def pruefe_plausibilitaet(
    eintraege: list[dict], kartenfeld: str, benoetigte_felder: int, anzahl_karten: int
) -> tuple[list[str], dict[tuple, list[int]]]:
    """
    Prüft die Datenbank in Bezug auf das Feld, das tatsächlich auf der Karte
    landet (kartenfeld). Gibt Warnungen sowie eine Wertschlüssel->IDs-Zuordnung
    zurück. Löst ValueError aus, wenn der Pool an UNTERSCHIEDLICHEN Werten zu
    klein ist, um eine Karte zu füllen (nicht die reine Anzahl an Einträgen
    zählt, sondern die Anzahl unterschiedlicher Werte -- doppelte Antworten
    verkleinern den nutzbaren Pool faktisch).
    """
    warnungen = []
    werte_zu_ids: dict[tuple, list[int]] = defaultdict(list)

    for e in eintraege:
        schluessel = feld_schluessel(e[kartenfeld])
        werte_zu_ids[schluessel].append(e["id"])

    duplikate = {w: ids for w, ids in werte_zu_ids.items() if len(ids) > 1}
    for w, ids in sorted(duplikate.items(), key=lambda kv: kv[1]):
        anzeige = w[1] if len(w) > 1 else w
        warnungen.append(f"Doppelter Wert im Feld '{kartenfeld}' bei IDs {ids}: {anzeige!r}")

    distinct_anzahl = len(werte_zu_ids)
    if distinct_anzahl < benoetigte_felder:
        raise ValueError(
            f"Zu wenige UNTERSCHIEDLICHE Werte im Feld '{kartenfeld}': {distinct_anzahl} vorhanden, "
            f"aber {benoetigte_felder} pro Karte nötig (doppelte Werte zählen dabei nur einmal). "
            f"Aufgabenpool vergrößern oder Rastergröße verkleinern."
        )
    if distinct_anzahl < 2 * benoetigte_felder:
        warnungen.append(
            f"Aufgabenpool ist mit {distinct_anzahl} unterschiedlichen Werten eher knapp für "
            f"{benoetigte_felder} Felder pro Karte -- die {anzahl_karten} Karten werden sich stark ähneln."
        )

    warnungen.extend(pruefe_graph_terme(eintraege))
    return warnungen, dict(werte_zu_ids)


# ---------------------------------------------------------------------------
# Kartenverteilung
# ---------------------------------------------------------------------------

def _runde_robin_fuellen(
    werte: list[tuple], zaehler: dict[tuple, int], anzahl_karten: int, benoetigte_felder: int, rng
) -> list[list[tuple]] | None:
    """
    Füllt `anzahl_karten` Karten mit je `benoetigte_felder` Werten, so dass
    jeder Wert genau `zaehler[wert]`-mal im gesamten Kartensatz vorkommt und
    nie zweimal auf derselben Karte landet. Funktioniert immer (liefert nie
    None), solange kein Wert öfter vorkommen soll, als es Karten gibt --
    das ist durch die Poolgrößen-Prüfung vorher sichergestellt.
    """
    reihenfolge = werte[:]
    rng.shuffle(reihenfolge)
    reihenfolge.sort(key=lambda w: -zaehler[w])  # häufigste Werte zuerst verteilen

    karten: list[list[tuple]] = [[] for _ in range(anzahl_karten)]
    belegt: list[set] = [set() for _ in range(anzahl_karten)]
    zeiger = rng.randrange(anzahl_karten)
    for w in reihenfolge:
        for _ in range(zaehler[w]):
            versuche = 0
            while (w in belegt[zeiger] or len(karten[zeiger]) >= benoetigte_felder) and versuche < anzahl_karten:
                zeiger = (zeiger + 1) % anzahl_karten
                versuche += 1
            if versuche >= anzahl_karten:
                return None  # sollte bei korrekter Poolgrößen-Prüfung nicht vorkommen
            karten[zeiger].append(w)
            belegt[zeiger].add(w)
            zeiger = (zeiger + 1) % anzahl_karten
    return karten


def _kartendubletten_reparieren(
    karten: list[list[tuple]], alle_werte: list[tuple], rng, max_versuche: int = 5000
) -> list[list[tuple]] | None:
    """
    Das Runde-Robin-Verfahren füllt zwar jede Karte korrekt, kann aber durch
    seine Regelmäßigkeit zufällig zwei identische Kartenwertmengen erzeugen.
    Diese Funktion tauscht in einer betroffenen Karte einzelne Werte gegen
    Werte aus, die sie noch nicht enthält, bis alle Karten paarweise
    verschieden sind. Gibt None zurück, wenn das nicht gelingt (dann wird im
    Aufrufer mit neuer Durchmischung neu versucht).
    """
    anzahl_karten = len(karten)
    for _ in range(max_versuche):
        mengen = [frozenset(k) for k in karten]
        dup_index = None
        for i in range(anzahl_karten):
            for j in range(i):
                if mengen[i] == mengen[j]:
                    dup_index = i
                    break
            if dup_index is not None:
                break
        if dup_index is None:
            return karten

        nutzung = Counter(w for karte in karten for w in karte)
        karte = karten[dup_index]
        positionen = list(range(len(karte)))
        rng.shuffle(positionen)
        repariert = False
        for pos in positionen:
            kandidaten = [w for w in alle_werte if w not in karte]
            # am wenigsten genutzte Werte zuerst probieren, damit Reparaturen
            # die Gesamtverteilung nicht schiefziehen
            kandidaten.sort(key=lambda w: (nutzung[w], rng.random()))
            for ersatz in kandidaten:
                neue_karte = karte[:pos] + [ersatz] + karte[pos + 1:]
                neue_menge = frozenset(neue_karte)
                if all(neue_menge != mengen[j] for j in range(anzahl_karten) if j != dup_index):
                    karten[dup_index] = neue_karte
                    repariert = True
                    break
            if repariert:
                break
        if not repariert:
            return None
    return None


def erzeuge_kartensatz(
    werte_zu_ids: dict[tuple, list[int]],
    benoetigte_felder: int,
    anzahl_karten: int,
    rng,
    max_versuche: int = 50,
) -> list[list[int]]:
    """
    Verteilt Aufgaben auf `anzahl_karten` Karten mit je `benoetigte_felder`
    Feldern.

    Wichtig: Die Fairness-Verteilung läuft auf Ebene der WERTE, nicht der
    IDs. Ein Wert (z.B. das Ergebnis "24") darf pro Karte höchstens einmal
    vorkommen, unabhängig davon, wie viele verschiedene Aufgaben-IDs zu
    diesem Wert führen -- sonst könnte dieselbe Zahl zweimal auf einer Karte
    stehen. Erst nachdem feststeht, WELCHE Werte auf welcher Karte landen,
    wird für jedes Wert-Vorkommen eine konkrete ID ausgewählt (wieder
    Least-Used-First, damit sich bei Dubletten-Clustern wie 4/7/10="24" die
    Nutzung der einzelnen IDs über den Kartensatz ausgleicht).

    Verfahren:
    1. Jeder Wert bekommt eine faire Häufigkeit zugewiesen (Gesamtzahl
       benötigter Felder gleichmäßig auf die unterschiedlichen Werte
       verteilt, Rest zufällig verteilt).
    2. Ein Round-Robin-Verfahren (_runde_robin_fuellen) verteilt diese
       Häufigkeiten so auf die Karten, dass jede Karte exakt voll wird und
       nie ein Wert doppelt auf einer Karte landet -- das gelingt garantiert.
    3. Da das Verfahren regelmäßig ist, können zufällig zwei Karten identisch
       werden; _kartendubletten_reparieren behebt das durch gezielte Tausche.
    """
    werte = list(werte_zu_ids.keys())
    n = len(werte)
    gesamt = benoetigte_felder * anzahl_karten
    basis, rest = divmod(gesamt, n)

    for versuch in range(max_versuche):
        werte_fuer_rest = werte[:]
        rng.shuffle(werte_fuer_rest)
        extra_werte = set(werte_fuer_rest[:rest])
        zaehler = {w: basis + (1 if w in extra_werte else 0) for w in werte}

        karten_werte = _runde_robin_fuellen(werte, zaehler, anzahl_karten, benoetigte_felder, rng)
        if karten_werte is None:
            continue
        karten_werte = _kartendubletten_reparieren(karten_werte, werte, rng)
        if karten_werte is None:
            continue

        id_nutzung: dict[int, int] = defaultdict(int)
        karten_ids: list[list[int]] = []
        for karte in karten_werte:
            ids_karte = []
            for w in karte:
                kandidaten = werte_zu_ids[w]
                min_nutzung = min(id_nutzung[eid] for eid in kandidaten)
                am_wenigsten_genutzt = [eid for eid in kandidaten if id_nutzung[eid] == min_nutzung]
                gewaehlt = rng.choice(am_wenigsten_genutzt)
                id_nutzung[gewaehlt] += 1
                ids_karte.append(gewaehlt)
            karten_ids.append(ids_karte)
        return karten_ids

    raise RuntimeError(
        f"Konnte nach {max_versuche} Versuchen keinen Satz von {anzahl_karten} paarweise "
        f"verschiedenen Karten erzeugen. Aufgabenpool vergrößern oder Kartenzahl/Rastergröße senken."
    )


# ---------------------------------------------------------------------------
# LaTeX-Rendering
# ---------------------------------------------------------------------------

_LATEX_ERSETZUNGEN = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_LATEX_MUSTER = re.compile("|".join(re.escape(z) for z in _LATEX_ERSETZUNGEN))


def latex_escape(text: str) -> str:
    return _LATEX_MUSTER.sub(lambda m: _LATEX_ERSETZUNGEN[m.group()], text)


# Formate, die pdflatex per \includegraphics direkt einbinden kann. SVG gehört
# ausdrücklich NICHT dazu -- ohne diese Prüfung landet eine Datei namens
# "bild_3_antwort.svg+xml" im Build-Ordner und LaTeX bricht mit einer
# kryptischen Meldung ab, statt das eigentliche Problem zu benennen.
UNTERSTUETZTE_BILDFORMATE = {"png": "png", "jpg": "jpg", "jpeg": "jpg", "pdf": "pdf"}


def bild_datei_schreiben(daten_uri: str, verzeichnis: Path, basisname: str) -> Path:
    m = re.match(r"^data:image/(?P<ext>[a-zA-Z0-9.+-]+);base64,(?P<daten>.+)$", daten_uri, re.DOTALL)
    if not m:
        raise ValueError(f"Ungültige Bilddaten (erwarte data:image/...;base64,...) bei {basisname}.")
    roh_ext = m.group("ext").lower()
    if roh_ext not in UNTERSTUETZTE_BILDFORMATE:
        erlaubt = ", ".join(sorted(set(UNTERSTUETZTE_BILDFORMATE)))
        raise ValueError(
            f"Bildformat '{roh_ext}' bei {basisname} wird von pdflatex nicht unterstützt "
            f"(möglich sind: {erlaubt}). Das Bild bitte vorher umwandeln, z.B. als PNG."
        )
    ext = UNTERSTUETZTE_BILDFORMATE[roh_ext]
    pfad = verzeichnis / f"{basisname}.{ext}"
    pfad.write_bytes(base64.b64decode(m.group("daten")))
    return pfad


def _schriftgroesse_befehl(text: str) -> str:
    """
    Wählt eine LaTeX-Schriftgrößen anhand der Textlänge. Bewusst KEIN
    \\resizebox auf Textinhalt verwendet: das verrechnet sich in
    Tabellenzeilen gelegentlich mit der Zeilenhöhe und schneidet die oberste
    Zeile einer Karte optisch an (in Tests bei 5x5-Karten beobachtet).
    Normale Schriftgrößenbefehle haben dagegen korrekte Boxmetriken.
    """
    n = len(text)
    if n <= 2:
        return r"\Huge"
    if n <= 4:
        return r"\huge"
    if n <= 7:
        return r"\LARGE"
    if n <= 12:
        return r"\Large"
    return r"\large"


def schoene_schrittweite(spanne: float, ziel_anzahl: float = 5) -> float:
    """
    Wählt eine "schöne" Achsenbeschriftungs-Schrittweite (1/2/5 * 10^n) für
    eine gegebene Wertebereichs-Spanne, sodass ungefähr `ziel_anzahl`
    Beschriftungen entstehen -- z.B. Schritt 2 bei Spanne 10 (Werte
    2, 4, 6, 8, ...). Dieselbe Logik existiert unabhängig auch in JS
    (Spiel-App und Editor-Vorschau), damit alle drei Renderer dieselben
    Achsenbeschriftungen zeigen.
    """
    if spanne <= 0:
        return 1.0
    roh = spanne / ziel_anzahl
    exponent = math.floor(math.log10(roh))
    basis = roh / (10 ** exponent)
    if basis < 1.5:
        nett = 1
    elif basis < 3:
        nett = 2
    elif basis < 7:
        nett = 5
    else:
        nett = 10
    return nett * (10 ** exponent)


def render_zelle(eintrag: dict, feldname: str, bild_verzeichnis: Path, zellengroesse_cm: float) -> str:
    feld = eintrag[feldname]
    typ = feld["typ"]
    bildgroesse = max(zellengroesse_cm - 0.3, 0.8)
    if typ == "text":
        return _schriftgroesse_befehl(feld["text"]) + " " + latex_escape(feld["text"])
    if typ == "latex":
        return _schriftgroesse_befehl(feld["text"]) + " $" + feld["text"] + "$"
    if typ == "graph":
        if zellengroesse_cm < 2.7:
            # Bei sehr kleinen Zellen (5x5-Raster) überlappen sich selbst die
            # reduzierten Randbeschriftungen -- dort lieber ganz ohne Zahlen
            # (nur Achsenkreuz), das bleibt wenigstens lesbar.
            tick_optionen = "ticks=none,"
        else:
            # Weniger Zielbeschriftungen als am Bildschirm (JS-Renderer nutzt
            # 5) -- die kleine Kartenzelle verträgt sonst zu viele Zahlen nahe
            # am Ursprung.
            x_schritt = schoene_schrittweite(feld["xmax"] - feld["xmin"], ziel_anzahl=3)
            y_schritt = schoene_schrittweite(feld["ymax"] - feld["ymin"], ziel_anzahl=3)
            tick_optionen = (
                f"xtick distance={x_schritt:g},ytick distance={y_schritt:g},"
                r"tick label style={font=\tiny},tick align=outside,"
            )
        return (
            r"\begin{tikzpicture}"
            rf"\begin{{axis}}[width={bildgroesse}cm,height={bildgroesse}cm,"
            f"xmin={feld['xmin']},xmax={feld['xmax']},ymin={feld['ymin']},ymax={feld['ymax']},"
            f"{tick_optionen}"
            r"axis lines=middle,axis line style={draw=gray},clip=true]"
            f"\\addplot[domain={feld['xmin']}:{feld['xmax']},samples=80,thick] {{{feld['term']}}};"
            r"\end{axis}\end{tikzpicture}"
        )
    if typ == "bild":
        pfad = bild_datei_schreiben(feld["daten"], bild_verzeichnis, f"bild_{eintrag['id']}_{feldname}")
        return rf"\includegraphics[width=0.85\linewidth,height={bildgroesse}cm,keepaspectratio]{{{pfad.as_posix()}}}"
    raise ValueError(f"Unbekannter Feldtyp: {typ}")


def render_karte(
    karten_ids: list[int],
    eintraege_by_id: dict[int, dict],
    feldname: str,
    groesse: int,
    joker: bool,
    nummer: int,
    bild_verzeichnis: Path,
    rng,
    titel: str = "",
) -> str:
    anzahl_zellen = groesse * groesse
    mitte = anzahl_zellen // 2 if joker else None
    zellengroesse_cm = KARTENBREITE_CM / groesse

    reihenfolge = karten_ids[:]
    rng.shuffle(reihenfolge)

    positionen_inhalt: list[str] = [""] * anzahl_zellen
    positionen_typ: list[str | None] = [None] * anzahl_zellen
    idx_frei = 0
    for pos in range(anzahl_zellen):
        if joker and pos == mitte:
            positionen_inhalt[pos] = r"\bfseries JOKER"
        else:
            eid = reihenfolge[idx_frei]
            idx_frei += 1
            eintrag = eintraege_by_id[eid]
            positionen_inhalt[pos] = render_zelle(eintrag, feldname, bild_verzeichnis, zellengroesse_cm)
            positionen_typ[pos] = eintrag[feldname]["typ"]

    # \Tstrut in einer Zeile auslassen, wenn IRGENDEINE Spalte dieser Zeile
    # direkt über einem Bild steht: \Tstrut + \includegraphics in der Zelle
    # darunter erzeugt sonst eine störende Geisterlinie (bekannter LaTeX/
    # array-Effekt, empirisch gefunden). Die Entscheidung gilt pro ganzer
    # Zeile (nicht nur pro Zelle), weil unterschiedliche Struts innerhalb
    # derselben Zeile sonst ihrerseits zu einer fragmentierten Trennlinie
    # führen -- ebenfalls empirisch gefunden.
    zeilen_ohne_tstrut: set[int] = set()
    for pos in range(anzahl_zellen):
        darunter = pos + groesse
        if darunter < anzahl_zellen and positionen_typ[darunter] == "bild":
            zeilen_ohne_tstrut.add(pos // groesse)

    zellen: list[str] = []
    for pos in range(anzahl_zellen):
        tstrut = "" if (pos // groesse) in zeilen_ohne_tstrut else r"\Tstrut "
        zellen.append(tstrut + positionen_inhalt[pos] + r"\Bstrut")

    spalten = "|" + f"p{{{zellengroesse_cm:.3f}cm}}|" * groesse
    zeilen = []
    for r in range(groesse):
        zeile = " & ".join(
            r"\centering\arraybackslash " + zellen[r * groesse + c] for c in range(groesse)
        )
        zeilen.append(zeile + r" \\ \hline")

    # Kopfzeile auf Kartenbreite: links der Titel des Kartensatzes (falls die
    # Datenbank einen hat), rechts die laufende Nummer. Praktisch, sobald
    # mehrere Kartensätze gleichzeitig im Umlauf sind.
    nummer_text = rf"\textbf{{Karte Nr.\ {nummer:02d}}}"
    if titel:
        kopf = (rf"\noindent\parbox{{{KARTENBREITE_CM}cm}}{{\textbf{{{latex_escape(titel)}}}"
                rf"\hfill {nummer_text}}}\\[1.5mm]")
    else:
        kopf = rf"\noindent{nummer_text}\\[1.5mm]"

    tabelle = (
        r"\renewcommand{\arraystretch}{1.3}" + "\n"
        + kopf + "\n"
        rf"\begin{{tabular}}{{{spalten}}}" + "\n"
        r"\hline" + "\n"
        + "\n".join(zeilen) + "\n"
        r"\end{tabular}"
    )
    return tabelle


TRENNLINIE = (
    r"\vspace{4mm}"
    r"\noindent\begin{tikzpicture}\draw[dashed,gray] (0,0) -- (\linewidth,0);\end{tikzpicture}"
    r"\vspace{4mm}"
)


def baue_dokument(karten_latex: list[str]) -> str:
    praeambel = r"""
\documentclass[a4paper,12pt]{article}
\usepackage[ngerman]{babel}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=1.3cm]{geometry}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
\usepackage{array}
\usepackage{xcolor}
\usepackage{graphicx}
\pagestyle{empty}
\setlength{\parindent}{0pt}
% Feste Innenabstände oben/unten pro Tabellenzelle, damit große Ziffern nie
% die Rahmenlinie berühren -- unabhängig von der tatsächlichen Zeilenhöhe,
% die LaTeX sonst allein aus dem Zelleninhalt herleitet (bei kurzem Inhalt
% wie einzelnen Zahlen reicht das nicht als Abstand zur Linie darüber).
\newcommand{\Tstrut}{\rule{0pt}{0.9cm}}
\newcommand{\Bstrut}{\rule[-0.35cm]{0pt}{0pt}}
""".strip()

    teile = [praeambel, r"\begin{document}"]
    for i in range(0, len(karten_latex), 2):
        teile.append(karten_latex[i])
        if i + 1 < len(karten_latex):
            teile.append(TRENNLINIE)
            teile.append(karten_latex[i + 1])
        teile.append(r"\newpage")
    teile.append(r"\end{document}")
    return "\n\n".join(teile)


# ---------------------------------------------------------------------------
# Kontrollliste
# ---------------------------------------------------------------------------

def schreibe_kontrollliste(pfad: Path, karten: list[list[int]], eintraege_by_id: dict, feldname: str) -> None:
    # utf-8-sig + Semikolon: So öffnet deutsches Excel die Datei direkt mit
    # korrekten Umlauten und sauber getrennten Spalten (LibreOffice ebenfalls).
    with pfad.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["karte_nr", "id", "thema", f"inhalt_{feldname}"])
        for nummer, karte in enumerate(karten, start=1):
            for eid in sorted(karte):
                feld = eintraege_by_id[eid][feldname]
                inhalt = feld.get("text") or feld.get("term") or "(Bild)"
                writer.writerow([f"{nummer:02d}", eid, eintraege_by_id[eid].get("thema", ""), inhalt])


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def finde_json_automatisch() -> Path:
    """
    Sucht die Aufgabendatenbank, wenn weder ein Kommandozeilen-Parameter noch
    die Konstante JSON_DATEI gesetzt ist: die einzige JSON-Datei im Ordner
    "daten/" neben diesem Projekt. Bei keiner oder mehreren Kandidaten wird
    ein klarer Fehler ausgegeben statt zu raten.
    """
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
    namen = ", ".join(k.name for k in kandidaten)
    raise SystemExit(
        f"Mehrere JSON-Dateien in {daten_ordner} gefunden ({namen}). "
        f"Bitte JSON_DATEI oben im Skript setzen oder den Pfad als Parameter übergeben, "
        f"welche verwendet werden soll."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Erzeugt Bingokarten-PDFs aus einer Aufgabendatenbank (JSON). "
                     "Ohne Parameter aufgerufen werden die Konstanten oben im Skript verwendet."
    )
    parser.add_argument("json_pfad", type=Path, nargs="?", default=None,
                         help="Pfad zur Aufgabendatenbank (Default: Konstante JSON_DATEI bzw. automatische Suche in daten/)")
    parser.add_argument("-n", "--anzahl-karten", type=int, default=None,
                         help=f"Anzahl zu erzeugender Karten (Default: Konstante ANZAHL_KARTEN = {ANZAHL_KARTEN})")
    parser.add_argument("-g", "--groesse", type=int, choices=[3, 4, 5], default=None,
                         help=f"Rastergröße NxN (Default: Konstante RASTERGROESSE = {RASTERGROESSE})")
    parser.add_argument("--seed", type=int, default=None,
                         help=f"Zufalls-Seed für Reproduzierbarkeit (Default: Konstante SEED = {SEED})")
    parser.add_argument("--kartenfeld", choices=["frage", "antwort"], default=None,
                         help="Welches Feld auf der Karte steht (Default: Konstante KARTENFELD bzw. meta.kartenfeld der JSON)")
    parser.add_argument("--joker", choices=["auto", "ja", "nein"], default=None,
                         help=f"Joker-Mittelfeld (Default: Konstante JOKER = {JOKER!r})")
    parser.add_argument("-o", "--ausgabe", type=Path, default=None,
                         help="Ausgabe-PDF (Default: Konstante AUSGABE_PDF bzw. <json_name>_karten.pdf)")
    parser.add_argument("--nur-pruefen", action="store_true", help="Nur Plausibilitätsprüfung ausführen, kein PDF erzeugen")
    args = parser.parse_args()

    json_pfad = args.json_pfad or (Path(JSON_DATEI) if JSON_DATEI else None) or finde_json_automatisch()
    anzahl_karten = args.anzahl_karten if args.anzahl_karten is not None else ANZAHL_KARTEN
    groesse = args.groesse if args.groesse is not None else RASTERGROESSE
    seed = args.seed if args.seed is not None else SEED
    kartenfeld_vorgabe = args.kartenfeld or KARTENFELD
    joker_modus = args.joker or JOKER
    ausgabe_vorgabe = args.ausgabe or (Path(AUSGABE_PDF) if AUSGABE_PDF else None)

    if anzahl_karten < 1:
        print(
            f"FEHLER: Anzahl Karten muss mindestens 1 sein (angegeben: {anzahl_karten}).",
            file=sys.stderr,
        )
        return 1

    try:
        daten = lade_datenbank(json_pfad)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"FEHLER beim Laden der Datenbank: {exc}", file=sys.stderr)
        return 1

    print(f"Verwende Aufgabendatenbank: {json_pfad}")

    eintraege = daten["eintraege"]
    eintraege_by_id = {e["id"]: e for e in eintraege}
    kartenfeld = kartenfeld_vorgabe or daten.get("meta", {}).get("kartenfeld", "antwort")

    if joker_modus == "auto":
        joker = groesse % 2 == 1
    else:
        joker = joker_modus == "ja"
    benoetigte_felder = groesse * groesse - (1 if joker else 0)

    try:
        warnungen, werte_zu_ids = pruefe_plausibilitaet(eintraege, kartenfeld, benoetigte_felder, anzahl_karten)
    except ValueError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1

    if warnungen:
        print("Warnungen zur Aufgabendatenbank:")
        for w in warnungen:
            print(f"  - {w}")
        print()

    if args.nur_pruefen:
        print("Prüfung abgeschlossen (--nur-pruefen), es wurde kein PDF erzeugt.")
        return 0

    if shutil.which("pdflatex") is None:
        print(
            "FEHLER: 'pdflatex' wurde nicht gefunden. Für den PDF-Bau wird eine "
            "LaTeX-Distribution benötigt:\n"
            "  Linux (Debian/Ubuntu): sudo apt install texlive-latex-extra texlive-pictures texlive-lang-german\n"
            "  Windows: MiKTeX (https://miktex.org/)\n"
            "  macOS:   MacTeX (https://tug.org/mactex/)\n"
            "Danach mit 'pdflatex --version' prüfen, ob es im PATH liegt.\n"
            "Tipp: Die Datenbank lässt sich mit --nur-pruefen auch ohne LaTeX prüfen.",
            file=sys.stderr,
        )
        return 1

    rng = random.Random(seed)

    try:
        karten = erzeuge_kartensatz(werte_zu_ids, benoetigte_felder, anzahl_karten, rng)
    except RuntimeError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1

    ausgabe = ausgabe_vorgabe or json_pfad.with_name(json_pfad.stem + "_karten.pdf")
    if ausgabe.suffix.lower() != ".pdf":
        # Ohne .pdf-Endung wäre das Build-Verzeichnis (Ausgabepfad ohne Endung)
        # identisch mit der Zieldatei -- der Lauf würde erst nach dem kompletten
        # LaTeX-Bau am Verschieben scheitern.
        ausgabe = ausgabe.with_name(ausgabe.name + ".pdf")
        print(f"Hinweis: Ausgabedatei ohne .pdf-Endung angegeben, verwende {ausgabe.name}")
    build_verzeichnis = ausgabe.with_suffix("")
    build_verzeichnis.mkdir(parents=True, exist_ok=True)

    # Bilder aus früheren Läufen entfernen: Sie gehören womöglich zu IDs, die
    # es in der Datenbank gar nicht mehr gibt, und blieben sonst für immer im
    # Build-Ordner liegen.
    for alte_datei in build_verzeichnis.glob("bild_*"):
        alte_datei.unlink()

    titel = daten.get("meta", {}).get("titel", "")
    try:
        karten_latex = [
            render_karte(karte, eintraege_by_id, kartenfeld, groesse, joker, nr,
                         build_verzeichnis, rng, titel)
            for nr, karte in enumerate(karten, start=1)
        ]
    except ValueError as exc:
        print(f"FEHLER beim Aufbereiten der Karten: {exc}", file=sys.stderr)
        return 1
    tex_quelltext = baue_dokument(karten_latex)

    tex_pfad = build_verzeichnis / "karten.tex"
    tex_pfad.write_text(tex_quelltext, encoding="utf-8")

    log_pfad = build_verzeichnis / "karten.log"

    # Ein Durchlauf genügt: Das Dokument hat weder Querverweise noch
    # Inhaltsverzeichnis, es gibt also nichts, was ein zweiter Lauf noch
    # auflösen müsste. Falls LaTeX doch einmal einen zweiten Lauf anfordert
    # ("Rerun" im Log), wird er unten nachgeholt -- das spart bei
    # graphlastigen Kartensätzen die halbe Bauzeit.
    for durchlauf in range(2):
        ergebnis = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_pfad.name],
            cwd=build_verzeichnis,
            capture_output=True,
            text=True,
        )
        if ergebnis.returncode != 0:
            print("FEHLER bei pdflatex-Kompilierung. Log-Auszug:", file=sys.stderr)
            print("\n".join(ergebnis.stdout.splitlines()[-40:]), file=sys.stderr)
            print(f"Vollständiges Log: {log_pfad}", file=sys.stderr)
            return 1
        log_text = log_pfad.read_text(encoding="utf-8", errors="replace") if log_pfad.exists() else ""
        if "Rerun" not in log_text:
            break

    erzeugtes_pdf = build_verzeichnis / "karten.pdf"
    erzeugtes_pdf.replace(ausgabe)

    kontrollliste_pfad = ausgabe.with_name(ausgabe.stem + "_kontrollliste.csv")
    schreibe_kontrollliste(kontrollliste_pfad, karten, eintraege_by_id, kartenfeld)

    print(f"PDF erzeugt: {ausgabe} ({len(karten)} Karten, {groesse}x{groesse}, Joker={joker})")
    print(f"Kontrollliste: {kontrollliste_pfad}")
    print(f"Zwischendateien (LaTeX-Log etc.): {build_verzeichnis}/")

    # Bei großem Aufgabenpool und wenigen Karten kommt nicht jede Aufgabe vor.
    # Für die Lehrkraft beim Vorlesen ist das eine nützliche Information.
    verwendete_ids = {eid for karte in karten for eid in karte}
    unbenutzt = sorted(set(eintraege_by_id) - verwendete_ids)
    if unbenutzt:
        anzeige = ", ".join(str(i) for i in unbenutzt[:20])
        weitere = f", ... (+{len(unbenutzt) - 20})" if len(unbenutzt) > 20 else ""
        print(
            f"Hinweis: {len(unbenutzt)} von {len(eintraege_by_id)} Aufgaben kommen auf "
            f"keiner Karte vor: IDs {anzeige}{weitere}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
