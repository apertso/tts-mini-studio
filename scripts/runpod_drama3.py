"""Run the Fish Speech server and queue handler in one RunPod worker."""

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


MODEL_CACHE = Path("/runpod-volume/huggingface-cache/hub/models--fishaudio--drama-3")


def checkpoint_path(cache=MODEL_CACHE):
    """Resolve the configured checkpoint or the RunPod Hugging Face cache."""
    configured = os.environ.get("LLAMA_CHECKPOINT_PATH")
    # The upstream image defaults to S2-Pro; ignore that inherited default.
    if configured and configured != "checkpoints/s2-pro":
        path = Path(configured)
    else:
        revision = (cache / "refs" / "main").read_text(encoding="utf-8").strip()
        if not revision or any(c not in "0123456789abcdef" for c in revision):
            raise ValueError("Invalid Drama 3 cached model revision")
        path = cache / "snapshots" / revision
    if not (path / "config.json").is_file() or not (path / "codec.pth").is_file():
        raise FileNotFoundError(f"Drama 3 checkpoint is incomplete: {path}")
    return str(path)


def wait_for_server(server, timeout=900):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"Fish Speech exited during startup: {server.returncode}")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/v1/health", timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(1)
    raise TimeoutError("Fish Speech did not become healthy before the startup deadline")


def stop_process(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    def stop_on_signal(signum, _frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, stop_on_signal)
    signal.signal(signal.SIGINT, stop_on_signal)
    server = worker = None
    try:
        env = os.environ.copy()
        env.update({
            "LLAMA_CHECKPOINT_PATH": checkpoint_path(),
            "API_SERVER_NAME": "127.0.0.1",
            "API_SERVER_PORT": "8080",
            "DEVICE": "cuda:0",
            "COMPILE": "0",
            "TTS_MODE": "runpod",
            "TTS_PROVIDER": "fish-speech",
            "FISH_SPEECH_BASE_URL": "http://127.0.0.1:8080",
        })
        server = subprocess.Popen(["/app/start_server.sh"], cwd="/app", env=env)
        wait_for_server(server)
        worker = subprocess.Popen([sys.executable, "-m", "tts"], cwd="/app/studio", env=env)
        while True:
            if server.poll() is not None:
                raise RuntimeError(f"Fish Speech exited: {server.returncode}")
            if worker.poll() is not None:
                return worker.returncode
            time.sleep(1)
    finally:
        stop_process(worker)
        stop_process(server)


if __name__ == "__main__":
    sys.exit(main())
