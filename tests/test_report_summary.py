import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "sender" / "send_report_summary.py"
spec = importlib.util.spec_from_file_location("send_report_summary", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReportSummaryTests(unittest.TestCase):
    def test_counts_only_expected_sections(self):
        report = """DualDesktopSecurityMonitor - Local Inventory Report
Generated: 2026-10-22 12:00:00

[Running processes]
PID=10  Name=explorer.exe
PID=11  Name=notepad.exe

[Current-user startup Run entries]
Name=ExampleApp  Data=C:\\Example\\app.exe

[Machine startup Run entries]
Name=AnotherApp  Data=C:\\Another\\app.exe
"""
        result = module.summarize_report(report)
        self.assertEqual(result["process_entries"], 2)
        self.assertEqual(result["startup_entries"], 2)
        self.assertEqual(result["generated"], "2026-10-22 12:00:00")
        self.assertNotIn("explorer.exe", str(result))
        self.assertNotIn("app.exe", str(result))

    def test_rejects_unrelated_file(self):
        with self.assertRaises(ValueError):
            module.summarize_report("this is not a DDSM report")

    def test_empty_sections_count_as_zero(self):
        report = """DualDesktopSecurityMonitor - Local Inventory Report
[Running processes]
[Current-user startup Run entries]
[Machine startup Run entries]
"""
        result = module.summarize_report(report)
        self.assertEqual(result["process_entries"], 0)
        self.assertEqual(result["startup_entries"], 0)


if __name__ == "__main__":
    unittest.main()
