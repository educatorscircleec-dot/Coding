"""Text-to-speech for dialogue, using Kokoro (an open model that runs on the CPU, for free).

Model files: models/kokoro/kokoro-v1.0.onnx and voices-v1.0.bin
(download once from the Hugging Face repo fastrtc/kokoro-onnx; see README).
Each character picks a voice with `tts_voice` and `tts_speed` in characters/<id>.yaml.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

SAMPLE_RATE = 24000
GAP_BETWEEN_LINES = 0.25  # seconds of silence between two lines in one shot


class KokoroVoice:
    def __init__(self, model_dir: Path):
        from kokoro_onnx import Kokoro

        onnx, voices = model_dir / "kokoro-v1.0.onnx", model_dir / "voices-v1.0.bin"
        if not onnx.exists():
            raise FileNotFoundError(f"Kokoro model not found in {model_dir}; see README")
        self.tts = Kokoro(str(onnx), str(voices))

    def speak(self, text: str, voice: str, speed: float = 1.0) -> np.ndarray:
        samples, sr = self.tts.create(text, voice=voice, speed=speed, lang="en-us")
        assert sr == SAMPLE_RATE
        return samples.astype(np.float32)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SAMPLE_RATE), dtype=np.float32)


def write_wav(samples: np.ndarray, path: Path) -> Path:
    import soundfile as sf

    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), samples, SAMPLE_RATE)
    return path
