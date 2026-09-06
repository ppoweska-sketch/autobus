"use strict";

/* =======================================================================
   DOMYŚLNA KONFIGURACJA  —  podmień na własne dane (albo edytuj w ⚙)
   ======================================================================= */
/* Które dziecko — ustawia to plik HTML (marysia.html / janek.html / alicja.html)
   przed wczytaniem tego skryptu. */
const DZIECKO = (window.DZIECKO || "marysia").toLowerCase();

/* ---------------------------------------------------------------------
   PRZYSTANKI DOMOWE
   Podoluszyn Nowy 02 leży 14 min ZA Widokową 02 na tej samej trasie tego
   samego kursu — dlatego godziny przyjazdu do szkoły (niżej) są wspólne.
   --------------------------------------------------------------------- */
const PRZYSTANKI_DOMOWE = {
  widokowa: {
    stop: "Widokowa 02",
    walk: 15,                        // minut dojścia z domu na przystanek
    weekday:  ["05:36","06:16","07:11","08:01","08:56","09:46",
               "10:51","11:56","13:17","14:12","15:12","16:06","17:14","17:54"],
    saturday: ["08:46","10:46","13:46","15:46"]
  },
  podoluszyn: {
    stop: "Podoluszyn Nowy 02",
    walk: 5,
    weekday:  ["05:50","06:30","07:25","08:15","09:10","10:00",
               "11:05","12:10","13:31","14:26","15:26","16:20","17:28","18:08"],
    saturday: ["09:00","11:00","14:00","16:00"]
  }
};

/* Godziny PRZYJAZDU na Łady – Szkoła 02. Wspólne dla wszystkich przystanków
   domowych, bo to ten sam autobus — zmienia się tylko miejsce wsiadania. */
const PRZYJAZDY_DO_SZKOLY = {
  weekday:  ["05:54","06:34","07:29","08:19","09:14","10:04",
             "11:09","12:14","13:35","14:30","15:30","16:24","17:32","18:12"],
  saturday: ["09:04","11:04","14:04","16:04"],
  sunday:   []
};

/* Dzieci: imię, z którego przystanku jeżdżą i ich plan lekcji.
   Klucz planu to dzień tygodnia: 1 = poniedziałek … 5 = piątek. */
const LEKCJE_MARYSI = {          // wspólny dla Marysi i Alicji
  1: { start: "07:45", koniec: "13:05" },
  2: { start: "07:45", koniec: "13:05" },
  3: { start: "11:20", koniec: "15:55" },
  4: { start: "11:20", koniec: "15:55" },
  5: { start: "10:20", koniec: "15:55" }
};

const DZIECI = {
  marysia: { imie: "Marysia", przystanek: "widokowa",   lekcje: LEKCJE_MARYSI },
  alicja:  { imie: "Alicja",  przystanek: "podoluszyn", lekcje: LEKCJE_MARYSI },
  janek:   { imie: "Janek",   przystanek: "widokowa", lekcje: {
    1: { start: "07:45", koniec: "11:05" },
    2: { start: "07:45", koniec: "11:05" },
    3: { start: "07:45", koniec: "13:05" },
    4: { start: "09:30", koniec: "14:05" },
    5: { start: "11:20", koniec: "15:05" }
  } }
};

const PROFIL = DZIECI[DZIECKO] || DZIECI.marysia;
const IMIE = PROFIL.imie;
const PRZYSTANEK = PRZYSTANKI_DOMOWE[PROFIL.przystanek];

const DEFAULT_CONFIG = {
  // PODNIEŚ przy każdej zmianie rozkładu albo planu lekcji.
  version: 10,

  lekcje: PROFIL.lekcje,

  places: [
    {
      id: "dom", name: "Dom", emoji: "🏠",
      inPlace: "Jesteś w domu",
      goingTo: "Jedziesz do szkoły",
      lat: 52.139126, lon: 20.942015,  // ← współrzędne domu
      radius: 300,
      walk: PRZYSTANEK.walk,
      stop: PRZYSTANEK.stop,
      arriveLabel: "Będziesz w szkole o",
      arriveWalk: 5,                   // minut z przystanku Łady – Szkoła 02 do szkoły
      lines: [
        { number: "R3", direction: "",
          weekday:  PRZYSTANEK.weekday,
          saturday: PRZYSTANEK.saturday,
          sunday:   [],
          arrivals: PRZYJAZDY_DO_SZKOLY }
      ]
    },
    {
      id: "szkola", name: "Szkoła", emoji: "🎒",
      inPlace: "Jesteś w szkole",
      goingTo: "Jedziesz do domu",
      lat: 52.127140, lon: 20.961425,  // ← współrzędne szkoły
      radius: 300,
      walk: 2,
      stop: "Łady – Szkoła 01",
      lines: [
        { number: "R3", direction: "",
          weekday:  ["06:01","06:41","07:36","08:26","09:21","10:11",
                     "11:16","12:21","13:42","14:37","15:37","16:31","17:39","18:19"],
          saturday: ["09:11","11:11","14:11","16:11"],
          sunday:   [] }
      ]
    }
  ]
};

