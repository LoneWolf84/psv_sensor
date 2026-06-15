"""Costanti per l'integrazione PSV Sensor."""

DOMAIN = "psv_sensor"

# Configurazione
CONF_SCAN_HOUR = "scan_hour"
DEFAULT_SCAN_HOUR = 19  # Dopo le 18:30 il dato del giorno è definitivo

# Retry in minuti in caso di errore (stessa logica di pun_sensor)
RETRY_MINUTES = [1, 10, 60, 120, 180]

# -----------------------------------------------------------------------
# Endpoint pubblico GME – nessuna autenticazione richiesta
# Anno=0, Mese=0 → mese corrente; Dettaglio=G → giornaliero
# Risposta JSON: [{"data": 20260601, "dataAggiornamento": 20260615, "igi": 47.09}, ...]
# -----------------------------------------------------------------------
GME_IGI_URL = (
    "https://www.mercatoelettrico.org"
    "/DesktopModules/GmeIGIndex/API/item/GetGasIGI"
    "?Anno=0&Mese=0&Dettaglio=G"
)

# Unità di misura
UNIT_EUR_MWH = "€/MWh"
UNIT_EUR_SMC = "€/Smc"

# Fattore di conversione €/MWh → €/Smc (PCS convenzionale ARERA = 10.6923 kWh/Smc)
MWH_TO_SMC = 0.0105833

# Attributi extra dei sensori
ATTR_LAST_UPDATE = "ultimo_aggiornamento"
ATTR_PRICES_AVAILABLE = "prezzi_disponibili"
ATTR_MONTHLY_AVERAGE = "media_mensile_progressiva"
ATTR_DAYS_COUNT = "giorni_calcolati"
