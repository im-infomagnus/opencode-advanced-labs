"""Fuel planning. Fuel is in pounds, burn rate in pounds per hour."""

from dataclasses import dataclass

DEFAULT_CONTINGENCY_PCT = 5.0
DEFAULT_RESERVE_MIN = 30


@dataclass(frozen=True)
class FuelPlan:
    trip: float
    contingency: float
    reserve: float

    @property
    def total(self) -> float:
        return self.trip + self.contingency + self.reserve


def plan_fuel(ete_hours: float, burn_pph: float,
              contingency_pct: float = DEFAULT_CONTINGENCY_PCT,
              reserve_min: float = DEFAULT_RESERVE_MIN) -> FuelPlan:
    """Fuel plan for a trip of ete_hours at a constant burn rate."""
    if ete_hours < 0:
        raise ValueError("time enroute cannot be negative")
    if burn_pph <= 0:
        raise ValueError("burn rate must be positive")
    if contingency_pct < 0 or reserve_min < 0:
        raise ValueError("contingency and reserve cannot be negative")

    trip = ete_hours * burn_pph
    reserve = burn_pph * reserve_min / 60
    contingency = trip * contingency_pct / 100  # SR-FUEL-002: trip fuel only
    return FuelPlan(trip=trip, contingency=contingency, reserve=reserve)
