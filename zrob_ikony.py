#!/usr/bin/env python3
"""
Rysuje ikonę autobusu i zapisuje jako PNG — bez zewnętrznych bibliotek
(na tej maszynie nie ma ani Pillow, ani pyarrow dla obrazów).

    python3 zrob_ikony.py marysia    -> icon-180/192/512.png        (niebieska)
    python3 zrob_ikony.py janek      -> icon-janek-180/192/512.png  (zielona)

Dwa kolory po to, żeby dało się odróżnić obie aplikacje na jednym telefonie.
"""
import struct
import sys
import zlib

SS = 3  # nadpróbkowanie: rysujemy 3x większe i uśredniamy, żeby krawędzie były gładkie

MOTYWY = {
    "marysia": {
        "plik": "icon-{}.png",
        "nadwozie": (255, 255, 255),
        "pas": (0x1d, 0x4e, 0xd8),
        "szyby": (0x38, 0xbd, 0xf8),
        "tlo": ((0x14, 0x24, 0x52), (0x2c, 0x5e, 0xb4)),
    },
    "janek": {
        "plik": "icon-janek-{}.png",
        "nadwozie": (0xec, 0xfd, 0xf5),
        "pas": (0x04, 0x78, 0x57),
        "szyby": (0x34, 0xd3, 0x99),
        "tlo": ((0x0a, 0x2e, 0x22), (0x1a, 0x63, 0x4a)),
    },
}

CIEMNY = (0x0f, 0x17, 0x2a)
SZARY = (0x94, 0xa3, 0xb8)
BURSZTYN = (0xfb, 0xbf, 0x24)


def zaokraglony(x, y, w, h, r):
    x2, y2 = x + w, y + h
    def wewnatrz(px, py):
        if x <= px <= x2 and y + r <= py <= y2 - r: return True
        if x + r <= px <= x2 - r and y <= py <= y2: return True
        cx = min(max(px, x + r), x2 - r)
        cy = min(max(py, y + r), y2 - r)
        return (px - cx) ** 2 + (py - cy) ** 2 <= r * r
    return wewnatrz


def kolo(cx, cy, r):
    return lambda px, py: (px - cx) ** 2 + (py - cy) ** 2 <= r * r


def rysuj(rozmiar, motyw):
    S = rozmiar * SS
    nadwozie = zaokraglony(0.20 * S, 0.19 * S, 0.60 * S, 0.50 * S, 0.10 * S)
    szyby = [zaokraglony((0.255 + i * 0.175) * S, 0.355 * S, 0.135 * S, 0.155 * S, 0.030 * S)
             for i in range(3)]
    pas = zaokraglony(0.20 * S, 0.575 * S, 0.60 * S, 0.045 * S, 0.02 * S)
    kola = [kolo(0.335 * S, 0.735 * S, 0.078 * S), kolo(0.665 * S, 0.735 * S, 0.078 * S)]
    piasty = [kolo(0.335 * S, 0.735 * S, 0.032 * S), kolo(0.665 * S, 0.735 * S, 0.032 * S)]
    swiatla = [kolo(0.265 * S, 0.655 * S, 0.026 * S), kolo(0.735 * S, 0.655 * S, 0.026 * S)]
    (t0, t1) = motyw["tlo"]

    def kolor(px, py):
        for k in kola:
            if k(px, py):
                return SZARY if any(h(px, py) for h in piasty) else CIEMNY
        if nadwozie(px, py):
            if any(s(px, py) for s in swiatla): return BURSZTYN
            if pas(px, py): return motyw["pas"]
            if any(s(px, py) for s in szyby): return motyw["szyby"]
            return motyw["nadwozie"]
        t = py / S
        return tuple(int(a + t * (b - a)) for a, b in zip(t0, t1))

    wiersze = []
    for y in range(rozmiar):
        w = bytearray()
        for x in range(rozmiar):
            r = g = b = 0
            for sy in range(SS):
                for sx in range(SS):
                    c = kolor(x * SS + sx + 0.5, y * SS + sy + 0.5)
                    r += c[0]; g += c[1]; b += c[2]
            n = SS * SS
            w += bytes((r // n, g // n, b // n))
        wiersze.append(bytes(w))
    return wiersze


def zapisz_png(sciezka, rozmiar, wiersze):
    surowe = b"".join(b"\x00" + w for w in wiersze)
    def kawalek(tag, dane):
        return (struct.pack(">I", len(dane)) + tag + dane
                + struct.pack(">I", zlib.crc32(tag + dane) & 0xffffffff))
    png = (b"\x89PNG\r\n\x1a\n"
           + kawalek(b"IHDR", struct.pack(">IIBBBBB", rozmiar, rozmiar, 8, 2, 0, 0, 0))
           + kawalek(b"IDAT", zlib.compress(surowe, 9))
           + kawalek(b"IEND", b""))
    with open(sciezka, "wb") as f:
        f.write(png)
    return len(png)


if __name__ == "__main__":
    kto = sys.argv[1] if len(sys.argv) > 1 else "marysia"
    if kto not in MOTYWY:
        raise SystemExit(f"nieznany motyw {kto!r}; dostępne: {', '.join(MOTYWY)}")
    motyw = MOTYWY[kto]
    for rozmiar in (180, 192, 512):
        nazwa = motyw["plik"].format(rozmiar)
        n = zapisz_png(nazwa, rozmiar, rysuj(rozmiar, motyw))
        print(f"{nazwa}  {n} B")