/* Widoczny znacznik wersji — pozwala sprawdzić, czy telefon ma aktualny plik. */
const WERSJA = " · " + IMIE + " · v" + DEFAULT_CONFIG.version;

/* Szkielet ekranu wstrzykiwany z kodu — dzięki temu marysia.html i janek.html
   są cienkie i nie trzeba poprawiać układu w dwóch miejscach. */
document.getElementById("app").innerHTML = `
  <button id="gear" aria-label="Ustawienia">⚙</button>
  <button id="kalendarz" aria-label="Plan tygodnia">📅</button>
  <div id="banner" class="banner hidden"></div>
  <div id="switch" class="switch hidden"></div>
  <main id="main" class="main">
    <div id="lineTitle">Autobus</div>
    <div id="whereAmI"></div>
    <div id="goingTo"></div>
    <div id="atLabel">Następny autobus o godzinie</div>
    <div id="at"></div>
    <div id="count"></div>
    <div id="arrive"></div>
    <div id="leave"></div>
  </main>
  <footer id="foot"></footer>`;

/* ============================ narzędzia ============================ */
const $ = (s, r = document) => r.querySelector(s);
const pad = n => String(n).padStart(2, "0");
const hhmm = d => pad(d.getHours()) + ":" + pad(d.getMinutes());

