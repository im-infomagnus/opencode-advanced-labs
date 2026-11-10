"""Tests for mission/check_prompt.py. Run from the workspace root:

    python3 -m unittest discover -s mission -p "test_*.py"
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_prompt  # noqa: E402

GOOD = (HERE / "MISSION-PROMPT.example.md").read_text(encoding="utf-8")
REGISTRY = json.loads((HERE / "workstreams.json").read_text(encoding="utf-8"))


def errors(text):
    return check_prompt.check(text, REGISTRY)


class CheckPromptTests(unittest.TestCase):
    def test_example_prompt_passes(self):
        self.assertEqual(errors(GOOD), [])

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, str(HERE / "check_prompt.py"), str(HERE / "MISSION-PROMPT.example.md")],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertTrue(ok.stdout.startswith("PASS: "))
        missing = subprocess.run([sys.executable, str(HERE / "check_prompt.py"), str(HERE / "no-such-prompt.md")],
                                 capture_output=True, text=True)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("FAIL: ", missing.stdout)

    def test_missing_heading_is_named(self):
        broken = GOOD.replace("## 7. Check-in protocol", "## 7. Status updates")
        self.assertIn("missing heading '## 7. Check-in protocol'", errors(broken))

    def test_missing_workstream_field_is_named(self):
        start = GOOD.index("### W3 Performance")
        end = GOOD.index("### W4 Alternates")
        section = GOOD[start:end]
        lines = [l for l in section.splitlines(keepends=True) if not l.lstrip("- ").startswith("**Interface:**")]
        broken = GOOD[:start] + "".join(lines) + GOOD[end:]
        self.assertIn("W3: missing or empty **Interface:** field", errors(broken))

    def test_missing_workstream_is_named(self):
        start = GOOD.index("### W6 Assurance")
        end = GOOD.index("## 4. File ownership")
        broken = GOOD[:start] + GOOD[end:]
        self.assertIn("W6: missing '### W6 Assurance' under ## 3. Workstreams", errors(broken))

    def test_file_owned_twice_is_named(self):
        broken = GOOD.replace("| `skyroute/alternates.py` | W4 |",
                              "| `skyroute/alternates.py` | W4 |\n| `skyroute/weather.py` | W4 |")
        self.assertIn("## File ownership: `skyroute/weather.py` owned twice (W1 and W4)", errors(broken))

    def test_wrong_owner_is_named(self):
        broken = GOOD.replace("| `skyroute/cli.py` | commander |", "| `skyroute/cli.py` | W5 |")
        self.assertIn("## File ownership: `skyroute/cli.py` belongs to commander, not W5", errors(broken))

    def test_dependency_violation_is_named(self):
        broken = GOOD.replace("| 1 | W1, W2, W3, W6 (tooling) |", "| 1 | W1, W2, W3, W4, W6 (tooling) |")
        self.assertIn("## Dependency order: W4 starts in wave 1 but depends on W1 (wave 1)", errors(broken))

    def test_launch_rules_need_background(self):
        section_start = GOOD.index("## 6. Subagent launch rules")
        section_end = GOOD.index("## 7. Check-in protocol")
        section = GOOD[section_start:section_end].replace("background: true", "in the foreground")
        broken = GOOD[:section_start] + section + GOOD[section_end:]
        self.assertIn("## Subagent launch rules: must contain 'background: true'", errors(broken))

    def test_check_in_protocol_needs_report_format(self):
        section_start = GOOD.index("## 7. Check-in protocol")
        section_end = GOOD.index("## 8. Phase 1")
        section = GOOD[section_start:section_end].replace("Open issues:", "Problems:")
        broken = GOOD[:section_start] + section + GOOD[section_end:]
        self.assertIn("## Check-in protocol: must contain 'Open issues:'", errors(broken))

    def test_registry_carries_ids_and_signatures(self):
        w1 = next(w for w in REGISTRY["workstreams"] if w["id"] == "W1")
        self.assertIn("SR-WX-002", w1["requirements"])
        self.assertIn("def flight_category(ceiling_ft: int | None, visibility_sm: float) -> str: ...", w1["signatures"])

    def test_dropped_requirement_id_is_named(self):
        start = GOOD.index("  - SR-WX-002:")
        end = GOOD.index("  - SR-WX-003:")
        broken = GOOD[:start] + GOOD[end:]
        self.assertIn("W1: **Requirements:** does not list SR-WX-002", errors(broken))

    def test_requirement_id_in_wrong_section_does_not_count(self):
        broken = GOOD.replace("  - SR-WX-002:", "  - SR-WX-0002:")
        broken = broken.replace("- **Goal:** Parse synthetic NOTAMs", "- **Goal:** SR-WX-002. Parse synthetic NOTAMs")
        self.assertIn("W1: **Requirements:** does not list SR-WX-002", errors(broken))

    def test_changed_signature_is_named(self):
        old = "def flight_category(ceiling_ft: int | None, visibility_sm: float) -> str: ..."
        broken = GOOD.replace(old, "def flight_category(ceiling_ft: int, visibility_sm: float) -> str: ...")
        self.assertNotEqual(broken, GOOD)
        self.assertIn(f"W1: **Interface:** lacks this line from mission/BRIEF.md, copy it exactly: {old}", errors(broken))

    def test_dropped_dataclass_field_is_named(self):
        start = GOOD.index("### W1 Weather")
        end = GOOD.index("### W2 NOTAMs")
        section = GOOD[start:end].replace("    gust_kt: int | None\n", "")
        broken = GOOD[:start] + section + GOOD[end:]
        self.assertIn("W1: **Interface:** lacks this line from mission/BRIEF.md, copy it exactly: gust_kt: int | None",
                      errors(broken))

    def test_signature_comments_and_spacing_may_differ(self):
        ok = GOOD.replace("    wind_dir_deg: int | None     # None for VRB", "    wind_dir_deg:  int | None")
        self.assertNotEqual(ok, GOOD)
        self.assertEqual(errors(ok), [])

    def test_done_needs_per_workstream_verify(self):
        broken = GOOD.replace("`python3 tools/mission_status.py --verify W2` prints", "the full suite prints")
        self.assertIn("W2: **Done:** must include `python3 tools/mission_status.py --verify W2`", errors(broken))

    def test_short_prompt_is_rejected(self):
        short = "\n".join(GOOD.splitlines()[:120])
        self.assertTrue(any(e.startswith("only 120 lines") for e in errors(short)), errors(short))

    def test_ground_rules_need_future_import_and_command_rule(self):
        start = GOOD.index("## 2. Ground rules")
        end = GOOD.index("## 3. Workstreams")
        section = GOOD[start:end].replace("from __future__ import annotations", "type hints").replace("pipes, or redirection", "pipes")
        broken = GOOD[:start] + section + GOOD[end:]
        found = errors(broken)
        self.assertIn("## Ground rules: must contain 'from __future__ import annotations'", found)
        self.assertIn("## Ground rules: must contain 'without `cd`, pipes, or redirection'", found)

    def test_dashes_and_placeholders_are_rejected(self):
        broken = GOOD.replace("## 1. Role\n", "## 1. Role\n\nYou lead \u2014 {{name}}.\n", 1)
        found = errors(broken)
        self.assertTrue(any("em or en dash" in e for e in found), found)
        self.assertTrue(any("template placeholder left in" in e for e in found), found)


if __name__ == "__main__":
    unittest.main()
