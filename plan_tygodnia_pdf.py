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

    # Każde pole z dniami czytamy z WŁASNEGO bloku klamrowego. Wcześniej wyrażenie
    # zbierało pierwsze pięć „N: { start, koniec }" z całego wpisu dziecka — gdy przed
    # lekcjami stanęło pole angielski, Janek dostał godziny angielskiego jako lekcje,
    # a kontrola „jest 5 wpisów" to przepuściła.
    dni_re = r'(\d):\s*\{\s*start:\s*"(\d{2}:\d{2})",\s*koniec:\s*"(\d{2}:\d{2})"'

    def blok_pola(tresc, pole):
        m = re.search(r"\b" + pole + r":\s*", tresc)
        if not m:
            return None
        if tresc[m.end()] != "{":              # nazwa wspólnego obiektu, np. LEKCJE_MARYSI
            return blok(src, re.match(r"\w+", tresc[m.end():]).group(0))
        i = m.end()
        glebokosc, j = 0, i
        while True:
            if tresc[j] == "{": glebokosc += 1
            elif tresc[j] == "}":
                glebokosc -= 1
                if glebokosc == 0: return tresc[i:j + 1]
            j += 1

    zrodlo_planu = blok_pola(profil, "lekcje")
    if zrodlo_planu is None:
        raise SystemExit(f"{kto}: brak pola lekcje")
    pary = re.findall(dni_re, zrodlo_planu)
    if [int(d) for d, _, _ in pary] != [1, 2, 3, 4, 5]:
        raise SystemExit(f"{kto}: plan lekcji nie ma dokładnie dni 1–5, odczytane: {pary}")

    # angielski: osobne pole dziecka, tylko w wybrane dni
    angielski = {}
    a_zrodlo = blok_pola(profil, "angielski")
    if a_zrodlo is not None:
        a_pary = re.findall(dni_re, a_zrodlo)
        if not a_pary or len(a_pary) != a_zrodlo.count("start:"):
            raise SystemExit(f"{kto}: nie odczytałem całego pola angielski: {a_zrodlo}")
        angielski = {int(d): (a, b) for d, a, b in a_pary}

    # dodatkowe: zajęcia PO lekcjach w TYM SAMYM budynku (np. szachy) — wydłużają
    # koniec dnia, ale w odróżnieniu od angielskiego/Early Stage NIE wymuszają R3,
    # bo nie zmieniają przystanku ani linii. Patrz dzienSzkolny() w autobus.js.
    dodatkowe = {}
    d_zrodlo = blok_pola(profil, "dodatkowe")
    if d_zrodlo is not None:
        d_re = r'(\d):\s*\{\s*nazwa:\s*"([^"]+)",\s*start:\s*"(\d{2}:\d{2})",\s*koniec:\s*"(\d{2}:\d{2})"'
        d_pary = re.findall(d_re, d_zrodlo)
        if not d_pary or len(d_pary) != d_zrodlo.count("start:"):
            raise SystemExit(f"{kto}: nie odczytałem całego pola dodatkowe: {d_zrodlo}")
        dodatkowe = {int(d): (nazwa, a, b) for d, nazwa, a, b in d_pary}

    plan = [(DNI[int(d) - 1], a, b, angielski.get(int(d)), dodatkowe.get(int(d)))
            for d, a, b in pary]

    def zbuduj_rano(klucze_):
        wynik = []
        for k in klucze_:
            if k not in do_szkoly:
                raise SystemExit(f"{kto}: kurs {k!r} nie istnieje w DO_SZKOLY")
            t = do_szkoly[k]
            przyj = re.search(r"przyjazdy:\s*\{(.*?)\}", t, re.S).group(1)
            nry = re.search(r"numery:\s*\[(.*?)\]", t, re.S)
            wynik.append({"linia": tekst(t, "linia"), "stop": tekst(t, "stop"),
                         "walk": liczba(t, "walk"), "zPrzystanku": liczba(t, "zPrzystanku"),
                         "odjazdy": godziny(t, "weekday"), "przyjazdy": godziny(przyj, "weekday"),
                         "numery": re.findall(r'"([^"]+)"', nry.group(1)) if nry else []})
        return wynik

    rano = zbuduj_rano(klucze)

    # Early Stage: OSOBNE miejsce z własnym przystankiem — obowiązuje tylko w dni,
    # gdy angielski jest pierwszy/ostatni (patrz linieNaDzien() w autobus.js).
    klucze_early_rano = re.findall(r'"(\w+)"',
        re.search(r"naEarlyStage:\s*\[(.*?)\]", profil, re.S).group(1)) \
        if "naEarlyStage" in profil else []
    rano_early = zbuduj_rano(klucze_early_rano)

    klucze_pow = re.findall(r'"(\w+)"',
                            re.search(r"zeSzkoly:\s*\[(.*?)\]", profil, re.S).group(1)) \
        if "zeSzkoly" in profil else list(ze_szkoly)
    # ograniczenie typu „gimbusem nie wcześniej niż o 15:00" — musi działać
    # tak samo jak w aplikacji, inaczej PDF pokaże inny kurs niż telefon
    m_od = re.search(r'powrotGimbusOd:\s*"(\d{2}:\d{2})"', profil)
    gimbus_od = mn(m_od.group(1)) if m_od else None

    def zbuduj_powroty(klucze_):
        wynik = []
        for k in klucze_:
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
            wynik.append({"linia": linia, "stop": tekst(t, "stop"),
                          "walk": liczba(t, "walk"), "odjazdy": odjazdy,
                          "cele": lista_celow, "numery": lista_nrow})
        return wynik

    powroty = zbuduj_powroty(klucze_pow)

    klucze_early_pow = re.findall(r'"(\w+)"',
        re.search(r"zEarlyStage:\s*\[(.*?)\]", profil, re.S).group(1)) \
        if "zEarlyStage" in profil else []
    powrot_early = zbuduj_powroty(klucze_early_pow)

    if a_zrodlo is not None and not (rano_early or powrot_early):
        raise SystemExit(f"{kto}: ma pole angielski, ale brak naEarlyStage/zEarlyStage")

    return imie, plan, rano, powroty, rano_early, powrot_early