function b64enc(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = ""; for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64dec(s) {
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/"));
  return new TextDecoder().decode(Uint8Array.from(bin, c => c.charCodeAt(0)));
}

/* Odległość w metrach (haversine) */
function distance(lat1, lon1, lat2, lon2) {
  const R = 6371000, rad = Math.PI / 180;
  const dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

/* Wielkanoc (algorytm Meeusa/Jonesa/Butchera) */
function easter(year) {
  const a = year % 19, b = Math.floor(year / 100), c = year % 100;
  const d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(year, month - 1, day);
}

const holidayCache = {};
function holidays(year) {
  if (holidayCache[year]) return holidayCache[year];
  const set = new Set(["01-01", "01-06", "05-01", "05-03", "08-15", "11-01", "11-11", "12-25", "12-26"]);
  const e = easter(year);
  for (const offset of [1, 49, 50, 60]) {          // pon. wielkanocny, Zesłanie Ducha Św. + pon., Boże Ciało
    const d = new Date(e); d.setDate(d.getDate() + offset);
    set.add(pad(d.getMonth() + 1) + "-" + pad(d.getDate()));
  }
  set.add(pad(e.getMonth() + 1) + "-" + pad(e.getDate()));
  return (holidayCache[year] = set);
}

/* Który rozkład obowiązuje danego dnia */
function dayType(date) {
  const key = pad(date.getMonth() + 1) + "-" + pad(date.getDate());
  if (holidays(date.getFullYear()).has(key)) return "sunday";
  const d = date.getDay();
  if (d === 0) return "sunday";
  if (d === 6) return "saturday";
  return "weekday";
}

/* Pierwszy przyjazd późniejszy niż dany odjazd. Zwraca Date albo null. */
function pierwszyPrzyjazdPo(line, type, base, minutyOdjazdu) {
  let najlepsze = null;
  for (const raw of line.arrivals?.[type] || []) {
    const m = /^\s*(\d{1,2})[:.](\d{2})\s*$/.exec(raw);
    if (!m) continue;
    const minuty = Number(m[1]) * 60 + Number(m[2]);
    if (minuty <= minutyOdjazdu) continue;
    if (najlepsze === null || minuty < najlepsze) najlepsze = minuty;
  }
  if (najlepsze === null) return null;
  const d = new Date(base);
  d.setHours(0, najlepsze, 0, 0);
  return d;
}

/* Najbliższe odjazdy z danego miejsca */
function nextDepartures(place, now, count) {
  const out = [];
  for (let offset = 0; offset < 4 && out.length < count; offset++) {
    const base = new Date(now);
    base.setDate(base.getDate() + offset);
    base.setHours(0, 0, 0, 0);
    const type = dayType(base);
    const found = [];
    for (const line of place.lines || []) {
      for (const raw of line[type] || []) {
        const m = /^\s*(\d{1,2})[:.](\d{2})\s*$/.exec(raw);
        if (!m) continue;
        const minutyOdjazdu = Number(m[1]) * 60 + Number(m[2]);
        const when = new Date(base);
        when.setHours(0, minutyOdjazdu, 0, 0);                      // obsługuje też 24:15, 25:00
        if (when.getTime() < now.getTime() - 30000) continue;
        // Przyjazd dopasowujemy po godzinie, nie po pozycji w liście — dzięki temu
        // ręczna edycja jednej z list nie rozjeżdża par odjazd/przyjazd.
        found.push({ line, when, arrive: pierwszyPrzyjazdPo(line, type, base, minutyOdjazdu) });
      }
    }
    found.sort((a, b) => a.when - b.when);
    out.push(...found);
  }
  out.sort((a, b) => a.when - b.when);
  return out.slice(0, count);
}

function minutesUntil(when, now) {
  return Math.floor((when.getTime() - now.getTime()) / 60000);
}
/* Polska odmiana: 1 minutę, 2–4 minuty, 5+ minut (z wyjątkiem 12–14) */
function plural(n, one, few, many) {
  if (n === 1) return one;
  const d = n % 10, h = n % 100;
  return (d >= 2 && d <= 4 && !(h >= 12 && h <= 14)) ? few : many;
}
function minutesWord(m) {
  if (m < 60) return m + " " + plural(m, "minutę", "minuty", "minut");
  const h = Math.floor(m / 60), r = m % 60;
  const hs = h + " " + plural(h, "godzinę", "godziny", "godzin");
  return r ? hs + " " + r + " " + plural(r, "minutę", "minuty", "minut") : hs;
}
/* "jutro", "w środę", "we wtorek" */
function dayPhrase(when) {
  const jutro = new Date(); jutro.setDate(jutro.getDate() + 1);
  if (when.toDateString() === jutro.toDateString()) return "jutro";
  const dni = ["w niedzielę", "w poniedziałek", "we wtorek", "w środę",
               "w czwartek", "w piątek", "w sobotę"];
  return dni[when.getDay()];
}

/* ============================ konfiguracja ============================ */
const STORAGE_KEY = "autobus.config." + DZIECKO;   // osobna pamięć na dziecko
let config, manualPlaceId = null, position = null, positionError = null;

/* Ekran odświeża się co sekundę, ale DOM przebudowujemy tylko gdy treść naprawdę
   się zmieniła — inaczej element znika między dotknięciem a puszczeniem palca
   i kliknięcia przepadają. */
const sigs = {};
function changed(key, value) {
  if (sigs[key] === value) return false;
  sigs[key] = value;
  return true;
}
function setText(sel, text) {
  if (changed("t:" + sel, text)) $(sel).textContent = text;
}
function setClass(sel, cls) {
  if (changed("c:" + sel, cls)) $(sel).className = cls;
}

function normalize(cfg) {
  const places = (cfg && Array.isArray(cfg.places) ? cfg.places : []).map((p, i) => ({
    id: p.id || "p" + i,
    name: p.name || "Miejsce",
    emoji: p.emoji || "📍",
    inPlace: p.inPlace || "Jesteś: " + (p.name || "Miejsce"),
    goingTo: p.goingTo || "",
    lat: Number(p.lat) || 0,
    lon: Number(p.lon) || 0,
    radius: Number(p.radius) > 0 ? Number(p.radius) : 300,
    walk: Number(p.walk) >= 0 ? Number(p.walk) : 0,
    stop: p.stop || "",
    arriveLabel: p.arriveLabel || "",
    arriveWalk: Number(p.arriveWalk) >= 0 ? Number(p.arriveWalk) : 0,
    lines: (Array.isArray(p.lines) ? p.lines : []).map(l => ({
      number: String(l.number ?? "?"),
      direction: l.direction || "",
      weekday: Array.isArray(l.weekday) ? l.weekday : [],
      saturday: Array.isArray(l.saturday) ? l.saturday : [],
      sunday: Array.isArray(l.sunday) ? l.sunday : [],
      arrivals: {
        weekday: Array.isArray(l.arrivals?.weekday) ? l.arrivals.weekday : [],
        saturday: Array.isArray(l.arrivals?.saturday) ? l.arrivals.saturday : [],
        sunday: Array.isArray(l.arrivals?.sunday) ? l.arrivals.sunday : []
      }
    }))
  }));
  const lekcje = {};
  for (const d of [1, 2, 3, 4, 5]) {
    const l = cfg?.lekcje?.[d];
    if (l && /^\d{1,2}:\d{2}$/.test(l.start || "") && /^\d{1,2}:\d{2}$/.test(l.koniec || "")) {
      lekcje[d] = { start: l.start, koniec: l.koniec };
    }
  }
  return {
    version: Number(cfg?.version) || 0,
    lekcje,
    places: places.length ? places : structuredClone(DEFAULT_CONFIG).places
  };
}

function loadConfig() {
  // 1) konfiguracja z linku (#c=...) — nadpisuje i zapisuje lokalnie
  if (location.hash.startsWith("#c=")) {
    try {
      const cfg = normalize(JSON.parse(b64dec(location.hash.slice(3))));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
      history.replaceState(null, "", location.pathname + location.search);
      return cfg;
    } catch (e) { console.warn("Zły link konfiguracyjny", e); }
  }
  // 2) zapisana lokalnie — ale tylko jeśli nie jest starsza niż ta wbudowana w plik
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const cfg = normalize(JSON.parse(saved));
      if (cfg.version >= (DEFAULT_CONFIG.version || 0)) return cfg;
      console.info("Zapisana konfiguracja v" + cfg.version + " jest starsza niż wbudowana v"
                   + DEFAULT_CONFIG.version + " — biorę nowszą.");
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch (e) { console.warn("Zła zapisana konfiguracja", e); }
  // 3) domyślna
  return normalize(structuredClone(DEFAULT_CONFIG));
}

function saveConfig(cfg) {
  config = normalize(cfg);
  config.version = DEFAULT_CONFIG.version || 0;   // ręczny zapis = wersja bieżąca
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(config)); }
  catch (e) { alert("Nie udało się zapisać: " + e.message); }
}

