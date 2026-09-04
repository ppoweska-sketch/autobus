#!/usr/bin/env python3
"""
Generuje plan_tygodnia.pdf — jedna strona A4 z rozpiską na cały tydzień.

Godziny NIE są tu wpisane na sztywno: skrypt czyta rozkład wprost z index.html,
więc PDF nie może się rozjechać z aplikacją. Sprawdza przy okazji, że przejazd
do szkoły trwa 18 min, a kurs powrotny odjeżdża 25 min po odjeździe spod domu —
jeśli któreś przesunięcie przestanie być stałe, przerywa zamiast wypisać
wiarygodnie wyglądające bzdury.

Uruchomienie:  ../claude\\ trading\\ bot/.venv/bin/python plan_tygodnia_pdf.py
"""
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ZRODLO = Path(__file__).with_name("autobus.js")
DZIECKO = (sys.argv[1] if len(sys.argv) > 1 else "marysia").lower()
WYNIK = Path(__file__).with_name(f"plan_tygodnia_{DZIECKO}.pdf")

# Wbudowane fonty reportlaba (Helvetica) nie mają ł, ś, ż, ć, ę — trzeba osadzić TTF.
pdfmetrics.registerFont(TTFont("PL", "/System/Library/Fonts/Supplemental/Arial.ttf"))
pdfmetrics.registerFont(TTFont("PL-B", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))

Z_DOMU, DO_SZKOLY, NA_PRZYSTANEK = 15, 5, 2      # minuty dojścia

DNI = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]


def wczytaj_plan_lekcji(kto):
    """Plan lekcji czytany z autobus.js — jedno źródło prawdy z aplikacją."""
    src = ZRODLO.read_text(encoding="utf-8")
    blok = src[src.index("const PLANY_LEKCJI"):src.index("const IMIE")]
    czesc = blok[blok.index(kto + ":"):]
    pary = re.findall(r'(\d):\s*\{\s*start:\s*"(\d{2}:\d{2})",\s*koniec:\s*"(\d{2}:\d{2})"',
                      czesc)[:5]
    if len(pary) != 5:
        raise SystemExit(f"nie znalazłem pełnego planu lekcji dla {kto!r}")
    return [(DNI[int(d) - 1], s, k) for d, s, k in pary]


PLAN_LEKCJI = None  # ustawiane w main()


def wczytaj_rozklad():
    src = ZRODLO.read_text(encoding="utf-8")
    blok = src[src.index("const DEFAULT_CONFIG"):src.index("const WERSJA")]
    dom = blok[blok.index('id: "dom"'):blok.index('id: "szkola"')]
    szk = blok[blok.index('id: "szkola"'):]

    def lista(zrodlo, nazwa):
        m = re.search(nazwa + r"\s*:\s*\[(.*?)\]", zrodlo, re.S)
        return re.findall(r'"(\d{2}:\d{2})"', m.group(1))

    odjazd = lista(dom[:dom.index("arrivals")], "weekday")
    przyjazd = lista(dom[dom.index("arrivals"):], "weekday")
    powrot = lista(szk, "weekday")

    if {mn(p) - mn(o) for o, p in zip(odjazd, przyjazd)} != {18}:
        raise SystemExit("Przejazd do szkoły nie wynosi równo 18 min — sprawdź rozkład.")
    if {mn(p) - mn(o) for o, p in zip(odjazd, powrot)} != {25}:
        raise SystemExit("Kurs powrotny nie jest równo +25 min — sprawdź rozkład.")
    return odjazd, przyjazd, powrot


