import unittest

from skyroute.navdata import Fix
from skyroute.route import Route


def wp(ident, lat, lon):
    return Fix("WP", ident, lat, lon)


class RouteTests(unittest.TestCase):
    def setUp(self):
        # Three points one degree apart on the equator: two legs of 60.04 NM each.
        self.route = Route([wp("AAAAA", 0, 0), wp("BBBBB", 0, 1), wp("CCCCC", 0, 2)])

    def test_legs_connect_consecutive_fixes(self):
        self.assertEqual([leg.name for leg in self.route.legs()],
                         ["AAAAA-BBBBB", "BBBBB-CCCCC"])

    def test_leg_distance(self):
        self.assertAlmostEqual(self.route.legs()[0].distance_nm, 60.0405, places=3)

    def test_total_distance_includes_every_leg(self):
        self.assertAlmostEqual(self.route.total_distance_nm(), 120.081, places=2)

    def test_ete_rejects_zero_groundspeed(self):
        with self.assertRaises(ValueError):
            self.route.ete_hours(0)

    def test_route_needs_two_fixes(self):
        with self.assertRaises(ValueError):
            Route([wp("AAAAA", 0, 0)])

    def test_from_idents_uses_navdata(self):
        route = Route.from_idents(["KDVT", "ZUNIX", "KMSP"])
        self.assertEqual(route.idents, ["KDVT", "ZUNIX", "KMSP"])

    def test_from_idents_rejects_unknown_fix(self):
        with self.assertRaisesRegex(ValueError, "unknown fix: NOPE1"):
            Route.from_idents(["KDVT", "NOPE1"])


if __name__ == "__main__":
    unittest.main()
