import unittest

from skyroute.fuel import plan_fuel


class FuelTests(unittest.TestCase):
    def setUp(self):
        # Two hours at 2400 lb/h: trip 4800, contingency 5% of trip, 30 min reserve.
        self.plan = plan_fuel(2.0, 2400)

    def test_trip_fuel_is_ete_times_burn(self):
        self.assertEqual(self.plan.trip, 4800.0)

    def test_reserve_is_thirty_minutes_at_burn(self):
        self.assertEqual(self.plan.reserve, 1200.0)

    def test_contingency_is_percent_of_trip(self):
        self.assertEqual(self.plan.contingency, 240.0)

    def test_total_is_sum_of_parts(self):
        self.assertEqual(self.plan.total, 6240.0)

    def test_contingency_uses_configured_percent(self):
        self.assertEqual(plan_fuel(1.0, 2000, contingency_pct=10).contingency, 200.0)

    def test_rejects_nonpositive_burn(self):
        with self.assertRaises(ValueError):
            plan_fuel(1.0, 0)


if __name__ == "__main__":
    unittest.main()