def zbuduj(plan, rano, powroty, rano_early=(), powrot_early=()):
    wiersze, uwagi = [], []
    for dzien, start, koniec, ang, dod in plan:
        # Dzień szkolny = od pierwszych do ostatnich zajęć; między angielskim a lekcjami
        # dziecko zostaje w szkole. Angielski na początku dnia -> rano jedzie na Early
        # Stage (osobny przystanek), na końcu -> wraca spod Early Stage. Dodatkowe (np.
        # szachy) wydłuża tylko koniec dnia, bez wymuszania R3 — ten sam budynek co
        # szkoła. "Tylko R3" wraca spod Early Stage tylko wtedy, gdy to WŁAŚNIE
        # angielski jest faktycznie ostatnim punktem dnia. Ta sama reguła co
        # linieNaDzien()/dzienSzkolny() w autobus.js.
        m_lekcje_koniec = mn(koniec)
        s = mn(start)
        rano_r3 = bool(ang) and mn(ang[0]) < s
        if rano_r3:
            s = mn(ang[0])
        m_ang = mn(ang[1]) if ang else -1
        m_dod = mn(dod[2]) if dod else -1
        k = max(m_lekcje_koniec, m_ang, m_dod)
        powrot_r3 = bool(ang) and m_ang == k and m_ang > m_lekcje_koniec
        pierwsze = gg(s)

        # w dni z Early Stage na początku/końcu korzysta się WYŁĄCZNIE z jej kursów;
        # brak takich kursów u dziecka -> spadamy na zwykłe R3, tak jak w aplikacji
        zrodlo_rano = rano_early if (rano_r3 and rano_early) else \
            [k_ for k_ in rano if re.search(r"\bR3\b", k_["linia"])] if rano_r3 else rano
        zrodlo_pow = powrot_early if (powrot_r3 and powrot_early) else \
            [k_ for k_ in powroty if re.search(r"\bR3\b", k_["linia"])] if powrot_r3 else powroty

        naj = None
        for kurs in zrodlo_rano:
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
            raise SystemExit(f"{dzien}: żaden kurs nie dowozi przed {pierwsze}")

        pow = None
        for kurs in zrodlo_pow:
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
            raise SystemExit(f"{dzien}: brak kursu powrotnego po {gg(k)}")

        czesci = [f"{start}–{koniec}"]
        if dod:
            czesci.append(f"{dod[0]}: {dod[1]}–{dod[2]}")
        if ang:
            wiersz_ang = f"ang. {ang[0]}–{ang[1]}"
            czesci = [wiersz_ang] + czesci if rano_r3 else czesci + [wiersz_ang]
        zajecia = "\n".join(czesci)
        wiersze.append([dzien, zajecia, gg(naj["wyjscie"]),
                        f"{naj['linia']}\n{naj['stop']}", naj["odjazd"],
                        gg(naj["wSzkole"]),
                        (f"{pow['linia']}\n→ {pow['cel']}\n{pow['odjazd']}" if pow.get("cel")
                         else f"{pow['linia']}\n{pow['odjazd']}")])
        uwagi.append((dzien, s - naj["wSzkole"], mn(pow["odjazd"]) - k))
    return wiersze, uwagi


def main():
    imie, plan, rano, powroty, rano_early, powrot_early = wczytaj(DZIECKO)
    wiersze, uwagi = zbuduj(plan, rano, powroty, rano_early, powrot_early)

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
                colWidths=[26 * mm, 29 * mm, 20 * mm, 34 * mm, 19 * mm, 20 * mm, 38 * mm],
                rowHeights=[15 * mm] + [17 * mm] * 5)
    tab.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "PL-B"), ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18213a")),
        ("FONTNAME", (0, 1), (0, -1), "PL-B"), ("FONTSIZE", (0, 1), (0, -1), 10),
        ("FONTNAME", (1, 1), (-1, -1), "PL"), ("FONTSIZE", (1, 1), (-1, -1), 11),
        ("FONTSIZE", (3, 1), (3, -1), 8.5),
        ("FONTSIZE", (1, 1), (1, -1), 9.5),     # lekcje + ewentualnie angielski w 2 liniach
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
