# Mój autobus — strona dla dziecka

Strona pokazuje jeden ekran: która linia, gdzie dziecko jest, dokąd jedzie,
o której odjeżdża najbliższy autobus i za ile minut.

```
        Autobus R3                      Jest sobota

      Jesteś w domu             Dziś nie idziesz do szkoły!
    Jedziesz do szkoły

  Następny autobus o godzinie
           07:11

    Autobus za 11 minut
        Wyjdź o 07:01
```

Kolor napisu „Autobus za…" zmienia się sam: zielony = spokojnie, pomarańczowy = zbieraj się,
czerwony = wyjdź natychmiast (liczone z czasu dojścia do przystanku).

W soboty, niedziele i święta (także ruchome — Wielkanoc, Boże Ciało) pokazuje się
ekran po prawej. W święto wypadające w dzień powszedni napis brzmi „Dziś jest święto".
Gdy autobusów danego dnia już nie ma, zamiast bezużytecznego „za 43 godziny"
pojawia się „Dziś autobus już nie jeździ" i godzina najbliższego kursu w kolejnym dniu.

## Wpisane dane

| | Dom | Szkoła |
|---|---|---|
| Przystanek | Widokowa 02 | Szkoła Łady 01 |
| Współrzędne | 52.139126, 20.942015 | 52.127140, 20.961425 |
| Promień | 300 m | 300 m |
| Dojście | 10 min | 2 min |
| Kursy (dni robocze) | 14 | 14 |
| Weekendy | brak kursów | brak kursów |

Odległość dom ↔ szkoła to 1879 m, więc promienie 300 m nie zachodzą na siebie.

## Pliki

| Plik | Do czego |
|---|---|
| `index.html` | cała aplikacja — ekran, rozkład, logika, ustawienia |
| `sw.js` | pozwala uruchomić stronę bez internetu |
| `manifest.webmanifest` | ikona i tryb pełnoekranowy po dodaniu do ekranu głównego |
| `icon-*.png` | ikony |

## 1. Wpisz swoje dane

**Zalecane:** otwórz `index.html` w edytorze i podmień blok `DEFAULT_CONFIG` (na samej górze skryptu).
Dane wbudowane w plik działają od razu na każdym telefonie — nic nie trzeba konfigurować po instalacji.

```js
{
  id: "dom", name: "Dom", emoji: "🏠",
  inPlace: "Jesteś w domu",        // napis nr 1
  goingTo: "Jedziesz do szkoły",   // napis nr 2
  lat: 52.2297, lon: 21.0122,      // współrzędne domu
  radius: 300,                     // ile metrów wokół liczy się jako „dom”
  walk: 4,                         // minut dojścia do przystanku
  stop: "Przystanek przy domu",    // drobny napis na dole ekranu
  lines: [
    { number: "R3", direction: "",
      weekday:  ["06:52","07:12", ...],   // dni robocze
      saturday: ["07:20", ...],
      sunday:   ["08:40", ...] }          // niedziele i święta
  ]
}
```

Godziny po północy zapisuj jako `24:15`, `25:00`.
Święta państwowe (także ruchome: Wielkanoc, Boże Ciało) są rozpoznawane automatycznie
i traktowane jak niedziela.

**Nie znasz współrzędnych?** Otwórz stronę, naciśnij ⚙ i przy każdym miejscu użyj
przycisku „📍 Użyj mojej obecnej lokalizacji" — trzeba przy tym stać w domu / przy szkole.
Potem przepisz liczby do `DEFAULT_CONFIG`.

## 2. Wrzuć na hosting z HTTPS

Geolokalizacja **nie działa** z pliku na dysku (`file://`) — przeglądarka jej nie udostępni.
Potrzebny jest adres `https://`. Najprościej GitHub Pages (darmowy):

1. Załóż repozytorium na github.com, np. `autobus`.
2. Wrzuć do niego wszystkie pliki z tego katalogu (przeciągnij je w „Add file → Upload files").
3. `Settings` → `Pages` → Source: `Deploy from a branch`, Branch: `main`, folder `/ (root)` → `Save`.
4. Po 1–2 minutach strona jest pod `https://TWOJA-NAZWA.github.io/autobus/`.

> Adres jest publiczny. Nie umieszczaj w konfiguracji dokładnego adresu domu jako tekstu —
> same współrzędne w kodzie strony też są widoczne dla każdego, kto zna link.
> Jeśli to problem, lepszy będzie hosting z hasłem albo prywatny serwer.

## 3. Dodaj na ekran główny iPhone'a

Na telefonie dziecka, **w Safari** (nie w Chrome — tylko Safari potrafi dodać do ekranu głównego):

1. Otwórz adres strony.
2. Przycisk „Udostępnij" (kwadrat ze strzałką) → **Dodaj do ekranu początkowego**.
3. Uruchom z ikony. Przy pierwszym starcie iPhone zapyta o dostęp do lokalizacji — **Zezwól**.

Od tej pory działa jak aplikacja: pełny ekran, własna ikona, otwiera się też bez internetu.

**Uwaga:** aplikacja z ekranu głównego ma własną, oddzielną pamięć — ustawienia zrobione
wcześniej w Safari **nie** przeniosą się do niej. Dlatego najlepiej wpisać rozkład
w `DEFAULT_CONFIG` przed wrzuceniem na hosting (punkt 1).

## 4. Zmiana rozkładu później

Dwa sposoby:

- **Trwale:** popraw `DEFAULT_CONFIG` w `index.html`, wrzuć plik na GitHub jeszcze raz,
  podnieś `CACHE = "autobus-v1"` w `sw.js` na `v2` (inaczej telefon pokaże starą wersję z pamięci).
- **Doraźnie, na jednym telefonie:** ⚙ w rogu ekranu → popraw → „Zapisz".
  Przycisk „🔗 Skopiuj link z tą konfiguracją" tworzy adres zawierający cały rozkład —
  po otwarciu go na innym telefonie ustawienia przeniosą się tam same.

## Gdy GPS nie działa

Jeśli lokalizacja jest niedostępna albo dziecko jest gdzieś indziej, na ekranie pojawiają się
dwa duże przyciski — „🏠 Dom" i „🎒 Szkoła" — do ręcznego wyboru przystanku.

## Test na komputerze

```bash
cd ~/autobus-dziecka && python3 -m http.server 8777
```

Otwórz `http://127.0.0.1:8777/` — `localhost` liczy się jako połączenie bezpieczne,
więc geolokalizacja tu zadziała.
