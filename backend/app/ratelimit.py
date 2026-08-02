"""Lichte per-IP rate-limiter voor /ask — een kostenrem nu de endpoint via de
embed-widget en de publieke API breder gebruikt wordt. Pure, in-memory
sliding-window en dus los testbaar (geen tijd/IO binnenin: `nu` komt van buiten).

Let op: elke uvicorn-worker houdt een eigen venster bij, dus de effectieve
limiet is limiet × aantal workers. Ruim genoeg als rem tegen kostenmisbruik,
niet bedoeld als harde quota per gebruiker.
"""
from __future__ import annotations

from collections import deque


class RateLimiter:
    def __init__(self, max_per_window: int, window_seconds: float):
        self.max = max_per_window
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}

    def toegestaan(self, sleutel: str, nu: float) -> bool:
        """True als deze sleutel (IP) nog binnen de limiet zit; registreert de
        aanroep meteen. Verlopen tikken vervallen; lege sleutels worden opgeruimd
        zodat de dict niet groeit met eenmalige IP's."""
        grens = nu - self.window
        # Zeldzame sweep: verwijder IP's zonder recente tikken zodat de dict
        # niet meegroeit met elk eenmalig IP dat ooit langskwam.
        if len(self._hits) > 10_000:
            self._hits = {k: dq for k, dq in self._hits.items() if dq and dq[-1] > grens}
        q = self._hits.get(sleutel)
        if q is None:
            q = deque()
        while q and q[0] <= grens:
            q.popleft()
        if len(q) >= self.max:
            self._hits[sleutel] = q
            return False
        q.append(nu)
        self._hits[sleutel] = q
        return True
