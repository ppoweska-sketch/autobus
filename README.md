# Mój autobus — strona dla dzieci

Dwie osobne strony, jedna dla Marysi i jedna dla Janka. **Rozkład autobusu jest
wspólny, różni się tylko plan lekcji.** Każde dziecko widzi jeden ekran: która linia,
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
| `marysia.html`, `janek.html` | cienkie strony: ustawiają, czyje to, i wczytują resztę |
| `index.html` | ekran wyboru „Marysia czy Janek", zapamiętuje wybór |
| `manifest-*.webmanifest` | osobna ikona i nazwa dla każdego dziecka |
| `icon-*.png` | niebieskie = Marysia, zielone = Janek |
| `sw.js` | praca bez internetu i samoaktualizacja |
| `plan_tygodnia_pdf.py` | generuje PDF z planem tygodnia |
| `zrob_ikony.py` | rysuje ikony (bez zewnętrznych bibliotek) |

Kod jest w jednym miejscu celowo: gdyby każde dziecko miało własną kopię całej
aplikacji, zmiana rozkładu wymagałaby dwóch edycji i prędzej czy później
któraś by się nie zgadzała.

## Wpisane dane

| | Dom | Szkoła |
|---|---|---|
| Przystanek | Widokowa 02 | Łady – Szkoła 01 (powrót), 02 (przyjazd) |
| Współrzędne | 52.139126, 20.942015 | 52.127140, 20.961425 |
| Promień | 300 m | 300 m |
| Dojście | 15 min | 2 min na przystanek, 5 min z przystanku do szkoły |
| Kursy w dni robocze | 14 | 14 |
| Kursy w soboty | 4 | 4 |
| Niedziele i święta | nie jeździ | nie jeździ |

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
janek: {
  imie: "Janek",
  1: { start: "07:45", koniec: "11:05" },
  ...
}
```

Autobusy dobierają się z tego same, dwiema regułami: **rano** ostatni kurs, który
dowozi przed dzwonkiem; **po lekcjach** pierwszy, na który da się dojść.

## Zmiana rozkładu albo planu lekcji

Popraw `autobus.js` i podnieś **dwa numery**:

- `version:` w `DEFAULT_CONFIG` — bez tego telefon z własną zapisaną kopią
  (ktoś nacisnął „Zapisz" w ⚙) zignoruje zmianę na zawsze;
- `CACHE = "autobus-vN"` w `sw.js` — bez tego telefon weźmie stary plik z pamięci.

Potem `git push`. Publikacja trwa 1–2 minuty (zakładka **Actions** w repozytorium).
Aplikacja na telefonie sama się przeładuje — sprawdza przy starcie i raz na godzinę.

### Jak sprawdzić, czy telefon ma aktualną wersję

Na dole ekranu, w szarej linijce, jest imię i numer: `… · Janek · v7`. Numer musi się
zgadzać z `version:` w `autobus.js`. Jeśli jest mniejszy, telefon ma starą kopię.

To nie ozdobnik: raz już zniknęła przez to cała funkcja — kod był poprawny i wgrany,
ale telefon go nie widział, a z samego ekranu nie dało się tego odróżnić od błędu.

## Instalacja na telefonie dziecka

W **Safari** (tylko Safari potrafi dodać do ekranu głównego):

1. Otwórz adres **swojego** dziecka:
   `https://ppoweska-sketch.github.io/autobus/marysia.html`
   albo `.../janek.html`
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
