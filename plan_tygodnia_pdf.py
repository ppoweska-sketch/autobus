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

DO_SZKOLY, NA_PRZYSTANEK = 5, 2   # dojście z przystanku do szkoły / ze szkoły na przystanek
Z_DOMU = None                     # zależy od dziecka, ustawiane w main()

DNI = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]
PLAN_LEKCJI = None


def _tablica(zrodlo, nazwa):
    m = re.search(nazwa + r"\s*:\s*\[(.*?)\]", zrodlo, re.S)
    return re.findall(r'"(\d{2}:\d{2})"', m.group(1)) if m else []


def wczytaj(kto):
    """Czyta z autobus.js: plan lekcji, przystanek domowy i rozkłady.
    Jedno źródło prawdy z aplikacją — PDF nie może się z nią rozjechać."""
    src = ZRODLO.read_text(encoding="utf-8")

    # które dziecko, z którego przystanku i jaki plan lekcji
    blok_dzieci = src[src.index("const DZIECI"):src.index("const PROFIL")]
    m = re.search(kto + r"\s*:\s*\{(.*?)\n  \}", blok_dzieci, re.S) \
        or re.search(kto + r"\s*:\s*\{([^}]*\}[^}]*)\}", blok_dzieci, re.S)
    if not m:
        raise SystemExit(f"nie znalazłem dziecka {kto!r} w autobus.js")
    wpis = m.group(1)
    przystanek = re.search(r'przystanek:\s*"(\w+)"', wpis).group(1)

    nazwa_planu = re.search(r"lekcje:\s*(\w+)", wpis)
    if nazwa_planu and nazwa_planu.group(1) != "{":
        blok_planu = src[src.index("const " + nazwa_planu.group(1)):]
        blok_planu = blok_planu[:blok_planu.index("};")]
    else:
        blok_planu = wpis
    pary = re.findall(r'(\d):\s*\{\s*start:\s*"(\d{2}:\d{2})",\s*koniec:\s*"(\d{2}:\d{2})"',
                      blok_planu)[:5]
    if len(pary) != 5:
        raise SystemExit(f"niepełny plan lekcji dla {kto!r}")
    plan = [(DNI[int(d) - 1], a, b) for d, a, b in pary]

    # rozkład z przystanku domowego dziecka
    blok_przyst = src[src.index("const PRZYSTANKI_DOMOWE"):src.index("const PRZYJAZDY_DO_SZKOLY")]
    czesc = blok_przyst[blok_przyst.index(przystanek + ":"):]
    odjazd = _tablica(czesc, "weekday")
    nazwa_przystanku = re.search(r'stop:\s*"([^"]+)"', czesc).group(1)
    dojscie = int(re.search(r"walk:\s*(\d+)", czesc).group(1))

    blok_przyj = src[src.index("const PRZYJAZDY_DO_SZKOLY"):src.index("const LEKCJE_MARYSI")]
    przyjazd = _tablica(blok_przyj, "weekday")

    blok_szk = src[src.index('id: "szkola"'):]
    powrot = _tablica(blok_szk, "weekday")

    # kontrola: przejazd i kurs powrotny muszą mieć STAŁE przesunięcie
    przejazd = {mn(b) - mn(a) for a, b in zip(odjazd, przyjazd)}
    powrotne = {mn(b) - mn(a) for a, b in zip(odjazd, powrot)}
    if len(przejazd) != 1 or len(powrotne) != 1:
        raise SystemExit(f"przesunięcia nie są stałe (przejazd {sorted(przejazd)}, "
                         f"powrót {sorted(powrotne)}) — rozkład z niewłaściwego słupka?")
    return plan, odjazd, przyjazd, powrot, nazwa_przystanku, dojscie, przejazd.pop()


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
    global PLAN_LEKCJI, Z_DOMU
    (PLAN_LEKCJI, odjazd, przyjazd, powrot,
     nazwa_przystanku, Z_DOMU, przejazd) = wczytaj(DZIECKO)
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
        Paragraph(f"rano: {nazwa_przystanku} &rarr; Łady – Szkoła 02 ({przejazd} min)"
                  f"&nbsp;&nbsp;·&nbsp;&nbsp;po lekcjach: Łady – Szkoła 01 &rarr; dom", podtytul),
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
