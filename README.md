# Prezzi PSV del mese
Prezzi PSV del mese - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Integrazione per **Home Assistant** che espone i prezzi del gas naturale (IG Index GME)
scaricati dall'endpoint pubblico del [GME](https://www.mercatoelettrico.org).

Ispirata a [pun_sensor](https://github.com/virtualdj/pun_sensor). Nessuna registrazione richiesta.

## Sensori

| Entità | Descrizione | Unità |
|---|---|---|
| `sensor.psv_prezzo_giornaliero_eur_mwh` | Prezzo IGI dell'ultimo giorno disponibile | €/MWh |
| `sensor.psv_prezzo_giornaliero_eur_smc` | Stesso valore convertito | €/Smc |
| `sensor.psv_media_mese_eur_mwh` | Media progressiva dal 1° del mese | €/MWh |
| `sensor.psv_media_mese_eur_smc` | Media progressiva — riferimento bolletta | €/Smc |

## Installazione HACS

1. HACS → `⋮` → Archivi personalizzati → aggiungi `https://github.com/LoneWolf84/psv_sensor`
2. Cerca "PSV" e installa
3. Riavvia Home Assistant
4. Impostazioni → Dispositivi e servizi → Aggiungi integrazione → "PSV"

## Licenza

[MIT](LICENSE)
