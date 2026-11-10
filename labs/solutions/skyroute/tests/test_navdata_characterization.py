"""Characterization tests for skyroute.navdata.

These pin what the reader does today, quirks included, so a refactor can be
checked against them. They must pass against the legacy reader and the
modernized one. Do not "fix" an assertion here without a requirement change.
"""

import tempfile
import unittest
from pathlib import Path

from skyroute import navdata


def rec(kind, ident, lat, lon, elev="", freq="", name=""):
    """One SRN-1 line in the fixed columns the reader expects."""
    return f"{kind:2} {ident:5} {lat:9} {lon:10} {elev:>5} {freq:>6} {name}"


FIXTURE_LINES = [
    "* comment line",
    "",
    "   ",
    rec("AP", "KTST1", "N33411800", "W112045700", "1478", "", "TEST FIELD   "),
    rec("WP", "ALPHA", "N40000000", "W101000000").rstrip(),
    rec("WP", "BRAVO", "N4O000000", "W101000000").rstrip(),
    rec("WP", "ALPHA", "N40053000", "W101020000").rstrip(),
    rec("NV", "ZZV", "S33300000", "E151000000", "120", "113.90", "SOUTH VOR"),
    rec("NV", "ZER", "N10000000", "W010000000", "0", "0.00", "ZERO FREQ"),
    rec("XX", "OTHER", "N10000000", "W010000000").rstrip(),
    rec("wp", "LOWER", "N10000000", "W010000000").rstrip(),
    rec("WP", "lowfx", "N10000000", "W010000000").rstrip(),
    rec("WP", "HEMIX", "n10000000", "w010000000").rstrip(),
    "WP SHORT N10000000",
    rec("WP", "CRLF1", "N10000000", "W010000000").rstrip() + "\r",
]


class CharacterizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        cls.path = str(Path(tmp.name) / "fixture.srn")
        with open(cls.path, "w", newline="") as f:
            f.write("\n".join(FIXTURE_LINES) + "\n")
        cls.fixes = navdata.load(cls.path)

    def fields(self, ident):
        fix = self.fixes[ident]
        return (fix.kind, fix.ident, round(fix.lat, 9), round(fix.lon, 9),
                fix.elev, fix.freq, fix.name)

    def test_skipped_lines(self):
        # Comments, blanks, unknown or lowercase kinds, short and malformed records.
        self.assertEqual(sorted(self.fixes),
                         ["ALPHA", "CRLF1", "HEMIX", "KTST1", "ZER", "ZZV", "lowfx"])

    def test_airport_fields(self):
        self.assertEqual(self.fields("KTST1"),
                         ("AP", "KTST1", 33.688333333, -112.0825, 1478, None, "TEST FIELD"))

    def test_navaid_fields(self):
        self.assertEqual(self.fields("ZZV"),
                         ("NV", "ZZV", -33.5, 151.0, 120, 113.9, "SOUTH VOR"))

    def test_waypoint_without_optional_columns(self):
        self.assertEqual(self.fields("CRLF1"), ("WP", "CRLF1", 10.0, -10.0, 0, None, ""))

    def test_last_duplicate_wins(self):
        self.assertEqual(self.fields("ALPHA"),
                         ("WP", "ALPHA", 40.091666667, -101.033333333, 0, None, ""))

    def test_zero_frequency_reads_as_none(self):
        self.assertIsNone(self.fixes["ZER"].freq)

    def test_lowercase_hemisphere_reads_as_north_and_east(self):
        self.assertEqual((self.fixes["HEMIX"].lat, self.fixes["HEMIX"].lon), (10.0, 10.0))

    def test_lowercase_ident_is_loaded_but_lookup_cannot_find_it(self):
        self.assertIn("lowfx", self.fixes)
        self.assertIsNone(navdata.lookup("lowfx", self.path))

    def test_lookup_normalizes_query(self):
        self.assertEqual(navdata.lookup("  ktst1 ", self.path).ident, "KTST1")
        self.assertIsNone(navdata.lookup("NOPE1", self.path))
        self.assertIsNone(navdata.lookup(None, self.path))

    def test_missing_file_raises_oserror(self):
        with self.assertRaises(OSError):
            navdata.load(self.path + ".missing")

    def test_shipped_data_idents(self):
        self.assertEqual(sorted(navdata.load()), [
            "CEDRR", "GULFF", "KBFI", "KDVT", "KESTL", "KMSP", "KPHX", "KPIE", "LKV",
            "LOONZ", "MESAS", "PINEZ", "PRARI", "PRV", "RAINR", "SRV", "TWINZ", "ZUNIX",
        ])

    def test_shipped_duplicate_uses_amended_record(self):
        prari = navdata.lookup("PRARI")
        self.assertEqual((round(prari.lat, 9), round(prari.lon, 9)), (40.091666667, -101.033333333))


if __name__ == "__main__":
    unittest.main()
