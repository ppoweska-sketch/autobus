# Mój autobus — strona dla dzieci

Trzy osobne strony: Marysia, Alicja i Janek. **Rozkład linii jest wspólny** —
różnią się tylko plan lekcji i przystanek, z którego dziecko wsiada. Każde dziecko widzi jeden ekran: która linia,
gdzie jest, dokąd jedzie, o której odjeżdża najbliższy autobus i o której będzie w szkole.

```
        Autobus R3                      Jest niedziela
      Jesteś w domu               Dziś autobus nie jeździ!
    Jedziesz do szkoły

  Następny autobus o godzinie
           07:11
    Autobus za 11 minut
  Będziesz w szkole o 07:34
        Wyjdź o 06:56
```

Kolor napisu „Autobus za…" zmienia się sam: zielony = spokojnie, pomarańczowy = zbieraj się,
czerwony = wyjdź natychmiast. W soboty działa rozkład sobotni, w niedziele i święta
(także ruchome) pokazuje się ekran po prawej.

Pod ikoną 📅 w lewym górnym rogu jest **plan całego tygodnia** z podświetlonym dziś.

## Pliki

| Plik | Do czego |
|---|---|
| `autobus.js` | **cała logika + rozkład + plany lekcji obojga dzieci** — tu się zmienia dane |
| `autobus.css` | wygląd, wspólny |
| `marysia.html`, `alicja.html`, `janek.html` | cienkie strony: ustawiają, czyje to, i wczytują resztę |
| `index.html` | ekran wyboru dziecka, zapamiętuje wybór |
| `manifest-*.webmanifest` | osobna ikona i nazwa dla każdego dziecka |
| `icon-*.png` | niebieskie = Marysia, fioletowe = Alicja, zielone = Janek |
| `sw.js` | praca bez internetu i samoaktualizacja |
| `plan_tygodnia_pdf.py` | generuje PDF z planem tygodnia |
| `zrob_ikony.py` | rysuje ikony (bez zewnętrznych bibliotek) |

Kod jest w jednym miejscu celowo: gdyby każde dziecko miało własną kopię całej
aplikacji, zmiana rozkładu wymagałaby dwóch edycji i prędzej czy później
któraś by się nie zgadzała.

## Wpisane dane

### Dwie linie, nie jedna

Od 06.09 aplikacja wybiera między **R3** a **gimbusem** (rozkład SP Łady, gmina Raszyn):

| Kurs | Przystanek | Kto | Dojście | Kursy |
|---|---|---|---|---|
| R3 | Widokowa 02 | Marysia, Janek | 15 min | 14 dz. rob. + 4 sob. |
| R3 | Podolszyn Nowy 02 | Alicja | 5 min | jw., 14 min później |
| Gimbus | Limby | wszyscy | 15 min | 2 rano, 4 po lekcjach |

**Reguła wyboru:** rano ten kurs, przy którym można wyjść z domu **najpóźniej**
(a nie ten, który dowozi najbliżej dzwonka — przy dwóch przystankach o różnym
czasie dojścia to nie to samo). Po lekcjach — **najkrótsze czekanie**.

Wszystkie 6 kursów gimbusa mija Widokową i Limby w odstępie minuty; sprawdzone
w rozkładzie gminy, kursów obsługujących tylko jeden z tych przystanków nie ma.
Wybrane **Limby** — lepsze dojście, a odjazd o minutę późniejszy niż z Widokowej.
Gimbus wysadza pod szkołą (0 min dojścia) i stamtąd też odjeżdża.

**Gimbus wraca różnymi trasami — to nie jest jedna linia.** Sprawdzone w rozkładzie:

| Odjazd ze szkoły | Limby | Podolszyn Nowy | Pętla Podolszyn |
|---|---|---|---|
| 12:25 | 12:44 | **12:26** | 12:28 |
| 13:20 | 13:30 | — | 13:38 |
| 14:36 | — | — | 14:39 |
| 15:15 | 15:17 | — | 15:26 |
| 16:05 | 16:07 | — | 16:18 |