/* ============================ lokalizacja ============================ */
function startGeolocation() {
  if (!navigator.geolocation) { positionError = "brak-api"; return; }
  navigator.geolocation.watchPosition(
    p => { position = p; positionError = null; render(); },
    e => { positionError = e.code === e.PERMISSION_DENIED ? "odmowa" : "blad"; render(); },
    { enableHighAccuracy: true, maximumAge: 15000, timeout: 20000 }
  );
}

/* Gdzie jestem: dokładne trafienie w promień, inaczej najbliższe miejsce */
function resolvePlace() {
  if (manualPlaceId) {
    const p = config.places.find(x => x.id === manualPlaceId);
    if (p) return { place: p, mode: "manual" };
  }
  if (!position) return { place: null, mode: "nogps" };
  let best = null, bestDist = Infinity;
  for (const p of config.places) {
    const d = distance(position.coords.latitude, position.coords.longitude, p.lat, p.lon);
    if (d < bestDist) { bestDist = d; best = p; }
  }
  if (!best) return { place: null, mode: "nogps" };
  return { place: best, dist: bestDist, mode: bestDist <= best.radius ? "inside" : "outside" };
}

/* ============================ rysowanie ============================ */
function render() {
  if (!$("#settings").classList.contains("hidden")) return;   // ustawienia otwarte
  if (!$("#week").classList.contains("hidden")) return;       // plan tygodnia otwarty
  const now = new Date();

  // --- niedziela / święto: autobus nie jeździ, ekran nie zależy od lokalizacji ---
  const typDnia = dayType(now);
  const saKursyDzis = config.places.some(p =>
    (p.lines || []).some(l => (l[typDnia] || []).length));
  if (typDnia === "sunday" && !saKursyDzis) {
    if (changed("banner", "")) {
      $("#banner").innerHTML = ""; $("#banner").classList.add("hidden");
    }
    if (changed("switch", "wolne")) {
      $("#switch").innerHTML = ""; $("#switch").classList.add("hidden");
    }
    setText("#lineTitle", "Autobus " + ((config.places[0].lines[0] || {}).number || ""));
    setText("#whereAmI", "Dziś autobus nie jeździ!");
    setText("#goingTo", "");
    setText("#atLabel", "");
    setText("#at", "");
    setText("#count", "");
    setText("#arrive", "");
    setText("#leave", "");
    setClass("#main", "main wolne");
    setText("#foot", hhmm(now) + WERSJA);
    return;
  }

  const { place, mode, dist } = resolvePlace();

  // --- komunikaty ---
  let bannerHtml = "";
  if (positionError === "odmowa" && !position) {
    bannerHtml = "<b>Brak dostępu do lokalizacji.</b><br>Włącz go w Ustawieniach iPhone'a → Safari → Lokalizacja, albo wybierz miejsce ręcznie poniżej.";
  } else if (!position && (positionError === "brak-api" || !window.isSecureContext)) {
    bannerHtml = "<b>Lokalizacja niedostępna.</b><br>Strona musi być otwarta przez <b>https://</b>. Wybierz miejsce ręcznie poniżej.";
  } else if (mode === "outside" && place) {
    bannerHtml = "Nie jesteś ani w domu, ani w szkole. Pokazuję najbliższe miejsce: <b>" +
      esc(place.name) + "</b> (" + formatDist(dist) + " stąd).";
  }
  if (changed("banner", bannerHtml)) {
    $("#banner").innerHTML = bannerHtml;
    $("#banner").classList.toggle("hidden", !bannerHtml);
  }

  // --- ręczny przełącznik miejsc ---
  const sw = $("#switch");
  const showSwitch = mode !== "inside" && config.places.length > 1;
  if (changed("switch", showSwitch + "|" + manualPlaceId + "|" +
      config.places.map(p => p.id + p.emoji + p.name).join(","))) {
    sw.innerHTML = "";
    if (showSwitch) {
      for (const p of config.places) {
        const b = document.createElement("button");
        b.textContent = p.emoji + " " + p.name;
        if (manualPlaceId === p.id) b.className = "on";
        b.onclick = () => { manualPlaceId = manualPlaceId === p.id ? null : p.id; render(); };
        sw.appendChild(b);
      }
    }
    sw.classList.toggle("hidden", !showSwitch);
  }

  // --- zanim znamy miejsce ---
  if (!place) {
    setText("#lineTitle", "Autobus");
    setText("#whereAmI", positionError ? "Nie znam Twojej lokalizacji" : "Sprawdzam, gdzie jesteś…");
    setText("#goingTo", "");
    setText("#atLabel", "");
    setText("#at", "");
    setText("#count", "");
    setText("#arrive", "");
    setText("#leave", "");
    setClass("#main", "main");
    setText("#foot", hhmm(now) + WERSJA);
    return;
  }

  const deps = nextDepartures(place, now, 1);
  const d = deps[0];

  // 1. Autobus R3
  setText("#lineTitle", "Autobus " + (d ? d.line.number : (place.lines[0] || {}).number || ""));

  // 2. Jesteś w domu / w szkole
  setText("#whereAmI", mode === "inside" || mode === "manual"
    ? (place.inPlace || "Jesteś: " + place.name)
    : "Jesteś blisko: " + place.name);

  // 3. Jedziesz do szkoły / do domu
  setText("#goingTo", place.goingTo || "");

  if (!d) {
    setText("#atLabel", "");
    setText("#at", "Brak autobusów");
    setText("#count", "");
    setText("#arrive", "");
    setText("#leave", "Na dziś i najbliższe dni nie ma nic w rozkładzie.");
    setClass("#main", "main");
  } else {
    const mins = minutesUntil(d.when, now);
    const walk = place.walk || 0;
    const sameDay = d.when.toDateString() === now.toDateString();

    // 4. Następny autobus o godzinie 07:25
    setText("#atLabel", sameDay
      ? "Następny autobus o godzinie"
      : "Następny autobus " + dayPhrase(d.when) + " o godzinie");
    setText("#at", hhmm(d.when));

    // 5. Autobus za 7 minut
    if (!sameDay) {
      // odliczanie w stylu "za 43 godziny" nic dziecku nie mówi
      setText("#count", "Dziś autobus już nie jeździ");
      setClass("#main", "main");
    } else {
      setText("#count", mins <= 0 ? "Autobus odjeżdża TERAZ" : "Autobus za " + minutesWord(mins));
      setClass("#main", "main " + (mins <= walk ? "bad" : mins <= walk + 4 ? "warn" : "ok"));
    }

    // 6. Będziesz w szkole o 07:34  (przyjazd autobusu + dojście z przystanku)
    //    Pokazujemy TAKŻE dla kursu z następnego dnia — skoro wyżej piszemy
    //    "następny autobus w poniedziałek", to godzina przyjazdu dotyczy tego samego kursu.
    if (place.arriveLabel && d.arrive) {
      const naMiejscu = new Date(d.arrive.getTime() + (place.arriveWalk || 0) * 60000);
      setText("#arrive", place.arriveLabel + " " + hhmm(naMiejscu));
    } else {
      setText("#arrive", "");
    }

    setText("#leave", walk > 0 && sameDay
      ? (mins <= walk
          ? "Wyjdź TERAZ — dojście " + minutesWord(walk)
          : "Wyjdź o " + hhmm(new Date(d.when.getTime() - walk * 60000)))
      : "");
    $("#leave").classList.toggle("urgent", walk > 0 && mins <= walk);
  }

  // --- stopka ---
  const acc = position ? " · GPS ±" + Math.round(position.coords.accuracy) + " m" : "";
  setText("#foot", place.stop + " · " + hhmm(now) + " · " + dayLabel(now) + acc + WERSJA);
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function formatDist(m) {
  if (m == null) return "";
  return m < 1000 ? Math.round(m) + " m" : (m / 1000).toFixed(1) + " km";
}
function dayLabel(d) {
  return { weekday: "dzień roboczy", saturday: "sobota", sunday: "niedziela / święto" }[dayType(d)];
}

/* ======================= plan całego tygodnia ======================= */
const DNI_PL = { 1: "Poniedziałek", 2: "Wtorek", 3: "Środa", 4: "Czwartek", 5: "Piątek" };
const naMinuty = s => Number(s.slice(0, s.indexOf(":"))) * 60 + Number(s.slice(s.indexOf(":") + 1));
const naGodzine = t => pad(Math.floor(t / 60)) + ":" + pad(t % 60);

/* Dla jednego dnia: który kurs rano, który po lekcjach.
   Te same reguły co w PDF-ie — rano ostatni kurs zdążający przed dzwonkiem,
   po lekcjach pierwszy, na który da się dojść. */
function planDnia(dzien) {
  const l = config.lekcje?.[dzien];
  const dom = config.places.find(p => p.arriveLabel);
  const szkola = config.places.find(p => p !== dom);
  if (!l || !dom || !szkola) return null;

  const linia = dom.lines[0] || {};
  const powrotna = (szkola.lines[0] || {}).weekday || [];
  const start = naMinuty(l.start), koniec = naMinuty(l.koniec);

  let rano = null;
  (linia.weekday || []).forEach((o, i) => {
    const p = (linia.arrivals?.weekday || [])[i];
    if (!p) return;
    const wSzkole = naMinuty(p) + (dom.arriveWalk || 0);
    if (wSzkole <= start) rano = { odjazd: o, wSzkole, zapas: start - wSzkole };
  });

  const powrot = powrotna.find(d => naMinuty(d) >= koniec + (szkola.walk || 0));

  return {
    dzien, nazwa: DNI_PL[dzien], start: l.start, koniec: l.koniec,
    zDomu: rano ? naGodzine(naMinuty(rano.odjazd) - (dom.walk || 0)) : null,
    odjazd: rano ? rano.odjazd : null,
    wSzkole: rano ? naGodzine(rano.wSzkole) : null,
    zapas: rano ? rano.zapas : null,
    powrot: powrot || null,
    czekanie: powrot ? naMinuty(powrot) - koniec : null
  };
}

function pokazTydzien() {
  const box = $("#week");
  const dzisiaj = new Date().getDay();
  let html = '<h1>Plan tygodnia — ' + IMIE + '</h1>';

  for (const d of [1, 2, 3, 4, 5]) {
    const p = planDnia(d);
    if (!p) continue;
    const dzis = d === dzisiaj ? " dzis" : "";
    html +=
      '<div class="dzien' + dzis + '">' +
      '<h3>' + p.nazwa + (dzis ? ' <span class="znacznik">dziś</span>' : '') + '</h3>' +
      (p.odjazd
        ? '<div class="etap"><span class="opis">Wyjdź z domu</span><b>' + p.zDomu + '</b></div>' +
          '<div class="etap"><span class="opis">Odjazd autobusu</span><b>' + p.odjazd + '</b></div>' +
          '<div class="etap"><span class="opis">W szkole jesteś</span><b>' + p.wSzkole + '</b>' +
          '<span class="mala">' + p.zapas + ' min przed lekcjami</span></div>'
        : '<div class="etap"><span class="opis">Rano</span><b>brak kursu</b></div>') +
      '<div class="etap lekcje"><span class="opis">Lekcje</span><b>' +
        p.start + ' – ' + p.koniec + '</b></div>' +
      (p.powrot
        ? '<div class="etap"><span class="opis">Powrót — odjazd</span><b>' + p.powrot + '</b>' +
          '<span class="mala">' + p.czekanie + ' min czekania</span></div>'
        : '<div class="etap"><span class="opis">Powrót</span><b>brak kursu</b></div>') +
      '</div>';
  }

  html += '<div class="hint" style="margin-top:14px">Godziny liczone z rozkładu: rano ostatni ' +
          'kurs, który dowozi przed dzwonkiem; po lekcjach pierwszy, na który da się zdążyć.</div>';
  box.innerHTML = html;
  const zamknij = document.createElement("button");
  zamknij.className = "btn"; zamknij.textContent = "Zamknij";
  zamknij.onclick = () => { box.classList.add("hidden"); box.innerHTML = ""; render(); };
  box.appendChild(zamknij);
  box.classList.remove("hidden");
}

/* ============================ ustawienia ============================ */
function openSettings() {
  const box = $("#settings");
  box.classList.remove("hidden");
  box.innerHTML = "<h1>Ustawienia</h1>";
  const draft = structuredClone(config);

  draft.places.forEach((place, pi) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML =
      "<h3>" + esc(place.emoji) + " " + esc(place.name) + "</h3>" +
      '<div class="grid2">' +
      '<div><label>Nazwa</label><input data-f="name" value="' + esc(place.name) + '"></div>' +
      '<div><label>Ikona</label><input data-f="emoji" value="' + esc(place.emoji) + '"></div>' +
      "</div>" +
      "<label>Napis 1 — gdzie jest dziecko</label><input data-f='inPlace' value=\"" + esc(place.inPlace) + "\">" +
      "<label>Napis 2 — dokąd jedzie</label><input data-f='goingTo' value=\"" + esc(place.goingTo) + "\">" +
      "<label>Nazwa przystanku (drobny napis na dole)</label><input data-f='stop' value=\"" + esc(place.stop) + "\">" +
      '<div class="grid2">' +
      '<div><label>Szerokość (lat)</label><input data-f="lat" inputmode="decimal" value="' + place.lat + '"></div>' +
      '<div><label>Długość (lon)</label><input data-f="lon" inputmode="decimal" value="' + place.lon + '"></div>' +
      "</div>" +
      '<div class="grid2">' +
      '<div><label>Promień (m)</label><input data-f="radius" inputmode="numeric" value="' + place.radius + '"></div>' +
      '<div><label>Dojście (min)</label><input data-f="walk" inputmode="numeric" value="' + place.walk + '"></div>' +
      "</div>" +
      '<button class="btn" data-here="1">📍 Użyj mojej obecnej lokalizacji</button>' +
      '<div class="hint">Stań w miejscu (dom / szkoła) i naciśnij ten przycisk — współrzędne wpiszą się same.</div>';

    card.querySelector("[data-here]").onclick = ev => {
      ev.preventDefault();
      const btn = ev.currentTarget;
      btn.textContent = "Pobieram…";
      navigator.geolocation.getCurrentPosition(
        p => {
          card.querySelector('[data-f="lat"]').value = p.coords.latitude.toFixed(6);
          card.querySelector('[data-f="lon"]').value = p.coords.longitude.toFixed(6);
          btn.textContent = "✓ Zapisano (±" + Math.round(p.coords.accuracy) + " m)";
        },
        e => { btn.textContent = "Nie udało się: " + e.message; },
        { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
      );
    };

    const linesWrap = document.createElement("div");
    card.appendChild(linesWrap);

    const drawLines = () => {
      linesWrap.innerHTML = "";
      place.lines.forEach((line, li) => {
        const lb = document.createElement("div");
        lb.className = "lineBox";
        lb.innerHTML =
          '<div class="lineHead">' +
          '<input data-l="number" style="width:90px" value="' + esc(line.number) + '" placeholder="nr">' +
          '<input data-l="direction" value="' + esc(line.direction) + '" placeholder="kierunek">' +
          "</div>" +
          "<label>Dni robocze</label><textarea data-l='weekday'>" + line.weekday.join(" ") + "</textarea>" +
          "<label>Soboty</label><textarea data-l='saturday'>" + line.saturday.join(" ") + "</textarea>" +
          "<label>Niedziele i święta</label><textarea data-l='sunday'>" + line.sunday.join(" ") + "</textarea>" +
          '<div class="hint">Godziny w formacie <b>07:25</b>, oddzielone spacją, przecinkiem lub nową linią. Kursy po północy zapisz jako 24:15, 25:00.</div>' +
          // godziny przyjazdu edytujemy tylko tam, gdzie ekran je pokazuje
          (place.arriveLabel
            ? "<label>Przyjazd na przystanek docelowy — dni robocze</label>" +
              "<textarea data-a='weekday'>" + line.arrivals.weekday.join(" ") + "</textarea>" +
              "<label>Przyjazd — soboty</label>" +
              "<textarea data-a='saturday'>" + line.arrivals.saturday.join(" ") + "</textarea>" +
              '<div class="hint">Z tego liczy się napis „' + esc(place.arriveLabel) +
              ' …”: godzina przyjazdu plus ' + place.arriveWalk + ' min dojścia.</div>'
            : "") +
          '<button class="btn danger" data-del="1">Usuń linię ' + esc(line.number) + "</button>";

        lb.querySelector("[data-del]").onclick = ev => {
          ev.preventDefault();
          harvest(); place.lines.splice(li, 1); drawLines();
        };
        linesWrap.appendChild(lb);
      });

      const add = document.createElement("button");
      add.className = "btn"; add.textContent = "+ Dodaj linię";
      add.onclick = ev => {
        ev.preventDefault(); harvest();
        place.lines.push({ number: "", direction: "", weekday: [], saturday: [], sunday: [] });
        drawLines();
      };
      linesWrap.appendChild(add);
    };

    // przepisanie tego, co wpisane w polach, z powrotem do obiektu `place`
    const harvest = () => {
      for (const el of card.querySelectorAll("[data-f]")) {
        const f = el.dataset.f;
        place[f] = ["lat", "lon", "radius", "walk"].includes(f) ? parseFloat(el.value) || 0 : el.value;
      }
      const godziny = el => el.value
        .split(/[\s,;]+/).map(s => s.trim()).filter(Boolean)
        .map(s => { const m = /^(\d{1,2})[:.](\d{1,2})$/.exec(s); return m ? pad(m[1]) + ":" + pad(m[2]) : s; })
        .filter(s => /^\d{1,2}:\d{2}$/.test(s))
        .sort();

      const boxes = linesWrap.querySelectorAll(".lineBox");
      boxes.forEach((lb, li) => {
        if (!place.lines[li]) return;
        place.lines[li].number = lb.querySelector('[data-l="number"]').value.trim();
        place.lines[li].direction = lb.querySelector('[data-l="direction"]').value.trim();
        for (const day of ["weekday", "saturday", "sunday"]) {
          place.lines[li][day] = godziny(lb.querySelector('[data-l="' + day + '"]'));
          const pole = lb.querySelector('[data-a="' + day + '"]');
          if (pole) place.lines[li].arrivals[day] = godziny(pole);
        }
      });
    };

    card.dataset.pi = pi;
    card._harvest = harvest;
    drawLines();
    box.appendChild(card);
  });

  const harvestAll = () => {
    for (const c of box.querySelectorAll(".card")) if (c._harvest) c._harvest();
  };

  const save = document.createElement("button");
  save.className = "btn primary"; save.textContent = "Zapisz";
  save.onclick = () => { harvestAll(); saveConfig(draft); closeSettings(); };
  box.appendChild(save);

  const link = document.createElement("button");
  link.className = "btn"; link.textContent = "🔗 Skopiuj link z tą konfiguracją";
  link.onclick = async () => {
    harvestAll();
    const url = location.origin + location.pathname + "#c=" + b64enc(JSON.stringify(draft));
    try { await navigator.clipboard.writeText(url); link.textContent = "✓ Skopiowano — wyślij na telefon dziecka"; }
    catch (e) { prompt("Skopiuj ten link:", url); }
  };
  box.appendChild(link);

  const reset = document.createElement("button");
  reset.className = "btn danger"; reset.textContent = "Przywróć ustawienia domyślne";
  reset.onclick = () => {
    if (confirm("Skasować całą konfigurację i wrócić do domyślnej?")) {
      localStorage.removeItem(STORAGE_KEY);
      config = normalize(structuredClone(DEFAULT_CONFIG));
      closeSettings();
    }
  };
  box.appendChild(reset);

  const cancel = document.createElement("button");
  cancel.className = "btn"; cancel.textContent = "Anuluj";
  cancel.onclick = closeSettings;
  box.appendChild(cancel);
}

function closeSettings() {
  $("#settings").classList.add("hidden");
  $("#settings").innerHTML = "";
  render();
}

/* ============================ start ============================ */
config = loadConfig();
$("#gear").onclick = openSettings;
$("#kalendarz").onclick = pokazTydzien;
startGeolocation();
render();
setInterval(render, 1000);
document.addEventListener("visibilitychange", () => { if (!document.hidden) render(); });

/* Aktualizacja bez udziału użytkownika.
   Wcześniej trzeba było otworzyć aplikację dwa razy: za pierwszym razem telefon
   pobierał nowe pliki w tle, ale pokazywał jeszcze stare. Jeśli ktoś tego nie
   zrobił, tygodniami widział poprzednią wersję — i tak właśnie zniknęła linijka
   „Będziesz w szkole o…”. Teraz strona sama się przeładowuje, gdy nowa wersja
   przejmie kontrolę. */
if ("serviceWorker" in navigator && window.isSecureContext) {
  let juzPrzeladowano = false;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (juzPrzeladowano) return;      // controllerchange potrafi przyjść dwa razy
    juzPrzeladowano = true;
    location.reload();
  });
  navigator.serviceWorker.register("sw.js")
    .then(reg => {
      // brak zasięgu nie może wywalić aplikacji — dlatego każde sprawdzenie z catch
      const sprawdz = () => reg.update().catch(() => {});
      sprawdz();                                   // od razu przy starcie
      setInterval(sprawdz, 60 * 60 * 1000);        // i raz na godzinę
    })
    .catch(e => console.warn("SW:", e));
}
