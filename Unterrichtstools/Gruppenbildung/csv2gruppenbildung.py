
#!/usr/bin/env python3
import csv
import re
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

def finde_rufname(text):
    m = re.search(r"\(([^()]*)\)\s*$", text.strip())
    return m.group(1).strip() if m else None

root = tk.Tk()
root.withdraw()

klasse = simpledialog.askstring("Klasse", "Klassenname (z.B. 5a):")
if not klasse:
    raise SystemExit

csvdatei = filedialog.askopenfilename(
    title="CSV-Datei auswählen",
    filetypes=[("CSV-Dateien","*.csv"),("Alle Dateien","*.*")]
)
if not csvdatei:
    raise SystemExit

namen = []
warnungen = []

with open(csvdatei, encoding="utf-8-sig", newline="") as f:
    sample = f.read(4096)
    f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except Exception:
        dialect = csv.excel

    reader = csv.reader(f, dialect)

    for zeile_nr, row in enumerate(reader, start=1):
        if not row:
            continue

        # Kopf überspringen
        if zeile_nr == 1 and "name" in " ".join(row).lower():
            continue

        # Gesamte Zeile wieder zusammensetzen
        gesamt = ", ".join(x.strip() for x in row if x.strip())

        rn = finde_rufname(gesamt)

        # Falls nicht gefunden: jede Spalte einzeln testen
        if rn is None:
            for feld in row:
                rn = finde_rufname(feld)
                if rn:
                    break

        if rn:
            namen.append(rn)
        else:
            warnungen.append(f"Zeile {zeile_nr}: {gesamt}")

# alphabetisch
namen = sorted(namen, key=lambda s: s.casefold())

# Doppelte erkennen
doppelte = sorted({n for n in namen if namen.count(n) > 1}, key=str.casefold)



js = ' "' + klasse + '" : [' + ", ".join(f'"{n}"' for n in namen) + '] }'

# Ausgabe
print(js)

root.clipboard_clear()
root.clipboard_append(js)
root.update()

ziel = Path(csvdatei).with_name(f"{klasse}.js.txt")
ziel.write_text(js, encoding="utf-8")

msg = f"{len(namen)} Rufnamen übernommen.\n\nGespeichert als:\n{ziel}\n\nDie JavaScript-Zeile wurde in die Zwischenablage kopiert."

if doppelte:
    msg += "\n\nDoppelte Rufnamen:\n" + ", ".join(doppelte)

if warnungen:
    msg += f"\n\n{len(warnungen)} Zeilen konnten nicht gelesen werden."
    if len(warnungen) <= 10:
        msg += "\n" + "\n".join(warnungen)

messagebox.showinfo("Fertig", msg)