def mn(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def gg(t):
    return f"{t // 60:02d}:{t % 60:02d}"


def zbuduj_wiersze(odjazd, przyjazd, powrot):
    wiersze, uwagi = [], []
    for dzien, start, koniec in PLAN_LEKCJI:
        s, k = mn(start), mn(koniec)
        # rano: ostatni kurs, który dowozi do szkoły przed dzwonkiem
        kandydaci = [(o, p) for o, p in zip(odjazd, przyjazd) if mn(p) + DO_SZKOLY <= s]
        if not kandydaci:
            raise SystemExit(f"{dzien}: żaden kurs nie dowozi przed {start}")
        o, p = kandydaci[-1]
        w_szkole = mn(p) + DO_SZKOLY
        # po lekcjach: pierwszy odjazd, na który da się dojść
        pozniejsze = [d for d in powrot if mn(d) >= k + NA_PRZYSTANEK]
        if not pozniejsze:
            raise SystemExit(f"{dzien}: brak kursu powrotnego po {koniec}")
        wiersze.append([dzien, start, gg(mn(o) - Z_DOMU), o, gg(w_szkole), koniec, pozniejsze[0]])
        uwagi.append((dzien, s - w_szkole, mn(pozniejsze[0]) - k))
    return wiersze, uwagi


def main():
    global PLAN_LEKCJI
    PLAN_LEKCJI = wczytaj_plan_lekcji(DZIECKO)
    odjazd, przyjazd, powrot = wczytaj_rozklad()
    wiersze, uwagi = zbuduj_wiersze(odjazd, przyjazd, powrot)

    doc = SimpleDocTemplate(str(WYNIK), pagesize=A4,
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=16 * mm, bottomMargin=14 * mm,
                            title=f"Autobus R3 — plan tygodnia — {DZIECKO}", author="")
    tytul = ParagraphStyle("t", fontName="PL-B", fontSize=21, leading=25,
                           alignment=TA_CENTER, textColor=colors.HexColor("#0e1526"))
    podtytul = ParagraphStyle("p", fontName="PL", fontSize=10.5, leading=15,
                              alignment=TA_CENTER, textColor=colors.HexColor("#5b6b8c"))
    stopka = ParagraphStyle("s", fontName="PL", fontSize=9, leading=14,
                            textColor=colors.HexColor("#42506f"))

    naglowki = ["", "Początek\nlekcji", "Wyjdź\nz domu", "Odjazd\nautobusu",
                "W szkole\njesteś", "Koniec\nlekcji", "Odjazd\nautobusu"]
    dane = [naglowki] + wiersze

    tab = Table(dane, colWidths=[34 * mm] + [24 * mm] * 6, rowHeights=[15 * mm] + [14 * mm] * 5)
    tab.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "PL-B"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18213a")),
        ("FONTNAME", (0, 1), (0, -1), "PL-B"),
        ("FONTSIZE", (0, 1), (0, -1), 11),
        ("FONTNAME", (1, 1), (-1, -1), "PL"),
        ("FONTSIZE", (1, 1), (-1, -1), 13),
        # dwie kolumny, na które dziecko patrzy najczęściej
        ("FONTNAME", (2, 1), (2, -1), "PL-B"),
        ("TEXTCOLOR", (2, 1), (2, -1), colors.HexColor("#1d4ed8")),
        ("FONTNAME", (6, 1), (6, -1), "PL-B"),
        ("TEXTCOLOR", (6, 1), (6, -1), colors.HexColor("#1d4ed8")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 1), (0, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5fb")]),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#d5dcea")),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#18213a")),
        ("LINEAFTER", (0, 0), (0, -1), 0.9, colors.HexColor("#18213a")),
        ("LINEAFTER", (4, 0), (4, -1), 0.9, colors.HexColor("#18213a")),
    ]))

    najciasniejszy = min(uwagi, key=lambda u: u[1])
    czekania = sorted({c for _, _, c in uwagi})

    tresc = [
        Paragraph(f"Autobus R3 — plan tygodnia — {DZIECKO.capitalize()}", tytul),
        Spacer(1, 3 * mm),
        Paragraph("rano: Widokowa 02 &rarr; Łady – Szkoła 02&nbsp;&nbsp;·&nbsp;&nbsp;"
                  "po lekcjach: Łady – Szkoła 01 &rarr; dom", podtytul),
        Spacer(1, 7 * mm),
        tab,
        Spacer(1, 8 * mm),
        Paragraph(f"<b>Jak dobrane:</b> rano ostatni kurs, który dowozi przed dzwonkiem; "
                  f"po lekcjach pierwszy kurs, na który da się zdążyć. "
                  f"Dojście z domu na przystanek {Z_DOMU} min, z przystanku do szkoły "
                  f"{DO_SZKOLY} min, ze szkoły na przystanek {NA_PRZYSTANEK} min.", stopka),
        Spacer(1, 2 * mm),
        Paragraph(f"<b>Uwaga:</b> najmniejszy zapas jest w {najciasniejszy[0].lower()} — "
                  f"tylko {najciasniejszy[1]} min od przyjścia do szkoły do dzwonka. "
                  f"Po lekcjach czeka się na autobus "
                  f"{czekania[0]}–{czekania[-1]} min, codziennie.", stopka),
        Spacer(1, 2 * mm),
        Paragraph("W soboty autobus jeździ (4 kursy), w niedziele i święta nie jeździ wcale.",
                  stopka),
    ]
    doc.build(tresc)
    print(f"zapisano {WYNIK}")
    for d, z, c in uwagi:
        print(f"  {d:<13} zapas {z:>2} min, czekanie {c:>2} min")


if __name__ == "__main__":
    main()
