#!/usr/bin/env sh
# Rooktest na een deploy: staat de site echt, en werkt de hele RAG-keten?
# Draait in CI (laatste stap) maar is ook los bruikbaar: scripts/rooktest.sh
# POSIX sh + curl, geen andere afhankelijkheden (CI-image is alpine).
#
# De /ask-check kost één echte Mistral-aanroep (centen) — dat is de prijs voor
# weten dat de kéten werkt, niet alleen dat de poort open staat. "citaten"
# moet gevuld zijn: precies de belofte van de tool.
set -u
BASIS="${ROOKTEST_BASIS:-https://grondslag.eu}"
fouten=0

# 1. Health — met retries: direct na compose up -d start uvicorn nog op
#    (bekende koude-start-502; geen backend-healthcheck die het opvangt vóór
#    nginx al doorverwijst).
poging=0
until curl -sf -m 10 "$BASIS/api/health" | grep -q '"ok"'; do
  poging=$((poging + 1))
  if [ "$poging" -ge 12 ]; then
    echo "FOUT: $BASIS/api/health antwoordt niet na $poging pogingen" >&2
    exit 1
  fi
  sleep 5
done
echo "ok: health"

# 2. http -> https-redirect met behoud van pad.
doel=$(curl -s -m 10 -o /dev/null -w '%{redirect_url}' "http://grondslag.eu/over")
case "$doel" in
  https://grondslag.eu/over) echo "ok: redirect" ;;
  *) echo "FOUT: http-redirect wijst naar '$doel'" >&2; fouten=1 ;;
esac

# 3. Frontend-pagina's bereikbaar.
for pad in / /transparantie; do
  if curl -sf -m 10 -o /dev/null "$BASIS$pad"; then
    echo "ok: pagina $pad"
  else
    echo "FOUT: pagina $pad niet bereikbaar" >&2; fouten=1
  fi
done

# 4. De RAG-keten: één echte vraag, antwoord mét citaten. Eén herkansing —
#    een enkele model-hik mag de pipeline niet rood kleuren, twee wel.
for poging in 1 2; do
  antwoord=$(curl -s -m 60 -X POST "$BASIS/api/ask" \
    -H 'Content-Type: application/json' \
    -d '{"vraag":"Wij screenen cvs met AI bij werving. Valt dat onder de AI-verordening?"}')
  if printf '%s' "$antwoord" | grep -q '"citaten":\[{'; then
    echo "ok: /ask met citaten"
    break
  elif [ "$poging" = 2 ]; then
    echo "FOUT: /ask gaf geen antwoord met citaten: $(printf '%s' "$antwoord" | head -c 200)" >&2
    fouten=1
  else
    sleep 10
  fi
done

exit "$fouten"
