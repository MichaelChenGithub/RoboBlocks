import tempfile
from pathlib import Path
import unittest

try:
    from pyqt_app.bridge import RobotCompilerBridge
except ModuleNotFoundError:  # pragma: no cover - PyQt6 missing in CI
    RobotCompilerBridge = None


@unittest.skipIf(RobotCompilerBridge is None, "PyQt6 is not installed")
class RobotCompilerBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = RobotCompilerBridge()

    def test_update_python_code_emits_signal_and_caches_source(self) -> None:
        captured: list[str] = []
        self.bridge.pythonCodeUpdated.connect(captured.append)

        sample = "print('hello world')\n"
        self.bridge.updatePythonCode(sample)

        self.assertEqual(captured, [sample])
        self.assertEqual(self.bridge.currentSource(), sample)

    def test_save_source_to_file_persists_last_source(self) -> None:
        self.bridge.updatePythonCode("print('save me')")

        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "program.py"
            result = self.bridge.saveSourceToFile(str(target))
            self.assertTrue(result)
            self.assertEqual(target.read_text(encoding="utf-8"), "print('save me')")

    def test_save_source_returns_false_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "program.py"
            result = self.bridge.saveSourceToFile(str(target))
            self.assertFalse(result)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