Limby obsługują wszystkie kursy, **Podolszyn Nowy tylko ten o 12:25**. Dlatego Alicja
korzysta z obu przystanków w Podolszynie, a ekran **zawsze pisze, na który wysiada**
(„Wysiadasz: Pętla Podolszyn o 13:38") — bez tego dziecko wysiadłoby nie tam.
R3 wraca ze szkoły równo **+13 min** na Widokową 01 i **+2 min** na Podolszyn Nowy 01
(także w soboty). Dzięki temu powrót wybierany jest po **godzinie dotarcia do domu**,
nie po samym odjeździe — gimbus bywa wolniejszy albo wysadza dalej.

Przy każdym kursie gimbusa jest **numer autobusu z rozkładu gminy** (nr 1, 2 lub 3),
bo o tej samej porze spod szkoły potrafią ruszać różne autobusy w różne strony.

**Janek nie wraca gimbusem przed 15:00** (`powrotGimbusOd` w jego wpisie) — kursy 12:25
i 13:20 są dla niego odsiewane, więc w środę wraca R3 o 13:42. Reguła działa w aplikacji
i w skrypcie PDF; przy dodawaniu podobnych ograniczeń trzeba poprawić **oba**, inaczej
telefon i wydruk pokażą inny kurs. Raz już tak było.

Podolszyn Nowy 02 leży **14 minut za Widokową 02 na tej samej trasie tego samego
kursu** — dlatego godziny przyjazdu do szkoły są wspólne dla wszystkich dzieci
i trzymane w jednym miejscu (`PRZYJAZDY_DO_SZKOLY`). Kto wsiada później, ten
krócej jedzie; do szkoły docierają o tej samej godzinie.

### Domy

Dzieci **nie mieszkają razem** — Alicja ma inny adres (blok `DOMY` w `autobus.js`):

| Dom | Kto | Współrzędne |
|---|---|---|
| Falenty Nowe | Marysia, Janek | 52.139126, 20.942015 |
| Podolszyn | Alicja | 52.122500, 20.944778 |

Miało to znaczenie: dopóki Alicja miała wpisany dom rodzeństwa, stojąc u siebie była
1858 m od „domu" i tylko 1248 m od szkoły — aplikacja uznawała, że **jest już w szkole**
i rano pokazywała jej rozkład powrotny.

### Szkoła

| | |
|---|---|
| Przystanek | Łady – Szkoła 01 (powrót), 02 (przyjazd) |
| Współrzędne | 52.127140, 20.961425 |
| Dojście | 2 min na przystanek, 5 min z przystanku do szkoły |
| Kursy | 14 w dni robocze, 4 w soboty, w niedziele i święta nie jeździ |

Odległość dom ↔ szkoła to 1879 m, więc promienie 300 m nie zachodzą na siebie.

### Dwa słupki przy szkole — i dlaczego oba są potrzebne

R3 jeździ pętlą i wraca tą samą trasą, więc przy szkole są dwa słupki o różnym
przeznaczeniu. Oba mają idealnie stałe przesunięcie względem odjazdu spod domu:

| Słupek | Rola | Przesunięcie |
|---|---|---|
| **Łady – Szkoła 02** | przyjazd — tu dziecko wysiada rano | **+18 min** |
| **Łady – Szkoła 01** | odjazd — stąd wraca do domu | **+25 min** |

> **Kontrola przy wpisywaniu nowych godzin:** jeśli któreś przesunięcie przestanie być
> stałe, rozkład prawie na pewno pochodzi z niewłaściwego słupka. Skrypt PDF sprawdza
> to sam i przerywa. Ta reguła już raz uratowała pomiar.

## Plan lekcji

W `autobus.js`, blok `PLANY_LEKCJI`. Klucz to dzień tygodnia (1 = poniedziałek):

```js
const DZIECI = {
  marysia: { imie: "Marysia", przystanek: "widokowa",   lekcje: LEKCJE_MARYSI },
  alicja:  { imie: "Alicja",  przystanek: "podolszyn", lekcje: LEKCJE_MARYSI },
  janek:   { imie: "Janek",   przystanek: "widokowa",   lekcje: { ... } }
};
```

**Alicja i Marysia dzielą jeden obiekt planu** (`LEKCJE_MARYSI`) — zmiana u jednej
zmienia u obu. Gdy ich plany się rozejdą, trzeba zrobić Alicji własny obiekt.

Autobusy dobierają się z tego same, dwiema regułami: **rano** ostatni kurs, który
dowozi przed dzwonkiem; **po lekcjach** pierwszy, na który da się dojść.

## Zmiana rozkładu albo planu lekcji

Popraw `autobus.js` i podnieś **dwa numery**:

- `version:` w `DEFAULT_CONFIG` — bez tego telefon z własną zapisaną kopią
  (ktoś nacisnął „Zapisz" w ⚙) zignoruje zmianę na zawsze;
- `CACHE = "autobus-vN"` w `sw.js` — bez tego telefon weźmie stary plik z pamięci.

Po zmianie uruchom **`./sprawdz_wersje.sh`** — pilnuje, żeby oba numery były równe.
Raz `sw.js` utknął na v18, gdy konfiguracja była już na v22: podmiana tekstu nie
znalazła szukanego wzorca i cicho nic nie zrobiła. Na ekranie tego nie widać.

Potem `git push`. Publikacja trwa 1–2 minuty (zakładka **Actions** w repozytorium).
Aplikacja na telefonie sama się przeładuje — sprawdza przy starcie i raz na godzinę.

### Jak sprawdzić, czy telefon ma aktualną wersję

Na dole ekranu, w szarej linijce, jest imię i numer: `… · Alicja · v8`. Numer musi się
zgadzać z `version:` w `autobus.js`. Jeśli jest mniejszy, telefon ma starą kopię.

To nie ozdobnik: raz już zniknęła przez to cała funkcja — kod był poprawny i wgrany,
ale telefon go nie widział, a z samego ekranu nie dało się tego odróżnić od błędu.

## Instalacja na telefonie dziecka

W **Safari** (tylko Safari potrafi dodać do ekranu głównego):

1. Otwórz adres **swojego** dziecka:
   `.../autobus/marysia.html`, `.../autobus/alicja.html` albo `.../autobus/janek.html`
2. Udostępnij → **Dodaj do ekranu początkowego**
3. Uruchom z ikony, przy pierwszym starcie **Zezwól** na lokalizację

Adres główny (`/autobus/`) pokazuje ekran wyboru i zapamiętuje go, więc aplikacja
dodana wcześniej pod starym adresem nadal działa. Żeby zmienić wybór, otwórz
`https://ppoweska-sketch.github.io/autobus/?wybierz`.

## Gdy GPS nie działa

Jeśli lokalizacja jest niedostępna albo dziecko jest gdzie indziej, pojawiają się
dwa duże przyciski — „🏠 Dom" i „🎒 Szkoła" — do ręcznego wyboru przystanku.

## Test na komputerze

```bash
cd ~/autobus-dziecka && python3 -m http.server 8777
```

Otwórz `http://127.0.0.1:8777/` — `localhost` liczy się jako połączenie bezpieczne,
więc geolokalizacja tu zadziała.

## PDF z planem tygodnia

```bash
cd ~/autobus-dziecka && "../claude trading bot/.venv/bin/python" plan_tygodnia_pdf.py janek
```

Godziny czyta z `autobus.js`, więc PDF nie może rozjechać się z aplikacją.
