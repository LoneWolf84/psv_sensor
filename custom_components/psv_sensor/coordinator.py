"""Coordinator per PSV Sensor: scarica i prezzi IGI dal GME.

Il sito GME (basato su DNN/ASP.NET) protegge l'endpoint dati con un
meccanismo anti-forgery: la pagina HTML imposta un cookie
`__RequestVerificationToken` e lo stesso valore deve essere rispedito
come header `RequestVerificationToken` nella chiamata successiva.
Servono inoltre gli header custom `ModuleId` e `TabId`, fissi per la
pagina IGIndexGmeEsiti.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from statistics import mean

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    GME_IGI_URL,
    GME_MODULE_ID,
    GME_PAGE_URL,
    GME_TAB_ID,
    MWH_TO_SMC,
    RETRY_MINUTES,
)

_LOGGER = logging.getLogger(__name__)

HTTP_TIMEOUT = aiohttp.ClientTimeout(total=30)

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Nome del cookie anti-forgery impostato dalla pagina GME
TOKEN_COOKIE_NAME = "__RequestVerificationToken"


class PsvData:
    """Dati calcolati dal coordinator."""

    def __init__(self) -> None:
        self.prezzo_giornaliero_eur_mwh: float | None = None
        self.prezzo_giornaliero_eur_smc: float | None = None
        self.media_mensile_eur_mwh: float | None = None
        self.media_mensile_eur_smc: float | None = None
        self.prezzi_giornalieri: dict[str, float] = {}  # {"YYYY-MM-DD": prezzo}
        self.giorni_calcolati: int = 0
        self.ultimo_aggiornamento: datetime | None = None
        self.ultimo_giorno_disponibile: str | None = None


class PsvDataCoordinator(DataUpdateCoordinator[PsvData]):
    """Coordinator che scarica e calcola i prezzi IGI/PSV dal GME."""

    def __init__(self, hass: HomeAssistant, scan_hour: int) -> None:
        self.scan_hour = scan_hour
        self._retry_count = 0
        self._next_update: datetime | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=10),
        )

    def _get_next_scheduled_update(self) -> datetime:
        now = dt_util.now()
        scan_minute = (now.day * 7 + 13) % 60
        target = now.replace(hour=self.scan_hour, minute=scan_minute, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        return target

    async def _async_update_data(self) -> PsvData:
        now = dt_util.now()

        if self._next_update is not None and now < self._next_update:
            if self.data is not None:
                return self.data

        try:
            data = await self._fetch_and_compute(now)
            self._retry_count = 0
            self._next_update = self._get_next_scheduled_update()
            _LOGGER.debug("Dati IGI aggiornati. Prossimo aggiornamento: %s", self._next_update)
            return data

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            delay = RETRY_MINUTES[min(self._retry_count, len(RETRY_MINUTES) - 1)]
            self._retry_count += 1
            self._next_update = now + timedelta(minutes=delay)
            _LOGGER.warning("Errore GME: %s. Retry tra %d minuti.", err, delay)
            if self.data is not None:
                return self.data
            raise UpdateFailed(f"Impossibile scaricare dati IGI: {err}") from err

    async def _get_verification_token(self, session: aiohttp.ClientSession) -> str:
        """Visita la pagina GME e restituisce il valore del cookie anti-forgery.

        Il cookie viene impostato automaticamente nella CookieJar della
        sessione aiohttp; lo leggiamo da lì per poterlo rispedire anche
        come header (richiesto dal sito, oltre al cookie stesso).
        """
        async with session.get(
            GME_PAGE_URL,
            headers={"User-Agent": BROWSER_USER_AGENT},
            timeout=HTTP_TIMEOUT,
        ) as resp:
            await resp.read()  # consuma il body, i cookie sono già stati salvati
            if resp.status != 200:
                _LOGGER.debug(
                    "Visita pagina GME ha restituito HTTP %s", resp.status
                )

        # Cerca il cookie nella jar della sessione (per il dominio gme.mercatoelettrico.org)
        for cookie in session.cookie_jar:
            if cookie.key == TOKEN_COOKIE_NAME:
                return cookie.value

        raise aiohttp.ClientError(
            f"Cookie '{TOKEN_COOKIE_NAME}' non trovato dopo la visita alla pagina GME. "
            "Il meccanismo di sicurezza del sito potrebbe essere cambiato."
        )

    async def _fetch_and_compute(self, now: datetime) -> PsvData:
        """Scarica il JSON dal GME e calcola i sensori."""
        async with aiohttp.ClientSession() as session:
            # Step 1: visita la pagina per ottenere cookie + token anti-forgery
            token = await self._get_verification_token(session)

            # Step 2: chiama l'API con cookie (automatici) + header richiesti
            api_headers = {
                "User-Agent": BROWSER_USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
                "Referer": GME_PAGE_URL,
                "X-Requested-With": "XMLHttpRequest",
                "ModuleId": GME_MODULE_ID,
                "TabId": GME_TAB_ID,
                "RequestVerificationToken": token,
            }

            async with session.get(
                GME_IGI_URL, headers=api_headers, timeout=HTTP_TIMEOUT
            ) as resp:
                if resp.status == 401:
                    raise aiohttp.ClientError(
                        "HTTP 401: token anti-forgery rifiutato. Il GME potrebbe "
                        "aver cambiato ModuleId/TabId o il meccanismo di sicurezza."
                    )
                if resp.status != 200:
                    raise aiohttp.ClientError(f"HTTP {resp.status}")
                records: list[dict] = await resp.json(content_type=None)

        if not records:
            raise UpdateFailed("Risposta GME vuota")

        # Parsing: {"data": 20260601, "dataAggiornamento": 20260615, "igi": 47.09}
        prezzi: dict[str, float] = {}
        for r in records:
            try:
                raw = str(int(r["data"]))
                date_str = f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
                prezzi[date_str] = float(r["igi"])
            except (KeyError, ValueError, TypeError):
                continue

        if not prezzi:
            raise UpdateFailed("Nessun prezzo valido nella risposta GME")

        data = PsvData()
        data.prezzi_giornalieri = prezzi
        data.giorni_calcolati = len(prezzi)

        valori = list(prezzi.values())
        data.media_mensile_eur_mwh = round(mean(valori), 4)
        data.media_mensile_eur_smc = round(data.media_mensile_eur_mwh * MWH_TO_SMC, 6)

        ultimo_giorno = max(prezzi.keys())
        data.ultimo_giorno_disponibile = ultimo_giorno
        data.prezzo_giornaliero_eur_mwh = round(prezzi[ultimo_giorno], 4)
        data.prezzo_giornaliero_eur_smc = round(data.prezzo_giornaliero_eur_mwh * MWH_TO_SMC, 6)

        data.ultimo_aggiornamento = now
        return data
