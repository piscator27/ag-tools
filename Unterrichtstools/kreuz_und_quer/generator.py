import random

# -------------------------------------------------------
# Kreuz und Quer - Arbeitsblattgenerator
# erzeugt kreuz_und_quer.tex
# -------------------------------------------------------

maxzahl = int(input("Größte Spielzahl (z.B. 6, 10, 13): "))

DATEI = "kreuz_und_quer.tex"


def kopfzahl():
    return random.randint(maxzahl, maxzahl * 6)


def spielfeld():
    z = [kopfzahl() for _ in range(3)]
    s = [kopfzahl() for _ in range(3)]

    return r"""
\begin{minipage}[t]{0.48\textwidth}
\centering

\renewcommand{\arraystretch}{2.0}

\begin{tabular}{|c||p{1.25cm}|p{1.25cm}|p{1.25cm}|}
\hline
 & \centering %d & \centering %d & \centering %d \tabularnewline
\hline\hline
%d & & &\\
\hline
%d & & &\\
\hline
%d & & &\\
\hline
\end{tabular}

\vspace{0.2cm}

\small
Zeilen:\hrulefill

\vspace{0.15cm}

Spalten:\hrulefill

\vspace{0.15cm}

Gesamt:\hrulefill

\end{minipage}
""" % (s[0], s[1], s[2], z[0], z[1], z[2])


with open(DATEI, "w", encoding="utf8") as f:

    f.write(r"""
\documentclass[a4paper,11pt]{article}

\usepackage[a4paper,margin=1.5cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{array}

\pagestyle{empty}
\setlength{\parindent}{0pt}

\begin{document}

\begin{center}
{\Large\bfseries Kreuz und Quer}\\[1mm]
{\large Teilerspiel}\\[1mm]
Fi
\end{center}

Es werden nacheinander zufällige Zahlen von 1 bis """)

    f.write(str(maxzahl))

    f.write(r"""\
\ genannt.
Trage jede Zahl genau einmal in ein freies Feld ein.
Werte anschließend jede Tabelle selbst aus.

\vspace{0.6cm}
""")

    # obere Reihe
    f.write(spielfeld())
    f.write(r"\hfill")
    f.write(spielfeld())

    f.write(r"""

\vspace{0.8cm}

""")

    # untere Reihe
    f.write(spielfeld())
    f.write(r"\hfill")
    f.write(spielfeld())

    f.write(r"""

\end{document}
""")

print()
print("Datei", DATEI, "wurde erzeugt.")
