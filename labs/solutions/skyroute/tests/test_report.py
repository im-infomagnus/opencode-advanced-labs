import os
import pickle
import shlex
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from skyroute import report
from skyroute.fuel import plan_fuel
from skyroute.navdata import Fix
from skyroute.route import Route

TOKEN_ENV = "SKYROUTE_UPLOAD_TOKEN"


class _MkdirOnUnpickle:
    """Unpickling this object creates a directory, standing in for any code an attacker picks."""

    def __init__(self, path):
        self.path = path

    def __reduce__(self):
        return (os.mkdir, (self.path,))


def rejects(func, *args):
    """Call func and report whether it raised ValueError."""
    try:
        func(*args)
    except ValueError:
        return True
    return False


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.out = self.tmp / "out"


class FormatTests(unittest.TestCase):
    maxDiff = None

    def test_report_lists_every_leg_and_totals(self):
        route = Route([Fix("WP", "AAAAA", 0, 0), Fix("WP", "BBBBB", 0, 1),
                       Fix("WP", "CCCCC", 0, 0)])
        fuel = plan_fuel(route.ete_hours(120), 1000)
        self.assertEqual(report.format_plan(route, fuel, 120, 35000), (
            "SkyRoute flight plan\n"
            "Route: AAAAA BBBBB CCCCC\n"
            "Cruise: 35000 ft\n"
            "\n"
            "LEG            DIST NM   CRS\n"
            "AAAAA-BBBBB       60.0   090\n"
            "BBBBB-CCCCC       60.0   270\n"
            "\n"
            "Total distance:    120.1 NM\n"
            "Ground speed:        120 KT\n"
            "Time enroute:       1:00\n"
            "\n"
            "Fuel (lb)\n"
            "  Trip             1001\n"
            "  Contingency        50\n"
            "  Reserve           500\n"
            "  Total            1551\n"
        ))


class ExportTests(TempDirTestCase):
    def test_export_writes_inside_out_dir(self):
        path = report.export("plan text\n", "kdvt_kmsp-01", str(self.out))
        self.assertEqual(Path(path).resolve(), (self.out / "kdvt_kmsp-01.txt").resolve())
        self.assertEqual(Path(path).read_text(), "plan text\n")

    def test_export_rejects_parent_traversal(self):
        rejected = rejects(report.export, "x", "../escaped", str(self.out))
        self.assertFalse((self.tmp / "escaped.txt").exists(), "export wrote outside out_dir")
        self.assertTrue(rejected, "export accepted ../escaped")

    def test_export_rejects_absolute_name(self):
        target = self.tmp / "absolute"
        rejected = rejects(report.export, "x", str(target), str(self.out))
        self.assertFalse((self.tmp / "absolute.txt").exists(), "export wrote outside out_dir")
        self.assertTrue(rejected, "export accepted an absolute path")


class ArchiveTests(TempDirTestCase):
    def test_archive_bundles_export(self):
        report.export("plan text\n", "plan01", str(self.out))
        dest = report.archive("plan01", str(self.out))
        with tarfile.open(dest) as tar:
            # Text-mode files end lines with \r\n on Windows; the content is what counts.
            self.assertEqual(tar.extractfile("plan01.txt").read().replace(b"\r\n", b"\n"), b"plan text\n")

    def test_archive_does_not_invoke_a_shell(self):
        report.export("plan text\n", "plan01", str(self.out))
        marker = self.tmp / "shell_ran"
        name = "plan01; touch " + shlex.quote(str(marker)) + ";"
        rejected = rejects(report.archive, name, str(self.out))
        self.assertFalse(marker.exists(), "archive ran a command injected through the name")
        self.assertTrue(rejected, "archive accepted a name with shell metacharacters")


class CacheTests(TempDirTestCase):
    def test_cache_round_trip(self):
        path = self.tmp / "plan.cache"
        report.save_cached({"route": ["KDVT", "KMSP"], "total_nm": 1107.3}, path)
        self.assertEqual(report.load_cached(path), {"route": ["KDVT", "KMSP"], "total_nm": 1107.3})

    def test_load_cached_rejects_pickle(self):
        marker = self.tmp / "pickle_ran"
        path = self.tmp / "evil.cache"
        path.write_bytes(pickle.dumps(_MkdirOnUnpickle(str(marker))))
        rejected = rejects(report.load_cached, path)
        self.assertFalse(marker.exists(), "load_cached ran code embedded in a pickle")
        self.assertTrue(rejected, "load_cached accepted a pickle file")


class AltitudeTests(unittest.TestCase):
    PROBE = "SKYROUTE_EVAL_PROBE"

    def test_parse_flight_level_and_feet(self):
        self.assertEqual(report.parse_altitude("FL350"), 35000)
        self.assertEqual(report.parse_altitude(" 12500 "), 12500)

    def test_parse_altitude_rejects_expressions(self):
        with self.assertRaises(ValueError):
            report.parse_altitude("FL350+1")

    def test_parse_altitude_does_not_execute_input(self):
        self.addCleanup(os.environ.pop, self.PROBE, None)
        payload = f"__import__('os').environ.setdefault('{self.PROBE}', 'ran') and 0"
        rejected = rejects(report.parse_altitude, payload)
        self.assertIsNone(os.environ.get(self.PROBE), "parse_altitude executed its input")
        self.assertTrue(rejected, "parse_altitude accepted a Python expression")


class UploadTests(unittest.TestCase):
    def test_upload_token_comes_from_environment(self):
        with mock.patch.dict(os.environ, {TOKEN_ENV: "test-token"}):
            self.assertEqual(report.upload_headers(), {"Authorization": "Bearer test-token"})

    def test_upload_without_token_fails(self):
        with mock.patch.dict(os.environ):
            os.environ.pop(TOKEN_ENV, None)
            with self.assertRaises(RuntimeError):
                report.upload_headers()


if __name__ == "__main__":
    unittest.main()
