"""Sensori PSV per Home Assistant."""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import ATTR_DAYS_COUNT, ATTR_LAST_UPDATE, ATTR_MONTHLY_AVERAGE, ATTR_PRICES_AVAILABLE, DOMAIN, UNIT_EUR_MWH, UNIT_EUR_SMC
from .coordinator import PsvDataCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: PsvDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        PsvGiornalieroEurMwh(coordinator, config_entry),
        PsvGiornalieroEurSmc(coordinator, config_entry),
        PsvMediaMeseEurMwh(coordinator, config_entry),
        PsvMediaMeseEurSmc(coordinator, config_entry),
    ], update_before_add=True)

class PsvBaseSensor(CoordinatorEntity[PsvDataCoordinator], SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    # has_entity_name = False: l'entity_id e il friendly_name si basano solo
    # sul nome del sensore stesso (es. "PSV Prezzo giornaliero (€/MWh)"),
    # senza nessun prefisso aggiuntivo.
    _attr_has_entity_name = False

    def __init__(self, coordinator, config_entry, unique_suffix):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{unique_suffix}"

    # NOTA: niente device_info qui. Raggruppare i sensori sotto un device
    # induce Home Assistant a usare il nome del device come contesto nel
    # calcolo dello slug iniziale dell'entity_id (es. "prezzi_psv_del_mese_"),
    # anche con has_entity_name = False. Tenendo i 4 sensori come entità
    # indipendenti, l'entity_id deriva esclusivamente dal nome del sensore.

    @property
    def available(self):
        return self.coordinator.data is not None

class PsvGiornalieroEurMwh(PsvBaseSensor):
    _attr_icon = "mdi:fire"
    _attr_native_unit_of_measurement = UNIT_EUR_MWH
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "giornaliero_mwh")
        self._attr_name = "PSV Prezzo giornaliero (€/MWh)"

    @property
    def native_value(self):
        return self.coordinator.data.prezzo_giornaliero_eur_mwh if self.coordinator.data else None

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data
        return {
            ATTR_LAST_UPDATE: d.ultimo_aggiornamento.isoformat() if d.ultimo_aggiornamento else None,
            "ultimo_giorno_disponibile": d.ultimo_giorno_disponibile,
            ATTR_PRICES_AVAILABLE: d.prezzi_giornalieri,
        }

class PsvGiornalieroEurSmc(PsvBaseSensor):
    _attr_icon = "mdi:fire"
    _attr_native_unit_of_measurement = UNIT_EUR_SMC
    _attr_suggested_display_precision = 5

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "giornaliero_smc")
        self._attr_name = "PSV Prezzo giornaliero (€/Smc)"

    @property
    def native_value(self):
        return self.coordinator.data.prezzo_giornaliero_eur_smc if self.coordinator.data else None

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data
        return {
            ATTR_LAST_UPDATE: d.ultimo_aggiornamento.isoformat() if d.ultimo_aggiornamento else None,
            "ultimo_giorno_disponibile": d.ultimo_giorno_disponibile,
        }

class PsvMediaMeseEurMwh(PsvBaseSensor):
    _attr_icon = "mdi:gas-burner"
    _attr_native_unit_of_measurement = UNIT_EUR_MWH
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "media_mese_mwh")
        self._attr_name = "PSV Media mese (€/MWh)"

    @property
    def native_value(self):
        return self.coordinator.data.media_mensile_eur_mwh if self.coordinator.data else None

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data
        return {
            ATTR_LAST_UPDATE: d.ultimo_aggiornamento.isoformat() if d.ultimo_aggiornamento else None,
            ATTR_DAYS_COUNT: d.giorni_calcolati,
            ATTR_MONTHLY_AVERAGE: d.media_mensile_eur_mwh,
        }

class PsvMediaMeseEurSmc(PsvBaseSensor):
    _attr_icon = "mdi:gas-burner"
    _attr_native_unit_of_measurement = UNIT_EUR_SMC
    _attr_suggested_display_precision = 5

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "media_mese_smc")
        self._attr_name = "PSV Media mese (€/Smc)"

    @property
    def native_value(self):
        return self.coordinator.data.media_mensile_eur_smc if self.coordinator.data else None

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data
        return {
            ATTR_LAST_UPDATE: d.ultimo_aggiornamento.isoformat() if d.ultimo_aggiornamento else None,
            ATTR_DAYS_COUNT: d.giorni_calcolati,
            ATTR_MONTHLY_AVERAGE: d.media_mensile_eur_smc,
        }
