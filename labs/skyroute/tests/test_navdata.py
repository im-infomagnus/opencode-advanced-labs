import unittest

from skyroute import navdata


class NavdataTests(unittest.TestCase):
    def test_airport_position(self):
        fix = navdata.lookup("KDVT")
        self.assertEqual((fix.kind, fix.name, fix.elev),
                         ("AP", "PHOENIX DEER VALLEY", 1478))
        self.assertAlmostEqual(fix.lat, 33.688333, places=6)
        self.assertAlmostEqual(fix.lon, -112.0825, places=6)

    def test_navaid_frequency(self):
        self.assertEqual(navdata.lookup("SRV").freq, 113.9)

    def test_lookup_ignores_case(self):
        self.assertEqual(navdata.lookup("kmsp").ident, "KMSP")

    def test_unknown_ident_is_none(self):
        self.assertIsNone(navdata.lookup("NOPE1"))


if __name__ == "__main__":
    unittest.main()
