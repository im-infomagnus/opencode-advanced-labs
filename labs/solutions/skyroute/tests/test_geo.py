import unittest

from skyroute.geo import distance_nm, format_hours, initial_bearing_deg

KDVT = (33.68833333, -112.0825)
KPHX = (33.43416667, -112.01166667)
KBFI = (47.53, -122.30194444)


class GeoTests(unittest.TestCase):
    def test_distance_kdvt_to_kphx(self):
        self.assertAlmostEqual(distance_nm(*KDVT, *KPHX), 15.666, places=2)

    def test_distance_one_degree_of_longitude_at_equator(self):
        self.assertAlmostEqual(distance_nm(0, 0, 0, 1), 60.0405, places=3)

    def test_distance_to_same_point_is_zero(self):
        self.assertEqual(distance_nm(*KDVT, *KDVT), 0.0)

    def test_eastbound_bearing(self):
        self.assertAlmostEqual(initial_bearing_deg(0, 0, 0, 1), 90.0)

    def test_bearing_kdvt_to_kphx(self):
        self.assertAlmostEqual(initial_bearing_deg(*KDVT, *KPHX), 166.906, places=2)

    def test_format_hours(self):
        self.assertEqual(format_hours(2.4475), "2:27")

    def test_westbound_bearing_is_normalized(self):
        self.assertAlmostEqual(initial_bearing_deg(0, 0, 0, -1), 270.0)

    def test_bearing_kdvt_to_kbfi(self):
        self.assertAlmostEqual(initial_bearing_deg(*KDVT, *KBFI), 333.960, places=2)

    def test_due_north_bearing_is_zero(self):
        self.assertEqual(initial_bearing_deg(0, 0, 1, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
