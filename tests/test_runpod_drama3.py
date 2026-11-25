import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts import runpod_drama3


class Drama3StartupTests(unittest.TestCase):
    def test_resolves_complete_cached_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {}, clear=True):
            cache = Path(tmp)
            (cache / "refs").mkdir()
            (cache / "refs" / "main").write_text("abcdef123\n", encoding="utf-8")
            checkpoint = cache / "snapshots" / "abcdef123"
            checkpoint.mkdir(parents=True)
            (checkpoint / "config.json").touch()
            (checkpoint / "codec.pth").touch()
            self.assertEqual(runpod_drama3.checkpoint_path(cache), str(checkpoint))

            (checkpoint / "codec.pth").unlink()
            with self.assertRaises(FileNotFoundError):
                runpod_drama3.checkpoint_path(cache)

    def test_refuses_invalid_cache_revision(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {}, clear=True):
            cache = Path(tmp)
            (cache / "refs").mkdir()
            (cache / "refs" / "main").write_text("../../other", encoding="utf-8")
            with self.assertRaises(ValueError):
                runpod_drama3.checkpoint_path(cache)

    def test_wait_reports_server_exit(self):
        server = MagicMock()
        server.poll.return_value = 1
        server.returncode = 1
        with self.assertRaisesRegex(RuntimeError, "exited during startup"):
            runpod_drama3.wait_for_server(server)

    def test_server_exit_stops_queue_worker(self):
        server = MagicMock()
        server.poll.side_effect = [1, 1]
        server.returncode = 1
        worker = MagicMock()
        worker.poll.return_value = None
        with patch.object(runpod_drama3, "checkpoint_path", return_value="/checkpoint"), \
             patch.object(runpod_drama3, "wait_for_server"), \
             patch.object(runpod_drama3.subprocess, "Popen", side_effect=[server, worker]):
            with self.assertRaisesRegex(RuntimeError, "Fish Speech exited"):
                runpod_drama3.main()
        worker.terminate.assert_called_once()
        worker.wait.assert_called_once_with(timeout=10)


if __name__ == "__main__":
    unittest.main()
