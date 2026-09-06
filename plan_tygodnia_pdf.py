#!/usr/bin/env python3
"""
Generuje plan_tygodnia_<dziecko>.pdf — jedna strona A4 z rozpiską na cały tydzień.

Dane czyta z autobus.js, więc PDF nie może rozjechać się z aplikacją, i stosuje
DOKŁADNIE te same reguły wyboru kursu:
  rano       — wyjść z domu jak najpóźniej, byle zdążyć przed dzwonkiem
  po lekcjach — najkrótsze czekanie, czyli najwcześniejszy osiągalny odjazd

Uwaga na przyszłość: parsowanie JavaScriptu wyrażeniami regularnymi jest kruche
i pękało już przy każdej zmianie struktury konfiguracji. Dlatego każdy brakujący
element przerywa działanie — lepiej brak PDF-u niż PDF z cichym błędem.

    "../claude trading bot/.venv/bin/python" plan_tygodnia_pdf.py janek
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

# Wbudowane fonty reportlaba nie mają ł, ś, ż, ć, ę — trzeba osadzić TTF.
pdfmetrics.registerFont(TTFont("PL", "/System/Library/Fonts/Supplemental/Arial.ttf"))
pdfmetrics.registerFont(TTFont("PL-B", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))

DNI = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]

mn = lambda s: int(s[:2]) * 60 + int(s[3:])
gg = lambda t: f"{t // 60:02d}:{t % 60:02d}"


def blok(src, nazwa):
    """Wycina `const NAZWA = { ... };` licząc nawiasy klamrowe."""
    i = src.index(f"const {nazwa}")
    i = src.index("{", i)
    glebokosc, j = 0, i
    while True:
        if src[j] == "{": glebokosc += 1
        elif src[j] == "}":
            glebokosc -= 1
            if glebokosc == 0: return src[i:j + 1]
        j += 1


def wpisy(tresc):
    """Dzieli obiekt na pary klucz -> treść wpisu (jeden poziom zagnieżdżenia)."""
    out, i = {}, 0
    for m in re.finditer(r"(\w+)\s*:\s*\{", tresc):
        if tresc.count("{", 0, m.start()) - tresc.count("}", 0, m.start()) != 1:
            continue                                   # zagnieżdżone głębiej
        start = m.end() - 1
        glebokosc, j = 0, start
        while True:
            if tresc[j] == "{": glebokosc += 1
            elif tresc[j] == "}":
                glebokosc -= 1
                if glebokosc == 0: break
            j += 1
        out[m.group(1)] = tresc[start:j + 1]
    return out


def godziny(tresc, nazwa):
    m = re.search(nazwa + r"\s*:\s*\[(.*?)\]", tresc, re.S)
    return re.findall(r'"(\d{2}:\d{2})"', m.group(1)) if m else []


def liczba(tresc, nazwa, domyslnie=0):
    m = re.search(nazwa + r"\s*:\s*(\d+)", tresc)
    return int(m.group(1)) if m else domyslnie


def tekst(tresc, nazwa):
    m = re.search(nazwa + r'\s*:\s*"([^"]*)"', tresc)
    return m.group(1) if m else ""


def wczytaj(kto):
    src = ZRODLO.read_text(encoding="utf-8")
    do_szkoly = wpisy(blok(src, "DO_SZKOLY"))
    ze_szkoly = wpisy(blok(src, "ZE_SZKOLY"))
    dzieci = wpisy(blok(src, "DZIECI"))
    if kto not in dzieci:
        raise SystemExit(f"nie znam dziecka {kto!r}; są: {', '.join(dzieci)}")
    profil = dzieci[kto]

    imie = tekst(profil, "imie")
    klucze = re.findall(r'"(\w+)"', re.search(r"doSzkoly:\s*\[(.*?)\]", profil, re.S).group(1))

    # plan lekcji: albo wprost we wpisie, albo przez nazwę wspólnego obiektu
    m = re.search(r"lekcje:\s*(\w+)", profil)
    zrodlo_planu = blok(src, m.group(1)) if m else profil
    pary = re.findall(r'(\d):\s*\{\s*start:\s*"(\d{2}:\d{2})",\s*koniec:\s*"(\d{2}:\d{2})"',
                      zrodlo_planu)[:5]
    if len(pary) != 5:
        raise SystemExit(f"niepełny plan lekcji dla {kto!r}")
    plan = [(DNI[int(d) - 1], a, b) for d, a, b in pary]

    rano = []
    for k in klucze:
        if k not in do_szkoly:
            raise SystemExit(f"{kto}: kurs {k!r} nie istnieje w DO_SZKOLY")
        t = do_szkoly[k]
        przyj = re.search(r"przyjazdy:\s*\{(.*?)\}", t, re.S).group(1)
        nry = re.search(r"numery:\s*\[(.*?)\]", t, re.S)
        rano.append({"linia": tekst(t, "linia"), "stop": tekst(t, "stop"),
                     "walk": liczba(t, "walk"), "zPrzystanku": liczba(t, "zPrzystanku"),
                     "odjazdy": godziny(t, "weekday"), "przyjazdy": godziny(przyj, "weekday"),
                     "numery": re.findall(r'"([^"]+)"', nry.group(1)) if nry else []})

    klucze_pow = re.findall(r'"(\w+)"',
                            re.search(r"zeSzkoly:\s*\[(.*?)\]", profil, re.S).group(1)) \
        if "zeSzkoly" in profil else list(ze_szkoly)
    # ograniczenie typu „gimbusem nie wcześniej niż o 15:00" — musi działać
    # tak samo jak w aplikacji, inaczej PDF pokaże inny kurs niż telefon
    m_od = re.search(r'powrotGimbusOd:\s*"(\d{2}:\d{2})"', profil)
    gimbus_od = mn(m_od.group(1)) if m_od else None

    powroty = []
    for k in klucze_pow:
        t = ze_szkoly[k]
        cele = re.search(r"doPrzystanku:\s*\[(.*?)\]", t, re.S)
        nry = re.search(r"numery:\s*\[(.*?)\]", t, re.S)
        staly_cel = tekst(t, "przystanekDocelowy")
        linia = tekst(t, "linia")
        odjazdy = godziny(t, "weekday")
        lista_celow = re.findall(r'"([^"]+)"', cele.group(1)) if cele else []
        lista_nrow = re.findall(r'"([^"]+)"', nry.group(1)) if nry else []
        if gimbus_od is not None and linia == "Gimbus":
            zostaw = [i for i, o in enumerate(odjazdy) if mn(o) >= gimbus_od]
            odjazdy = [odjazdy[i] for i in zostaw]
            lista_celow = [lista_celow[i] for i in zostaw if i < len(lista_celow)]
            lista_nrow = [lista_nrow[i] for i in zostaw if i < len(lista_nrow)]
        if not lista_celow and staly_cel:
            lista_celow = [staly_cel] * len(odjazdy)
        powroty.append({"linia": linia, "stop": tekst(t, "stop"),
                        "walk": liczba(t, "walk"), "odjazdy": odjazdy,
                        "cele": lista_celow, "numery": lista_nrow})
    return imie, plan, rano, powroty


def zbuduj(plan, rano, powroty):
    wiersze, uwagi = [], []
    for dzien, start, koniec in plan:
        s, k = mn(start), mn(koniec)

        naj = None
        for kurs in rano:
            for o, p in zip(kurs["odjazdy"], kurs["przyjazdy"]):
                w_szkole = mn(p) + kurs["zPrzystanku"]
                if w_szkole > s:
                    continue
                wyjscie = mn(o) - kurs["walk"]
                if naj is None or wyjscie > naj["wyjscie"]:
                    i = kurs["odjazdy"].index(o)
                    nr = kurs["numery"][i] if i < len(kurs["numery"]) else ""
                    naj = {"linia": kurs["linia"] + (" " + nr if nr else ""),
                           "stop": kurs["stop"], "odjazd": o,
                           "wSzkole": w_szkole, "wyjscie": wyjscie}
        if naj is None:
            raise SystemExit(f"{dzien}: żaden kurs nie dowozi przed {start}")

        pow = None
        for kurs in powroty:
            for d in kurs["odjazdy"]:
                if mn(d) < k + kurs["walk"]:
                    continue
                if pow is None or mn(d) < mn(pow["odjazd"]):
                    i = kurs["odjazdy"].index(d)
                    cel = kurs["cele"][i] if i < len(kurs["cele"]) else None
                    nr = kurs["numery"][i] if i < len(kurs["numery"]) else ""
                    pow = {"linia": kurs["linia"] + (" " + nr if nr else ""),
                           "odjazd": d, "cel": cel}
                break
        if pow is None:
            raise SystemExit(f"{dzien}: brak kursu powrotnego po {koniec}")

        wiersze.append([dzien, f"{start}–{koniec}", gg(naj["wyjscie"]),
                        f"{naj['linia']}\n{naj['stop']}", naj["odjazd"],
                        gg(naj["wSzkole"]),
                        (f"{pow['linia']}\n→ {pow['cel']}\n{pow['odjazd']}" if pow.get("cel")
                         else f"{pow['linia']}\n{pow['odjazd']}")])
        uwagi.append((dzien, s - naj["wSzkole"], mn(pow["odjazd"]) - k))
    return wiersze, uwagi


def main():
    imie, plan, rano, powroty = wczytaj(DZIECKO)
    wiersze, uwagi = zbuduj(plan, rano, powroty)

    doc = SimpleDocTemplate(str(WYNIK), pagesize=A4,
                            leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=16 * mm, bottomMargin=14 * mm,
                            title=f"Autobus — plan tygodnia — {imie}", author="")
    tytul = ParagraphStyle("t", fontName="PL-B", fontSize=21, leading=25,
                           alignment=TA_CENTER, textColor=colors.HexColor("#0e1526"))
    podtytul = ParagraphStyle("p", fontName="PL", fontSize=10.5, leading=15,
                              alignment=TA_CENTER, textColor=colors.HexColor("#5b6b8c"))
    stopka = ParagraphStyle("s", fontName="PL", fontSize=9, leading=14,
                            textColor=colors.HexColor("#42506f"))

    naglowki = ["", "Lekcje", "Wyjdź\nz domu", "Czym jedziesz", "Odjazd",
                "W szkole\njesteś", "Powrót"]
    tab = Table([naglowki] + wiersze,
                colWidths=[26 * mm, 23 * mm, 20 * mm, 34 * mm, 19 * mm, 20 * mm, 44 * mm],
                rowHeights=[15 * mm] + [17 * mm] * 5)
    tab.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "PL-B"), ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18213a")),
        ("FONTNAME", (0, 1), (0, -1), "PL-B"), ("FONTSIZE", (0, 1), (0, -1), 10),
        ("FONTNAME", (1, 1), (-1, -1), "PL"), ("FONTSIZE", (1, 1), (-1, -1), 11),
        ("FONTSIZE", (3, 1), (3, -1), 8.5),
        ("FONTNAME", (2, 1), (2, -1), "PL-B"), ("FONTSIZE", (2, 1), (2, -1), 13),
        ("TEXTCOLOR", (2, 1), (2, -1), colors.HexColor("#1d4ed8")),
        ("FONTNAME", (6, 1), (6, -1), "PL-B"), ("FONTSIZE", (6, 1), (6, -1), 8),
        ("TEXTCOLOR", (6, 1), (6, -1), colors.HexColor("#1d4ed8")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 1), (0, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5fb")]),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#d5dcea")),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#18213a")),
        ("LINEAFTER", (0, 0), (0, -1), 0.9, colors.HexColor("#18213a")),
        ("LINEAFTER", (5, 0), (5, -1), 0.9, colors.HexColor("#18213a")),
    ]))

    naj = min(uwagi, key=lambda u: u[1])
    czekania = sorted({c for _, _, c in uwagi})

    doc.build([
        Paragraph(f"Plan tygodnia — {imie}", tytul),
        Spacer(1, 3 * mm),
        Paragraph("wybrany kurs to ten, przy którym wychodzisz z domu najpóźniej "
                  "i najkrócej czekasz po lekcjach", podtytul),
        Spacer(1, 7 * mm),
        tab,
        Spacer(1, 8 * mm),
        Paragraph(f"<b>Uwaga:</b> najmniejszy zapas jest w {naj[0].lower()} — "
                  f"{naj[1]} min od przyjścia do szkoły do dzwonka. "
                  f"Po lekcjach czekasz {czekania[0]}–{czekania[-1]} min.", stopka),
        Spacer(1, 2 * mm),
        Paragraph("Gimbus jeździ tylko w dni nauki i nie kursuje w soboty. "
                  "W soboty jeździ wyłącznie R3, w niedziele i święta nic.", stopka),
    ])
    print(f"zapisano {WYNIK}")
    for d, z, c in uwagi:
        print(f"  {d:<13} zapas {z:>2} min, czekanie {c:>2} min")


if __name__ == "__main__":
    main()
