#!/bin/bash
# Pilnuje, żeby numer w sw.js zgadzał się z `version:` w autobus.js.
# Rozjazd jest niewidoczny na ekranie, a powoduje, że telefony offline
# serwują starą wersję i nie czyszczą pamięci. Zdarzyło się: sw.js utknął
# na v18, gdy konfiguracja była już na v22.
cd "$(dirname "$0")"
KONF=$(grep -o 'version: [0-9]*' autobus.js | head -1 | grep -o '[0-9]*')
CACHE=$(grep -o 'autobus-v[0-9]*' sw.js | head -1 | grep -o '[0-9]*')
if [ "$KONF" = "$CACHE" ]; then
  echo "OK: obie wersje to v$KONF"
else
  echo "ROZJAZD: autobus.js ma v$KONF, sw.js ma v$CACHE  -> popraw sw.js"
  exit 1
fi
