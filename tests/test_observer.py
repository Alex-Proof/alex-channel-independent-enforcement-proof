import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("deny_observer", ROOT / "observer" / "deny_observer.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class ObserverTests(unittest.TestCase):
    def test_only_denials_are_emitted_and_paths_are_redacted(self):
        lines = (ROOT / "tests" / "fixtures" / "denials.strace").read_text().splitlines()
        events = [event for line in lines if (event := MODULE.parse_denial(line))]
        self.assertEqual([event["errno"] for event in events], ["EROFS", "EACCES", "EACCES"])
        self.assertEqual(events[0]["path"], "<redacted>/customer-a.txt")
        self.assertEqual(events[1]["path"], "<redacted>/customer-b.txt")
        self.assertEqual(events[2]["path"], "<fd:9>")
        serialized = repr(events)
        self.assertNotIn("/home/runner", serialized)
        self.assertNotIn("/srv/secret", serialized)


if __name__ == "__main__":
    unittest.main()
