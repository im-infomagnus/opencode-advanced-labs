"""Routes: an ordered list of navdata fixes and the legs between them."""

from dataclasses import dataclass

from skyroute import navdata
from skyroute.geo import distance_nm, initial_bearing_deg


@dataclass(frozen=True)
class Leg:
    start: navdata.Fix
    end: navdata.Fix
    distance_nm: float
    bearing_deg: float

    @property
    def name(self) -> str:
        return f"{self.start.ident}-{self.end.ident}"


class Route:
    def __init__(self, fixes):
        if len(fixes) < 2:
            raise ValueError("a route needs at least two fixes")
        self.fixes = list(fixes)

    @classmethod
    def from_idents(cls, idents, navdata_path=None):
        """Build a route from fix identifiers such as ["KDVT", "ZUNIX", "KMSP"]."""
        fixes = []
        for ident in idents:
            fix = navdata.lookup(ident, navdata_path)
            if fix is None:
                raise ValueError(f"unknown fix: {ident.strip()}")
            fixes.append(fix)
        return cls(fixes)

    @property
    def idents(self) -> list:
        return [fix.ident for fix in self.fixes]

    def legs(self) -> list:
        out = []
        for a, b in zip(self.fixes, self.fixes[1:]):
            out.append(Leg(
                start=a,
                end=b,
                distance_nm=distance_nm(a.lat, a.lon, b.lat, b.lon),
                bearing_deg=initial_bearing_deg(a.lat, a.lon, b.lat, b.lon),
            ))
        return out

    def total_distance_nm(self) -> float:
        total = 0.0
        for i in range(len(self.fixes) - 2):
            a, b = self.fixes[i], self.fixes[i + 1]
            total += distance_nm(a.lat, a.lon, b.lat, b.lon)
        return total

    def ete_hours(self, groundspeed_kt: float) -> float:
        """Estimated time enroute at a constant ground speed."""
        if groundspeed_kt <= 0:
            raise ValueError("ground speed must be positive")
        return self.total_distance_nm() / groundspeed_kt
